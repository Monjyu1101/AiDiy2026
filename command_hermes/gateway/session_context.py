"""Session-scoped environment compatibility helpers.

The upstream Hermes tree uses this module when running inside messaging
gateways. AiDiy's Python-only CLI does not run a gateway, but shared tools still
import these helpers. Environment variables are enough for the CLI surface.
"""

from __future__ import annotations

import contextvars
import os
from contextlib import contextmanager
from typing import Iterator, Mapping


_session_env: contextvars.ContextVar[dict[str, str]] = contextvars.ContextVar(
    "hermes_session_env",
    default={},
)


def get_session_env(name: str, default: str = "") -> str:
    value = _session_env.get().get(name)
    if value is not None:
        return value
    return os.environ.get(name, default)


def set_session_env(values: Mapping[str, object] | None = None, **kwargs: object) -> None:
    merged = dict(_session_env.get())
    for source in (values or {}, kwargs):
        for key, value in source.items():
            if value is None:
                merged.pop(str(key), None)
            else:
                merged[str(key)] = str(value)
    _session_env.set(merged)


def clear_session_env() -> None:
    _session_env.set({})


@contextmanager
def session_env(values: Mapping[str, object] | None = None, **kwargs: object) -> Iterator[None]:
    token = _session_env.set(dict(_session_env.get()))
    try:
        set_session_env(values, **kwargs)
        yield
    finally:
        _session_env.reset(token)
