"""ユーザーが添付した画像のインバウンドルーティングヘルパー。

2つのモード:

  native  — ユーザーターンで OpenAI スタイルの ``image_url`` コンテンツパーツとして
            画像を添付する。プロバイダーアダプター（Anthropic、Gemini、Bedrock、
            Codex、OpenAI chat.completions）がベンダー固有のマルチモーダル形式に変換する。

  text    — 各画像に事前に ``vision_analyze`` を実行し、説明をユーザーテキストの
            先頭に追加する。モデルはピクセルを直接見ず、損失のあるテキスト要約のみ
            見る。これは従来の動作であり、非ビジョンモデルには今でも適切な選択。

決定は :func:`decide_image_input_mode` がメッセージターンごとに1回行う。
config.yaml の ``agent.image_input_mode``（``auto`` | ``native`` | ``text``、
デフォルト ``auto``）とアクティブモデルの機能メタデータを読み取る。

``auto`` モードで:
  - ユーザーが ``auxiliary.vision.provider`` を明示的に設定している場合
    （``auto`` でなく空でもない）、メインモデルに関わらずテキストパイプラインを
    希望していると仮定する — 特定のビジョンバックエンドを理由（コスト、品質、
    ローカル専用等）でオプトインしている。
  - そうでなく、アクティブモデルが models.dev メタデータで ``supports_vision=True``
    を報告している場合、ネイティブに添付する。
  - それ以外（非ビジョンモデル、明示的な上書きなし）はテキストにフォールバックする。

これにより ``vision_analyze`` はすべてのセッションでツールとして公開し続ける —
それを連鎖するスキルとエージェントフロー（ブラウザのスクリーンショット、
URL 参照画像の詳細検査、スタイルゲートループ）が引き続き機能する。
ルーティングは *現在のターンのユーザー添付画像* のメインモデルへの提示方法にのみ影響する。
"""

from __future__ import annotations

import base64
import logging
import mimetypes
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


_VALID_MODES = frozenset({"auto", "native", "text"})


def _coerce_mode(raw: Any) -> str:
    """設定値を有効なモードのいずれかに正規化する。"""
    if not isinstance(raw, str):
        return "auto"
    val = raw.strip().lower()
    if val in _VALID_MODES:
        return val
    return "auto"


def _explicit_aux_vision_override(cfg: Optional[Dict[str, Any]]) -> bool:
    """ユーザーが特定の補助ビジョンバックエンドを設定している場合に True を返す。

    明示的な上書きはユーザーがテキストパイプラインを *望んでいる* ことを意味する
    （専用ビジョンモデルを使用している）ため、暗黙にバイパスしない。
    """
    if not isinstance(cfg, dict):
        return False
    aux = cfg.get("auxiliary") or {}
    if not isinstance(aux, dict):
        return False
    vision = aux.get("vision") or {}
    if not isinstance(vision, dict):
        return False

    provider = str(vision.get("provider") or "").strip().lower()
    model = str(vision.get("model") or "").strip()
    base_url = str(vision.get("base_url") or "").strip()

    # "auto" / "" / blank = not explicit
    if provider in ("", "auto") and not model and not base_url:
        return False
    return True


def _lookup_supports_vision(provider: str, model: str) -> Optional[bool]:
    """機能が解決できれば True/False を返す。不明な場合は None を返す。"""
    if not provider or not model:
        return None
    try:
        from core.models_dev import get_model_capabilities
        caps = get_model_capabilities(provider, model)
    except Exception as exc:  # pragma: no cover - defensive
        logger.debug("image_routing: caps lookup failed for %s:%s — %s", provider, model, exc)
        return None
    if caps is None:
        return None
    return bool(caps.supports_vision)


def decide_image_input_mode(
    provider: str,
    model: str,
    cfg: Optional[Dict[str, Any]],
) -> str:
    """Return ``"native"`` or ``"text"`` for the given turn.

    Args:
      provider: active inference provider ID (e.g. ``"anthropic"``, ``"openrouter"``).
      model:    active model slug as it would be sent to the provider.
      cfg:      loaded config.yaml dict, or None. When None, behaves as auto.
    """
    mode_cfg = "auto"
    if isinstance(cfg, dict):
        agent_cfg = cfg.get("agent") or {}
        if isinstance(agent_cfg, dict):
            mode_cfg = _coerce_mode(agent_cfg.get("image_input_mode"))

    if mode_cfg == "native":
        return "native"
    if mode_cfg == "text":
        return "text"

    # auto
    if _explicit_aux_vision_override(cfg):
        return "text"

    supports = _lookup_supports_vision(provider, model)
    if supports is True:
        return "native"
    return "text"


# Image size handling is REACTIVE rather than proactive: we attempt native
# attachment at full size regardless of provider, and rely on
# ``run_agent._try_shrink_image_parts_in_messages`` to shrink + retry if
# the provider rejects the request (e.g. Anthropic's hard 5 MB per-image
# ceiling returned as HTTP 400 "image exceeds 5 MB maximum").
#
# Why reactive: our knowledge of provider ceilings is partial and evolving
# (OpenAI accepts 49 MB+, Anthropic 5 MB, Gemini 100 MB, others unknown).
# A proactive per-provider table would be stale the moment a provider raises
# or lowers its limit, and silently degrading quality for users on providers
# that would have accepted the full image is the worse failure mode.
# The shrink-on-reject path loses 1 API call + maybe 1s of Pillow work when
# it fires, which is cheaper than permanent quality loss.


def _guess_mime(path: Path) -> str:
    mime, _ = mimetypes.guess_type(str(path))
    if mime and mime.startswith("image/"):
        return mime
    # mimetypes on some Linux distros mis-maps .jpg; default to jpeg when
    # the suffix looks imagey.
    suffix = path.suffix.lower()
    return {
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".png": "image/png",
        ".gif": "image/gif",
        ".webp": "image/webp",
        ".bmp": "image/bmp",
    }.get(suffix, "image/jpeg")


def _file_to_data_url(path: Path) -> Optional[str]:
    """Encode a local image as a base64 data URL at its native size.

    Size limits are NOT enforced here — the agent retry loop
    (``run_agent._try_shrink_image_parts_in_messages``) shrinks on the
    provider's first rejection. Keeping this simple means providers that
    accept large images (OpenAI 49 MB+, Gemini 100 MB) don't pay a silent
    quality tax just because one other provider is stricter.

    Returns None only if the file can't be read (missing, permission
    denied, etc.); the caller reports those paths in ``skipped``.
    """
    try:
        raw = path.read_bytes()
    except Exception as exc:
        logger.warning("image_routing: failed to read %s — %s", path, exc)
        return None
    mime = _guess_mime(path)
    b64 = base64.b64encode(raw).decode("ascii")
    return f"data:{mime};base64,{b64}"


def build_native_content_parts(
    user_text: str,
    image_paths: List[str],
) -> Tuple[List[Dict[str, Any]], List[str]]:
    """Build an OpenAI-style ``content`` list for a user turn.

    Shape:
      [{"type": "text", "text": "..."},
       {"type": "image_url", "image_url": {"url": "data:image/png;base64,..."}},
       ...]

    Images are attached at their native size. If a provider rejects the
    request because an image is too large (e.g. Anthropic's 5 MB per-image
    ceiling), the agent's retry loop transparently shrinks and retries
    once — see ``run_agent._try_shrink_image_parts_in_messages``.

    Returns (content_parts, skipped_paths). Skipped paths are files that
    couldn't be read from disk.
    """
    parts: List[Dict[str, Any]] = []
    skipped: List[str] = []

    text = (user_text or "").strip()
    if text:
        parts.append({"type": "text", "text": text})

    for raw_path in image_paths:
        p = Path(raw_path)
        if not p.exists() or not p.is_file():
            skipped.append(str(raw_path))
            continue
        data_url = _file_to_data_url(p)
        if not data_url:
            skipped.append(str(raw_path))
            continue
        parts.append({
            "type": "image_url",
            "image_url": {"url": data_url},
        })

    # If the text was empty, add a neutral prompt so the turn isn't just images.
    if not text and any(p.get("type") == "image_url" for p in parts):
        parts.insert(0, {"type": "text", "text": "What do you see in this image?"})

    return parts, skipped


__all__ = [
    "decide_image_input_mode",
    "build_native_content_parts",
]
