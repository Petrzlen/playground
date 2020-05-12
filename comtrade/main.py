# TODO: Generate useful Country lists (like G20, EU, Asia, Africa...).

import logging
import sys

from comtrade_client import ComtradeClient, ComtradeRetriableException
from comtrade_enums import Country
from utils import safe_mkdir

logging.basicConfig(stream=sys.stdout, level=logging.INFO)

client = ComtradeClient()
# for partner in [Country.USA, Country.GERMANY, Country.CHINA, Country.CZECHIA]:
for partner in Country:
    # TODO: Remove the below filter.
    if partner in [Country.ALL, Country.SLOVAKIA] or str(partner.name) < str(Country.UKRAINE.name):
        print(f"Skipping country {partner.name}")
        continue

    directory = f"data/{partner.name.lower()}"
    safe_mkdir(directory)

    for period in ComtradeClient.Period.generate_years(2019, 2019):
        def get_trade_data():
            client.get_trade_data(
                output_filepath=f"{directory}/{period}.json",
                partner=partner,
                frequency=ComtradeClient.Frequency.ANNUAL,
                period=period,
                classification_code=ComtradeClient.CommodityCode.AG2,
            )

        # TODO: Use decreasing sized arggroups with RetriableException to get maximum possible granularity.
        try:
            get_trade_data()
        except ComtradeRetriableException:
            print(f"Retrying once for {partner.name} for {period}")
            get_trade_data()
