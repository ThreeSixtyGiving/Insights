import logging
import re
from tempfile import TemporaryFile
from zipfile import ZipFile
import csv
import codecs
from datetime import datetime

import click
from flask import Flask, url_for, current_app
from flask.cli import AppGroup, with_appcontext
import requests
from tqdm import tqdm

from ..db import db
from ..data import bcp
from ..data.models import Organisation
from ..data.process import COMPANY_REPLACE

cli = AppGroup('import')

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(threadName)-12.12s] [%(levelname)-5.5s]  %(message)s",
    handlers=[
        logging.StreamHandler()
    ])


def parse_company_number(coyno):
        if not coyno:
            return None

        coyno = coyno.strip()
        if coyno == "":
            return None

        if coyno.isdigit():
            return coyno.rjust(8, "0")

        return coyno

@cli.command('companies')
@with_appcontext
def cli_fetch_companies():
    logging.info("Starting to import companies")

    # get the update statements
    upsert_statement = Organisation.upsert_statement()

    # find the download ZIP
    companies_house_base = "http://download.companieshouse.gov.uk/"
    companies_house_url = companies_house_base + "en_output.html"
    r = requests.get(companies_house_url)
    download_file_name = re.search(
        r'BasicCompanyDataAsOneFile\-[0-9]{4}\-[0-9]{2}\-[0-9]{2}\.zip', r.text)[0]
    download_url = companies_house_base + download_file_name
    logging.info("Downloading from: {}".format(download_url))

    # start the download
    tmp_zip = TemporaryFile()
    r = requests.head(download_url)
    total_size = int(r.headers.get('content-length', 0))
    logging.info("File size: {:,.0f}".format(total_size))
    r = requests.get(download_url, stream=True)

    for chunk in tqdm(r.iter_content(32*1024), total=total_size, unit='B', unit_scale=True):
        if chunk:
            tmp_zip.write(chunk)

    with ZipFile(tmp_zip) as z:
        for filename in z.namelist():
            if not filename.endswith(".csv"):
                continue
            logging.info("Importing from: {}".format(filename))

            f = z.open(filename)
            reader = csv.DictReader(codecs.iterdecode(f, 'utf-8'))
            row_count = 0
            objects = []

            for row in tqdm(reader):
                org = Organisation(
                    orgid="GB-COH-{}".format(row[' CompanyNumber']),
                    company_number=row[' CompanyNumber'],
                    date_registered=None if row['IncorporationDate'] == '' else datetime.strptime(
                        row['IncorporationDate'], "%d/%m/%Y"),
                    date_removed=None if row['DissolutionDate'] == '' else datetime.strptime(
                        row['DissolutionDate'], "%d/%m/%Y"),
                    postcode=None if row['RegAddress.PostCode'].strip() == '' else row['RegAddress.PostCode'].strip(),
                    org_type=COMPANY_REPLACE.get(row['CompanyCategory'].strip(), row['CompanyCategory'].strip()),
                    source='Companies House',
                    last_updated=datetime.now(),
                )
                objects.append(org.__dict__)

                if len(objects) == 1000:
                    db.session.execute(upsert_statement, objects)
                    db.session.commit()
                    objects = []

@cli.command('charities')
@with_appcontext
def cli_fetch_charities():
    logging.info("Starting to import charities")

    # get the update statements
    upsert_statement = Organisation.upsert_statement()

    # find the download ZIP
    cc_base = "http://data.charitycommission.gov.uk/"
    r = requests.get(cc_base)
    download_file_name = re.findall(
        r'http:\/\/.*\/RegPlusExtract_.*\.zip', r.text)
    download_url = str(download_file_name[0])
    logging.info("Downloading from: {}".format(download_url))

    # start the download
    tmp_zip = TemporaryFile()
    r = requests.head(download_url)
    total_size = int(r.headers.get('content-length', 0))
    logging.info("File size: {:,.0f}".format(total_size))
    r = requests.get(download_url, stream=True)

    for chunk in tqdm(r.iter_content(32*1024), total=total_size, unit='B', unit_scale=True):
        if chunk:
            tmp_zip.write(chunk)

    with ZipFile(tmp_zip) as z:
        charities = {}
        registrations = {}

        # extract_registration
        filename = 'extract_registration.bcp'
        logging.info("Importing from: {}".format(filename))

        f = z.open(filename)
        contents = bcp.convert(f.read().decode("latin1")).replace('\0', "")
        reader = csv.DictReader(
            contents.splitlines(),
            fieldnames = [
                "regno", "subno", "regdate", "remdate", "remcode"
            ],
            escapechar= "\\"
        )

        for row in tqdm(reader):
            regno = row['regno'].strip()
            if regno is None or regno == "" or row["subno"] is None or (row["subno"].strip() != "0"):
                continue
            if regno not in registrations:
                registrations[regno] = []
            registrations[regno].append({
                "reg": None if row["regdate"].strip() == "" else datetime.strptime(row["regdate"].strip()[0:10], "%Y-%m-%d"),
                "rem": None if row["remdate"].strip() == "" else datetime.strptime(row["remdate"].strip()[0:10], "%Y-%m-%d"),
            })

        # extract_charity
        filename = 'extract_charity.bcp'
        logging.info("Importing from: {}".format(filename))

        f = z.open(filename)
        contents = bcp.convert(f.read().decode("latin1")).replace('\0', "")
        reader = csv.DictReader(
            contents.splitlines(),
            fieldnames = [
                "regno", "subno", "name", "orgtype", "gd", "aob", "aob_defined",
                "nhs", "ha_no", "corr", "add1", "add2", "add3", "add4", "add5",
                "postcode", "phone", "fax"
            ],
            escapechar= "\\"
        )

        for row in tqdm(reader):
            regno = row['regno'].strip()
            orgid = "GB-CHC-{}".format(regno)
            regdates = sorted(registrations.get(regno, []), key=lambda k: k['reg'])
            if regno is None or regno == "" or row["subno"] is None or (row["subno"].strip() != "0"):
                continue
            charities[regno] = Organisation(
                orgid=orgid,
                charity_number=regno,
                company_number=None,
                date_registered=regdates[0]["reg"],
                date_removed=regdates[-1]["rem"],
                postcode=None if row["postcode"].strip(
                ) == "" else row["postcode"].strip(),
                latest_income=None,
                latest_income_date=None,
                org_type='Charitable Incorporated Organisation' if row["gd"].startswith("CIO - ") else 'Registered Charity',
                source='Charity Commission for England and Wales',
                last_updated=datetime.now(),
            )

        # extract_main_charity
        filename = 'extract_main_charity.bcp'
        logging.info("Importing from: {}".format(filename))

        f = z.open(filename)
        contents = bcp.convert(f.read().decode("latin1")).replace('\0', "")
        reader = csv.DictReader(
            contents.splitlines(),
            fieldnames = [
                "regno", "coyno", "trustees", "fyend", "welsh",
                "incomedate", "income", "grouptype", "email", "web"
            ]
        )

        for row in tqdm(reader):
            regno = row['regno'].strip()
            if regno is None or regno == "":
                continue
            coyno = parse_company_number(row["coyno"])
            if coyno:
                charities[regno].company_number = coyno
                if charities[regno].org_type =='Registered Charity':
                    charities[regno].org_type = 'Charitable Company'
            if row['income'].strip() != "":
                charities[regno].latest_income = int(row['income'].strip())
            if row['incomedate'].strip() != "":
                charities[regno].latest_income_date = datetime.strptime(
                    row['incomedate'].strip()[0:10], "%Y-%m-%d")

        # load into the database
        objects = []
        logging.info("Importing into the database")
        for org in tqdm(charities.values()):
            objects.append(org.__dict__)

            if len(objects) == 1000:
                db.session.execute(upsert_statement, objects)
                db.session.commit()
                objects = []
