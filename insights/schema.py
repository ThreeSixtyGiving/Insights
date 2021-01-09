import logging
from decimal import Decimal
from timeit import default_timer

import graphene
from graphene import relay
from graphene.utils.str_converters import to_camel_case, to_snake_case
from graphene_sqlalchemy import SQLAlchemyConnectionField, SQLAlchemyObjectType
from graphql.language.ast import Field, FragmentSpread
from sqlalchemy import String, cast, distinct, func, or_

from insights.db import Distribution as DistributionModel
from insights.db import GeoName
from insights.db import Grant as GrantModel
from insights.db import Publisher as PublisherModel
from insights.db import SourceFile as SourceFileModel
from insights.db import db


class Grant(SQLAlchemyObjectType):
    class Meta:
        model = GrantModel


class SourceFile(SQLAlchemyObjectType):
    class Meta:
        model = SourceFileModel


class Publisher(SQLAlchemyObjectType):
    class Meta:
        model = PublisherModel


class Distribution(SQLAlchemyObjectType):
    class Meta:
        model = DistributionModel
        exclude_fields = ("id", "source_file_id", "source_file")


class GrantCurrencyBucket(graphene.ObjectType):
    currency = graphene.String()
    total = graphene.Float()
    median = graphene.Float()
    mean = graphene.Float()
    grants = graphene.Float()
    recipients = graphene.Float()
    min_grant = graphene.Float()
    max_grant = graphene.Float()


class GrantBucketGroup(graphene.ObjectType):
    id = graphene.String()
    name = graphene.String()


class GrantBucket(graphene.ObjectType):
    bucket_group = graphene.List(GrantBucketGroup)
    grants = graphene.Int()
    recipients = graphene.Int()
    funders = graphene.Int()
    currencies = graphene.List(GrantCurrencyBucket)
    max_date = graphene.Date()
    min_date = graphene.Date()
    status = graphene.String()


class GrantAggregate(graphene.ObjectType):
    by_funder = graphene.List(GrantBucket, description="Group by the funder")
    by_funder_type = graphene.List(
        GrantBucket, description="Group by the type of funder"
    )
    by_grant_programme = graphene.List(GrantBucket)
    by_award_year = graphene.List(GrantBucket)
    by_award_date = graphene.List(GrantBucket)
    by_org_type = graphene.List(GrantBucket)
    by_org_size = graphene.List(GrantBucket)
    by_org_age = graphene.List(GrantBucket)
    by_source = graphene.List(GrantBucket)
    by_publisher = graphene.List(GrantBucket)
    by_amount_awarded = graphene.List(GrantBucket)
    by_country_region = graphene.List(GrantBucket)
    by_local_authority = graphene.List(GrantBucket)
    by_geo_source = graphene.List(GrantBucket)
    summary = graphene.List(GrantBucket)


class MaxMin(graphene.InputObjectType):
    max = graphene.Int()
    min = graphene.Int()


class MaxMinDate(graphene.InputObjectType):
    max = graphene.Date()
    min = graphene.Date()


grant_query_args = dict(
    dataset=graphene.Argument(type=graphene.String, required=True),
    q=graphene.Argument(
        type=graphene.String,
        description="Search in the title and description of grant",
    ),
    funders=graphene.Argument(type=graphene.List(graphene.String)),
    files=graphene.Argument(type=graphene.List(graphene.String)),
    publishers=graphene.Argument(type=graphene.List(graphene.String)),
    funder_types=graphene.Argument(type=graphene.List(graphene.String)),
    grant_programmes=graphene.Argument(type=graphene.List(graphene.String)),
    award_dates=graphene.Argument(type=MaxMinDate),
    award_amount=graphene.Argument(type=MaxMin),
    area=graphene.Argument(type=graphene.List(graphene.String)),
    orgtype=graphene.Argument(type=graphene.List(graphene.String)),
    org_size=graphene.Argument(type=MaxMin),
    org_age=graphene.Argument(type=MaxMin),
)


class Query(graphene.ObjectType):
    grant_aggregates = graphene.Field(GrantAggregate, **grant_query_args)
    grants = graphene.List(
        Grant,
        ids=graphene.Argument(type=graphene.List(graphene.String), required=False),
        **grant_query_args,
    )
    source_files = graphene.List(
        SourceFile,
        ids=graphene.Argument(type=graphene.List(graphene.String), required=True),
    )
    publishers = graphene.List(
        Publisher,
        ids=graphene.Argument(type=graphene.List(graphene.String), required=True),
    )
    grant = graphene.Field(
        Grant,
        id=graphene.Argument(type=graphene.String, required=True),
    )
    source_file = graphene.Field(
        SourceFile,
        id=graphene.Argument(type=graphene.String, required=True),
    )
    publisher = graphene.Field(
        Publisher,
        id=graphene.Argument(type=graphene.String, required=True),
    )

    def resolve_grant(self, info, id):
        query = Grant.get_query(info)
        return query.filter(GrantModel.grant_id == id).first()

    def resolve_source_file(self, info, id):
        query = SourceFile.get_query(info)
        return query.filter(SourceFileModel.id == id).first()

    def resolve_publisher(self, info, id):
        query = Publisher.get_query(info)
        return query.filter(PublisherModel.prefix == id).first()

    def resolve_grants(self, info, ids=None, page=0, size=1000, **kwargs):
        limit = (page + 1) * size
        offset = limit - size

        query = Grant.get_query(info)
        if ids:
            query = query.filter(GrantModel.grant_id.in_(ids))
        else:
            query = get_grants_base_query(query, **kwargs)

        return query.offset(offset).limit(limit).all()

    def resolve_source_files(self, info, ids):
        query = SourceFile.get_query(info)
        return query.filter(SourceFileModel.id.in_(ids)).all()

    def resolve_publishers(self, info, ids):
        query = Publisher.get_query(info)
        return query.filter(PublisherModel.prefix.in_(ids)).all()

    def resolve_grant_aggregates(self, info, **kwargs):
        query = get_grants_base_query(db.session.query(), **kwargs)

        geo_labels = {g.id: g.name for g in GeoName.query.all()}

        group_bys = {
            "by_funder": [
                [GrantModel.fundingOrganization_id, GrantModel.fundingOrganization_name]
            ],
            "by_funder_type": [GrantModel.insights_funding_org_type],
            "by_grant_programme": [GrantModel.grantProgramme_title],
            "by_award_date": [func.substr(cast(GrantModel.awardDate, String()), 0, 8)],
            "by_org_type": [GrantModel.insights_org_type],
            "by_org_size": [GrantModel.insights_band_income],
            "by_org_age": [GrantModel.insights_band_age],
            "by_amount_awarded": [GrantModel.currency, GrantModel.insights_band_amount],
            "by_source": [GrantModel.source_file_id],
            "by_publisher": [GrantModel.publisher_id],
            "by_country_region": [
                GrantModel.insights_geo_country,
                GrantModel.insights_geo_region,
            ],
            "by_local_authority": [GrantModel.insights_geo_la],
            "by_geo_source": [GrantModel.insights_geo_source],
            "summary": [],
        }
        return_result = {}

        operations = get_graphql_operations(info)

        for k, fields in group_bys.items():

            # skip the query if it hasn't been requested
            if k not in operations:
                continue

            labels = ["bucket_1_id", "bucket_2_id"]
            new_cols = []
            groupbys = []
            for i, v in enumerate(fields):
                if isinstance(v, list):
                    new_cols.append(v[0].label("bucket_{}_id".format(i + 1)))
                    new_cols.append(v[1].label("bucket_{}_name".format(i + 1)))
                    groupbys.append("bucket_{}_id".format(i + 1))
                    groupbys.append("bucket_{}_name".format(i + 1))
                else:
                    new_cols.append(v.label("bucket_{}_id".format(i + 1)))
                    groupbys.append("bucket_{}_id".format(i + 1))

            agg_cols = []
            if "grants" in operations[k] or "bucket" in operations[k]:
                agg_cols.append(func.count(GrantModel.id).label("grants"))
            if "recipients" in operations[k] or "bucket" in operations[k]:
                agg_cols.append(
                    func.count(distinct(GrantModel.insights_org_id)).label("recipients")
                )
            if "funders" in operations[k] or "bucket" in operations[k]:
                agg_cols.append(
                    func.count(distinct(GrantModel.fundingOrganization_id)).label(
                        "funders"
                    )
                )
            if "max_date" in operations[k]:
                agg_cols.append(func.max(GrantModel.awardDate).label("max_date"))
            if "min_date" in operations[k]:
                agg_cols.append(func.min(GrantModel.awardDate).label("min_date"))

            money_cols = []
            if "currencies" in operations[k] or "bucket" in operations[k]:
                money_cols.extend(
                    [
                        func.sum(GrantModel.amountAwarded).label("total"),
                        func.avg(GrantModel.amountAwarded).label("mean"),
                        func.max(GrantModel.amountAwarded).label("max_grant"),
                        func.min(GrantModel.amountAwarded).label("min_grant"),
                    ]
                )

            currency_col = [GrantModel.currency] if money_cols else []

            query_start_time = default_timer()
            result = query.add_columns(*(new_cols + agg_cols)).group_by(*groupbys).all()
            return_result[k] = [
                {
                    l: float(v) if isinstance(v, Decimal) else v
                    for l, v in r._asdict().items()
                }
                for r in result
            ]

            for r in return_result[k]:
                r["bucket_group"] = []
                if "bucket_1_id" in r:
                    r["bucket_group"].append(
                        {
                            "id": r["bucket_1_id"],
                            "name": r.get("bucket_1_name", r["bucket_1_id"]),
                        }
                    )
                if "bucket_2_id" in r:
                    r["bucket_group"].append(
                        {
                            "id": r["bucket_2_id"],
                            "name": r.get("bucket_2_name", r["bucket_2_id"]),
                        }
                    )

                if k in ("by_country_region", "by_local_authority"):
                    for b in r["bucket_group"]:
                        b["name"] = geo_labels.get(b["id"], b["id"])

                if k in ("by_geo_source"):
                    for b in r["bucket_group"]:
                        if not b["id"]:
                            continue
                        b["name"] = ''.join(map(lambda x: x if x.islower() else " "+x, b["id"])).capitalize()

            if k == "by_country_region":
                return_result[k] = sorted(
                    return_result[k],
                    key=lambda r: (
                        r["bucket_group"][0]["id"] or "",
                        r["bucket_group"][1]["id"] or "",
                    ),
                )

            if currency_col:
                currency_result = (
                    query.add_columns(
                        *(new_cols + currency_col + agg_cols + money_cols)
                    )
                    .group_by(*(groupbys + currency_col))
                    .all()
                )
                for l in return_result[k]:
                    for c in money_cols:
                        l["currencies"] = []
                    for r in currency_result:
                        r = r._asdict()
                        if (
                            l.get("bucket_1_id") == r.get("bucket_1_id")
                            and l.get("bucket_2_id") == r.get("bucket_2_id")
                            and l.get("bucket_1_name") == r.get("bucket_1_name")
                            and l.get("bucket_2_name") == r.get("bucket_2_name")
                        ):
                            cur = {"currency": r.get("currency")}
                            if "grants" in operations[k] or "bucket" in operations[k]:
                                cur["grants"] = r.get("grants")
                            if (
                                "recipients" in operations[k]
                                or "bucket" in operations[k]
                            ):
                                cur["recipients"] = r.get("recipients")
                            for c in money_cols:
                                v = r.get(c._label)
                                cur[c._label] = (
                                    float(v) if isinstance(v, Decimal) else v
                                )
                            l["currencies"].append(cur)
            logging.info(
                "{} query took {:,.4f} seconds".format(
                    k, (default_timer() - query_start_time)
                )
            )

        return return_result


schema = graphene.Schema(query=Query, types=[Grant])


def get_grants_base_query(query, **kwargs):
    query = query.filter(GrantModel.dataset == kwargs.get("dataset"))

    if kwargs.get("q"):
        q = f'%{kwargs.get("q")}%'
        query = query.filter(
            or_(
                GrantModel.title.like(q),
                GrantModel.description.like(q),
            )
        )
    if kwargs.get("funders"):
        query = query.filter(
            or_(
                GrantModel.fundingOrganization_id.in_(kwargs.get("funders")),
                GrantModel.fundingOrganization_name.in_(kwargs.get("funders")),
            )
        )
    if kwargs.get("files"):
        query = query.filter(GrantModel.source_file_id.in_(kwargs.get("files")))
    if kwargs.get("publishers"):
        query = query.filter(GrantModel.publisher_id.in_(kwargs.get("publishers")))
    if kwargs.get("funder_types"):
        query = query.filter(
            GrantModel.insights_funding_org_type.in_(kwargs.get("funder_types")),
        )
    if kwargs.get("grant_programmes"):
        query = query.filter(
            GrantModel.grantProgramme_title.in_(kwargs.get("grant_programmes")),
        )
    if kwargs.get("award_dates", {}).get("min"):
        query = query.filter(
            GrantModel.awardDate >= kwargs.get("award_dates", {}).get("min"),
        )
    if kwargs.get("award_dates", {}).get("max"):
        query = query.filter(
            GrantModel.awardDate <= kwargs.get("award_dates", {}).get("max"),
        )
    if kwargs.get("award_amount", {}).get("min"):
        query = query.filter(
            GrantModel.amountAwarded >= kwargs.get("award_amount", {}).get("min"),
        )
    if kwargs.get("award_amount", {}).get("max"):
        query = query.filter(
            GrantModel.amountAwarded <= kwargs.get("award_amount", {}).get("max"),
        )

    if kwargs.get("area"):
        query = query.filter(
            or_(
                GrantModel.insights_geo_region.in_(kwargs.get("area")),
                GrantModel.insights_geo_la.in_(kwargs.get("area")),
                GrantModel.insights_geo_country.in_(kwargs.get("area")),
            )
        )
    if kwargs.get("orgtype"):
        query = query.filter(
            GrantModel.insights_org_type.in_(kwargs.get("orgtype")),
        )
    if kwargs.get("org_size", {}).get("min"):
        query = query.filter(
            GrantModel.insights_org_latest_income
            >= kwargs.get("org_size", {}).get("min"),
        )
    if kwargs.get("org_size", {}).get("max"):
        query = query.filter(
            GrantModel.insights_org_latest_income
            <= kwargs.get("org_size", {}).get("max"),
        )
    # if kwargs.get("org_age", {}).get("min"):
    #     query = query.filter(
    #         GrantModel.recipientOrganization_ageAtGrant >= kwargs.get(
    #             "org_age", {}).get("min"),
    #     )
    # if kwargs.get("org_age", {}).get("max"):
    #     query = query.filter(
    #         GrantModel.recipientOrganization_ageAtGrant <= kwargs.get(
    #             "org_age", {}).get("max"),
    #     )
    return query


def get_graphql_operations(info):
    # get the names of the operations so we can only perform those that are requested
    operations = {}

    # first level is the type of the query
    for query in info.operation.selection_set.selections:

        # if we're not doing a grants query then try the next one
        if query.name.value != "grantAggregates":
            continue

        # next level is the individual aggregate queries
        for agg in query.selection_set.selections:
            if hasattr(agg.selection_set, "selections"):
                selections = []

                # finally we get to the fields
                for y in agg.selection_set.selections:
                    if isinstance(y, Field):
                        selections.append(to_snake_case(y.name.value))

                    # fragments need to be expanded
                    elif isinstance(y, FragmentSpread):
                        selections.extend(
                            [
                                to_snake_case(f.name.value)
                                for f in info.fragments[
                                    y.name.value
                                ].selection_set.selections
                            ]
                        )
                operations[to_snake_case(agg.name.value)] = selections

    return operations
