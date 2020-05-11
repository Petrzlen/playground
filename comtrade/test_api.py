# TODO: import pytest

import logging
import sys

from scrape import ComtradeClient

logging.basicConfig(stream=sys.stdout, level=logging.INFO)
client = ComtradeClient()
client.get_trade_data(output_filepath="data/slovakia_2019.json", partner="703")
