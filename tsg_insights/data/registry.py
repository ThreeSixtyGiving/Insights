import json

import pandas as pd
import requests
import requests_cache

from .cache import get_cache
from .utils import format_currency, get_fileid

THREESIXTY_STATUS_JSON = (
    "https://store.data.threesixtygiving.org/reports/daily_status.json"
)
DEFAULT_CACHE = 60 * 60 * 24
REG_KEY = "threesixty_status"


def get_registry(
    reg_url=THREESIXTY_STATUS_JSON, cache_expire=DEFAULT_CACHE, skip_cache=False
):
    # fetch the 360Giving registry
    r = get_cache()
    if not skip_cache:
        reg = r.get(REG_KEY)
        if reg:
            return json.loads(reg.decode("utf8"))

    with requests_cache.disabled():
        reg = requests.get(reg_url).json()
    r.set(REG_KEY, json.dumps(reg), ex=cache_expire)
    return reg


def process_registry(
    reg=None, reg_url=THREESIXTY_STATUS_JSON, cache_expire=DEFAULT_CACHE
):
    if not reg:
        reg = get_registry(reg_url, cache_expire)
    publishers = {}
    for v in reg:
        publisher = publisher_sort = v.get("publisher", {}).get("name", "")
        if publisher.lower().startswith("the "):
            publisher_sort = publisher[4:]

        grant_count = v.get("datagetter_aggregates", {}).get("count", 0)
        grant_amount = (
            v.get("datagetter_aggregates", {})
            .get("currencies", {})
            .get("GBP", {})
            .get("total_amount", None)
        )
        if grant_amount:
            grant_amount = format_currency(grant_amount, abbreviate=True)
            grant_amount = "{}{}".format(*grant_amount)

        min_award_date = pd.to_datetime(
            str(v.get("datagetter_aggregates", {}).get("min_award_date", None)),
            errors="coerce",
            format="%Y-%m-%d",
            exact=True,
        )
        max_award_date = pd.to_datetime(
            str(v.get("datagetter_aggregates", {}).get("max_award_date", None)),
            errors="coerce",
            format="%Y-%m-%d",
            exact=True,
        )

        award_date_str = ""
        if not pd.isnull(min_award_date) and not pd.isnull(max_award_date):
            if min_award_date.strftime("%b '%y") == max_award_date.strftime("%b '%y"):
                award_date_str = min_award_date.strftime("%b '%y")
            else:
                award_date_str = "{:%b '%y} - {:%b '%y}".format(
                    min_award_date, max_award_date
                )
        elif not pd.isnull(max_award_date):
            award_date_str = "- {:%b '%y}".format(max_award_date)
        elif not pd.isnull(min_award_date):
            award_date_str = "{:%b '%y} -".format(min_award_date)

        if publisher_sort not in publishers:
            publishers[publisher_sort] = []
        publishers[publisher_sort].append(
            {
                "publisher": publisher,
                "identifier": v.get("identifier"),
                "title": v.get("title", ""),
                "grant_count": grant_count,
                "grant_amount": grant_amount,
                "award_date": award_date_str,
                "max_award_date": max_award_date,
                "downloads": v.get("datagetter_metadata", {}).get("downloads", False),
                "file_size": v.get("datagetter_metadata", {}).get("file_size"),
                "file_type": v.get("datagetter_metadata", {}).get("file_type"),
                "download_url": v.get("distribution", [{}])[0].get("downloadURL"),
            }
        )
        publishers[publisher_sort] = sorted(
            publishers[publisher_sort], key=lambda x: x["max_award_date"], reverse=True
        )

    return publishers


def get_reg_file(identifier):
    registry = get_registry()
    file_ = [f for f in registry if f["identifier"] == identifier]
    if len(file_) != 1:
        return (None, None)

    return (
        file_[0].get("distribution", [{}])[0].get("downloadURL"),
        file_[0].get("datagetter_metadata", {}).get("file_type"),
    )


def get_reg_file_from_url(url):
    registry = get_registry()
    for f in registry:
        if f.get("distribution", [{}])[0].get("downloadURL") == url:
            return f
    return None


def fetch_reg_file(url, method="GET"):
    user_agents = {
        "insights": "insights.threesixtygiving.org",
        "spoof": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:63.0) Gecko/20100101 Firefox/63.0",
    }
    if method not in ["GET", "HEAD"]:
        raise ValueError("Request method [{}] not recognised".format(method))
    for u in user_agents.values():
        reg_file = requests.request(method, url, headers={"User-Agent": u})
        try:
            reg_file.raise_for_status()
            if method == "HEAD":
                return reg_file.headers
            return reg_file.content
        except:
            continue


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
                "6month": datetime.datetime.now() - datetime.timedelta(days=30 * 6),
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
            if (
                r.get("datagetter_metadata", {}).get("file_type")
                not in filters["filetype"]
            ):
                continue

        if p not in reg_:
            reg_[p] = []

        reg_[p].append(r)

    return reg_
