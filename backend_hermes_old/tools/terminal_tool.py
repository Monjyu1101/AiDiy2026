"""
端末（シェル）コマンド実行ツール。

LocalEnvironment をラップし、OpenAI 関数呼び出し形式のスキーマで
コマンド実行を提供する。``registry.register()`` により自己登録する。
"""

import sys
import threading
from tools.registry import registry, tool_result, tool_error
from tools.environments.local import LocalEnvironment

_callback_tls = threading.local()


def _get_approval_callback():
    """危険コマンド確認用のコールバックを現在スレッドから取得する。"""

    return getattr(_callback_tls, "approval", None)


def set_approval_callback(cb):
    """危険コマンド確認用のコールバックを現在スレッドへ登録する。

    旧版の `delegate_tool` がこの関数を import するため、AiDiy 版でも互換 API
    として残す。現行の簡易 terminal ツールは承認 UI を持たないが、サブエージェント
    側の import エラーを防ぐために必要。
    """

    _callback_tls.approval = cb


def terminal_handler(args: dict, **kwargs) -> str:
    """terminal ツールのハンドラ関数。

    Args:
        args: {
            "command":    str,       # 実行するコマンド（必須）
            "timeout":    int,       # タイムアウト秒数（任意、デフォルト 180）
            "workdir":    str,       # 作業ディレクトリ（任意）
            "background": bool,      # バックグラウンド実行フラグ（ハーネスでは無視）
            "pty":        bool,      # PTY モード（任意、ローカル環境では未対応）
        }

    Returns:
        JSON 文字列（tool_result または tool_error 形式）。
    """
    command = args.get("command")
    if not command or not isinstance(command, str):
        return tool_error("command は必須の文字列パラメータです")

    # タイムアウトを 10〜600 秒にクランプ
    timeout = args.get("timeout", 180)
    if timeout is not None:
        try:
            timeout = int(timeout)
        except (ValueError, TypeError):
            timeout = 180
        timeout = max(10, min(600, timeout))

    # 作業ディレクトリ
    workdir = args.get("workdir")

    # background フラグはハーネスでは常にフォアグラウンドとして扱う（無視）
    # pty フラグは LocalEnvironment が未対応のため現時点では無視

    # 環境を初期化
    env = LocalEnvironment()

    # Linux では文字列コマンドを sh -c でラップする
    # Windows では shell=True によりそのまま実行される
    if sys.platform != "win32" and isinstance(command, str):
        prepared_command = ["sh", "-c", command]
    else:
        prepared_command = command

    try:
        result = env.run_command(
            command=prepared_command,
            cwd=workdir,
            timeout=timeout,
        )
    except Exception as e:
        return tool_error(f"コマンド実行中に予期しないエラーが発生しました: {e}")

    if result.get("error"):
        return tool_error(
            result["error"],
            output=result.get("output", ""),
            exit_code=result.get("exit_code", -1),
        )

    return tool_result(
        output=result.get("output", ""),
        exit_code=result.get("exit_code", 0),
    )


# OpenAI 形式の関数スキーマ
_terminal_schema = {
    "description": "ローカルシェルでコマンドを実行します。"
    "Linux では sh -c 経由、Windows では shell=True で実行されます。",
    "parameters": {
        "type": "object",
        "properties": {
            "command": {
                "type": "string",
                "description": "実行するシェルコマンド。複数行やパイプ、リダイレクトも使用可能。",
            },
            "timeout": {
                "type": "integer",
                "description": "コマンドのタイムアウト秒数。最小10秒、最大600秒。デフォルトは180秒。",
                "default": 180,
            },
            "workdir": {
                "type": "string",
                "description": "コマンドを実行する作業ディレクトリの絶対パス。"
                "指定しない場合はプロセスのカレントディレクトリが使用される。",
            },
            "background": {
                "type": "boolean",
                "description": "バックグラウンド実行フラグ。"
                "現在のハーネスは常にフォアグラウンド実行として扱うため、このフラグは無視されます。",
                "default": False,
            },
            "pty": {
                "type": "boolean",
                "description": "疑似端末（PTY）モードで実行します。"
                "ローカル環境では未対応のため、このフラグは無視されます。",
                "default": False,
            },
        },
        "required": ["command"],
    },
}

# モジュールインポート時にレジストリに自己登録
registry.register(
    name="terminal",
    toolset="terminal",
    schema=_terminal_schema,
    handler=terminal_handler,
    description="ローカルシェルでコマンドを実行する",
    emoji="💻",
)
