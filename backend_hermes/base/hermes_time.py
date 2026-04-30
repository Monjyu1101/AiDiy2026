"""
Hermes 用タイムゾーン対応クロック。

ユーザーの設定した IANA タイムゾーン（例: ``Asia/Tokyo``）に基づいて
タイムゾーン対応 datetime を返す ``now()`` ヘルパーを提供します。

解決順序:
  1. ``HERMES_TIMEZONE`` 環境変数
  2. ``~/.hermes/config.yaml`` の ``timezone`` キー
  3. フォールバック: サーバーのローカル時刻 (``datetime.now().astimezone()``)

不正なタイムゾーン値は警告をログに出力し、安全にフォールバックします。
Hermes が不正なタイムゾーン文字列でクラッシュすることはありません。
"""

import logging
import os
from datetime import datetime
from base.hermes_constants import get_config_path
from typing import Optional

logger = logging.getLogger(__name__)

try:
    from zoneinfo import ZoneInfo
except ImportError:
    # Python 3.8 以前向けフォールバック（Hermes は 3.9+ 必須だが念のため）
    from backports.zoneinfo import ZoneInfo  # type: ignore[no-redef]

# キャッシュ — 一度解決したら以後は再利用する。
# reset_cache() を呼ぶと強制的に再解決する（設定変更後など）。
_cached_tz: Optional[ZoneInfo] = None
_cached_tz_name: Optional[str] = None
_cache_resolved: bool = False


def _resolve_timezone_name() -> str:
    """設定された IANA タイムゾーン文字列を読み取る（見つからなければ空文字列）。

    この関数は config.yaml の読み取りでファイル I/O を行う可能性があるため、
    呼び出し側は結果をキャッシュし、``now()`` のたびに呼ばないこと。
    """
    # 1. 環境変数（最優先 — Supervisor などから設定）
    tz_env = os.getenv("HERMES_TIMEZONE", "").strip()
    if tz_env:
        return tz_env

    # 2. config.yaml の ``timezone`` キー
    try:
        import yaml
        config_path = get_config_path()
        if config_path.exists():
            with open(config_path) as f:
                cfg = yaml.safe_load(f) or {}
            tz_cfg = cfg.get("timezone", "")
            if isinstance(tz_cfg, str) and tz_cfg.strip():
                return tz_cfg.strip()
    except Exception:
        pass

    return ""


def _get_zoneinfo(name: str) -> Optional[ZoneInfo]:
    """ZoneInfo を検証して返す。不正な名前なら None。"""
    if not name:
        return None
    try:
        return ZoneInfo(name)
    except (KeyError, Exception) as exc:
        logger.warning(
            "Invalid timezone '%s': %s. Falling back to server local time.",
            name, exc,
        )
        return None


def get_timezone() -> Optional[ZoneInfo]:
    """ユーザーの設定した ZoneInfo を返す。設定なしなら None（サーバーローカル）。

    初回呼び出し時に解決され、以後キャッシュされる。
    設定変更後は ``reset_cache()`` を呼ぶこと。
    """
    global _cached_tz, _cached_tz_name, _cache_resolved
    if not _cache_resolved:
        _cached_tz_name = _resolve_timezone_name()
        _cached_tz = _get_zoneinfo(_cached_tz_name)
        _cache_resolved = True
    return _cached_tz


def now() -> datetime:
    """
    現在時刻をタイムゾーン対応 datetime で返す。

    有効なタイムゾーンが設定されている場合はそのタイムゾーンの壁時計時刻。
    それ以外の場合はサーバーのローカル時刻（``astimezone()``）を返す。
    """
    tz = get_timezone()
    if tz is not None:
        return datetime.now(tz)
    # タイムゾーン未設定 → サーバーローカル（タイムゾーン情報は付く）
    return datetime.now().astimezone()


def reset_cache() -> None:
    """次回 ``get_timezone()`` 呼び出し時にタイムゾーンを再解決させる。"""
    global _cache_resolved
    _cache_resolved = False
