import os
import json

import pytest
import requests_mock
import pandas as pd

from tsg_insights.data.process import *

@pytest.fixture
def m():
    urls = [
        ("sample_external_apis/ftc/GB-CHC-225922.json",
         'https://findthatcharity.uk/orgid/GB-CHC-225922.json'),
        ('sample_external_apis/ftc/GB-SC-SC003558.json',
         'https://findthatcharity.uk/orgid/GB-SC-SC003558.json'),
        ('sample_external_apis/ftc/GB-NIC-100012.json',
         'https://findthatcharity.uk/orgid/GB-NIC-100012.json'),
        ('sample_external_apis/ftc/GB-COH-04325234.json',
         'https://findthatcharity.uk/orgid/GB-COH-04325234.json'),
        ('sample_external_apis/ch/04325234.json',
         'http://data.companieshouse.gov.uk/doc/company/04325234.json'),
        ('sample_external_apis/ch/09668396.json',
         'http://data.companieshouse.gov.uk/doc/company/09668396.json'),
        ('sample_external_apis/pc/SE1 1AA.json',
         'https://postcodes.findthatcharity.uk/postcodes/SE1%201AA.json'),
        ('sample_external_apis/pc/L4 0TH.json',
         'https://postcodes.findthatcharity.uk/postcodes/L4%200TH.json'),
        ('sample_external_apis/geonames.csv',
         'https://postcodes.findthatcharity.uk/areas/names.csv?types=ctry,cty,laua,pcon,rgn,imd,ru11ind,oac11,lat,long'),
    ]
    m = requests_mock.Mocker()
    thisdir = os.path.dirname(os.path.realpath(__file__))
    for i in urls:
        with open(os.path.join(thisdir, i[0]), 'rb') as f_:
            m.get(i[1], content=f_.read())

    missing_urls = [
        "https://postcodes.findthatcharity.uk/postcodes/M1A%201AM.json"
    ]
    for i in missing_urls:
        m.get(i, text="Not found", status_code=404)

    m.start()
    return m

class DummyCache(dict):

    def __init__(self, *args):
        dict.__init__(self, args)

    def exists(self, key):
        return key in self

    def hexists(self, key, field):
        return field in self.get(key, {})

    def hset(self, key, field, value):
        if not key in self:
            self[key] = {}
        self[key][field] = value.encode() if isinstance(value, str) else value

    def hget(self, key, field):
        return self.get(key, {}).get(field)

    def hscan_iter(self, key):
        for v in self.get(key, {}).items():
            yield v

    def hkeys(self, key):
        return list(self.get(key, {}).keys())


def test_check_column_names():
    df = pd.DataFrame([{
        "AmountAwarded": 0,
        "AwardDate": 10,
        "FuNdIng Org:0:NaMe": 20,
        'Recipient Org:0:Identifier': 30,
        'recipientorg:0:name': 40
    }])
    cache = DummyCache()
    stage = CheckColumnNames(df, cache, None)
    result_df = stage.run()
    assert result_df.columns.all(["Amount Awarded", "Award Date",
                                "Funding Org:0:Name", 'Recipient Org:0:Identifier',
                                'Recipient Org:0:Name'])

def test_check_columns_exist():
    mandatory_columns = ['Amount Awarded', 'Funding Org:0:Name', 'Award Date',
                         'Recipient Org:0:Name', 'Recipient Org:0:Identifier']
    df = pd.DataFrame([{
        v: k for k, v in enumerate(mandatory_columns)
    }])
    cache = DummyCache()
    stage = CheckColumnsExist(df, cache, None)
    result_df = stage.run()

    for m in mandatory_columns:
        df = pd.DataFrame([{
            v: k for k, v in enumerate(mandatory_columns) if v != m
        }])
        stage = CheckColumnsExist(df, cache, None)
        with pytest.raises(ValueError):
            result_df = stage.run()

def test_check_column_types():
    df = pd.DataFrame([{
        "Award Date": "2019-01-01",
        "Amount Awarded": "1234",
        "Funding Org:0:Name": "abcd ",
        "Funding Org:0:Identifier": "abcd ",
        "Recipient Org:0:Name": "abcd ",
        "Recipient Org:0:Identifier": "abcd ",
    }])
    cache = DummyCache()
    stage = CheckColumnTypes(df, cache, None)
    result_df = stage.run()
    assert result_df.dtypes["Award Date"] == "datetime64[ns]"
    assert result_df.dtypes["Amount Awarded"] == "float64"
    assert result_df["Funding Org:0:Name"][0] == "abcd"
    assert result_df["Funding Org:0:Identifier"][0] == "abcd"
    assert result_df["Recipient Org:0:Name"][0] == "abcd"
    assert result_df["Recipient Org:0:Identifier"][0] == "abcd"

    df = pd.DataFrame([{
        "Award Date": "Text here",
    }])
    stage = CheckColumnTypes(df, cache, None)
    with pytest.raises(ValueError):
        result_df = stage.run()


def test_add_extra_columns():
    df = pd.DataFrame({
        "Award Date": pd.to_datetime("2019-01-01"),
        "Recipient Org:0:Identifier": ["GB-CHC-1234567", "360G-1234567", "", "GB-RC000123", "US-ABC"]
    })
    cache = DummyCache()
    stage = AddExtraColumns(df, cache, None)
    result_df = stage.run()
    assert "Award Date:Year" in result_df.columns
    assert "Recipient Org:0:Identifier:Scheme" in result_df.columns
    
    schemes = result_df["Recipient Org:0:Identifier:Scheme"].tolist()
    assert schemes == ["GB-CHC", "360G", "", "GB-RC000123", "US-ABC"]


def test_clean_recipient_identifiers():
    original_schemes = ["GB-CHC", "GB-COH",
                        "360G", "360G", "360G", "360G", "", "GB-RC000123", "US-ABC"]
    df = pd.DataFrame({
        "Recipient Org:0:Identifier": ["GB-CHC-1234567", "GB-COH-12345", "360G-1234567", "abcdefgined", "scottish-charity", "ni-charity", "", "GB-RC000123", "US-ABC"],
        "Recipient Org:0:Identifier:Scheme": original_schemes,
        "Recipient Org:0:Company Number": [None, None, "987654", None, None, None, None, None, None],
        "Recipient Org:0:Charity Number": [None, None, None, "123456", "SC12345", "NI12345", None, None, None],
    })
    cache = DummyCache()
    stage = CleanRecipientIdentifiers(df, cache, None)
    result_df = stage.run()
    
    clean = result_df["Recipient Org:0:Identifier:Clean"].dropna().tolist()
    assert clean == ["GB-CHC-1234567", "GB-COH-12345",
                     "GB-COH-987654", "GB-CHC-123456",
                     "GB-SC-SC12345", "GB-NIC-NI12345"]

    schemes = result_df["Recipient Org:0:Identifier:Scheme"].tolist()
    assert schemes == ["GB-CHC", "GB-COH",
                       "GB-COH", "GB-CHC", "GB-SC", "GB-NIC", "", "GB-RC000123", "US-ABC"]


def test_charity_lookup(m):
    df = pd.DataFrame({
        "Award Date": pd.to_datetime("2019-01-01"),
        "Recipient Org:0:Identifier": ["GB-CHC-225922", "GB-CHC-225922", "GB-COH-04325234", "GB-NIC-100012", "GB-SC-SC003558", "US-ABC-123456"],
        "Recipient Org:0:Identifier:Clean": ["GB-CHC-225922", "GB-CHC-225922", "GB-COH-04325234", "GB-NIC-100012", "GB-SC-SC003558", None],
        "Recipient Org:0:Identifier:Scheme": ["GB-CHC", "GB-CHC", "GB-COH", "GB-NIC", "GB-SC", "US-ABC"],
    })
    cache = DummyCache()
    cache["charity"] = {}
    stage = LookupCharityDetails(df, cache, None)
    result_df = stage.run()
    assert len(cache["charity"]) == 4
    assert json.loads(cache["charity"]["GB-CHC-225922"])["ccew_number"] == "225922"
    assert json.loads(cache["charity"]["GB-COH-04325234"])["ccew_number"] == "1089464"
    assert json.loads(cache["charity"]["GB-NIC-100012"])["ccni_number"] == "100012"
    assert json.loads(cache["charity"]["GB-SC-SC003558"])["oscr_number"] == "SC003558"

def test_company_lookup(m):
    df = pd.DataFrame({
        "Award Date": pd.to_datetime("2019-01-01"),
        "Recipient Org:0:Identifier": ["GB-CHC-225922", "GB-COH-04325234", "GB-COH-00198344", "US-ABC-123456"],
        "Recipient Org:0:Identifier:Clean": ["GB-CHC-225922", "GB-COH-04325234", "GB-COH-00198344", None],
        "Recipient Org:0:Identifier:Scheme": ["GB-CHC", "GB-COH", "GB-COH", "US-ABC"],
    })
    cache = DummyCache()
    cache["company"] = {}
    cache["charity"] = {
            "GB-COH-00198344": {
                "test_data": "test_value"
            }
        }
    stage = LookupCompanyDetails(df, cache, None)
    result_df = stage.run()
    assert len(cache["company"]) == 1
    assert json.loads(cache["company"]["GB-COH-04325234"])["primaryTopic"]["CompanyName"] == "CANCER RESEARCH UK"
    assert "GB-COH-00198344" not in cache["company"]

def test_org_merge():
    cache = DummyCache()
    cache["charity"] = {}
    cache["company"] = {}

    # load sample data into cache
    thisdir = os.path.dirname(os.path.realpath(__file__))
    for f in os.scandir(os.path.join(thisdir, "sample_external_apis", "ftc")):
        with open(f, 'rb') as data:
            orgid = f.name.replace(".json", "")
            cache["charity"][orgid.encode()] = data.read()

    for f in os.scandir(os.path.join(thisdir, "sample_external_apis", "ch")):
        with open(f, 'rb') as data:
            orgid = "GB-COH-{}".format(f.name.replace(".json", ""))
            cache["company"][orgid.encode()] = data.read()

    df = pd.DataFrame({
        "Recipient Org:0:Identifier:Clean": ["GB-CHC-225922", "GB-CHC-225922", "GB-COH-09668396",
                                             "GB-COH-00198344", "GB-NIC-100012", "GB-SC-SC003558",
                                             "GB-CHC-DOESNOTEXIST"],
    })
    stage = MergeCompanyAndCharityDetails(df, cache, None)

    orgid_df = stage._create_orgid_df()
    assert len(orgid_df) == 4
    assert orgid_df.loc["GB-COH-04325234", "company_number"] == "04325234"
    assert orgid_df.loc["GB-NIC-100012", "org_type"] == "Registered Charity (NI)"
    assert orgid_df.loc["GB-SC-SC003558", "org_type"] == "Registered Charity (Scotland)"
    assert orgid_df.loc["GB-CHC-225922", "org_type"] == "Registered Charity (E&W)"

    company_df = stage._create_company_df()
    assert len(company_df) == 2
    assert company_df.loc["GB-COH-09668396", "company_number"] == "09668396"

    result_df = stage.run()
    assert len(result_df) == 7 # no rows should have been deleted
    assert len(result_df["__org_org_type"].dropna()) == 5 # these rows have been matched with the cache


def test_postcode_lookup(m):
    df = pd.DataFrame({
        "Recipient Org:0:Postal Code": ["SE1 1AA", "L4 0TH", "M1A 1AM", None, None],
        "__org_postcode": [None, None, None, "L4 0TH", None],
    })
    cache = DummyCache()
    cache["postcode"] = {}
    stage = FetchPostcodes(df, cache, None)
    result_df = stage.run()
    assert len(cache["postcode"]) == 2
    assert json.loads(cache["postcode"]["L4 0TH"])["data"]["attributes"]["laua_name"] == "Liverpool"


def test_geo_merge():
    cache = DummyCache()
    cache["postcode"] = {}

    # load sample data into cache
    thisdir = os.path.dirname(os.path.realpath(__file__))
    for f in os.scandir(os.path.join(thisdir, "sample_external_apis", "pc")):
        with open(f, 'rb') as data:
            pc = f.name.replace(".json", "")
            cache["postcode"][pc.encode()] = data.read()

    # get sample geodata
    cache = prepare_lookup_cache(cache)

    df = pd.DataFrame({
        "Recipient Org:0:Postal Code": ["SE1 1AA", "L4 0TH", "M1A 1AM", "L4 0TH", None],
    })
    stage = MergeGeoData(df, cache, None)

    pc_df = stage._create_postcode_df()
    assert len(pc_df) == 2
    assert pc_df.loc["L4 0TH", "laua"] == "Liverpool"

    result_df = stage.run()
    assert len(result_df) == 5  # no rows should have been deleted
    # these rows have been matched with the cache
    assert len(result_df["__geo_ctry"].dropna()) == 3
    assert result_df.iloc[1]["__geo_laua"] == "Liverpool"


def test_add_extra_fields():
    df = pd.DataFrame({
        "Amount Awarded": [0, 500, 250000, 12000000],
        "__org_latest_income": [0, 500, 500009, 120000000],
        "__org_age": pd.to_timedelta([0*365, 10*365, 6*365, 150*365], unit='D'),
    })
    cache = DummyCache()
    stage = AddExtraFieldsExternal(df, cache, None)
    result_df = stage.run()
    assert "Amount Awarded:Bands" in result_df.columns
    assert "__org_latest_income_bands" in result_df.columns
    assert "__org_age_bands" in result_df.columns
    assert "Grant Programme:0:Title" in result_df.columns
    
    assert result_df.loc[0, "Amount Awarded:Bands"] == "Under £500"
    assert result_df.loc[1, "Amount Awarded:Bands"] == "Under £500"
    assert result_df.loc[2, "Amount Awarded:Bands"] == "£100k - £1m"
    assert result_df.loc[3, "Amount Awarded:Bands"] == "Over £1m"

    assert result_df.loc[0, "__org_latest_income_bands"] == "Under £10k"
    assert result_df.loc[1, "__org_latest_income_bands"] == "Under £10k"
    assert result_df.loc[2, "__org_latest_income_bands"] == "£100k - £1m"
    assert result_df.loc[3, "__org_latest_income_bands"] == "Over £10m"

    assert result_df.loc[0, "__org_age_bands"] == "Under 1 year"
    assert result_df.loc[1, "__org_age_bands"] == "5-10 years"
    assert result_df.loc[2, "__org_age_bands"] == "5-10 years"
    assert result_df.loc[3, "__org_age_bands"] == "Over 25 years"

    assert len(result_df["Grant Programme:0:Title"].unique()) == 1
