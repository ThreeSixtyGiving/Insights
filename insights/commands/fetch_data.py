import datetime
import json

import click
import requests
from flask import current_app
from flask.cli import AppGroup, with_appcontext
from sqlalchemy import create_engine
from sqlalchemy.sql import text

from insights import settings
from insights.data import get_frontpage_options
from insights.db import Distribution, GeoName, Grant, Publisher, SourceFile, db
from insights.utils import get_org_schema, to_band

cli = AppGroup("data")


@cli.command("fetch")
@click.option(
    "--dataset",
    default=settings.DEFAULT_DATASET,
    show_default=True,
    help="Name of dataset",
)
@click.option(
    "--bulk-limit",
    default=settings.BULK_LIMIT,
    show_default=True,
    help="Number of rows to upload at once in bulk",
    type=int,
)
@click.option(
    "--limit",
    default=None,
    show_default=True,
    help="Do only this many rows (for testing)",
    type=int,
)
@with_appcontext
def fetch_data(dataset, bulk_limit, limit):
    """Import data from 360Giving Data Store into the database"""
    click.echo("Connecting to datastore")
    engine = create_engine(current_app.config["DATASTORE_URL"], echo=True)
    conn = engine.connect()
    click.echo("Connected to datastore")

    # Fetch source file data
    source_result = conn.execute(
        text(
            """
    select data
    from db_sourcefile ds 
    where ds.id in (
        select distinct source_file_id 
        from view_latest_grant vlg 
    )
    """
        )
    )
    for row in source_result:
        # create the publisher
        publisher = Publisher(**row.data["publisher"])
        db.session.merge(publisher)
        db.session.commit()

        # create the source file
        source_file = SourceFile(
            id=row.data["identifier"],
            title=row.data["title"],
            issued=datetime.date.fromisoformat(row.data["issued"]),
            modified=datetime.datetime.fromisoformat(row.data["modified"][0:19]),
            license=row.data["license"],
            license_name=row.data["license_name"],
            description=row.data["description"],
            publisher=publisher,
        )
        db.session.merge(source_file)
        db.session.commit()

        for index, d in enumerate(row.data["distribution"]):
            distribution = Distribution(
                id="{}-{}".format(row.data["identifier"], index),
                source_file=source_file,
                **d,
            )

            db.session.merge(distribution)
            db.session.commit()

    count_sql = text("select count(*) from view_latest_grant g")
    row_count = conn.execute(count_sql).fetchone()[0]

    s = """
    select g.data->>'id' as "grant_id",
        g.data->>'title' as title,
        g.data->>'description' as description,
        g.data->>'currency' as currency,
        (g.data->>'amountAwarded')::float as "amountAwarded",
        g.data->>'awardDate' as "awardDate",
        g.data->'plannedDates'->0->>'startDate' as "plannedDates_startDate",
        g.data->'plannedDates'->0->>'endDate' as "plannedDates_endDate",
        g.data->'plannedDates'->0->>'duration' as "plannedDates_duration",
        g.data->'recipientOrganization'->0->>'id' as "recipientOrganization_id",
        g.data->'recipientOrganization'->0->>'name' as "recipientOrganization_name",
        g.data->'recipientOrganization'->0->>'charityNumber' as "recipientOrganization_charityNumber",
        g.data->'recipientOrganization'->0->>'companyNumber' as "recipientOrganization_companyNumber",
        g.data->'recipientOrganization'->0->>'postalCode' as "recipientOrganization_postalCode",
        g.data->'fundingOrganization'->0->>'id' as "fundingOrganization_id",
        g.data->'fundingOrganization'->0->>'name' as "fundingOrganization_name",
        g.data->'fundingOrganization'->0->>'department' as "fundingOrganization_department",
        g.data->'grantProgramme'->0->>'title' as "grantProgramme_title",
        g.additional_data->'locationLookup'->0->>'rgncd' as "insights_geo_region",
        g.additional_data->'locationLookup'->0->>'ladcd' as "insights_geo_la",
        g.additional_data->'locationLookup'->0->>'ctrycd' as "insights_geo_country",
        (g.additional_data->'locationLookup'->0->>'latitude')::float as "insights_geo_lat",
        (g.additional_data->'locationLookup'->0->>'longitude')::float as "insights_geo_long",
        g.additional_data->'locationLookup'->0->>'source' as "insights_geo_source",
        g.additional_data->'recipientOrgInfos'->0->>'id' as "insights_org_id",
        g.additional_data->>'TSGFundingOrgType' as "insights_funding_org_type",
        NULLIF(g.additional_data->'recipientOrgInfos'->0->>'dateRegistered', '') as "insights_org_registered_date",
        (NULLIF(g.additional_data->'recipientOrgInfos'->0->>'latestIncome', ''))::float as "insights_org_latest_income",
        g.additional_data->'recipientOrgInfos'->0->>'organisationType' as "organisationType",
        g.source_data->>'identifier' as "source_file_id",
        g.source_data->'publisher'->>'prefix' as "publisher_id"
    from view_latest_grant g
    """
    if limit:
        s += " LIMIT {}".format(limit)

    click.echo("Removing existing grants")
    db.session.query(Grant).filter(Grant.dataset == dataset).delete()

    click.echo("Fetching rows")
    result = conn.execution_options(stream_results=True).execute(text(s))
    objects = []
    click.echo("Fetched rows")

    def save_objects(objects):
        if not objects:
            return []
        click.echo("{:,.0f} rows to save".format(len(objects)))
        db.session.bulk_insert_mappings(Grant, objects)
        click.echo("Saving rows")
        click.echo("Rows saved")
        return []

    with click.progressbar(
        result, label="Processing rows", show_pos=True, length=row_count
    ) as bar:
        for row in bar:
            row = dict(row)

            # add dataset name
            row["dataset"] = dataset

            # sort out organistion type
            orgType = []
            try:
                orgType = json.loads(row["organisationType"])
            except TypeError:
                pass
            except json.decoder.JSONDecodeError:
                if isinstance(row["organisationType"], str):
                    orgType = [row["organisationType"]]
                else:
                    click.echo(
                        "Couldn't process organisation type for grant {}: {}".format(
                            row["grant_id"], row["organisationType"]
                        ),
                        err=True,
                    )
            del row["organisationType"]

            if not row["insights_org_id"]:
                row["insights_org_id"] = row["recipientOrganization_id"]

            org_id_schema, org_id_value = get_org_schema(row["insights_org_id"])
            row["insights_org_type"] = "Identifier not recognised"
            if org_id_schema is None and orgType:
                row["insights_org_type"] = orgType[0]
            elif org_id_schema == "GB-COH" and len(orgType) > 1:
                row["insights_org_type"] = orgType[1]
            elif org_id_schema in settings.IDENTIFIER_MAP:
                row["insights_org_type"] = settings.IDENTIFIER_MAP.get(
                    org_id_schema, org_id_schema
                )
            elif org_id_schema and not org_id_schema.startswith("GB-"):
                row["insights_org_type"] = "Overseas organisation"
            elif org_id_schema:
                row["insights_org_type"] = org_id_schema

            # sort out duration field
            if row["plannedDates_duration"]:
                try:
                    row["plannedDates_duration"] = int(row["plannedDates_duration"])
                except ValueError:
                    row["plannedDates_duration"] = None

            # sort out dates
            for f in [
                "awardDate",
                "insights_org_registered_date",
                "plannedDates_startDate",
                "plannedDates_endDate",
            ]:
                if not row[f]:
                    continue
                try:
                    row[f] = datetime.date.fromisoformat(row[f][0:10])
                except ValueError:
                    row[f] = None
                    click.echo(
                        "Invalid date for grant {} [{}]: {}".format(
                            row["grant_id"], f, row[f]
                        ),
                        err=True,
                    )

            # sort out bandings
            row["insights_band_amount"] = to_band(
                row["amountAwarded"], settings.AMOUNT_BINS, settings.AMOUNT_BIN_LABELS
            )
            if row["insights_org_latest_income"]:
                row["insights_band_income"] = to_band(
                    row["insights_org_latest_income"],
                    settings.INCOME_BINS,
                    settings.INCOME_BIN_LABELS,
                )
            if row["insights_org_registered_date"]:
                days = (row["awardDate"] - row["insights_org_registered_date"]).days
                days = max(days, 0)
                row["insights_band_age"] = to_band(
                    days, settings.AGE_BINS, settings.AGE_BIN_LABELS
                )
            objects.append(row)

            if len(objects) >= bulk_limit:
                click.echo("")
                objects = save_objects(objects)

    objects = save_objects(objects)
    db.session.commit()
    click.echo("All rows saved")


@cli.command("geonames")
@click.option(
    "--url-template",
    default=settings.FTP_URL,
    show_default=True,
    help="Template URL to get data from findthatpostcode",
)
@with_appcontext
def fetch_data(url_template):
    opts = get_frontpage_options(with_url=False)
    click.echo("Fetching geonames")
    for i in ["countries", "regions", "local_authorities"]:
        count = 0
        click.echo(f"Fetching {i}")
        with click.progressbar(opts[i]) as bar:
            for v in bar:
                r = requests.get(url_template.format(v["id"]))
                geoname = GeoName(
                    id=v["id"],
                    name=r.json()["data"]["attributes"]["name"],
                    type_=i,
                )
                db.session.merge(geoname)
                db.session.commit()
                count += 1
        click.echo(f"Fetched {count:,.0f} {i}")
