import os
import random
import string
import re
import tempfile

import pytest
import requests_mock

from tsg_insights import create_app
from tsg_insights.data.registry import *
from tsg_insights.data.cache import get_from_cache, get_metadata_from_cache, delete_from_cache


@pytest.fixture
def get_file():
    thisdir = os.path.dirname(os.path.realpath(__file__))
    return lambda x: os.path.join(thisdir, x)


@pytest.fixture
def m():
    urls = [
        ('sample_external_apis/registry.json',
         'https://storage.googleapis.com/datagetter-360giving-output/branch/master/status.json'),
        ('sample_external_apis/registry-broken.json',
         'https://storage.googleapis.com/datagetter-360giving-output/branch/master/status_broken.json'),
    ]

    m = requests_mock.Mocker()
    thisdir = os.path.dirname(os.path.realpath(__file__))
    for i in urls:
        with open(os.path.join(thisdir, i[0]), 'rb') as f_:
            m.get(i[1], content=f_.read())
            m.head(i[1])

    m.start()
    return m

@pytest.fixture
def test_app():
    return create_app({
        "UPLOAD_FOLDER": tempfile.mkdtemp(),
        "REQUESTS_CACHE_ON": False,
        "CACHE_DEFAULT_PREFIX": "test_file_"
    })


def test_get_registry(get_file, m, test_app):
    with test_app.app_context():
        reg = get_registry(skip_cache=True)
        assert len(reg) == 147
        assert reg[0]["datagetter_aggregates"]["count"] == 381

def test_process_registry(get_file, m, test_app):
    with test_app.app_context():
        reg = get_registry(skip_cache=True)
        assert len(reg) == 147
        assert reg[0]["datagetter_aggregates"]["count"] == 381

        publishers = process_registry(reg)
        assert len(publishers) == 99
        assert len(publishers['Heart of England Community Foundation']) == 4

        assert publishers['A B Charitable Trust'][0]['award_date'] == "Jan '13 - Jan '18"
        assert publishers['Kingston Voluntary Action'][0]['award_date'] == "Jun '18"

        sorted_dates = [p['max_award_date']
                        for p in publishers['Community Foundation serving Tyne & Wear and Northumberland']]
        assert sorted_dates == sorted(sorted_dates, reverse=True)


def test_process_registry_broken(get_file, m, test_app):
    with test_app.app_context():
        reg = get_registry(
            reg_url='https://storage.googleapis.com/datagetter-360giving-output/branch/master/status_broken.json', skip_cache=True)
        assert len(reg) == 147
        assert reg[0]["datagetter_aggregates"]["count"] == 381

        publishers = process_registry(reg)
        assert len(publishers) == 99
        assert len(publishers['Heart of England Community Foundation'])==4

        assert publishers['A B Charitable Trust'][0]['award_date'] == "- Jan '18"


# def test_file_fetch_from_url(get_file, m, test_app):
#     with test_app.app_context():
#         test_urls = [
#             'https://findthatcharity.uk/grants/grants.json',
#             'https://findthatcharity.uk/grants/grants.xlsx',
#             'https://findthatcharity.uk/grants/grants.csv',
#         ]

#         for url in test_urls:
#             fileid, return_filename, headers = get_dataframe_from_url(url)
#             assert isinstance(fileid, str)
#             assert return_filename == url

#             df = get_from_cache(fileid)
#             assert isinstance(df, pd.DataFrame)
#             assert len(df) > 0

#             metadata = get_metadata_from_cache(fileid)
#             assert len(metadata.keys())==6
#             assert metadata["url"] == url

#             delete_from_cache(fileid)
