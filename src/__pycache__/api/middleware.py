import time
from collections import defaultdict

from fastapi import Request, Response
from loguru import logger
from starlette.middleware.base import BaseHTTPMiddleware

# Simple in-process rate limiter — replace with Redis in production
_request_counts: dict[str, list[float]] = defaultdict(list)
RATE_LIMIT = 60  # requests per window
WINDOW_SEC = 60  # 1 minute window


class RateLimitMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        client_ip = request.client.host if request.client else "unknown"
        now = time.time()
        window_start = now - WINDOW_SEC

        # Prune old timestamps
        _request_counts[client_ip] = [
            t for t in _request_counts[client_ip] if t > window_start
        ]

        if len(_request_counts[client_ip]) >= RATE_LIMIT:
            return Response(
                content='{"detail":"Rate limit exceeded. Max 60 requests/minute."}',
                status_code=429,
                media_type="application/json",
            )

        _request_counts[client_ip].append(now)
        return await call_next(request)


async def log_requests(request: Request, call_next):
    """Log every request with method, path, status code, and duration."""
    start = time.perf_counter()
    response = await call_next(request)
    duration_ms = (time.perf_counter() - start) * 1000
    logger.info(
        "{method} {path} -> {status} ({duration:.1f}ms)",
        method=request.method,
        path=request.url.path,
        status=response.status_code,
        duration=duration_ms,
    )
    return response