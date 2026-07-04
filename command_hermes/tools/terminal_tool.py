#!/usr/bin/env python3
"""Platform selector for terminal tools."""

import importlib
import os

PLATFORM_TOOL_WRAPPER = True

_IMPL_MODULE = "tools.terminal_tool_win" if os.name == "nt" else "tools.terminal_tool_linux"
_impl = importlib.import_module(_IMPL_MODULE)

for _name, _value in vars(_impl).items():
    if _name in {"__name__", "__package__", "__loader__", "__spec__"}:
        continue
    globals()[_name] = _value

__all__ = [
    _name for _name in globals()
    if not (_name.startswith("__") and _name.endswith("__"))
]
