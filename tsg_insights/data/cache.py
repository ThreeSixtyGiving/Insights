import os
import pickle
import logging
import json

from flask import current_app
from redis import StrictRedis, from_url
from .utils import CustomJSONEncoder

REDIS_DEFAULT_URL = 'redis://localhost:6379/0'
REDIS_ENV_VAR = 'REDIS_URL'


def get_cache(strict=False):
    redis_url = current_app.config.get("REDIS_URL")
    if strict:
        return StrictRedis.from_url(redis_url)
    return from_url(redis_url)

def get_filename(fileid):
    uploads_folder = current_app.config.get("UPLOADS_FOLDER")
    return os.path.join(uploads_folder, "{}.pkl".format(fileid))


def save_to_cache(fileid, df, metadata=None):
    r = get_cache()
    prefix = current_app.config.get("CACHE_DEFAULT_PREFIX", "file_")

    if current_app.config.get("FILE_CACHE")=="redis":
        r.set("{}{}".format(prefix, fileid), pickle.dumps(df))
        logging.info("Dataframe [{}] saved to redis".format(fileid))
    else:
        with open(get_filename(fileid), "wb") as pkl_file:
            pickle.dump(df, pkl_file)
        logging.info("Dataframe [{}] saved to filesystem".format(fileid))

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


def delete_from_cache(fileid):
    r = get_cache()
    prefix = current_app.config.get("CACHE_DEFAULT_PREFIX", "file_")

    if current_app.config.get("FILE_CACHE") == "redis":
        r.delete("{}{}".format(prefix, fileid))
        logging.info("Dataframe [{}] removed from redis".format(fileid))
    else:
        filename = get_filename(fileid)
        if os.path.exists(filename):
            os.remove(filename)
        logging.info("Dataframe [{}] removed from filesystem".format(fileid))

    r.hdel("files", fileid)
    logging.info("Dataframe [{}] metadata removed from redis".format(fileid))


def get_from_cache(fileid):
    r = get_cache()
    prefix = current_app.config.get("CACHE_DEFAULT_PREFIX", "file_")

    if not r.hexists("files", fileid):
        return None

    if current_app.config.get("FILE_CACHE") == "redis":
        df = r.get("{}{}".format(prefix, fileid))
        if df:
            try:
                logging.info("Retrieved dataframe [{}] from redis".format(fileid))
                return pickle.loads(df)
            except ImportError as error:
                return None

    else:
        filename = get_filename(fileid)
        if os.path.exists(filename):
            with open(filename, "rb") as pkl_file:
                try:
                    df = pickle.load(pkl_file)
                    logging.info(
                        "Retrieved dataframe [{}] from filesystem".format(fileid))
                    return df
                except ImportError as error:
                    return None

    return None

def get_metadata_from_cache(fileid):
    r = get_cache()

    if not r.hexists("files", fileid):
        return None

    return json.loads(r.hget("files", fileid).decode("utf8"))
