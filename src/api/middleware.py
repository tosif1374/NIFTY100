import os
import time

import redis.asyncio as aioredis
from fastapi import Request, Response
from loguru import logger
from starlette.middleware.base import BaseHTTPMiddleware

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

RATE_LIMIT = 60  # requests per minute
WINDOW_SEC = 60  # 1 minute
KEY_PREFIX = "rl:"

# Shared Redis client
redis_client = aioredis.from_url(
    REDIS_URL,
    decode_responses=True
)


class RateLimitMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        client_ip = request.client.host if request.client else "unknown"
        key = f"{KEY_PREFIX}{client_ip}"

        try:
            # Atomic increment + expiry
            async with redis_client.pipeline(transaction=True) as pipe:
                pipe.incr(key)
                pipe.expire(key, WINDOW_SEC)
                results = await pipe.execute()

            count = results[0]

            if count > RATE_LIMIT:
                logger.warning(
                    "Rate limit exceeded for IP {}",
                    client_ip
                )

                return Response(
                    content='{"detail":"Rate limit exceeded. Max 60 requests/minute."}',
                    status_code=429,
                    media_type="application/json",
                    headers={
                        "X-RateLimit-Limit": str(RATE_LIMIT),
                        "X-RateLimit-Remaining": "0",
                        "Retry-After": str(WINDOW_SEC),
                    },
                )

        except aioredis.RedisError as e:
            # Fail open if Redis is unavailable
            logger.error(
                "Redis unavailable for rate limiting: {}",
                e
            )

        response = await call_next(request)
        return response


async def log_requests(request: Request, call_next):
    """
    Log every request with method, path,
    status code, and duration.
    """
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