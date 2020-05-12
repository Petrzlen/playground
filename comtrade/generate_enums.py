import json
import logging
import re
import requests
import sys

from http import HTTPStatus
from slugify import slugify

from utils import safe_mkdir


LOGGER = logging.getLogger("GenerateEnums")
logging.basicConfig(stream=sys.stdout, level=logging.INFO)


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


def classification_name_transform(name, value):
    if len(name) > 50:
        name = name[:30] + "___" + name[-17:]
    return name + "_" + value


def generate_enums(urls, model_name, output_file, include_header=True, name_transform=None):
    """Generate Enum `model_name` from Entities merged from `urls` written into `output_file`.

    :param urls: merge all key/values from these urls
    :param model_name: the class ModelName(Enum): part
    :param output_file: where to write (BEWARE: Default is to override existing files)
    :param include_header: useful when generating multiple Enum models into the same file (good for brief ones).
    :param name_transform: additional transformation on name = name_transform(name, value)
    :return: Exception in case of error.
    """
    LOGGER.info(f"Generating {model_name} to {output_file.name}")

    for url in urls:
        LOGGER.info(f"Fetching data from {url}...")
        response = requests.get(url)
        assert response.status_code == HTTPStatus.OK
        LOGGER.info(".. Fetching done.")

        results = json.loads(response.content)
        enum_pairs = {}
        for r in results["results"]:
            value = r["id"]
            name = enumizy_name(r["text"])
            if name_transform:
                name = name_transform(name, value)
            if name in enum_pairs and enum_pairs[name] == value:
                raise Exception(f"{name} already exists with value {value}, original string: {r['text']}")
            enum_pairs[name] = value

    if include_header:
        output_file.write(f"# Generated by `python3 {__name__}`, DO NOT CHANGE, change the generator script\n")
        output_file.write(f"from utils import MMEnum\n")

    output_file.write(f"\n\nclass {model_name}(MMEnum):\n")
    for name, value in enum_pairs.items():
        output_file.write(f"    {name} = \"{value}\"\n")
    output_file.write("\n")


# TESTS
def assert_equal(a: str, b: str):
    if a != b:
        raise Exception(f"'{a}' different from '{b}'")


assert_equal(enumizy_name("Africa CAMEU region, nes"), "AFRICA_CAMEU_REGION")
assert_equal(enumizy_name("Antigua and Barbuda"), "ANTIGUA_AND_BARBUDA")
assert_equal(enumizy_name("Bolivia (Plurinational State of)"), "BOLIVIA")
assert_equal(enumizy_name("Br. Indian Ocean Terr."), "BR_INDIAN_OCEAN_TERR")
assert_equal(enumizy_name("Côte d'Ivoire"), "COTE_D_IVOIRE")
assert_equal(enumizy_name("Dem. People's Rep. of Korea"), "DEM_PEOPLES_REP_OF_KOREA")
assert_equal(enumizy_name("Dem. People's Rep. of Korea"), "DEM_PEOPLES_REP_OF_KOREA")
assert_equal(enumizy_name("AG6 - All 6-digit HS commodities"), "AG6_ALL_6_DIGIT_HS_COMMODITIES")
assert_equal(
    enumizy_name("010119 - Horses; live, other than pure-bred breeding animals"),
    "HORSES_LIVE_OTHER_THAN_PURE_BRED_BREEDING_ANIMALS"
)
assert_equal(
    enumizy_name("010599 - Poultry; live, ducks, geese, turkeys and guinea fowls, weighing more than 185g"),
    "POULTRY_LIVE_DUCKS_GEESE_TURKEYS_AND_GUINEA_FOWLS_WEIGHING_MORE_THAN_185G"
)

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
    )

classification_dir = f"{enum_dir}/classification"
safe_mkdir(classification_dir)
classification_list = ["HS", "H0", "H1", "H2", "H3", "H4", "ST", "S1", "S2", "S3", "S4", "BEC", "EB02"]

# TODO: Long-term make this is a tree-like class structure, long-long term have an entity service.
# TODO: Short-tem maybe shorten the names and add the code to it, it's kinda useless when over 30 chars.
for class_system in classification_list:
    with open(f"{classification_dir}/{class_system}.py", "w") as output_file:
        generate_enums(
            urls=[f"https://comtrade.un.org/Data/cache/classification{class_system}.json"],
            model_name=class_system,
            output_file=output_file,
            name_transform=classification_name_transform,
        )

