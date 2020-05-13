# TODO: Generate useful Country lists (like G20, EU, Asia, Africa...).
# TODO: Use logger, Use time in logger, Use Exception
# TODO: Make it a part of ComtradeClient (e.g. the get_trade_data state / parameters are getting shady).
# TODO: Add black formatting.

import logging
import os
import sys
import time

from comtrade_client import ComtradeClient, ComtradeRetriableException, ComtradeResultTooLarge
from enums.country import Country
from utils import print_and_sleep, safe_mkdir

logging.basicConfig(stream=sys.stdout, level=logging.INFO)

# TODO: Make a fancier rate-limiting lib once it's needed more (more scrapers to come).
start = time.time()
request_count = 0
request_at = []

cc_to_try = [ComtradeClient.CommodityCode.AG4, ComtradeClient.CommodityCode.AG2]
client = ComtradeClient()
# for partner in reversed(Country.list_european_union()):
for partner in [Country.USA, Country.GERMANY, Country.CHINA, Country.CZECHIA]:
    # if partner in [Country.ALL, Country.SLOVAKIA] or str(partner.name) < str(Country.ANTIGUA_AND_BARBUDA.name):
    if partner in [Country.ALL, Country.SLOVAKIA]:
        print(f"Skipping country {partner.name}")
        continue
    print(f"============ Fetching country {partner.name} ============")

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
            print(f"Skipping existing {output_filepath}")
            continue

        def get_trade_data(cc, retry=False):
            global request_at, request_count
            request_count += 1
            now = time.time()
            request_at.append(now)
            # Note the inside part of () is a generator. Minor optimization as list comprehension runs in a new func.
            request_count_last_hour = len(list(t for t in request_at if t > now - 3600))
            print(f"RateLimit hint: requests last hour: {request_count_last_hour}")

            try:
                client.get_trade_data(
                    output_filepath=output_filepath,
                    partner=partner,
                    frequency=ComtradeClient.Frequency.ANNUAL,
                    period=period,
                    classification_code=cc,
                )
            except ComtradeRetriableException as e:
                if retry:
                    print(f"Retrying once for {partner.name} for {period} as exception: {e}")
                    print_and_sleep(240)  # There are odds we got rate-limited, so chill out for a while.
                    get_trade_data(cc, retry=False)
                else:
                    print(f"Retry failed, so giving up on {partner.name} for {period} as exception: {e}")
                    # This doesn't create the data file, so a re-run can fill it in.

        try:
            get_trade_data(classification_code)
        except ComtradeResultTooLarge as e:
            cc_previous = classification_code
            cc_i = min(len(cc_to_try) - 1, cc_i + 1)
            classification_code = cc_to_try[cc_i]
            print(f"Falling back from {cc_previous} to {classification_code} as {e}")
            # no change
            if cc_previous == classification_code:
                print(f"ERROR: Cannot get data for {partner.name} for {period} as no where to fall back.")
            else:
                # TODO: Support multiple fall-backs.
                get_trade_data(classification_code)
