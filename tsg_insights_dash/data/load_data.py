import pickle
import logging
import os
import json
import datetime
import dateutil

from flask import g, Flask
from tsg_insights.data.cache import redis_cache, get_cache, save_to_cache, get_from_cache

import pandas as pd
import requests

from .filters import FILTERS

THREESIXTY_STATUS_JSON = 'https://storage.googleapis.com/datagetter-360giving-output/branch/master/status.json'
DEFAULT_PREFIX    = 'file_'


# fetch the 360Giving registry
def get_registry(reg_url=THREESIXTY_STATUS_JSON, cache_expire=60*60*24):
    # @TODO: duplicate with flask app
    reg_key = "threesixty_status"
    r = get_cache()
    reg = r.get(reg_key)
    if reg: 
        return json.loads(reg.decode('utf8'))

    reg = requests.get(reg_url).json()
    r.set(reg_key, json.dumps(reg), ex=cache_expire)
    return reg


def get_registry_by_publisher(filters={}, **kwargs):
    reg = get_registry(**kwargs)

    reg_ = {}
    for r in reg:
        
        p = r.get("publisher", {}).get("name")

        # filter
        if filters.get("licence"):
            if r.get("license", "") not in filters["licence"]:
                continue

        if filters.get("search"):
            if filters.get("search", "").lower() not in p.lower():
                continue

        if filters.get("last_modified"):
            last_modified_poss = {
                "lastmonth": datetime.datetime.now() - datetime.timedelta(days=30),
                "6month": datetime.datetime.now() - datetime.timedelta(days=30*6),
                "12month": datetime.datetime.now() - datetime.timedelta(days=365),
            }
            if last_modified_poss.get(filters.get("last_modified")):
                last_modified = dateutil.parser.parse(r.get("modified"), ignoretz=True)
                if last_modified < last_modified_poss.get(filters.get("last_modified")):
                    continue

        if filters.get("currency"):
            choose_this = False
            for c in filters.get("currency", []):
                if c in r.get("datagetter_aggregates", {}).get("currencies", {}).keys():
                    choose_this = True
            if not choose_this:
                continue

        if filters.get("filetype"):
            if r.get('datagetter_metadata', {}).get("file_type") not in filters["filetype"]:
                continue


        if p not in reg_:
            reg_[p] = []

        reg_[p].append(r)

    return reg_



def fetch_reg_file(url):
    # @TODO: duplicate with flask app
    user_agents = {
        "findthatcharity": 'FindThatCharity.uk',
        'spoof': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:63.0) Gecko/20100101 Firefox/63.0',
    }
    reg_file = requests.get(
        url, headers={'User-Agent': user_agents['findthatcharity']})
    try:
        reg_file.raise_for_status()
    except:
        reg_file = requests.get(
            url, headers={'User-Agent': user_agents['spoof']})
        reg_file.raise_for_status()
    return reg_file.content


def get_filtered_df(fileid, **filters):
    df = get_from_cache(fileid)

    for filter_id, filter_def in FILTERS.items():
        new_df = filter_def["apply_filter"](
            df,
            filters.get(filter_id),
            filter_def
        )
        if new_df is not None:
            df = new_df

    return df
