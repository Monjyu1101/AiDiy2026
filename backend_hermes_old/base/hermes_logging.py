"""Hermes Harness 向け集中ログ設定。

単一の ``setup_logging()`` エントリポイントを提供します。
CLI やゲートウェイが起動時に呼び出します。

セッションコンテキスト:
    ``set_session_context(session_id)`` を会話開始時に呼び、
    ``clear_session_context()`` を終了時に呼びます。
    同じスレッド上の全ログ行に ``[session_id]`` が付与されます。
"""

import logging
import sys
import threading

# setup_logging() が既に実行されたかどうかを追跡するセンチネル。
# 2回目の呼び出しは force=True でない限り no-op です。
_logging_initialized = False

# スレッドローカルなセッションコンテキスト（会話単位）。
_session_context = threading.local()

# デフォルトのログフォーマット。
# %(session_tag)s は _install_session_record_factory() によって
# 全ての LogRecord に自動注入されます。
_LOG_FORMAT = "%(asctime)s %(levelname)s%(session_tag)s %(name)s: %(message)s"
_LOG_FORMAT_VERBOSE = (
    "%(asctime)s - %(name)s - %(levelname)s%(session_tag)s - %(message)s"
)

# DEBUG/INFO レベルでノイズが多いサードパーティロガー。
_NOISY_LOGGERS = (
    "openai",
    "httpx",
    "httpcore",
    "urllib3",
)


# ---------------------------------------------------------------------------
# 公開セッションコンテキスト API
# ---------------------------------------------------------------------------


def set_session_context(session_id: str) -> None:
    """現在のスレッドにセッション ID を設定します。

    以後、このスレッド上の全ログレコードに ``[session_id]`` が
    フォーマット出力に含まれます。``run_conversation()`` の開始時に
    呼び出してください。
    """
    _session_context.session_id = session_id


def clear_session_context() -> None:
    """現在のスレッドのセッション ID をクリアします。"""
    _session_context.session_id = None


# ---------------------------------------------------------------------------
# LogRecord ファクトリ — 全てのレコードに session_tag を注入
# ---------------------------------------------------------------------------


def _install_session_record_factory() -> None:
    """グローバルな LogRecord ファクトリを差し替え、``session_tag`` を追加します。

    ``logging.Filter`` とは異なり、レコードファクトリはプロセス内の
    全てのレコードで実行されるため、``%(session_tag)s`` が常に
    フォーマット文字列で利用可能であることが保証されます。

    idempotent — モジュールが再読み込みされても二重適用を防ぐため、
    マーカー属性をチェックします。
    """
    current_factory = logging.getLogRecordFactory()
    if getattr(current_factory, "_hermes_session_injector", False):
        return  # 既にインストール済み

    def _session_record_factory(*args, **kwargs):
        record = current_factory(*args, **kwargs)
        sid = getattr(_session_context, "session_id", None)
        record.session_tag = f" [{sid}]" if sid else ""
        return record

    _session_record_factory._hermes_session_injector = True
    logging.setLogRecordFactory(_session_record_factory)


# インポート時に即座にインストール。setup_logging() が呼ばれる前でも
# session_tag は全てのレコードで利用可能になります。
_install_session_record_factory()


# ---------------------------------------------------------------------------
# メインのセットアップ
# ---------------------------------------------------------------------------


def setup_logging(
    *,
    log_level: str | None = None,
    verbose: bool = False,
    force: bool = False,
) -> None:
    """Hermes ログサブシステムを設定します。

    複数回呼び出しても安全です — 2回目以降は *force* が ``True`` でない限り
    no-op となります。

    Parameters
    ----------
    log_level
        最小ログレベル。標準の Python レベル名（``"DEBUG"``, ``"INFO"``,
        ``"WARNING"``）を受け付けます。デフォルトは ``"INFO"``。
    verbose
        ``True`` の場合、より詳細なフォーマット（``_LOG_FORMAT_VERBOSE``）を
        使用します。
    force
        既に初期化済みでも再実行します。
    """
    global _logging_initialized

    if _logging_initialized and not force:
        return

    root = logging.getLogger()
    level_name = (log_level or "INFO").upper()
    level = getattr(logging, level_name, logging.INFO)

    if force:
        for h in root.handlers[:]:
            root.removeHandler(h)

    if not any(isinstance(h, logging.StreamHandler) for h in root.handlers):
        handler = logging.StreamHandler(sys.stderr)
        handler.setLevel(level)
        fmt = _LOG_FORMAT_VERBOSE if verbose else _LOG_FORMAT
        handler.setFormatter(logging.Formatter(fmt, datefmt="%H:%M:%S"))
        root.addHandler(handler)

    root.setLevel(level)

    for name in _NOISY_LOGGERS:
        logging.getLogger(name).setLevel(logging.WARNING)

    _logging_initialized = True


def setup_verbose_logging() -> None:
    """``--verbose`` / ``-v`` モード向けに DEBUG レベルのコンソールログを有効にします。

    ``AIAgent.__init__()`` から ``verbose_logging=True`` のときに呼ばれます。
    """
    root = logging.getLogger()

    # 重複した StreamHandler の追加を防ぐ。
    for h in root.handlers:
        if isinstance(h, logging.StreamHandler):
            if getattr(h, "_hermes_verbose", False):
                return

    handler = logging.StreamHandler()
    handler.setLevel(logging.DEBUG)
    handler.setFormatter(
        logging.Formatter(_LOG_FORMAT_VERBOSE, datefmt="%H:%M:%S")
    )
    handler._hermes_verbose = True
    root.addHandler(handler)

    # DEBUG レコードが全てのハンドラに届くようルートロガーのレベルを下げる。
    if root.level > logging.DEBUG:
        root.setLevel(logging.DEBUG)

    # サードパーティライブラリは WARNING に抑えてノイズを削減。
    for name in _NOISY_LOGGERS:
        logging.getLogger(name).setLevel(logging.WARNING)
