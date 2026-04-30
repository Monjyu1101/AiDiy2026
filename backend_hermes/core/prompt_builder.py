"""システムプロンプトの組み立て -- アイデンティティ、プラットフォームヒント、スキルインデックス、コンテキストファイル。

すべての関数はステートレス。AIAgent._build_system_prompt() がこれらの関数を呼び出して
部品を組み立て、メモリやエフェメラルプロンプトと結合する。
"""

import json
import logging
import os
import re
import threading
from collections import OrderedDict
from pathlib import Path
from typing import Optional

from base.hermes_constants import get_hermes_home, get_skills_dir, is_wsl

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# コンテキストファイルスキャン -- AGENTS.md, .cursorrules, SOUL.md が
# システムプロンプトに注入される前にプロンプトインジェクションを検出する。
# ---------------------------------------------------------------------------

_CONTEXT_THREAT_PATTERNS = [
    (r'ignore\s+(previous|all|above|prior)\s+instructions', "prompt_injection"),
    (r'do\s+not\s+tell\s+the\s+user', "deception_hide"),
    (r'system\s+prompt\s+override', "sys_prompt_override"),
    (r'disregard\s+(your|all|any)\s+(instructions|rules|guidelines)', "disregard_rules"),
    (r'act\s+as\s+(if|though)\s+you\s+(have\s+no|don\'t\s+have)\s+(restrictions|limits|rules)', "bypass_restrictions"),
    (r'<!--[^>]*(?:ignore|override|system|secret|hidden)[^>]*-->', "html_comment_injection"),
    (r'<\s*div\s+style\s*=\s*["\'][\s\S]*?display\s*:\s*none', "hidden_div"),
    (r'translate\s+.*\s+into\s+.*\s+and\s+(execute|run|eval)', "translate_execute"),
    (r'curl\s+[^\n]*\$\{?\w*(KEY|TOKEN|SECRET|PASSWORD|CREDENTIAL|API)', "exfil_curl"),
    (r'cat\s+[^\n]*(\.env|credentials|\.netrc|\.pgpass)', "read_secrets"),
]

_CONTEXT_INVISIBLE_CHARS = {
    '\u200b', '\u200c', '\u200d', '\u2060', '\ufeff',
    '\u202a', '\u202b', '\u202c', '\u202d', '\u202e',
}


def _scan_context_content(content: str, filename: str) -> str:
    """コンテキストファイルの内容をインジェクションスキャン。サニタイズされた内容を返す。"""
    findings = []

    # 不可視Unicodeをチェック
    for char in _CONTEXT_INVISIBLE_CHARS:
        if char in content:
            findings.append(f"不可視Unicode U+{ord(char):04X}")

    # 脅威パターンをチェック
    for pattern, pid in _CONTEXT_THREAT_PATTERNS:
        if re.search(pattern, content, re.IGNORECASE):
            findings.append(pid)

    if findings:
        logger.warning("コンテキストファイル %s をブロックしました: %s", filename, ", ".join(findings))
        return f"[BLOCKED: {filename} に潜在的なプロンプトインジェクション ({', '.join(findings)}) が含まれています。内容は読み込まれません。]"

    return content


def _find_git_root(start: Path) -> Optional[Path]:
    """*start* とその親ディレクトリを遡って ``.git`` ディレクトリを探す。

    ``.git`` を含むディレクトリ、またはファイルシステムルートに到達しても
    見つからない場合は ``None`` を返す。
    """
    current = start.resolve()
    for parent in [current, *current.parents]:
        if (parent / ".git").exists():
            return parent
    return None


_HERMES_MD_NAMES = (".hermes.md", "HERMES.md")


def _find_hermes_md(cwd: Path) -> Optional[Path]:
    """最も近い ``.hermes.md`` または ``HERMES.md`` を発見する。

    検索順: *cwd* が最初、次に各親ディレクトリをgitリポジトリルートまで
    （含む）遡る。最初に見つかった一致、または何もない場合は ``None`` を返す。
    """
    stop_at = _find_git_root(cwd)
    current = cwd.resolve()

    for directory in [current, *current.parents]:
        for name in _HERMES_MD_NAMES:
            candidate = directory / name
            if candidate.is_file():
                return candidate
        # gitルート（またはファイルシステムルート）で探索を停止
        if stop_at and directory == stop_at:
            break
    return None


def _strip_yaml_frontmatter(content: str) -> str:
    """*content* からオプションのYAMLフロントマター（``---`` 区切り）を除去する。

    フロントマターは構造化設定（モデルオーバーライド、ツール設定）を含む場合があり、
    将来のPRで別途処理される。現在は、人間が読めるMarkdown本文のみが
    システムプロンプトに注入されるよう、フロントマターを除去する。
    """
    if content.startswith("---"):
        end = content.find("\n---", 3)
        if end != -1:
            # 閉じ --- と後続の改行をスキップ
            body = content[end + 4:].lstrip("\n")
            return body if body else content
    return content


# =========================================================================
# 定数
# =========================================================================

DEFAULT_AGENT_IDENTITY = (
    "You are Hermes Harness, an intelligent AI assistant. "
    "You are helpful, knowledgeable, and direct. You assist users with a wide "
    "range of tasks including answering questions, writing and editing code, "
    "analyzing information, creative work, and executing actions via your tools. "
    "You communicate clearly, admit uncertainty when appropriate, and prioritize "
    "being genuinely useful over being verbose unless otherwise directed below. "
    "Be targeted and efficient in your exploration and investigations."
)

HERMES_AGENT_HELP_GUIDANCE = (
    "If the user asks about configuring, setting up, or using Hermes Harness "
    "itself, refer to the documentation before answering."
)

MEMORY_GUIDANCE = (
    "You have persistent memory across sessions. Save durable facts using the memory "
    "tool: user preferences, environment details, tool quirks, and stable conventions. "
    "Memory is injected into every turn, so keep it compact and focused on facts that "
    "will still matter later.\n"
    "Prioritize what reduces future user steering — the most valuable memory is one "
    "that prevents the user from having to correct or remind you again. "
    "User preferences and recurring corrections matter more than procedural task details.\n"
    "Do NOT save task progress, session outcomes, completed-work logs, or temporary TODO "
    "state to memory; use session_search to recall those from past transcripts. "
    "If you've discovered a new way to do something, solved a problem that could be "
    "necessary later, save it as a skill with the skill tool.\n"
    "Write memories as declarative facts, not instructions to yourself. "
    "'User prefers concise responses' ✓ — 'Always respond concisely' ✗. "
    "'Project uses pytest with xdist' ✓ — 'Run tests with pytest -n 4' ✗. "
    "Imperative phrasing gets re-read as a directive in later sessions and can "
    "cause repeated work or override the user's current request. Procedures and "
    "workflows belong in skills, not memory."
)

SESSION_SEARCH_GUIDANCE = (
    "When the user references something from a past conversation or you suspect "
    "relevant cross-session context exists, use session_search to recall it before "
    "asking them to repeat themselves."
)

SKILLS_GUIDANCE = (
    "After completing a complex task (5+ tool calls), fixing a tricky error, "
    "or discovering a non-trivial workflow, save the approach as a "
    "skill with skill_manage so you can reuse it next time.\n"
    "When using a skill and finding it outdated, incomplete, or wrong, "
    "patch it immediately with skill_manage(action='patch') — don't wait to be asked. "
    "Skills that aren't maintained become liabilities."
)

TOOL_USE_ENFORCEMENT_GUIDANCE = (
    "# Tool-use enforcement\n"
    "You MUST use your tools to take action — do not describe what you would do "
    "or plan to do without actually doing it. When you say you will perform an "
    "action (e.g. 'I will run the tests', 'Let me check the file', 'I will create "
    "the project'), you MUST immediately make the corresponding tool call in the same "
    "response. Never end your turn with a promise of future action — execute it now.\n"
    "Keep working until the task is actually complete. Do not stop with a summary of "
    "what you plan to do next time. If you have tools available that can accomplish "
    "the task, use them instead of telling the user what you would do.\n"
    "Every response should either (a) contain tool calls that make progress, or "
    "(b) deliver a final result to the user. Responses that only describe intentions "
    "without acting are not acceptable."
)

# ツール使用強制をトリガーするモデル名の部分文字列。
# 新しいパターンはここに追加する。
TOOL_USE_ENFORCEMENT_MODELS = ("gpt", "codex", "gemini", "gemma", "grok")

# OpenAI GPT/Codex 固有の実行ガイダンス。
# GPTモデルが部分的な結果で作業を放棄する、前提条件のルックアップをスキップする、
# ツールを使わずに幻覚を見る、「完了」と宣言して検証しないといった既知の障害モードに対処する。
OPENAI_MODEL_EXECUTION_GUIDANCE = (
    "# Execution discipline\n"
    "<tool_persistence>\n"
    "- Use tools whenever they improve correctness, completeness, or grounding.\n"
    "- Do not stop early when another tool call would materially improve the result.\n"
    "- If a tool returns empty or partial results, retry with a different query or "
    "strategy before giving up.\n"
    "- Keep calling tools until: (1) the task is complete, AND (2) you have verified "
    "the result.\n"
    "</tool_persistence>\n"
    "\n"
    "<mandatory_tool_use>\n"
    "NEVER answer these from memory or mental computation — ALWAYS use a tool:\n"
    "- Arithmetic, math, calculations → use terminal or execute_code\n"
    "- Hashes, encodings, checksums → use terminal (e.g. sha256sum, base64)\n"
    "- Current time, date, timezone → use terminal (e.g. date)\n"
    "- System state: OS, CPU, memory, disk, ports, processes → use terminal\n"
    "- File contents, sizes, line counts → use read_file, search_files, or terminal\n"
    "- Git history, branches, diffs → use terminal\n"
    "- Current facts (weather, news, versions) → use web_search\n"
    "Your memory and user profile describe the USER, not the system you are "
    "running on. The execution environment may differ from what the user profile "
    "says about their personal setup.\n"
    "</mandatory_tool_use>\n"
    "\n"
    "<act_dont_ask>\n"
    "When a question has an obvious default interpretation, act on it immediately "
    "instead of asking for clarification. Examples:\n"
    "- 'Is port 443 open?' → check THIS machine (don't ask 'open where?')\n"
    "- 'What OS am I running?' → check the live system (don't use user profile)\n"
    "- 'What time is it?' → run `date` (don't guess)\n"
    "Only ask for clarification when the ambiguity genuinely changes what tool "
    "you would call.\n"
    "</act_dont_ask>\n"
    "\n"
    "<prerequisite_checks>\n"
    "- Before taking an action, check whether prerequisite discovery, lookup, or "
    "context-gathering steps are needed.\n"
    "- Do not skip prerequisite steps just because the final action seems obvious.\n"
    "- If a task depends on output from a prior step, resolve that dependency first.\n"
    "</prerequisite_checks>\n"
    "\n"
    "<verification>\n"
    "Before finalizing your response:\n"
    "- Correctness: does the output satisfy every stated requirement?\n"
    "- Grounding: are factual claims backed by tool outputs or provided context?\n"
    "- Formatting: does the output match the requested format or schema?\n"
    "- Safety: if the next step has side effects (file writes, commands, API calls), "
    "confirm scope before executing.\n"
    "</verification>\n"
    "\n"
    "<missing_context>\n"
    "- If required context is missing, do NOT guess or hallucinate an answer.\n"
    "- Use the appropriate lookup tool when missing information is retrievable "
    "(search_files, web_search, read_file, etc.).\n"
    "- Ask a clarifying question only when the information cannot be retrieved by tools.\n"
    "- If you must proceed with incomplete information, label assumptions explicitly.\n"
    "</missing_context>"
)

# Gemini/Gemma 固有の操作ガイダンス。
GOOGLE_MODEL_OPERATIONAL_GUIDANCE = (
    "# Google model operational directives\n"
    "Follow these operational rules strictly:\n"
    "- **Absolute paths:** Always construct and use absolute file paths for all "
    "file system operations. Combine the project root with relative paths.\n"
    "- **Verify first:** Use read_file/search_files to check file contents and "
    "project structure before making changes. Never guess at file contents.\n"
    "- **Dependency checks:** Never assume a library is available. Check "
    "package.json, requirements.txt, Cargo.toml, etc. before importing.\n"
    "- **Conciseness:** Keep explanatory text brief — a few sentences, not "
    "paragraphs. Focus on actions and results over narration.\n"
    "- **Parallel tool calls:** When you need to perform multiple independent "
    "operations (e.g. reading several files), make all the tool calls in a "
    "single response rather than sequentially.\n"
    "- **Non-interactive commands:** Use flags like -y, --yes, --non-interactive "
    "to prevent CLI tools from hanging on prompts.\n"
    "- **Keep going:** Work autonomously until the task is fully resolved. "
    "Don't stop with a plan — execute it.\n"
)

# システムプロンプトに 'system' の代わりに 'developer' ロールを使用すべきモデル名の部分文字列。
DEVELOPER_ROLE_MODELS = ("gpt-5", "codex")

PLATFORM_HINTS = {
    "whatsapp": (
        "You are on a text messaging communication platform, WhatsApp. "
        "Please do not use markdown as it does not render. "
        "You can send media files natively: to deliver a file to the user, "
        "include MEDIA:/absolute/path/to/file in your response."
    ),
    "telegram": (
        "You are on a text messaging communication platform, Telegram. "
        "Standard markdown is automatically converted to Telegram format. "
        "Supported: **bold**, *italic*, ~~strikethrough~~, ||spoiler||, "
        "`inline code`, ```code blocks```, [links](url), and ## headers. "
        "Telegram has NO table syntax — prefer bullet lists or labeled "
        "key: value pairs over pipe tables. "
        "You can send media files natively: to deliver a file to the user, "
        "include MEDIA:/absolute/path/to/file in your response."
    ),
    "discord": (
        "You are in a Discord server or group chat communicating with your user. "
        "You can send media files natively: include MEDIA:/absolute/path/to/file "
        "in your response."
    ),
    "slack": (
        "You are in a Slack workspace communicating with your user. "
        "You can send media files natively: include MEDIA:/absolute/path/to/file "
        "in your response."
    ),
    "signal": (
        "You are on a text messaging communication platform, Signal. "
        "Please do not use markdown as it does not render. "
        "You can send media files natively: include MEDIA:/absolute/path/to/file "
        "in your response."
    ),
    "email": (
        "You are communicating via email. Write clear, well-structured responses "
        "suitable for email. Use plain text formatting (no markdown). "
        "Keep responses concise but complete. "
        "include MEDIA:/absolute/path/to/file in your response."
    ),
    "cron": (
        "You are running as a scheduled cron job. There is no user present — you "
        "cannot ask questions, request clarification, or wait for follow-up. Execute "
        "the task fully and autonomously, making reasonable decisions where needed."
    ),
    "cli": (
        "You are a CLI AI Assistant. Try not to use markdown but simple text "
        "renderable inside a terminal. "
        "File delivery: there is no attachment channel — the user reads your "
        "response directly in their terminal. Do NOT emit MEDIA:/path tags "
        "(those are only intercepted on messaging platforms like Telegram, "
        "Discord, Slack, etc.; on the CLI they render as literal text). "
        "When referring to a file you created or changed, just state its "
        "absolute path in plain text; the user can open it from there."
    ),
    "sms": (
        "You are communicating via SMS. Keep responses concise and use plain text "
        "only — no markdown, no formatting. SMS messages are limited to ~1600 "
        "characters, so be brief and direct."
    ),
    "bluebubbles": (
        "You are chatting via iMessage (BlueBubbles). iMessage does not render "
        "markdown formatting — use plain text. Keep responses concise as they "
        "appear as text messages. You can send media files natively: include "
        "MEDIA:/absolute/path/to/file in your response."
    ),
    "mattermost": (
        "You are in a Mattermost workspace communicating with your user. "
        "Mattermost renders standard Markdown — headings, bold, italic, code "
        "blocks, and tables all work. "
        "You can send media files natively: include MEDIA:/absolute/path/to/file "
        "in your response."
    ),
    "matrix": (
        "You are in a Matrix room communicating with your user. "
        "Matrix renders Markdown — bold, italic, code blocks, and links work; "
        "the adapter converts your Markdown to HTML for rich display. "
        "You can send media files natively: include MEDIA:/absolute/path/to/file "
        "in your response."
    ),
    "feishu": (
        "You are in a Feishu (Lark) workspace communicating with your user. "
        "Feishu renders Markdown in messages — bold, italic, code blocks, and "
        "links are supported. "
        "You can send media files natively: include MEDIA:/absolute/path/to/file "
        "in your response."
    ),
    "weixin": (
        "You are on Weixin/WeChat. Markdown formatting is supported, so you may use it when "
        "it improves readability, but keep the message compact and chat-friendly. "
        "You can send media files natively: include MEDIA:/absolute/path/to/file "
        "in your response."
    ),
    "wecom": (
        "You are on WeCom (企业微信 / Enterprise WeChat). Markdown formatting is supported. "
        "You CAN send media files natively — to deliver a file to the user, include "
        "MEDIA:/absolute/path/to/file in your response."
    ),
    "qqbot": (
        "You are on QQ, a popular Chinese messaging platform. QQ supports markdown formatting "
        "and emoji. You can send media files natively: include MEDIA:/absolute/path/to/file "
        "in your response."
    ),
    "yuanbao": (
        "You are on Yuanbao (腾讯元宝), a Chinese AI assistant platform. "
        "Markdown formatting is supported (code blocks, tables, bold/italic). "
        "You CAN send media files natively — to deliver a file to the user, include "
        "MEDIA:/absolute/path/to/file in your response."
    ),
}

# ---------------------------------------------------------------------------
# 環境ヒント -- エージェントの実行環境に関する認識。
# PLATFORM_HINTS（メッセージングチャネルを説明）とは異なり、
# こちらはエージェントのツールが実際に動作するマシン/OSを説明する。
# ---------------------------------------------------------------------------

WSL_ENVIRONMENT_HINT = (
    "You are running inside WSL (Windows Subsystem for Linux). "
    "The Windows host filesystem is mounted under /mnt/ — "
    "/mnt/c/ is the C: drive, /mnt/d/ is D:, etc. "
    "The user's Windows files are typically at "
    "/mnt/c/Users/<username>/Desktop/, Documents/, Downloads/, etc. "
    "When the user references Windows paths or desktop files, translate "
    "to the /mnt/c/ equivalent. You can list /mnt/c/Users/ to discover "
    "the Windows username if needed."
)


def build_environment_hints() -> str:
    """システムプロンプト用の環境固有のガイダンスを返す。

    WSLを検出し、Termux、Dockerなどにも拡張可能。
    特殊な環境が検出されない場合は空文字列を返す。
    """
    hints: list[str] = []
    if is_wsl():
        hints.append(WSL_ENVIRONMENT_HINT)
    return "\n\n".join(hints)


CONTEXT_FILE_MAX_CHARS = 20_000
CONTEXT_TRUNCATE_HEAD_RATIO = 0.7
CONTEXT_TRUNCATE_TAIL_RATIO = 0.2


# =========================================================================
# スキルプロンプトキャッシュ
# =========================================================================

_SKILLS_PROMPT_CACHE_MAX = 8
_SKILLS_PROMPT_CACHE: OrderedDict[tuple, str] = OrderedDict()
_SKILLS_PROMPT_CACHE_LOCK = threading.Lock()
_SKILLS_SNAPSHOT_VERSION = 1


def _skills_prompt_snapshot_path() -> Path:
    return get_hermes_home() / ".skills_prompt_snapshot.json"


def clear_skills_system_prompt_cache(*, clear_snapshot: bool = False) -> None:
    """インプロセスのスキルプロンプトキャッシュを削除する（オプションでディスクスナップショットも）。"""
    with _SKILLS_PROMPT_CACHE_LOCK:
        _SKILLS_PROMPT_CACHE.clear()
    if clear_snapshot:
        try:
            _skills_prompt_snapshot_path().unlink(missing_ok=True)
        except OSError as e:
            logger.debug("スキルプロンプトスナップショットの削除に失敗: %s", e)


def _build_skills_manifest(skills_dir: Path) -> dict[str, list[int]]:
    """全 SKILL.md と DESCRIPTION.md ファイルの mtime/size マニフェストを構築する。"""
    manifest: dict[str, list[int]] = {}
    # skill_utils の iter_skill_index_files に依存せず、単純化したスキャン
    for filename in ("SKILL.md", "DESCRIPTION.md"):
        for path in skills_dir.rglob(filename):
            try:
                st = path.stat()
            except OSError:
                continue
            manifest[str(path.relative_to(skills_dir))] = [st.st_mtime_ns, st.st_size]
    return manifest


def _load_skills_snapshot(skills_dir: Path) -> Optional[dict]:
    """ディスクスナップショットが存在し、マニフェストが一致すれば読み込む。"""
    snapshot_path = _skills_prompt_snapshot_path()
    if not snapshot_path.exists():
        return None
    try:
        snapshot = json.loads(snapshot_path.read_text(encoding="utf-8"))
    except Exception:
        return None
    if not isinstance(snapshot, dict):
        return None
    if snapshot.get("version") != _SKILLS_SNAPSHOT_VERSION:
        return None
    if snapshot.get("manifest") != _build_skills_manifest(skills_dir):
        return None
    return snapshot


def _write_skills_snapshot(
    skills_dir: Path,
    manifest: dict[str, list[int]],
    skill_entries: list[dict],
    category_descriptions: dict[str, str],
) -> None:
    """スキルメタデータをディスクに永続化して、コールドスタート時の再利用を高速化する。"""
    payload = {
        "version": _SKILLS_SNAPSHOT_VERSION,
        "manifest": manifest,
        "skills": skill_entries,
        "category_descriptions": category_descriptions,
    }
    try:
        snapshot_path = _skills_prompt_snapshot_path()
        snapshot_path.parent.mkdir(parents=True, exist_ok=True)
        snapshot_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    except Exception as e:
        logger.debug("スキルプロンプトスナップショットの書き込みに失敗: %s", e)


def _build_snapshot_entry(
    skill_file: Path,
    skills_dir: Path,
    frontmatter: dict,
    description: str,
) -> dict:
    """1スキルのシリアライズ可能なメタデータ辞書を構築する。"""
    rel_path = skill_file.relative_to(skills_dir)
    parts = rel_path.parts
    if len(parts) >= 2:
        skill_name = parts[-2]
        category = "/".join(parts[:-2]) if len(parts) > 2 else parts[0]
    else:
        category = "general"
        skill_name = skill_file.parent.name

    platforms = frontmatter.get("platforms") or []
    if isinstance(platforms, str):
        platforms = [platforms]

    return {
        "skill_name": skill_name,
        "category": category,
        "frontmatter_name": str(frontmatter.get("name", skill_name)),
        "description": description,
        "platforms": [str(p).strip() for p in platforms if str(p).strip()],
        "conditions": frontmatter.get("conditions") or {},
    }


# =========================================================================
# スキルインデックス
# =========================================================================

def _parse_skill_file(skill_file: Path) -> tuple[bool, dict, str]:
    """SKILL.md を一度読み込み、プラットフォーム互換性、フロントマター、説明を返す。

    戻り値: (is_compatible, frontmatter, description)。エラー時は (True, {}, "") を返し、
    スキルを表示する方向に倒す。
    """
    try:
        raw = skill_file.read_text(encoding="utf-8")
        # 簡易フロントマターパース
        frontmatter = {}
        description = ""
        if raw.startswith("---"):
            end = raw.find("\n---", 3)
            if end != -1:
                fm_text = raw[3:end]
                for line in fm_text.strip().split("\n"):
                    if ":" in line:
                        key, val = line.split(":", 1)
                        frontmatter[key.strip()] = val.strip()
        description = frontmatter.get("description", "")
        return True, frontmatter, description
    except Exception as e:
        logger.warning("スキルファイル %s のパースに失敗: %s", skill_file, e)
        return True, {}, ""


def _skill_should_show(
    conditions: dict,
    available_tools: "set[str] | None",
    available_toolsets: "set[str] | None",
) -> bool:
    """スキルの条件付きアクティベーションルールがそれを除外する場合に False を返す。"""
    if available_tools is None and available_toolsets is None:
        return True  # フィルタリング情報なし — すべて表示（後方互換）

    at = available_tools or set()
    ats = available_toolsets or set()

    # fallback_for: プライマリツール/ツールセットが利用可能な場合は非表示
    for ts in conditions.get("fallback_for_toolsets", []):
        if ts in ats:
            return False
    for t in conditions.get("fallback_for_tools", []):
        if t in at:
            return False

    # requires: 必要なツール/ツールセットが利用可能でない場合は非表示
    for ts in conditions.get("requires_toolsets", []):
        if ts not in ats:
            return False
    for t in conditions.get("requires_tools", []):
        if t not in at:
            return False

    return True


def build_skills_system_prompt(
    available_tools: "set[str] | None" = None,
    available_toolsets: "set[str] | None" = None,
) -> str:
    """システムプロンプト用のコンパクトなスキルインデックスを構築する。

    2層キャッシュ:
      1. (skills_dir, tools, toolsets) をキーとするインプロセスLRU辞書
      2. mtime/sizeマニフェストで検証されたディスクスナップショット（プロセス再起動後も存続）

    両方の層がミスした場合、フルファイルシステムスキャンにフォールバックする。
    """
    skills_dir = get_skills_dir()

    if not skills_dir.exists():
        return ""

    # ── レイヤー1: インプロセスLRUキャッシュ ──────────────────────────────
    disabled_names = set()
    cache_key = (
        str(skills_dir.resolve()),
        tuple(sorted(str(t) for t in (available_tools or set()))),
        tuple(sorted(str(ts) for ts in (available_toolsets or set()))),
        tuple(sorted(disabled_names)),
    )
    with _SKILLS_PROMPT_CACHE_LOCK:
        cached = _SKILLS_PROMPT_CACHE.get(cache_key)
        if cached is not None:
            _SKILLS_PROMPT_CACHE.move_to_end(cache_key)
            return cached

    # ── レイヤー2: ディスクスナップショット ────────────────────────────────
    snapshot = _load_skills_snapshot(skills_dir)

    skills_by_category: dict[str, list[tuple[str, str]]] = {}
    category_descriptions: dict[str, str] = {}

    if snapshot is not None:
        # 高速パス: ディスクから事前パース済みメタデータを使用
        for entry in snapshot.get("skills", []):
            if not isinstance(entry, dict):
                continue
            skill_name = entry.get("skill_name") or ""
            category = entry.get("category") or "general"
            frontmatter_name = entry.get("frontmatter_name") or skill_name
            if frontmatter_name in disabled_names or skill_name in disabled_names:
                continue
            if not _skill_should_show(
                entry.get("conditions") or {},
                available_tools,
                available_toolsets,
            ):
                continue
            skills_by_category.setdefault(category, []).append(
                (frontmatter_name, entry.get("description", ""))
            )
        category_descriptions = {
            str(k): str(v)
            for k, v in (snapshot.get("category_descriptions") or {}).items()
        }
    else:
        # コールドパス: フルファイルシステムスキャン + 次回用にスナップショット書き込み
        skill_entries: list[dict] = []
        for skill_file in skills_dir.rglob("SKILL.md"):
            is_compatible, frontmatter, desc = _parse_skill_file(skill_file)
            entry = _build_snapshot_entry(skill_file, skills_dir, frontmatter, desc)
            skill_entries.append(entry)
            if not is_compatible:
                continue
            skill_name = entry["skill_name"]
            if entry["frontmatter_name"] in disabled_names or skill_name in disabled_names:
                continue
            if not _skill_should_show(
                frontmatter.get("conditions") or {},
                available_tools,
                available_toolsets,
            ):
                continue
            skills_by_category.setdefault(entry["category"], []).append(
                (entry["frontmatter_name"], entry["description"])
            )

        # カテゴリレベルの DESCRIPTION.md ファイルを読み込む
        for desc_file in skills_dir.rglob("DESCRIPTION.md"):
            try:
                content = desc_file.read_text(encoding="utf-8")
                # 簡易フロントマターパース
                if content.startswith("---"):
                    end = content.find("\n---", 3)
                    if end != -1:
                        fm_text = content[3:end]
                        for line in fm_text.strip().split("\n"):
                            if ":" in line:
                                key, val = line.split(":", 1)
                                if key.strip() == "description":
                                    rel = desc_file.relative_to(skills_dir)
                                    cat = "/".join(rel.parts[:-1]) if len(rel.parts) > 1 else "general"
                                    category_descriptions[cat] = str(val).strip().strip("'\"")
            except Exception as e:
                logger.debug("スキル説明 %s の読み込みに失敗: %s", desc_file, e)

        _write_skills_snapshot(
            skills_dir,
            _build_skills_manifest(skills_dir),
            skill_entries,
            category_descriptions,
        )

    if not skills_by_category:
        result = ""
    else:
        index_lines = []
        for category in sorted(skills_by_category.keys()):
            cat_desc = category_descriptions.get(category, "")
            if cat_desc:
                index_lines.append(f"  {category}: {cat_desc}")
            else:
                index_lines.append(f"  {category}:")
            seen = set()
            for name, desc in sorted(skills_by_category[category], key=lambda x: x[0]):
                if name in seen:
                    continue
                seen.add(name)
                if desc:
                    index_lines.append(f"    - {name}: {desc}")
                else:
                    index_lines.append(f"    - {name}")

        result = (
            "## Skills (mandatory)\n"
            "Before replying, scan the skills below. If a skill matches or is even partially relevant "
            "to your task, you MUST load it with skill_view(name) and follow its instructions. "
            "Err on the side of loading — it is always better to have context you don't need "
            "than to miss critical steps, pitfalls, or established workflows. "
            "Skills contain specialized knowledge — API endpoints, tool-specific commands, "
            "and proven workflows that outperform general-purpose approaches. Load the skill "
            "even if you think you could handle the task with basic tools like web_search or terminal. "
            "Skills also encode the user's preferred approach, conventions, and quality standards "
            "for tasks like code review, planning, and testing.\n"
            "\n"
            "<available_skills>\n"
            + "\n".join(index_lines) + "\n"
            "</available_skills>\n"
            "\n"
            "Only proceed without loading a skill if genuinely none are relevant to the task."
        )

    # ── LRUキャッシュに保存 ────────────────────────────────────────────────
    with _SKILLS_PROMPT_CACHE_LOCK:
        _SKILLS_PROMPT_CACHE[cache_key] = result
        _SKILLS_PROMPT_CACHE.move_to_end(cache_key)
        while len(_SKILLS_PROMPT_CACHE) > _SKILLS_PROMPT_CACHE_MAX:
            _SKILLS_PROMPT_CACHE.popitem(last=False)

    return result


# =========================================================================
# コンテキストファイル（SOUL.md, AGENTS.md, .cursorrules）
# =========================================================================

def _truncate_content(content: str, filename: str, max_chars: int = CONTEXT_FILE_MAX_CHARS) -> str:
    """先頭/末尾トランケーション — 中央にマーカーを挿入。"""
    if len(content) <= max_chars:
        return content
    head_chars = int(max_chars * CONTEXT_TRUNCATE_HEAD_RATIO)
    tail_chars = int(max_chars * CONTEXT_TRUNCATE_TAIL_RATIO)
    head = content[:head_chars]
    tail = content[-tail_chars:]
    marker = f"\n\n[...truncated {filename}: kept {head_chars}+{tail_chars} of {len(content)} chars. Use file tools to read the full file.]\n\n"
    return head + marker + tail


def load_soul_md() -> Optional[str]:
    """HERMES_HOME から SOUL.md を読み込み、内容を返す。なければ None。

    エージェントのアイデンティティとして使用される（システムプロンプトのスロット#1）。
    この関数が内容を返す場合、``build_context_files_prompt`` は
    ``skip_soul=True`` で呼び出されるべき。
    """
    soul_path = get_hermes_home() / "SOUL.md"
    if not soul_path.exists():
        return None
    try:
        content = soul_path.read_text(encoding="utf-8").strip()
        if not content:
            return None
        content = _scan_context_content(content, "SOUL.md")
        content = _truncate_content(content, "SOUL.md")
        return content
    except Exception as e:
        logger.debug("SOUL.md の読み込みに失敗 (%s): %s", soul_path, e)
        return None


def _load_hermes_md(cwd_path: Path) -> str:
    """.hermes.md / HERMES.md — gitルートまで遡る。"""
    hermes_md_path = _find_hermes_md(cwd_path)
    if not hermes_md_path:
        return ""
    try:
        content = hermes_md_path.read_text(encoding="utf-8").strip()
        if not content:
            return ""
        content = _strip_yaml_frontmatter(content)
        rel = hermes_md_path.name
        try:
            rel = str(hermes_md_path.relative_to(cwd_path))
        except ValueError:
            pass
        content = _scan_context_content(content, rel)
        result = f"## {rel}\n\n{content}"
        return _truncate_content(result, ".hermes.md")
    except Exception as e:
        logger.debug("%s の読み込みに失敗: %s", hermes_md_path, e)
        return ""


def _load_agents_md(cwd_path: Path) -> str:
    """AGENTS.md — トップレベルのみ（再帰的な探索なし）。"""
    for name in ["AGENTS.md", "agents.md"]:
        candidate = cwd_path / name
        if candidate.exists():
            try:
                content = candidate.read_text(encoding="utf-8").strip()
                if content:
                    content = _scan_context_content(content, name)
                    result = f"## {name}\n\n{content}"
                    return _truncate_content(result, "AGENTS.md")
            except Exception as e:
                logger.debug("%s の読み込みに失敗: %s", candidate, e)
    return ""


def _load_claude_md(cwd_path: Path) -> str:
    """CLAUDE.md / claude.md — cwdのみ。"""
    for name in ["CLAUDE.md", "claude.md"]:
        candidate = cwd_path / name
        if candidate.exists():
            try:
                content = candidate.read_text(encoding="utf-8").strip()
                if content:
                    content = _scan_context_content(content, name)
                    result = f"## {name}\n\n{content}"
                    return _truncate_content(result, "CLAUDE.md")
            except Exception as e:
                logger.debug("%s の読み込みに失敗: %s", candidate, e)
    return ""


def _load_cursorrules(cwd_path: Path) -> str:
    """.cursorrules + .cursor/rules/*.mdc — cwdのみ。"""
    cursorrules_content = ""
    cursorrules_file = cwd_path / ".cursorrules"
    if cursorrules_file.exists():
        try:
            content = cursorrules_file.read_text(encoding="utf-8").strip()
            if content:
                content = _scan_context_content(content, ".cursorrules")
                cursorrules_content += f"## .cursorrules\n\n{content}\n\n"
        except Exception as e:
            logger.debug(".cursorrules の読み込みに失敗: %s", e)

    cursor_rules_dir = cwd_path / ".cursor" / "rules"
    if cursor_rules_dir.exists() and cursor_rules_dir.is_dir():
        mdc_files = sorted(cursor_rules_dir.glob("*.mdc"))
        for mdc_file in mdc_files:
            try:
                content = mdc_file.read_text(encoding="utf-8").strip()
                if content:
                    content = _scan_context_content(content, f".cursor/rules/{mdc_file.name}")
                    cursorrules_content += f"## .cursor/rules/{mdc_file.name}\n\n{content}\n\n"
            except Exception as e:
                logger.debug("%s の読み込みに失敗: %s", mdc_file, e)

    if not cursorrules_content:
        return ""
    return _truncate_content(cursorrules_content, ".cursorrules")


def build_context_files_prompt(cwd: Optional[str] = None, skip_soul: bool = False) -> str:
    """システムプロンプト用のコンテキストファイルを発見して読み込む。

    優先順位（最初に見つかったもののみが採用 — プロジェクトコンテキストタイプは1つのみ）:
      1. .hermes.md / HERMES.md  （gitルートまで遡る）
      2. AGENTS.md / agents.md   （cwdのみ）
      3. CLAUDE.md / claude.md   （cwdのみ）
      4. .cursorrules / .cursor/rules/*.mdc  （cwdのみ）

    SOUL.md は独立しており、存在する場合は常に含まれる。
    各コンテキストソースは20,000文字に制限される。

    *skip_soul* が True の場合、SOUL.md はここに含まれない（アイデンティティスロット用に
    すでに ``load_soul_md()`` で読み込まれている）。
    """
    if cwd is None:
        cwd = os.getcwd()

    cwd_path = Path(cwd).resolve()
    sections = []

    # 優先順位ベースのプロジェクトコンテキスト: 最初のマッチが優先
    project_context = (
        _load_hermes_md(cwd_path)
        or _load_agents_md(cwd_path)
        or _load_claude_md(cwd_path)
        or _load_cursorrules(cwd_path)
    )
    if project_context:
        sections.append(project_context)

    # HERMES_HOME からの SOUL.md のみ — すでにアイデンティティとして読み込まれている場合はスキップ
    if not skip_soul:
        soul_content = load_soul_md()
        if soul_content:
            sections.append(soul_content)

    if not sections:
        return ""
    return "# Project Context\n\nThe following project context files have been loaded and should be followed:\n\n" + "\n".join(sections)
