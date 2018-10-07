import io
import json
import os

import pandas as pd
import requests
import tqdm

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
    for c in columns_to_check:
        if c not in df.columns:
            raise ValueError("Column {} not found in data".format(c))

    # ensure correct column types
    df.loc[:, "Award Date"] = pd.to_datetime(df["Award Date"])

    # add additional columns
    df.loc[:, "Award Date:Year"] = df["Award Date"].dt.year
    df.loc[:, "Recipient Org:Identifier:Scheme"] = df["Recipient Org:Identifier"].apply(
        lambda x: "360G" if x.startswith("360G-") else "-".join(x.split("-")[:2]))

    # add a column with a "clean" identifier that can be fetched from find that charity
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
    orgids = df.loc[df["Recipient Org:Identifier:Scheme"].isin(
        FTC_SCHEMES), "Recipient Org:Identifier:Clean"].dropna().unique()
    print("Finding details for {} charities".format(len(orgids)))
    for orgid in tqdm.tqdm(orgids):
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
    company_orgids = df.loc[
        ~df["Recipient Org:Identifier:Clean"].isin(orgid_df.index) &
        (df["Recipient Org:Identifier:Scheme"]=="GB-COH"), "Recipient Org:Identifier:Clean"].unique()
    print("Finding details for {} companies".format(len(company_orgids)))
    for orgid in tqdm.tqdm(company_orgids):
        if orgid not in cache["company"]:
            try:
                cache["company"][orgid] = get_company(orgid)
            except ValueError:
                pass

    # create company dataframe
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
    if "Recipient Org:Postcode" in df.columns:
        df.loc[:, "Recipient Org:Postcode"] = df.loc[:, "Recipient Org:Postcode"].fillna(df["postcode"])
    else:
        df.loc[:, "Recipient Org:Postcode"] = df["__org_postcode"]

    # fetch postcode data
    postcodes = df.loc[:, "Recipient Org:Postcode"].dropna().unique()
    print("Finding details for {} postcodes".format(len(postcodes)))
    for pc in tqdm.tqdm(postcodes):
        if pc not in cache["postcode"]:
            try:
                cache["postcode"][pc] = requests.get(PC_URL.format(pc)).json()
            except json.JSONDecodeError:
                continue

    # turn into a dataframe
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
    df = df.join(postcode_df.rename(columns=lambda x: "__geo_" + x), on="Recipient Org:Postcode", how="left")

    # add banded fields
    amount_bins = [0,500,1000,2000,5000,10000,100000,1000000,float("inf")]
    amount_bin_labels = ["Under £500", "£500 - £1,000", "£1,000 - £2,000", "£2k - £5k", "£5k - £10k",
                        "£10k - £100k", "£100k - £1m", "Over £1m"]
    income_bins = [0,10000,100000,1000000,10000000,float("inf")]
    income_bin_labels = ["Under £10k", "£10k - £100k", "£100k - £1m", "£1m - £10m", "Over £10m"]
    age_bins = pd.to_timedelta([x * 365 for x in [0,1,2,5,10,25,200]], unit="D")
    age_bin_labels = ["Under 1 year", "1-2 years", "2-5 years", "5-10 years", "10-25 years", "Over 25 years"]
    df.loc[:, "Amount Awarded:Bands"] = pd.cut(df["Amount Awarded"], bins=amount_bins, labels=amount_bin_labels)
    df.loc[:, "__org_latest_income_bands"] = pd.cut(df["__org_latest_income"].astype(float), 
                                                bins=income_bins, labels=income_bin_labels)
    df.loc[:, "__org_age_bands"] = pd.cut(df["__org_age"], bins=age_bins, labels=age_bin_labels)

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

