"""
ローカルターミナル実行バックエンド。

Windows / Linux 両対応。
subprocess.run をラップし、コマンドの実行結果を dict で返す。
"""

import os
import sys
import subprocess
import shutil
from typing import Optional


# 子プロセスへそのまま流さない Hermes / LLM プロバイダ系の環境変数。
_HERMES_PROVIDER_ENV_FORCE_PREFIX = "_HERMES_FORCE_"
_HERMES_PROVIDER_ENV_BLOCKLIST = frozenset(
    {
        "OPENAI_BASE_URL",
        "OPENAI_API_KEY",
        "OPENAI_API_BASE",
        "OPENAI_ORG_ID",
        "OPENAI_ORGANIZATION",
        "OPENROUTER_API_KEY",
        "ANTHROPIC_API_KEY",
        "ANTHROPIC_BASE_URL",
        "ANTHROPIC_TOKEN",
        "CLAUDE_CODE_OAUTH_TOKEN",
        "LLM_MODEL",
        "GOOGLE_API_KEY",
        "GEMINI_API_KEY",
        "DEEPSEEK_API_KEY",
        "MISTRAL_API_KEY",
        "GROQ_API_KEY",
        "TOGETHER_API_KEY",
        "PERPLEXITY_API_KEY",
        "COHERE_API_KEY",
        "FIREWORKS_API_KEY",
        "XAI_API_KEY",
        "HELICONE_API_KEY",
        "PARALLEL_API_KEY",
        "FIRECRAWL_API_KEY",
        "FIRECRAWL_API_URL",
        "GH_TOKEN",
        "GITHUB_TOKEN",
        "GITHUB_APP_ID",
        "GITHUB_APP_PRIVATE_KEY_PATH",
        "GITHUB_APP_INSTALLATION_ID",
    }
)


def _sanitize_subprocess_env(base_env: dict | None, extra_env: dict | None = None) -> dict:
    """子プロセス用の環境変数を作る。

    旧 Hermes の process_registry はこの関数を直接 import する。AiDiy 版では
    チャンネル系の大量設定は扱わないが、プロバイダ秘密情報の漏洩防止は維持する。
    `_HERMES_FORCE_FOO=bar` は明示上書きとして `FOO=bar` に展開する。
    """

    sanitized: dict[str, str] = {}
    for key, value in (base_env or {}).items():
        if key.startswith(_HERMES_PROVIDER_ENV_FORCE_PREFIX):
            continue
        if key not in _HERMES_PROVIDER_ENV_BLOCKLIST:
            sanitized[key] = value

    for key, value in (extra_env or {}).items():
        if key.startswith(_HERMES_PROVIDER_ENV_FORCE_PREFIX):
            real_key = key[len(_HERMES_PROVIDER_ENV_FORCE_PREFIX):]
            sanitized[real_key] = value
        elif key not in _HERMES_PROVIDER_ENV_BLOCKLIST:
            sanitized[key] = value

    return sanitized


def _find_shell() -> str:
    """対話/バックグラウンド実行用のシェルを返す。

    Windows では Git Bash があれば優先し、なければ PowerShell、最後に cmd.exe を使う。
    旧版は Git Bash 必須だったが、AiDiy 版は Windows 標準環境でも動くように緩める。
    """

    if sys.platform != "win32":
        return (
            shutil.which("bash")
            or os.environ.get("SHELL")
            or ("/bin/sh" if os.path.isfile("/bin/sh") else "sh")
        )

    custom = os.environ.get("HERMES_GIT_BASH_PATH")
    if custom and os.path.isfile(custom):
        return custom

    found = shutil.which("bash")
    if found:
        return found

    for candidate in (
        os.path.join(os.environ.get("ProgramFiles", r"C:\Program Files"), "Git", "bin", "bash.exe"),
        os.path.join(os.environ.get("ProgramFiles(x86)", r"C:\Program Files (x86)"), "Git", "bin", "bash.exe"),
        os.path.join(os.environ.get("LOCALAPPDATA", ""), "Programs", "Git", "bin", "bash.exe"),
    ):
        if candidate and os.path.isfile(candidate):
            return candidate

    return shutil.which("pwsh") or shutil.which("powershell") or os.environ.get("COMSPEC", "cmd.exe")


class LocalEnvironment:
    """ローカル環境でコマンドを実行するためのバックエンド。"""

    def run_command(
        self,
        command: list[str] | str,
        cwd: Optional[str] = None,
        timeout: Optional[int] = None,
        env: Optional[dict[str, str]] = None,
    ) -> dict:
        """
        コマンドを実行し、結果を dict で返す。

        Args:
            command: 実行するコマンド。
                     Linux ではリスト形式、Windows では文字列でもリストでも可。
            cwd:     作業ディレクトリ（存在しない場合は None 扱い）。
            timeout: タイムアウト秒数（None の場合はタイムアウトなし）。
            env:     環境変数（None の場合は親プロセスの環境を継承）。

        Returns:
            {
                "output":    str,       # 標準出力 + 標準エラー出力の結合テキスト
                "exit_code": int,       # プロセスの終了コード
                "error":     str | None # 例外発生時はエラーメッセージ、成功時は None
            }
        """
        # cwd の存在確認：存在しなければ None にする
        resolved_cwd = None
        if cwd is not None:
            if os.path.isdir(cwd):
                resolved_cwd = cwd
            else:
                # 警告は出さず、単に None にして subprocess のデフォルトに任せる
                resolved_cwd = None

        # OS によって shell フラグとコマンド形式を切り替え
        is_windows = sys.platform == "win32"

        try:
            proc = subprocess.run(
                command,
                capture_output=True,
                cwd=resolved_cwd,
                timeout=timeout,
                env=env,
                shell=is_windows,           # Windows では shell=True で .bat/.cmd 対応
                encoding="utf-8",
                errors="replace",
            )

            # 標準出力と標準エラーを結合（エラーは output にも含める）
            output_parts = []
            if proc.stdout:
                output_parts.append(proc.stdout)
            if proc.stderr:
                output_parts.append(proc.stderr)
            output = "\n".join(output_parts) if output_parts else ""

            return {
                "output": output.rstrip("\n"),
                "exit_code": proc.returncode,
                "error": None,
            }

        except subprocess.TimeoutExpired as e:
            # タイムアウト時は部分的出力があれば返す
            partial = ""
            if e.stdout:
                partial += e.stdout
            if e.stderr:
                if partial:
                    partial += "\n"
                partial += e.stderr
            return {
                "output": partial.rstrip("\n") if partial else "",
                "exit_code": -1,
                "error": f"コマンドがタイムアウトしました（制限: {timeout}秒）",
            }

        except FileNotFoundError as e:
            return {
                "output": "",
                "exit_code": -1,
                "error": f"コマンドが見つかりません: {e}",
            }

        except Exception as e:
            # その他の予期しないエラーもすべてキャッチして返す
            return {
                "output": "",
                "exit_code": -1,
                "error": f"コマンド実行中にエラーが発生しました: {e}",
            }
