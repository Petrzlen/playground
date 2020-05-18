import re
import requests

from xml.etree import ElementTree

from utils.enums import EXTRA_PREFIX, generate_enums
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
        # TODO: maybe drop the database name, e.g. QNA_REFERENCEPERIOD codelist -> REFERENCEPERIOD
        model_name = code_list_name_tag.text.replace("_", " ").title().replace(" ", "")

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
dataset = "QNA"

# Merge partner/reporter Areas for one comprehensive list of Countries.
generate_enums(
    urls=[f"https://stats.oecd.org/restsdmx/sdmx.ashx/GetDataStructure/{dataset}"],
    output_filepath=f"{enum_dir}/{dataset.lower()}.py",
    parse_response=parse_oecd_schema_response,
)