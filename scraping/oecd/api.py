import datetime
import http
import json
import os
import re
import requests

from bs4 import BeautifulSoup
from urllib.parse import urlencode

from utils.utils import MMEnum, safe_mkdir, set_basic_logging_config

LOGGER = set_basic_logging_config("OECD")


# =========== API PARAMS ====================
class AgencyName(MMEnum):
    ALL = "all"
    OECD = "OECD"


# TODO: Maybe distinguish from the result Period?
class Period:
    # TODO: Figure out how to do tree-like structures in general.
    class Semester(MMEnum):
        FIRST = "S1"
        SECOND = "S2"

    class Quarter(MMEnum):
        FIRST = "Q1"
        SECOND = "Q2"
        THIRD = "Q3"
        FOURTH = "Q4"

    class Month(MMEnum):
        JANUARY = "M1"
        FEBRUARY = "M2"
        MARCH = "M3"
        APRIL = "M4"
        MAY = "M5"
        JUNE = "M6"
        JULY = "M7"
        AUGUST = "M8"
        SEPTEMBER = "M9"
        OCTOBER = "M10"
        NOVEMBER = "M11"
        DECEMBER = "M12"

    def __init__(
            self,
            year,
            semester: Semester = None,
            quarter: Quarter = None,
            month: Month = None
    ):
        subval = None
        if semester is not None:
            subval = f"-{semester}"
        if quarter is not None:
            if subval is not None:
                raise Exception(f"cannot set both semester {semester} and quarter {quarter}")
            subval = f"-{quarter}"
        if month is not None:
            if subval is not None:
                raise Exception(f"cannot set month {month} if already set semester or quarter")
            subval = f"-{month}"

        self.value = f"{year}{subval if subval else ''}"

    def __str__(self):
        return self.value


class DimensionAtObservation(MMEnum):
    TIME = "TimeDimension"
    MEASURE = "MeasureDimension"
    ALL = "AllDimensions"
    """(default) results in a flat list of observations without any grouping."""


class Detail(MMEnum):
    """This attribute specifies the desired amount of information to be returned."""
    FULL = "Full"
    """(default) All data and documentation, including annotations"""
    DATA_ONLY = "DataOnly"
    """attributes – and therefore groups – will be excluded"""
    SERIES_KEYS_ONLY = "SeriesKeysOnly"
    """only the series elements and the dimensions that make up the series keys"""
    NO_DATE = "NoData"
    """ returns the groups and series, including attributes and annotations, without observations"""


class ContentType(MMEnum):
    JSON = "json"
    CSV = "csv"


# TODO(generalize): This can be generalized into sth like (data -> url, url -> data)
def list_database_codes(orig_db_codes, code_to_name_map, recurse_level=3):
    """
    param orig_db_codes: starting list of db codes to scrape, e.g.: ["MEI", "QNA"]
    param code_to_name_map: to collect code to name mappings, e.g. "MEI: Main Economic Indicators Publication"
    param recurse_level: how many calls (including this one) should be called with new db codes.

    An alternative approach would be going though the list API, but getting the dataset codes is non-straightforward.
    # page_start = 0
    # page_size = 200
    # url = f"https://data.oecd.org/search-api/?hf={page_size}&b={page_start}&r=%2Bf%2Ftype%2Fdatasets%2Fapi+access&r=%2Bf%2Flanguage%2Fen&l=en&sl=sl_dp&sc=enabled%3Atrue%2Cautomatically_correct%3Atrue&target=st_dp"
    """
    if recurse_level <= 0:
        return []


    parsed_db_codes = set()
    safe_mkdir("data/html")
    for db_code in orig_db_codes:
        # Cache the fetch results to disk as it's rather slow to fetch again.
        db_code_filename = f"data/html/{db_code}.html"
        url = f"https://stats.oecd.org/Index.aspx?DatasetCode={db_code}"

        if not os.path.exists(db_code_filename):
            LOGGER.info(f"Fetching data from {url}")
            response = requests.get(url)
            if response.status_code != http.HTTPStatus.OK:
                LOGGER.warning(f"Ignoring response {response.status_code}: {response.text[:100]}")
                continue
            with open(db_code_filename, "w") as output_file:
                output_file.write(response.text)

        with open(db_code_filename, "r") as fp:
            soup = BeautifulSoup(fp, features="html.parser")

        code_to_name_map[db_code] = soup.title.text.strip()
        for link in soup.find_all("a"):
            url = link.get("href")
            if url is not None:
                # Examples:
                # OECDStat_Metadata/ShowMetadata.ashx?DataSet=ITF_INDICATORS
                # Index.aspx?DataSetCode=ITF_ROAD_ACCIDENTS
                match = re.match(r'.*(DataSet[^"]*).*', url)
                if match:
                    parsed_db_codes.add(match.group(1).split("=")[1])

    new_db_codes = parsed_db_codes.difference(set(orig_db_codes))
    LOGGER.info(f"Found {len(new_db_codes)} new db_codes, first 10: {list(new_db_codes)[:10]}")
    if len(new_db_codes) > 0:
        recursed_db_codes = list_database_codes(new_db_codes, code_to_name_map, recurse_level=recurse_level - 1)
        parsed_db_codes.update(set(recursed_db_codes))
    return list(parsed_db_codes)


# ============== OECD API ================
def get_and_store_dataset(
        dataset,
        filepath,
        start_period: Period,
        end_period: Period = Period(year=datetime.datetime.now().year),
        dimension_at_observation: DimensionAtObservation = DimensionAtObservation.ALL,
        detail: Detail = Detail.FULL,
        agency_name: AgencyName = AgencyName.ALL,
        content_type: ContentType = ContentType.JSON,
):
    """Issues a GET request to OECD SDMX JSON API with the given parameters.

    Known limitations: does NOT support filtering at ALL (as it tries to get all possible data).
    Some helpful tips like contentType=csv: https://stackoverflow.com/questions/40565871/read-data-from-oecd-api-into-python-and-pandas
    """
    base_url = f"https://stats.oecd.org/sdmx-json/data/{dataset}/all/{agency_name}"
    query_params = {
        # Hm, they call it startPeriod/endPeriod in the definition, but examples have *Time*.
        "startTime": start_period,
        "endTime": end_period,
        "dimensionAtObservation": dimension_at_observation,
        "detail": detail,
    }
    if content_type == ContentType.CSV:
        query_params["contentType"] = ContentType.CSV

    url = f"{base_url}?{urlencode(query_params)}"
    LOGGER.info(f"Querying {url}")
    response = requests.get(url)
    if response.status_code != http.HTTPStatus.OK:
        raise Exception(f"Non-200 status code: {response.status_code}: {response.text[:100]} url={url}")

    with open(filepath, "w") as output_file:
        if content_type == ContentType.JSON:
            # Put it through json load / dump to verify it's a correct json.
            dataset = json.loads(response.content)
            LOGGER.info(f"{dataset['header']}")
            json.dump(dataset, output_file)
            # output_file.write(str(response.content))
        elif content_type == ContentType.CSV:
            output_file.write(response.text)
        else:
            Exception(f"Unexpected content type {content_type}")


safe_mkdir("data")

db_code_manual_list = ["MEI", "MEI_CLI", "SNA", "HEALTH_STATE", "CRSNEW", "NAAG", "SHA", "STLABOUR", "SOCX_AGG", "MSTI_PUB", "CITIES", "QNA", "PDB_GR", "IDD", "MIG", "PDB_LV", "LFS_SEXAGE_I_R", "REV", "PNNI_NEW", "PPPGDP", "GREEN_GROWTH", "AEI_OTHER", "WEALTH", "ULC_QUA", "RS_GBL", "EAG_NEAC", "AEA", "DUR_I", "EAG_TRANS", "AV_AN_WAGE", "GENDER_EMP", "JOBQ", "HH_DASH", "IDO", "AIR_GHG", "FIN_IND_FBS", "MATERIAL_R"]
enum_map = {}
list_database_codes(db_code_manual_list, enum_map, 3)
# TODO: Generate enums.

# get_and_store_dataset("QNA", filepath="data/test.json", start_period=Period(year="2019"), content_type=ContentType.JSON)



