import asyncio
import hashlib
import time
from collections import defaultdict, deque
from dataclasses import dataclass

from fastapi import HTTPException, Request, Response, status

# This file implements a simple "N requests per time window" limiter.
# Scope examples: chat, feedback, debug.
# It is in-memory, so limits apply per running app process.

# Result object returned by each limit check.
# Endpoints only need this object to decide allow/reject and set headers.
@dataclass
class RateLimitState:
    # True -> request can continue
    # False -> request must be rejected with 429
    allowed: bool
    # How many requests are left in this window after current check
    remaining: int
    # Seconds client should wait before retrying (used when blocked)
    retry_after: int
    # Seconds until this window fully resets
    reset_in: int


# Basic limiter for current phase: in-memory and process-local.
# Later, this can be replaced by Redis for multi-instance scaling.
class InMemoryRateLimiter:
    def __init__(self) -> None:
        # key -> list of accepted request timestamps still inside window
        self._buckets: dict[str, deque[float]] = defaultdict(deque)
        # Single async lock keeps bucket updates safe under concurrency.
        self._lock = asyncio.Lock()

    async def is_allowed(self, key: str, limit: int, window_sec: int) -> RateLimitState:
        # Monotonic clock is stable even if system time changes.
        now = time.monotonic()
        floor = now - window_sec

        async with self._lock:
            bucket = self._buckets[key]

            # Remove old entries that are no longer in the active window.
            while bucket and bucket[0] <= floor:
                bucket.popleft()

            # If already at limit, block request and tell client when to retry.
            if len(bucket) >= limit:
                retry_after = max(1, int(bucket[0] + window_sec - now))
                return RateLimitState(False, 0, retry_after, retry_after)

            # Otherwise accept, store timestamp, and compute remaining quota.
            bucket.append(now)
            remaining = max(0, limit - len(bucket))
            reset_in = max(1, int(bucket[0] + window_sec - now))
            return RateLimitState(True, remaining, 0, reset_in)


# Shared limiter instance used by dependency helpers.
limiter = InMemoryRateLimiter()

# Build caller key as: <scope>:<hashed-identity>
# We hash API key/IP so we do not store raw sensitive values.
def _caller_key(request: Request, scope: str) -> str:
    raw = request.headers.get("x-api-key") or (request.client.host if request.client else "unknown")
    digest = hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]
    return f"{scope}:{digest}"


# Reusable helper for route dependencies.
# It checks quota, writes informative headers, and raises 429 when exceeded.
async def enforce_rate_limit(
    request: Request,
    response: Response,
    *,
    scope: str,
    limit: int,
    window_sec: int,
) -> None:
    # Build per-scope caller identity and evaluate quota.
    key = _caller_key(request, scope)
    state = await limiter.is_allowed(key, limit, window_sec)

    # Expose current quota state to clients.
    response.headers["X-RateLimit-Limit"] = str(limit)
    response.headers["X-RateLimit-Remaining"] = str(state.remaining)
    response.headers["X-RateLimit-Reset"] = str(state.reset_in)

    if not state.allowed:
        # Retry-After is standard for throttled responses.
        response.headers["Retry-After"] = str(state.retry_after)
        # When raising HTTPException, include all quota headers here as well
        # so 429 responses preserve the same metadata contract.
        error_headers = {
            "Retry-After": str(state.retry_after),
            "X-RateLimit-Limit": str(limit),
            "X-RateLimit-Remaining": str(state.remaining),
            "X-RateLimit-Reset": str(state.reset_in),
        }
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail={
                "error": "Too Many Requests",
                "scope": scope,
                "limit": limit,
                "window_sec": window_sec,
                "retry_after": state.retry_after,
            },
            headers=error_headers,
        )