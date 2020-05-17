from utils.enums import enumizy_name
from utils.test import assert_equal


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
