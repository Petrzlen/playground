# The SDMX JSON API of OECD
This `oecd` dataset driver essentially implements a subset of [OECD's API](https://data.oecd.org/api/sdmx-json-documentation/), plus a few useful features:
* Get a list of all available databases through recursive scraping of their site, use `list_database_codes()`.
* List of all enum name/values from their schemas, you can re-generate it through `python3 generate_enums`

If you familiar with `pandas`, you might prefer to use [pandaSDMX](https://pandasdmx.readthedocs.io/en/v1.0/), 
for the data download and analysis part. The pandaSDMX also supports many more SDMX data sources than OECD (like FRED, IMF, ...).

## Some of datasets (whole list in enums/datasets.py)
The OECD datasets provide great variety of signals, especially on OECD countries, e.g. checkout [granularity on GDP](https://stats.oecd.org/Index.aspx?DatasetCode=SNA_TABLE1) and the list of datasets on the right.
A great sample of useful datasets can be found in OECDs publication: [How's Life? 2020 Measuring Well-being](https://books.google.com/books?id=bJLVDwAAQBAJ&pg=PA89#v=onepage&q&f=false) by OECD.
Below a sample of dataset codes I run into manually: 
* AEA
* AEI_OTHER (Anti Environment Indicators)
* AIR_GHG (Greenhouse Gas Emissions)
* AV_AN_WAGE (Average Annual Wages)
* CITIES (Metropolitan Areas)
* DUR_I (Unemployment by Duration)
* EAG_NEAC (Educational Attainment and Labour Force Status)
* EAG_TRANS (Transition from School to Work)
* GENDER_EMP (Gender Equality in Employment)
* GREEN_GROWTH
* FIN_IND_FBS (Financial Indicators - Stocks)
* HH_DASH (Household Dashboard)
* IDD (Income Distribution Database)
* JOBQ (Job Quality)
* LFS_SEXAGE_I_R (LFS (Labour Force Statistics) by Sex and Age): Transition from school to work.
* MATERIAL_RESOURCES: 
* MEI (Composite Leading Indicators)
* MEI_CLI
* MIG (International Migration Database)
* MSTI_PUB (Main Science and Technology Indicators)
* NAAG (National Account at a Glance)
* PDB_GR (Growth in GDP per capita)
* PDB_LV (Level of GDP per capita and Productivity)
* PNNI_NEW (Funded Pensions Indicator)
* PPPGDP
* REV (Revenue Statistics)
* RS_GBL
* QNA (Quarterly National Accounts)
* SHA (Health Expenditure and Financing)
* SNA_TABLE1 (GDP): There are a LOT of SNA tables.
* SNA_TABLE5 (National Accounts): 
* SOCX_AGG (Social Expenditure)
* STLABOUR (Short-Term Labour Market Statistics)
* ULC_QUA
* WEALTH


## Known limitation and implementation details (copied from OECD spec)
* Must be `https`
* Only anonymous queries are supported, there is no authentication
* TODO(shard): Each response is limited to 1 000 000 observations
* Maximum request URL length is 1000 characters
* Only the data resource is supported which returns data and relevant structural metadata. To obtain structural metadata on its own please use the SDMX-ML API
* Cross-origin requests are supported by `CORS` headers and `JSONP`
* Unlike some other implementations the default response content type is `application/vnd.sdmx.draft-sdmx-json+json;version=2.1`;
* Dimensions and attributes with only one requested value are not yet moved to dataset level even though the draft specification (see example message) would allow this
* TODO: Errors are not returned in the JSON format but HTTP status codes and messages are set according to the Web Services Guidelines
* TODO: 401 Unauthorized is returned if a non-authorised dataset is requested
* TODO: The source (or Agency ID) parameter in the REST query is mandatory but the `ALL` keyword is supported


## Data Structure
### JSON
From my naive understanding of SDMX,
the observation keys are keys into the structure(schema), e.g. `53:76:1:1:1`,
translates into the schema described the last par tof the response.
TODO: Figure out why there are so many values for an observation: [5242552.583,1,null,36,0,null]

Example:
```json
"dataSets": [{
  "action": "Information",
  "observations": {
      "0:0:0:0:0": [29276700.0, 0, null, 0, 0, null],
      "0:0:0:1:1": [28479600.0, 1, null, 0, 0, null],
      ....
}]
```
### CSV (Preferred by this project)
The CSV version is much more readable / parseable (also easier to merge multiple years). 

Example:
```text
"JPN","Japan","GFSPB","Public sector","CARSA","","A","Annual","2019","2019","JPY","Yen","6","Millions",,,29276700,,
```