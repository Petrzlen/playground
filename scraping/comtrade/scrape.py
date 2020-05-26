# TODO: Manage to get all the data (learn to run from multiple IPs).
# TODO: Add black formatting.
# TODO: Eventually: Use threadpools (instead of running it in multiple shells, note the shared rate limiting).
# TODO: Eventually: Use multiple IP Proxies for a more massive parallelization (to likely hit my frugal Comcast limits).

import json
import os
import requests
import time

import comtrade.api as api

from comtrade.enums.country import Country
from utils.utils import print_and_sleep, safe_mkdir, set_basic_logging_config

LOGGER = set_basic_logging_config("Comtrade")


def get_output_filepath(partner, period, **kwargs):
    safe_mkdir("data")

    directory = f"data/{partner.name.lower()}"
    safe_mkdir(directory)

    output_filepath = f"{directory}/{period}.json"
    # Idempotency check: Don't override existing (if messed up, you have to manually remove the file).
    if os.path.exists(output_filepath):
        return None
    return output_filepath


# TODO: Eventually create a fancier rate-limiting library.
request_count = 0
request_at = []


# The HOW
def scrape(params):
    global request_at, request_count

    # 1. Idempotency check
    output_filepath = get_output_filepath(**params)
    if output_filepath is None:
        LOGGER.info(f"  Skipping as output_filepath {output_filepath} is already present.")
        return

    # 2. Stats / Rate limit
    request_count += 1
    start = time.time()
    request_at.append(start)
    # Note the inside part of () is a generator. Minor optimization as list comprehension runs in a new func.
    request_count_last_hour = len(list(t for t in request_at if t > start - 3600))
    LOGGER.info(f"  RateLimit Hint: requests last hour: {request_count_last_hour}")

    # 3. Get Url
    url = api.create_url(**params)
    LOGGER.info(f"  Sending GET request for url {url}")

    # 4. Query for data
    try:
        response = requests.get(url)
    except requests.exceptions.ConnectionError as e:
        raise api.ComtradeRetriableException(e)
    # TODO: Pretty print content size
    LOGGER.info(f"  Received {response.status_code} size={len(response.content)} in {time.time() - start} seconds")

    # 5. Parse the dataset
    dataset = api.parse_dataset_from_response(response)

    # 6. Store the dataset
    with open(output_filepath, "w") as output_file:
        json.dump(dataset, output_file)


def scrape_with_retry(partner, period, classification_code, retry_count=0):
    params = {
        "partner": partner,
        "period": period,
        "classification_code": classification_code
    }
    for attempt in range(retry_count + 1):
        try:
            LOGGER.info(f"{partner.name}:{period} Scrape attempt {attempt+1}/{retry_count+1} with params {params}")
            scrape(params)
            break  # Success, nothing to do.
        except api.ComtradeRetriableException as e:
            if attempt < retry_count:
                LOGGER.warning(f"{partner.name},{period}: Retrying {retry_count - attempt} more times as exception: {e}")
                # There are odds we got rate-limited, so exponentially chill out for a while.
                # TODO(improvement): Use jitter (randomness) to exponential backoff: https://aws.amazon.com/blogs/architecture/exponential-backoff-and-jitter/
                print_and_sleep(2 ** attempt * 300, LOGGER)
            else:
                LOGGER.error(f"{partner.name},{period}: Retry failed, giving up. Exception: {e}")
                # This doesn't create the data file, so a re-run can fill it in.


# The WHAT
def scrape_all():
    # In case higher granularity is needed (likely not worth the 100-1500 second latency).
    # cc_to_try = [
    #   comtrade_api.CommodityCode.AG6,
    #   comtrade_api.CommodityCode.AG4,
    #   comtrade_api.CommodityCode.AG2,
    # ]
    # E.g. https://comtrade.un.org/api/get?r=all&p=703&freq=A&ps=2006&px=HS&cc=AG6&rg=all&type=C&fmt=json&max=100000&head=M
    # took a whopping 1258 seconds (91872 item count), although usually finishes in 100-200 seconds for AG6.
    cc_to_try = [api.CommodityCode.AG2]
    for partner in Country:
        if partner in [Country.ALL, Country.WORLD]:
            LOGGER.info(f"{partner.name}: Skipping blacklisted country")
            continue
        LOGGER.info(f"{partner.name}:========= START ==========")

        # Reset ClassificationCode granularity for every country, and if needed make it less granular to
        # fit into the row limit for the rest of the years.
        cc_i = 0
        for period in api.Period.generate_years(2007, 2018):
            while cc_i < len(cc_to_try):
                try:
                    scrape_with_retry(partner, period, cc_to_try[cc_i], retry_count=2)
                    break  # Success, nothing to do.
                except api.ComtradeResultTooLarge as e:
                    LOGGER.info(f"  Lowering granularity as {e}")
                    cc_i += 1

            if cc_i >= len(cc_to_try):
                LOGGER.error(f"C{partner.name}:{period} Cannot get data for as ResultTooLarge for every granularity.")
                cc_i = len(cc_to_try) - 1


# The DO IT
scrape_all()
