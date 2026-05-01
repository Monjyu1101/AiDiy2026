"""リトライユーティリティ — デコリレーションジッター付き指数バックオフ。"""
import random
import threading
import time

_jitter_counter = 0
_jitter_lock = threading.Lock()


def jittered_backoff(
    attempt: int,
    *,
    base_delay: float = 5.0,
    max_delay: float = 120.0,
    jitter_ratio: float = 0.5,
) -> float:
    """Compute a jittered exponential backoff delay.

    Args:
        attempt: 1-based retry attempt number.
        base_delay: Base delay in seconds for attempt 1.
        max_delay: Maximum delay in seconds.
        jitter_ratio: Jitter ratio (default 0.5 = ±50%).
    """
    exponential_delay = base_delay * (2 ** (attempt - 1))
    clamped = min(exponential_delay, max_delay)

    with _jitter_lock:
        global _jitter_counter
        _jitter_counter += 1
        seed = hash((attempt, _jitter_counter))

    rng = random.Random(seed)
    jitter_width = clamped * jitter_ratio
    return clamped - jitter_width + rng.random() * 2 * jitter_width


def retry(
    fn,
    max_attempts: int = 3,
    base_delay: float = 5.0,
    *args,
    **kwargs,
):
    """Execute a function with retry on failure."""
    last_error = None
    for attempt in range(1, max_attempts + 1):
        try:
            return fn(*args, **kwargs)
        except Exception as e:
            last_error = e
            if attempt < max_attempts:
                delay = jittered_backoff(attempt, base_delay=base_delay)
                time.sleep(delay)
    raise last_error  # type: ignore[misc]
