"""Anthropic Messages API アダプター（Hermes Agent 用）。

Hermes 内部の OpenAI スタイルメッセージ形式と
Anthropic Messages API の間で変換を行う。codex_responses
アダプターと同じパターンに従い、プロバイダー固有のロジックをここに集約する。

認証サポート:
  - 通常の API キー (sk-ant-api*) → x-api-key ヘッダー
  - OAuth セットアップトークン (sk-ant-oat*) → Bearer 認証 + beta ヘッダー
  - Claude Code 資格情報 (~/.claude.json または ~/.claude/.credentials.json) → Bearer 認証
"""

import copy
import json
import logging
import os
import platform
import subprocess
from pathlib import Path

from base.hermes_constants import get_hermes_home
from typing import Any, Dict, List, Optional, Tuple
from base.utils import normalize_proxy_env_vars

# NOTE: `import anthropic` is deliberately NOT at module top — the SDK pulls
# ~220 ms of imports (anthropic.types, anthropic.lib.tools._beta_runner, etc.)
# and the 3 usage sites (build_anthropic_client, build_anthropic_bedrock_client,
# read_claude_code_credentials_from_keychain) are all on cold user-triggered
# paths. Access via the `_get_anthropic_sdk()` accessor below, which caches
# the module after the first call and returns None on ImportError.
_anthropic_sdk: Any = ...  # sentinel — None means "tried and missing"


def _get_anthropic_sdk():
    """``anthropic`` SDK モジュールを遅延インポートして返す。未インストールなら None を返す。"""
    global _anthropic_sdk
    if _anthropic_sdk is ...:
        try:
            import anthropic as _sdk
            _anthropic_sdk = _sdk
        except ImportError:
            _anthropic_sdk = None
    return _anthropic_sdk

logger = logging.getLogger(__name__)

THINKING_BUDGET = {"xhigh": 32000, "high": 16000, "medium": 8000, "low": 4000}
# Hermes effort → Anthropic 適応的思考 effort (output_config.effort) のマッピング。
# Anthropic は 4.7+ で 5 レベルを提供: low, medium, high, xhigh, max。
# Opus/Sonnet 4.6 は 4 レベルのみ: low, medium, high, max（xhigh なし）。
# 4.7+ では xhigh をそのまま使用（コーディング・エージェント作業の推奨デフォルト）し、
# 4.7 以前の適応型モデルでは max にダウングレードする（最強レベルとして受け入れられる）。
# "minimal" はすべてのモデルで low にマッピングされるレガシーエイリアス。参照:
# https://platform.claude.com/docs/en/about-claude/models/migration-guide
ADAPTIVE_EFFORT_MAP = {
    "max":     "max",
    "xhigh":   "xhigh",
    "high":    "high",
    "medium":  "medium",
    "low":     "low",
    "minimal": "low",
}

# "xhigh" output_config.effort レベルを受け入れるモデル。Opus 4.7 で xhigh が
# high と max の間の独立したレベルとして追加された。4.7 以前の適応型モデル（4.6）は
# 400 エラーで拒否する。新しいモデルファミリーのリリースに合わせてリストを更新すること。
_XHIGH_EFFORT_SUBSTRINGS = ("4-7", "4.7")

# 拡張思考が非推奨・削除されたモデル（4.6+ の動作: 適応型のみサポート;
# 4.7 では手動思考が完全に禁止され、temperature/top_p/top_k も削除）。
_ADAPTIVE_THINKING_SUBSTRINGS = ("4-6", "4.6", "4-7", "4.7")

# デフォルト以外の値で temperature/top_p/top_k を設定すると 400 を返すモデル。
# Opus 4.7 の契約; 将来の 4.x+ モデルも同様の動作が予想される。
_NO_SAMPLING_PARAMS_SUBSTRINGS = ("4-7", "4.7")

# ── Anthropic モデルごとの最大出力トークン制限 ────────────────────────
# 出典: Anthropic ドキュメント + Cline モデルカタログ。Anthropic の API では
# max_tokens が必須フィールド。以前は 16384 をハードコードしていたが、
# 思考有効モデルでは不足する（思考トークンも制限に計上されるため）。
_ANTHROPIC_OUTPUT_LIMITS = {
    # Claude 4.7
    "claude-opus-4-7":   128_000,
    # Claude 4.6
    "claude-opus-4-6":   128_000,
    "claude-sonnet-4-6":  64_000,
    # Claude 4.5
    "claude-opus-4-5":    64_000,
    "claude-sonnet-4-5":  64_000,
    "claude-haiku-4-5":   64_000,
    # Claude 4
    "claude-opus-4":      32_000,
    "claude-sonnet-4":    64_000,
    # Claude 3.7
    "claude-3-7-sonnet": 128_000,
    # Claude 3.5
    "claude-3-5-sonnet":   8_192,
    "claude-3-5-haiku":    8_192,
    # Claude 3
    "claude-3-opus":       4_096,
    "claude-3-sonnet":     4_096,
    "claude-3-haiku":      4_096,
    # Third-party Anthropic-compatible providers
    "minimax":            131_072,
}

# テーブルに存在しないモデルは最大の現行制限を想定する。
# 将来の Anthropic モデルが出力容量を *減らす* 可能性は低い。
_ANTHROPIC_DEFAULT_OUTPUT_LIMIT = 128_000


def _get_anthropic_max_output(model: str) -> int:
    """Anthropic モデルの最大出力トークン制限を検索する。

    _ANTHROPIC_OUTPUT_LIMITS に対して部分文字列マッチングを使用するため、
    日付付きモデル ID（claude-sonnet-4-5-20250929）やバリアントサフィックス
    (:1m, :fast）も正しく解決できる。最長プレフィックスが優先（例: "claude-3-5" が
    "claude-3-5-sonnet" より先にマッチしないよう）。

    ``anthropic/claude-opus-4.6`` のようなモデル名が
    ``claude-opus-4-6`` テーブルキーにマッチするようドットをハイフンに正規化する。
    """
    m = model.lower().replace(".", "-")
    best_key = ""
    best_val = _ANTHROPIC_DEFAULT_OUTPUT_LIMIT
    for key, val in _ANTHROPIC_OUTPUT_LIMITS.items():
        if key in m and len(key) > len(best_key):
            best_key = key
            best_val = val
    return best_val


def _resolve_positive_anthropic_max_tokens(value) -> Optional[int]:
    """``value`` を正の整数に丸めて返す。有限の正の数でなければ ``None`` を返す。
    openclaw/openclaw#66664 からの移植。

    Anthropic の Messages API は ``max_tokens`` が 0・負・非整数・非有限の場合に
    HTTP 400 を返す。Python の ``or`` イディオム（``max_tokens or fallback``）は
    ``0`` を正しく捕捉するが、負の整数や小数（``-1``, ``0.5``）はそのまま
    API に渡してしまい、ローカルエラーではなくユーザー可視のエラーを引き起こす。
    """
    # bool は int のサブクラスなので明示的に除外する。
    # ``True`` が 1 に、``False`` が 0 にサイレント変換されないようにするため。
    if isinstance(value, bool):
        return None
    if not isinstance(value, (int, float)):
        return None
    try:
        import math
        if not math.isfinite(value):
            return None
    except Exception:
        return None
    floored = int(value)  # truncates toward zero for floats
    return floored if floored > 0 else None


def _resolve_anthropic_messages_max_tokens(
    requested,
    model: str,
    context_length: Optional[int] = None,
) -> int:
    """Anthropic Messages 呼び出しの ``max_tokens`` バジェットを解決する。

    ``requested`` が正の有限数の場合はそれを優先し、そうでなければ
    モデルの出力上限にフォールバックする。正のバジェットが解決できない場合は
    ``ValueError`` を発生させる（現在のモデルテーブルデフォルトでは発生しないはずだが、
    将来的に ``_get_anthropic_max_output`` が ``0`` を返すリグレッションを防ぐため）。

    コンテキストウィンドウのクランプは呼び出し側が行う — このリゾルバーは
    正値契約をエンドポイント固有のロジックと分離するため、クランプしない。

    openclaw/openclaw#66664 (resolveAnthropicMessagesMaxTokens) からの移植。
    """
    resolved = _resolve_positive_anthropic_max_tokens(requested)
    if resolved is not None:
        return resolved
    fallback = _get_anthropic_max_output(model)
    if fallback > 0:
        return fallback
    raise ValueError(
        f"Anthropic Messages adapter requires a positive max_tokens value for "
        f"model {model!r}; got {requested!r} and no model default resolved."
    )


def _supports_adaptive_thinking(model: str) -> bool:
    """適応的思考をサポートする Claude 4.6+ モデルの場合 True を返す。"""
    return any(v in model for v in _ADAPTIVE_THINKING_SUBSTRINGS)


def _supports_xhigh_effort(model: str) -> bool:
    """'xhigh' 適応的 effort レベルを受け入れるモデルの場合 True を返す。

    Opus 4.7 で xhigh が high と max の間の独立したレベルとして導入された。
    4.7 以前の適応型モデル（Opus/Sonnet 4.6）は low/medium/high/max のみ受け付け、
    xhigh は HTTP 400 で拒否される。False の場合、呼び出し側は xhigh→max にダウングレードすること。
    """
    return any(v in model for v in _XHIGH_EFFORT_SUBSTRINGS)


def _forbids_sampling_params(model: str) -> bool:
    """デフォルト以外の temperature/top_p/top_k で 400 を返すモデルの場合 True を返す。

    Opus 4.7 はサンプリングパラメーターを明示的に拒否する; 後続の Claude リリースも
    同様の動作が予想される。呼び出し側はゼロ/デフォルト値を渡すのではなく
    これらのフィールドを完全に省略すること（API は null 以外を拒否する）。
    """
    return any(v in model for v in _NO_SAMPLING_PARAMS_SUBSTRINGS)


# 拡張機能用の Beta ヘッダー（全認証タイプで送信）。
# Opus 4.7 (2026-04-16) 時点で最初の 2 つは Claude 4.6+ で GA —
# Beta ヘッダーは引き続き受け付けられる（無害な no-op）が必須ではない。
# 古い Claude (4.5, 4.1) + ヘッダーでゲートされているサードパーティ
# Anthropic 互換エンドポイントが拡張機能を使い続けられるよう残している。
#
# ``context-1m-2025-08-07`` は AWS Bedrock または Azure AI Foundry 経由で提供される
# Claude Opus 4.6/4.7 と Sonnet 4.6 の 1M コンテキストウィンドウを解放する。
# 1M はネイティブ Anthropic (api.anthropic.com) では Opus 4.6+ で GA だが、
# Bedrock/Azure は 2026-04 時点でこの Beta ヘッダーでゲートしている —
# これなしでは model_metadata.py が 1M と表示しても Bedrock は Opus を 200K に制限する。
# ヘッダーは 1M が GA のエンドポイントでは無害な no-op。
#
# 移行ガイド: ≤4.5 モデルをサポートしなくなった場合、または Bedrock/Azure が
# 1M を GA に昇格させた場合はこれらを削除すること。
_COMMON_BETAS = [
    "interleaved-thinking-2025-05-14",
    "fine-grained-tool-streaming-2025-05-14",
    "context-1m-2025-08-07",
]
# MiniMax の Anthropic 互換エンドポイントは fine-grained tool streaming beta が
# 存在するとツール使用リクエストに失敗する。ツール呼び出しがプロバイダーの
# デフォルトレスポンスパスにフォールバックするよう省略する。
_TOOL_STREAMING_BETA = "fine-grained-tool-streaming-2025-05-14"
# 1M コンテキスト beta — _COMMON_BETAS のコメント参照。Bearer 認証（MiniMax）
# エンドポイントでは、独自モデルをホストしており、不明な Anthropic beta ヘッダーが
# リクエスト拒否のリスクがあるため除外する。
_CONTEXT_1M_BETA = "context-1m-2025-08-07"

# Fast モード beta — Opus 4.6 で出力トークンスループットを大幅に向上させる
# ``speed: "fast"`` リクエストパラメーターを有効化（~2.5x）。
# 参照: https://platform.claude.com/docs/en/build-with-claude/fast-mode
_FAST_MODE_BETA = "fast-mode-2026-02-01"

# OAuth/サブスクリプション認証に必要な追加 beta ヘッダー。
# Claude Code（および pi-ai / OpenCode）が送信する内容と一致する。
_OAUTH_ONLY_BETAS = [
    "claude-code-20250219",
    "oauth-2025-04-20",
]

# Claude Code バージョン — OAuth トークン交換・リフレッシュリクエスト
# (platform.claude.com/v1/oauth/token) のクライアント user-agent として送信する。
# Anthropic の OAuth フローは UA を検証し、古すぎるバージョンのリクエストを拒否する
# 可能性があるため、動的に検出することで現行の Claude Code インストールがログイン・
# リフレッシュ中に古バージョンエラーに遭遇しないようにする。
_CLAUDE_CODE_VERSION_FALLBACK = "2.1.74"
_claude_code_version_cache: Optional[str] = None


def _detect_claude_code_version() -> str:
    """インストール済み Claude Code のバージョンを検出し、静的定数にフォールバックする。

    OAuth トークン交換・リフレッシュフロー
    (``platform.claude.com/v1/oauth/token``) でのみ使用される。
    Messages API クライアントは claude-cli user-agent を送信しなくなった。
    """
    import subprocess as _sp

    for cmd in ("claude", "claude-code"):
        try:
            result = _sp.run(
                [cmd, "--version"],
                capture_output=True, text=True, timeout=5,
            )
            if result.returncode == 0 and result.stdout.strip():
                # Output is like "2.1.74 (Claude Code)" or just "2.1.74"
                version = result.stdout.strip().split()[0]
                if version and version[0].isdigit():
                    return version
        except Exception:
            pass
    return _CLAUDE_CODE_VERSION_FALLBACK


def _get_claude_code_version() -> str:
    """OAuth フローヘッダー用にインストール済み Claude Code バージョンを遅延検出する。

    OAuth トークン交換・リフレッシュエンドポイント
    (``platform.claude.com/v1/oauth/token``) でのみ使用される。
    Messages API クライアントは claude-cli user-agent を送信しない。
    """
    global _claude_code_version_cache
    if _claude_code_version_cache is None:
        _claude_code_version_cache = _detect_claude_code_version()
    return _claude_code_version_cache


def _is_oauth_token(key: str) -> bool:
    """キーが Anthropic OAuth/セットアップトークンかどうかを確認する。

    キー形式で Anthropic OAuth トークンを識別する:
    - ``sk-ant-`` プレフィックス（``sk-ant-api`` 以外）→ セットアップトークン・管理キー
    - ``eyJ`` プレフィックス → Anthropic OAuth フローからの JWT
    - ``cc-`` プレフィックス → Claude Code OAuth アクセストークン（CLAUDE_CODE_OAUTH_TOKEN から）

    非 Anthropic キー（MiniMax, Alibaba 等）はどのパターンにもマッチせず
    正しく False を返す。
    """
    if not key:
        return False
    # 通常の Anthropic Console API キー — x-api-key 認証、OAuth ではない
    if key.startswith("sk-ant-api"):
        return False
    # Anthropic 発行のトークン（セットアップトークン sk-ant-oat-*、管理キー）
    if key.startswith("sk-ant-"):
        return True
    # Anthropic OAuth フローからの JWT
    if key.startswith("eyJ"):
        return True
    # Claude Code OAuth アクセストークン（不透明、CLAUDE_CODE_OAUTH_TOKEN から）
    if key.startswith("cc-"):
        return True
    return False


def _normalize_base_url_text(base_url) -> str:
    """SDK/ベーストランスポートの URL 値を検査用のプレーン文字列に正規化する。

    一部のクライアントオブジェクトは ``base_url`` を生の文字列ではなく
    ``httpx.URL`` として公開する。プロバイダー/認証検出はどちらの形式も受け入れる必要がある。
    """
    if not base_url:
        return ""
    return str(base_url).strip()


def _is_third_party_anthropic_endpoint(base_url: str | None) -> bool:
    """Anthropic Messages API を使用する非 Anthropic エンドポイントの場合 True を返す。

    サードパーティプロキシ（Azure AI Foundry, AWS Bedrock, セルフホスト）は
    Anthropic OAuth トークンではなく x-api-key で独自の API キーを使用して認証する。
    これらのエンドポイントでは OAuth 検出をスキップする必要がある。
    """
    normalized = _normalize_base_url_text(base_url)
    if not normalized:
        return False  # No base_url = direct Anthropic API
    normalized = normalized.rstrip("/").lower()
    if "anthropic.com" in normalized:
        return False  # Direct Anthropic API — OAuth applies
    return True  # Any other endpoint is a third-party proxy


def _is_kimi_coding_endpoint(base_url: str | None) -> bool:
    """claude-code UA が必要な Kimi の /coding エンドポイントの場合 True を返す。"""
    normalized = _normalize_base_url_text(base_url)
    if not normalized:
        return False
    return normalized.rstrip("/").lower().startswith("https://api.kimi.com/coding")


def _requires_bearer_auth(base_url: str | None) -> bool:
    """Bearer 認証が必要な Anthropic 互換プロバイダーの場合 True を返す。

    一部のサードパーティ /anthropic エンドポイントは Anthropic の Messages API を
    実装しているが、Anthropic ネイティブの x-api-key ヘッダーではなく
    Authorization: Bearer *** を要求する。MiniMax のグローバルと中国の
    Anthropic 互換エンドポイントがこのパターンに従う。
    """
    normalized = _normalize_base_url_text(base_url)
    if not normalized:
        return False
    normalized = normalized.rstrip("/").lower()
    return normalized.startswith(("https://api.minimax.io/anthropic", "https://api.minimaxi.com/anthropic"))


def _common_betas_for_base_url(base_url: str | None) -> list[str]:
    """設定されたエンドポイントに対して安全な beta ヘッダーを返す。

    MiniMax の Anthropic 互換エンドポイント（Bearer 認証）は Anthropic の
    ``fine-grained-tool-streaming`` beta を含むリクエストを拒否する —
    すべてのツール使用メッセージが接続エラーを引き起こす。
    Bearer 認証エンドポイントではこの beta を除去し、他の beta はそのまま保持する。

    ``context-1m-2025-08-07`` beta も Bearer 認証エンドポイントでは除去する —
    MiniMax は Claude ではなく独自モデルをホストしているため、このヘッダーは
    最良でも無関係、最悪はリクエスト拒否のリスクがある。
    """
    if _requires_bearer_auth(base_url):
        _stripped = {_TOOL_STREAMING_BETA, _CONTEXT_1M_BETA}
        return [b for b in _COMMON_BETAS if b not in _stripped]
    return _COMMON_BETAS


def build_anthropic_client(api_key: str, base_url: str = None, timeout: float = None):
    """Anthropic クライアントを作成し、セットアップトークンと API キーを自動検出する。

    *timeout* が指定された場合、デフォルトの 900 秒読み取りタイムアウトを上書きする。
    接続タイムアウトは 10 秒のまま。呼び出し側はプロバイダー/モデルごとの
    ``request_timeout_seconds`` 設定からこれを渡すため、Anthropic ネイティブと
    Anthropic 互換プロバイダーは OpenAI ワイアプロバイダーと同じパラメーターを尊重する。

    anthropic.Anthropic インスタンスを返す。
    """
    _anthropic_sdk = _get_anthropic_sdk()
    if _anthropic_sdk is None:
        raise ImportError(
            "The 'anthropic' package is required for the Anthropic provider. "
            "Install it with: pip install 'anthropic>=0.39.0'"
        )

    normalize_proxy_env_vars()

    from httpx import Timeout

    normalized_base_url = _normalize_base_url_text(base_url)
    _read_timeout = timeout if (isinstance(timeout, (int, float)) and timeout > 0) else 900.0
    kwargs = {
        "timeout": Timeout(timeout=float(_read_timeout), connect=10.0),
    }
    if normalized_base_url:
        # Azure Anthropic endpoints require an ``api-version`` query parameter.
        # Pass it via default_query so the SDK appends it to every request URL
        # without corrupting the base_url (appending it directly produces
        # malformed paths like /anthropic?api-version=.../v1/messages).
        _is_azure_endpoint = "azure.com" in normalized_base_url.lower()
        if _is_azure_endpoint and "api-version" not in normalized_base_url:
            kwargs["base_url"] = normalized_base_url.rstrip("/")
            kwargs["default_query"] = {"api-version": "2025-04-15"}
        else:
            kwargs["base_url"] = normalized_base_url
    common_betas = _common_betas_for_base_url(normalized_base_url)

    if _is_kimi_coding_endpoint(base_url):
        # Kimi's /coding endpoint requires User-Agent: claude-code/0.1.0
        # to be recognized as a valid Coding Agent. Without it, returns 403.
        # Check this BEFORE _requires_bearer_auth since both match api.kimi.com/coding.
        kwargs["api_key"] = api_key
        kwargs["default_headers"] = {
            "User-Agent": "claude-code/0.1.0",
            **( {"anthropic-beta": ",".join(common_betas)} if common_betas else {} )
        }
    elif _requires_bearer_auth(normalized_base_url):
        # Some Anthropic-compatible providers (e.g. MiniMax) expect the API key in
        # Authorization: Bearer *** for regular API keys. Route those endpoints
        # through auth_token so the SDK sends Bearer auth instead of x-api-key.
        # Check this before OAuth token shape detection because MiniMax secrets do
        # not use Anthropic's sk-ant-api prefix and would otherwise be misread as
        # Anthropic OAuth/setup tokens.
        kwargs["auth_token"] = api_key
        if common_betas:
            kwargs["default_headers"] = {"anthropic-beta": ",".join(common_betas)}
    elif _is_third_party_anthropic_endpoint(base_url):
        # Third-party proxies (Azure AI Foundry, AWS Bedrock, etc.) use their
        # own API keys with x-api-key auth. Skip OAuth detection — their keys
        # don't follow Anthropic's sk-ant-* prefix convention and would be
        # misclassified as OAuth tokens.
        kwargs["api_key"] = api_key
        if common_betas:
            kwargs["default_headers"] = {"anthropic-beta": ",".join(common_betas)}
    elif _is_oauth_token(api_key):
        # OAuth access token / setup-token → Bearer auth + OAuth-only betas.
        # The OAuth-specific beta headers are still required by Anthropic's
        # OAuth-gated Messages API path; the Claude Code user-agent / x-app
        # spoofing is deliberately NOT sent — Hermes identifies as itself.
        #
        # ``context-1m-2025-08-07`` is stripped here: Anthropic rejects
        # OAuth requests that carry it with
        #   "This authentication style is incompatible with the long
        #    context beta header."
        # Subscription-gated OAuth traffic gets the 200K default window.
        oauth_safe_common = [b for b in common_betas if b != _CONTEXT_1M_BETA]
        all_betas = oauth_safe_common + _OAUTH_ONLY_BETAS
        kwargs["auth_token"] = api_key
        kwargs["default_headers"] = {
            "anthropic-beta": ",".join(all_betas),
        }
    else:
        # Regular API key → x-api-key header + common betas
        kwargs["api_key"] = api_key
        if common_betas:
            kwargs["default_headers"] = {"anthropic-beta": ",".join(common_betas)}

    return _anthropic_sdk.Anthropic(**kwargs)


def build_anthropic_bedrock_client(region: str):
    """Bedrock Claude モデル用の AnthropicBedrock クライアントを作成する。

    Anthropic SDK のネイティブ Bedrock アダプターを使用し、完全な
    Claude 機能パリティを提供する: プロンプトキャッシュ、思考バジェット、
    適応的思考、高速モード — Converse API では利用できない機能。

    Bedrock ホスト Claude モデルがネイティブ Anthropic と同じ拡張機能を
    得られるよう、共通 Anthropic beta ヘッダーをクライアントレベルの
    デフォルトとして設定する。特に ``context-1m-2025-08-07`` beta は
    Bedrock 上の Opus 4.6/4.7 の 1M コンテキストウィンドウを解放する —
    これなしでは、Anthropic API がネイティブで 1M を提供していても
    Bedrock はこれらのモデルを 200K に制限する。

    認証には boto3 のデフォルト認証チェーン（IAM ロール、SSO、環境変数）を使用する。
    """
    _anthropic_sdk = _get_anthropic_sdk()
    if _anthropic_sdk is None:
        raise ImportError(
            "The 'anthropic' package is required for the Bedrock provider. "
            "Install it with: pip install 'anthropic>=0.39.0'"
        )
    if not hasattr(_anthropic_sdk, "AnthropicBedrock"):
        raise ImportError(
            "anthropic.AnthropicBedrock not available. "
            "Upgrade with: pip install 'anthropic>=0.39.0'"
        )
    from httpx import Timeout

    return _anthropic_sdk.AnthropicBedrock(
        aws_region=region,
        timeout=Timeout(timeout=900.0, connect=10.0),
        default_headers={"anthropic-beta": ",".join(_COMMON_BETAS)},
    )


def _read_claude_code_credentials_from_keychain() -> Optional[Dict[str, Any]]:
    """macOS キーチェーンから Claude Code OAuth 資格情報を読み込む。

    Claude Code >=2.1.114 は、~/.claude/.credentials.json の JSON ファイルではなく
    （または加えて）、サービス名 "Claude Code-credentials" の下の macOS キーチェーンに
    資格情報を保存する。

    パスワードフィールドには JSON ファイルと同じ claudeAiOauth 構造の
    JSON 文字列が含まれる。

    {accessToken, refreshToken?, expiresAt?} の dict または None を返す。
    """
    if platform.system() != "Darwin":
        return None

    try:
        # Read the "Claude Code-credentials" generic password entry
        result = subprocess.run(
            ["security", "find-generic-password",
             "-s", "Claude Code-credentials",
             "-w"],
            capture_output=True,
            text=True,
            timeout=5,
        )
    except (OSError, subprocess.TimeoutExpired):
        logger.debug("Keychain: security command not available or timed out")
        return None

    if result.returncode != 0:
        logger.debug("Keychain: no entry found for 'Claude Code-credentials'")
        return None

    raw = result.stdout.strip()
    if not raw:
        return None

    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        logger.debug("Keychain: credentials payload is not valid JSON")
        return None

    oauth_data = data.get("claudeAiOauth")
    if oauth_data and isinstance(oauth_data, dict):
        access_token = oauth_data.get("accessToken", "")
        if access_token:
            return {
                "accessToken": access_token,
                "refreshToken": oauth_data.get("refreshToken", ""),
                "expiresAt": oauth_data.get("expiresAt", 0),
                "source": "macos_keychain",
            }

    return None


def read_claude_code_credentials() -> Optional[Dict[str, Any]]:
    """リフレッシュ可能な Claude Code OAuth 資格情報を読み込む。

    2 つのソースを順番に確認する:
      1. macOS キーチェーン（Darwin のみ）— "Claude Code-credentials" エントリ
      2. ~/.claude/.credentials.json ファイル

    これは意図的に ~/.claude.json の primaryApiKey を除外している。Opencode の
    サブスクリプションフローはリフレッシュ可能な資格情報による OAuth/セットアップ
    トークンベースであり、ネイティブ直接 Anthropic プロバイダーの使用は
    Claude のファーストパーティ管理キーを自動検出するのではなく、
    そのパスに従う必要がある。

    {accessToken, refreshToken?, expiresAt?} の dict または None を返す。
    """
    # Try macOS Keychain first (covers Claude Code >=2.1.114)
    kc_creds = _read_claude_code_credentials_from_keychain()
    if kc_creds:
        return kc_creds

    # Fall back to JSON file
    cred_path = Path.home() / ".claude" / ".credentials.json"
    if cred_path.exists():
        try:
            data = json.loads(cred_path.read_text(encoding="utf-8"))
            oauth_data = data.get("claudeAiOauth")
            if oauth_data and isinstance(oauth_data, dict):
                access_token = oauth_data.get("accessToken", "")
                if access_token:
                    return {
                        "accessToken": access_token,
                        "refreshToken": oauth_data.get("refreshToken", ""),
                        "expiresAt": oauth_data.get("expiresAt", 0),
                        "source": "claude_code_credentials_file",
                    }
        except (json.JSONDecodeError, OSError, IOError) as e:
            logger.debug("Failed to read ~/.claude/.credentials.json: %s", e)

    return None


def read_claude_managed_key() -> Optional[str]:
    """診断目的のみで ~/.claude.json から Claude のネイティブ管理キーを読み込む。"""
    claude_json = Path.home() / ".claude.json"
    if claude_json.exists():
        try:
            data = json.loads(claude_json.read_text(encoding="utf-8"))
            primary_key = data.get("primaryApiKey", "")
            if isinstance(primary_key, str) and primary_key.strip():
                return primary_key.strip()
        except (json.JSONDecodeError, OSError, IOError) as e:
            logger.debug("Failed to read ~/.claude.json: %s", e)
    return None


def is_claude_code_token_valid(creds: Dict[str, Any]) -> bool:
    """Claude Code 資格情報に期限切れでないアクセストークンがあるか確認する。"""
    import time

    expires_at = creds.get("expiresAt", 0)
    if not expires_at:
        # No expiry set (managed keys) — valid if token is present
        return bool(creds.get("accessToken"))

    # expiresAt is in milliseconds since epoch
    now_ms = int(time.time() * 1000)
    # Allow 60 seconds of buffer
    return now_ms < (expires_at - 60_000)


def refresh_anthropic_oauth_pure(refresh_token: str, *, use_json: bool = False) -> Dict[str, Any]:
    """ローカルの資格情報ファイルを変更せずに Anthropic OAuth トークンをリフレッシュする。"""
    import time
    import urllib.parse
    import urllib.request

    if not refresh_token:
        raise ValueError("refresh_token is required")

    client_id = "9d1c250a-e61b-44d9-88ed-5944d1962f5e"
    if use_json:
        data = json.dumps({
            "grant_type": "refresh_token",
            "refresh_token": refresh_token,
            "client_id": client_id,
        }).encode()
        content_type = "application/json"
    else:
        data = urllib.parse.urlencode({
            "grant_type": "refresh_token",
            "refresh_token": refresh_token,
            "client_id": client_id,
        }).encode()
        content_type = "application/x-www-form-urlencoded"

    token_endpoints = [
        "https://platform.claude.com/v1/oauth/token",
        "https://console.anthropic.com/v1/oauth/token",
    ]
    last_error = None
    for endpoint in token_endpoints:
        req = urllib.request.Request(
            endpoint,
            data=data,
            headers={
                "Content-Type": content_type,
                "User-Agent": f"claude-cli/{_get_claude_code_version()} (external, cli)",
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=10) as resp:
                result = json.loads(resp.read().decode())
        except Exception as exc:
            last_error = exc
            logger.debug("Anthropic token refresh failed at %s: %s", endpoint, exc)
            continue

        access_token = result.get("access_token", "")
        if not access_token:
            raise ValueError("Anthropic refresh response was missing access_token")
        next_refresh = result.get("refresh_token", refresh_token)
        expires_in = result.get("expires_in", 3600)
        return {
            "access_token": access_token,
            "refresh_token": next_refresh,
            "expires_at_ms": int(time.time() * 1000) + (expires_in * 1000),
        }

    if last_error is not None:
        raise last_error
    raise ValueError("Anthropic token refresh failed")


def _refresh_oauth_token(creds: Dict[str, Any]) -> Optional[str]:
    """期限切れの Claude Code OAuth トークンのリフレッシュを試みる。"""
    refresh_token = creds.get("refreshToken", "")
    if not refresh_token:
        logger.debug("No refresh token available — cannot refresh")
        return None

    try:
        refreshed = refresh_anthropic_oauth_pure(refresh_token, use_json=False)
        _write_claude_code_credentials(
            refreshed["access_token"],
            refreshed["refresh_token"],
            refreshed["expires_at_ms"],
        )
        logger.debug("Successfully refreshed Claude Code OAuth token")
        return refreshed["access_token"]
    except Exception as e:
        logger.debug("Failed to refresh Claude Code token: %s", e)
        return None


def _write_claude_code_credentials(
    access_token: str,
    refresh_token: str,
    expires_at_ms: int,
    *,
    scopes: Optional[list] = None,
) -> None:
    """リフレッシュされた資格情報を ~/.claude/.credentials.json に書き戻す。

    オプションの *scopes* リスト（例: ``["user:inference", "user:profile", ...]``）は
    Claude Code 自身の認証チェックが資格情報を有効と認識できるよう永続化される。
    Claude Code >=2.1.81 はトークンを使用する前に保存されたスコープに
    ``"user:inference"`` が含まれているかをゲートとしてチェックする。
    """
    cred_path = Path.home() / ".claude" / ".credentials.json"
    try:
        # Read existing file to preserve other fields
        existing = {}
        if cred_path.exists():
            existing = json.loads(cred_path.read_text(encoding="utf-8"))

        oauth_data: Dict[str, Any] = {
            "accessToken": access_token,
            "refreshToken": refresh_token,
            "expiresAt": expires_at_ms,
        }
        if scopes is not None:
            oauth_data["scopes"] = scopes
        elif "claudeAiOauth" in existing and "scopes" in existing["claudeAiOauth"]:
            # Preserve previously-stored scopes when the refresh response
            # does not include a scope field.
            oauth_data["scopes"] = existing["claudeAiOauth"]["scopes"]

        existing["claudeAiOauth"] = oauth_data

        cred_path.parent.mkdir(parents=True, exist_ok=True)
        _tmp_cred = cred_path.with_suffix(".tmp")
        _tmp_cred.write_text(json.dumps(existing, indent=2), encoding="utf-8")
        _tmp_cred.replace(cred_path)
        # パーミッション制限（資格情報ファイル）— Unix 系のみ有効
        if hasattr(cred_path, "chmod"):
            try:
                cred_path.chmod(0o600)
            except (OSError, NotImplementedError):
                pass  # Windows ではパーミッション設定をスキップ
    except (OSError, IOError) as e:
        logger.debug("Failed to write refreshed credentials: %s", e)


def _resolve_claude_code_token_from_credentials(creds: Optional[Dict[str, Any]] = None) -> Optional[str]:
    """Claude Code 資格情報ファイルからトークンを解決する。必要に応じてリフレッシュする。"""
    creds = creds or read_claude_code_credentials()
    if creds and is_claude_code_token_valid(creds):
        logger.debug("Using Claude Code credentials (auto-detected)")
        return creds["accessToken"]
    if creds:
        logger.debug("Claude Code credentials expired — attempting refresh")
        refreshed = _refresh_oauth_token(creds)
        if refreshed:
            return refreshed
        logger.debug("Token refresh failed — re-run 'claude setup-token' to reauthenticate")
    return None


def _prefer_refreshable_claude_code_token(env_token: str, creds: Optional[Dict[str, Any]]) -> Optional[str]:
    """永続化された env OAuth トークンがリフレッシュを妨げる場合、Claude Code 資格情報を優先する。

    Hermes は歴史的にセットアップトークンを ANTHROPIC_TOKEN に永続化してきた。
    これにより、静的 env トークンが Claude Code のリフレッシュ可能な資格情報ファイルを
    確認する前に優先されるため、後でリフレッシュができなくなる。
    リフレッシュ可能な Claude Code 資格情報レコードがある場合は、
    静的 env OAuth トークンよりも優先する。
    """
    if not env_token or not _is_oauth_token(env_token) or not isinstance(creds, dict):
        return None
    if not creds.get("refreshToken"):
        return None

    resolved = _resolve_claude_code_token_from_credentials(creds)
    if resolved and resolved != env_token:
        logger.debug(
            "Preferring Claude Code credential file over static env OAuth token so refresh can proceed"
        )
        return resolved
    return None


def resolve_anthropic_token() -> Optional[str]:
    """利用可能なすべてのソースから Anthropic トークンを解決する。

    優先順位:
      1. Hermes 資格情報プール（``~/.hermes/auth.json`` →
         ``credential_pool.anthropic``）— Hermes 独自の PKCE ログインフローで
         発行された OAuth トークン。期限切れ近くのエントリは自動リフレッシュされる。
         env ソースのプールエントリ（``source="env:..."``）は、以下の env-var
         優先ロジックが実行できるようここでスキップする。
      2. ANTHROPIC_TOKEN 環境変数（Hermes が保存した OAuth/セットアップトークン）
      3. CLAUDE_CODE_OAUTH_TOKEN 環境変数
      4. Claude Code 資格情報（~/.claude.json または ~/.claude/.credentials.json）
         — 期限切れかつリフレッシュトークンが利用可能な場合は自動リフレッシュ
      5. ANTHROPIC_API_KEY 環境変数（通常の API キー、またはレガシーフォールバック）

    トークン文字列または None を返す。
    """
    # 1. Hermes credential pool — the live source of truth for tokens
    #    minted via ``hermes login anthropic`` / the dashboard PKCE flow.
    #    ``select()`` picks the best available entry and refreshes it if
    #    it's near expiry, so callers always get a fresh token.
    #
    #    Skip env-sourced pool entries (``env:ANTHROPIC_TOKEN``, etc.) —
    #    those are passthroughs of the env var, and the env-var branches
    #    below have richer priority logic (``_prefer_refreshable_claude_code_token``)
    #    that can upgrade a static env OAuth token to a refreshed
    #    Claude Code token. Letting the pool win here would short-circuit
    #    that upgrade.
    try:
        from core.credential_pool import load_pool
        pool = load_pool("anthropic")
        entry = pool.select()
        if entry and entry.access_token and not entry.source.startswith("env:"):
            return entry.access_token
    except Exception as exc:
        # Pool lookup is best-effort — fall through to env/file sources
        # if anything goes wrong (e.g. auth.json corruption during a
        # concurrent write).
        logger.debug("Credential-pool lookup failed for anthropic: %s", exc)

    creds = read_claude_code_credentials()

    # 2. Hermes-managed OAuth/setup token env var
    token = os.getenv("ANTHROPIC_TOKEN", "").strip()
    if token:
        preferred = _prefer_refreshable_claude_code_token(token, creds)
        if preferred:
            return preferred
        return token

    # 3. CLAUDE_CODE_OAUTH_TOKEN (used by Claude Code for setup-tokens)
    cc_token = os.getenv("CLAUDE_CODE_OAUTH_TOKEN", "").strip()
    if cc_token:
        preferred = _prefer_refreshable_claude_code_token(cc_token, creds)
        if preferred:
            return preferred
        return cc_token

    # 4. Claude Code credential file
    resolved_claude_token = _resolve_claude_code_token_from_credentials(creds)
    if resolved_claude_token:
        return resolved_claude_token

    # 5. Regular API key, or a legacy OAuth token saved in ANTHROPIC_API_KEY.
    # This remains as a compatibility fallback for pre-migration Hermes configs.
    api_key = os.getenv("ANTHROPIC_API_KEY", "").strip()
    if api_key:
        return api_key

    return None


def run_oauth_setup_token() -> Optional[str]:
    """'claude setup-token' をインタラクティブに実行し、生成されたトークンを返す。

    サブプロセス完了後に複数のソースを確認する:
      1. Claude Code 資格情報ファイル（サブプロセスによって書き込まれる可能性がある）
      2. CLAUDE_CODE_OAUTH_TOKEN / ANTHROPIC_TOKEN 環境変数

    トークン文字列を返す。資格情報が取得できなかった場合は None。
    'claude' CLI がインストールされていない場合は FileNotFoundError を発生させる。
    """
    import shutil
    import subprocess

    claude_path = shutil.which("claude")
    if not claude_path:
        raise FileNotFoundError(
            "The 'claude' CLI is not installed. "
            "Install it with: npm install -g @anthropic-ai/claude-code"
        )

    # Run interactively — stdin/stdout/stderr inherited so user can interact
    try:
        subprocess.run([claude_path, "setup-token"])
    except (KeyboardInterrupt, EOFError):
        return None

    # Check if credentials were saved to Claude Code's config files
    creds = read_claude_code_credentials()
    if creds and is_claude_code_token_valid(creds):
        return creds["accessToken"]

    # Check env vars that may have been set
    for env_var in ("CLAUDE_CODE_OAUTH_TOKEN", "ANTHROPIC_TOKEN"):
        val = os.getenv(env_var, "").strip()
        if val:
            return val

    return None


# ── Hermes ネイティブ PKCE OAuth フロー ──────────────────────────────────
# Claude Code、pi-ai、OpenCode が使用するフローをミラーリングする。
# 資格情報を ~/.hermes/.anthropic_oauth.json（独自ファイル）に保存する。

_OAUTH_CLIENT_ID = "9d1c250a-e61b-44d9-88ed-5944d1962f5e"
_OAUTH_TOKEN_URL = "https://console.anthropic.com/v1/oauth/token"
_OAUTH_REDIRECT_URI = "https://console.anthropic.com/oauth/code/callback"
_OAUTH_SCOPES = "org:create_api_key user:profile user:inference"
_HERMES_OAUTH_FILE = get_hermes_home() / ".anthropic_oauth.json"


def _generate_pkce() -> tuple:
    """PKCE の code_verifier と code_challenge (S256) を生成する。"""
    import base64
    import hashlib
    import secrets

    verifier = base64.urlsafe_b64encode(secrets.token_bytes(32)).rstrip(b"=").decode()
    challenge = base64.urlsafe_b64encode(
        hashlib.sha256(verifier.encode()).digest()
    ).rstrip(b"=").decode()
    return verifier, challenge


def run_hermes_oauth_login_pure() -> Optional[Dict[str, Any]]:
    """Hermes ネイティブ OAuth PKCE フローを実行し、資格情報の状態を返す。"""
    import time
    import webbrowser

    verifier, challenge = _generate_pkce()

    params = {
        "code": "true",
        "client_id": _OAUTH_CLIENT_ID,
        "response_type": "code",
        "redirect_uri": _OAUTH_REDIRECT_URI,
        "scope": _OAUTH_SCOPES,
        "code_challenge": challenge,
        "code_challenge_method": "S256",
        "state": verifier,
    }
    from urllib.parse import urlencode

    auth_url = f"https://claude.ai/oauth/authorize?{urlencode(params)}"

    print()
    print("Authorize Hermes with your Claude Pro/Max subscription.")
    print()
    print("╭─ Claude Pro/Max Authorization ────────────────────╮")
    print("│                                                   │")
    print("│  Open this link in your browser:                  │")
    print("╰───────────────────────────────────────────────────╯")
    print()
    print(f"  {auth_url}")
    print()

    try:
        webbrowser.open(auth_url)
        print("  (Browser opened automatically)")
    except Exception:
        pass

    print()
    print("After authorizing, you'll see a code. Paste it below.")
    print()
    try:
        auth_code = input("Authorization code: ").strip()
    except (KeyboardInterrupt, EOFError):
        return None

    if not auth_code:
        print("No code entered.")
        return None

    splits = auth_code.split("#")
    code = splits[0]
    state = splits[1] if len(splits) > 1 else ""

    try:
        import urllib.request

        exchange_data = json.dumps({
            "grant_type": "authorization_code",
            "client_id": _OAUTH_CLIENT_ID,
            "code": code,
            "state": state,
            "redirect_uri": _OAUTH_REDIRECT_URI,
            "code_verifier": verifier,
        }).encode()

        req = urllib.request.Request(
            _OAUTH_TOKEN_URL,
            data=exchange_data,
            headers={
                "Content-Type": "application/json",
                "User-Agent": f"claude-cli/{_get_claude_code_version()} (external, cli)",
            },
            method="POST",
        )

        with urllib.request.urlopen(req, timeout=15) as resp:
            result = json.loads(resp.read().decode())
    except Exception as e:
        print(f"Token exchange failed: {e}")
        return None

    access_token = result.get("access_token", "")
    refresh_token = result.get("refresh_token", "")
    expires_in = result.get("expires_in", 3600)

    if not access_token:
        print("No access token in response.")
        return None

    expires_at_ms = int(time.time() * 1000) + (expires_in * 1000)
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "expires_at_ms": expires_at_ms,
    }


def read_hermes_oauth_credentials() -> Optional[Dict[str, Any]]:
    """~/.hermes/.anthropic_oauth.json から Hermes 管理 OAuth 資格情報を読み込む。"""
    if _HERMES_OAUTH_FILE.exists():
        try:
            data = json.loads(_HERMES_OAUTH_FILE.read_text(encoding="utf-8"))
            if data.get("accessToken"):
                return data
        except (json.JSONDecodeError, OSError, IOError) as e:
            logger.debug("Failed to read Hermes OAuth credentials: %s", e)
    return None


# ---------------------------------------------------------------------------
# メッセージ / ツール / レスポンス形式変換
# ---------------------------------------------------------------------------


def _is_bedrock_model_id(model: str) -> bool:
    """ネームスペース区切り文字としてドットを使用する AWS Bedrock モデル ID を検出する。

    Bedrock モデル ID は 2 つの形式がある:
    - ベア形式:    ``anthropic.claude-opus-4-7``
    - リージョン形式（推論プロファイル）: ``us.anthropic.claude-sonnet-4-5-v1:0``

    どちらの場合もドットはバージョン番号ではなくネームスペースコンポーネントを分離し、
    Bedrock API のためにそのまま保持する必要がある。
    """
    lower = model.lower()
    # Regional inference-profile prefixes
    if any(lower.startswith(p) for p in ("global.", "us.", "eu.", "ap.", "jp.")):
        return True
    # Bare Bedrock model IDs: provider.model-family
    if lower.startswith("anthropic."):
        return True
    return False


def normalize_model_name(model: str, preserve_dots: bool = False) -> str:
    """Anthropic API 向けにモデル名を正規化する。

    - 'anthropic/' プレフィックスを除去（OpenRouter 形式、大文字小文字を区別しない）
    - バージョン番号のドットをハイフンに変換（OpenRouter はドット、Anthropic はハイフン:
      claude-opus-4.6 → claude-opus-4-6）。preserve_dots が True の場合は変換しない
      （例: Alibaba/DashScope の qwen3.5-plus）。
    - Bedrock モデル ID（``anthropic.claude-opus-4-7``）と
      リージョン推論プロファイル（``us.anthropic.claude-*``）のドット（バージョン区切り
      ではなくネームスペース区切り）を保持する。
    """
    lower = model.lower()
    if lower.startswith("anthropic/"):
        model = model[len("anthropic/"):]
    if not preserve_dots:
        # Bedrock model IDs use dots as namespace separators
        # (e.g. "anthropic.claude-opus-4-7", "us.anthropic.claude-*").
        # These must not be converted to hyphens.  See issue #12295.
        if _is_bedrock_model_id(model):
            return model
        # OpenRouter uses dots for version separators (claude-opus-4.6),
        # Anthropic uses hyphens (claude-opus-4-6). Convert dots to hyphens.
        model = model.replace(".", "-")
    return model


def _sanitize_tool_id(tool_id: str) -> str:
    """Anthropic API 向けにツール呼び出し ID をサニタイズする。

    Anthropic は [a-zA-Z0-9_-] に一致する ID を要求する。無効な文字を
    アンダースコアに置換し、空でないことを保証する。
    """
    import re
    if not tool_id:
        return "tool_0"
    sanitized = re.sub(r"[^a-zA-Z0-9_-]", "_", tool_id)
    return sanitized or "tool_0"


def _normalize_tool_input_schema(schema: Any) -> Dict[str, Any]:
    """Anthropic に送信する前にツールスキーマを正規化する。

    Anthropic のツールスキーマバリデーターは Pydantic/MCP がオプションフィールドに
    よく生成する ``anyOf: [{"type": "string"}, {"type": "null"}]`` のような
    nullable ユニオンを拒否する。ツールのオプション性は親の ``required`` 配列で
    表現されるため、共有の ``strip_nullable_unions`` ヘルパーに委譲して
    nullable ユニオンを description/default などのメタデータを保持しながら
    non-null ブランチに折り畳む。

    ``keep_nullable_hint=False``: Anthropic バリデーターは OpenAPI スタイルの
    ``nullable: true`` 拡張を認識せず、厳格なスキーマ-文法コンバーターが
    不明なキーワードを拒否する可能性があるため。
    """
    if not schema:
        return {"type": "object", "properties": {}}

    from tools.schema_sanitizer import strip_nullable_unions

    normalized = strip_nullable_unions(schema, keep_nullable_hint=False)
    if not isinstance(normalized, dict):
        return {"type": "object", "properties": {}}
    if normalized.get("type") == "object" and not isinstance(normalized.get("properties"), dict):
        normalized = {**normalized, "properties": {}}
    return normalized


def convert_tools_to_anthropic(tools: List[Dict]) -> List[Dict]:
    """OpenAI ツール定義を Anthropic 形式に変換する。"""
    if not tools:
        return []
    result = []
    for t in tools:
        fn = t.get("function", {})
        result.append({
            "name": fn.get("name", ""),
            "description": fn.get("description", ""),
            "input_schema": _normalize_tool_input_schema(
                fn.get("parameters", {"type": "object", "properties": {}})
            ),
        })
    return result


def _image_source_from_openai_url(url: str) -> Dict[str, str]:
    """OpenAI スタイルの画像 URL/データ URL を Anthropic 画像ソース形式に変換する。"""
    url = str(url or "").strip()
    if not url:
        return {"type": "url", "url": ""}

    if url.startswith("data:"):
        header, _, data = url.partition(",")
        media_type = "image/jpeg"
        if header.startswith("data:"):
            mime_part = header[len("data:"):].split(";", 1)[0].strip()
            if mime_part.startswith("image/"):
                media_type = mime_part
        return {
            "type": "base64",
            "media_type": media_type,
            "data": data,
        }

    return {"type": "url", "url": url}


def _convert_content_part_to_anthropic(part: Any) -> Optional[Dict[str, Any]]:
    """単一の OpenAI スタイルコンテンツパーツを Anthropic 形式に変換する。"""
    if part is None:
        return None
    if isinstance(part, str):
        return {"type": "text", "text": part}
    if not isinstance(part, dict):
        return {"type": "text", "text": str(part)}

    ptype = part.get("type")

    if ptype == "input_text":
        block: Dict[str, Any] = {"type": "text", "text": part.get("text", "")}
    elif ptype in {"image_url", "input_image"}:
        image_value = part.get("image_url", {})
        url = image_value.get("url", "") if isinstance(image_value, dict) else str(image_value or "")
        block = {"type": "image", "source": _image_source_from_openai_url(url)}
    else:
        block = dict(part)

    if isinstance(part.get("cache_control"), dict) and "cache_control" not in block:
        block["cache_control"] = dict(part["cache_control"])
    return block


def _to_plain_data(value: Any, *, _depth: int = 0, _path: Optional[set] = None) -> Any:
    """SDK オブジェクトをプレーン Python データ構造に再帰的に変換する。

    循環参照（``_path`` は *現在の* 再帰パス上のオブジェクトの ``id()`` を追跡）と
    暴走する深さ（20 レベル上限）を防ぐ。
    パスベースの追跡を使用するため、複数の兄弟から参照される共有（ただし非循環）
    オブジェクトは文字列化されずに正しく変換される。
    """
    _MAX_DEPTH = 20
    if _depth > _MAX_DEPTH:
        return str(value)

    if _path is None:
        _path = set()

    obj_id = id(value)
    if obj_id in _path:
        return str(value)

    if hasattr(value, "model_dump"):
        _path.add(obj_id)
        result = _to_plain_data(value.model_dump(), _depth=_depth + 1, _path=_path)
        _path.discard(obj_id)
        return result
    if isinstance(value, dict):
        _path.add(obj_id)
        result = {k: _to_plain_data(v, _depth=_depth + 1, _path=_path) for k, v in value.items()}
        _path.discard(obj_id)
        return result
    if isinstance(value, (list, tuple)):
        _path.add(obj_id)
        result = [_to_plain_data(v, _depth=_depth + 1, _path=_path) for v in value]
        _path.discard(obj_id)
        return result
    if hasattr(value, "__dict__"):
        _path.add(obj_id)
        result = {
            k: _to_plain_data(v, _depth=_depth + 1, _path=_path)
            for k, v in vars(value).items()
            if not k.startswith("_")
        }
        _path.discard(obj_id)
        return result
    return value


def _extract_preserved_thinking_blocks(message: Dict[str, Any]) -> List[Dict[str, Any]]:
    """メッセージに以前保存された Anthropic 思考ブロックを返す。"""
    raw_details = message.get("reasoning_details")
    if not isinstance(raw_details, list):
        return []

    preserved: List[Dict[str, Any]] = []
    for detail in raw_details:
        if not isinstance(detail, dict):
            continue
        block_type = str(detail.get("type", "") or "").strip().lower()
        if block_type not in {"thinking", "redacted_thinking"}:
            continue
        preserved.append(copy.deepcopy(detail))
    return preserved


def _convert_content_to_anthropic(content: Any) -> Any:
    """OpenAI スタイルのマルチモーダルコンテンツ配列を Anthropic ブロックに変換する。"""
    if not isinstance(content, list):
        return content

    converted = []
    for part in content:
        block = _convert_content_part_to_anthropic(part)
        if block is not None:
            converted.append(block)
    return converted


def convert_messages_to_anthropic(
    messages: List[Dict],
    base_url: str | None = None,
) -> Tuple[Optional[Any], List[Dict]]:
    """OpenAI 形式のメッセージを Anthropic 形式に変換する。

    (system_prompt, anthropic_messages) を返す。
    Anthropic は別個のパラメーターとしてシステムメッセージを受け取るため抽出する。
    system_prompt は文字列またはコンテンツブロックのリスト（cache_control がある場合）。

    *base_url* が指定されサードパーティ Anthropic 互換エンドポイントを指す場合、
    すべての思考ブロック署名が除去される。署名は Anthropic 専用であり、
    サードパーティエンドポイントはそれを検証できないため
    HTTP 400 "Invalid signature in thinking block" で拒否する。
    """
    system = None
    result = []

    for m in messages:
        role = m.get("role", "user")
        content = m.get("content", "")

        if role == "system":
            if isinstance(content, list):
                # Preserve cache_control markers on content blocks
                has_cache = any(
                    p.get("cache_control") for p in content if isinstance(p, dict)
                )
                if has_cache:
                    system = [p for p in content if isinstance(p, dict)]
                else:
                    system = "\n".join(
                        p["text"] for p in content if p.get("type") == "text"
                    )
            else:
                system = content
            continue

        if role == "assistant":
            blocks = _extract_preserved_thinking_blocks(m)
            if content:
                if isinstance(content, list):
                    converted_content = _convert_content_to_anthropic(content)
                    if isinstance(converted_content, list):
                        blocks.extend(converted_content)
                else:
                    blocks.append({"type": "text", "text": str(content)})
            for tc in m.get("tool_calls", []):
                if not tc or not isinstance(tc, dict):
                    continue
                fn = tc.get("function", {})
                args = fn.get("arguments", "{}")
                try:
                    parsed_args = json.loads(args) if isinstance(args, str) else args
                except (json.JSONDecodeError, ValueError):
                    parsed_args = {}
                blocks.append({
                    "type": "tool_use",
                    "id": _sanitize_tool_id(tc.get("id", "")),
                    "name": fn.get("name", ""),
                    "input": parsed_args,
                })
            # Kimi's /coding endpoint (Anthropic protocol) requires assistant
            # tool-call messages to carry reasoning_content when thinking is
            # enabled server-side.  Preserve it as a thinking block so Kimi
            # can validate the message history.  See hermes-agent#13848.
            #
            # Accept empty string "" — _copy_reasoning_content_for_api()
            # injects "" as a tier-3 fallback for Kimi tool-call messages
            # that had no reasoning.  Kimi requires the field to exist, even
            # if empty.
            #
            # Prepend (not append): Anthropic protocol requires thinking
            # blocks before text and tool_use blocks.
            #
            # Guard: only add when reasoning_details didn't already contribute
            # thinking blocks.  On native Anthropic, reasoning_details produces
            # signed thinking blocks — adding another unsigned one from
            # reasoning_content would create a duplicate (same text) that gets
            # downgraded to a spurious text block on the last assistant message.
            reasoning_content = m.get("reasoning_content")
            _already_has_thinking = any(
                isinstance(b, dict) and b.get("type") in ("thinking", "redacted_thinking")
                for b in blocks
            )
            if isinstance(reasoning_content, str) and not _already_has_thinking:
                blocks.insert(0, {"type": "thinking", "thinking": reasoning_content})
            # Anthropic rejects empty assistant content
            effective = blocks or content
            if not effective or effective == "":
                effective = [{"type": "text", "text": "(empty)"}]
            result.append({"role": "assistant", "content": effective})
            continue

        if role == "tool":
            # Sanitize tool_use_id and ensure non-empty content
            result_content = content if isinstance(content, str) else json.dumps(content)
            if not result_content:
                result_content = "(no output)"
            tool_result = {
                "type": "tool_result",
                "tool_use_id": _sanitize_tool_id(m.get("tool_call_id", "")),
                "content": result_content,
            }
            if isinstance(m.get("cache_control"), dict):
                tool_result["cache_control"] = dict(m["cache_control"])
            # Merge consecutive tool results into one user message
            if (
                result
                and result[-1]["role"] == "user"
                and isinstance(result[-1]["content"], list)
                and result[-1]["content"]
                and result[-1]["content"][0].get("type") == "tool_result"
            ):
                result[-1]["content"].append(tool_result)
            else:
                result.append({"role": "user", "content": [tool_result]})
            continue

        # Regular user message — validate non-empty content (Anthropic rejects empty)
        if isinstance(content, list):
            converted_blocks = _convert_content_to_anthropic(content)
            # Check if all text blocks are empty
            if not converted_blocks or all(
                b.get("text", "").strip() == ""
                for b in converted_blocks
                if isinstance(b, dict) and b.get("type") == "text"
            ):
                converted_blocks = [{"type": "text", "text": "(empty message)"}]
            result.append({"role": "user", "content": converted_blocks})
        else:
            # Validate string content is non-empty
            if not content or (isinstance(content, str) and not content.strip()):
                content = "(empty message)"
            result.append({"role": "user", "content": content})

    # Strip orphaned tool_use blocks (no matching tool_result follows)
    tool_result_ids = set()
    for m in result:
        if m["role"] == "user" and isinstance(m["content"], list):
            for block in m["content"]:
                if block.get("type") == "tool_result":
                    tool_result_ids.add(block.get("tool_use_id"))
    for m in result:
        if m["role"] == "assistant" and isinstance(m["content"], list):
            m["content"] = [
                b
                for b in m["content"]
                if b.get("type") != "tool_use" or b.get("id") in tool_result_ids
            ]
            if not m["content"]:
                m["content"] = [{"type": "text", "text": "(tool call removed)"}]

    # Strip orphaned tool_result blocks (no matching tool_use precedes them).
    # This is the mirror of the above: context compression or session truncation
    # can remove an assistant message containing a tool_use while leaving the
    # subsequent tool_result intact.  Anthropic rejects these with a 400.
    tool_use_ids = set()
    for m in result:
        if m["role"] == "assistant" and isinstance(m["content"], list):
            for block in m["content"]:
                if block.get("type") == "tool_use":
                    tool_use_ids.add(block.get("id"))
    for m in result:
        if m["role"] == "user" and isinstance(m["content"], list):
            m["content"] = [
                b
                for b in m["content"]
                if b.get("type") != "tool_result" or b.get("tool_use_id") in tool_use_ids
            ]
            if not m["content"]:
                m["content"] = [{"type": "text", "text": "(tool result removed)"}]

    # Enforce strict role alternation (Anthropic rejects consecutive same-role messages)
    fixed = []
    for m in result:
        if fixed and fixed[-1]["role"] == m["role"]:
            if m["role"] == "user":
                # Merge consecutive user messages
                prev_content = fixed[-1]["content"]
                curr_content = m["content"]
                if isinstance(prev_content, str) and isinstance(curr_content, str):
                    fixed[-1]["content"] = prev_content + "\n" + curr_content
                elif isinstance(prev_content, list) and isinstance(curr_content, list):
                    fixed[-1]["content"] = prev_content + curr_content
                else:
                    # Mixed types — wrap string in list
                    if isinstance(prev_content, str):
                        prev_content = [{"type": "text", "text": prev_content}]
                    if isinstance(curr_content, str):
                        curr_content = [{"type": "text", "text": curr_content}]
                    fixed[-1]["content"] = prev_content + curr_content
            else:
                # Consecutive assistant messages — merge text content.
                # Drop thinking blocks from the *second* message: their
                # signature was computed against a different turn boundary
                # and becomes invalid once merged.
                if isinstance(m["content"], list):
                    m["content"] = [
                        b for b in m["content"]
                        if not (isinstance(b, dict) and b.get("type") in ("thinking", "redacted_thinking"))
                    ]
                prev_blocks = fixed[-1]["content"]
                curr_blocks = m["content"]
                if isinstance(prev_blocks, list) and isinstance(curr_blocks, list):
                    fixed[-1]["content"] = prev_blocks + curr_blocks
                elif isinstance(prev_blocks, str) and isinstance(curr_blocks, str):
                    fixed[-1]["content"] = prev_blocks + "\n" + curr_blocks
                else:
                    # Mixed types — normalize both to list and merge
                    if isinstance(prev_blocks, str):
                        prev_blocks = [{"type": "text", "text": prev_blocks}]
                    if isinstance(curr_blocks, str):
                        curr_blocks = [{"type": "text", "text": curr_blocks}]
                    fixed[-1]["content"] = prev_blocks + curr_blocks
        else:
            fixed.append(m)
    result = fixed

    # ── Thinking block signature management ──────────────────────────
    # Anthropic signs thinking blocks against the full turn content.
    # Any upstream mutation (context compression, session truncation,
    # orphan stripping, message merging) invalidates the signature,
    # causing HTTP 400 "Invalid signature in thinking block".
    #
    # Signatures are Anthropic-proprietary.  Third-party endpoints
    # (MiniMax, Azure AI Foundry, self-hosted proxies) cannot validate
    # them and will reject them outright.  When targeting a third-party
    # endpoint, strip ALL thinking/redacted_thinking blocks from every
    # assistant message — the third-party will generate its own
    # thinking blocks if it supports extended thinking.
    #
    # For direct Anthropic (strategy following clawdbot/OpenClaw):
    # 1. Strip thinking/redacted_thinking from all assistant messages
    #    EXCEPT the last one — preserves reasoning continuity on the
    #    current tool-use chain while avoiding stale signature errors.
    # 2. Downgrade unsigned thinking blocks (no signature) to text —
    #    Anthropic can't validate them and will reject them.
    # 3. Strip cache_control from thinking/redacted_thinking blocks —
    #    cache markers can interfere with signature validation.
    _THINKING_TYPES = frozenset(("thinking", "redacted_thinking"))
    _is_third_party = _is_third_party_anthropic_endpoint(base_url)
    _is_kimi = _is_kimi_coding_endpoint(base_url)

    last_assistant_idx = None
    for i in range(len(result) - 1, -1, -1):
        if result[i].get("role") == "assistant":
            last_assistant_idx = i
            break

    for idx, m in enumerate(result):
        if m.get("role") != "assistant" or not isinstance(m.get("content"), list):
            continue

        if _is_kimi:
            # Kimi's /coding endpoint enables thinking server-side and
            # requires unsigned thinking blocks on replayed assistant
            # tool-call messages.  Strip signed Anthropic blocks (Kimi
            # can't validate signatures) but preserve the unsigned ones
            # we synthesised from reasoning_content above.
            new_content = []
            for b in m["content"]:
                if not isinstance(b, dict) or b.get("type") not in _THINKING_TYPES:
                    new_content.append(b)
                    continue
                if b.get("signature") or b.get("data"):
                    # Anthropic-signed block — Kimi can't validate, strip
                    continue
                # Unsigned thinking (synthesised from reasoning_content) —
                # keep it: Kimi needs it for message-history validation.
                new_content.append(b)
            m["content"] = new_content or [{"type": "text", "text": "(empty)"}]
        elif _is_third_party or idx != last_assistant_idx:
            # Third-party endpoint: strip ALL thinking blocks from every
            # assistant message — signatures are Anthropic-proprietary.
            # Direct Anthropic: strip from non-latest assistant messages only.
            stripped = [
                b for b in m["content"]
                if not (isinstance(b, dict) and b.get("type") in _THINKING_TYPES)
            ]
            m["content"] = stripped or [{"type": "text", "text": "(thinking elided)"}]
        else:
            # Latest assistant on direct Anthropic: keep signed thinking
            # blocks for reasoning continuity; downgrade unsigned ones to
            # plain text.
            new_content = []
            for b in m["content"]:
                if not isinstance(b, dict) or b.get("type") not in _THINKING_TYPES:
                    new_content.append(b)
                    continue
                if b.get("type") == "redacted_thinking":
                    # Redacted blocks use 'data' for the signature payload
                    if b.get("data"):
                        new_content.append(b)
                    # else: drop — no data means it can't be validated
                elif b.get("signature"):
                    # Signed thinking block — keep it
                    new_content.append(b)
                else:
                    # Unsigned thinking — downgrade to text so it's not lost
                    thinking_text = b.get("thinking", "")
                    if thinking_text:
                        new_content.append({"type": "text", "text": thinking_text})
            m["content"] = new_content or [{"type": "text", "text": "(empty)"}]

        # Strip cache_control from any remaining thinking/redacted_thinking
        # blocks — cache markers interfere with signature validation.
        for b in m["content"]:
            if isinstance(b, dict) and b.get("type") in _THINKING_TYPES:
                b.pop("cache_control", None)

    return system, result


def build_anthropic_kwargs(
    model: str,
    messages: List[Dict],
    tools: Optional[List[Dict]],
    max_tokens: Optional[int],
    reasoning_config: Optional[Dict[str, Any]],
    tool_choice: Optional[str] = None,
    is_oauth: bool = False,
    preserve_dots: bool = False,
    context_length: Optional[int] = None,
    base_url: str | None = None,
    fast_mode: bool = False,
) -> Dict[str, Any]:
    """Build kwargs for anthropic.messages.create().

    Naming note — two distinct concepts, easily confused:
      max_tokens     = OUTPUT token cap for a single response.
                       Anthropic's API calls this "max_tokens" but it only
                       limits the *output*.  Anthropic's own native SDK
                       renamed it "max_output_tokens" for clarity.
      context_length = TOTAL context window (input tokens + output tokens).
                       The API enforces: input_tokens + max_tokens ≤ context_length.
                       Stored on the ContextCompressor; reduced on overflow errors.

    When *max_tokens* is None the model's native output ceiling is used
    (e.g. 128K for Opus 4.6, 64K for Sonnet 4.6).

    When *context_length* is provided and the model's native output ceiling
    exceeds it (e.g. a local endpoint with an 8K window), the output cap is
    clamped to context_length − 1.  This only kicks in for unusually small
    context windows; for full-size models the native output cap is always
    smaller than the context window so no clamping happens.
    NOTE: this clamping does not account for prompt size — if the prompt is
    large, Anthropic may still reject the request.  The caller must detect
    "max_tokens too large given prompt" errors and retry with a smaller cap
    (see parse_available_output_tokens_from_error + _ephemeral_max_output_tokens).

    When *is_oauth* is True, enables the OAuth-only beta headers required by
    Anthropic's subscription-gated Messages endpoint (fast-mode branch only;
    the default headers are set by build_anthropic_client). No system-prompt
    or tool-name rewriting is performed — Hermes identifies as itself.

    When *preserve_dots* is True, model name dots are not converted to hyphens
    (for Alibaba/DashScope anthropic-compatible endpoints: qwen3.5-plus).

    When *base_url* points to a third-party Anthropic-compatible endpoint,
    thinking block signatures are stripped (they are Anthropic-proprietary).

    When *fast_mode* is True, adds ``extra_body["speed"] = "fast"`` and the
    fast-mode beta header for ~2.5x faster output throughput on Opus 4.6.
    Currently only supported on native Anthropic endpoints (not third-party
    compatible ones).
    """
    system, anthropic_messages = convert_messages_to_anthropic(messages, base_url=base_url)
    anthropic_tools = convert_tools_to_anthropic(tools) if tools else []

    model = normalize_model_name(model, preserve_dots=preserve_dots)
    # effective_max_tokens = output cap for this call (≠ total context window)
    # Use the resolver helper so non-positive values (negative ints,
    # fractional floats, NaN, non-numeric) fail locally with a clear error
    # rather than 400-ing at the Anthropic API. See openclaw/openclaw#66664.
    effective_max_tokens = _resolve_anthropic_messages_max_tokens(
        max_tokens, model, context_length=context_length
    )

    # Clamp output cap to fit inside the total context window.
    # Only matters for small custom endpoints where context_length < native
    # output ceiling.  For standard Anthropic models context_length (e.g.
    # 200K) is always larger than the output ceiling (e.g. 128K), so this
    # branch is not taken.
    if context_length and effective_max_tokens > context_length:
        effective_max_tokens = max(context_length - 1, 1)

    # OAuth requests go through Anthropic's subscription-gated Messages
    # endpoint but otherwise send the real Hermes system prompt and real
    # Hermes tool names — the only OAuth-specific wire differences are
    # Bearer auth and the _OAUTH_ONLY_BETAS header (applied in
    # build_anthropic_client and the fast-mode branch below).

    kwargs: Dict[str, Any] = {
        "model": model,
        "messages": anthropic_messages,
        "max_tokens": effective_max_tokens,
    }

    if system:
        kwargs["system"] = system

    if anthropic_tools:
        kwargs["tools"] = anthropic_tools
        # Map OpenAI tool_choice to Anthropic format
        if tool_choice == "auto" or tool_choice is None:
            kwargs["tool_choice"] = {"type": "auto"}
        elif tool_choice == "required":
            kwargs["tool_choice"] = {"type": "any"}
        elif tool_choice == "none":
            # Anthropic has no tool_choice "none" — omit tools entirely to prevent use
            kwargs.pop("tools", None)
        elif isinstance(tool_choice, str):
            # Specific tool name
            kwargs["tool_choice"] = {"type": "tool", "name": tool_choice}

    # Map reasoning_config to Anthropic's thinking parameter.
    # Claude 4.6+ models use adaptive thinking + output_config.effort.
    # Older models use manual thinking with budget_tokens.
    # MiniMax Anthropic-compat endpoints support thinking (manual mode only,
    # not adaptive).  Haiku does NOT support extended thinking — skip entirely.
    #
    # Kimi's /coding endpoint speaks the Anthropic Messages protocol but has
    # its own thinking semantics: when ``thinking.enabled`` is sent, Kimi
    # validates the message history and requires every prior assistant
    # tool-call message to carry OpenAI-style ``reasoning_content``.  The
    # Anthropic path never populates that field, and
    # ``convert_messages_to_anthropic`` strips all Anthropic thinking blocks
    # on third-party endpoints — so the request fails with HTTP 400
    # "thinking is enabled but reasoning_content is missing in assistant
    # tool call message at index N".  Kimi's reasoning is driven server-side
    # on the /coding route, so skip Anthropic's thinking parameter entirely
    # for that host.  (Kimi on chat_completions enables thinking via
    # extra_body in the ChatCompletionsTransport — see #13503.)
    #
    # On 4.7+ the `thinking.display` field defaults to "omitted", which
    # silently hides reasoning text that Hermes surfaces in its CLI. We
    # request "summarized" so the reasoning blocks stay populated — matching
    # 4.6 behavior and preserving the activity-feed UX during long tool runs.
    _is_kimi_coding = _is_kimi_coding_endpoint(base_url)
    if reasoning_config and isinstance(reasoning_config, dict) and not _is_kimi_coding:
        if reasoning_config.get("enabled") is not False and "haiku" not in model.lower():
            effort = str(reasoning_config.get("effort", "medium")).lower()
            budget = THINKING_BUDGET.get(effort, 8000)
            if _supports_adaptive_thinking(model):
                kwargs["thinking"] = {
                    "type": "adaptive",
                    "display": "summarized",
                }
                adaptive_effort = ADAPTIVE_EFFORT_MAP.get(effort, "medium")
                # Downgrade xhigh→max on models that don't list xhigh as a
                # supported level (Opus/Sonnet 4.6). Opus 4.7+ keeps xhigh.
                if adaptive_effort == "xhigh" and not _supports_xhigh_effort(model):
                    adaptive_effort = "max"
                kwargs["output_config"] = {
                    "effort": adaptive_effort,
                }
            else:
                kwargs["thinking"] = {"type": "enabled", "budget_tokens": budget}
                # Anthropic requires temperature=1 when thinking is enabled on older models
                kwargs["temperature"] = 1
                kwargs["max_tokens"] = max(effective_max_tokens, budget + 4096)

    # ── Strip sampling params on 4.7+ ─────────────────────────────────
    # Opus 4.7 rejects any non-default temperature/top_p/top_k with a 400.
    # Callers (auxiliary_client, etc.) may set these for older models;
    # drop them here as a safety net so upstream 4.6 → 4.7 migrations
    # don't require coordinated edits everywhere.
    if _forbids_sampling_params(model):
        for _sampling_key in ("temperature", "top_p", "top_k"):
            kwargs.pop(_sampling_key, None)

    # ── Fast mode (Opus 4.6 only) ────────────────────────────────────
    # Adds extra_body.speed="fast" + the fast-mode beta header for ~2.5x
    # output speed. Only for native Anthropic endpoints — third-party
    # providers would reject the unknown beta header and speed parameter.
    if fast_mode and not _is_third_party_anthropic_endpoint(base_url):
        kwargs.setdefault("extra_body", {})["speed"] = "fast"
        # Build extra_headers with ALL applicable betas (the per-request
        # extra_headers override the client-level anthropic-beta header).
        betas = list(_common_betas_for_base_url(base_url))
        if is_oauth:
            # Strip context-1m — incompatible with OAuth auth. See matching
            # comment in build_anthropic_client().
            betas = [b for b in betas if b != _CONTEXT_1M_BETA]
            betas.extend(_OAUTH_ONLY_BETAS)
        betas.append(_FAST_MODE_BETA)
        kwargs["extra_headers"] = {"anthropic-beta": ",".join(betas)}

    return kwargs


