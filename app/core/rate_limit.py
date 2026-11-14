"""Small single-process fixed-window rate limiter for the initial deployment."""

from __future__ import annotations

import asyncio
import time
from collections import defaultdict

from app.core.errors import AppError


class FixedWindowLimiter:
    def __init__(self) -> None:
        self._windows: dict[tuple[str, int], int] = defaultdict(int)
        self._lock = asyncio.Lock()

    async def check(self, key: str, limit: int, period_seconds: int = 60) -> None:
        if limit < 1 or period_seconds < 1:
            return
        now = int(time.time())
        window_start = now - now % period_seconds
        window_key = (key, window_start)
        async with self._lock:
            self._windows[window_key] += 1
            count = self._windows[window_key]
            cutoff = now - period_seconds * 2
            stale = [candidate for candidate in self._windows if candidate[1] < cutoff]
            for candidate in stale:
                del self._windows[candidate]
        if count > limit:
            retry_after = max(1, period_seconds - (now - window_start))
            raise AppError(
                "rate_limited",
                "Too many requests",
                "The request budget has been exceeded. Try again later.",
                status_code=429,
                retryable=True,
                extra={"retry_after": retry_after},
            )


limiter = FixedWindowLimiter()
