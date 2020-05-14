# TODO: Make it a part of ComtradeClient (e.g. the get_trade_data state / parameters are getting shady).
# TODO: Add black formatting.
# TODO: Use threadpools (instead of running it in multiple shells, note the shared rate limiting).
# TODO: Use multiple IP Proxies for a more massive parallelization (to likely hit my frugal Comcast limits).

import logging
import os
import sys
import time

from comtrade_client import ComtradeClient, ComtradeRetriableException, ComtradeResultTooLarge
from enums.country import Country
from utils import print_and_sleep, safe_mkdir

logging.basicConfig(
    stream=sys.stdout,
    level=logging.INFO,
    format="%(asctime)s %(levelname)-8s %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
LOGGER = logging.getLogger("Controller")

# TODO: Make a fancier rate-limiting lib once it's needed more (more scrapers to come).
start = time.time()
request_count = 0
request_at = []

cc_to_try = [ComtradeClient.CommodityCode.AG4, ComtradeClient.CommodityCode.AG2]
client = ComtradeClient()
safe_mkdir("data")
for partner in Country.list_g20():
    if partner in [Country.ALL]:
        LOGGER.info(f"Skipping blacklisted country {partner.name}")
        continue
    LOGGER.info(f"============ Fetching country {partner.name} ============")

    directory = f"data/{partner.name.lower()}"
    safe_mkdir(directory)

    # When going through years incrementally, it's very unlikely that a more granular classification would work
    # in T + N, if it didn't in T. So reset it for each country, and only keep it while it works.
    cc_i = 0
    classification_code = cc_to_try[cc_i]
    for period in ComtradeClient.Period.generate_years(2007, 2018):
        output_filepath = f"{directory}/{period}.json"
        # Don't override existing (if messed up, you have to manually remove the file)
        if os.path.exists(output_filepath):
            LOGGER.info(f"Skipping existing {output_filepath}")
            continue

        def get_trade_data(cc, retry_count=2):
            global request_at, request_count
            request_count += 1
            now = time.time()
            request_at.append(now)
            # Note the inside part of () is a generator. Minor optimization as list comprehension runs in a new func.
            request_count_last_hour = len(list(t for t in request_at if t > now - 3600))
            LOGGER.info(f"RateLimit Hint: requests last hour: {request_count_last_hour}")

            try:
                client.get_trade_data(
                    output_filepath=output_filepath,
                    partner=partner,
                    frequency=ComtradeClient.Frequency.ANNUAL,
                    period=period,
                    classification_code=cc,
                )
            except ComtradeRetriableException as e:
                if retry_count > 0:
                    LOGGER.info(f"Retrying {retry_count} times for {partner.name} for {period} as exception: {e}")
                    # There are odds we got rate-limited, so chill out for a while.
                    print_and_sleep(2 ** (2 - retry_count) * 300)
                    get_trade_data(cc, retry_count=retry_count - 1)
                else:
                    LOGGER.info(f"Retry failed, so giving up on {partner.name} for {period} as exception: {e}")
                    # This doesn't create the data file, so a re-run can fill it in.

        try:
            get_trade_data(classification_code)
        except ComtradeResultTooLarge as e:
            cc_previous = classification_code
            cc_i = min(len(cc_to_try) - 1, cc_i + 1)
            classification_code = cc_to_try[cc_i]
            LOGGER.info(f"Falling back from {cc_previous} to {classification_code} as {e}")
            # no change
            if cc_previous == classification_code:
                LOGGER.error(f"Cannot get data for {partner.name} for {period} as no where to fall back.")
            else:
                # TODO: Support multiple fall-backs.
                get_trade_data(classification_code)
