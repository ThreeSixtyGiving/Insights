import datetime

from sqlalchemy import func
from sqlalchemy.dialects import postgresql

from ..db import db


class ModelWithUpsert:

    @classmethod
    def upsert_statement(cls):
        insert_statement = postgresql.insert(cls.__table__)
        return insert_statement.on_conflict_do_update(
            constraint=cls.__table__.primary_key,
            set_={
                c.name: insert_statement.excluded.get(c.name)
                for c in cls.__table__.columns
            }
        )

    def as_json(self):

        def convert_date(value):
            if isinstance(value, (datetime.date, datetime.datetime)):
                return str(value)
            return value

        return {
            c.name: convert_date(getattr(self, c.name)) for c in self.__table__.columns
        }


class Organisation(db.Model, ModelWithUpsert):
    orgid = db.Column(db.String, primary_key=True)
    charity_number = db.Column(db.String, index=True)
    company_number = db.Column(db.String, index=True)
    date_registered = db.Column(db.Date)
    date_removed = db.Column(db.Date)
    postcode = db.Column(db.String)
    latest_income = db.Column(db.BigInteger)
    latest_income_date = db.Column(db.Date)
    org_type = db.Column(db.String, index=True)
    source = db.Column(db.String)
    last_updated = db.Column(db.DateTime, onupdate=func.utc_timestamp())

    def __repr__(self):
        return '<Organisation {}>'.format(self.orgid)


class Grant(db.Model, ModelWithUpsert):
    dataset = db.Column(db.String, primary_key=True)
    id = db.Column(db.String, primary_key=True)
    title = db.Column(db.String)
    description = db.Column(db.String)
    currency = db.Column(db.String, index=True)
    amountAwarded = db.Column(db.BigInteger, index=True)
    amountAwardedBand = db.Column(db.String, index=True)
    awardDate = db.Column(db.Date, index=True)
    awardDateYear = db.Column(db.Integer, index=True)
    plannedDates_startDate = db.Column(db.Date)
    plannedDates_endDate = db.Column(db.Date)
    plannedDates_duration = db.Column(db.Integer)
    plannedDates_durationBand = db.Column(db.String, index=True)
    recipientOrganization_id = db.Column(db.String, index=True)
    recipientOrganization_idScheme = db.Column(db.String, index=True)
    recipientOrganization_idCanonical = db.Column(db.String, index=True)
    recipientOrganization_name = db.Column(db.String)
    recipientOrganization_charityNumber = db.Column(db.String)
    recipientOrganization_companyNumber = db.Column(db.String)
    recipientOrganization_postalCode = db.Column(db.String, index=True)
    recipientOrganization_postalCodeCanonical = db.Column(db.String, index=True)
    recipientOrganization_latestIncome = db.Column(db.BigInteger)
    recipientOrganization_latestIncomeDate = db.Column(db.Date)
    recipientOrganization_latestIncomeBand = db.Column(db.String, index=True)
    recipientOrganization_registrationDate = db.Column(db.Date)
    recipientOrganization_ageAtGrant = db.Column(db.Integer)
    recipientOrganization_ageAtGrantBands = db.Column(db.String, index=True)
    recipientOrganization_organisationType = db.Column(db.String, index=True)
    fundingOrganization_id = db.Column(db.String, index=True)
    fundingOrganization_name = db.Column(db.String, index=True)
    fundingOrganization_type = db.Column(db.String, index=True)
    fundingOrganization_department = db.Column(db.String)
    grantProgramme_title = db.Column(db.String, index=True)
    geoCtry = db.Column(db.String, index=True)
    geoCty = db.Column(db.String, index=True)
    geoLaua = db.Column(db.String)
    geoPcon = db.Column(db.String)
    geoRgn = db.Column(db.String)
    geoImd = db.Column(db.Integer)
    geoImdBand = db.Column(db.String, index=True)
    geoRu11ind = db.Column(db.String)
    geoOac11 = db.Column(db.String)
    geoLat = db.Column(db.Float)
    geoLong = db.Column(db.Float)
    last_updated = db.Column(db.DateTime, onupdate=func.utc_timestamp())

    def __repr__(self):
        return '<Grant {} [from {}]>'.format(self.id, self.dataset)


class Postcode(db.Model, ModelWithUpsert):
    id = db.Column(db.String, primary_key=True)
    ctry = db.Column(db.String)
    cty = db.Column(db.String)
    laua = db.Column(db.String)
    pcon = db.Column(db.String)
    rgn = db.Column(db.String)
    imd = db.Column(db.Integer)
    ru11ind = db.Column(db.String)
    oac11 = db.Column(db.String)
    lat = db.Column(db.Float)
    long = db.Column(db.Float)
    last_updated = db.Column(db.DateTime, onupdate=func.utc_timestamp())

    def __repr__(self):
        return '<Postcode {}>'.format(self.id)
