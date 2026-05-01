"""AiDiy Hermes lightweight code execution tool."""

import os
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any, Dict

from tools.ansi_strip import strip_ansi
from tools.registry import registry, tool_error, tool_result


def _normalize_output(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, bytes):
        text = value.decode("utf-8", errors="replace")
    else:
        text = str(value)
    return strip_ansi(text)[-20000:]


def _handle_execute_code(args: Dict[str, Any], **_kw) -> str:
    code = str(args.get("code") or "")
    if not code.strip():
        return tool_error("code is required")

    language = str(args.get("language") or "python").strip().lower()
    timeout = int(args.get("timeout") or 30)
    timeout = max(1, min(timeout, 120))
    workdir = str(args.get("workdir") or "").strip() or None

    if language not in {"python", "py"}:
        return tool_error("only python is supported by this lightweight execute_code tool")

    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8:replace"

    with tempfile.TemporaryDirectory(prefix="aidiy_hermes_code_") as tmp:
        script = Path(tmp) / "snippet.py"
        script.write_text(code, encoding="utf-8")
        try:
            proc = subprocess.run(
                [sys.executable, str(script)],
                cwd=workdir,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                env=env,
                timeout=timeout,
            )
        except subprocess.TimeoutExpired as exc:
            return tool_error(
                f"code execution timed out after {timeout}s",
                stdout=_normalize_output(exc.stdout),
                stderr=_normalize_output(exc.stderr),
            )
        except Exception as exc:
            return tool_error(f"code execution failed: {exc}")

    return tool_result(
        success=proc.returncode == 0,
        exit_code=proc.returncode,
        stdout=_normalize_output(proc.stdout),
        stderr=_normalize_output(proc.stderr),
    )


EXECUTE_CODE_SCHEMA = {
    "description": "Run a short Python snippet in a temporary file and return stdout/stderr.",
    "parameters": {
        "type": "object",
        "properties": {
            "code": {"type": "string", "description": "Python code to execute."},
            "language": {"type": "string", "enum": ["python", "py"], "default": "python"},
            "timeout": {"type": "integer", "default": 30, "description": "Timeout seconds, max 120."},
            "workdir": {"type": "string", "description": "Optional working directory."},
        },
        "required": ["code"],
    },
}


registry.register(
    name="execute_code",
    toolset="code_execution",
    schema=EXECUTE_CODE_SCHEMA,
    handler=_handle_execute_code,
    description="短いPythonコードを実行する",
)
