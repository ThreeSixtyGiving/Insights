import base64
import json
import io
import os
import logging

import pandas as pd
import requests
from rq import get_current_job
import tqdm
from threesixty import ThreeSixtyGiving

from .cache import get_cache, get_from_cache, save_to_cache
from .utils import get_fileid, charity_number_to_org_id
from .registry import fetch_reg_file, get_reg_file_from_url

FTC_URL = 'https://findthatcharity.uk/orgid/{}.json'
CH_URL = 'http://data.companieshouse.gov.uk/doc/company/{}.json'
PC_URL = 'https://postcodes.findthatcharity.uk/postcodes/{}.json'

# config
# schemes with data on findthatcharity
FTC_SCHEMES = ["GB-CHC", "GB-NIC", "GB-SC", "GB-COH"]
POSTCODE_FIELDS = ['ctry', 'cty', 'laua', 'pcon', 'rgn', 'imd', 'ru11ind',
                   'oac11', 'lat', 'long']  # fields to care about from the postcodes)


def get_dataframe_from_file(filename, contents, date=None):
    fileid = get_fileid(contents, filename, date)

    # 2. Check cache for file
    df = get_from_cache(fileid)
    if df is not None:
        return (fileid, filename)

    # 3. Fetch and prepare the data
    df = None
    cache = prepare_lookup_cache()
    job = get_current_job()

    data_preparation = DataPreparation(
        df, cache, job, filename=filename, contents=contents)
    data_preparation.stages = [LoadDatasetFromFile] + data_preparation.stages
    df = data_preparation.run()

    # 5. save to cache
    save_to_cache(fileid, df)  # dataframe

    return (fileid, filename)

def get_dataframe_from_url(url):
    # 1. Work out the file id
    headers = fetch_reg_file(url, 'HEAD')
    # work out the version of the file
    # https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/Last-Modified
    last_modified = headers.get("ETag", headers.get("Last-Modified"))

    fileid = get_fileid(None, url, last_modified)

    # 2. Check cache for file
    df = get_from_cache(fileid)
    if df is not None:
        return (fileid, url, headers)

    # 3. Fetch and prepare the data
    df = None
    cache = prepare_lookup_cache()
    job = get_current_job()

    data_preparation = DataPreparation(df, cache, job, url=url)
    data_preparation.stages = [LoadDatasetFromURL] + data_preparation.stages
    df = data_preparation.run()

    # 4. Get metadata about the file
    metadata = {
        "headers": headers,
        "url": url,
    }
    registry = get_reg_file_from_url(url)
    if registry:
        metadata["registry_entry"] = registry

    # 5. save to cache
    save_to_cache(fileid, df, metadata=metadata)  # dataframe

    return (fileid, url, headers)


def prepare_lookup_cache(cache=None):
    if cache is None:
        cache = get_cache()

    if not cache.exists("geocodes"):
        for g, name in fetch_geocodes().items():
            cache.hset("geocodes", g, name)
    return cache


def fetch_geocodes():
    r = requests.get("https://postcodes.findthatcharity.uk/areas/names.csv",
                     params={"types": ",".join(POSTCODE_FIELDS)})
    pc_names = pd.read_csv(io.StringIO(r.text)).set_index(
        ["type", "code"]).sort_index()
    geocodes = pc_names["name"].to_dict()
    geocodes = {"-".join(c): d for c, d in geocodes.items()}
    return geocodes


class DataPreparation(object):
    
    def __init__(self, df, cache=None, job=None, **kwargs):
        self.stages = [
            CheckColumnNames,
            CheckColumnsExist,
            CheckColumnTypes,
            AddExtraColumns,
            CleanRecipientIdentifiers,
            LookupCharityDetails,
            LookupCompanyDetails,
            MergeCompanyAndCharityDetails,
            FetchPostcodes,
            MergeGeoData,
            AddExtraFieldsExternal,
        ]
        self.df = df
        self.cache = cache
        self.job = job
        self.attributes = kwargs

    def _progress_job(self, stage_id, progress=None):
        if not self.job:
            return
        self.job.meta['progress']["stage"] = stage_id
        self.job.meta['progress']["progress"] = progress
        self.job.save_meta()

    def _setup_job_meta(self):
        if not self.job:
            return
        self.job.meta['stages'] = [s.name for s in self.stages]
        self.job.meta['progress'] = {"stage": 0, "progress": None}
        self.job.save_meta()

    def run(self):
        df = None
        self._setup_job_meta()
        for k, Stage in enumerate(self.stages):
            stage = Stage(df, self.cache, self.job, **self.attributes)
            logging.info(stage.name)
            df = stage.run()
            self._progress_job(k)
        return df


class DataPreparationStage(object):

    def __init__(self, df, cache, job, **kwargs):
        self.df = df
        self.cache = cache
        self.job = job
        self.attributes = kwargs

    def _progress_job(self, item_key, total_items):
        if not self.job:
            return
        self.job.meta['progress']["progress"] = (item_key, total_items)
        self.job.save_meta()

    def run(self):
        # subclasses should implement a `run()` method
        # which returns an altered version of the dataframe
        return self.df


class LoadDatasetFromURL(DataPreparationStage):

    name = 'Load data to be prepared from an URL'

    def run(self):
        if not self.attributes.get("url"):
            return self.df

        url = self.attributes.get("url")
        self.df = ThreeSixtyGiving.from_url(url).to_pandas()

        return self.df

class LoadDatasetFromFile(DataPreparationStage):

    name = 'Load data to be prepared from a file'

    def run(self):
        if not self.attributes.get("contents") or not self.attributes.get("filename"):
            return self.df

        contents = self.attributes.get("contents")
        filename = self.attributes.get("filename")

        if isinstance(contents, str):
            # if it's a string we assume it's dataurl/base64 encoded
            content_type, content_string = contents.split(',')
            contents = base64.b64decode(content_string)

        if filename.endswith("csv"):
            # Assume that the user uploaded a CSV file
            self.df = ThreeSixtyGiving.from_csv(io.BytesIO(contents)).to_pandas()
        elif filename.endswith("xls") or filename.endswith("xlsx"):
            # Assume that the user uploaded an excel file
            self.df = ThreeSixtyGiving.from_excel(
                io.BytesIO(contents)).to_pandas()
        elif filename.endswith("json"):
            # Assume that the user uploaded a json file
            self.df = ThreeSixtyGiving.from_json(
                io.BytesIO(contents)).to_pandas()

        return self.df


class CheckColumnNames(DataPreparationStage):
    # check column names for typos

    name = 'Check column names'
    columns_to_check = [
        'Amount Awarded', 'Funding Org:0:Name', 'Award Date',
        'Recipient Org:0:Name', 'Recipient Org:0:Identifier'
    ]

    def run(self):
        renames = {}
        for c in self.df.columns:
            for w in self.columns_to_check:
                if c.replace(" ", "").lower() == w.replace(" ", "").lower() and c != w:
                    renames[c] = w
                # @TODO: could include a replacement of (eg) "Recipient Org:Name" with "Recipient Org:0:Name"
        self.df = self.df.rename(columns=renames)
        return self.df

class CheckColumnsExist(CheckColumnNames):

    name = 'Check columns exist'

    def run(self):
        for c in self.columns_to_check:
            if c not in self.df.columns:
                raise ValueError("Column {} not found in data. Columns: [{}]".format(
                    c, ", ".join(self.df.columns)
                ))
        return self.df

class CheckColumnTypes(DataPreparationStage):

    name = 'Check column types'
    columns_to_check = {
        "Amount Awarded": lambda x: x.astype(float),
        "Funding Org:0:Identifier": lambda x: x.str.strip(),
        "Funding Org:0:Name": lambda x: x.str.strip(),
        "Recipient Org:0:Name": lambda x: x.str.strip(),
        "Recipient Org:0:Identifier": lambda x: x.str.strip(),
        "Award Date": lambda x: pd.to_datetime(x),
    }

    def run(self):
        for c, func in self.columns_to_check.items():
            if c in self.df.columns:
                self.df.loc[:, c] = func(self.df[c])
        return self.df

class AddExtraColumns(DataPreparationStage):

    name = 'Add extra columns'

    def run(self):
        self.df.loc[:, "Award Date:Year"] = self.df["Award Date"].dt.year
        self.df.loc[:, "Recipient Org:0:Identifier:Scheme"] = self.df["Recipient Org:0:Identifier"].apply(
            lambda x: "360G" if x.startswith("360G-") else "-".join(x.split("-")[:2])
        )
        return self.df

class CleanRecipientIdentifiers(DataPreparationStage):

    name = 'Clean recipient identifiers'

    def run(self):
        # default is use existing identifier
        self.df.loc[
            self.df["Recipient Org:0:Identifier:Scheme"].isin(FTC_SCHEMES),
            "Recipient Org:0:Identifier:Clean"
        ] = self.df.loc[
            self.df["Recipient Org:0:Identifier:Scheme"].isin(FTC_SCHEMES),
            "Recipient Org:0:Identifier"
        ]

        # add company number for those with it
        if "Recipient Org:0:Company Number" in self.df.columns:
            self.df.loc[
                self.df["Recipient Org:0:Company Number"].notnull(),
                "Recipient Org:0:Identifier:Clean"
            ] = self.df.loc[:, "Recipient Org:0:Identifier:Clean"].fillna(
                self.df["Recipient Org:0:Company Number"].apply("GB-COH-{}".format)
            )

        # add charity number for those with it
        if "Recipient Org:0:Charity Number" in self.df.columns:
            self.df.loc[:, "Recipient Org:0:Identifier:Clean"] = self.df.loc[:, "Recipient Org:0:Identifier:Clean"].fillna(
                self.df["Recipient Org:0:Charity Number"].apply(charity_number_to_org_id)
            )
        
        # overwrite the identifier scheme using the new identifiers
        # @TODO: this doesn't work well at the moment - seems to lose lots of identifiers
        self.df.loc[:, "Recipient Org:0:Identifier:Scheme"] = self.df["Recipient Org:0:Identifier:Clean"].apply(
            lambda x: ("360G" if x.startswith(
                "360G-") else "-".join(x.split("-")[:2])) if isinstance(x, str) else None
        ).fillna(self.df["Recipient Org:0:Identifier:Scheme"])

        return self.df

class LookupCharityDetails(DataPreparationStage):

    name = 'Look up charity data'
    ftc_url=FTC_URL

    # utils
    def _get_charity(self, orgid):
        if self.cache.hexists("charity", orgid):
            return json.loads(self.cache.hget("charity", orgid))
        return requests.get(self.ftc_url.format(orgid)).json()

    def run(self):    
        orgids = self.df.loc[
            self.df["Recipient Org:0:Identifier:Scheme"].isin(FTC_SCHEMES),
            "Recipient Org:0:Identifier:Clean"
        ].dropna().unique()
        print("Finding details for {} charities".format(len(orgids)))
        for k, orgid in tqdm.tqdm(enumerate(orgids)):
            self._progress_job(k+1, len(orgids))
            try:
                self.cache.hset("charity", orgid, json.dumps(self._get_charity(orgid)))
            except ValueError:
                pass

        return self.df

class LookupCompanyDetails(DataPreparationStage):

    name = 'Look up company data'
    ch_url = CH_URL

    def _get_company(self, orgid):
        if self.cache.hexists("company", orgid):
            return json.loads(self.cache.hget("company", orgid))
        return requests.get(self.ch_url.format(orgid.replace("GB-COH-", ""))).json()

    def _get_orgid_index(self):
        # find records where the ID has already been found in charity lookup
        return list(self.cache.hkeys("charity"))

    def run(self):
        company_orgids = self.df.loc[
            ~self.df["Recipient Org:0:Identifier:Clean"].isin(self._get_orgid_index()) &
            (self.df["Recipient Org:0:Identifier:Scheme"] == "GB-COH"),
            "Recipient Org:0:Identifier:Clean"
        ].unique()
        print("Finding details for {} companies".format(len(company_orgids)))
        for k, orgid in tqdm.tqdm(enumerate(company_orgids)):
            self._progress_job(k+1, len(company_orgids))
            try:
                self.cache.hset("company", orgid, json.dumps(self._get_company(orgid)))
            except ValueError:
                pass

        return self.df


class MergeCompanyAndCharityDetails(DataPreparationStage):

    name = 'Add charity and company details to data'

    COMPANY_REPLACE = {
        "PRI/LBG/NSC (Private, Limited by guarantee, no share capital, use of 'Limited' exemption)": "Company Limited by Guarantee",
        "PRI/LTD BY GUAR/NSC (Private, limited by guarantee, no share capital)": "Company Limited by Guarantee",
        "PRIV LTD SECT. 30 (Private limited company, section 30 of the Companies Act)": "Private Limited Company",
    }  # replacement values for companycategory

    def _get_org_type(self, id):
        if id.startswith("S") or id.startswith("GB-SC-"):
            return "Registered Charity (Scotland)"
        elif id.startswith("N") or id.startswith("GB-NIC-"):
            return "Registered Charity (NI)"
        return "Registered Charity (E&W)"

    def _create_orgid_df(self):
        charity_rows = []
        for k, c in self.cache.hscan_iter("charity"):
            c = json.loads(c)
            charity_rows.append({
                "orgid": k.decode("utf8"),
                "charity_number": c.get('id'),
                "company_number": c.get("company_number")[0].get("number") if c.get("company_number") else None,
                "date_registered": c.get("date_registered"),
                "date_removed": c.get("date_removed"),
                "postcode": c.get("geo", {}).get("postcode"),
                "latest_income": c.get("latest_income"),
                "org_type": self._get_org_type(c.get("id")),
            })

        orgid_df = pd.DataFrame(charity_rows).set_index("orgid")

        orgid_df.loc[:, "date_registered"] = pd.to_datetime(
            orgid_df.loc[:, "date_registered"])
        orgid_df.loc[:, "date_removed"] = pd.to_datetime(
            orgid_df.loc[:, "date_removed"])

        return orgid_df

    def _create_company_df(self):

        company_rows = []
        for k, c in self.cache.hscan_iter("company"):
            c = json.loads(c)
            company = c.get("primaryTopic", {})
            company = {} if company is None else company
            address = c.get("primaryTopic", {}).get("RegAddress", {})
            address = {} if address is None else address
            company_rows.append({
                "orgid": k.decode("utf8"),
                "charity_number": None,
                "company_number": company.get("CompanyNumber"),
                "date_registered": company.get("IncorporationDate"),
                "date_removed": company.get("DissolutionDate"),
                "postcode": address.get("Postcode"),
                "latest_income": None,
                "org_type": self.COMPANY_REPLACE.get(company.get("CompanyCategory"), company.get("CompanyCategory")),
            })
        
        if not company_rows:
            return None

        companies_df = pd.DataFrame(company_rows).set_index("orgid")
        companies_df.loc[:, "date_registered"] = pd.to_datetime(
            companies_df.loc[:, "date_registered"], dayfirst=True)
        companies_df.loc[:, "date_removed"] = pd.to_datetime(
            companies_df.loc[:, "date_removed"], dayfirst=True)

        return companies_df

    def run(self):

        # create orgid dataframes
        orgid_df = self._create_orgid_df()
        companies_df = self._create_company_df()

        if isinstance(orgid_df, pd.DataFrame) and isinstance(companies_df, pd.DataFrame):
            orgid_df = pd.concat([orgid_df, companies_df], sort=False)
        elif isinstance(companies_df, pd.DataFrame):
            orgid_df = companies_df
        
        if not isinstance(orgid_df, pd.DataFrame):
            return self.df

        # create some extra fields
        orgid_df.loc[:, "age"] = pd.datetime.now() - orgid_df["date_registered"]
        orgid_df.loc[:, "latest_income"] = orgid_df["latest_income"].astype(float)

        # merge org details into main dataframe
        self.df = self.df.join(orgid_df.rename(columns=lambda x: "__org_" + x),
                     on="Recipient Org:0:Identifier:Clean", how="left")
        return self.df

class FetchPostcodes(DataPreparationStage):

    name = 'Look up postcode data'
    pc_url = PC_URL

    def _get_postcode(self, pc):
        if self.cache.hexists("postcode", pc):
            return json.loads(self.cache.hget("postcode", pc))
        # @TODO: postcode cleaning and formatting
        return requests.get(self.pc_url.format(pc)).json()

    def run(self):
        # check for recipient org postcode field first
        if "Recipient Org:0:Postal Code" in self.df.columns and "__org_postcode" in self.df.columns:
            self.df.loc[:, "Recipient Org:0:Postal Code"] = self.df.loc[:, "Recipient Org:0:Postal Code"].fillna(self.df["__org_postcode"])
        elif "__org_postcode" in self.df.columns:
            self.df.loc[:, "Recipient Org:0:Postal Code"] = self.df["__org_postcode"]
        elif "Recipient Org:0:Postal Code" not in self.df.columns:
            self.df.loc[:, "Recipient Org:0:Postal Code"] = None

        # fetch postcode data
        postcodes = self.df.loc[:, "Recipient Org:0:Postal Code"].dropna().unique()
        print("Finding details for {} postcodes".format(len(postcodes)))
        for k, pc in tqdm.tqdm(enumerate(postcodes)):
            self._progress_job(k+1, len(postcodes))
            try:
                self.cache.hset("postcode", pc, json.dumps(self._get_postcode(pc)))
            except json.JSONDecodeError:
                continue

        return self.df

class MergeGeoData(DataPreparationStage):

    name = 'Add geo data'
    POSTCODE_FIELDS = POSTCODE_FIELDS

    def _convert_geocode(self, areatype, geocode_code):
        geocode_name = self.cache.hget(
            "geocodes", "-".join([areatype, str(geocode_code)]))
        if not geocode_name:
            return geocode_code
        if isinstance(geocode_name, bytes):
            return geocode_name.decode("utf8")
        return geocode_name

    def _create_postcode_df(self):
        postcode_rows = []
        for k, c in self.cache.hscan_iter("postcode"):
            c = json.loads(c)
            postcode_rows.append({
                **{"postcode": k.decode("utf8")},
                **{j: c.get("data", {}).get("attributes", {}).get(j) for j in self.POSTCODE_FIELDS}
            })
        postcode_df = pd.DataFrame(postcode_rows).set_index(
            "postcode")[self.POSTCODE_FIELDS]

        # swap out names for codes
        for c in postcode_df.columns:
            postcode_df.loc[:, c] = postcode_df[c].apply(
                lambda x: self._convert_geocode(c, str(x))
            ).fillna(postcode_df[c])
            if postcode_df[c].dtype == 'object':
                postcode_df.loc[:, c] = postcode_df[c].str.replace(r"\(pseudo\)", "")
                postcode_df.loc[
                    postcode_df[c].fillna("")=="N99999999",
                    c
                ] = "Northern Ireland"
                postcode_df.loc[
                    postcode_df[c].fillna("").str.endswith("99999999"),
                    c
                ] = None

        return postcode_df

    def run(self):
        postcode_df = self._create_postcode_df()
        self.df = self.df.join(postcode_df.rename(columns=lambda x: "__geo_" + x),
                        on="Recipient Org:0:Postal Code", how="left")
        return self.df

class AddExtraFieldsExternal(DataPreparationStage):

    name = 'Add extra fields from external data'

    # Bins used for numeric fields
    AMOUNT_BINS = [-1, 500, 1000, 2000, 5000, 10000, 100000, 1000000, float("inf")]
    AMOUNT_BIN_LABELS = ["Under £500", "£500 - £1k", "£1k - £2k", "£2k - £5k", "£5k - £10k",
                        "£10k - £100k", "£100k - £1m", "Over £1m"]
    INCOME_BINS = [-1, 10000, 100000, 1000000, 10000000, float("inf")]
    INCOME_BIN_LABELS = ["Under £10k", "£10k - £100k",
                        "£100k - £1m", "£1m - £10m", "Over £10m"]
    AGE_BINS = pd.to_timedelta(
        [x * 365 for x in [-1, 1, 2, 5, 10, 25, 200]], unit="D")
    AGE_BIN_LABELS = ["Under 1 year", "1-2 years", "2-5 years",
                    "5-10 years", "10-25 years", "Over 25 years"]

    def run(self):
        self.df.loc[:, "Amount Awarded:Bands"] = pd.cut(
            self.df["Amount Awarded"], bins=self.AMOUNT_BINS, labels=self.AMOUNT_BIN_LABELS)

        if "__org_latest_income" in self.df.columns:
            self.df.loc[:, "__org_latest_income_bands"] = pd.cut(self.df["__org_latest_income"].astype(float),
                                                                 bins=self.INCOME_BINS, labels=self.INCOME_BIN_LABELS)

        if "__org_age" in self.df.columns:
            self.df.loc[:, "__org_age_bands"] = pd.cut(
                self.df["__org_age"], bins=self.AGE_BINS, labels=self.AGE_BIN_LABELS)

        if "Grant Programme:0:Title" not in self.df.columns:
            self.df.loc[:, "Grant Programme:0:Title"] = "All grants"

        return self.df
