# name of the main dataset used in creating the data
DEFAULT_DATASET = "main"

# number of rows to upload at once in bulk
BULK_LIMIT = 10000

# bins for amount awarded
AMOUNT_BINS = [0, 500, 1000, 2000, 5000, 10000, 100000, 1000000, float("inf")]
AMOUNT_BIN_LABELS = [
    "Up to £500",
    "£501 - £1,000",
    "£1,001 - £2,000",
    "£2,001 - £5,000",
    "£5,001 - £10,000",
    "£10,001 - £100k",
    "£101k - £1m",
    "Over £1m",
]

# bins for latest income
INCOME_BINS = [-1, 10000, 100000, 250000, 500000, 1000000, 10000000, float("inf")]
INCOME_BIN_LABELS = [
    "Under £10k",
    "£10k - £100k",
    "£100k - £250k",
    "£250k - £500k",
    "£500k - £1m",
    "£1m - £10m",
    "Over £10m",
]

# bins for organisation age (in days)
AGE_BINS = [x * 365 for x in [-1, 1, 2, 5, 10, 25, 200]]
AGE_BIN_LABELS = [
    "Under 1 year",
    "1-2 years",
    "2-5 years",
    "5-10 years",
    "10-25 years",
    "Over 25 years",
]

# Lookups for organisation types from org ID schema
IDENTIFIER_MAP = {
    "360G": "Identifier not recognised",  # 360G          41190
    "GB-CHC": "Registered Charity (E&W)",  # GB-CHC	157106
    "GB-COH": "Registered Company",  # GB-COH	37263
    "GB-SC": "Registered Charity (Scotland)",  # GB-SC	25627
    "GB-NIC": "Registered Charity (NI)",  # GB-NIC	4089
    "GB-EDU": "School/University/Education",  # GB-EDU	1750
    "GB-NHS": "NHS",  # GB-NHS	800
    "GB-LAE": "Local Authority",  # GB-LAE	403
    "GB-UKPRN": "School/University/Education",  # GB-UKPRN	253
    "US-EIN": "US - registered with IRS",  # US-EIN	176
    "GB-REV": "Registered Charity (HMRC)",  # GB-REV	161
    "GB-MPR": "Mutual",  # GB-MPR	114
    "GB-LAS": "Local Authority",  # GB-LAS	88
    "GB-PLA": "Local Authority",  # GB-LAS	88
    "GB-GOR": "Government",  # GB-GOR	39
    "GB-SHPE": "Social Housing Provider",
    "ZA-NPO": "South Africa - registered with Nonprofit Organisation Directorate",  # ZA-NPO	39
    "IM-GR": "Registered Charity (Isle of Man)",  # IM-GR	20
    # IL-RA	25
    # UK-COH	24
    # NL-KVK	13
    # ZA-PBO	12
    # GB-SCOTEDU	11
    # CA-CRA_ACR	9
    # XM-DAC	8
    # IL-ROC	7
    # KE-NCB	7
    # BE-BCE_KBO	7
    # GG-RCE	6
    # ZA-CIP	5
    # GB-GOV	4
    # IE-CHY	4
    # SE-BLV	3
    # CH-FDJP	3
    # GC-MPR	3
    # JE-FSC	2
    # GB-PLA	2
    # IT-CF	2
    # MW-RG	2
    # GB-URN	2
    # UG-NGB	2
    # RW-RGB	1
    # AU-ANC	1
    # SG-COC	1
    # TZ-BRLA	1
    # UG-RSB	1
    # GB-WOC	1
    # US-DOS	1
    # US-EIN 27	1
    # XI-GRID	1
    # GB-NI	1
    # GB-GEC	1
    # DE-CR	1
    # IS-RSK	1
    # ZW-PVO	1
    # IN-MHA	1
    # KE-RCO	1
    # MW-NBM	1
    # GH-COH	1
    # NO-BRREG	1
}

FTP_URL = "https://findthatpostcode.uk/areas/{}.json"

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

URL_FETCH_ALLOW_LIST = [
    "grantnav.threesixtygiving.org",
]
