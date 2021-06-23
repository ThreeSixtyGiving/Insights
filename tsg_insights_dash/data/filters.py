from pandas import NA

from tsg_insights.data.cache import get_from_cache

from .results import (
    AGE_BAND_CHANGES,
    AWARD_BAND_CHANGES,
    INCOME_BAND_CHANGES,
    get_ctry_rgn,
    get_identifier_schemes,
    get_org_income,
    get_org_income_bands,
)


def get_filtered_df(fileid, **filters):
    df = get_from_cache(fileid)

    # fix for region and country being wrongly encoded
    df.loc[df["__geo_ctry"].isin(["None", "Unknown"]), "__geo_ctry"] = NA
    df.loc[df["__geo_rgn"].isin(["None", "Unknown"]), "__geo_rgn"] = NA

    for filter_id, filter_def in FILTERS.items():
        new_df = filter_def["apply_filter"](df, filters.get(filter_id), filter_def)
        if new_df is not None:
            df = new_df

    return df


def apply_area_filter(df, filter_args, filter_def):

    if not filter_args or filter_args == ["__all"]:
        return

    countries = []
    regions = []
    for f in filter_args:
        if "##" in f:
            f = f.split("##")
            countries.append(f[0])
            regions.append(f[1])
    if countries and regions:
        return df[
            (df["__geo_ctry"].isin(countries))
            & (df["__geo_rgn"].fillna(df["__geo_ctry"]).isin(regions))
        ]


def apply_org_size_filter(df, filter_args, filter_def):

    if not filter_args or filter_args == ["__all"]:
        return

    bands = get_org_income_bands(df)
    return df[bands.isin(filter_args)]


def apply_org_type_filter(df, filter_args, filter_def):

    if not filter_args or filter_args == ["__all"]:
        return

    org_type = get_identifier_schemes(df)
    return df[org_type.isin(filter_args)]


def apply_field_filter(df, filter_args, filter_def):

    if not filter_args or filter_args == ["__all"]:
        return

    return df[df[filter_def["field"]].isin(filter_args)]


def apply_date_range_filter(df, filter_args, filter_def):
    if not filter_args or df is None:
        return

    return df[
        (df[filter_def["field"]].dt.year >= int(filter_args[0]))
        & (df[filter_def["field"]].dt.year <= int(filter_args[1]))
    ]


def apply_range_filter(df, filter_args, filter_def):
    if not filter_args or df is None:
        return

    return df[
        (df[filter_def["field"]] >= filter_args[0])
        & (df[filter_def["field"]] <= filter_args[1])
    ]


FILTERS = {
    "funders": {
        "label": "Funders",
        "type": "multidropdown",
        "defaults": [{"label": "Funder", "value": "__all"}],
        "get_values": (
            lambda df: [
                {"label": "{} ({})".format(i[0], i[1]), "value": i[0]}
                for i in df["Funding Org:0:Name"].value_counts().iteritems()
            ]
        ),
        "field": "Funding Org:0:Name",
        "apply_filter": apply_field_filter,
    },
    "grant_programmes": {
        "label": "Grant programmes",
        "type": "multidropdown",
        "defaults": [{"label": "All grants", "value": "__all"}],
        "get_values": (
            lambda df: [
                {"label": "{} ({})".format(i[0], i[1]), "value": i[0]}
                for i in df["Grant Programme:0:Title"].value_counts().iteritems()
            ]
        ),
        "field": "Grant Programme:0:Title",
        "apply_filter": apply_field_filter,
    },
    "award_dates": {
        "label": "Date awarded",
        "type": "rangeslider",
        "defaults": {"min": 2015, "max": 2018},
        "get_values": (
            lambda df: {
                "min": int(df["Award Date"].dt.year.min()),
                "max": int(df["Award Date"].dt.year.max()),
            }
        ),
        "field": "Award Date",
        "apply_filter": apply_date_range_filter,
    },
    "area": {
        "label": "Region and country",
        "type": "multidropdown",
        "defaults": [{"label": "All areas", "value": "__all"}],
        "get_values": (
            lambda df: [
                {
                    "label": (
                        "{} ({})".format(value[0], count)
                        if value[0].strip() == value[1].strip()
                        or value[1] is None
                        or value[1] == "Unknown"
                        else "{} - {} ({})".format(value[0], value[1], count)
                    ),
                    "value": "{}##{}".format(value[0], value[1]),
                }
                for value, count in get_ctry_rgn(df)["Grants"].iteritems()
            ]
        ),
        "apply_filter": apply_area_filter,
    },
    "orgtype": {
        "label": "Organisation type",
        "type": "multidropdown",
        "defaults": [{"label": "All organisation types", "value": "__all"}],
        "get_values": (
            lambda df: [
                {"label": "{} ({})".format(i[0], i[1]), "value": i[0]}
                for i in get_identifier_schemes(df).value_counts().iteritems()
            ]
        ),
        "field": "__org_org_type",
        "apply_filter": apply_org_type_filter,
    },
    "award_amount": {
        "label": "Amount awarded",
        "type": "multidropdown",
        "defaults": [{"label": "All amounts", "value": "__all"}],
        "get_values": (
            lambda df: [
                {
                    "label": "{} ({})".format(AWARD_BAND_CHANGES.get(i[0], i[0]), i[1]),
                    "value": i[0],
                }
                for i in df["Amount Awarded:Bands"]
                .value_counts()
                .sort_index()
                .iteritems()
            ]
        ),
        "field": "Amount Awarded:Bands",
        "apply_filter": apply_field_filter,
    },
    "org_size": {
        "label": "Organisation size",
        "type": "multidropdown",
        "defaults": [{"label": "All sizes", "value": "__all"}],
        "get_values": (
            lambda df: [
                {
                    "label": "{} ({})".format(
                        INCOME_BAND_CHANGES.get(i[0], i[0]), i[1]
                    ),
                    "value": i[0],
                }
                for i in get_org_income(df).iteritems()
            ]
            if get_org_income(df).sum()
            else []
        ),
        "field": "__org_latest_income_bands",
        "apply_filter": apply_org_size_filter,
    },
    "org_age": {
        "label": "Organisation age",
        "type": "multidropdown",
        "defaults": [{"label": "All ages", "value": "__all"}],
        "get_values": (
            lambda df: [
                {
                    "label": "{} ({})".format(AGE_BAND_CHANGES.get(i[0], i[0]), i[1]),
                    "value": i[0],
                }
                for i in df["__org_age_bands"].value_counts().sort_index().iteritems()
            ]
            if "__org_age_bands" in df and df["__org_age_bands"].value_counts().sum()
            else []
        ),
        "field": "__org_age_bands",
        "apply_filter": apply_field_filter,
    },
}
