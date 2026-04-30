"""API error classification for smart failover and recovery."""
from __future__ import annotations

import enum
import logging
from dataclasses import dataclass
from typing import Optional

logger = logging.getLogger(__name__)


class FailoverReason(enum.Enum):
    """API 呼び出しが失敗した理由 — リカバリ戦略を決定する。"""

    auth = "auth"
    rate_limit = "rate_limit"
    overloaded = "overloaded"
    timeout = "timeout"
    bad_request = "bad_request"
    context_too_long = "context_too_long"
    model_not_found = "model_not_found"
    unknown = "unknown"


@dataclass
class ClassificationResult:
    """エラー分類の結果。"""
    reason: FailoverReason = FailoverReason.unknown
    retryable: bool = True
    message: str = ""
    status_code: Optional[int] = None
    raw_error: str = ""


_AUTH_PATTERNS = ["403", "unauthorized", "unauthorised", "invalid_api_key",
                  "authentication", "permission denied", "not authorized", "auth error"]
_RATE_LIMIT_PATTERNS = ["429", "rate limit", "too many requests", "rate_limit", "ratelimit"]
_OVERLOAD_PATTERNS = ["502", "503", "504", "service unavailable", "overloaded",
                      "internal server error", "bad gateway", "service temporarily"]
_TIMEOUT_PATTERNS = ["timeout", "timed out", "connection error", "connection refused",
                     "deadline exceeded", "read timeout", "connect timeout"]
_CONTEXT_TOO_LONG_PATTERNS = ["context length", "maximum context", "token limit",
                              "too many tokens", "context window"]


def classify_error(error: Exception, status_code: Optional[int] = None) -> ClassificationResult:
    """API エラーを分類する。

    Args:
        error: 発生した例外。
        status_code: オプションの HTTP ステータスコード。

    Returns:
        理由とリカバリ情報を含む ClassificationResult。
    """
    error_str = str(error).lower()
    result = ClassificationResult(
        raw_error=str(error),
        status_code=status_code,
    )

    if status_code:
        if status_code in (401, 403):
            result.reason = FailoverReason.auth
            result.retryable = True
            result.message = "Auth error — refresh key and retry"
            return result
        if status_code == 429:
            result.reason = FailoverReason.rate_limit
            result.retryable = True
            result.message = "Rate limited — backoff and retry"
            return result
        if status_code in (502, 503, 504):
            result.reason = FailoverReason.overloaded
            result.retryable = True
            result.message = "Server overloaded — fallback to another provider"
            return result
        if status_code == 400:
            result.reason = FailoverReason.bad_request
            result.retryable = False
            result.message = "Bad request — report to user"
            return result

    def _matches_any(patterns: list) -> bool:
        return any(p in error_str for p in patterns)

    if _matches_any(_AUTH_PATTERNS):
        result.reason = FailoverReason.auth
        result.message = "Auth error"
    elif _matches_any(_RATE_LIMIT_PATTERNS):
        result.reason = FailoverReason.rate_limit
        result.message = "Rate limited"
    elif _matches_any(_OVERLOAD_PATTERNS):
        result.reason = FailoverReason.overloaded
        result.message = "Server overloaded"
    elif _matches_any(_TIMEOUT_PATTERNS):
        result.reason = FailoverReason.timeout
        result.message = "Timeout"
    elif _matches_any(_CONTEXT_TOO_LONG_PATTERNS):
        result.reason = FailoverReason.context_too_long
        result.message = "Context too long"
    else:
        result.reason = FailoverReason.unknown
        result.message = f"Unknown error: {error}"

    return result
