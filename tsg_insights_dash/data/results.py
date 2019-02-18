import pandas as pd

from tsg_insights.data.utils import format_currency

IDENTIFIER_MAP = {
    "360G": "No organisation identifier",       # 360G          41190
    "GB-CHC": "Registered Charity",             # GB-CHC        42190
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
    amount_awarded = df.groupby("Currency").sum()["Amount Awarded"]
    amount_awarded = [format_currency(amount, currency)
                      for currency, amount in amount_awarded.items()]

    return {
        "grants": len(df),
        "recipients": df["Recipient Org:0:Identifier"].unique().size,
        "amount_awarded": amount_awarded,
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
        "No organisation identifier"
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
        'get_results': (lambda df: pd.crosstab(df["Amount Awarded:Bands"], df["Currency"]).sort_index()),
    },
    identifier_scheme={
        'title': 'Identifier scheme',
        'units': '(number of grants)',
        'get_results': (lambda df: df["Recipient Org:0:Identifier"].apply(
            lambda x: "360G" if x.startswith("360G-") else "-".join(x.split("-")[:2])).value_counts().sort_index()),
    },
    award_date={
        'title': 'Award Date',
        'units': '(number of grants)',
        'get_results': (lambda df: {
            "all": df['Award Date'].dt.strftime("%Y-%m-%d").tolist(),
            "min": df['Award Date'].dt.year.min(),
            "max": df['Award Date'].dt.year.max()
        }),
    },
    ctry_rgn={
        'title': 'Region and Country',
        'units': '(number of grants)',
        'desc': '''Based on the registered address of a charity or company
(or a postcode if included with the grant data). Only available for registered
charities or companies, or those grants which contain a postcode.''',
        'missing': '''This chart can\'t be shown as there are no recipients in the data with 
income data. If your data contains grants to charities, you can add charity
numbers to your data to show a chart of their latest income.''',
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
        'get_results': (lambda df: df["__org_latest_income_bands"].value_counts().sort_index()),
    },
    org_age={
        'title': 'Age of recipient organisations',
        'units': '(number of grants)',
        'desc': 'Organisation age uses the registration date of that organisation. Based only on recipients with charity or company numbers.',
        'missing': '''This chart can\'t be shown as there are no recipients in the data with 
organisation age data. Add company or charity numbers to your data to show a chart of
the age of organisations.''',
        'get_results': (lambda df: df["__org_age_bands"].value_counts().sort_index()),
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
