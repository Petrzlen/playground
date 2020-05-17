import logging
import re
import requests
from slugify import slugify

from http import HTTPStatus

LOGGER = logging.getLogger(__name__)


def enumizy_name(name: str) -> str:
    replace_pairs = [
        (r"d'", "d "),
        (r"'s", "s"),
        (r", nes", ""),
        # (r"\(.*\)", ""),
        (r"\(Plurinational State of\)", "")
    ]
    for p in replace_pairs:
        name = re.sub(p[0], p[1], name)
    slug = slugify(name).upper().replace("-", "_")
    # We could've made this RegEx part of replace_pairs, but unsure how it deals with non-ASCII starting characters.
    # Enums names must start with a letter.
    return re.sub(r"^[^a-zA-Z]*", "", slug)


def generate_enums(urls, model_name, output_file, parse_response, include_header=True, name_transform=None):
    """Generate Enum `model_name` from Entities merged from `urls` written into `output_file`.

    :param urls: merge all key/values from these urls
    :param model_name: the class ModelName(Enum): part
    :param output_file: where to write (BEWARE: Default is to override existing files)
    :param parse_response: function from requests.Response to a dictionary of (raw emum name -> enum value).
    :param include_header: useful when generating multiple Enum models into the same file (good for brief ones).
    :param name_transform: additional transformation on name = name_transform(name, value)
    :return: Exception in case of error.
    """
    LOGGER.info(f"Generating {model_name} to {output_file.name}")

    for url in urls:
        LOGGER.info(f"Fetching data from {url}")
        response = requests.get(url)
        if response.status_code != HTTPStatus.OK:
            raise Exception(f"Non 200 status code {response.status_code} for {url}")
        LOGGER.info(".. Fetching done.")

        raw_name_to_values = parse_response(response)
        enum_pairs = {}
        longest_name = ""
        for raw_name, value in raw_name_to_values.items():
            name = enumizy_name(raw_name)
            if len(name) > len(longest_name):
                longest_name = name
            if name_transform:
                name = name_transform(name, value)
            if name in enum_pairs and enum_pairs[name] == value:
                raise Exception(f"{name} already exists with value {value}, original string: {r['text']}")
            enum_pairs[name] = value

        print(f"Longest name was: {longest_name}")

    if include_header:
        output_file.write(f"# Generated by `python3 {__name__}`, DO NOT CHANGE, change the generator script\n")
        output_file.write(f"from utils.utils import MMEnum\n")

    output_file.write(f"\n\nclass {model_name}(MMEnum):\n")
    for name, value in enum_pairs.items():
        output_file.write(f"    {name} = \"{value}\"\n")
    output_file.write("\n")
