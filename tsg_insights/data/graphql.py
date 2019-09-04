from decimal import Decimal

import graphene
from graphene_sqlalchemy import SQLAlchemyObjectType
from graphene.utils.str_converters import to_camel_case, to_snake_case
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
    by_grant_programme = graphene.List(GrantBucket)
    # by_amount_awarded = graphene.List(GrantBucket)
    by_award_year = graphene.List(GrantBucket)
    by_award_date = graphene.List(GrantBucket)


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

        group_bys = {
            "by_funder": [GrantModel.fundingOrganization_id, GrantModel.fundingOrganization_name],
            "by_grant_programme": [GrantModel.grantProgramme_title, GrantModel.grantProgramme_title],
            "by_award_year": [GrantModel.awardDateYear, GrantModel.awardDateYear],
            "by_award_date": [GrantModel.awardDate, GrantModel.awardDate],
        }
        return_result = {}

        # get the names of the operations so we can only perform those that are requested
        operations = []
        for s in info.operation.selection_set.selections:
            if s.name.value != 'grants':
                continue
            operations.extend([x.name.value for x in s.selection_set.selections])
        
        for k, fields in group_bys.items():

            # skip the query if it hasn't been requested
            if k not in operations and to_camel_case(k) not in operations:
                continue

            result = query.add_columns(
                fields[0].label("bucket_id"),
                fields[1].label("bucket_name"),
                func.count(GrantModel.id).label("grants"),
                func.sum(GrantModel.amountAwarded).label("grant_amount")
            ).group_by(*fields).all()
            return_result[k]= [{
                k: float(v) if isinstance(v, Decimal) else v
                for k, v in r._asdict().items()} for r in result]

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
