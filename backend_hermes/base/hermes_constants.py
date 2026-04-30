"""Hermes Harness 用の共有定数。

依存関係のないインポートセーフなモジュール — どこからでもインポート可能で、
循環インポートのリスクがありません。
"""

import os
from pathlib import Path


def get_hermes_home() -> Path:
    """Hermes ホームディレクトリを返す（デフォルト: ~/.hermes）。

    HERMES_HOME 環境変数を読み取り、未設定の場合は ~/.hermes にフォールバック。
    これが唯一の情報源 — 他のコピーはすべてこれをインポートすべき。
    """
    val = os.environ.get("HERMES_HOME", "").strip()
    return Path(val) if val else Path.home() / ".hermes"


def get_default_hermes_root() -> Path:
    """プロファイルレベルの操作のためのルート Hermes ディレクトリを返す。

    標準的なデプロイでは ``~/.hermes`` になります。

    Docker やカスタムデプロイで ``HERMES_HOME`` が ``~/.hermes`` の外を
    指している場合（例: ``/opt/data``）、``HERMES_HOME`` をそのまま返します
    — それがルートです。

    プロファイルモードで ``HERMES_HOME`` が ``<root>/profiles/<name>`` の
    場合、``<root>`` を返して ``profile list`` が全プロファイルを
    見られるようにします。
    標準レイアウト（``~/.hermes/profiles/coder``）と Docker レイアウト
    （``/opt/data/profiles/coder``）の両方で動作します。

    インポートセーフ — stdlib 以外の依存関係は不要。
    """
    native_home = Path.home() / ".hermes"
    env_home = os.environ.get("HERMES_HOME", "")
    if not env_home:
        return native_home
    env_path = Path(env_home)
    try:
        env_path.resolve().relative_to(native_home.resolve())
        # HERMES_HOME は ~/.hermes 配下（通常モードまたはプロファイルモード）
        return native_home
    except ValueError:
        pass

    # Docker / カスタムデプロイ
    # プロファイルパスかどうかをチェック: <root>/profiles/<name>
    # 親ディレクトリ名が "profiles" の場合、ルートは祖父母ディレクトリ
    # — Docker プロファイルも正しくカバー
    if env_path.parent.name == "profiles":
        return env_path.parent.parent

    # プロファイルパスではない — HERMES_HOME 自体がルート
    return env_path


def get_optional_skills_dir(default: Path | None = None) -> Path:
    """オプションスキルディレクトリを返す。パッケージマネージャラッパーに対応。

    パッケージインストールでは ``optional-skills`` が Python パッケージツリーの
    外に配置され、``HERMES_OPTIONAL_SKILLS`` 経由で公開されることがあります。
    """
    override = os.getenv("HERMES_OPTIONAL_SKILLS", "").strip()
    if override:
        return Path(override)
    if default is not None:
        return default
    return get_hermes_home() / "optional-skills"


def get_hermes_dir(new_subpath: str, old_name: str) -> Path:
    """Hermes サブディレクトリを解決する。下位互換性あり。

    新規インストールは統合レイアウトを使用（例: ``cache/images``）。
    既存のインストールで古いパス（例: ``image_cache``）がすでにある場合は
    そのまま使い続けます — 移行不要。

    Args:
        new_subpath: HERMES_HOME からの推奨パス（例: ``"cache/images"``）。
        old_name: HERMES_HOME からのレガシーパス（例: ``"image_cache"``）。

    Returns:
        絶対 ``Path`` — 古い場所がディスク上に存在すればそちらを、
        そうでなければ新しい場所を返す。
    """
    home = get_hermes_home()
    old_path = home / old_name
    if old_path.exists():
        return old_path
    return home / new_subpath


def display_hermes_home() -> str:
    """現在の HERMES_HOME をユーザーフレンドリーな表示文字列で返す。

    可読性のために ``~/`` の短縮形を使用::

        default:  ``~/.hermes``
        profile:  ``~/.hermes/profiles/coder``
        custom:   ``/opt/hermes-custom``

    これは **ユーザー向け** の print/log メッセージで使用し、``~/.hermes`` を
    ハードコードしないこと。実際の ``Path`` が必要なコードでは
    :func:`get_hermes_home` を使用。
    """
    home = get_hermes_home()
    try:
        return "~/" + str(home.relative_to(Path.home()))
    except ValueError:
        return str(home)


def get_subprocess_home() -> str | None:
    """サブプロセス用のプロファイル別 HOME ディレクトリを返す。なければ None。

    ``{HERMES_HOME}/home/`` がディスク上に存在する場合、サブプロセスは
    それを ``HOME`` として使用し、システムツール（git, ssh, gh, npm …）の
    設定を OS レベルの ``/root`` や ``~/`` ではなく Hermes データディレクトリ
    内に書き込むようにする。これにより:

    * **Docker の永続性** — ツールの設定が永続ボリューム内に配置される。
    * **プロファイルの分離** — 各プロファイルが独自の git 識別情報、SSH 鍵、
      gh トークンなどを持つ。

    Python プロセス自身の ``os.environ["HOME"]`` や ``Path.home()`` は
    **決して**変更されません — サブプロセスの環境のみがこの値を注入すべきです。
    アクティベーションはディレクトリベース: ``home/`` サブディレクトリが
    存在しなければ ``None`` を返し、動作は変わりません。
    """
    hermes_home = os.getenv("HERMES_HOME")
    if not hermes_home:
        return None
    profile_home = os.path.join(hermes_home, "home")
    if os.path.isdir(profile_home):
        return profile_home
    return None


VALID_REASONING_EFFORTS = ("minimal", "low", "medium", "high", "xhigh")


def parse_reasoning_effort(effort: str) -> dict | None:
    """推論努力レベルを設定 dict にパースする。

    有効なレベル: "none", "minimal", "low", "medium", "high", "xhigh"。
    入力が空または認識できない場合は None を返す（呼び出し側はデフォルトを使用）。
    "none" の場合は {"enabled": False} を返す。
    有効な努力レベルの場合は {"enabled": True, "effort": <level>} を返す。
    """
    if not effort or not effort.strip():
        return None
    effort = effort.strip().lower()
    if effort == "none":
        return {"enabled": False}
    if effort in VALID_REASONING_EFFORTS:
        return {"enabled": True, "effort": effort}
    return None


def is_termux() -> bool:
    """Termux（Android）環境内で実行中の場合に True を返す。

    ``TERMUX_VERSION``（Termux が設定）または Termux 固有の
    ``PREFIX`` パスをチェック。インポートセーフ — 重い依存関係なし。
    """
    prefix = os.getenv("PREFIX", "")
    return bool(os.getenv("TERMUX_VERSION") or "com.termux/files/usr" in prefix)


_wsl_detected: bool | None = None


def is_wsl() -> bool:
    """WSL（Windows Subsystem for Linux）内で実行中の場合に True を返す。

    ``/proc/version`` で WSL1 と WSL2 の両方が注入する ``microsoft``
    マーカーをチェック。結果はプロセス寿命中キャッシュされる。
    インポートセーフ — 重い依存関係なし。
    """
    global _wsl_detected
    if _wsl_detected is not None:
        return _wsl_detected
    try:
        with open("/proc/version", "r") as f:  # Windows ではファイルが存在しない
            _wsl_detected = "microsoft" in f.read().lower()
    except Exception:
        # Windows ではこの操作は無視される（/proc/version が存在しない）
        _wsl_detected = False
    return _wsl_detected


_container_detected: bool | None = None


def is_container() -> bool:
    """Docker/Podman コンテナ内で実行中の場合に True を返す。

    ``/.dockerenv``（Docker）、``/run/.containerenv``（Podman）、
    および ``/proc/1/cgroup`` のコンテナランタイムマーカーをチェック。
    結果はプロセス寿命中キャッシュされる。
    インポートセーフ — 重い依存関係なし。
    """
    global _container_detected
    if _container_detected is not None:
        return _container_detected
    if os.path.exists("/.dockerenv"):
        _container_detected = True
        return True
    if os.path.exists("/run/.containerenv"):
        _container_detected = True
        return True
    try:
        with open("/proc/1/cgroup", "r") as f:  # Windows ではファイルが存在しない
            cgroup = f.read()
            if "docker" in cgroup or "podman" in cgroup or "/lxc/" in cgroup:
                _container_detected = True
                return True
    except OSError:
        # Windows ではこの操作は無視される（/proc/1/cgroup が存在しない）
        pass
    _container_detected = False
    return False


# ─── 既知のパス ───


def get_config_path() -> Path:
    """HERMES_HOME 配下の ``config.yaml`` へのパスを返す。

    ``get_hermes_home() / "config.yaml"`` のパターンを置き換え、
    7つ以上のファイル（skill_utils.py, hermes_logging.py,
    hermes_time.py など）で繰り返されていたものを集約。
    """
    return get_hermes_home() / "config.yaml"


def get_skills_dir() -> Path:
    """HERMES_HOME 配下のスキルディレクトリへのパスを返す。"""
    return get_hermes_home() / "skills"


def get_env_path() -> Path:
    """HERMES_HOME 配下の ``.env`` ファイルへのパスを返す。"""
    return get_hermes_home() / ".env"


# ─── ネットワーク設定 ───


def apply_ipv4_preference(force: bool = False) -> None:
    """``socket.getaddrinfo`` をモンキーパッチして IPv4 接続を優先する。

    IPv6 が壊れているか到達不能なサーバーでは、Python は最初に AAAA
    レコードを試し、IPv4 にフォールバックする前に TCP タイムアウトの
    全時間を待機してハングします。
    これは httpx, requests, urllib, OpenAI SDK — ``socket.getaddrinfo``
    を使用するすべてのものに影響します。

    *force* が True の場合、``getaddrinfo`` をパッチして
    ``family=AF_UNSPEC``（デフォルト）の呼び出しを ``AF_INET`` として
    解決し、IPv6 を完全にスキップします。A レコードがない場合は、
    元のフィルタリングなし解決にフォールバックするため、純粋な IPv6
    ホストでも動作します。

    複数回呼び出しても安全 — パッチは一度だけ適用されます。
    有効にするには ``config.yaml`` で ``network.force_ipv4: true``
    を設定してください。
    """
    if not force:
        return

    import socket

    # 二重パッチの防止
    if getattr(socket.getaddrinfo, "_hermes_ipv4_patched", False):
        return

    _original_getaddrinfo = socket.getaddrinfo

    def _ipv4_getaddrinfo(host, port, family=0, type=0, proto=0, flags=0):
        if family == 0:  # AF_UNSPEC — 呼び出し側は特定の family を要求していない
            try:
                return _original_getaddrinfo(
                    host, port, socket.AF_INET, type, proto, flags
                )
            except socket.gaierror:
                # A レコードなし — フル解決にフォールバック（純粋 IPv6 ホスト用）
                return _original_getaddrinfo(host, port, family, type, proto, flags)
        return _original_getaddrinfo(host, port, family, type, proto, flags)

    _ipv4_getaddrinfo._hermes_ipv4_patched = True  # type: ignore[attr-defined]
    socket.getaddrinfo = _ipv4_getaddrinfo  # type: ignore[assignment]


OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"
OPENROUTER_MODELS_URL = f"{OPENROUTER_BASE_URL}/models"

AI_GATEWAY_BASE_URL = "https://ai-gateway.vercel.sh/v1"
