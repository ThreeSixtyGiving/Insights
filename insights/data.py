from flask import url_for
from sqlalchemy import func

from insights.db import GeoName, Grant, Publisher
from insights.settings import DEFAULT_DATASET


def get_frontpage_options(dataset=DEFAULT_DATASET, with_url=True):

    publishers = Publisher.query.all()
    publisher_counts = get_field_counts(Grant.publisher_id)

    funder_types = get_field_counts(Grant.insights_funding_org_type, dataset=dataset)
    funders = get_field_counts(Grant.fundingOrganization_id, dataset=dataset)
    countries = get_field_counts(Grant.insights_geo_country, dataset=dataset)
    regions = get_field_counts(Grant.insights_geo_region, dataset=dataset)
    local_authorities = get_field_counts(Grant.insights_geo_la, dataset=dataset)

    area_names = {g.id: g.name for g in GeoName.query.all()}
    funder_names = get_funder_names(dataset=dataset)
    all_grants = get_field_counts(Grant.dataset, dataset=dataset)

    return dict(
        publishers=sorted(
            [
                {
                    "id": p.prefix,
                    "name": p.name,
                    "url": url_for("data", data_type="publisher", data_id=p.prefix) if with_url else None,
                    **publisher_counts.get(p.prefix, {"grant_count": 0}),
                }
                for p in publishers
            ],
            key=lambda x: -x["grant_count"],
        ),
        funder_types=[
            {
                "id": "all",
                "name": "All grants",
                "url": url_for("data") if with_url else None,
                **all_grants[dataset],
            }
        ]
        + sorted(
            [
                {
                    "id": k,
                    "name": k,
                    "url": url_for("data", data_type="funder_type", data_id=k) if with_url else None,
                    **v,
                }
                for k, v in funder_types.items()
            ],
            key=lambda x: -x["grant_count"],
        ),
        funders=sorted(
            [
                {
                    "id": k,
                    "name": funder_names.get(k, k),
                    "url": url_for("data", data_type="funder", data_id=k) if with_url else None,
                    **v,
                }
                for k, v in funders.items()
            ],
            key=lambda x: -x["grant_count"],
        ),
        countries=sorted(
            [
                {
                    "id": k,
                    "name": area_names.get(k, k),
                    "url": url_for("data", data_type="area", data_id=k) if with_url else None,
                    **v,
                }
                for k, v in countries.items()
            ],
            key=lambda x: -x["grant_count"],
        ),
        regions=sorted(
            [
                {
                    "id": k,
                    "name": area_names.get(k, k),
                    "url": url_for("data", data_type="area", data_id=k) if with_url else None,
                    **v,
                }
                for k, v in regions.items()
            ],
            key=lambda x: -x["grant_count"],
        ),
        local_authorities=sorted(
            [
                {
                    "id": k,
                    "name": area_names.get(k, k),
                    "url": url_for("data", data_type="area", data_id=k) if with_url else None,
                    **v,
                }
                for k, v in local_authorities.items()
            ],
            key=lambda x: -x["grant_count"],
        ),
    )


def get_funder_names(dataset=DEFAULT_DATASET):
    funder_names = (
        Grant.query.filter(Grant.dataset == dataset)
        .with_entities(
            Grant.fundingOrganization_id,
            Grant.fundingOrganization_name,
            func.max(Grant.awardDate).label("max_date"),
        )
        .group_by(
            Grant.fundingOrganization_id,
            Grant.fundingOrganization_name,
        )
        .all()
    )
    funders = set([f[0] for f in funder_names])
    return {
        f: sorted([v for v in funder_names if v[0] == f], key=lambda x: x[2])[-1][1]
        for f in funders
    }


def get_field_counts(field, dataset=DEFAULT_DATASET):
    counts = (
        Grant.query.filter(Grant.dataset == dataset)
        .with_entities(
            field,
            func.count(Grant.id).label("grant_count"),
            func.max(Grant.awardDate).label("max_date"),
            func.min(Grant.awardDate).label("min_date"),
        )
        .group_by(field)
        .all()
    )
    return {
        p[0]: {
            "grant_count": p[1],
            "max_date": p[2],
            "min_date": p[3],
        }
        for p in counts
        if p[0]
    }
