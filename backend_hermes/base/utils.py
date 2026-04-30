"""hermes-agent 共通ユーティリティ関数。

yaml, json, os に依存。hermes_constants より下位、他のモジュールより上位。
"""

import json
import logging
import os
import stat
import tempfile
from pathlib import Path
from typing import Any, Union
from urllib.parse import urlparse

import yaml

logger = logging.getLogger(__name__)


TRUTHY_STRINGS = frozenset({"1", "true", "yes", "on"})


def is_truthy_value(value: Any, default: bool = False) -> bool:
    """真偽値っぽい値をプロジェクト共通の truthy 文字列セットで真偽値に変換する。

    Args:
        value: 変換する値（None, bool, str, その他）。
        default: value が None の場合のデフォルト値。

    Returns:
        真偽値に変換された値。
    """
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() in TRUTHY_STRINGS
    return bool(value)


def env_var_enabled(name: str, default: str = "") -> bool:
    """環境変数が truthy な値に設定されている場合に True を返す。

    Args:
        name: 環境変数名。
        default: 環境変数が未設定の場合のデフォルト値（文字列）。

    Returns:
        環境変数が truthy なら True。
    """
    return is_truthy_value(os.getenv(name, default), default=False)


def _preserve_file_mode(path: Path) -> "int | None":
    """*path* が存在すればパーミッションビットを取得し、存在しなければ ``None`` を返す。

    Args:
        path: パーミッションを保存するファイルパス。

    Returns:
        パーミッションビット、または None。
    """
    try:
        return stat.S_IMODE(path.stat().st_mode) if path.exists() else None
    except OSError:
        return None


def _restore_file_mode(path: Path, mode: "int | None") -> None:
    """アトミック置換後に *path* に *mode* を再適用する。

    ``tempfile.mkstemp`` は 0o600（所有者のみ）でファイルを作成する。
    ``os.replace`` でテンポラリファイルを所定の位置に置き換えると、
    ターゲットファイルがその制限的なパーミッションを継承してしまい、
    Docker や NAS のボリュームマウントが壊れる可能性がある。
    この関数を ``os.replace`` の直後に呼び出すことで元のパーミッションを復元する。

    Args:
        path: パーミッションを復元するファイルパス。
        mode: 復元するパーミッションビット（None の場合は何もしない）。
    """
    if mode is None:
        return
    try:
        os.chmod(path, mode)
    except OSError:
        # Windows ではこの操作は無視される
        pass


def atomic_replace(tmp_path: Union[str, Path], target: Union[str, Path]) -> str:
    """*tmp_path* を *target* にアトミックに移動し、シンボリックリンクを維持する。

    ``os.replace(tmp, target)`` は ``tmp`` を ``target`` にアトミックに置き換える。
    しかし *target* がシンボリックリンクの場合、リンク自体が通常ファイルに置き換えられてしまい、
    ``config.yaml`` / ``SOUL.md`` / ``auth.json`` などを
    ``~/.hermes/`` から git 管理のプロファイルパッケージや dotfiles リポジトリに
    シンボリックリンクしている管理デプロイメントが静かに切り離されてしまう（GitHub #16743）。

    このヘルパーは先にシンボリックリンクを解決するため、``os.replace`` は
    実体のファイルに in-place で書き込み、シンボリックリンクは維持される。
    非シンボリックリンクおよび存在しないパスでは、単純な ``os.replace`` と同様に動作する。

    置換に使用された実際の解決済みパスを返すので、呼び出し側が
    パーミッションを再適用する際にシンボリックリンクではなく実体パスを対象にできる。

    Args:
        tmp_path: テンポラリファイルのパス。
        target: 置き換え先のターゲットパス。

    Returns:
        置換に使用された解決済みの実パス。
    """
    target_str = str(target)
    real_path = os.path.realpath(target_str) if os.path.islink(target_str) else target_str
    os.replace(str(tmp_path), real_path)
    return real_path


def atomic_json_write(
    path: Union[str, Path],
    data: Any,
    *,
    indent: int = 2,
    **dump_kwargs: Any,
) -> None:
    """JSON データをファイルにアトミックに書き込む。

    テンポラリファイル + fsync + os.replace を使用して、ターゲットファイルが
    中途半端に書き込まれた状態になることがないようにする。
    書き込み中にプロセスがクラッシュしても、以前のバージョンのファイルはそのまま残る。

    Args:
        path: ターゲットファイルパス（存在しなければ作成、存在すれば上書き）。
        data: JSON シリアライズ可能なデータ。
        indent: JSON のインデント（デフォルト 2）。
        **dump_kwargs: json.dump() に渡す追加のキーワード引数（例: default=str）。
    """
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)

    original_mode = _preserve_file_mode(path)

    fd, tmp_path = tempfile.mkstemp(
        dir=str(path.parent),
        prefix=f".{path.stem}_",
        suffix=".tmp",
    )
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(
                data,
                f,
                indent=indent,
                ensure_ascii=False,
                **dump_kwargs,
            )
            f.flush()
            os.fsync(f.fileno())
        # シンボリックリンクを維持 — 実体ファイルに in-place で書き込む（GitHub #16743）
        real_path = atomic_replace(tmp_path, path)
        _restore_file_mode(real_path, original_mode)
    except BaseException:
        # 意図的に BaseException をキャッチし、KeyboardInterrupt/SystemExit が
        # 発生してもテンポラリファイルのクリーンアップを実行してから再送出する。
        try:
            os.unlink(tmp_path)
        except OSError:
            pass
        raise


def atomic_yaml_write(
    path: Union[str, Path],
    data: Any,
    *,
    default_flow_style: bool = False,
    sort_keys: bool = False,
    extra_content: str | None = None,
) -> None:
    """YAML データをファイルにアトミックに書き込む。

    テンポラリファイル + fsync + os.replace を使用して、ターゲットファイルが
    中途半端に書き込まれた状態になることがないようにする。
    書き込み中にプロセスがクラッシュしても、以前のバージョンのファイルはそのまま残る。

    Args:
        path: ターゲットファイルパス（存在しなければ作成、存在すれば上書き）。
        data: YAML シリアライズ可能なデータ。
        default_flow_style: YAML フロースタイル（デフォルト False）。
        sort_keys: 辞書のキーをソートするかどうか（デフォルト False）。
        extra_content: YAML ダンプの後に追加するオプションの文字列
            （例: ユーザー参照用のコメントアウトされたセクション）。
    """
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)

    original_mode = _preserve_file_mode(path)

    fd, tmp_path = tempfile.mkstemp(
        dir=str(path.parent),
        prefix=f".{path.stem}_",
        suffix=".tmp",
    )
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            yaml.dump(data, f, default_flow_style=default_flow_style, sort_keys=sort_keys)
            if extra_content:
                f.write(extra_content)
            f.flush()
            os.fsync(f.fileno())
        # シンボリックリンクを維持 — 実体ファイルに in-place で書き込む（GitHub #16743）
        real_path = atomic_replace(tmp_path, path)
        _restore_file_mode(real_path, original_mode)
    except BaseException:
        # atomic_json_write と同様に、プロセスレベルの割り込みでも
        # クリーンアップを実行してから再送出する。
        try:
            os.unlink(tmp_path)
        except OSError:
            pass
        raise


# ─── JSON ヘルパー ─────────────────────────────────────────────────────────────


def safe_json_loads(text: str, default: Any = None) -> Any:
    """JSON をパースし、パースエラー時は *default* を返す。

    display.py, anthropic_adapter.py, auxiliary_client.py などで重複している
    ``try: json.loads(x) except (JSONDecodeError, TypeError)`` パターンを置き換える。

    Args:
        text: JSON 文字列。
        default: パースエラー時のデフォルト値。

    Returns:
        パースされたオブジェクト、またはデフォルト値。
    """
    try:
        return json.loads(text)
    except (json.JSONDecodeError, TypeError, ValueError):
        return default


# ─── 環境変数ヘルパー ─────────────────────────────────────────────────────────


def env_int(key: str, default: int = 0) -> int:
    """環境変数を整数として読み込む。フォールバック値付き。

    Args:
        key: 環境変数名。
        default: パース失敗時または未設定時のデフォルト値。

    Returns:
        整数値、またはデフォルト値。
    """
    raw = os.getenv(key, "").strip()
    if not raw:
        return default
    try:
        return int(raw)
    except (ValueError, TypeError):
        return default


def env_bool(key: str, default: bool = False) -> bool:
    """環境変数を真偽値として読み込む。

    Args:
        key: 環境変数名。
        default: 未設定時またはパース失敗時のデフォルト値。

    Returns:
        真偽値。
    """
    return is_truthy_value(os.getenv(key, ""), default=default)


# ─── プロキシヘルパー ──────────────────────────────────────────────────────────


_PROXY_ENV_KEYS = (
    "HTTPS_PROXY", "HTTP_PROXY", "ALL_PROXY",
    "https_proxy", "http_proxy", "all_proxy",
)


def normalize_proxy_url(proxy_url: str | None) -> str | None:
    """プロキシ URL を httpx/aiohttp 互換に正規化する。

    WSL/Clash 環境では SOCKS プロキシを ``socks://127.0.0.1:PORT`` として
    エクスポートすることがよくある。httpx はそのエイリアスを拒否し、
    明示的な ``socks5://`` スキームを期待する。

    Args:
        proxy_url: 正規化するプロキシ URL。

    Returns:
        正規化されたプロキシ URL、または None。
    """
    candidate = str(proxy_url or "").strip()
    if not candidate:
        return None
    if candidate.lower().startswith("socks://"):
        return f"socks5://{candidate[len('socks://'):]}"
    return candidate


def normalize_proxy_env_vars() -> None:
    """サポートされているプロキシ環境変数を正規化された URL 形式に in-place で書き換える。"""
    for key in _PROXY_ENV_KEYS:
        value = os.getenv(key, "")
        normalized = normalize_proxy_url(value)
        if normalized and normalized != value:
            os.environ[key] = normalized


# ─── URL パースヘルパー ──────────────────────────────────────────────────────


def base_url_hostname(base_url: str) -> str:
    """ベース URL から小文字のホスト名を返す。存在しない場合は ``""`` を返す。

    既知のプロバイダホスト（``api.openai.com``、``api.x.ai``、``api.anthropic.com``）
    との比較には、ホスト名の完全一致を使用する。生の URL に対する部分文字列マッチは
    使用しない。部分文字列チェックは、攻撃者またはプロキシが制御するパス/ホスト
    （``https://api.openai.com.example/v1`` や ``https://proxy.test/api.openai.com/v1`` など）
    をネイティブエンドポイントとして誤認識し、api_mode / 認証ルーティングが
    誤ったものになる原因となる。

    Args:
        base_url: ベース URL。

    Returns:
        小文字のホスト名、または空文字列。
    """
    raw = (base_url or "").strip()
    if not raw:
        return ""
    parsed = urlparse(raw if "://" in raw else f"//{raw}")
    return (parsed.hostname or "").lower().rstrip(".")


def base_url_host_matches(base_url: str, domain: str) -> bool:
    """ベース URL のホスト名が *domain* またはそのサブドメインの場合に True を返す。

    ``domain in base_url`` の部分文字列マッチよりも安全な代替手段。
    部分文字列マッチは ``base_url_hostname`` で文書化されている偽陽性クラスに該当する。
    ベアホスト、完全な URL、パス付き URL に対応。

    使用例::

        base_url_host_matches("https://api.moonshot.ai/v1", "moonshot.ai") == True
        base_url_host_matches("https://moonshot.ai", "moonshot.ai")        == True
        base_url_host_matches("https://evil.com/moonshot.ai/v1", "moonshot.ai") == False
        base_url_host_matches("https://moonshot.ai.evil/v1", "moonshot.ai")     == False

    Args:
        base_url: ベース URL。
        domain: 比較するドメイン。

    Returns:
        ホスト名がドメインまたはそのサブドメインであれば True。
    """
    hostname = base_url_hostname(base_url)
    if not hostname:
        return False
    domain = (domain or "").strip().lower().rstrip(".")
    if not domain:
        return False
    return hostname == domain or hostname.endswith("." + domain)
