import datetime
import http
import json

import requests

from urllib.parse import urlencode
from xml.etree import ElementTree

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


# ==================== GENERATORS =========================
# TODO: This is likely easier to get from the SDMX-JSON response["structure"], which seems to have the same data.
# -> But lets do it this way, good exercise to learn XML (and to separate the queries).
def generate_schema(dataset):
    url = f"https://stats.oecd.org/restsdmx/sdmx.ashx/GetDataStructure/{dataset}"
    LOGGER.info(f"Getting schema definition: {url}")
    response = requests.get(url)
    if response.status_code != http.HTTPStatus.OK:
        raise Exception(f"Failed to fetch schema for dataset {dataset}: {response.status_code}")

    namespaces = {
        "message": "http://www.SDMX.org/resources/SDMXML/schemas/v2_0/message",
        "structure": "http://www.SDMX.org/resources/SDMXML/schemas/v2_0/structure",
        "xml": "http://www.w3.org/XML/1998/namespace",
    }
    # Structure:
    # message:Header
    #   message:Prepared
    # message:CodeLists
    #   structure:CodeList(id, agencyID)
    #     structure:Name(lang=en|fr).text
    #     structure:Code(value, parentCode)
    #       structure:Description(lang=en|fr)
    # message:Concepts
    #   structure:Concept
    #     structure:Name(lang=en|fr).txt
    # message:KeyFamilies
    #   structure:KeyFamily(id=<dataset>, agencyID)
    #     structure:Name(lang=en|fr).text<dataset.name>

    root = ElementTree.fromstring(response.text)
    # prepared = root.find("Prepared").text
    # print(prepared)

    for child in root:
        print(child.tag, child.attrib)
        for grandchild in child:
            print("  ", grandchild.tag, grandchild.attrib, grandchild.text)
            for ggchild in grandchild:
                print("    ", ggchild.tag, ggchild.attrib, ggchild.text)
                for gggchild in ggchild:
                    print("      ", gggchild.tag, gggchild.attrib, gggchild.text)


def generate_database_identifiers():
    # Go through pagination here
    # TODO: Export pagination into utils/crawling
    url = "https://data.oecd.org/search-api/?hf=20&b=80&r=f%2Ftype%2Fdatasets%2Fapi+access&r=%2Bf%2Ftype%2Fdatasets%2Fapi+access&r=%2Bf%2Flanguage%2Fen&l=en&sl=sl_dp&sc=enabled%3Atrue%2Cautomatically_correct%3Atrue&target=st_dp"


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
# generate_schema("QNA")

# TODO: Verify that the observation keys are keys into the structure(schema), e.g. "53:76:1:1:1"
# TODO: Figure out why there are so many values for an observation: [5242552.583,1,null,36,0,null]
# Looks like this:
# "dataSets": [{
#   "action": "Information",
#   "observations": {
#       "0:0:0:0:0": [29276700.0, 0, null, 0, 0, null],
#       "0:0:0:1:1": [28479600.0, 1, null, 0, 0, null],
#       ....
get_and_store_dataset("QNA", filepath="data/test.json", start_period=Period(year="2019"), content_type=ContentType.JSON)
# TODO: Normalize currencies.
# The CSV version is much more readable / parsable (also easier to merge multiple years).
# "JPN","Japan","GFSPB","Public sector","CARSA","","A","Annual","2019","2019","JPY","Yen","6","Millions",,,29276700,,
get_and_store_dataset("QNA", filepath="data/test.csv", start_period=Period(year="2019"), content_type=ContentType.CSV)



