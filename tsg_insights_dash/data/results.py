import datetime
import re

import pandas as pd

from tsg_insights.data.utils import format_currency
from tsg_insights.data.process import AddExtraFieldsExternal

IDENTIFIER_MAP = {
    "360G": "Identifier not recognised",        # 360G          41190
    "GB-CHC": "Registered Charity (E&W)",       # GB-CHC        42190
    "GB-SC": "Registered Charity (Scotland)",   # GB-SC          7134
    "GB-NIC": "Registered Charity (NI)",        # GB-NIC          718
    "GB-COH": "Registered Company",             # GB-COH        11698
    "GB-GOR": "Government",                     # GB-GOR           13
    "GB-MPR": "Mutual",                         # GB-MPR           32
    "GB-NHS": "NHS",                            # GB-NHS           14
    "GB-UKPRN": "School/University/Education",  # GB-UKPRN         48
    "GB-EDU": "School/University/Education",    # GB-EDU          255
    "GB-SHPE": "Social Housing Provider",
    "GB-LAE": "Local Authority",                # GB-LAE           39
    "GB-LAS": "Local Authority",                # GB-LAS            2
    "GB-REV": "Registered Charity (HMRC)",      # GB-REV           92
    "US-EIN": "US - registered with IRS",       # US-EIN           38
    "ZA-NPO": "South Africa - registered with Nonprofit Organisation Directorate", # ZA-NPO           12
    "IM-GR": "Registered Charity (Isle of Man)",# IM-GR             8
    # NL-KVK            3
    # GG-RCE            3
    # XM-DAC            2
    # IL-ROC            2
    # BE-BCE_KBO        2
    # CA-CRA_ACR        2
    # ZA-PBO            2
    # SE-BLV            1
    # CH-FDJP           1
    # JE-FSC            1
}

INCOME_BAND_CHANGES = {
    "Under £10k": "Up to £10k",
    "£10k - £100k": "£10k - £100k",
    "£100k - £250k": "£100k - £250k",
    "£250k - £500k": "£250k - £500k",
    "£500k - £1m": "£500k - £1m",
    "£1m - £10m": "£1.1m - £10m",
    "Over £10m": "Over £10m"
}

AWARD_BAND_CHANGES = {
    "Under 500": "Up to 500",
    "500 - 1k": "501 - 1,000",
    "1k - 2k": "1,001 - 2,000",
    "2k - 5k": "2,001 - 5,000",
    "5k - 10k": "5,001 - 10,000",
    "10k - 100k": "10,001 - 100k",
    "100k - 1m": "101k - 1m",
    "Over 1m": "Over 1m",
}

AGE_BAND_CHANGES = {
    "Under 1 year": "Up to 1 year",
    "1-2 years": "2 years",
    "2-5 years": "3-5 years",
    "5-10 years": "6-10 years",
    "10-25 years": "11-25 years",
    "Over 25 years": "Over 25 years"
}

def band_sort(value, l):
    if value not in l:
        return 0
    return l.index(value)

def get_imd_data(df):

    imd_order = [
        '1: most deprived', '2 ', '3 ', '4 ', '5 ', '6 ', '7 ', '8 ', '9 ', '10: least deprived'
    ]

    imd = df.loc[df['__geo_ctry'] == 'England', '__geo_imd']
    if imd.count() == 0:
        return None

    # maximum rank of LSOAs by IMD
    # from: https://www.arcgis.com/sharing/rest/content/items/0a404beab6f544be8fb72d0c2b12d62b/data
    # NSPL user guid
    # 1 = most deprived, this number = most deprived
    imd_total_eng = 32844
    imd_total_scot = 6976
    imd_total_wal = 1909
    imd_total_ni = 890

    # work out the IMD decile
    imd = ((imd / imd_total_eng) * 10).apply(pd.np.ceil).value_counts().sort_index().reindex(
        pd.np.arange(1, 11)
    ).fillna(0)

    imd.index = pd.Series(imd_order)
    return imd


def get_statistics(df):
    curr_gb = df.groupby("Currency")
    currencies = pd.DataFrame({
        "total": curr_gb["Amount Awarded"].sum(),
        "median": curr_gb["Amount Awarded"].median(),
        "grants": curr_gb.size(),
        "recipients": curr_gb["Recipient Org:0:Identifier"].nunique(),
    })
    currencies = currencies.sort_values("grants", ascending=False).to_dict('index')
    for c in currencies:
        currencies[c]["total_f"] = format_currency(currencies[c]["total"], c)
        currencies[c]["median_f"] = format_currency(currencies[c]["median"], c)

    return {
        "grants": len(df),
        "recipients": df["Recipient Org:0:Identifier"].unique().size,
        "currencies": currencies,
        "award_years": {
            "min": df["summary"][0]["minDate"][0:4],
            "max": df["summary"][0]["maxDate"][0:4],
        }
    }


def get_ctry_rgn(df):

    if not [i for i in df.get("byCountryRegion", []) if i["bucketId"]]:
        return None

    REGION_ORDER = {
        "S99999999": ("Scotland", "Scotland"),
        "N99999999": ("Northern Ireland", "Northern Ireland"),
        "W99999999": ("Wales", "Wales"),
        "E12000001": ("England", "North East"),
        "E12000002": ("England", "North West"),
        "E12000003": ("England", "Yorkshire and The Humber"),
        "E12000005": ("England", "West Midlands"),
        "E12000004": ("England", "East Midlands"),
        "E12000006": ("England", "East of England"),
        "E12000007": ("England", "London"),
        "E12000009": ("England", "South West"),
        "E12000008": ("England", "South East"),
        "M99999999": ("Isle of Man", "Isle of Man"),
        "L99999999": ("Channel Islands", "Channel Islands"),
        "Unknown": ("Unknown", "Unknown"),
    }

    values = {
        v["bucket2Id"] if v["bucket2Id"] else "Unknown": v["grants"]
        for v in df["byCountryRegion"]
    }

    # generate region groupby
    ctry_rgn = [
        (v, values.get(k, 0), k)
        for k, v in REGION_ORDER.items()
    ][::-1]

    return ctry_rgn


def get_identifier_schemes(df):
    identifier_schemes = df["Recipient Org:0:Identifier"].apply(
        lambda x: "360G" if len(x.split("-"))<3 or x.startswith("360G-") else "-".join(x.split("-")[:2]))
    
    if "__org_org_type" in df:
        identifier_schemes = df["__org_org_type"].fillna(
            identifier_schemes
        )

    return identifier_schemes.fillna(
        "Identifier not recognised"
    ).apply(
        lambda x: IDENTIFIER_MAP.get(x, "Other identifier")
    )


CHARTS = dict(
    funders={
        'title': 'Funders',
        'units': '(number of grants)',
        'get_results': (lambda df: [(v["bucket2Id"], v["grants"]) for v in sorted(df["byFunder"], key=lambda x: -x['grants'])]),
    },
    grant_programmes={
        'title': 'Grant programmes',
        'units': '(number of grants)',
        'get_results': (lambda df: [(v["bucketId"], v["grants"]) for v in sorted(df["byGrantProgramme"], key=lambda x: -x['grants']) if v["bucketId"]]),
    },
    amount_awarded={
        'title': 'Amount awarded',
        'units': '(number of grants)',
        'get_results': (lambda df: {
            w["bucketId"]: [
                (AWARD_BAND_CHANGES.get(v["bucket2Id"], v["bucket2Id"]), v["grants"])
                for v in sorted(
                    df["byAmountAwarded"],
                    key=lambda x: band_sort(x['bucket2Id'], list(AWARD_BAND_CHANGES.keys()))
                )
                if w.get("bucketId") == v.get("bucketId")]
            for w in df["byAmountAwarded"]
        }),
    },
    identifier_scheme={
        'title': 'Identifier scheme',
        'units': '(number of grants)',
        'get_results': (lambda df: df["Recipient Org:0:Identifier"].apply(
            lambda x: "360G" if x.startswith("360G-") else "-".join(x.split("-")[:2])).value_counts().sort_index()),
    },
    award_date={
        'title': 'Award date',
        'units': '(number of grants)',
        'get_results': (lambda df: {
            "all": [inner for outer in [
                [datetime.datetime.strptime(v["bucketId"], "%Y-%m-%d")] * v["grants"] for v in df["byAwardDate"]
            ] for inner in outer],
            "min": datetime.datetime.strptime(df["summary"][0]["minDate"], "%Y-%m-%d"),
            "max": datetime.datetime.strptime(df["summary"][0]["maxDate"], "%Y-%m-%d")
        }),
    },
    ctry_rgn={
        'title': 'UK region and country',
        'units': '(number of grants)',
        'desc': '''This chart is based on postcodes found in the grants data.
If postcodes aren’t present, they are sourced from UK charity or company registers.''',
        'missing': '''This chart can\'t be shown as there is no information on the country and region of recipients or grants. 
This can be added by using charity or company numbers, or by including a postcode.''',
        'get_results': get_ctry_rgn,
    },
    org_type={
        'title': 'Recipient type',
        'units': '(proportion of grants)',
        'desc': '''Organisation type is only available for recipients with a valid
organisation identifier.''',
        'get_results': (lambda df: [
            (v["bucketId"] if v["bucketId"] else "Identifier not recognised", v["grants"])
            for v in sorted(df["byOrgType"], key=lambda x: x['grants'] if x["bucketId"] else -x["grants"])
        ]),
    },
    org_income={
        'title': 'Latest income of charity recipients',
        'units': '(number of grants)',
        'missing': '''This chart can\'t be shown as there are no recipients in the data with 
organisation income data. Add company or charity numbers to your data to show a chart of
the income of organisations.''',
        'get_results': (lambda df: [
            (v["bucketId"], v["grants"])
            for v in sorted(df["byOrgSize"], key=lambda x: band_sort(x['bucketId'], list(INCOME_BAND_CHANGES.keys())))
            if v["bucketId"]
        ]),
    },
    org_age={
        'title': 'Age of recipient organisations',
        'units': '(number of grants)',
        'desc': 'Organisation age at the time of the grant award, based on the registration date of that organisation. Only available for recipients with charity or company numbers.',
        'missing': '''This chart can\'t be shown as there are no recipients in the data with 
organisation age data. Add company or charity numbers to your data to show a chart of
the age of organisations.''',
        'get_results': (lambda df: [
            (AGE_BAND_CHANGES.get(v["bucketId"], v["bucketId"]), v["grants"])
            for v in sorted(df["byOrgAge"], key=lambda x: band_sort(x['bucketId'], list(AGE_BAND_CHANGES.keys())))
            if v["bucketId"]
        ]),
    },
    imd={
        'title': 'Index of multiple deprivation',
        'units': '(number of grants)',
        'desc': '''Shows the number of grants made in each decile of deprivation in England, 
        from 1 (most deprived) to 10 (most deprived). Based on the postcode included with the grant
        or on an organisation's registered postcode, so may not reflect where grant activity took place.''',
        'missing': '''We can't show this chart as we couldn't find any details of the index of multiple deprivation 
            ranking for postcodes in your data. At the moment we can only use data for England.''',
        'get_results': get_imd_data,
    },
)
