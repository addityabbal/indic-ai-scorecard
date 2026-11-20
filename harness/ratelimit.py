"""Per-provider pacing, retry on 429 honouring retry-after, and a clean stop at a daily limit."""
from __future__ import annotations

import time

from .providers import RateLimited


class DailyLimitReached(Exception):
    """Raised when a provider keeps refusing: stop now, the next run resumes from the cache."""


class Pacer:
    def __init__(self) -> None:
        self.last: dict[str, float] = {}

    def wait(self, key: str, rpm: float) -> None:
        gap = 60.0 / max(rpm, 1)
        since = time.monotonic() - self.last.get(key, 0)
        if since < gap:
            time.sleep(gap - since)
        self.last[key] = time.monotonic()


def with_retry(call, pacer: Pacer, key: str, rpm: float, attempts: int = 4, sleep=time.sleep):
    for attempt in range(attempts):
        pacer.wait(key, rpm)
        try:
            return call()
        except RateLimited as error:
            wait = error.retry_after if error.retry_after is not None else 10 * (2 ** attempt)
            # A wait of more than 10 minutes means a daily or token-per-day cap: stop for today.
            if wait > 600 or "per day" in str(error).lower() or "daily" in str(error).lower():
                raise DailyLimitReached(str(error)) from error
            if attempt < attempts - 1:
                sleep(wait)
    raise DailyLimitReached(f"{key}: still rate limited after {attempts} attempts")
