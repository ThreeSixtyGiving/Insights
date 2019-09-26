from decimal import Decimal
import logging
from timeit import default_timer

import graphene
from graphene_sqlalchemy import SQLAlchemyObjectType
from graphene.utils.str_converters import to_camel_case, to_snake_case
from sqlalchemy import or_, func, distinct
from flask_sqlalchemy_caching import FromCache

from ..data.models import Grant as GrantModel, Organisation as OrganisationModel, Postcode as PostcodeModel
from ..db import db, cache


class Grant(SQLAlchemyObjectType):
    class Meta:
        model = GrantModel


class GrantCurrencyBucket(graphene.ObjectType):
    currency = graphene.String()
    value = graphene.Float()

class GrantBucket(graphene.ObjectType):
    bucket_id = graphene.String()
    bucket_2_id = graphene.String()
    grants = graphene.Int()
    recipients = graphene.Int()
    funders = graphene.Int()
    grant_amount = graphene.List(GrantCurrencyBucket)
    mean_grant = graphene.List(GrantCurrencyBucket)
    max_grant = graphene.List(GrantCurrencyBucket)
    min_grant = graphene.List(GrantCurrencyBucket)
    max_date = graphene.Date()
    min_date = graphene.Date()



class GrantAggregate(graphene.ObjectType):
    by_funder = graphene.List(GrantBucket, description='Group by the funder')
    by_funder_type = graphene.List(GrantBucket, description='Group by the type of funder')
    by_grant_programme = graphene.List(GrantBucket)
    by_award_year = graphene.List(GrantBucket)
    by_award_date = graphene.List(GrantBucket)
    by_org_type = graphene.List(GrantBucket)
    by_org_size = graphene.List(GrantBucket)
    by_org_age = graphene.List(GrantBucket)
    by_amount_awarded = graphene.List(GrantBucket)
    by_country_region = graphene.List(GrantBucket)
    by_local_authority = graphene.List(GrantBucket)
    summary = graphene.List(GrantBucket)


class Organisation(SQLAlchemyObjectType):
    class Meta:
        model = OrganisationModel


class Postcode(SQLAlchemyObjectType):
    class Meta:
        model = PostcodeModel


class MaxMin(graphene.InputObjectType):
    max = graphene.Int()
    min = graphene.Int()

class Query(graphene.ObjectType):
    grants = graphene.Field(
        GrantAggregate,
        dataset=graphene.Argument(type=graphene.String, required=True),
        q=graphene.Argument(type=graphene.String, description='Search in the title and description of grant'),
        funders=graphene.Argument(type=graphene.List(graphene.String)),
        funder_types=graphene.Argument(type=graphene.List(graphene.String)),
        grant_programmes=graphene.Argument(type=graphene.List(graphene.String)),
        award_dates=graphene.Argument(type=MaxMin),
        award_amount=graphene.Argument(type=MaxMin),
        area=graphene.Argument(type=graphene.List(graphene.String)),
        orgtype=graphene.Argument(type=graphene.List(graphene.String)),
        org_size=graphene.Argument(type=MaxMin),
        org_age=graphene.Argument(type=MaxMin),
    )
    grant = graphene.Field(
        Grant,
        id=graphene.Argument(type=graphene.String, required=True),
    )

    def resolve_grant(self, info, id):
        query = Grant.get_query(info)
        return query.filter(GrantModel.id == id).first()

    def resolve_grants(self, info, dataset, **kwargs):

        # query = Grant.get_query(info)
        query = db.session.query().options(FromCache(cache)).filter(GrantModel.dataset == dataset)
        
        if kwargs.get("q"):
            q = f'%{kwargs.get("q")}%'
            query = query.filter(or_(
                GrantModel.title.like(q),
                GrantModel.description.like(q),
            ))
        if kwargs.get("funders"):
            query = query.filter(or_(
                GrantModel.fundingOrganization_id.in_(kwargs.get("funders")),
                GrantModel.fundingOrganization_name.in_(kwargs.get("funders")),
            ))
        if kwargs.get("funder_types"):
            query = query.filter(
                GrantModel.fundingOrganization_type.in_(
                    kwargs.get("funder_types")),
            )
        if kwargs.get("grant_programmes"):
            query = query.filter(
                GrantModel.grantProgramme_title.in_(
                    kwargs.get("grant_programmes")),
            )
        if kwargs.get("award_dates", {}).get("min"):
            query = query.filter(
                GrantModel.awardDateYear >= kwargs.get(
                    "award_dates", {}).get("min"),
            )
        if kwargs.get("award_dates", {}).get("max"):
            query = query.filter(
                GrantModel.awardDateYear <= kwargs.get(
                    "award_dates", {}).get("max"),
            )
        if kwargs.get("award_amount", {}).get("min"):
            query = query.filter(
                GrantModel.amountAwarded >= kwargs.get(
                    "award_amount", {}).get("min"),
            )
        if kwargs.get("award_amount", {}).get("max"):
            query = query.filter(
                GrantModel.amountAwarded <= kwargs.get(
                    "award_amount", {}).get("max"),
            )
        
        if kwargs.get("area"):
            query = query.filter(or_(
                GrantModel.geoCtry.in_(kwargs.get("area")),
                GrantModel.geoRgn.in_(kwargs.get("area")),
            ))
        if kwargs.get("orgtype"):
            query = query.filter(
                GrantModel.recipientOrganization_organisationType.in_(
                    kwargs.get("orgtype")),
            )
        if kwargs.get("org_size", {}).get("min"):
            query = query.filter(
                GrantModel.recipientOrganization_latestIncome >= kwargs.get(
                    "org_size", {}).get("min"),
            )
        if kwargs.get("org_size", {}).get("max"):
            query = query.filter(
                GrantModel.recipientOrganization_latestIncome <= kwargs.get(
                    "org_size", {}).get("mac"),
            )
        if kwargs.get("org_age", {}).get("min"):
            query = query.filter(
                GrantModel.recipientOrganization_ageAtGrant >= kwargs.get(
                    "org_age", {}).get("min"),
            )
        if kwargs.get("org_age", {}).get("max"):
            query = query.filter(
                GrantModel.recipientOrganization_ageAtGrant <= kwargs.get(
                    "org_age", {}).get("max"),
            )

        group_bys = {
            "by_funder": [GrantModel.fundingOrganization_id, GrantModel.fundingOrganization_name],
            "by_funder_type": [GrantModel.fundingOrganization_type],
            "by_grant_programme": [GrantModel.grantProgramme_title],
            "by_award_year": [GrantModel.awardDateYear],
            "by_award_date": [func.to_char(GrantModel.awardDate, 'yyyy-mm-01')],
            "by_org_type": [GrantModel.recipientOrganization_organisationType],
            "by_org_size": [GrantModel.recipientOrganization_latestIncomeBand],
            "by_org_age": [GrantModel.recipientOrganization_ageAtGrantBands],
            "by_amount_awarded": [GrantModel.currency, GrantModel.amountAwardedBand],
            "by_country_region": [GrantModel.geoCtry, GrantModel.geoRgn],
            "by_local_authority": [GrantModel.geoLaua],
            "summary": [],
        }
        return_result = {}

        # get the names of the operations so we can only perform those that are requested
        operations = {}
        for s in info.operation.selection_set.selections:
            if s.name.value != 'grants':
                continue

            for x in s.selection_set.selections:
                if hasattr(x.selection_set, 'selections'):
                    operations[to_snake_case(x.name.value)] = [
                        to_snake_case(y.name.value) for y in x.selection_set.selections]
        
        for k, fields in group_bys.items():

            # skip the query if it hasn't been requested
            if k not in operations:
                continue

            labels = ['bucket_id', 'bucket_2_id']
            new_cols = [v.label(labels[k]) for k, v in enumerate(fields)]

            agg_cols = []
            if "grants" in operations[k] or "bucket" in operations[k]:
                agg_cols.append(func.count(GrantModel.id).label("grants"))
            if "recipients" in operations[k] or "bucket" in operations[k]:
                agg_cols.append(
                    func.count(distinct(GrantModel.recipientOrganization_idCanonical)).label("recipients")
                )
            if "funders" in operations[k] or "bucket" in operations[k]:
                agg_cols.append(
                    func.count(distinct(GrantModel.fundingOrganization_id)).label("funders")
                )
            if "max_date" in operations[k]:
                agg_cols.append(
                    func.max(GrantModel.awardDate).label("max_date")
                )
            if "min_date" in operations[k]:
                agg_cols.append(
                    func.min(GrantModel.awardDate).label("min_date")
                )
            
            money_cols = []
            if "grant_amount" in operations[k] or "bucket" in operations[k]:
                money_cols.append(
                    func.sum(GrantModel.amountAwarded).label("grant_amount"))
            if "mean_grant" in operations[k] or "bucket" in operations[k]:
                money_cols.append(
                    func.avg(GrantModel.amountAwarded).label("mean_grant"))
            if "max_grant" in operations[k] or "bucket" in operations[k]:
                money_cols.append(
                    func.max(GrantModel.amountAwarded).label("max_grant"))
            if "min_grant" in operations[k] or "bucket" in operations[k]:
                money_cols.append(
                    func.min(GrantModel.amountAwarded).label("min_grant"))

            currency_col = [GrantModel.currency] if money_cols else []
            
            query_start_time = default_timer()
            result = query.add_columns(*(new_cols + agg_cols)).group_by(*fields).all()
            return_result[k]= [{
                l: float(v) if isinstance(v, Decimal) else v
                for l, v in r._asdict().items()} for r in result]

            if currency_col:
                currency_result = query.add_columns(
                    *(new_cols + currency_col + money_cols)).group_by(*(fields + currency_col)).all()
                for l in return_result[k]:
                    for c in money_cols:
                        l[c._label] = []
                    for r in currency_result:
                        r = r._asdict()
                        if l.get("bucket_id") == r.get("bucket_id") and l.get("bucket_2_id") == r.get("bucket_2_id"):
                            for c in money_cols:
                                v = r.get(c._label)
                                l[c._label].append({
                                    "currency": r.get("currency"),
                                    "value": float(v) if isinstance(v, Decimal) else v,
                                })
            logging.info('{} query took {:,.4f} seconds'.format(
                k, (default_timer() - query_start_time)))

        return return_result

    organisations = graphene.List(Organisation)
    organisation = graphene.Field(
        Organisation,
        id=graphene.Argument(type=graphene.String, required=True),
    )

    def resolve_organisation(self, info, id):
        query = Organisation.get_query(info)
        return query.filter(OrganisationModel.id == id).first()

    def resolve_organisations(self, info):
        query = Organisation.get_query(info)
        return query.limit(50).all()

    postcodes = graphene.List(Postcode)
    postcode = graphene.Field(
        Postcode,
        postcode=graphene.Argument(type=graphene.String, required=True),
    )

    def resolve_postcode(self, info, postcode):
        query = Postcode.get_query(info)
        return query.filter(PostcodeModel.id == postcode).first()

    def resolve_postcodes(self, info):
        query = Postcode.get_query(info)
        return query.limit(50).all()


schema = graphene.Schema(
    query=Query, types=[Grant, Organisation, Postcode])
