"""AiDiy Hermes lightweight process tool."""

import os
import signal
import subprocess
import sys
from typing import Any, Dict

from tools.registry import registry, tool_error, tool_result


def _handle_process(args: Dict[str, Any], **_kw) -> str:
    action = str(args.get("action") or "list").strip().lower()

    if action == "list":
        if sys.platform == "win32":
            cmd = ["powershell", "-NoProfile", "-Command", "Get-Process | Select-Object -First 80 Id,ProcessName,CPU,WorkingSet | ConvertTo-Json -Compress"]
        else:
            cmd = ["ps", "-eo", "pid,comm,%cpu,%mem", "--sort=-%cpu"]
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
        return tool_result(success=proc.returncode == 0, output=proc.stdout[-20000:], stderr=proc.stderr[-4000:])

    if action == "kill":
        try:
            pid = int(args.get("pid"))
        except Exception:
            return tool_error("pid is required for kill")
        if pid == os.getpid():
            return tool_error("refusing to kill current process")
        try:
            if sys.platform == "win32":
                subprocess.run(["taskkill", "/PID", str(pid), "/T", "/F"], capture_output=True, text=True, timeout=15)
            else:
                os.kill(pid, signal.SIGTERM)
            return tool_result(success=True, pid=pid)
        except Exception as exc:
            return tool_error(f"failed to kill process {pid}: {exc}")

    return tool_error("action must be one of: list, kill")


PROCESS_SCHEMA = {
    "description": "List or terminate local processes.",
    "parameters": {
        "type": "object",
        "properties": {
            "action": {"type": "string", "enum": ["list", "kill"], "default": "list"},
            "pid": {"type": "integer", "description": "Process id for kill."},
        },
    },
}


registry.register(
    name="process",
    toolset="terminal",
    schema=PROCESS_SCHEMA,
    handler=_handle_process,
    description="ローカルプロセスを一覧表示または終了する",
)
