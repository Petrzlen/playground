# TODO: Manage to get all the data (learn to run from multiple IPs).
# TODO: Add models for Countries (oo Czechoslovakia), Products (merge Comm, Services)
#       Subtask: Figure out how to convert / align different classification schemes.
# TODO: Add black formatting.
# TODO: Somehow get Token, "You don't have enough right to access this page ... "
#       https://comtrade.un.org/data/doc/api/#APIKey
# TODO: Refactor when writing a second scraper, now just get the data.

import json
import logging
import requests
import time

from enum import Enum
from http import HTTPStatus
from urllib.parse import urlencode


# ============== General utils
class MMEnum(Enum):
    # https://stackoverflow.com/questions/24487405/enum-getting-value-of-enum-on-string-conversion
    def __str__(self):
        return str(self.value)


# ============== Real deal
# TODO: Explore BULK download, since we want to get all of the Data:
#       https://comtrade.un.org/data/doc/api/bulk/#DataRequests
class ComtradeClient:
    """
    ComtradeClient implements a subset of UNs Public API https://comtrade.un.org/data/doc/api/#APIKey

    BEWARE of the following usage limits:
    - Rate limit (guest): 1 request every second (per IP address or authenticated user).
    - Rate limit (authenticated): 1 request every second (per IP address or authenticated user).
    - Usage limit (guest): 100 requests per hour (per IP address or authenticated user).
    - Usage limit (authenticated): 10,000 requests per hour (per IP address or authenticated user).

    Parameter combination limits:
    - ps, r and p are limited to 5 codes each.
    - Only one of the above codes may use the special ALL value in a given API call.
    - Classification codes (cc) are limited to 20 items. ALL is always a valid classification code.
    """
    API_BASE_URL = "https://comtrade.un.org/api/get"
    _logger = logging.getLogger("ComtradeClient")

    # You can also pass in "YYYY", "YYYYMM" like 201911
    class Period(MMEnum):
        NOW = "now"
        RECENT = "recent"
        ALL = "all"

    class Frequency(MMEnum):
        ANNUAL = "A"
        MONTHLY = "M"

    class TradeFlow(MMEnum):
        # https://comtrade.un.org/data/cache/tradeRegimes.json
        ALL = "all"
        IMPORTS = "1"
        EXPORTS = "2"
        RE_EXPORTS = "3"  # TODO what is this?
        RE_IMPORTS = "4"

    class ClassificationCode(MMEnum):
        HS = "HS"
        HS_0_1992 = "H0"
        HS_1_1996 = "H1"
        HS_2_2002 = "H2"
        HS_3_2007 = "H3"
        HS_4_2012 = "H4"
        SITC = "ST"
        SITC_1 = "S1"
        SITC_2 = "S2"
        SITC_3 = "S3"
        SITC_4 = "S4"
        BEC = "BEC"
        EB02 = "EB02"

    # TODO: Many more, depends on ClassificationCode, also services.
    class CommodityCode(MMEnum):
        AGGREGATED = "total"  # aggregated
        ALL = "all"
        AG1 = "AG1"  # one-digit HS commodity codes
        AG2 = "AG2"  # two-digit HS commodity codes
        AG3 = "AG3"  # three-digit HS commodity codes
        AG4 = "AG4"  # four-digit HS commodity codes
        AG5 = "AG5"  # five-digit HS commodity codes
        AG6 = "AG6"  # six-digit HS commodity codes

    class OutputFormat(MMEnum):
        # USE_REQUEST_HEADER = None
        CSV = "csv"
        JSON = "json"

    class TradeType(MMEnum):
        COMMODITIES = "C"
        SERVICES = "S"

    class HeadingFormat(MMEnum):
        HUMAN_READABLE = "H"
        MACHINE_READABLE = "M"  # Matches JSON field names.

    # TODO add a merged enum: from https://comtrade.un.org/data/cache/reporterAreas.json
    #      and https://comtrade.un.org/data/cache/partnerAreas.json
    def get_trade_data(self, output_filepath: str, partner="703", row_limit=100000):
        """
            Queries the UN COMTRADE GET API for the requested arguments and stores it locally into `output_filepath`.
            More features to come (see TODOs) around.

            :param output_filepath: where to output the downloaded dataset in case of success.
            :param partner: UN country code of which trade data is requested
            :param row_limit: UN says that max is 100 000: https://comtrade.un.org/data/dev/portal#subscription
        """
        query_params = {
            # reporting area: WHO reported the trade to UNSD.
            "r": "all",  # 703 = Slovakia, 842 = USA
            # partner area.The area receiving the trade, based on the reporting areas data.
            "p": partner,
            "freq": ComtradeClient.Frequency.ANNUAL,
            "ps": ComtradeClient.Period.NOW,
            "px": ComtradeClient.ClassificationCode.HS,  # classification scheme used
            "cc": ComtradeClient.CommodityCode.AG6,  # result products classification code
            "rg": ComtradeClient.TradeFlow.ALL,  # imports / exports
            "type": ComtradeClient.TradeType.COMMODITIES,
            "fmt": ComtradeClient.OutputFormat.JSON,
            "max": row_limit,
            "head": ComtradeClient.HeadingFormat.MACHINE_READABLE,
        }
        url = ComtradeClient.API_BASE_URL + "?" + urlencode(query_params)
        self._logger.info(f"Sending GET request for url {url}, query params: {query_params}")

        start = time.time()
        response = requests.get(url)
        self._logger.info(
            f"  Received response {response.status_code} size={len(response.content)} in {time.time() - start} seconds"
        )

        dataset = self._parse_dataset(response, query_params)
        with open(output_filepath, "w") as output_file:
            json.dump(dataset, output_file)

    # TODO: Work on retry-able errors (like timeouts, rate limits and so).
    # TODO: Introduce specific errors.
    def _parse_dataset(self, response: requests.Response, query_params):
        if response.status_code != HTTPStatus.OK:
            raise Exception(f"  Problem occurred, non-OK response code: {response.status_code}")

        content = json.loads(response.content)
        if "validation" not in content:
            raise Exception("Validation object expected")

        v = content["validation"]
        validation_status = v["status"]["value"]
        if validation_status != 0:  # name = "ok"
            raise Exception(v["message"])

        # Maybe we can do sth with these.
        item_count = v["count"]["value"]
        if item_count > query_params["max"]:
            # TODO: Figure out if there is pagination, if Yes how to follow, if not how to bypass.
            self._logger.warning(f"item_count higher than max: {item_count} > {query_params['max']}")
        query_duration = v["count"]["durationSeconds"]
        fetch_duration = v["datasetTimer"]["durationSeconds"]
        self._logger.info(
            f"  Validated response, item count: {item_count}, UN query time: {query_duration}, " +
            f"UN fetch_duration: {fetch_duration}",
        )
        return content["dataset"]



# TODO: Result processing
#     {
#       "pfCode": "H5",
#       "yr": 2019,
#       "period": 2019,
#       "periodDesc": "2019",
#       "aggrLevel": 0,
#       "IsLeaf": 0,
#       "rgCode": 1,
#       "rgDesc": "Import",
#       "rtCode": 842,
#       "rtTitle": "USA",
#       "rt3ISO": "USA",
#       "ptCode": 0,
#       "ptTitle": "World",
#       "pt3ISO": "WLD",
#       "ptCode2": null,
#       "ptTitle2": "",
#       "pt3ISO2": "",
#       "cstCode": "",
#       "cstDesc": "",
#       "motCode": "",
#       "motDesc": "",
#       "cmdCode": "TOTAL",
#       "cmdDescE": "All Commodities",
#       "qtCode": 1,
#       "qtDesc": "No Quantity",
#       "qtAltCode": null,
#       "qtAltDesc": "",
#       "TradeQuantity": 0,
#       "AltQuantity": null,
#       "NetWeight": 0,
#       "GrossWeight": null,
#       "TradeValue": 2567492197103,
#       "CIFValue": null,
#       "FOBValue": null,
#       "estCode": 4
#     },



































