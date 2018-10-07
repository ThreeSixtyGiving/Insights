import os
from redis import StrictRedis, from_url

REDIS_DEFAULT_URL = 'redis://localhost:6379/0'
REDIS_ENV_VAR = 'REDIS_URL'


def redis_cache(strict=False):
    redis_url = os.environ.get(REDIS_ENV_VAR, REDIS_DEFAULT_URL)
    if strict:
        return StrictRedis.from_url(redis_url)
    return from_url(redis_url)
