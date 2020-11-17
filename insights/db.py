from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import relationship

from insights import settings

db = SQLAlchemy()
migrate = Migrate()


# https://stackoverflow.com/questions/2546207/does-sqlalchemy-have-an-equivalent-of-djangos-get-or-create
def get_or_create(session, model, **kwargs):
    instance = session.query(model).filter_by(**kwargs).first()
    if instance:
        return instance
    else:
        instance = model(**kwargs)
        session.add(instance)
        session.commit()
        return instance


class Grant(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    dataset = db.Column(
        db.String(255), nullable=False, index=True, default=settings.DEFAULT_DATASET
    )
    grant_id = db.Column(db.String(255), nullable=False)
    title = db.Column(db.String(1000), nullable=False)
    description = db.Column(db.Text, nullable=False)
    currency = db.Column(db.String(3), nullable=False, index=True)
    amountAwarded = db.Column(db.Integer, nullable=False, index=True)
    awardDate = db.Column(db.Date, nullable=False, index=True)
    plannedDates_startDate = db.Column(db.Date, nullable=True)
    plannedDates_endDate = db.Column(db.Date, nullable=True)
    plannedDates_duration = db.Column(db.Integer, nullable=True)
    recipientOrganization_id = db.Column(db.String(255), nullable=False, index=True)
    recipientOrganization_name = db.Column(db.String(1000), nullable=False)
    recipientOrganization_charityNumber = db.Column(db.String(255), nullable=True)
    recipientOrganization_companyNumber = db.Column(db.String(255), nullable=True)
    recipientOrganization_postalCode = db.Column(db.String(255), nullable=True)
    fundingOrganization_id = db.Column(db.String(255), nullable=False, index=True)
    fundingOrganization_name = db.Column(db.String(255), nullable=False)
    fundingOrganization_department = db.Column(db.String(255), nullable=True)
    grantProgramme_title = db.Column(db.String(255), nullable=True, index=True)

    # file link
    source_file_id = db.Column(
        db.String(255), db.ForeignKey("source_file.id"), nullable=True, index=True
    )
    source_file = relationship("SourceFile", back_populates="grants")
    publisher_id = db.Column(
        db.String(255), db.ForeignKey("publisher.prefix"), nullable=True, index=True
    )
    publisher = relationship("Publisher", back_populates="grants")

    # insights specific fields - geography
    insights_geo_region = db.Column(db.String(255), nullable=True, index=True)
    insights_geo_la = db.Column(db.String(255), nullable=True)
    insights_geo_country = db.Column(db.String(255), nullable=True, index=True)
    insights_geo_lat = db.Column(db.Float, nullable=True)
    insights_geo_long = db.Column(db.Float, nullable=True)
    insights_geo_source = db.Column(db.String(255), nullable=True)

    # insights specific fields - organisation
    insights_org_id = db.Column(db.String(255), nullable=True)
    insights_org_registered_date = db.Column(db.Date, nullable=True)
    insights_org_latest_income = db.Column(db.Integer, nullable=True)
    insights_org_type = db.Column(db.String(255), nullable=True, index=True)
    insights_funding_org_type = db.Column(db.String(255), nullable=True, index=True)

    # insights specific fields - bands
    insights_band_age = db.Column(db.String(255), nullable=True, index=True)
    insights_band_income = db.Column(db.String(255), nullable=True, index=True)
    insights_band_amount = db.Column(db.String(255), nullable=True, index=True)

    def __str__(self):
        return "<Grant {}>".format(self.id)


class SourceFile(db.Model):
    id = db.Column(db.String(255), primary_key=True)
    title = db.Column(db.String(255), nullable=True, index=True)
    issued = db.Column(db.Date, nullable=True)
    modified = db.Column(db.DateTime, nullable=True)
    license = db.Column(db.String(255), nullable=True, index=True)
    license_name = db.Column(db.String(255), nullable=True, index=True)
    description = db.Column(db.Text, nullable=True)
    publisher_prefix = db.Column(db.String(255), db.ForeignKey("publisher.prefix"))
    publisher = relationship("Publisher", back_populates="source_files")
    grants = relationship("Grant", back_populates="source_file")
    distribution = relationship("Distribution", back_populates="source_file")


class Distribution(db.Model):
    id = db.Column(db.String(255), primary_key=True)
    title = db.Column(db.String(255), nullable=False, index=True)
    accessURL = db.Column(db.String(255), nullable=True, index=True)
    downloadURL = db.Column(db.String(255), nullable=True, index=True)
    source_file_id = db.Column(
        db.String(255), db.ForeignKey("source_file.id"), nullable=True
    )
    source_file = relationship("SourceFile", back_populates="distribution")


class Publisher(db.Model):
    prefix = db.Column(db.String(255), primary_key=True)
    name = db.Column(db.String(255), nullable=False, index=True)
    website = db.Column(db.String(255), nullable=True, index=True)
    logo = db.Column(db.String(255), nullable=True, index=True)
    source_files = relationship("SourceFile", back_populates="publisher")
    grants = relationship("Grant", back_populates="publisher")


class GeoName(db.Model):
    id = db.Column(db.String(255), primary_key=True)
    name = db.Column(db.String(255), nullable=False, index=True)
    type_ = db.Column(db.String(255), nullable=False, index=True)
