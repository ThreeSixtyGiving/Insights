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
    # "Under £10k": "Up to £10k",
    # "£10k - £100k": "£11k - £100k",
    # "£100k - £1m": "£101k - £1m",
    # "£1m - £10m": "£1.1m - £10m",
    # "Over £10m": "Over £10m"
}

AWARD_BAND_CHANGES = {
    "Under £500": "Up to £500",
    "£500 - £1k": "£501 - £1,000",
    "£1k - £2k": "£1,001 - £2,000",
    "£2k - £5k": "£2,001 - £5,000",
    "£5k - £10k": "£5,001 - £10,000",
    "£10k - £100k": "£10,001 - £100k",
    "£100k - £1m": "£101k - £1m",
    "Over £1m": "Over £1m",
}

AGE_BAND_CHANGES = {
    "Under 1 year": "Up to 1 year",
    "1-2 years": "2 years",
    "2-5 years": "3-5 years",
    "5-10 years": "6-10 years",
    "10-25 years": "11-25 years",
    "Over 25 years": "Over 25 years"
}

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
        "total": curr_gb.sum()["Amount Awarded"],
        "median": curr_gb.median()["Amount Awarded"],
        "grants": curr_gb.size(),
        "recipients": curr_gb.nunique()["Recipient Org:0:Identifier"],
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
            "min": df["Award Date"].dt.year.min(),
            "max": df["Award Date"].dt.year.max(),
        }
    }


def get_ctry_rgn(df):

    if "__geo_ctry" not in df.columns or "__geo_rgn" not in df.columns:
        return None

    REGION_ORDER = [
        ("Scotland", "Scotland"),
        ("Northern Ireland", "Northern Ireland"),
        ("Wales", "Wales"),
        ("England", "North East"),
        ("England", "North West"),
        ("England", "Yorkshire and The Humber"),
        ("England", "West Midlands"),
        ("England", "East Midlands"),
        ("England", "East of England"),
        ("England", "London"),
        ("England", "South West"),
        ("England", "South East"),
        ("Isle of Man", "Isle of Man"),
        ("Unknown", "Unknown"),
    ]

    # generate region groupby
    ctry_rgn = df.groupby([
        df["__geo_ctry"].fillna("Unknown").str.strip(),
        # ensure countries where region is null are correctly labelled
        df.loc[:, "__geo_rgn"].fillna(df["__geo_ctry"]).fillna("Unknown").str.strip(),
    ]).agg({
        "Amount Awarded": "sum",
        "Title": "size"
    }).rename(columns={"Title": "Grants"})

    # Sort from North -> South
    idx = ctry_rgn.index.tolist()
    new_idx = [i for i in REGION_ORDER if i in idx] + [i for i in idx if i not in REGION_ORDER]
    ctry_rgn = ctry_rgn.reindex(new_idx)

    return ctry_rgn


def get_org_income_bands(df):
    return pd.cut(
        df["__org_latest_income"],
        bins=AddExtraFieldsExternal.INCOME_BINS,
        labels=AddExtraFieldsExternal.INCOME_BIN_LABELS
    )

def get_org_income(df):
    return get_org_income_bands(df).value_counts().sort_index()


def get_org_type(df):
    return get_identifier_schemes(df).value_counts().sort_index()


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
        lambda x: IDENTIFIER_MAP.get(x, x)
    )


CHARTS = dict(
    funders={
        'title': 'Funders',
        'units': '(number of grants)',
        'get_results': (lambda df: df["Funding Org:0:Name"].value_counts()),
    },
    grant_programmes={
        'title': 'Grant programmes',
        'units': '(number of grants)',
        'get_results': (lambda df: df["Grant Programme:0:Title"].value_counts()),
    },
    amount_awarded={
        'title': 'Amount awarded',
        'units': '(number of grants)',
        'get_results': (lambda df: pd.crosstab(
            df["Amount Awarded:Bands"].cat.rename_categories(AWARD_BAND_CHANGES),
            df["Currency"],
            dropna=False
        ).sort_index()),
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
            "all": df['Award Date'].dt.strftime("%Y-%m-%d").tolist(),
            "min": df['Award Date'].dt.year.min(),
            "max": df['Award Date'].dt.year.max()
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
        'get_results': get_org_type,
    },
    org_income={
        'title': 'Latest income of charity recipients',
        'units': '(number of grants)',
        'missing': '''This chart can\'t be shown as there are no recipients in the data with 
organisation income data. Add company or charity numbers to your data to show a chart of
the income of organisations.''',
        'get_results': get_org_income,
    },
    org_age={
        'title': 'Age of recipient organisations',
        'units': '(number of grants)',
        'desc': 'Organisation age at the time of the grant award, based on the registration date of that organisation. Only available for recipients with charity or company numbers.',
        'missing': '''This chart can\'t be shown as there are no recipients in the data with 
organisation age data. Add company or charity numbers to your data to show a chart of
the age of organisations.''',
        'get_results': (lambda df: df["__org_age_bands"].cat.rename_categories(AGE_BAND_CHANGES).value_counts().sort_index()),
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
