import os
import random
import string
import re
import tempfile

import pytest
import requests_mock

from tsg_insights import create_app
from tsg_insights.data.process import *
from tsg_insights.data.cache import get_from_cache, get_metadata_from_cache, delete_from_cache


@pytest.fixture
def get_file():
    thisdir = os.path.dirname(os.path.realpath(__file__))
    return lambda x: os.path.join(thisdir, x)


@pytest.fixture
def m():
    urls = [
        ('sample-data/ExampleTrust-grants-fixed.json',
         'https://findthatcharity.uk/grants/grants.json'),
        ('sample-data/ExampleTrust-grants-fixed.xlsx',
         'https://findthatcharity.uk/grants/grants.xlsx'),
        ('sample-data/ExampleTrust-grants-fixed.csv',
         'https://findthatcharity.uk/grants/grants.csv'),
        ('sample-data/360-giving-package-schema.json',
         'https://raw.githubusercontent.com/ThreeSixtyGiving/standard/master/schema/360-giving-package-schema.json'),
        ('sample-data/360-giving-schema.json',
         'https://raw.githubusercontent.com/ThreeSixtyGiving/standard/master/schema/360-giving-schema.json'),
        ("sample_external_apis/ftc/GB-CHC-225922.json",
         re.compile('https://findthatcharity.uk/orgid/')),
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


def test_file_upload(get_file, m, test_app):
    with test_app.app_context():
        files = [
            'sample-data/ExampleTrust-grants-fixed.json',
            'sample-data/ExampleTrust-grants-fixed.xlsx',
            'sample-data/ExampleTrust-grants-fixed.csv',
        ]
        for filename in files:
            salt = ''.join(random.choices(
                string.ascii_uppercase + string.digits, k=6))
            with open(get_file(filename), 'rb') as a:
                fileid, return_filename = get_dataframe_from_file(filename, a.read(), date=salt)
                assert isinstance(fileid, str)
                assert return_filename == filename

            df = get_from_cache(fileid)
            assert isinstance(df, pd.DataFrame)
            assert len(df) > 0

            metadata = get_metadata_from_cache(fileid)
            assert len(metadata.keys()) == 5
            assert isinstance(metadata["expires"], str)

            delete_from_cache(fileid)


def test_file_fetch_from_url(get_file, m, test_app):
    with test_app.app_context():
        test_urls = [
            'https://findthatcharity.uk/grants/grants.json',
            'https://findthatcharity.uk/grants/grants.xlsx',
            'https://findthatcharity.uk/grants/grants.csv',
        ]

        for url in test_urls:
            fileid, return_filename, headers = get_dataframe_from_url(url)
            assert isinstance(fileid, str)
            assert return_filename == url

            df = get_from_cache(fileid)
            assert isinstance(df, pd.DataFrame)
            assert len(df) > 0

            metadata = get_metadata_from_cache(fileid)
            assert len(metadata.keys())==6
            assert metadata["url"] == url

            delete_from_cache(fileid)
