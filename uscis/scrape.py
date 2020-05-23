import json
import logging
import requests
import sys

from datetime import datetime
from enum import Enum


logging.basicConfig(
    stream=sys.stdout,
    level=logging.INFO,
    format="%(asctime)s %(levelname)-8s %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
LOGGER = logging.getLogger("USCIS SCRAPER")


class FormCode(Enum):
    def __str__(self):
        return str(self.value)

    I_90_APPLICATION_TO_REPLACE_PERMANENT_RESIDENT_CARD = "I-90"
    I_102_APPLICATION_FOR_REPLACEMENT_INITIAL_NONIMMIGRANT_ARRIVAL_DEPARTURE_DOCUMENT = "I-102"
    I_129_PETITION_FOR_A_NONIMMIGRANT_WORKER = "I-129"
    I_129CW_PETITION_FOR_A_CNMI_ONLY_NONIMMIGRANT_TRANSITIONAL_WORKER = "I-129CW"
    I_129F_PETITION_FOR_ALIEN_FIANCE_E = "I-129F"
    I_130_PETITION_FOR_ALIEN_RELATIVE = "I-130"
    I_131_APPLICATION_FOR_TRAVEL_DOCUMENT = "I-131"
    I_140_IMMIGRANT_PETITION_FOR_ALIEN_WORKER = "I-140"
    I_212_APPLICATION_FOR_PERMISSION_TO_REAPPLY_FOR_ADMISSION_INTO_THE_UNITED_STATES_AFTER_DEPORTATION_OR_REMOVAL = "I-212"
    I_360_PETITION_FOR_AMERASIAN_WIDOW_ER_OR_SPECIAL_IMMIGRANT = "I-360"
    I_485_APPLICATION_TO_REGISTER_PERMANENT_RESIDENCE_OR_ADJUST_STATUS = "I-485"
    I_526_IMMIGRANT_PETITION_BY_ALIEN_ENTREPRENEUR = "I-526"
    I_539_APPLICATION_TO_EXTEND_CHANGE_NONIMMIGRANT_STATUS = "I-539"
    I_600_PETITION_TO_CLASSIFY_ORPHAN_AS_AN_IMMEDIATE_RELATIVE = "I-600"
    I_600A_APPLICATION_FOR_ADVANCE_PROCESSING_OF_AN_ORPHAN_PETITION = "I-600A"
    I_601_APPLICATION_FOR_WAIVER_OF_GROUNDS_OF_INADMISSIBILITY = "I-601"
    I_601A_APPLICATION_FOR_PROVISIONAL_UNLAWFUL_PRESENCE_WAIVER = "I-601A"
    I_612_APPLICATION_FOR_WAIVER_OF_THE_FOREIGN_RESIDENCE_REQUIREMENT_UNDER_SECTION_212_E_OF_THE_IMMIGRATION_AND_NATIONALITY_ACT_AS_AMENDED = "I-612"
    I_730_REFUGEE_ASYLEE_RELATIVE_PETITION = "I-730"
    I_751_PETITION_TO_REMOVE_CONDITIONS_ON_RESIDENCE = "I-751"
    I_765_APPLICATION_FOR_EMPLOYMENT_AUTHORIZATION = "I-765"
    I_765V_APPLICATION_FOR_EMPLOYMENT_AUTHORIZATION_FOR_ABUSED_NONIMMIGRANT_SPOUSE = "I-765V"
    I_800_PETITION_TO_CLASSIFY_CONVENTION_ADOPTEE_AS_AN_IMMEDIATE_RELATIVE = "I-800"
    I_800A_APPLICATION_FOR_DETERMINATION_OF_SUITABILITY_TO_ADOPT_A_CHILD_FROM_A_CONVENTION_COUNTRY = "I-800A"
    I_817_APPLICATION_FOR_FAMILY_UNITY_BENEFITS = "I-817"
    I_821_APPLICATION_FOR_TEMPORARY_PROTECTED_STATUS = "I-821"
    I_821D_CONSIDERATION_OF_DEFERRED_ACTION_FOR_CHILDHOOD_ARRIVALS = "I-821D"
    I_824_APPLICATION_FOR_ACTION_ON_AN_APPROVED_APPLICATION_OR_PETITION = "I-824"
    I_829_PETITION_BY_ENTREPRENEUR_TO_REMOVE_CONDITIONS_ON_PERMANENT_RESIDENT_STATUS = "I-829"
    I_914_APPLICATION_FOR_T_NONIMMIGRANT_STATUS = "I-914"
    I_918_PETITION_FOR_U_NONIMMIGRANT_STATUS = "I-918"
    I_924_APPLICATION_FOR_REGIONAL_CENTER_DESIGNATION_UNDER_THE_IMMIGRANT_INVESTOR_PROGRAM = "I-924"
    I_929_PETITION_FOR_QUALIFYING_FAMILY_MEMBER_OF_A_U_1_NONIMMIGRANT = "I-929"
    N_400_APPLICATION_FOR_NATURALIZATION = "N-400"
    N_565_APPLICATION_FOR_REPLACEMENT_NATURALIZATION_CITIZENSHIP_DOCUMENT = "N-565"
    N_600_APPLICATION_FOR_CERTIFICATE_OF_CITIZENSHIP = "N-600"
    N_600K_APPLICATION_FOR_CITIZENSHIP_AND_ISSUANCE_OF_CERTIFICATE_UNDER_SECTION_322 = "N-600K"


class ProcessingCenter(Enum):
    def __str__(self):
        return str(self.value)

    CALIFORNIA_SERVICE_CENTER = "CSC"
    NEBRASKA_SERVICE_CENTER = "NSC"
    POTOMAC_SERVICE_CENTER = "YSC"
    TEXAS_SERVICE_CENTER = "SSC"
    VERMONT_SERVICE_CENTER = "ESC"


def generate_form_codes():
    """Translating form_options.html to FormCode enum"""
    LOGGER.info("Generating FormCode-s ...")
    # Putting imports on-demand, so one just doing the scraping doesn't have to install the slugify library.
    from slugify import slugify
    from xml.etree import ElementTree

    with open("form_options.html", "r") as input_file:
        html_form_raw = input_file.read()
    select = ElementTree.fromstring(html_form_raw)
    for option in select:
        if "Select One" in option.text:
            continue
        parts = option.text.split("|")
        form_code = parts[0].strip()
        form_name = parts[1].strip()
        enum_form_name = f"{form_code}_{slugify(form_name)}".upper().replace("-", "_")
        print(f"{enum_form_name} = \"{form_code}\"")


def get(form_code: FormCode, processing_center: ProcessingCenter):
    url = f"https://egov.uscis.gov/processing-times/api/processingtime/{form_code}/{processing_center}"
    headers = {
        "Host": "egov.uscis.gov",
        "User-Agent": "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:76.0) Gecko/20100101 Firefox/76.0",
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "en-US,en;q=0.5",
        "Accept-Encoding": "gzip, deflate, br",
        "DNT": "1",
        "Connection": "keep-alive",
        "Referer": "https://egov.uscis.gov/processing-times/",
    }
    LOGGER.info(f"Requesting GET {url}")
    response = requests.get(url=url, headers=headers)
    if response.status_code != 200:
        if response.status_code == 400:
            response_data = json.loads(response.content)
            if response_data["message"].startswith("Query was unsuccessful for payload"):
                # This is expected in case trying to get data points for all, e.g. I-90 is processed only in Potomac.
                LOGGER.warning(f"No data for ({form_code},{processing_center.name}) combo")
                return None
        raise Exception(f"Unexpected status code {response.status_code}: {response.text[:100]}")

    return json.loads(response.content)


# generate_form_codes()
rows = []
LOGGER.info(
    f"Will get current USCIS Processing Times for {len(FormCode)} forms"
    f" and {len(ProcessingCenter)} processing centers"
)
for form_code in FormCode:
    for processing_center in ProcessingCenter:
        response_data = get(form_code, processing_center)
        if response_data is None:
            continue

        subtypes = response_data["data"]["processing_time"]["subtypes"]
        for subtype in subtypes:
            row = "\t".join([
                form_code.value,
                subtype["form_type"],
                # human readable name of the processing center
                processing_center.name,
                # requests before this dates SHOULD be processes (you can formally inquire if not)
                subtype["service_request_date"],
                # when it was updated by USCIS (usually monthly)
                subtype["publication_date"],
            ])
            rows.append(row)


output_filename = f"data/processing-times-as-of-{datetime.today().strftime('%Y-%m-%d')}.tsv"
LOGGER.info(f"Writing {output_filename} with {len(rows)} of data (tab separated)")
with open(output_filename, "w") as output_file:
    # Header
    output_file.write("\t".join(["FormCode", "Subtype", "ProcessingCenter", "ServiceRequestDate", "UpdatedByUSCIS"]))
    output_file.write("\n")
    # Rows
    output_file.write("\n".join(sorted(rows)))
