Yet another Downloader for [UN Comtrade](https://comtrade.un.org/data/doc/api/get) (Itemized Imports/Exports per Country).

Difference to existing?
1. The code was written to be very explicit and robust,
using Documentation with shared learnings, Exceptions, Enums, Retries and Rate Limits for best results. 
2. It features a *Guessing Game*! For a random product, bet who is the biggest exporter to your country!

BEWARE: It takes days to download it (unless you deploy it on multiple IPs), 
since the [Bulk API is only for Premium users](https://comtrade.un.org/data/doc/api/bulk/#DataRequests).

### Usage
```
pip install -r requirements
# To scrape it (set list of needed countries / periodsd)
python3 main.py
# Some geeky fun!
python3 guessing_game.py
```

### Contributing
Hit me up with a question, feature or a pull request!

### Learnings
* There is a LOT of already classified products by International Customs, one my favorites is named:
`ODORIFEROUS_SUBSTANCES_AND_MIXTURES_INCLUDING_ALCOHOLIC_SOLUTIONS_WITH_A_BASIS_OF_ONE_OR_MORE_OF_THESE_SUBSTANCES_OF_A_KIND_USED_AS_RAW_MATERIALS_IN_INDUSTRY_OTHER_PREPARATIONS_BASED_ON_ODORIFEROUS_SUBSTANCES_OF_A_KIND_USED_FOR_BEVERAGE_MANUFACTURE`
* Failed to get an AuthToken, the site is hard to navigate, or links are dead. <https://comtrade.un.org/api/swagger/ui/index#!/Auth/Auth_Authorize>

### Glossary
* AES (Automated Export System): shipments over $2500 or licensed. WCO.
* BEC (Broad Econimic Categories): [full list](https://comtrade.un.org/Data/cache/classificationBEC.json).
* EB02 (Extended Balance of Payments Services Classification): HS for services, [full list](https://comtrade.un.org/Data/cache/classificationEB02.json).
* HS (Harmonized System): product/service codes, administered by WCO, updated every 5y.
* IMTS ()
* Schedule B Code (WCO): TODO: seems like HS categorization
* SITC (Standard International Trade Classification)
* SIC (UK Tariff Codes): [link](https://data.gov.uk/dataset/8c68d3d1-e506-4f50-835d-949c974aa4ad/uk-tariff-codes)
* WCO (World Customs Organizaton)

### Useful Links
* Very nice slice and dice visualization from [OCE](https://oec.world/en/visualize/tree_map/hs92/export/svk/show/8703/2017/)
* Nice visualization for relations between countries from [GED](https://viz.ged-project.de/?lang=en)