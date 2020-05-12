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

from http import HTTPStatus
from urllib.parse import urlencode

from utils import MMEnum

MIN_YEAR = 1961
MAX_YEAR = 2019


class ComtradeException(Exception):
    pass


class ComtradeRetriableException(Exception):
    """Catch this to retry network / comtrade network failures."""
    pass


class ComtradeQueryTooBig(Exception):
    """Catch this to restrict filtering of your query (e.g. from AG6 to AG4, or all to Imports)."""
    pass


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

        @staticmethod
        def generate_years(start=MIN_YEAR, end=MAX_YEAR):
            return [str(year) for year in range(start, end+1, 1)]

        @staticmethod
        def generate_yearmonths(start_year=MIN_YEAR, end_year=MAX_YEAR):
            result = []
            for year in ComtradeClient.Period.generate_years(start_year, end_year):
                result.extend([f"{year}{month:0>2}" for month in range(1, 13)])
            return result

    class Frequency(MMEnum):
        ANNUAL = "A"
        MONTHLY = "M"  # Was not able to get any data from 2008 USA

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
        AG3 = "AG3"  # three-digit HS commodity codes  # This doesn't seem to get any results.
        AG4 = "AG4"  # four-digit HS commodity codes  # This is too much for USA 2008
        AG5 = "AG5"  # five-digit HS commodity codes
        AG6 = "AG6"  # six-digit HS commodity codes  # This is too much for Slovakia 2013

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

    def get_trade_data(
            self,
            output_filepath: str,
            partner="703",
            frequency=Frequency.ANNUAL,
            period=Period.NOW,
            classification_code=CommodityCode.AG4,
            row_limit=100000
    ):
        """
            Queries the UN COMTRADE GET API for the requested arguments and stores it locally into `output_filepath`.
            More features to come (see TODOs) around.

            :param frequency: TODO
            :param output_filepath: where to output the downloaded dataset in case of success.
            :param partner: UN country code of which trade data is requested
            :param period: See ComtradeClient.Period for possible values, note ALL can lead to "query too complex".
            :param classification_code: TODO
            :param row_limit: UN says that max is 100 000: https://comtrade.un.org/data/dev/portal#subscription
        """
        query_params = {
            # reporting area: WHO reported the trade to UNSD.
            "r": "all",
            # partner area.The area receiving the trade, based on the reporting areas data.
            "p": partner,
            "freq": frequency,
            "ps": period,
            "px": ComtradeClient.ClassificationCode.HS,  # classification scheme used
            "cc": classification_code,
            "rg": ComtradeClient.TradeFlow.ALL,  # imports / exports
            "type": ComtradeClient.TradeType.COMMODITIES,
            "fmt": ComtradeClient.OutputFormat.JSON,
            "max": row_limit,
            "head": ComtradeClient.HeadingFormat.MACHINE_READABLE,
        }
        url = ComtradeClient.API_BASE_URL + "?" + urlencode(query_params)
        self._logger.info(f"Sending GET request for url {url}")

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
            err_str = f"HTTP {response.status_code}: {response.content[:100]}"
            if response.status_code in [HTTPStatus.GATEWAY_TIMEOUT, HTTPStatus.REQUEST_TIMEOUT, HTTPStatus.CONFLICT]:
                raise ComtradeRetriableException(err_str)
            raise ComtradeException(err_str)

        content = json.loads(response.content)
        if "validation" not in content:
            raise ComtradeRetriableException(f"Validation object expected in response: {response.content[:100]}")

        v = content["validation"]

        # Maybe we can do sth with these.
        item_count = v["count"]["value"]
        if item_count > query_params["max"]:
            # This possibly leads into error 5003
            # TODO: Figure out if there is pagination, if Yes how to follow, if not how to bypass.
            self._logger.warning(f"item_count higher than max: {item_count} > {query_params['max']}")
        if item_count == 0:
            self._logger.warning("item_count is zero, this is likely unexpected")

        validation_status = v["status"]["value"]
        if validation_status != 0:  # name = "ok"
            # TODO: Better classify, and make it retriable with increased filtering (e.g. AG6 -> AG4, or YYYY to YYYYMM)
            # 5002: Query complexity: "your query is too complex. Please simplify.
            # 5003: Result too large: you do not have permissions to access such a large resultset
            # 5004: Invalid parameter: the selected query does not accept the passed option.
            self._logger.error(f"Non-zero validation.status: {v}")
            raise ComtradeQueryTooBig(v["message"])

        self._logger.info(f"{v}")
        query_duration = v["count"]["durationSeconds"]
        dataset_timer = v["datasetTimer"]["durationSeconds"] if "datasetTimer" in v and v["datasetTimer"] else None

        self._logger.info(
            f"  Validated response, item count: {item_count}, UN query time: {query_duration}, " +
            f"UN datasetTimer: {dataset_timer}",
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



































