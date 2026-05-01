"""
画像生成プロバイダーレジストリ
================================

登録済みプロバイダーの中央マップ。プラグインがインポート時に
``PluginContext.register_image_gen_provider()`` で登録し、
``image_generate`` ツールが各呼び出しをアクティブなバックエンドに
ディスパッチするために使用する。

アクティブ選択
--------------
アクティブなプロバイダーは ``config.yaml`` の ``image_gen.provider`` で選択される。
未設定の場合、:func:`get_active_provider` は以下のフォールバックロジックを適用する:

1. ちょうど1つのプロバイダーが登録されている場合、それを使用する。
2. そうでなく ``fal`` という名前のプロバイダーが登録されている場合、それを使用する
   （レガシーデフォルト — プラグイン導入前の動作に一致）。
3. それ以外は ``None`` を返す（ツールがユーザーを ``hermes tools`` に誘導するエラーを表示）。
"""

from __future__ import annotations

import logging
import threading
from typing import Dict, List, Optional

from core.image_gen_provider import ImageGenProvider

logger = logging.getLogger(__name__)


_providers: Dict[str, ImageGenProvider] = {}
_lock = threading.Lock()


def register_provider(provider: ImageGenProvider) -> None:
    """画像生成プロバイダーを登録する。

    再登録（同じ ``name``）は前のエントリを上書きしてデバッグメッセージを
    ログに記録する — ホットリロードシナリオ（テスト、開発ループ）で
    予測可能な動作をする。
    """
    if not isinstance(provider, ImageGenProvider):
        raise TypeError(
            f"register_provider() expects an ImageGenProvider instance, "
            f"got {type(provider).__name__}"
        )
    name = provider.name
    if not isinstance(name, str) or not name.strip():
        raise ValueError("Image gen provider .name must be a non-empty string")
    with _lock:
        existing = _providers.get(name)
        _providers[name] = provider
    if existing is not None:
        logger.debug("Image gen provider '%s' re-registered (was %r)", name, type(existing).__name__)
    else:
        logger.debug("Registered image gen provider '%s' (%s)", name, type(provider).__name__)


def list_providers() -> List[ImageGenProvider]:
    """全ての登録済みプロバイダーを名前順にソートして返す。"""
    with _lock:
        items = list(_providers.values())
    return sorted(items, key=lambda p: p.name)


def get_provider(name: str) -> Optional[ImageGenProvider]:
    """*name* で登録されたプロバイダーを返す。存在しない場合は None を返す。"""
    if not isinstance(name, str):
        return None
    with _lock:
        return _providers.get(name.strip())


def get_active_provider() -> Optional[ImageGenProvider]:
    """現在アクティブなプロバイダーを解決する。

    config.yaml から ``image_gen.provider`` を読み取り、モジュール docstring
    に従ってフォールバックする。
    """
    configured: Optional[str] = None
    try:
        from hermes_cli.config import load_config

        cfg = load_config()
        section = cfg.get("image_gen") if isinstance(cfg, dict) else None
        if isinstance(section, dict):
            raw = section.get("provider")
            if isinstance(raw, str) and raw.strip():
                configured = raw.strip()
    except Exception as exc:
        logger.debug("Could not read image_gen.provider from config: %s", exc)

    with _lock:
        snapshot = dict(_providers)

    if configured:
        provider = snapshot.get(configured)
        if provider is not None:
            return provider
        logger.debug(
            "image_gen.provider='%s' configured but not registered; falling back",
            configured,
        )

    # Fallback: single-provider case
    if len(snapshot) == 1:
        return next(iter(snapshot.values()))

    # Fallback: prefer legacy FAL for backward compat
    if "fal" in snapshot:
        return snapshot["fal"]

    return None


def _reset_for_tests() -> None:
    """レジストリをクリアする。**テスト専用。**"""
    with _lock:
        _providers.clear()
