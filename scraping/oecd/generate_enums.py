import re
from http import HTTPStatus

import requests

from xml.etree import ElementTree

from utils.enums import EXTRA_PREFIX, generate_enums, titlezy_name
from utils.utils import safe_mkdir, set_basic_logging_config


set_basic_logging_config(__name__)


def parse_oecd_schema_response(response: requests.Response):
    """Parse enum raw_name and values from GetDataStructure XML response.
    Note: The other way to get this data is from the bottom of the JSON response on the /sdmx-json/data/ API.

    Structure:
    message:Header
      message:Prepared
    message:CodeLists
      structure:CodeList(id, agencyID)
        structure:Name(lang=en|fr).text
        structure:Code(value, parentCode)
          structure:Description(lang=en|fr)
    message:Concepts
      structure:Concept
        structure:Name(lang=en|fr).txt
    message:KeyFamilies
      structure:KeyFamily(id=<dataset>, agencyID)
        structure:Name(lang=en|fr).text<dataset.name>
    """
    if response.text.startswith("Semantic Error - Dataset not found"):
        raise FileNotFoundError("Response returned not found")

    namespaces = {
        "message": "http://www.SDMX.org/resources/SDMXML/schemas/v2_0/message",
        "structure": "http://www.SDMX.org/resources/SDMXML/schemas/v2_0/structure",
        "xml": "http://www.w3.org/XML/1998/namespace",
    }

    root = ElementTree.fromstring(response.text)

    master_model = "CodeList"
    model_to_name_to_values = {master_model: {}}
    code_lists_tag = root.find("message:CodeLists", namespaces)
    for code_list_tag in code_lists_tag:
        code_list_name_tag = code_list_tag.find(".//structure:Name[@xml:lang='en']", namespaces)
        model_name_raw = code_list_name_tag.text
        for common in ["_UNIT", "_POWERCODE", "_REFERENCEPERIOD", "_TIME_FORMAT"]:
            pos = model_name_raw.find(common)
            if pos >= 0:
                # Remove the starting f"{dataset}_" part:
                model_name_raw = model_name_raw[pos + 1:]

        # Remove the ending codelist and make it a nice name
        model_name = titlezy_name(model_name_raw.replace(" codelist", ""))

        model_to_name_to_values[master_model][code_list_tag.attrib["id"]] = model_name
        model_to_name_to_values[model_name] = {}

        for code_tag in code_list_tag.findall("structure:Code", namespaces):
            description_tag = code_tag.find(".//structure:Description[@xml:lang='en']", namespaces)
            name = description_tag.text
            # The special case of stuffs like 2015M06_100, otherwise would run into:
            # Exception: For QnaReferenceperiodCodelist: tried to override 2010M12_100 with 1993M12_100 for M12_100
            if name[:4].isdigit():
                name = EXTRA_PREFIX + name

            value = code_tag.attrib["value"]

            # TODO(entity): Once we allow relationships between, use: code_tag.attrib.get("parentCode")
            model_to_name_to_values[model_name][name] = value

    return model_to_name_to_values


enum_dir = "enums"
safe_mkdir(enum_dir)
# NOTE: Some Databases exist, but their schema is NOT present. E.g. MATERIAL_RESOURCES
datasets = ["AEA", "AEI_OTHER", "AIR_GHG", "AV_AN_WAGE", "CITIES", "DUR_I", "EAG_NEAC", "EAG_TRANS", "GENDER_EMP", "GREEN_GROWTH", "FIN_IND_FBS", "HH_DASH", "IDD", "JOBQ", "LFS_SEXAGE_I_R", "MATERIAL_RESOURCES:", "MEI", "MEI_CLI", "MIG", "MSTI_PUB", "NAAG", "PDB_GR", "PDB_LV", "PNNI_NEW", "PPPGDP", "REV", "RS_GBL", "QNA", "SHA", "SNA_TABLE1", "SNA_TABLE5", "SOCX_AGG", "STLABOUR", "ULC_QUA", "WEALTH"]
urls = [f"https://stats.oecd.org/restsdmx/sdmx.ashx/GetDataStructure/{dataset}" for dataset in datasets]
# TODO: Maybe use explanation sites like https://data.oecd.org/fdi/fdi-stocks.htm to generate doc-strings
#  for values. More ideas can be found by searching https://data.oecd.org/searchresults/
# TODO: Might have useful docustrings: https://www.oecd.org/els/health-systems/List-of-variables-OECD-Health-Statistics-2018.pdf

generate_enums(
    urls=urls,
    output_filepath=f"{enum_dir}/all.py",
    parse_response=parse_oecd_schema_response,
    ignore_status_codes=[HTTPStatus.BAD_REQUEST],
)

