from sqlalchemy import func
from sqlalchemy.dialects import postgresql

from ..db import db

class Organisation(db.Model):
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
