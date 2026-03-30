"""
Rate Limiting Utilities

Simple in-memory rate limiter with sliding window.
For production, use Redis-based rate limiting with slowapi.
"""

import asyncio
import time
from collections import defaultdict
from dataclasses import dataclass
from typing import Callable


@dataclass
class RateLimitConfig:
    requests_per_window: int
    window_seconds: float


class SlidingWindowRateLimiter:
    """
    Sliding window rate limiter with per-key tracking.

    Tracks request timestamps per key and enforces rate limits.
    """

    def __init__(self, config: RateLimitConfig):
        self.config = config
        self._requests: dict[str, list[float]] = defaultdict(list)
        self._lock = asyncio.Lock()

    async def is_allowed(self, key: str) -> tuple[bool, dict]:
        """
        Check if a request from `key` is allowed under the rate limit.

        Returns:
            (is_allowed, info) where info contains rate limit headers
        """
        async with self._lock:
            now = time.time()
            window_start = now - self.config.window_seconds

            request_times = self._requests[key]
            request_times = [t for t in request_times if t > window_start]
            self._requests[key] = request_times

            count = len(request_times)
            remaining = max(0, self.config.requests_per_window - count)

            if count >= self.config.requests_per_window:
                oldest = min(request_times) if request_times else now
                retry_after = oldest + self.config.window_seconds - now
                return False, {
                    "X-RateLimit-Limit": str(self.config.requests_per_window),
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Reset": str(int(oldest + self.config.window_seconds)),
                    "Retry-After": str(int(retry_after)),
                }

            if request_times:
                oldest = min(request_times)
                reset_time = oldest + self.config.window_seconds
            else:
                reset_time = now + self.config.window_seconds

            self._requests[key].append(now)

            return True, {
                "X-RateLimit-Limit": str(self.config.requests_per_window),
                "X-RateLimit-Remaining": str(remaining),
                "X-RateLimit-Reset": str(int(reset_time)),
            }

    async def reset(self, key: str) -> None:
        """Reset rate limit for a specific key."""
        async with self._lock:
            self._requests.pop(key, None)

    async def reset_all(self) -> None:
        """Reset all rate limits."""
        async with self._lock:
            self._requests.clear()


class RateLimitExceeded(Exception):
    """Exception raised when rate limit is exceeded."""

    def __init__(self, retry_after: int, headers: dict):
        self.retry_after = retry_after
        self.headers = headers
        super().__init__(f"Rate limit exceeded. Retry after {retry_after} seconds.")


def rate_limit(
    limiter: SlidingWindowRateLimiter,
    key_func: Callable = lambda: "default",
) -> Callable:
    """
    Decorator to add rate limiting to an endpoint.

    Usage:
        @router.post("/execute")
        @rate_limit(execute_limiter, key_func=lambda request: request.session_id)
        async def execute(request: ExecuteRequest):
            ...
    """

    def decorator(func: Callable) -> Callable:
        async def wrapper(*args, **kwargs):
            key = key_func(*args, **kwargs)
            is_allowed, headers = await limiter.is_allowed(key)

            if not is_allowed:
                raise RateLimitExceeded(
                    retry_after=int(headers.get("Retry-After", 60)),
                    headers=headers,
                )

            return await func(*args, **kwargs)

        return wrapper

    return decorator


DEFAULT_RATE_LIMIT = RateLimitConfig(requests_per_window=100, window_seconds=60.0)
EXECUTE_RATE_LIMIT = RateLimitConfig(requests_per_window=30, window_seconds=60.0)

execute_limiter = SlidingWindowRateLimiter(EXECUTE_RATE_LIMIT)
global_limiter = SlidingWindowRateLimiter(DEFAULT_RATE_LIMIT)
