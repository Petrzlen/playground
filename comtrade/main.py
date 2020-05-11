# TODO: import pytest

import logging
import sys

from comtrade_client import ComtradeClient
from comtrade_enums import Country

logging.basicConfig(stream=sys.stdout, level=logging.INFO)

client = ComtradeClient()
for year in ComtradeClient.Period.generate_years(1991):
    client.get_trade_data(
        output_filepath=f"data/slovakia_{year}.json",
        partner=Country.SLOVAKIA,
        period=year,
    )
