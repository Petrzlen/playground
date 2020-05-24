import logging
import os
import sys
import time

from enum import Enum


# TODO: Will need dictionary from values to name.
class MMEnum(Enum):
    """So the enum values are 'value' instead of '<class Blah: ...>' """
    # https://stackoverflow.com/questions/24487405/enum-getting-value-of-enum-on-string-conversion
    def __str__(self):
        return str(self.value)


def format_money(amount):
    # https://stackoverflow.com/questions/1823058/how-to-print-number-with-commas-as-thousands-separators
    # return locale.format("$%d", amount, grouping=True)  # for non-american
    return f"${amount:,}"


def safe_mkdir(directory):
    if not os.path.exists(directory):
        os.mkdir(directory)


def print_and_sleep(seconds, logger=None):
    if logger:
        logger.info(f"Sleeping for {seconds}")
    else:
        print(f"Sleeping for {seconds}")

    time.sleep(seconds)


def set_basic_logging_config(name):
    logging.basicConfig(
        stream=sys.stdout,
        level=logging.INFO,
        format="%(asctime)s %(levelname)-8s %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    return logging.getLogger(name)

