import json
import logging
import requests
import sys

from datetime import datetime
from dateutil import parser
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
    NATIONAL_BENEFITS_CENTER = "NBC"
    AGANA_GU = "AGA"
    ALBANY_NY = "ALB"
    ALBUQUERQUE_NM = "ALB"
    ANCHORAGE_AK = "ANC"
    ATLANTA_GA = "ATL"
    BALTIMORE_MD = "BAL"
    BOISE_ID = "BOI"
    BOSTON_MA = "BOS"
    BROOKLYN_NY = "BRO"
    BUFFALO_NY = "BUF"
    CHARLESTON_SC = "CHA"
    CHARLOTTE_AMALIE_VI = "CHA"
    CHARLOTTE_NC = "CHA"
    CHICAGO_IL = "CHI"
    CHRISTIANSTED_VI = "CHR"
    CINCINNATI_OH = "CIN"
    CLEVELAND_OH = "CLE"
    COLUMBUS_OH = "COL"
    DALLAS_TX = "DAL"
    DENVER_CO = "DEN"
    DES_MOINES_IA = "DES"
    DETROIT_MI = "DET"
    EL_PASO_TX = "ELP"
    FORT_MYERS_FL = "FOR"
    FORT_SMITH_AR = "FOR"
    FRESNO_CA = "FRE"
    GREER_SC = "GRE"
    HARLINGEN_TX = "HAR"
    HARTFORD_CT = "HAR"
    HELENA_MT = "HEL"
    HIALEAH_FL = "HIA"
    HONOLULU_HI = "HON"
    HOUSTON_TX = "HOU"
    IMPERIAL_CA = "IMP"
    INDIANAPOLIS_IN = "IND"
    JACKSONVILLE_FL = "JAC"
    KANSAS_CITY_MO = "KAN"
    KENDALL_FL = "KEN"
    LAS_VEGAS_NV = "LAS"
    LAWRENCE_MA = "LAW"
    LONG_ISLAND_NY = "LON"
    LOS_ANGELES_CA = "LOS"
    LOS_ANGELES_COUNTY_CA = "LAC"
    LOUISVILLE_KY = "LOU"
    MANCHESTER_NH = "MAN"
    MEMPHIS_TN = "MEM"
    MIAMI_FL = "MIA"
    MILWAUKEE_WI = "MIL"
    MINNEAPOLIS_ST_PAUL_MN = "MIN"
    MONTGOMERY_AL = "MON"
    MOUNT_LAUREL_NJ = "MOU"
    NASHVILLE_TN = "NAS"
    NEWARK_NJ = "NEW"
    NEW_ORLEANS_LA = "NEW"
    NEW_YORK_CITY_NY = "NEW"
    NORFOLK_VA = "NOR"
    OAKLAND_PARK_FL = "OAK"
    OKLAHOMA_CITY_OK = "OKL"
    OMAHA_NE = "OMA"
    ORLANDO_FL = "ORL"
    PHILADELPHIA_PA = "PHI"
    PHOENIX_AZ = "PHO"
    PITTSBURGH_PA = "PIT"
    PORTLAND_ME = "POM"
    PORTLAND_OR = "POO"
    PROVIDENCE_RI = "PRO"
    QUEENS_NY = "QUE"
    RALEIGH_NC = "RAL"
    RENO_NV = "REN"
    SACRAMENTO_CA = "SAC"
    SAINT_ALBANS_VT = "SAI"
    SAINT_LOUIS_MO = "SAI"
    SALT_LAKE_CITY_UT = "SAL"
    SAN_ANTONIO_TX = "SNA"
    SAN_BERNARDINO_CA = "SNB"
    SAN_DIEGO_CA = "SND"
    SAN_FERNANDO_VALLEY_CA = "SNF"
    SAN_FRANCISCO_CA = "SFR"
    SAN_JOSE_CA = "SNJ"
    SAN_JUAN_PR = "SAJ"
    SANTA_ANA_CA = "SAA"
    SEATTLE_WA = "SEA"
    SPOKANE_WA = "SPO"
    TAMPA_FL = "TAM"
    TUCSON_AZ = "TUC"
    WASHINGTON_DC = "WAS"
    WEST_PALM_BEACH_FL = "WES"
    WICHITA_KS = "WIC"
    YAKIMA_WA = "YAK"


def generate_form_codes():
    """Translating form_options.html to FormCode enum"""
    LOGGER.info("Generating FormCode-s ...")
    # Putting imports on-demand, so one just doing the scraping doesn't have to install the slugify library.
    from slugify import slugify
    from xml.etree import ElementTree

    with open("form_code_options.html", "r") as input_file:
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

    with open("processing_center_options.html", "r") as input_file:
        html_form_raw = input_file.read()
    select = ElementTree.fromstring(html_form_raw)
    for option in select:
        if "Select One" in option.text:
            continue
        enum_form_name = slugify(option.text).upper().replace("-", "_")
        print(f"{enum_form_name} = \"{enum_form_name[:3]}\"")  # Best effort code is to take first three letters.


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


def maybe_shorten(text, max_length):
    if len(text) <= max_length:
        return text

    return text[:(max_length + 1)//2 - 2] + "..." + text[-(max_length//2 - 1):]


# ============== ONE-TIME setup (copy this to enum definitions)
# generate_form_codes()

# ============== RE-SCRAPE data
rows = []
LOGGER.info(
    f"Will get current USCIS Processing Times for {len(FormCode)} forms"
    f" and {len(ProcessingCenter)} processing centers"
)
for form_code in list(FormCode)[:2]:
    publication_date = None

    # For most of Forms, only the first 6 centers make sense. The full list is used e.g. for I-485
    for processing_center in list(ProcessingCenter)[:6]:
        response_data = get(form_code, processing_center)
        if response_data is None:
            continue

        subtypes = response_data["data"]["processing_time"]["subtypes"]
        for subtype in subtypes:
            if publication_date is None:
                publication_date = subtype["publication_date"]
            if publication_date and publication_date != subtype["publication_date"]:
                LOGGER.warning(
                    f"Two different publication dates {publication_date} and {subtype['publication_date']}"
                )

            range = subtype["range"]
            range_text = f"{range[1]['value']} {range[1]['unit']} - {range[0]['value']} {range[0]['unit']}"
            row = "\t".join([
                form_code.value,
                maybe_shorten(subtype["subtype_info_en"], 50),   # Human-readable version of subtype["form_type"],
                # human readable name of the processing center
                processing_center.name.split("_")[0],
                # USCIS expected processing time range (also depends on the application)
                range_text,
                # requests before this dates SHOULD be processes (you can formally inquire if not)
                subtype["service_request_date"],
            ])
            rows.append(row)


publication_date_parsed = parser.parse(publication_date)
output_filename = f"data/processing-times-as-of-{publication_date_parsed.strftime('%Y-%m-%d')}.tsv"
LOGGER.info(f"Writing {output_filename} with {len(rows)} of data (tab separated)")
with open(output_filename, "w") as output_file:
    # Header
    output_file.write("\t".join(
        ["FormCode", "Subtype", "ProcessingCenter", "ExpectedProcessingTime", "ServiceRequestDate", "UpdatedByUSCIS"])
    )
    output_file.write("\n")
    # Rows
    output_file.write("\n".join(sorted(rows)))
