import datetime
import json
import os
from tempfile import mkstemp, TemporaryDirectory
from urllib.parse import urljoin
import uuid
import hashlib

from flask import flash, request, redirect, url_for
from libcove.config import LibCoveConfig
from libcove.lib.converters import convert_spreadsheet, convert_json
from libcove.lib.exceptions import CoveInputDataError
from libcove.lib.tools import get_file_type

from insights import settings
from insights.db import Grant, db, SourceFile
from insights.utils import get_org_schema, to_band


COVE_CONFIG = {
    "app_name": "cove_360",
    "app_base_template": "cove_360/base.html",
    "app_verbose_name": "360Giving Data Quality Tool",
    "app_strapline": "Convert, Validate, Explore 360Giving Data",
    "schema_name": "360-giving-package-schema.json",
    "schema_item_name": "360-giving-schema.json",
    "schema_host": "https://raw.githubusercontent.com/ThreeSixtyGiving/standard/master/schema/",
    "schema_version": None,
    "schema_version_choices": None,
    "root_list_path": "grants",
    "root_id": "",
    "convert_titles": True,
    "input_methods": ["upload", "url", "text"],
    "support_email": "support@threesixtygiving.org",
    "hashcomments": True,
}

CONTENT_TYPE_MAP = {
    "application/json": "json",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": "xlsx",
    "text/csv": "csv",
    "application/vnd.oasis.opendocument.spreadsheet": "ods",
    "application/xml": "xml",
    "text/xml": "xml",
}


def upload_file():
    if "file" not in request.files:
        return {
            "error": "File not found",
        }
    f = request.files["file"]
    # dataset = request.values.get(
    #     "dataset",
    #     str(uuid.uuid4()),
    # )

    fileinfo = {
        "filename": f.filename,
        "content_type": f.content_type,
        "content_length": f.content_length,
        "headers": dict(f.headers),
        "mimetype": f.mimetype,
    }

    if f.mimetype in CONTENT_TYPE_MAP:
        fileinfo["filetype"] = CONTENT_TYPE_MAP[f.mimetype]
    else:
        fileinfo["filetype"] = get_file_type(f.filename)

    with TemporaryDirectory() as upload_dir:
        lib_cove_config = LibCoveConfig()
        lib_cove_config.config.update(COVE_CONFIG)


        with open(os.path.join(upload_dir, f.filename), "wb") as a:
            contents = f.read()
            fileinfo["dataset"] = hashlib.md5(contents).hexdigest()
            a.write(contents)

        try:
            result = convert_spreadsheet(
                upload_dir,
                "",  # upload_url,
                os.path.join(upload_dir, f.filename),  # file_name,
                fileinfo["filetype"],  # file_type,
                lib_cove_config,
                urljoin(COVE_CONFIG["schema_host"], COVE_CONFIG["schema_item_name"]),
                urljoin(COVE_CONFIG["schema_host"], COVE_CONFIG["schema_name"]),
            )
            if result.get("converted_path"):

                source_file_id = "uploaded_dataset_" + fileinfo['dataset']
                source_file = db.session.query(SourceFile).filter_by(id=source_file_id).first()
                if not source_file:
                    source_file = SourceFile(
                        id=source_file_id,
                        title=request.values.get("source_title", fileinfo['filename']),
                        issued=datetime.datetime.now(),
                        modified=datetime.datetime.now(),
                        license=request.values.get("source_license"),
                        license_name=request.values.get("source_license_name"),
                        description=request.values.get("source_description"),
                    )
                    db.session.add(source_file)
                    db.session.commit()

                with open(result.get("converted_path")) as a:
                    data = json.load(a)
                    rows_saved = save_json_to_db(data, fileinfo["dataset"], source_file_id)
                    return {
                        **fileinfo,
                        "rows_saved": rows_saved,
                        "data_url": url_for('data', dataset=fileinfo["dataset"]),
                    }
        except CoveInputDataError as e:
            return {
                **fileinfo,
                "error": str(e),
            }


def save_json_to_db(data, dataset, source_file_id):
    grants = []
    rows = 0
    db.session.query(Grant).filter(Grant.dataset == dataset).delete()

    def save_objects(objects):
        if not objects:
            return []
        print("{:,.0f} rows to save".format(len(objects)))
        db.session.bulk_insert_mappings(Grant, objects)
        print("Saving rows")
        print("Rows saved")
        return []

    for row in data.get("grants", []):
        grants.append(
            dict(
                dataset=dataset,
                grant_id=row["id"],
                title=row["title"],
                description=row["description"],
                currency=row["currency"],
                amountAwarded=row["amountAwarded"],
                awardDate=row["awardDate"],
                plannedDates_startDate=row.get("plannedDates", [{}])[0].get(
                    "startDate"
                ),
                plannedDates_endDate=row.get("plannedDates", [{}])[0].get("endDate"),
                plannedDates_duration=row.get("plannedDates", [{}])[0].get("duration"),
                recipientOrganization_id=row.get("recipientOrganization", [{}])[0].get(
                    "id"
                ),
                recipientOrganization_name=row.get("recipientOrganization", [{}])[
                    0
                ].get("name"),
                recipientOrganization_charityNumber=row.get(
                    "recipientOrganization", [{}]
                )[0].get("charityNumber"),
                recipientOrganization_companyNumber=row.get(
                    "recipientOrganization", [{}]
                )[0].get("companyNumber"),
                recipientOrganization_postalCode=row.get("recipientOrganization", [{}])[
                    0
                ].get("postalCode"),
                fundingOrganization_id=row.get("fundingOrganization", [{}])[0].get(
                    "id"
                ),
                fundingOrganization_name=row.get("fundingOrganization", [{}])[0].get(
                    "name"
                ),
                fundingOrganization_department=row.get("fundingOrganization", [{}])[
                    0
                ].get("department"),
                grantProgramme_title=row.get("grantProgramme", [{}])[0].get("title"),
                # file link,
                source_file_id=source_file_id,
                publisher_id=None,
                # insights specific fields - geography,
                insights_geo_region=None,
                insights_geo_la=None,
                insights_geo_country=None,
                insights_geo_lat=None,
                insights_geo_long=None,
                insights_geo_source=None,
                # insights specific fields - organisation,
                insights_org_id=row.get("recipientOrganization", [{}])[0].get("id"),
                insights_org_registered_date=None,
                insights_org_latest_income=None,
                insights_org_type=None,
                insights_funding_org_type=None,
                # insights specific fields - bands,
                insights_band_age=None,
                insights_band_income=None,
                insights_band_amount=to_band(
                    row["amountAwarded"],
                    settings.AMOUNT_BINS,
                    settings.AMOUNT_BIN_LABELS,
                ),
            )
        )
        rows += 1
        if len(grants) > 1000:
            grants = save_objects(grants)
    save_objects(grants)
    db.session.commit()
    return rows
