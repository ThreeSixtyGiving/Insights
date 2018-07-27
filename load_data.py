import pickle
import logging
import os
import json

from flask import g
from redis import StrictRedis

import pandas as pd
import requests

THREESIXTY_STATUS_JSON = 'https://storage.googleapis.com/datagetter-360giving-output/branch/master/status.json'
REDIS_DEFAULT_URL = 'redis://localhost:6379/0'
DEFAULT_PREFIX    = 'file_'

def get_cache():
    if 'cache' not in g:
        redis_url = os.environ.get('REDIS_URL', REDIS_DEFAULT_URL)
        g.cache = StrictRedis.from_url(redis_url)

    return g.cache


def save_to_cache(fileid, df, prefix=DEFAULT_PREFIX):
    r = get_cache()
    r.set("{}{}".format(prefix, fileid), pickle.dumps(df))
    logging.info("Dataframe [{}] saved to redis".format(fileid))

    metadata = {
        "fileid": fileid,
        "funders": df["Funding Org:Name"].unique().tolist(),
        "max_date": df["Award Date"].max().isoformat(),
        "min_date": df["Award Date"].min().isoformat(),
    }
    r.hset("files", fileid, json.dumps(metadata))
    logging.info("Dataframe [{}] metadata saved to redis".format(fileid))


def get_from_cache(fileid, prefix=DEFAULT_PREFIX):
    r = get_cache()
    
    if not r.hexists("files", fileid):
        return None

    df = r.get("{}{}".format(prefix, fileid))
    if df:
        logging.info("Retrieved dataframe [{}] from redis".format(fileid))
        return pickle.loads(df)


# fetch the 360 giving registry
def get_registry(reg_url=THREESIXTY_STATUS_JSON, cache_expire=60*60*24):
    reg_key = "threesixty_status"
    r = get_cache()
    reg = r.get(reg_key)
    if reg: 
        return json.loads(reg.decode('utf8'))

    reg = requests.get(reg_url).json()
    r.set(reg_key, json.dumps(reg), ex=cache_expire)
    return reg


def get_registry_by_publisher(**kwargs):
    reg = get_registry(**kwargs)

    reg_ = {}
    for r in reg:
        p = r.get("publisher", {}).get("name")
        if p not in reg_:
            reg_[p] = []

        reg_[p].append(r)

    return reg_



def fetch_reg_file(url):
    reg_file = requests.get(url)
    return reg_file.content


def get_filtered_df(fileid, **filters):
    df = get_from_cache(fileid)
    
    # Filter on grant programme
    if filters.get("grant_programme") and '__all' not in filters.get("grant_programme", []):
        df = df[df["Grant Programme:Title"].isin(filters.get("grant_programme", []))]
    
    # Filter on funder
    if filters.get("funder") and '__all' not in filters.get("funder", []):
        df = df[df["Funding Org:Name"].isin(filters.get("funder", []))]

    # filter on year
    if filters.get("year") and df is not None:
        df = df[
            (df["Award Date"].dt.year >= filters.get("year")[0]) & 
            (df["Award Date"].dt.year <= filters.get("year")[1])
        ]

    return df