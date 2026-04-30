"""長い会話のコンテキストウィンドウを自動圧縮するモジュール。

要約用に独自の OpenAI クライアントを持つ自己完結型クラス。
ヘッドとテールのコンテキストを保護しながら、補助モデル（安価・高速）で
中間ターンを要約する。

v2 からの改善点:
  - 解決済み/未解決の質問追跡を含む構造化要約テンプレート
  - 要約者プリアンブル: "質問に回答しないこと"（OpenCode から）
  - ハンドオフの枠組み: "別のアシスタント"（Codex から）による分離
  - "残作業"が"次のステップ"に替わり、能動的な指示として読まれることを回避
  - 要約がテールメッセージにマージされる際の明確なセパレーター
  - 反復的な要約更新（複数の圧縮をまたいで情報を保持）
  - 固定メッセージ数の代わりにトークン予算によるテール保護
  - LLM 要約前のツール出力のプルーニング（安価なプリパス）
  - スケーリングされた要約予算（圧縮コンテンツに比例）
  - 要約者入力にツール呼び出し/結果の詳細情報を追加
"""

import hashlib
import json
import logging
import re
import time
from typing import Any, Dict, List, Optional

from core.auxiliary_client import call_llm
from core.context_engine import ContextEngine
from core.model_metadata import (
    MINIMUM_CONTEXT_LENGTH,
    get_model_context_length,
    estimate_messages_tokens_rough,
)
from core.redact import redact_sensitive_text

logger = logging.getLogger(__name__)

SUMMARY_PREFIX = (
    "[CONTEXT COMPACTION — REFERENCE ONLY] Earlier turns were compacted "
    "into the summary below. This is a handoff from a previous context "
    "window — treat it as background reference, NOT as active instructions. "
    "Do NOT answer questions or fulfill requests mentioned in this summary; "
    "they were already addressed. "
    "Your current task is identified in the '## Active Task' section of the "
    "summary — resume exactly from there. "
    "Respond ONLY to the latest user message "
    "that appears AFTER this summary. The current session state (files, "
    "config, etc.) may reflect work described here — avoid repeating it:"
)
LEGACY_SUMMARY_PREFIX = "[CONTEXT SUMMARY]:"

# 要約出力の最小トークン数
_MIN_SUMMARY_TOKENS = 2000
# 要約に割り当てる圧縮コンテンツの割合
_SUMMARY_RATIO = 0.20
# 要約トークンの絶対上限（非常に大きなコンテキストウィンドウでも適用）
_SUMMARY_TOKENS_CEILING = 12_000

# 古いツール結果をプルーニングする際のプレースホルダー
_PRUNED_TOOL_PLACEHOLDER = "[Old tool output cleared to save context space]"

# 1 トークンあたりの文字数（概算）
_CHARS_PER_TOKEN = 4
# 添付画像 1 枚あたりのフラットトークンコスト。
# 実コストはプロバイダーと画像サイズによって異なる（Anthropic ≈ width×height/750、
# GPT-4o はハイディテール 2048×2048 で最大 ~1700、Gemini は 258/タイル）が、
# 1600 はマルチ画像会話の圧縮予算を誠実に保つための現実的な上限値。
# Claude Code の IMAGE_TOKEN_ESTIMATE 定数と一致する。
_IMAGE_TOKEN_ESTIMATE = 1600
# コンプレッサーが使用する文字予算単位に換算した同じ値。
# テールカット判断における "コンテンツ長" の累積に使用する。
_IMAGE_CHAR_EQUIVALENT = _IMAGE_TOKEN_ESTIMATE * _CHARS_PER_TOKEN
_SUMMARY_FAILURE_COOLDOWN_SECONDS = 600


def _content_length_for_budget(raw_content: Any) -> int:
    """トークン予算計算用にメッセージコンテンツの有効文字数を返す。

    プレーン文字列: ``len(content)``。マルチモーダルリスト: テキスト部分の
    ``len(text)`` の合計に、画像部分（``image_url`` / ``input_image`` /
    Anthropic 形式の ``image``）ごとにフラットな ``_IMAGE_CHAR_EQUIVALENT``
    を加算する。これにより、テキスト部分が空でも 5 枚の添付画像を持つ
    ターンをほぼゼロトークンとして扱うことを防ぐ。
    """
    if isinstance(raw_content, str):
        return len(raw_content)
    if not isinstance(raw_content, list):
        return len(str(raw_content or ""))

    total = 0
    for p in raw_content:
        if isinstance(p, str):
            total += len(p)
            continue
        if not isinstance(p, dict):
            total += len(str(p))
            continue
        ptype = p.get("type")
        if ptype in {"image_url", "input_image", "image"}:
            total += _IMAGE_CHAR_EQUIVALENT
        else:
            # text / input_text / tool_result-with-text / anything else with
            # a text field.  Ignore the raw base64 payload inside image_url
            # dicts — dimensions don't matter, only whether it's an image.
            total += len(p.get("text", "") or "")
    return total


def _content_text_for_contains(content: Any) -> str:
    """メッセージコンテンツのベストエフォートなテキストビューを返す。

    メッセージにノートを既に追加済みかどうかをサブストリング検査する際のみ使用する。
    他の箇所ではマルチモーダルリストをそのまま保持する。
    """
    if content is None:
        return ""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts: list[str] = []
        for item in content:
            if isinstance(item, str):
                parts.append(item)
            elif isinstance(item, dict):
                text = item.get("text")
                if isinstance(text, str):
                    parts.append(text)
        return "\n".join(part for part in parts if part)
    return str(content)


def _append_text_to_content(content: Any, text: str, *, prepend: bool = False) -> Any:
    """プレーンテキストをメッセージコンテンツに安全に追記または前置する。

    圧縮処理でノートを追加したり、要約を既存メッセージにマージする必要がある場合に使用する。
    メッセージコンテンツはプレーンテキストまたはマルチモーダルなブロックのリストである可能性があるため、
    直接の文字列連結は常に安全とは限らない。
    """
    if content is None:
        return text
    if isinstance(content, str):
        return text + content if prepend else content + text
    if isinstance(content, list):
        text_block = {"type": "text", "text": text}
        return [text_block, *content] if prepend else [*content, text_block]
    rendered = str(content)
    return text + rendered if prepend else rendered + text


def _truncate_tool_call_args_json(args: str, head_chars: int = 200) -> str:
    """ツール呼び出し引数 JSON 内の長い文字列値を JSON の有効性を保ちながら縮小する。

    ツール呼び出しの ``function.arguments`` フィールドは LLM プロバイダーに渡される
    JSON エンコード済み文字列であり、ダウンストリームプロバイダーは厳格に検証して
    不正な形式の場合は非リトライ可能な 400 を返す。
    以前の実装は固定バイトオフセットで生 JSON を切り取って ``...[truncated]`` を追加していたが、
    これは以下のような不正な文字列を生成することがあった::

        {"path": "/foo/bar", "content": "# long markdown
        ...[truncated]

    つまり、未終端の文字列と欠落した閉じブレースである。MiniMax などはこれを
    ``invalid function arguments json string`` として拒否し、
    同じ壊れた履歴を毎ターン再送し続けるループに陥る（issue #11762 を参照）。

    このヘルパーは引数をパースし、解析済み構造内の長い文字列葉を縮小して再シリアライズする。
    非文字列値（パス、整数、ブーリアン）はそのまま保持する。
    引数が最初から有効な JSON でない場合（モデルバックエンドによっては非 JSON ツール引数を使用する）、
    元の文字列をそのまま返し、解析不能な値に置き換えない。
    """
    try:
        parsed = json.loads(args)
    except (ValueError, TypeError):
        return args

    def _shrink(obj: Any) -> Any:
        if isinstance(obj, str):
            if len(obj) > head_chars:
                return obj[:head_chars] + "...[truncated]"
            return obj
        if isinstance(obj, dict):
            return {k: _shrink(v) for k, v in obj.items()}
        if isinstance(obj, list):
            return [_shrink(v) for v in obj]
        return obj

    shrunken = _shrink(parsed)
    # ensure_ascii=False preserves CJK/emoji instead of bloating with \uXXXX
    return json.dumps(shrunken, ensure_ascii=False)


def _summarize_tool_result(tool_name: str, tool_args: str, tool_content: str) -> str:
    """ツール呼び出しと結果を 1 行にまとめた有益な要約を作成する。

    圧縮前のプルーニングパスで、大きなツール出力を情報ゼロの汎用プレースホルダーではなく、
    ツールが何をしたかの短くて有用な説明に置き換えるために使用する。

    以下のような文字列を返す::

        [terminal] ran `npm test` -> exit 0, 47 lines output
        [read_file] read config.py from line 1 (1,200 chars)
        [search_files] content search for 'compress' in agent/ -> 12 matches
    """
    try:
        args = json.loads(tool_args) if tool_args else {}
    except (json.JSONDecodeError, TypeError):
        args = {}

    content = tool_content or ""
    content_len = len(content)
    line_count = content.count("\n") + 1 if content.strip() else 0

    if tool_name == "terminal":
        cmd = args.get("command", "")
        if len(cmd) > 80:
            cmd = cmd[:77] + "..."
        exit_match = re.search(r'"exit_code"\s*:\s*(-?\d+)', content)
        exit_code = exit_match.group(1) if exit_match else "?"
        return f"[terminal] ran `{cmd}` -> exit {exit_code}, {line_count} lines output"

    if tool_name == "read_file":
        path = args.get("path", "?")
        offset = args.get("offset", 1)
        return f"[read_file] read {path} from line {offset} ({content_len:,} chars)"

    if tool_name == "write_file":
        path = args.get("path", "?")
        written_lines = args.get("content", "").count("\n") + 1 if args.get("content") else "?"
        return f"[write_file] wrote to {path} ({written_lines} lines)"

    if tool_name == "search_files":
        pattern = args.get("pattern", "?")
        path = args.get("path", ".")
        target = args.get("target", "content")
        match_count = re.search(r'"total_count"\s*:\s*(\d+)', content)
        count = match_count.group(1) if match_count else "?"
        return f"[search_files] {target} search for '{pattern}' in {path} -> {count} matches"

    if tool_name == "patch":
        path = args.get("path", "?")
        mode = args.get("mode", "replace")
        return f"[patch] {mode} in {path} ({content_len:,} chars result)"

    if tool_name in ("browser_navigate", "browser_click", "browser_snapshot",
                     "browser_type", "browser_scroll", "browser_vision"):
        url = args.get("url", "")
        ref = args.get("ref", "")
        detail = f" {url}" if url else (f" ref={ref}" if ref else "")
        return f"[{tool_name}]{detail} ({content_len:,} chars)"

    if tool_name == "web_search":
        query = args.get("query", "?")
        return f"[web_search] query='{query}' ({content_len:,} chars result)"

    if tool_name == "web_extract":
        urls = args.get("urls", [])
        url_desc = urls[0] if isinstance(urls, list) and urls else "?"
        if isinstance(urls, list) and len(urls) > 1:
            url_desc += f" (+{len(urls) - 1} more)"
        return f"[web_extract] {url_desc} ({content_len:,} chars)"

    if tool_name == "delegate_task":
        goal = args.get("goal", "")
        if len(goal) > 60:
            goal = goal[:57] + "..."
        return f"[delegate_task] '{goal}' ({content_len:,} chars result)"

    if tool_name == "execute_code":
        code_preview = (args.get("code") or "")[:60].replace("\n", " ")
        if len(args.get("code", "")) > 60:
            code_preview += "..."
        return f"[execute_code] `{code_preview}` ({line_count} lines output)"

    if tool_name in ("skill_view", "skills_list", "skill_manage"):
        name = args.get("name", "?")
        return f"[{tool_name}] name={name} ({content_len:,} chars)"

    if tool_name == "vision_analyze":
        question = args.get("question", "")[:50]
        return f"[vision_analyze] '{question}' ({content_len:,} chars)"

    if tool_name == "memory":
        action = args.get("action", "?")
        target = args.get("target", "?")
        return f"[memory] {action} on {target}"

    if tool_name == "todo":
        return "[todo] updated task list"

    if tool_name == "clarify":
        return "[clarify] asked user a question"

    if tool_name == "text_to_speech":
        return f"[text_to_speech] generated audio ({content_len:,} chars)"

    if tool_name == "cronjob":
        action = args.get("action", "?")
        return f"[cronjob] {action}"

    if tool_name == "process":
        action = args.get("action", "?")
        sid = args.get("session_id", "?")
        return f"[process] {action} session={sid}"

    # Generic fallback
    first_arg = ""
    for k, v in list(args.items())[:2]:
        sv = str(v)[:40]
        first_arg += f" {k}={sv}"
    return f"[{tool_name}]{first_arg} ({content_len:,} chars result)"


class ContextCompressor(ContextEngine):
    """デフォルトのコンテキストエンジン — 損失のある要約で会話コンテキストを圧縮する。

    アルゴリズム:
      1. 古いツール結果をプルーニング（安価、LLM 呼び出しなし）
      2. ヘッドメッセージを保護（システムプロンプト + 最初のやり取り）
      3. トークン予算でテールメッセージを保護（最新の約 20K トークン）
      4. 構造化 LLM プロンプトで中間ターンを要約
      5. 再圧縮時は前の要約を反復的に更新
    """

    @property
    def name(self) -> str:
        return "compressor"

    def on_session_reset(self) -> None:
        """/new または /reset 時のセッションごとの状態をリセットする。"""
        super().on_session_reset()
        self._context_probed = False
        self._context_probe_persistable = False
        self._previous_summary = None
        self._last_summary_error = None
        self._last_summary_dropped_count = 0
        self._last_summary_fallback_used = False
        self._last_aux_model_failure_error = None
        self._last_aux_model_failure_model = None
        self._last_compression_savings_pct = 100.0
        self._ineffective_compression_count = 0

    def update_model(
        self,
        model: str,
        context_length: int,
        base_url: str = "",
        api_key: str = "",
        provider: str = "",
        api_mode: str = "",
    ) -> None:
        """モデルの切り替えまたはフォールバック有効化後にモデル情報を更新する。"""
        self.model = model
        self.base_url = base_url
        self.api_key = api_key
        self.provider = provider
        self.api_mode = api_mode
        self.context_length = context_length
        self.threshold_tokens = max(
            int(context_length * self.threshold_percent),
            MINIMUM_CONTEXT_LENGTH,
        )
        # Recalculate token budgets for the new context length so the
        # compressor stays calibrated after a model switch (e.g. 200K → 32K).
        target_tokens = int(self.threshold_tokens * self.summary_target_ratio)
        self.tail_token_budget = target_tokens
        self.max_summary_tokens = min(
            int(context_length * 0.05), _SUMMARY_TOKENS_CEILING,
        )

    def __init__(
        self,
        model: str,
        threshold_percent: float = 0.50,
        protect_first_n: int = 3,
        protect_last_n: int = 20,
        summary_target_ratio: float = 0.20,
        quiet_mode: bool = False,
        summary_model_override: str = None,
        base_url: str = "",
        api_key: str = "",
        config_context_length: int | None = None,
        provider: str = "",
        api_mode: str = "",
    ):
        self.model = model
        self.base_url = base_url
        self.api_key = api_key
        self.provider = provider
        self.api_mode = api_mode
        self.threshold_percent = threshold_percent
        self.protect_first_n = protect_first_n
        self.protect_last_n = protect_last_n
        self.summary_target_ratio = max(0.10, min(summary_target_ratio, 0.80))
        self.quiet_mode = quiet_mode

        self.context_length = get_model_context_length(
            model, base_url=base_url, api_key=api_key,
            config_context_length=config_context_length,
            provider=provider,
        )
        # Floor: never compress below MINIMUM_CONTEXT_LENGTH tokens even if
        # the percentage would suggest a lower value.  This prevents premature
        # compression on large-context models at 50% while keeping the % sane
        # for models right at the minimum.
        self.threshold_tokens = max(
            int(self.context_length * threshold_percent),
            MINIMUM_CONTEXT_LENGTH,
        )
        self.compression_count = 0

        # Derive token budgets: ratio is relative to the threshold, not total context
        target_tokens = int(self.threshold_tokens * self.summary_target_ratio)
        self.tail_token_budget = target_tokens
        self.max_summary_tokens = min(
            int(self.context_length * 0.05), _SUMMARY_TOKENS_CEILING,
        )

        if not quiet_mode:
            logger.info(
                "Context compressor initialized: model=%s context_length=%d "
                "threshold=%d (%.0f%%) target_ratio=%.0f%% tail_budget=%d "
                "provider=%s base_url=%s",
                model, self.context_length, self.threshold_tokens,
                threshold_percent * 100, self.summary_target_ratio * 100,
                self.tail_token_budget,
                provider or "none", base_url or "none",
            )
        self._context_probed = False  # True after a step-down from context error

        self.last_prompt_tokens = 0
        self.last_completion_tokens = 0

        self.summary_model = summary_model_override or ""

        # Stores the previous compaction summary for iterative updates
        self._previous_summary: Optional[str] = None
        # Anti-thrashing: track whether last compression was effective
        self._last_compression_savings_pct: float = 100.0
        self._ineffective_compression_count: int = 0
        self._summary_failure_cooldown_until: float = 0.0
        self._last_summary_error: Optional[str] = None
        # When summary generation fails and a static fallback is inserted,
        # record how many turns were unrecoverably dropped so callers
        # (gateway hygiene, /compress) can surface a visible warning.
        self._last_summary_dropped_count: int = 0
        self._last_summary_fallback_used: bool = False
        # When a user-configured summary model fails and we recover by
        # retrying on the main model, record the failure so gateway /
        # CLI callers can still warn the user even though compression
        # succeeded.  Silent recovery would hide the broken config.
        self._last_aux_model_failure_error: Optional[str] = None
        self._last_aux_model_failure_model: Optional[str] = None

    def update_from_response(self, usage: Dict[str, Any]):
        """API レスポンスからトークン使用量の追跡値を更新する。"""
        self.last_prompt_tokens = usage.get("prompt_tokens", 0)
        self.last_completion_tokens = usage.get("completion_tokens", 0)

    def should_compress(self, prompt_tokens: int = None) -> bool:
        """コンテキストが圧縮閾値を超えているか確認する。

        アンチスラッシング保護を含む: 直近 2 回の圧縮がそれぞれ 10% 未満の
        削減しかしなかった場合、1〜2 メッセージしか削除されない無限ループを
        避けるため圧縮をスキップする。
        """
        tokens = prompt_tokens if prompt_tokens is not None else self.last_prompt_tokens
        if tokens < self.threshold_tokens:
            return False
        # Anti-thrashing: back off if recent compressions were ineffective
        if self._ineffective_compression_count >= 2:
            if not self.quiet_mode:
                logger.warning(
                    "Compression skipped — last %d compressions saved <10%% each. "
                    "Consider /new to start a fresh session, or /compress <topic> "
                    "for focused compression.",
                    self._ineffective_compression_count,
                )
            return False
        return True

    # ------------------------------------------------------------------
    # Tool output pruning (cheap pre-pass, no LLM call)
    # ------------------------------------------------------------------

    def _prune_old_tool_results(
        self, messages: List[Dict[str, Any]], protect_tail_count: int,
        protect_tail_tokens: int | None = None,
    ) -> tuple[List[Dict[str, Any]], int]:
        """古いツール結果の内容を有益な 1 行要約に置き換える。

        汎用プレースホルダーの代わりに、以下のような要約を生成する::

            [terminal] ran `npm test` -> exit 0, 47 lines output
            [read_file] read config.py from line 1 (3,400 chars)

        また、同一のツール結果の重複を排除し（例: 同じファイルを 5 回読む場合は最新の完全なコピーのみ保持）、
        保護されたテール外のアシスタントメッセージの大きなツール呼び出し引数を切り詰める。

        末尾から後ろ向きに走査し、``protect_tail_tokens`` が指定されている場合は
        その範囲内、または後方互換デフォルトとして最後の ``protect_tail_count`` メッセージを保護する。
        両方が指定された場合、トークン予算が優先され、メッセージ数は最低限の床として機能する。

        (pruned_messages, pruned_count) を返す。
        """
        if not messages:
            return messages, 0

        result = [m.copy() for m in messages]
        pruned = 0

        # Build index: tool_call_id -> (tool_name, arguments_json)
        call_id_to_tool: Dict[str, tuple] = {}
        for msg in result:
            if msg.get("role") == "assistant":
                for tc in msg.get("tool_calls") or []:
                    if isinstance(tc, dict):
                        cid = tc.get("id", "")
                        fn = tc.get("function", {})
                        call_id_to_tool[cid] = (fn.get("name", "unknown"), fn.get("arguments", ""))
                    else:
                        cid = getattr(tc, "id", "") or ""
                        fn = getattr(tc, "function", None)
                        name = getattr(fn, "name", "unknown") if fn else "unknown"
                        args_str = getattr(fn, "arguments", "") if fn else ""
                        call_id_to_tool[cid] = (name, args_str)

        # Determine the prune boundary
        if protect_tail_tokens is not None and protect_tail_tokens > 0:
            # Token-budget approach: walk backward accumulating tokens
            accumulated = 0
            boundary = len(result)
            min_protect = min(protect_tail_count, len(result) - 1)
            for i in range(len(result) - 1, -1, -1):
                msg = result[i]
                raw_content = msg.get("content") or ""
                content_len = _content_length_for_budget(raw_content)
                msg_tokens = content_len // _CHARS_PER_TOKEN + 10
                for tc in msg.get("tool_calls") or []:
                    if isinstance(tc, dict):
                        args = tc.get("function", {}).get("arguments", "")
                        msg_tokens += len(args) // _CHARS_PER_TOKEN
                if accumulated + msg_tokens > protect_tail_tokens and (len(result) - i) >= min_protect:
                    boundary = i
                    break
                accumulated += msg_tokens
                boundary = i
            prune_boundary = max(boundary, len(result) - min_protect)
        else:
            prune_boundary = len(result) - protect_tail_count

        # Pass 1: Deduplicate identical tool results.
        # When the same file is read multiple times, keep only the most recent
        # full copy and replace older duplicates with a back-reference.
        content_hashes: dict = {}  # hash -> (index, tool_call_id)
        for i in range(len(result) - 1, -1, -1):
            msg = result[i]
            if msg.get("role") != "tool":
                continue
            content = msg.get("content") or ""
            # Skip multimodal content (list of content blocks)
            if isinstance(content, list):
                continue
            if len(content) < 200:
                continue
            h = hashlib.md5(content.encode("utf-8", errors="replace")).hexdigest()[:12]
            if h in content_hashes:
                # This is an older duplicate — replace with back-reference
                result[i] = {**msg, "content": "[Duplicate tool output — same content as a more recent call]"}
                pruned += 1
            else:
                content_hashes[h] = (i, msg.get("tool_call_id", "?"))

        # Pass 2: Replace old tool results with informative summaries
        for i in range(prune_boundary):
            msg = result[i]
            if msg.get("role") != "tool":
                continue
            content = msg.get("content", "")
            # Skip multimodal content (list of content blocks)
            if isinstance(content, list):
                continue
            if not content or content == _PRUNED_TOOL_PLACEHOLDER:
                continue
            # Skip already-deduplicated or previously-summarized results
            if content.startswith("[Duplicate tool output"):
                continue
            # Only prune if the content is substantial (>200 chars)
            if len(content) > 200:
                call_id = msg.get("tool_call_id", "")
                tool_name, tool_args = call_id_to_tool.get(call_id, ("unknown", ""))
                summary = _summarize_tool_result(tool_name, tool_args, content)
                result[i] = {**msg, "content": summary}
                pruned += 1

        # Pass 3: Truncate large tool_call arguments in assistant messages
        # outside the protected tail. write_file with 50KB content, for
        # example, survives pruning entirely without this.
        #
        # The shrinking is done inside the parsed JSON structure so the
        # result remains valid JSON — otherwise downstream providers 400
        # on every subsequent turn until the broken call falls out of
        # the window. See ``_truncate_tool_call_args_json`` docstring.
        for i in range(prune_boundary):
            msg = result[i]
            if msg.get("role") != "assistant" or not msg.get("tool_calls"):
                continue
            new_tcs = []
            modified = False
            for tc in msg["tool_calls"]:
                if isinstance(tc, dict):
                    args = tc.get("function", {}).get("arguments", "")
                    if len(args) > 500:
                        new_args = _truncate_tool_call_args_json(args)
                        if new_args != args:
                            tc = {**tc, "function": {**tc["function"], "arguments": new_args}}
                            modified = True
                new_tcs.append(tc)
            if modified:
                result[i] = {**msg, "tool_calls": new_tcs}

        return result, pruned

    # ------------------------------------------------------------------
    # Summarization
    # ------------------------------------------------------------------

    def _compute_summary_budget(self, turns_to_summarize: List[Dict[str, Any]]) -> int:
        """圧縮されるコンテンツ量に応じて要約トークン予算をスケールする。

        上限はモデルのコンテキストウィンドウに比例（コンテキストの 5%、
        ``_SUMMARY_TOKENS_CEILING`` で上限設定）するため、大規模コンテキストモデルは
        8K トークン固定ではなく、より豊富な要約を得られる。
        """
        content_tokens = estimate_messages_tokens_rough(turns_to_summarize)
        budget = int(content_tokens * _SUMMARY_RATIO)
        return max(_MIN_SUMMARY_TOKENS, min(budget, self.max_summary_tokens))

    # 要約者入力の切り詰め上限。各メッセージを要約モデルが見る量を制限する。
    # 予算はメインモデルではなく*要約*モデルのコンテキストウィンドウである。
    _CONTENT_MAX = 6000       # メッセージ本体の合計文字数
    _CONTENT_HEAD = 4000      # 先頭から保持する文字数
    _CONTENT_TAIL = 1500      # 末尾から保持する文字数
    _TOOL_ARGS_MAX = 1500     # ツール呼び出し引数の文字数
    _TOOL_ARGS_HEAD = 1200    # ツール引数の先頭から保持する文字数

    def _serialize_for_summary(self, turns: List[Dict[str, Any]]) -> str:
        """会話ターンを要約者向けのラベル付きテキストにシリアライズする。

        ツール呼び出し引数と結果コンテンツ（メッセージごとに最大 ``_CONTENT_MAX`` 文字）を含み、
        ファイルパス・コマンド・出力などの具体的な詳細を要約者が保持できるようにする。

        補助モデルに送られて圧縮をまたいで永続化される要約にシークレット（API キー・
        トークン・パスワード）が漏洩しないよう、シリアライズ前にすべてのコンテンツを
        リダクトする。
        """
        parts = []
        for msg in turns:
            role = msg.get("role", "unknown")
            content = redact_sensitive_text(msg.get("content") or "")

            # Tool results: keep enough content for the summarizer
            if role == "tool":
                tool_id = msg.get("tool_call_id", "")
                if len(content) > self._CONTENT_MAX:
                    content = content[:self._CONTENT_HEAD] + "\n...[truncated]...\n" + content[-self._CONTENT_TAIL:]
                parts.append(f"[TOOL RESULT {tool_id}]: {content}")
                continue

            # Assistant messages: include tool call names AND arguments
            if role == "assistant":
                if len(content) > self._CONTENT_MAX:
                    content = content[:self._CONTENT_HEAD] + "\n...[truncated]...\n" + content[-self._CONTENT_TAIL:]
                tool_calls = msg.get("tool_calls", [])
                if tool_calls:
                    tc_parts = []
                    for tc in tool_calls:
                        if isinstance(tc, dict):
                            fn = tc.get("function", {})
                            name = fn.get("name", "?")
                            args = redact_sensitive_text(fn.get("arguments", ""))
                            # Truncate long arguments but keep enough for context
                            if len(args) > self._TOOL_ARGS_MAX:
                                args = args[:self._TOOL_ARGS_HEAD] + "..."
                            tc_parts.append(f"  {name}({args})")
                        else:
                            fn = getattr(tc, "function", None)
                            name = getattr(fn, "name", "?") if fn else "?"
                            tc_parts.append(f"  {name}(...)")
                    content += "\n[Tool calls:\n" + "\n".join(tc_parts) + "\n]"
                parts.append(f"[ASSISTANT]: {content}")
                continue

            # User and other roles
            if len(content) > self._CONTENT_MAX:
                content = content[:self._CONTENT_HEAD] + "\n...[truncated]...\n" + content[-self._CONTENT_TAIL:]
            parts.append(f"[{role.upper()}]: {content}")

        return "\n\n".join(parts)

    def _generate_summary(self, turns_to_summarize: List[Dict[str, Any]], focus_topic: str = None) -> Optional[str]:
        """会話ターンの構造化要約を生成する。

        目標・進捗・決定・解決済み/未解決の質問・ファイル・残作業を含む構造化テンプレートと、
        要約者に質問へ回答しないよう明示するプリアンブルを使用する。
        以前の要約が存在する場合、最初から要約するのではなく反復的な更新を生成する。

        Args:
            focus_topic: ガイド付き圧縮のオプションのフォーカス文字列。指定された場合、
                要約者はこのトピックに関連する情報の保持を優先し、それ以外をより
                積極的に圧縮する。Claude Code の ``/compact`` にインスパイアされた機能。

        すべての試みが失敗した場合は None を返す — 呼び出し元は役に立たないプレースホルダーを
        注入するのではなく、要約なしで中間ターンを削除すること。
        """
        now = time.monotonic()
        if now < self._summary_failure_cooldown_until:
            logger.debug(
                "Skipping context summary during cooldown (%.0fs remaining)",
                self._summary_failure_cooldown_until - now,
            )
            return None

        summary_budget = self._compute_summary_budget(turns_to_summarize)
        content_to_summarize = self._serialize_for_summary(turns_to_summarize)

        # Preamble shared by both first-compaction and iterative-update prompts.
        # Inspired by OpenCode's "do not respond to any questions" instruction
        # and Codex's "another language model" framing.
        _summarizer_preamble = (
            "You are a summarization agent creating a context checkpoint. "
            "Your output will be injected as reference material for a DIFFERENT "
            "assistant that continues the conversation. "
            "Do NOT respond to any questions or requests in the conversation — "
            "only output the structured summary. "
            "Do NOT include any preamble, greeting, or prefix. "
            "Write the summary in the same language the user was using in the "
            "conversation — do not translate or switch to English. "
            "NEVER include API keys, tokens, passwords, secrets, credentials, "
            "or connection strings in the summary — replace any that appear "
            "with [REDACTED]. Note that the user had credentials present, but "
            "do not preserve their values."
        )

        # Shared structured template (used by both paths).
        _template_sections = f"""## Active Task
[THE SINGLE MOST IMPORTANT FIELD. Copy the user's most recent request or
task assignment verbatim — the exact words they used. If multiple tasks
were requested and only some are done, list only the ones NOT yet completed.
The next assistant must pick up exactly here. Example:
"User asked: 'Now refactor the auth module to use JWT instead of sessions'"
If no outstanding task exists, write "None."]

## Goal
[What the user is trying to accomplish overall]

## Constraints & Preferences
[User preferences, coding style, constraints, important decisions]

## Completed Actions
[Numbered list of concrete actions taken — include tool used, target, and outcome.
Format each as: N. ACTION target — outcome [tool: name]
Example:
1. READ config.py:45 — found `==` should be `!=` [tool: read_file]
2. PATCH config.py:45 — changed `==` to `!=` [tool: patch]
3. TEST `pytest tests/` — 3/50 failed: test_parse, test_validate, test_edge [tool: terminal]
Be specific with file paths, commands, line numbers, and results.]

## Active State
[Current working state — include:
- Working directory and branch (if applicable)
- Modified/created files with brief note on each
- Test status (X/Y passing)
- Any running processes or servers
- Environment details that matter]

## In Progress
[Work currently underway — what was being done when compaction fired]

## Blocked
[Any blockers, errors, or issues not yet resolved. Include exact error messages.]

## Key Decisions
[Important technical decisions and WHY they were made]

## Resolved Questions
[Questions the user asked that were ALREADY answered — include the answer so the next assistant does not re-answer them]

## Pending User Asks
[Questions or requests from the user that have NOT yet been answered or fulfilled. If none, write "None."]

## Relevant Files
[Files read, modified, or created — with brief note on each]

## Remaining Work
[What remains to be done — framed as context, not instructions]

## Critical Context
[Any specific values, error messages, configuration details, or data that would be lost without explicit preservation. NEVER include API keys, tokens, passwords, or credentials — write [REDACTED] instead.]

Target ~{summary_budget} tokens. Be CONCRETE — include file paths, command outputs, error messages, line numbers, and specific values. Avoid vague descriptions like "made some changes" — say exactly what changed.

Write only the summary body. Do not include any preamble or prefix."""

        if self._previous_summary:
            # Iterative update: preserve existing info, add new progress
            prompt = f"""{_summarizer_preamble}

You are updating a context compaction summary. A previous compaction produced the summary below. New conversation turns have occurred since then and need to be incorporated.

PREVIOUS SUMMARY:
{self._previous_summary}

NEW TURNS TO INCORPORATE:
{content_to_summarize}

Update the summary using this exact structure. PRESERVE all existing information that is still relevant. ADD new completed actions to the numbered list (continue numbering). Move items from "In Progress" to "Completed Actions" when done. Move answered questions to "Resolved Questions". Update "Active State" to reflect current state. Remove information only if it is clearly obsolete. CRITICAL: Update "## Active Task" to reflect the user's most recent unfulfilled request — this is the most important field for task continuity.

{_template_sections}"""
        else:
            # First compaction: summarize from scratch
            prompt = f"""{_summarizer_preamble}

Create a structured handoff summary for a different assistant that will continue this conversation after earlier turns are compacted. The next assistant should be able to understand what happened without re-reading the original turns.

TURNS TO SUMMARIZE:
{content_to_summarize}

Use this exact structure:

{_template_sections}"""

        # Inject focus topic guidance when the user provides one via /compress <focus>.
        # This goes at the end of the prompt so it takes precedence.
        if focus_topic:
            prompt += f"""

FOCUS TOPIC: "{focus_topic}"
The user has requested that this compaction PRIORITISE preserving all information related to the focus topic above. For content related to "{focus_topic}", include full detail — exact values, file paths, command outputs, error messages, and decisions. For content NOT related to the focus topic, summarise more aggressively (brief one-liners or omit if truly irrelevant). The focus topic sections should receive roughly 60-70% of the summary token budget. Even for the focus topic, NEVER preserve API keys, tokens, passwords, or credentials — use [REDACTED]."""

        try:
            call_kwargs = {
                "task": "compression",
                "main_runtime": {
                    "model": self.model,
                    "provider": self.provider,
                    "base_url": self.base_url,
                    "api_key": self.api_key,
                    "api_mode": self.api_mode,
                },
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": int(summary_budget * 1.3),
                # timeout resolved from auxiliary.compression.timeout config by call_llm
            }
            if self.summary_model:
                call_kwargs["model"] = self.summary_model
            response = call_llm(**call_kwargs)
            content = response.choices[0].message.content
            # Handle cases where content is not a string (e.g., dict from llama.cpp)
            if not isinstance(content, str):
                content = str(content) if content else ""
            # Redact the summary output as well — the summarizer LLM may
            # ignore prompt instructions and echo back secrets verbatim.
            summary = redact_sensitive_text(content.strip())
            # Store for iterative updates on next compaction
            self._previous_summary = summary
            self._summary_failure_cooldown_until = 0.0
            self._summary_model_fallen_back = False
            self._last_summary_error = None
            return self._with_summary_prefix(summary)
        except RuntimeError:
            # No provider configured — long cooldown, unlikely to self-resolve
            self._summary_failure_cooldown_until = time.monotonic() + _SUMMARY_FAILURE_COOLDOWN_SECONDS
            self._last_summary_error = "no auxiliary LLM provider configured"
            logging.warning("Context compression: no provider available for "
                            "summary. Middle turns will be dropped without summary "
                            "for %d seconds.",
                            _SUMMARY_FAILURE_COOLDOWN_SECONDS)
            return None
        except Exception as e:
            # If the summary model is different from the main model and the
            # error looks permanent (model not found, 503, 404), fall back to
            # using the main model instead of entering cooldown that leaves
            # context growing unbounded.  (#8620 sub-issue 4)
            _status = getattr(e, "status_code", None) or getattr(getattr(e, "response", None), "status_code", None)
            _err_str = str(e).lower()
            _is_model_not_found = (
                _status in (404, 503)
                or "model_not_found" in _err_str
                or "does not exist" in _err_str
                or "no available channel" in _err_str
            )
            if (
                _is_model_not_found
                and self.summary_model
                and self.summary_model != self.model
                and not getattr(self, "_summary_model_fallen_back", False)
            ):
                self._summary_model_fallen_back = True
                logging.warning(
                    "Summary model '%s' not available (%s). "
                    "Falling back to main model '%s' for compression.",
                    self.summary_model, e, self.model,
                )
                # Record the aux-model failure so callers can warn the user
                # even if the retry-on-main succeeds — a misconfigured aux
                # model is something the user needs to fix.
                _err_text = str(e).strip() or e.__class__.__name__
                if len(_err_text) > 220:
                    _err_text = _err_text[:217].rstrip() + "..."
                self._last_aux_model_failure_error = _err_text
                self._last_aux_model_failure_model = self.summary_model
                self.summary_model = ""  # empty = use main model
                self._summary_failure_cooldown_until = 0.0  # no cooldown
                return self._generate_summary(turns_to_summarize, focus_topic=focus_topic)  # retry immediately

            # Unknown-error best-effort retry on main model.  Losing N turns of
            # context is almost always worse than one extra summary attempt, so
            # if we haven't already fallen back and the summary model differs
            # from the main model, try once more on main before entering
            # cooldown.  Errors that DID match _is_model_not_found above are
            # already handled by the fast-path retry; this branch catches
            # everything else (400s, provider-specific "no route" strings,
            # aggregator rejections, etc.) where auto-retry is still safer
            # than dropping the turns.
            if (
                self.summary_model
                and self.summary_model != self.model
                and not getattr(self, "_summary_model_fallen_back", False)
            ):
                self._summary_model_fallen_back = True
                logging.warning(
                    "Summary model '%s' failed (%s). "
                    "Retrying on main model '%s' before giving up.",
                    self.summary_model, e, self.model,
                )
                # Record the aux-model failure (see 404 branch above) — user
                # should know their configured model is broken even if main
                # recovers the call.
                _err_text = str(e).strip() or e.__class__.__name__
                if len(_err_text) > 220:
                    _err_text = _err_text[:217].rstrip() + "..."
                self._last_aux_model_failure_error = _err_text
                self._last_aux_model_failure_model = self.summary_model
                self.summary_model = ""  # empty = use main model
                self._summary_failure_cooldown_until = 0.0
                return self._generate_summary(turns_to_summarize, focus_topic=focus_topic)

            # Transient errors (timeout, rate limit, network) — shorter cooldown
            _transient_cooldown = 60
            self._summary_failure_cooldown_until = time.monotonic() + _transient_cooldown
            err_text = str(e).strip() or e.__class__.__name__
            if len(err_text) > 220:
                err_text = err_text[:217].rstrip() + "..."
            self._last_summary_error = err_text
            logging.warning(
                "Failed to generate context summary: %s. "
                "Further summary attempts paused for %d seconds.",
                e,
                _transient_cooldown,
            )
            return None

    @staticmethod
    def _with_summary_prefix(summary: str) -> str:
        """要約テキストを現在の圧縮ハンドオフ形式に正規化する。"""
        text = (summary or "").strip()
        for prefix in (LEGACY_SUMMARY_PREFIX, SUMMARY_PREFIX):
            if text.startswith(prefix):
                text = text[len(prefix):].lstrip()
                break
        return f"{SUMMARY_PREFIX}\n{text}" if text else SUMMARY_PREFIX

    # ------------------------------------------------------------------
    # Tool-call / tool-result pair integrity helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _get_tool_call_id(tc) -> str:
        """tool_call エントリ（dict または SimpleNamespace）から呼び出し ID を取得する。"""
        if isinstance(tc, dict):
            return tc.get("id", "")
        return getattr(tc, "id", "") or ""

    def _sanitize_tool_pairs(self, messages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """圧縮後の孤立した tool_call / tool_result ペアを修正する。

        2 つの失敗モード:
        1. ツール*結果*が、削除（要約/切り詰め）されたアシスタントの tool_call の
           call_id を参照している。API は "No tool call found for function call
           output with call_id ..." としてこれを拒否する。
        2. アシスタントメッセージの tool_calls の結果が削除されている。
           API はすべての tool_call に対して一致する call_id を持つツール結果が
           後続することを要求するため、これを拒否する。

        このメソッドは孤立した結果を削除し、孤立した呼び出しにスタブ結果を挿入して
        メッセージリストが常に整形式であるようにする。
        """
        surviving_call_ids: set = set()
        for msg in messages:
            if msg.get("role") == "assistant":
                for tc in msg.get("tool_calls") or []:
                    cid = self._get_tool_call_id(tc)
                    if cid:
                        surviving_call_ids.add(cid)

        result_call_ids: set = set()
        for msg in messages:
            if msg.get("role") == "tool":
                cid = msg.get("tool_call_id")
                if cid:
                    result_call_ids.add(cid)

        # 1. Remove tool results whose call_id has no matching assistant tool_call
        orphaned_results = result_call_ids - surviving_call_ids
        if orphaned_results:
            messages = [
                m for m in messages
                if not (m.get("role") == "tool" and m.get("tool_call_id") in orphaned_results)
            ]
            if not self.quiet_mode:
                logger.info("Compression sanitizer: removed %d orphaned tool result(s)", len(orphaned_results))

        # 2. Add stub results for assistant tool_calls whose results were dropped
        missing_results = surviving_call_ids - result_call_ids
        if missing_results:
            patched: List[Dict[str, Any]] = []
            for msg in messages:
                patched.append(msg)
                if msg.get("role") == "assistant":
                    for tc in msg.get("tool_calls") or []:
                        cid = self._get_tool_call_id(tc)
                        if cid in missing_results:
                            patched.append({
                                "role": "tool",
                                "content": "[Result from earlier conversation — see context summary above]",
                                "tool_call_id": cid,
                            })
            messages = patched
            if not self.quiet_mode:
                logger.info("Compression sanitizer: added %d stub tool result(s)", len(missing_results))

        return messages

    def _align_boundary_forward(self, messages: List[Dict[str, Any]], idx: int) -> int:
        """圧縮開始境界を孤立したツール結果を越えて前方にずらす。

        ``messages[idx]`` がツール結果の場合、グループの途中から要約領域を
        開始しないよう、非ツールメッセージに達するまで前方にスライドする。
        """
        while idx < len(messages) and messages[idx].get("role") == "tool":
            idx += 1
        return idx

    def _align_boundary_backward(self, messages: List[Dict[str, Any]], idx: int) -> int:
        """tool_call / 結果グループの分割を避けるために圧縮終了境界を後方に引く。

        境界がツール結果グループの途中（つまり ``idx`` の前に連続したツール
        メッセージがある）に落ちた場合、親のアシスタントメッセージを見つけるまで
        後方に走査する。見つかった場合、アシスタントの前に境界を移動して、
        アシスタント + ツール結果グループ全体が要約領域に含まれるようにする
        （分割すると ``_sanitize_tool_pairs`` が孤立したテール結果を削除して
        サイレントなデータ損失が生じる）。
        """
        if idx <= 0 or idx >= len(messages):
            return idx
        # Walk backward past consecutive tool results
        check = idx - 1
        while check >= 0 and messages[check].get("role") == "tool":
            check -= 1
        # If we landed on the parent assistant with tool_calls, pull the
        # boundary before it so the whole group gets summarised together.
        if check >= 0 and messages[check].get("role") == "assistant" and messages[check].get("tool_calls"):
            idx = check
        return idx

    # ------------------------------------------------------------------
    # Tail protection by token budget
    # ------------------------------------------------------------------

    def _find_last_user_message_idx(
        self, messages: List[Dict[str, Any]], head_end: int
    ) -> int:
        """*head_end* 以降の最後の user ロールメッセージのインデックス、なければ -1 を返す。"""
        for i in range(len(messages) - 1, head_end - 1, -1):
            if messages[i].get("role") == "user":
                return i
        return -1

    def _ensure_last_user_message_in_tail(
        self,
        messages: List[Dict[str, Any]],
        cut_idx: int,
        head_end: int,
    ) -> int:
        """最新のユーザーメッセージが保護されたテールに含まれることを保証する。

        コンテキストコンプレッサーのバグ（#10896）: ``_align_boundary_backward`` が
        tool_call/結果グループをまとめようとするとき、``cut_idx`` をユーザーメッセージを
        越えて引いてしまうことがある。最後のユーザーメッセージが*圧縮された*中間領域に
        入ると、LLM 要約者はそれを "Pending User Asks" に書き込むが、
        ``SUMMARY_PREFIX`` は次のモデルに要約の*後*のユーザーメッセージのみに
        回答するよう指示するため、タスクがアクティブコンテキストから実質的に消えてしまい、
        エージェントが停止・完了済み作業の繰り返し・ユーザーの最新リクエストのサイレント
        ドロップを引き起こす。

        修正: 最後の user ロールメッセージが既にテール（``messages[cut_idx:]``）に
        なければ、``cut_idx`` を後方にずらして含める。その後、ユーザーメッセージの
        直前の tool_call/結果グループを分割しないよう、再度後方に整列する。
        """
        last_user_idx = self._find_last_user_message_idx(messages, head_end)
        if last_user_idx < 0:
            # No user message found beyond head — nothing to anchor.
            return cut_idx

        if last_user_idx >= cut_idx:
            # Already in the tail; nothing to do.
            return cut_idx

        # The last user message is in the middle (compressed) region.
        # Pull cut_idx back to it directly — a user message is already a
        # clean boundary (no tool_call/result splitting risk), so there is no
        # need to call _align_boundary_backward here; doing so would
        # unnecessarily pull the cut further back into the preceding
        # assistant + tool_calls group.
        if not self.quiet_mode:
            logger.debug(
                "Anchoring tail cut to last user message at index %d "
                "(was %d) to prevent active-task loss after compression",
                last_user_idx,
                cut_idx,
            )
        # Safety: never go back into the head region.
        return max(last_user_idx, head_end + 1)

    def _find_tail_cut_by_tokens(
        self, messages: List[Dict[str, Any]], head_end: int,
        token_budget: int | None = None,
    ) -> int:
        """メッセージの末尾から後ろ向きに走査してトークン予算に達するまで累積する。
        テールが開始するインデックスを返す。

        ``token_budget`` のデフォルトは ``self.tail_token_budget`` で、
        ``summary_target_ratio * context_length`` から導出されるため、
        モデルのコンテキストウィンドウに合わせて自動的にスケールする。

        トークン予算が主基準。最低 3 メッセージは常に保護されるが、
        大きすぎるメッセージ（ツール出力・ファイル読み込みなど）の途中での
        切断を避けるため、予算の 1.5 倍まで超過することを許容する。
        最低 3 メッセージでも予算の 1.5 倍を超える場合、圧縮が実行されるよう
        ヘッドの直後にカットを配置する。

        tool_call/結果グループの途中では切断しない。
        最新のユーザーメッセージが常にテールにあることを保証する
        （``_ensure_last_user_message_in_tail`` を参照）。
        """
        if token_budget is None:
            token_budget = self.tail_token_budget
        n = len(messages)
        # Hard minimum: always keep at least 3 messages in the tail
        min_tail = min(3, n - head_end - 1) if n - head_end > 1 else 0
        soft_ceiling = int(token_budget * 1.5)
        accumulated = 0
        cut_idx = n  # start from beyond the end

        for i in range(n - 1, head_end - 1, -1):
            msg = messages[i]
            raw_content = msg.get("content") or ""
            content_len = _content_length_for_budget(raw_content)
            msg_tokens = content_len // _CHARS_PER_TOKEN + 10  # +10 for role/metadata
            # Include tool call arguments in estimate
            for tc in msg.get("tool_calls") or []:
                if isinstance(tc, dict):
                    args = tc.get("function", {}).get("arguments", "")
                    msg_tokens += len(args) // _CHARS_PER_TOKEN
            # Stop once we exceed the soft ceiling (unless we haven't hit min_tail yet)
            if accumulated + msg_tokens > soft_ceiling and (n - i) >= min_tail:
                break
            accumulated += msg_tokens
            cut_idx = i

        # Ensure we protect at least min_tail messages
        fallback_cut = n - min_tail
        if cut_idx > fallback_cut:
            cut_idx = fallback_cut

        # If the token budget would protect everything (small conversations),
        # force a cut after the head so compression can still remove middle turns.
        if cut_idx <= head_end:
            cut_idx = max(fallback_cut, head_end + 1)

        # Align to avoid splitting tool groups
        cut_idx = self._align_boundary_backward(messages, cut_idx)

        # Ensure the most recent user message is always in the tail so the
        # active task is never lost to compression (fixes #10896).
        cut_idx = self._ensure_last_user_message_in_tail(messages, cut_idx, head_end)

        return max(cut_idx, head_end + 1)

    # ------------------------------------------------------------------
    # ContextEngine: manual /compress preflight
    # ------------------------------------------------------------------

    def has_content_to_compress(self, messages: List[Dict[str, Any]]) -> bool:
        """コンパクトできる空でない中間領域がある場合に True を返す。

        ABC のデフォルトをオーバーライドして、トランスクリプトが保護された
        ヘッド/テール内に完全に収まっている場合に、ゲートウェイの ``/compress``
        ガードが LLM 呼び出しをスキップできるようにする。
        """
        compress_start = self._align_boundary_forward(messages, self.protect_first_n)
        compress_end = self._find_tail_cut_by_tokens(messages, compress_start)
        return compress_start < compress_end

    # ------------------------------------------------------------------
    # Main compression entry point
    # ------------------------------------------------------------------

    def compress(self, messages: List[Dict[str, Any]], current_tokens: int = None, focus_topic: str = None) -> List[Dict[str, Any]]:
        """中間ターンを要約することで会話メッセージを圧縮する。

        アルゴリズム:
          1. 古いツール結果をプルーニング（安価なプリパス、LLM 呼び出しなし）
          2. ヘッドメッセージを保護（システムプロンプト + 最初のやり取り）
          3. トークン予算でテール境界を特定（最新コンテキストの約 20K トークン）
          4. 構造化 LLM プロンプトで中間ターンを要約
          5. 再圧縮時は前の要約を反復的に更新

        圧縮後、孤立した tool_call / tool_result ペアをクリーンアップして
        API に不一致の ID が送られないようにする。

        Args:
            focus_topic: ガイド付き圧縮のオプションのフォーカス文字列。指定された場合、
                要約者はこのトピックに関連する情報の保持を優先し、それ以外をより
                積極的に圧縮する。Claude Code の ``/compact`` にインスパイアされた機能。
        """
        # Reset per-call summary failure state — callers inspect these fields
        # after compress() returns to decide whether to surface a warning.
        self._last_summary_dropped_count = 0
        self._last_summary_fallback_used = False
        self._last_summary_error = None
        self._last_aux_model_failure_error = None
        self._last_aux_model_failure_model = None
        n_messages = len(messages)
        # Only need head + 3 tail messages minimum (token budget decides the real tail size)
        _min_for_compress = self.protect_first_n + 3 + 1
        if n_messages <= _min_for_compress:
            if not self.quiet_mode:
                logger.warning(
                    "Cannot compress: only %d messages (need > %d)",
                    n_messages, _min_for_compress,
                )
            return messages

        display_tokens = current_tokens if current_tokens else self.last_prompt_tokens or estimate_messages_tokens_rough(messages)

        # Phase 1: Prune old tool results (cheap, no LLM call)
        messages, pruned_count = self._prune_old_tool_results(
            messages, protect_tail_count=self.protect_last_n,
            protect_tail_tokens=self.tail_token_budget,
        )
        if pruned_count and not self.quiet_mode:
            logger.info("Pre-compression: pruned %d old tool result(s)", pruned_count)

        # Phase 2: Determine boundaries
        compress_start = self.protect_first_n
        compress_start = self._align_boundary_forward(messages, compress_start)

        # Use token-budget tail protection instead of fixed message count
        compress_end = self._find_tail_cut_by_tokens(messages, compress_start)

        if compress_start >= compress_end:
            return messages

        turns_to_summarize = messages[compress_start:compress_end]

        if not self.quiet_mode:
            logger.info(
                "Context compression triggered (%d tokens >= %d threshold)",
                display_tokens,
                self.threshold_tokens,
            )
            logger.info(
                "Model context limit: %d tokens (%.0f%% = %d)",
                self.context_length,
                self.threshold_percent * 100,
                self.threshold_tokens,
            )
            tail_msgs = n_messages - compress_end
            logger.info(
                "Summarizing turns %d-%d (%d turns), protecting %d head + %d tail messages",
                compress_start + 1,
                compress_end,
                len(turns_to_summarize),
                compress_start,
                tail_msgs,
            )

        # Phase 3: Generate structured summary
        summary = self._generate_summary(turns_to_summarize, focus_topic=focus_topic)

        # Phase 4: Assemble compressed message list
        compressed = []
        for i in range(compress_start):
            msg = messages[i].copy()
            if i == 0 and msg.get("role") == "system":
                existing = msg.get("content")
                _compression_note = "[Note: Some earlier conversation turns have been compacted into a handoff summary to preserve context space. The current session state may still reflect earlier work, so build on that summary and state rather than re-doing work.]"
                if _compression_note not in _content_text_for_contains(existing):
                    msg["content"] = _append_text_to_content(
                        existing,
                        "\n\n" + _compression_note if isinstance(existing, str) and existing else _compression_note,
                    )
            compressed.append(msg)

        # If LLM summary failed, insert a static fallback so the model
        # knows context was lost rather than silently dropping everything.
        if not summary:
            if not self.quiet_mode:
                logger.warning("Summary generation failed — inserting static fallback context marker")
            n_dropped = compress_end - compress_start
            self._last_summary_dropped_count = n_dropped
            self._last_summary_fallback_used = True
            summary = (
                f"{SUMMARY_PREFIX}\n"
                f"Summary generation was unavailable. {n_dropped} message(s) were "
                f"removed to free context space but could not be summarized. The removed "
                f"messages contained earlier work in this session. Continue based on the "
                f"recent messages below and the current state of any files or resources."
            )

        _merge_summary_into_tail = False
        last_head_role = messages[compress_start - 1].get("role", "user") if compress_start > 0 else "user"
        first_tail_role = messages[compress_end].get("role", "user") if compress_end < n_messages else "user"
        # Pick a role that avoids consecutive same-role with both neighbors.
        # Priority: avoid colliding with head (already committed), then tail.
        if last_head_role in ("assistant", "tool"):
            summary_role = "user"
        else:
            summary_role = "assistant"
        # If the chosen role collides with the tail AND flipping wouldn't
        # collide with the head, flip it.
        if summary_role == first_tail_role:
            flipped = "assistant" if summary_role == "user" else "user"
            if flipped != last_head_role:
                summary_role = flipped
            else:
                # Both roles would create consecutive same-role messages
                # (e.g. head=assistant, tail=user — neither role works).
                # Merge the summary into the first tail message instead
                # of inserting a standalone message that breaks alternation.
                _merge_summary_into_tail = True
        if not _merge_summary_into_tail:
            compressed.append({"role": summary_role, "content": summary})

        for i in range(compress_end, n_messages):
            msg = messages[i].copy()
            if _merge_summary_into_tail and i == compress_end:
                merged_prefix = (
                    summary
                    + "\n\n--- END OF CONTEXT SUMMARY — "
                    "respond to the message below, not the summary above ---\n\n"
                )
                msg["content"] = _append_text_to_content(
                    msg.get("content"),
                    merged_prefix,
                    prepend=True,
                )
                _merge_summary_into_tail = False
            compressed.append(msg)

        self.compression_count += 1

        compressed = self._sanitize_tool_pairs(compressed)

        new_estimate = estimate_messages_tokens_rough(compressed)
        saved_estimate = display_tokens - new_estimate

        # Anti-thrashing: track compression effectiveness
        savings_pct = (saved_estimate / display_tokens * 100) if display_tokens > 0 else 0
        self._last_compression_savings_pct = savings_pct
        if savings_pct < 10:
            self._ineffective_compression_count += 1
        else:
            self._ineffective_compression_count = 0

        if not self.quiet_mode:
            logger.info(
                "Compressed: %d -> %d messages (~%d tokens saved, %.0f%%)",
                n_messages,
                len(compressed),
                saved_estimate,
                savings_pct,
            )
            logger.info("Compression #%d complete", self.compression_count)

        return compressed
