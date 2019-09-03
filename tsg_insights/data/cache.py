import os
import pickle
import logging
import json
import datetime

import pandas as pd
from flask import current_app
from redis import StrictRedis, from_url
from .utils import CustomJSONEncoder

REDIS_DEFAULT_URL = 'redis://localhost:6379/0'
REDIS_ENV_VAR = 'REDIS_URL'


def get_cache(strict=False):
    redis_url = current_app.config.get("REDIS_URL")
    if strict:
        return StrictRedis.from_url(redis_url)
    return from_url(redis_url)

def get_filename(fileid):
    uploads_folder = current_app.config.get("UPLOADS_FOLDER")
    return os.path.join(uploads_folder, "{}.pkl".format(fileid))


def save_to_cache(fileid, df, metadata=None, cache_type=None):
    r = get_cache()
    prefix = current_app.config.get("CACHE_DEFAULT_PREFIX", "file_")
    cache_type = cache_type or current_app.config.get("FILE_CACHE")

    if cache_type == "redis":
        r.set("{}{}".format(prefix, fileid), pickle.dumps(df))
        logging.info("Dataframe [{}] saved to redis".format(fileid))
    else:
        with open(get_filename(fileid), "wb") as pkl_file:
            pickle.dump(df, pkl_file)
        logging.info("Dataframe [{}] saved to filesystem".format(fileid))

    if not metadata:
        metadata = {}

    metadata = {
        "fileid": fileid,
        "funders": df["Funding Org:0:Name"].unique().tolist(),
        "max_date": df["Award Date"].max().isoformat(),
        "min_date": df["Award Date"].min().isoformat(),
        **metadata
    }
    r.hset("files", fileid, json.dumps(metadata, default=CustomJSONEncoder().default))
    logging.info("Dataframe [{}] metadata saved to redis".format(fileid))


def delete_from_cache(fileid, cache_type=None):
    r = get_cache()
    prefix = current_app.config.get("CACHE_DEFAULT_PREFIX", "file_")
    cache_type = cache_type or current_app.config.get("FILE_CACHE")

    if cache_type == "redis":
        r.delete("{}{}".format(prefix, fileid))
        logging.info("Dataframe [{}] removed from redis".format(fileid))
    else:
        filename = get_filename(fileid)
        if os.path.exists(filename):
            os.remove(filename)
        logging.info("Dataframe [{}] removed from filesystem".format(fileid))

    r.hdel("files", fileid)
    logging.info("Dataframe [{}] metadata removed from redis".format(fileid))


def get_from_cache(fileid, cache_type=None):
    r = get_cache()
    prefix = current_app.config.get("CACHE_DEFAULT_PREFIX", "file_")
    cache_type = cache_type or current_app.config.get("FILE_CACHE")

    metadata = get_metadata_from_cache(fileid)
    if not metadata:
        logging.info("Dataframe [{}] not found".format(fileid))
        df = get_dataframe(fileid)
        save_to_cache(fileid, df)
        return df
    if "expires" in metadata:
        if datetime.datetime.strptime(metadata["expires"], "%Y-%m-%dT%H:%M:%S.%f") < datetime.datetime.now():
            logging.info("Dataframe [{}] expired on {}".format(
                fileid, metadata["expires"]))
            return None

    if cache_type == "redis":
        df = r.get("{}{}".format(prefix, fileid))
        if df:
            try:
                logging.info("Retrieved dataframe [{}] from redis".format(fileid))
                return pickle.loads(df)
            except ImportError as error:
                logging.info(
                    "Dataframe [{}] could not be loaded".format(fileid))
                return None

    else:
        filename = get_filename(fileid)
        if os.path.exists(filename):
            with open(filename, "rb") as pkl_file:
                try:
                    df = pickle.load(pkl_file)
                    logging.info(
                        "Retrieved dataframe [{}] from filesystem".format(fileid))
                    return df
                except ImportError as error:
                    logging.info("Dataframe [{}] could not be loaded".format(fileid))
                    return None
        logging.info("File [{}] doesn't exist".format(filename))

    df = get_dataframe(fileid)
    save_to_cache(fileid, df)
    return df


def get_dataframe(fileid):
    from tsg_insights.data.process import DataPreparation, CheckColumnNames, CheckColumnsExist, CheckColumnTypes, AddExtraColumns, CleanRecipientIdentifiers, AddExtraFieldsExternal
    df = pd.read_sql(
        '''
        select "grant"."id" as "Identifier",
            "grant"."title" as "Title",
            "grant"."description" as "Description",
            "grant"."currency" as "Currency",
            "grant"."amountAwarded" as "Amount Awarded",
            "grant"."awardDate" as "Award Date",
            "grant"."plannedDates_startDate",
            "grant"."plannedDates_endDate",
            "grant"."plannedDates_duration",
            "grant"."recipientOrganization_id" as "Recipient Org:0:Identifier",
            "grant"."recipientOrganization_name" as "Recipient Org:0:Name",
            "grant"."recipientOrganization_charityNumber" as "Recipient Org:0:Charity Number",
            "grant"."recipientOrganization_companyNumber" as "Recipient Org:0:Company Number",
            "grant"."recipientOrganization_postalCode" as "Recipient Org:0:Postcode",
            "grant"."fundingOrganization_id" as "Funding Org:0:Identifier",
            "grant"."fundingOrganization_name" as "Funding Org:0:Name",
            "grant"."fundingOrganization_department" as "Funding Org:0:Department",
            "grant"."grantProgramme_title" as "Grant Programme:0:Title",
            "postcode"."ctry" as "__geo_ctry",
            "postcode"."cty" as "__geo_cty",
            "postcode"."laua" as "__geo_laua",
            "postcode"."pcon" as "__geo_pcon",
            "postcode"."rgn" as "__geo_rgn",
            "postcode"."imd" as "__geo_imd",
            "postcode"."ru11ind" as "__geo_ru11ind",
            "postcode"."oac11" as "__geo_oac11",
            "postcode"."lat" as "__geo_lat",
            "postcode"."long" as "__geo_long",
            "organisation"."latest_income" as "__org_latest_income"
        from "grant"
            left outer join "postcode"
                on "grant"."recipientOrganization_postalCode" = "postcode"."id"
            left outer join "organisation"
                on "grant"."recipientOrganization_id" = "organisation"."orgid"
        where "dataset" = %(dataset)s
        ''',
        current_app.config.get('SQLALCHEMY_DATABASE_URI'),
        params={'dataset': fileid},
        parse_dates=['Award Date', 'plannedDates_startDate',
                     'plannedDates_endDate']
    )
    prep = DataPreparation(df)
    prep.stages = [CheckColumnNames,
                   CheckColumnsExist,
                   CheckColumnTypes,
                   AddExtraColumns,
                   CleanRecipientIdentifiers,
                   AddExtraFieldsExternal]
    df = prep.run()
    return df

def get_metadata_from_cache(fileid):
    r = get_cache()

    if not r.hexists("files", fileid):
        return None

    return json.loads(r.hget("files", fileid).decode("utf8"))
