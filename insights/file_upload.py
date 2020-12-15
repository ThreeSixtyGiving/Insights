import datetime
import json
import os
from tempfile import mkstemp, TemporaryDirectory
from urllib.parse import urljoin, urlparse
import uuid
import hashlib
from io import BytesIO

from flask import flash, request, redirect, url_for, current_app
from libcove.config import LibCoveConfig
from libcove.lib.converters import convert_spreadsheet, convert_json
from libcove.lib.exceptions import CoveInputDataError
from libcove.lib.tools import get_file_type
import requests

from insights import settings
from insights.db import Grant, db, SourceFile
from insights.utils import get_org_schema, to_band


class FileImportError(Exception):
    pass


def upload_file():
    if "file" not in request.files:
        return {
            "error": "File not found",
        }
    f = request.files["file"]
    fileinfo = {
        "filename": f.filename,
        "content_type": f.content_type,
        "content_length": f.content_length,
        "headers": dict(f.headers),
        "mimetype": f.mimetype,
    }

    result = fetch_file(f, fileinfo)
    if result.get("error"):
        return result, 400
    return result


def fetch_file_from_url(url):

    if urlparse(url).netloc not in current_app.config.get("URL_FETCH_ALLOW_LIST"):
        raise FileImportError("Fetching from that URL is not supported")

    r = requests.get(url)
    r.raise_for_status()
    dataset = str(uuid.uuid4())
    fileinfo = {
        "filename": dataset,
        "content_type": r.headers.get("content-type"),
        "content_length": r.headers.get("content-length"),
        "headers": dict(r.headers),
        "mimetype": r.headers.get("content-type"),
    }
    result = fetch_file(BytesIO(r.content), fileinfo)
    if result.get("data_url"):
        return result["data_url"]
    raise FileImportError("Could not fetch data from URL. " + result.get("error", ""))


def fetch_file(f, fileinfo):

    if fileinfo["mimetype"] in settings.CONTENT_TYPE_MAP:
        fileinfo["filetype"] = settings.CONTENT_TYPE_MAP[fileinfo["mimetype"]]
    else:
        fileinfo["filetype"] = get_file_type(fileinfo["filename"])

    with TemporaryDirectory() as upload_dir:
        lib_cove_config = LibCoveConfig()
        lib_cove_config.config.update(settings.COVE_CONFIG)
        with open(os.path.join(upload_dir, fileinfo["filename"]), "wb") as a:
            contents = f.read()
            fileinfo["dataset"] = hashlib.md5(contents).hexdigest()
            a.write(contents)

        try:
            convert_settings = (
                lib_cove_config,
                urljoin(settings.COVE_CONFIG["schema_host"], settings.COVE_CONFIG["schema_item_name"]),
                urljoin(settings.COVE_CONFIG["schema_host"], settings.COVE_CONFIG["schema_name"]),
            )
            if fileinfo['filetype'] == "json":
                result = convert_json(
                    upload_dir,
                    "",  # upload_url,
                    os.path.join(upload_dir, fileinfo["filename"]),  # file_name,
                    *convert_settings
                )
                result['converted_path'] = os.path.join(upload_dir, fileinfo["filename"])
            else:
                result = convert_spreadsheet(
                    upload_dir,
                    "",  # upload_url,
                    os.path.join(upload_dir, fileinfo["filename"]),  # file_name,
                    fileinfo["filetype"],  # file_type,
                    *convert_settings
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

                with open(result.get("converted_path"), 'rb') as a:
                    data = json.load(a)
                    rows_saved = save_json_to_db(data, fileinfo["dataset"], source_file_id)

                    if rows_saved == 0:
                        return {
                            **fileinfo,
                            "error": "No rows imported from file",
                        }
                    return {
                        **fileinfo,
                        "rows_saved": rows_saved,
                        "data_url": url_for('data', dataset=fileinfo["dataset"]),
                    }
            return {
                **fileinfo,
                "error": "Could not find data to return",
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

    # if any of these fields are missing then we can't include them
    required_fields = ["id", "title", "description", "currency", "amountAwarded", "awardDate"]

    def save_objects(objects):
        if not objects:
            return []
        print("{:,.0f} rows to save".format(len(objects)))
        db.session.bulk_insert_mappings(Grant, objects)
        print("Saving rows")
        print("Rows saved")
        return []

    for row in data.get("grants", []):
        try:
            grant = dict(
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
                recipientOrganization_id=row["recipientOrganization"][0]["id"],
                recipientOrganization_name=row["recipientOrganization"][0]["name"],
                recipientOrganization_charityNumber=row.get(
                    "recipientOrganization", [{}]
                )[0].get("charityNumber"),
                recipientOrganization_companyNumber=row.get(
                    "recipientOrganization", [{}]
                )[0].get("companyNumber"),
                recipientOrganization_postalCode=row.get("recipientOrganization", [{}])[
                    0
                ].get("postalCode"),
                fundingOrganization_id=row["fundingOrganization"][0]["id"],
                fundingOrganization_name=row["fundingOrganization"][0]["name"],
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
        except KeyError:
            print("Could not import grant record")
            continue
        for f in ["awardDate", "plannedDates_startDate", "plannedDates_endDate"]:
            if grant[f] and isinstance(grant[f], str):
                grant[f] = datetime.datetime.strptime(grant[f][0:10], "%Y-%m-%d")
        grants.append(grant)
        rows += 1
        if len(grants) > 1000:
            grants = save_objects(grants)

    save_objects(grants)
    db.session.commit()
    return rows
