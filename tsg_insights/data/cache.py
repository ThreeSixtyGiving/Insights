import os
import pickle
import logging
import json

from redis import StrictRedis, from_url
from .utils import CustomJSONEncoder

REDIS_DEFAULT_URL = 'redis://localhost:6379/0'
REDIS_ENV_VAR = 'REDIS_URL'
CACHE_DEFAULT_PREFIX = 'file_'

def redis_cache(strict=False):
    redis_url = os.environ.get(REDIS_ENV_VAR, REDIS_DEFAULT_URL)
    if strict:
        return StrictRedis.from_url(redis_url)
    return from_url(redis_url)

def get_cache():
    return redis_cache()


def save_to_cache(fileid, df, prefix=CACHE_DEFAULT_PREFIX, metadata=None):
    r = get_cache()
    r.set("{}{}".format(prefix, fileid), pickle.dumps(df))
    logging.info("Dataframe [{}] saved to redis".format(fileid))

    if not metadata:
        metadata = {}

    metadata = {
        "fileid": fileid,
        "funders": df["Funding Org:0:Name"].unique().tolist(),
        "max_date": df["Award Date"].max().isoformat(),
        "min_date": df["Award Date"].min().isoformat(),
        **metadata
    }
    r.hset("files", fileid, json.dumps(metadata, default=CustomJSONEncoder().default))
    logging.info("Dataframe [{}] metadata saved to redis".format(fileid))


def delete_from_cache(fileid, prefix=CACHE_DEFAULT_PREFIX):
    r = get_cache()
    r.delete("{}{}".format(prefix, fileid))
    logging.info("Dataframe [{}] removed from redis".format(fileid))

    r.hdel("files", fileid)
    logging.info("Dataframe [{}] metadata removed from redis".format(fileid))

def get_from_cache(fileid, prefix=CACHE_DEFAULT_PREFIX):
    r = get_cache()

    if not r.hexists("files", fileid):
        return None

    df = r.get("{}{}".format(prefix, fileid))
    if df:
        try:
            logging.info("Retrieved dataframe [{}] from redis".format(fileid))
            return pickle.loads(df)
        except ImportError as error:
            return None

def get_metadata_from_cache(fileid):
    r = get_cache()

    if not r.hexists("files", fileid):
        return None

    return json.loads(r.hget("files", fileid).decode("utf8"))
