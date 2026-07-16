import redis.asyncio as aioredis

from app.core.config import settings

_redis: aioredis.Redis | None = None
_redis_disabled = False


async def get_redis() -> aioredis.Redis | None:
    global _redis, _redis_disabled
    if not settings.REDIS_ENABLED:
        _redis_disabled = True
        return None
    if _redis is None and not _redis_disabled:
        try:
            _redis = aioredis.Redis(
                host=settings.REDIS_HOST,
                port=settings.REDIS_PORT,
                password=settings.REDIS_PASSWORD or None,
                db=settings.REDIS_DB,
                ssl=settings.REDIS_SSL,
                ssl_cert_reqs=None if settings.REDIS_SSL else "required",
                max_connections=settings.REDIS_POOL_MAX_CONNECTIONS,
                decode_responses=True,
            )
        except Exception:
            _redis_disabled = True
            return None
    return _redis


async def close_redis() -> None:
    global _redis
    if _redis is not None:
        await _redis.close()
        _redis = None
