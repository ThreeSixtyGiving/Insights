import os
import logging

from .results import get_identifier_schemes, AGE_BAND_CHANGES, AWARD_BAND_CHANGES, INCOME_BAND_CHANGES, get_ctry_rgn
from tsg_insights.data.cache import get_from_cache
from tsg_insights.data.graphql import schema

with open(os.path.join(os.path.dirname(__file__), 'query.gql')) as gql:
    QUERY_GQL = gql.read()


def get_filtered_df(fileid, **filters):

    gql_filters = dict(dataset=fileid)

    if filters.get("award_dates"):
        gql_filters["awardDates"] = dict(
            min=filters.get("award_dates")[0],
            max=filters.get("award_dates")[1],
        )

    for i in ["funders", "grant_programmes", "area", "orgtype"]:
        if isinstance(filters.get(i), list):
            values = [f for f in filters.get(i) if f != "__all"]
            if values:
                gql_filters[i] = values

    results = schema.execute(QUERY_GQL, variables=gql_filters)
    logging.info(gql_filters)
    return results.data["grants"]

FILTERS = {
    "funders": {
        "label": "Funders",
        "type": "multidropdown",
        "defaults": [{"label": "Funder", "value": "__all"}],
        "get_values": (lambda df: [
            {
                'label': '{} ({})'.format(v["bucket2Id"], v["grants"]),
                'value': v["grants"]
            } for v in sorted(df["byFunder"], key=lambda x: -x['grants'])
        ]),
    },
    "grant_programmes": {
        "label": "Grant programmes",
        "type": "multidropdown",
        "defaults": [{"label": "All grants", "value": "__all"}],
        "get_values": (lambda df: [
            {
                'label': '{} ({})'.format(v["bucketId"], v["grants"]),
                'value': v["grants"]
            } for v in sorted(df["byGrantProgramme"], key=lambda x: -x['grants'])
            if v["bucketId"]
        ]),
    },
    "award_dates": {
        "label": "Date awarded",
        "type": "rangeslider",
        "defaults": {"min": 2015, "max": 2018},
        "get_values": (lambda df: {
            "min": int(df["summary"][0]["minDate"][0:4]),
            "max": int(df["summary"][0]["maxDate"][0:4]),
        }),
    },
    "area": {
        "label": "Region and country",
        "type": "multidropdown",
        "defaults": [{"label": "All areas", "value": "__all"}],
        "get_values": (lambda df: [
            {
                'label': (
                    '{} ({})'.format(v[0][0], v[1])
                    if v[0][0].strip() == v[0][1].strip()
                    else "{} - {} ({})".format(v[0][0], v[0][1], v[1])
                ),
                'value': v[2]
            } for v in get_ctry_rgn(df)
        ]),
    },
    "orgtype": {
        "label": "Organisation type",
        "type": "multidropdown",
        "defaults": [{"label": "All organisation types", "value": "__all"}],
        "get_values": (lambda df: [
            {
                'label': '{} ({})'.format(v["bucketId"], v["grants"]),
                'value': v["grants"]
            } for v in sorted(df["byOrgType"], key=lambda x: -x['grants'])
            if v["bucketId"]
        ]),
    },
    "award_amount": {
        "label": "Amount awarded",
        "type": "multidropdown",
        "defaults": [{"label": "All amounts", "value": "__all"}],
        "get_values": (lambda df: [
            {
                'label': '{} ({})'.format(AWARD_BAND_CHANGES.get(i[0], i[0]), i[1]),
                'value': i[0]
            } for i in df["Amount Awarded:Bands"].value_counts().sort_index().iteritems()
        ]),
    },
    "org_size": {
        "label": "Organisation size",
        "type": "multidropdown",
        "defaults": [{"label": "All sizes", "value": "__all"}],
        "get_values": (lambda df: [] if get_org_income(df).sum() else []),
    },
    "org_age": {
        "label": "Organisation age",
        "type": "multidropdown",
        "defaults": [{"label": "All ages", "value": "__all"}],
        "get_values": (lambda df: [
            {
                'label': '{} ({})'.format(AGE_BAND_CHANGES.get(i[0], i[0]), i[1]),
                'value': i[0]
            } for i in df["__org_age_bands"].value_counts().sort_index().iteritems()
        ] if df["__org_age_bands"].value_counts().sum() else []),
    },
}
