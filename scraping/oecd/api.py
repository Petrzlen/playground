import datetime
import http
import json
import os
import re
import requests

from bs4 import BeautifulSoup
from urllib.parse import urlencode

from oecd.enums.database_codes import DatabaseCode
from utils.enums import enumizy_name, generate_enums
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


def url_to_soup(url: str, filepath: str):
    if not os.path.exists(filepath):
        LOGGER.info(f"Fetching data from {url}")
        response = requests.get(url)
        if response.status_code != http.HTTPStatus.OK:
            LOGGER.warning(f"Ignoring response {response.status_code}: {response.text[:100]}")
            return None
        with open(filepath, "w") as output_file:
            output_file.write(response.text)

    with open(filepath, "r") as fp:
        return BeautifulSoup(fp, features="html.parser")


# TODO(generalize): This can be generalized into sth like (data -> url, url -> data)
def list_database_codes(seed_db_codes, codes_to_raw_names, recurse_level=3):
    """
    param orig_db_codes: starting list of db codes to scrape, e.g.: ["MEI", "QNA"]
    param code_to_name_map: to collect code to name mappings, e.g. "MEI: Main Economic Indicators Publication"
    param recurse_level: how many calls (including this one) should be called with new db codes.

    An alternative approach would be going though the list API, but getting the dataset codes is non-straightforward.
    # page_start = 0
    # page_size = 200
    # url = f"https://data.oecd.org/search-api/?hf={page_size}&b={page_start}&r=%2Bf%2Ftype%2Fdatasets%2Fapi+access&r=%2Bf%2Flanguage%2Fen&l=en&sl=sl_dp&sc=enabled%3Atrue%2Cautomatically_correct%3Atrue&target=st_dp"
    """

    all_db_codes = set()
    new_db_codes = set(seed_db_codes)
    safe_mkdir("data/html")
    for i in range(1, recurse_level+1):
        this_iter_db_codes = set()
        LOGGER.info(f"Iter {i}: Iterating through {len(new_db_codes)} new db codes")
        for j, db_code in enumerate(new_db_codes):
            if (j + 1) % 100 == 0:
                LOGGER.info(f"Iter {i}: Parsed {j}/{len(new_db_codes)} so far.")
            # Cache the fetch results to disk as it's rather slow to fetch again.
            db_code_filename = f"data/html/{db_code}.html"
            url = f"https://stats.oecd.org/Index.aspx?DatasetCode={db_code}"
            soup = url_to_soup(url, db_code_filename)
            if soup is None:
                continue

            codes_to_raw_names[db_code] = soup.title.text.strip()
            for link in soup.find_all("a"):
                url = link.get("href")
                if url is not None:
                    # Examples of URLs which we looking for:
                    # OECDStat_Metadata/ShowMetadata.ashx?DataSet=ITF_INDICATORS
                    # Index.aspx?DataSetCode=ITF_ROAD_ACCIDENTS
                    match = re.match(r'.*(DataSet[^"]*).*', url)
                    if match:
                        this_iter_db_codes.add(match.group(1).split("=")[1])

        new_db_codes = this_iter_db_codes.difference(all_db_codes)
        if len(new_db_codes) == 0:
            LOGGER.info(f"Iter {i}: No new db codes founds, returning the {len(all_db_codes)} db codes found.")
            return all_db_codes

        LOGGER.info(f"Iter {i}: Found {len(new_db_codes)} new db codes, first 10: {list(new_db_codes)[:10]}")
        all_db_codes.update(new_db_codes)

    LOGGER.info(f"Max recursion {recurse_level} reached, returning the {len(all_db_codes)} db codes found.")
    return list(all_db_codes)


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

# ==== Initial run
# db_code_manual_list = ["MEI", "MEI_CLI", "SNA", "HEALTH_STATE", "CRSNEW", "NAAG", "SHA", "STLABOUR", "SOCX_AGG", "MSTI_PUB", "CITIES", "QNA", "PDB_GR", "IDD", "MIG", "PDB_LV", "LFS_SEXAGE_I_R", "REV", "PNNI_NEW", "PPPGDP", "GREEN_GROWTH", "AEI_OTHER", "WEALTH", "ULC_QUA", "RS_GBL", "EAG_NEAC", "AEA", "DUR_I", "EAG_TRANS", "AV_AN_WAGE", "GENDER_EMP", "JOBQ", "HH_DASH", "IDO", "AIR_GHG", "FIN_IND_FBS", "MATERIAL_R"]
# codes_to_raw_names = {}
# list_database_codes(db_code_manual_list, codes_to_raw_names, 3)
#
# # Transform into enum names
# name_to_values = {}
# for code, raw_name in sorted(codes_to_raw_names.items()):
#     name_to_values[enumizy_name(raw_name)] = code
# generate_enums({"DatabaseCode": name_to_values}, "enums/database_codes.py")

# ==== Download all the data omnomnomnom.
for year in range(2019, 2008, -1):
    LOGGER.info(f"Year: {year}")
    # for db_code in DatabaseCode:
    for db_code in ["MEI", "MEI_CLI", "SNA", "HEALTH_STATE", "CRSNEW", "NAAG", "SHA", "STLABOUR", "SOCX_AGG", "MSTI_PUB", "CITIES", "QNA", "PDB_GR", "IDD", "MIG", "PDB_LV", "LFS_SEXAGE_I_R", "REV", "PNNI_NEW", "PPPGDP", "GREEN_GROWTH", "AEI_OTHER", "WEALTH", "ULC_QUA", "RS_GBL", "EAG_NEAC", "AEA", "DUR_I", "EAG_TRANS", "AV_AN_WAGE", "GENDER_EMP", "JOBQ", "HH_DASH", "IDO", "AIR_GHG", "FIN_IND_FBS", "MATERIAL_R"]:
        dirpath = f"data/{db_code}"
        safe_mkdir(dirpath)

        get_and_store_dataset(
            db_code,
            filepath=f"{dirpath}/{year}.csv",
            start_period=Period(year=str(year)),
            content_type=ContentType.CSV
        )



