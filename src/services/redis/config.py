import redis.asyncio as redis

from src.config import settings


async def get_redis_client():
    redis_client = redis.Redis(host=settings.REDIS_SERVER, port=6379, db=0)
    return redis_client
