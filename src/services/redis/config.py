import redis.asyncio as redis

async def get_redis_client():
    redis_client = redis.Redis(host='localhost', port=6379, db=0)
    return redis_client