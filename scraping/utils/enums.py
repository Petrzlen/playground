import logging
import re
import requests
from slugify import slugify

from http import HTTPStatus

LOGGER = logging.getLogger(__name__)
EXTRA_PREFIX = "VAL_"


def titlezy_name(name: str) -> str:
    """From 'Some_GARBAGE-str blah' creates SomeGarbageStrBlah, good for class names."""
    return re.sub(r'[-/ ]', "", name.replace("_", " ").title())


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
    upper_slug = slugify(name).upper().replace("-", "_").replace("/", "_")
    # We could've made this RegEx part of replace_pairs, but unsure how it deals with non-ASCII starting characters.
    # Enums names must start with a letter.
    name = re.sub(r"^[^a-zA-Z]*", "", upper_slug)
    # The case when there are no [^a-zA-Z] in the whole string.
    if len(name) == 0:
        return EXTRA_PREFIX + upper_slug
    return name


def generate_enums(
    urls,
    output_filepath,
    parse_response,
    include_header=True,
    name_transform=None,
    ignore_status_codes=None,
):
    """Generate Enum `model_name` from Entities merged from `urls` written into `output_file`.

    :param urls: merge all key/values from these urls
    :param output_filepath: where to write (BEWARE: Default is to override existing files)
    :param parse_response: function from requests.Response to a dict(ModelName -> tuple(emum name, enum value)).
    :param include_header: useful when generating multiple Enum models into the same file (good for brief ones).
    :param name_transform: additional transformation on name = name_transform(name, value)
    :param ignore_status_codes: if present, the results with these HTTP status code will be ignored
    :return: Exception in case of error.
    """
    LOGGER.info(f"Generating enums from {len(urls)} urls to {output_filepath}")

    model_to_name_to_values = {}
    longest_name = ""
    for url in urls:
        LOGGER.info(f"Fetching data from {url}")
        response = requests.get(url)
        if response.status_code != HTTPStatus.OK:
            err_msg = f"Non 200 status code {response.status_code} for {url}"
            if ignore_status_codes and response.status_code in ignore_status_codes:
                LOGGER.warning(f"Ignoring response {response.status_code} as in ignore list: {response.text[:100]}")
                continue
            # TODO HTTP 400 from OECD means database not found, this is a too general place to be at.
            if response.status_code in [HTTPStatus.BAD_REQUEST, HTTPStatus.NOT_FOUND]:
                raise FileNotFoundError(err_msg)
            raise Exception(err_msg)
        LOGGER.info("... Fetching done.")

        data = parse_response(response)
        # Merge it with existing
        for model_name, name_values in data.items():
            if model_name not in model_to_name_to_values:
                model_to_name_to_values[model_name] = {}
            for raw_name, value in name_values.items():
                # Transform
                name = enumizy_name(raw_name)
                if len(name) > len(longest_name):
                    longest_name = name
                if name_transform:
                    name = name_transform(name, value)

                # Store
                orig_value = model_to_name_to_values[model_name].get(name, None)
                if orig_value and orig_value != value:
                    # Meaning the caller is mapping two different values into the same id.
                    # TODO, maybe generate a backup name for it? E.g. VAR_1, VAR_2, ... .
                    # raise Exception(
                    LOGGER.warning(
                        f"For {model_name}: tried to override {orig_value} with {value} for {name}({raw_name})"
                    )
                model_to_name_to_values[model_name][name] = value

    with open(output_filepath, "w") as output_file:
        if include_header:
            output_file.write(f"# Generated by `python3 {__name__}`, DO NOT CHANGE, change the generator script\n")
            output_file.write(f"from utils.utils import MMEnum\n")

        for model_name, name_values in model_to_name_to_values.items():
            LOGGER.info(f"Generating {model_name} with {len(name_values)} values")

            output_file.write(f"\n\nclass {model_name}(MMEnum):\n")
            # TODO: Maybe append a docstring from the generator metadata.
            for name, value in name_values.items():
                output_file.write(f"    {name} = \"{value}\"\n")

            LOGGER.info("... Generating done.")

        output_file.write("\n")

    # Print some fun-facts lol
    LOGGER.info(f"Longest name was: {longest_name}")
