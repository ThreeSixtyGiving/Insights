import io
import os

from flask import request
import pytest
import requests_mock

from .test_insights import test_app, client


WORKING_FILES = [
    (r"sample-data/ExampleTrust-grants-fixed.csv", "csv"),
    (r"sample-data/ExampleTrust-grants-fixed.xlsx", "xlsx"),
    (r"sample-data/ExampleTrust-grants-fixed.json", "json"),
    (r"sample-data/ExampleTrust-grants-merged-cell.xlsx", "xlsx"),
]
BROKEN_FILES = [
    (r"sample-data/ExampleTrust-grants-broken.csv", "csv"),
    (r"sample-data/ExampleTrust-grants-broken.xlsx", "xlsx"),
]


@pytest.fixture
def get_file():
    thisdir = os.path.dirname(os.path.realpath(__file__))
    return lambda x: os.path.join(thisdir, x)


@pytest.fixture
def m():
    urls = [
        (
            r"sample-data/ExampleTrust-grants-fixed.json",
            "https://grantnav.threesixtygiving.org/grants/grants.json",
            "application/json",
        ),
        (
            r"sample-data/ExampleTrust-grants-fixed.xlsx",
            "https://grantnav.threesixtygiving.org/grants/grants.xlsx",
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        ),
        (
            r"sample-data/ExampleTrust-grants-fixed.csv",
            "https://grantnav.threesixtygiving.org/grants/grants.csv",
            "text/csv",
        ),
        (
            r"sample-data/ExampleTrust-grants-broken.csv",
            "https://grantnav.threesixtygiving.org/grants/broken-grants.csv",
            "text/csv",
        ),
        (
            r"sample-data/360-giving-package-schema.json",
            "https://raw.githubusercontent.com/ThreeSixtyGiving/standard/master/schema/360-giving-package-schema.json",
            "application/json",
        ),
        (
            r"sample-data/360-giving-schema.json",
            "https://raw.githubusercontent.com/ThreeSixtyGiving/standard/master/schema/360-giving-schema.json",
            "application/json",
        ),
        # (r'sample_external_apis/registry.json',
        #  'https://store.data.threesixtygiving.org/reports/daily_status.json'),
        # (r"sample_external_apis/ftc/GB-CHC-225922.json",
        #  re.compile('https://findthatcharity.uk/orgid/')),
        # (r"sample_external_apis/ch/04325234.json",
        #  re.compile('http://data.companieshouse.gov.uk/')),
        # (r'sample_external_apis/pc/SE1 1AA.json',
        #  re.compile('https://findthatpostcode.uk/postcodes/')),
        # (r'sample_external_apis/geonames.csv',
        #  'https://findthatpostcode.uk/areas/names.csv?types=ctry,cty,laua,pcon,rgn,imd,ru11ind,oac11,lat,long'),
    ]

    m = requests_mock.Mocker()
    thisdir = os.path.dirname(os.path.realpath(__file__))
    for i in urls:
        with open(os.path.join(thisdir, i[0]), "rb") as f_:
            m.get(i[1], content=f_.read(), headers={"Content-Type": i[2]})
            m.head(i[1], headers={"Content-Type": i[2]})

    m.start()
    return m


@pytest.mark.parametrize("filename,filetype", WORKING_FILES)
def test_upload(m, client, filename, filetype):
    thisdir = os.path.dirname(os.path.realpath(__file__))
    with open(os.path.join(thisdir, filename), "rb") as f_:
        data = {"file": (io.BytesIO(f_.read()), filename.split("/")[1])}
        rv = client.post(
            "/upload",
            data=data,
            follow_redirects=True,
            content_type="multipart/form-data",
        )
        assert rv.status_code == 200
        assert rv.json["rows_saved"] == 10
        assert rv.json["filetype"] == filetype

        data_page = client.get(rv.json["data_url"])
        assert data_page.status_code == 200
        assert rv.json["dataset"].encode("utf8") in data_page.data


@pytest.mark.parametrize("filename,filetype", BROKEN_FILES)
def test_upload_broken(m, client, filename, filetype):
    thisdir = os.path.dirname(os.path.realpath(__file__))
    with open(os.path.join(thisdir, filename), "rb") as f_:
        data = {"file": (io.BytesIO(f_.read()), filename.split("/")[1])}
        rv = client.post(
            "/upload",
            data=data,
            follow_redirects=True,
            content_type="multipart/form-data",
        )
        assert rv.status_code == 400
        assert "error" in rv.json
        assert rv.json.get("rows_saved", 0) == 0
        assert rv.json["filetype"] == filetype


@pytest.mark.parametrize("url", [
    "https://grantnav.threesixtygiving.org/grants/grants.json",
    "https://grantnav.threesixtygiving.org/grants/grants.csv",
])
def test_fetch_from_url(m, client, url):
    rv = client.get("/?url=" + url, follow_redirects=True)
    assert rv.status_code == 200
    assert "/data/" in request.path
    assert b'Uploaded dataset' in rv.data
    assert b'Could not fetch from URL' not in rv.data


@pytest.mark.parametrize("url", [
    "https://raw.githubusercontent.com/ThreeSixtyGiving/standard/master/schema/360-giving-package-schema.json",
    "https://grantnav.threesixtygiving.org/grants/broken-grants.csv",
])
def test_fetch_from_url_broken(m, client, url):
    rv = client.get("/?url=" + url, follow_redirects=True)
    assert rv.status_code == 200
    assert request.path == "/"
    assert b'Could not fetch from URL' in rv.data
