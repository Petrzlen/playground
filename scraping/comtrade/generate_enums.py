import json
import logging
import requests
import sys

from utils.enums import generate_enums
from utils.test import assert_equal
from utils.utils import safe_mkdir


logging.basicConfig(stream=sys.stdout, level=logging.INFO)


def classification_name_transform(name, value):
    if len(name) > 50:
        name = name[:30] + "___" + name[-17:]
    return name + "_" + value


def parse_comtrade_schema_response(response: requests.Response):
    response_results = json.loads(response.content)
    raw_name_to_values = {}
    for r in response_results["results"]:
        raw_name_to_values[r["text"]] = r["id"]
    return raw_name_to_values


# Inline tests
assert_equal(
    classification_name_transform("HORSES_LIVE_OTHER_THAN_PURE_BRED_BREEDING_ANIMALS", "010119"),
    "HORSES_LIVE_OTHER_THAN_PURE_BRED_BREEDING_ANIMALS_010119"
)
assert_equal(
    classification_name_transform("POULTRY_LIVE_DUCKS_GEESE_TURKEYS_AND_GUINEA_FOWLS_WEIGHING_MORE_THAN_185", "010599"),
    "POULTRY_LIVE_DUCKS_GEESE_TURKE___ING_MORE_THAN_185_010599"
)

# REAL DEAL
enum_dir = "enums"
safe_mkdir(enum_dir)
with open(f"{enum_dir}/country.py", "w") as output_file:
    # Merge partner/reporter Areas for one comprehensive list of Countries.
    generate_enums(
        urls=[
            "https://comtrade.un.org/Data/cache/partnerAreas.json",
            "https://comtrade.un.org/data/cache/reporterAreas.json",
        ],
        model_name="Country",
        output_file=output_file,
        parse_response=parse_comtrade_schema_response,
    )

# classification_dir = f"{enum_dir}/classification"
# safe_mkdir(classification_dir)
# classification_list = ["HS", "H0", "H1", "H2", "H3", "H4", "ST", "S1", "S2", "S3", "S4", "BEC", "EB02"]
#
# # TODO: Long-term make this is a tree-like class structure, long-long term have an entity service.
# # TODO: Short-tem maybe shorten the names and add the code to it, it's kinda useless when over 30 chars.
# for class_system in classification_list:
#     with open(f"{classification_dir}/{class_system}.py", "w") as output_file:
#         generate_enums(
#             urls=[f"https://comtrade.un.org/Data/cache/classification{class_system}.json"],
#             model_name=class_system,
#             output_file=output_file,
#             parse_response=parse_comtrade_schema_response,
#             name_transform=classification_name_transform,
#         )

