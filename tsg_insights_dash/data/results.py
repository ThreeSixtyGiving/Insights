import pandas as pd

from tsg_insights.data.utils import format_currency


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
        "recipients": df["Recipient Org:Identifier"].unique().size,
        "amount_awarded": amount_awarded,
        "award_years": {
            "min": df["Award Date"].dt.year.min(),
            "max": df["Award Date"].dt.year.max(),
        }
    }


def get_ctry_rgn(df):

    ctry_rgn = df.fillna({"__geo_ctry": "Unknown", "__geo_rgn": "Unknown"}).groupby(["__geo_ctry", "__geo_rgn"]).agg({
        "Amount Awarded": "sum",
        "Title": "size"
    }).rename(columns={"Title": "Grants"})
    # ctry_rgn.index = ctry_rgn.index.map(
    #     lambda x: " - ".join(x) if x[0].strip() != x[1].strip() else x[0].strip())
    return ctry_rgn


CHARTS = dict(
    funders={
        'title': 'Funders',
        'units': '(number of grants)',
        'get_results': (lambda df: df["Funding Org:Name"].value_counts()),
    },
    grant_programmes={
        'title': 'Grant programmes',
        'units': '(number of grants)',
        'get_results': (lambda df: df["Grant Programme:Title"].value_counts()),
    },
    amount_awarded={
        'title': 'Amount awarded',
        'units': '(number of grants)',
        'get_results': (lambda df: df["Amount Awarded:Bands"].value_counts().sort_index()),
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
        'get_results': (lambda df: df["__org_org_type"].fillna(
            "No organisation identifier").value_counts().sort_index()),
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
