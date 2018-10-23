import io
import json
import os

import pandas as pd
import requests
import tqdm
from rq import get_current_job

FTC_URL  = 'https://findthatcharity.uk/orgid/{}.json'
CH_URL   = 'http://data.companieshouse.gov.uk/doc/company/{}.json'
PC_URL   = 'https://postcodes.findthatcharity.uk/postcodes/{}.json'

# config
FTC_SCHEMES = ["GB-CHC", "GB-NIC", "GB-SC", "GB-COH"] # schemes with data on findthatcharity
COMPANY_REPLACE = {
    "PRI/LBG/NSC (Private, Limited by guarantee, no share capital, use of 'Limited' exemption)": "Company Limited by Guarantee",
    "PRI/LTD BY GUAR/NSC (Private, limited by guarantee, no share capital)": "Company Limited by Guarantee",
    "PRIV LTD SECT. 30 (Private limited company, section 30 of the Companies Act)": "Private Limited Company",
} # replacement values for companycategory
POSTCODE_FIELDS = ['ctry', 'cty', 'laua', 'pcon', 'rgn', 'imd', 'ru11ind', 'oac11', 'lat', 'long'] # fields to care about from the postcodes)

# Bins used for numeric fields
AMOUNT_BINS = [0,500,1000,2000,5000,10000,100000,1000000,float("inf")]
AMOUNT_BIN_LABELS = ["Under £500", "£500 - £1,000", "£1,000 - £2,000", "£2k - £5k", "£5k - £10k",
                    "£10k - £100k", "£100k - £1m", "Over £1m"]
INCOME_BINS = [0,10000,100000,1000000,10000000,float("inf")]
INCOME_BIN_LABELS = ["Under £10k", "£10k - £100k", "£100k - £1m", "£1m - £10m", "Over £10m"]
AGE_BINS = pd.to_timedelta([x * 365 for x in [0,1,2,5,10,25,200]], unit="D")
AGE_BIN_LABELS = ["Under 1 year", "1-2 years", "2-5 years", "5-10 years", "10-25 years", "Over 25 years"]

# utils
def charity_number_to_org_id(regno):
    if not isinstance(regno, str):
        return None
    if regno.startswith("S"):
        return "GB-SC-{}".format(regno)
    elif regno.startswith("N"):
        return "GB-NIC-{}".format(regno)
    else:
        return "GB-CHC-{}".format(regno)


def get_charity(orgid, ftc_url=FTC_URL):
    return requests.get(ftc_url.format(orgid)).json()

def get_company(orgid, ch_url=CH_URL):
    return requests.get(ch_url.format(orgid.replace("GB-COH-", ""))).json()


def prepare_data(df, cache={}):
    
    job = get_current_job()
    job.meta['stages'] = [
        'Check column names', 'Check columns exist', 'Check column types',
        'Add extra columns', 'Clean recipient identifiers', 'Look up charity data',
        'Look up company data', 'Add charity and company details to data', 
        'Look up postcode data', 'Add geo data', 'Add extra fields from external data'
    ]
    job.meta['progress'] = {"stage": 0, "progress": None}

    def progress_job(add_stage=1, progress=None):
        job.meta['progress']["stage"] += add_stage
        job.meta['progress']["progress"] = progress
        job.save_meta()

    # check column names for typos
    columns_to_check = [
        'Amount Awarded', 'Funding Org:Name', 'Award Date', 
        'Recipient Org:Name', 'Recipient Org:Identifier'
    ]
    renames = {}
    for c in df.columns:
        for w in columns_to_check:
            if c.replace(" ","").lower() == w.replace(" ","").lower() and c != w:
                renames[c] = w
    df = df.rename(columns=renames)

    # columns to check exist
    progress_job()
    for c in columns_to_check:
        if c not in df.columns:
            raise ValueError("Column {} not found in data".format(c))

    # ensure correct column types
    progress_job()
    df.loc[:, "Award Date"] = pd.to_datetime(df["Award Date"])

    # add additional columns
    progress_job()
    df.loc[:, "Award Date:Year"] = df["Award Date"].dt.year
    df.loc[:, "Recipient Org:Identifier:Scheme"] = df["Recipient Org:Identifier"].apply(
        lambda x: "360G" if x.startswith("360G-") else "-".join(x.split("-")[:2]))

    # add a column with a "clean" identifier that can be fetched from find that charity
    progress_job()
    df.loc[
        df["Recipient Org:Identifier:Scheme"].isin(FTC_SCHEMES), "Recipient Org:Identifier:Clean"
    ] = df.loc[df["Recipient Org:Identifier:Scheme"].isin(FTC_SCHEMES), "Recipient Org:Identifier"]
    if "Recipient Org:Company Number" in df.columns:
        df.loc[:, "Recipient Org:Identifier:Clean"] = df.loc[:, "Recipient Org:Identifier:Clean"].fillna(
            df["Recipient Org:Company Number"].apply("GB-COH-{}".format))
    if "Recipient Org:Charity Number" in df.columns:
        df.loc[:, "Recipient Org:Identifier:Clean"] = df.loc[:, "Recipient Org:Identifier:Clean"].fillna(
            df["Recipient Org:Charity Number"].apply(charity_number_to_org_id))
    df.loc[:, "Recipient Org:Identifier:Scheme"] = df["Recipient Org:Identifier:Clean"].apply(
        lambda x: ("360G" if x.startswith("360G-") else "-".join(x.split("-")[:2])) if isinstance(x, str) else None
        ).fillna(df["Recipient Org:Identifier:Scheme"])

    # look for any charity details
    progress_job()
    orgids = df.loc[df["Recipient Org:Identifier:Scheme"].isin(
        FTC_SCHEMES), "Recipient Org:Identifier:Clean"].dropna().unique()
    print("Finding details for {} charities".format(len(orgids)))
    for k, orgid in tqdm.tqdm(enumerate(orgids)):
        progress_job(0, (k+1, len(orgids)))
        if orgid not in cache["charity"]:
            try:
                cache["charity"][orgid] = get_charity(orgid)
            except ValueError:
                pass

    # construct a dataframe from charity details
    orgid_df = pd.DataFrame([{
        "orgid": k,
        "charity_number": c.get('id'),
        "company_number": c.get("company_number")[0].get("number") if c.get("company_number") else None,
        "date_registered": c.get("date_registered"),
        "date_removed": c.get("date_removed"),
        "postcode": c.get("geo", {}).get("postcode"),
        "latest_income": c.get("latest_income"),
        "org_type": "Registered Charity"
    } for k, c in cache["charity"].items() if c.get('id')]).set_index("orgid")
    orgid_df.loc[:, "date_registered"] = pd.to_datetime(
        orgid_df.loc[:, "date_registered"])
    orgid_df.loc[:, "date_removed"] = pd.to_datetime(
        orgid_df.loc[:, "date_removed"])

    # look for any company details
    progress_job()
    company_orgids = df.loc[
        ~df["Recipient Org:Identifier:Clean"].isin(orgid_df.index) &
        (df["Recipient Org:Identifier:Scheme"]=="GB-COH"), "Recipient Org:Identifier:Clean"].unique()
    print("Finding details for {} companies".format(len(company_orgids)))
    for k, orgid in tqdm.tqdm(enumerate(company_orgids)):
        progress_job(0, (k+1, len(company_orgids)))
        if orgid not in cache["company"]:
            try:
                cache["company"][orgid] = get_company(orgid)
            except ValueError:
                pass

    # create company dataframe
    progress_job()
    if cache["company"]:
        company_rows = []
        for k, c in cache["company"].items():
            try:
                company = c.get("primaryTopic", {})
                company = {} if company is None else company
                address = c.get("primaryTopic", {}).get("RegAddress", {})
                address = {} if address is None else address
                company_rows.append({
                    "orgid": k,
                    "charity_number": None,
                    "company_number": company.get("CompanyNumber"),
                    "date_registered": company.get("IncorporationDate"),
                    "date_removed": company.get("DissolutionDate"),
                    "postcode": address.get("Postcode"),
                    "latest_income": None,
                    "org_type": COMPANY_REPLACE.get(company.get("CompanyCategory"), company.get("CompanyCategory")),
                })
            except AttributeError:
                pass
        companies_df = pd.DataFrame(company_rows).set_index("orgid")
        companies_df.loc[:, "date_registered"] = pd.to_datetime(
            companies_df.loc[:, "date_registered"], dayfirst=True)
        companies_df.loc[:, "date_removed"] = pd.to_datetime(
            companies_df.loc[:, "date_removed"], dayfirst=True)

        # merge in companies
        orgid_df = pd.concat([orgid_df, companies_df], sort=False)

    # create some extra fields
    orgid_df.loc[:, "age"] = pd.datetime.now() - orgid_df["date_registered"]
    orgid_df.loc[:, "latest_income"] = orgid_df["latest_income"].astype(float)

    # merge org details into main dataframe
    df = df.join(orgid_df.rename(columns=lambda x: "__org_" + x),
                on="Recipient Org:Identifier:Clean", how="left")


    # look for postcode

    # check for recipient org postcode field first
    if "Recipient Org:Postal Code" in df.columns:
        df.loc[:, "Recipient Org:Postal Code"] = df.loc[:, "Recipient Org:Postal Code"].fillna(df["__org_postcode"])
    else:
        df.loc[:, "Recipient Org:Postal Code"] = df["__org_postcode"]

    # fetch postcode data
    progress_job()
    postcodes = df.loc[:, "Recipient Org:Postal Code"].dropna().unique()
    print("Finding details for {} postcodes".format(len(postcodes)))
    for k, pc in tqdm.tqdm(enumerate(postcodes)):
        progress_job(0, (k+1, len(postcodes)))
        if pc not in cache["postcode"]:
            try:
                cache["postcode"][pc] = requests.get(PC_URL.format(pc)).json()
            except json.JSONDecodeError:
                continue

    # turn into a dataframe
    progress_job()
    postcode_df = pd.DataFrame([{
        **{"postcode": k}, 
        **{j: c.get("data", {}).get("attributes", {}).get(j) for j in POSTCODE_FIELDS}
    } for k, c in cache["postcode"].items()]).set_index("postcode")[POSTCODE_FIELDS]

    # swap out codes for names
    for c in postcode_df.columns:
        postcode_df.loc[:, c] = postcode_df[c].apply(lambda x: cache["geocodes"].get("-".join([c, str(x)]), x))
        if postcode_df[c].dtype == 'object':
            postcode_df.loc[:, c] = postcode_df[c].str.replace(r"\(pseudo\)", "")
            postcode_df.loc[postcode_df[c].fillna("").str.endswith("99999999"), c] = None

    # merge into main dataframe
    df = df.join(postcode_df.rename(columns=lambda x: "__geo_" + x), on="Recipient Org:Postal Code", how="left")

    # add banded fields
    progress_job()
    df.loc[:, "Amount Awarded:Bands"] = pd.cut(df["Amount Awarded"], bins=AMOUNT_BINS, labels=AMOUNT_BIN_LABELS)
    df.loc[:, "__org_latest_income_bands"] = pd.cut(df["__org_latest_income"].astype(float), 
                                                bins=INCOME_BINS, labels=INCOME_BIN_LABELS)
    df.loc[:, "__org_age_bands"] = pd.cut(df["__org_age"], bins=AGE_BINS, labels=AGE_BIN_LABELS)

    if "Grant Programme:Title" not in df.columns:
        df.loc[:, "Grant Programme:Title"] = "All grants"

    return (df, cache)

def fetch_geocodes():
    r = requests.get("https://postcodes.findthatcharity.uk/areas/names.csv", params={"types": ",".join(POSTCODE_FIELDS)})
    pc_names = pd.read_csv(io.StringIO(r.text)).set_index(
        ["type", "code"]).sort_index()
    geocodes = pc_names["name"].to_dict()
    geocodes = {"-".join(c): d for c,d in geocodes.items()}
    return geocodes

