import json

import requests
import pandas as pd

from .cache import get_cache, save_to_cache, get_from_cache
from .process import get_dataframe
from .utils import format_currency, get_fileid

THREESIXTY_STATUS_JSON = 'https://storage.googleapis.com/datagetter-360giving-output/branch/master/status.json'
DEFAULT_CACHE = 60*60*24

# fetch the 360Giving registry


def get_registry(reg_url=THREESIXTY_STATUS_JSON, cache_expire=DEFAULT_CACHE):
    reg_key = "threesixty_status"
    r = get_cache()
    reg = r.get(reg_key)
    if reg:
        return json.loads(reg.decode('utf8'))

    reg = requests.get(reg_url).json()
    r.set(reg_key, json.dumps(reg), ex=cache_expire)
    return reg


def process_registry(reg=None, reg_url=THREESIXTY_STATUS_JSON, cache_expire=DEFAULT_CACHE):
    if not reg:
        reg = get_registry(reg_url, cache_expire)
    publishers = {}
    for v in reg:
        publisher = v.get("publisher", {}).get("name", "")
        grant_count = v.get("datagetter_aggregates", {}).get("count", 0)
        grant_amount = v.get("datagetter_aggregates", {}).get(
            "currencies", {}).get("GBP", {}).get("total_amount", None)
        if grant_amount:
            grant_amount = format_currency(grant_amount, abbreviate=True)
            grant_amount = "{}{}".format(*grant_amount)

        min_award_date = pd.to_datetime(v.get("datagetter_aggregates", {}).get("min_award_date", None))
        max_award_date = pd.to_datetime(v.get("datagetter_aggregates", {}).get("max_award_date", None))

        min_award_date = min_award_date.strftime("%b '%y") if not pd.isna(min_award_date) else None
        max_award_date = max_award_date.strftime("%b '%y") if not pd.isna(max_award_date) else None

        if min_award_date == max_award_date:
            award_date_str = min_award_date
        else:
            award_date_str = "{} - {}".format(min_award_date, max_award_date)

        if publisher not in publishers:
            publishers[publisher] = []
        publishers[publisher].append({
            'identifier': v.get('identifier'),
            'title': v.get("title", ""),
            'grant_count': grant_count,
            'award_date': award_date_str,
            'grant_amount': grant_amount,
            # @TODO: add file type
        })

    return publishers


def get_reg_file(identifier):
    registry = get_registry()
    file_ = [f for f in registry if f['identifier'] == identifier]
    if len(file_) != 1:
        return (None, None)

    return (
        file_[0].get("distribution", [{}])[0].get("downloadURL"),
        file_[0].get("datagetter_metadata", {}).get("file_type")
    )


def fetch_reg_file(url):
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


def fetch_and_parse(filename, content=None):
    # 1. fetch file
    if not content and filename:
        content = fetch_reg_file(filename)

    fileid = get_fileid(content, filename)

    # 1a. Check cache for file
    df = get_from_cache(fileid)
    if df is not None:
        return (fileid, filename)

    # 2. prepare data
    df = get_dataframe(filename, content)

    # 3. save to cache
    save_to_cache(fileid, df)

    # 4. return the fileid and filename
    return (fileid, filename)
