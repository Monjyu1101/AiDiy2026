"""ツールと ACP シムの両方で使用される共通ファイル安全ルール。"""

from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Optional


def _hermes_home_path() -> Path:
    """循環インポートなしにアクティブな HERMES_HOME（プロファイル対応）を解決する。"""
    try:
        from base.hermes_constants import get_hermes_home  # 循環回避のためローカルインポート
        return get_hermes_home()
    except Exception:
        return Path(os.path.expanduser("~/.hermes"))


def build_write_denied_paths(home: str) -> set[str]:
    """書き込みを絶対に許可しない機密パスの集合を返す。"""
    hermes_home = _hermes_home_path()
    paths = [
        os.path.join(home, ".ssh", "authorized_keys"),
        os.path.join(home, ".ssh", "id_rsa"),
        os.path.join(home, ".ssh", "id_ed25519"),
        os.path.join(home, ".ssh", "config"),
        str(hermes_home / ".env"),
        os.path.join(home, ".bashrc"),
        os.path.join(home, ".zshrc"),
        os.path.join(home, ".profile"),
        os.path.join(home, ".bash_profile"),
        os.path.join(home, ".zprofile"),
        os.path.join(home, ".netrc"),
        os.path.join(home, ".pgpass"),
        os.path.join(home, ".npmrc"),
        os.path.join(home, ".pypirc"),
    ]
    # Unix 専用パス（Windows では存在しない）
    if sys.platform != "win32":
        paths.extend([
            "/etc/sudoers",
            "/etc/passwd",
            "/etc/shadow",
        ])
    return {os.path.realpath(p) for p in paths}


def build_write_denied_prefixes(home: str) -> list[str]:
    """書き込みを絶対に許可しない機密ディレクトリプレフィックスのリストを返す。"""
    dirs = [
        os.path.join(home, ".ssh"),
        os.path.join(home, ".aws"),
        os.path.join(home, ".gnupg"),
        os.path.join(home, ".kube"),
        os.path.join(home, ".docker"),
        os.path.join(home, ".azure"),
        os.path.join(home, ".config", "gh"),
    ]
    # Unix 専用ディレクトリ（Windows では存在しない）
    if sys.platform != "win32":
        dirs.extend([
            "/etc/sudoers.d",
            "/etc/systemd",
        ])
    return [os.path.realpath(p) + os.sep for p in dirs]


def get_safe_write_root() -> Optional[str]:
    """解決済みの HERMES_WRITE_SAFE_ROOT パスを返す。未設定の場合は None を返す。"""
    root = os.getenv("HERMES_WRITE_SAFE_ROOT", "")
    if not root:
        return None
    try:
        return os.path.realpath(os.path.expanduser(root))
    except Exception:
        return None


def is_write_denied(path: str) -> bool:
    """パスが書き込み拒否リストまたは安全ルートによってブロックされている場合に True を返す。"""
    home = os.path.realpath(os.path.expanduser("~"))
    resolved = os.path.realpath(os.path.expanduser(str(path)))

    if resolved in build_write_denied_paths(home):
        return True
    for prefix in build_write_denied_prefixes(home):
        if resolved.startswith(prefix):
            return True

    safe_root = get_safe_write_root()
    if safe_root and not (resolved == safe_root or resolved.startswith(safe_root + os.sep)):
        return True

    return False


def get_read_block_error(path: str) -> Optional[str]:
    """読み取り対象が Hermes 内部キャッシュファイルの場合にエラーメッセージを返す。"""
    resolved = Path(path).expanduser().resolve()
    hermes_home = _hermes_home_path().resolve()
    blocked_dirs = [
        hermes_home / "skills" / ".hub" / "index-cache",
        hermes_home / "skills" / ".hub",
    ]
    for blocked in blocked_dirs:
        try:
            resolved.relative_to(blocked)
        except ValueError:
            continue
        return (
            f"Access denied: {path} is an internal Hermes cache file "
            "and cannot be read directly to prevent prompt injection. "
            "Use the skills_list or skill_view tools instead."
        )
    return None
