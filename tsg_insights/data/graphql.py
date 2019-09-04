from decimal import Decimal

import graphene
from graphene_sqlalchemy import SQLAlchemyObjectType
from sqlalchemy import or_, func

from ..data.models import Grant as GrantModel, Organisation as OrganisationModel, Postcode as PostcodeModel
from ..db import db


class Grant(SQLAlchemyObjectType):
    class Meta:
        model = GrantModel
        # # only return specified fields
        # only_fields = ("name",)
        # # exclude specified fields
        # exclude_fields = ("last_name",)

class GrantBucket(graphene.ObjectType):
    bucket_id = graphene.String()
    bucket_name = graphene.String()
    grants = graphene.Int()
    grant_amount = graphene.Float()


class GrantAggregate(graphene.ObjectType):
    by_funder = graphene.List(GrantBucket)


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
        grant_programmes=graphene.Argument(
            type=graphene.List(graphene.String)),
        award_dates=graphene.Argument(type=MaxMin),
        award_amount=graphene.Argument(type=MaxMin),
        # Not yet implemented
        # area=graphene.Argument(type=graphene.String),
        # orgtype=graphene.Argument(type=graphene.String),
        # org_size=graphene.Argument(type=MaxMin),
        # org_age=graphene.Argument(type=MaxMin),
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
        query = db.session.query().filter(GrantModel.dataset == dataset)
        
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
        
        # not yet implemented
        # if kwargs.get("area"):
        #     query = query
        # if kwargs.get("orgtype"):
        #     query = query
        # if kwargs.get("org_size", {}).get("min"):
        #     query = query
        # if kwargs.get("org_size", {}).get("max"):
        #     query = query
        # if kwargs.get("org_age", {}).get("min"):
        #     query = query
        # if kwargs.get("org_age", {}).get("max"):
        #     query = query

        result = query.add_columns(
            GrantModel.fundingOrganization_id.label("bucket_id"),
            GrantModel.fundingOrganization_name.label("bucket_name"),
            func.count(GrantModel.id).label("grants"),
            func.sum(GrantModel.amountAwarded).label("grant_amount")
        ).group_by(
            GrantModel.fundingOrganization_id,
            GrantModel.fundingOrganization_name
        ).all()

        x = dict(
            by_funder = [{
                k: float(v) if isinstance(v, Decimal) else v
                for k, v in r._asdict().items()} for r in result]
        )
        print(x)
        return x

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
