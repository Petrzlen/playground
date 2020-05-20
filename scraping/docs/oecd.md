# The SDMX JSON API of OECD
This `oecd` driver essentially implements a subset of [OECD's documentation](https://data.oecd.org/api/sdmx-json-documentation/).
If you familiar with `pandas`, you should prefer to use [pandaSDMX](https://pandasdmx.readthedocs.io/en/v1.0/) or learn it. It supports many more SDMX data sources than OECD.

They have a LOT of data on these countries. E.g. checkout [granularity on GDP](https://stats.oecd.org/Index.aspx?DatasetCode=SNA_TABLE1) and the list of datasets on the right.

## Known limitation and implementation details (copied from OECD spec)
* Must be `https`
* Only anonymous queries are supported, there is no authentication
* TODO: Each response is limited to 1 000 000 observations
* Maximum request URL length is 1000 characters
* Only the data resource is supported which returns data and relevant structural metadata. To obtain structural metadata on its own please use the SDMX-ML API
* Cross-origin requests are supported by `CORS` headers and `JSONP`
* Unlike some other implementations the default response content type is `application/vnd.sdmx.draft-sdmx-json+json;version=2.1`;
* Dimensions and attributes with only one requested value are not yet moved to dataset level even though the draft specification (see example message) would allow this
* TODO: Errors are not returned in the JSON format but HTTP status codes and messages are set according to the Web Services Guidelines
* TODO: 401 Unauthorized is returned if a non-authorised dataset is requested
* TODO: The source (or Agency ID) parameter in the REST query is mandatory but the `ALL` keyword is supported

UnitCodelist
PowercodeCodelist
ReferenceperiodCodelist
TimeFormatCodelist
CliUnitCodelist
CliPowercodeCodelist

## Some of datasets
A lot the codes (and potentially interesting stats) can be found in the [How's Life? 2020 Measuring Well-being](https://books.google.com/books?id=bJLVDwAAQBAJ&pg=PA89#v=onepage&q&f=false) by OECD.
Note: To conver this into `db_code_manual_list` just `awk '{print $2}' /tmp/stuff | xargs | sed 's/ /", "/g'`

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


#### (Storytime) History of my Exploration:
Or how I've got from Browser->Inspect Element and Curl to pandaSDMX.

##### First Chapter
My first try was much more complicated, and would need extra `curl` commands to link the `WEALTH` dataset somehow into the `ASP.NET_Session_Id` (you can observe that although the below command gets you the csv (sometimes in gzip), it has NO identifier which dataset you getting). 
```
# -v verbose
# -O last part of URL as filename
# -o output.csv
echo "Curling"
curl -v -o "output3.csv" \
"https://stats.oecd.org/Download.ashx?type=csv&Delimiter=%2c&IncludeTimeSeriesIdentifiers=False&LabelType=CodeAndLabel&LanguageCode=en" \
 -H"Host: stats.oecd.org" \
 -H"Connection: keep-alive" \
 -H"Cache-Control: max-age=0" \
 -H"Upgrade-Insecure-Requests: 1" \
 -H"User-Agent: Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Ubuntu Chromium/81.0.4044.138 Chrome/81.0.4044.138 Safari/537.36" \
 -H"Accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9" \
 -H"Sec-Fetch-Site: same-origin" \
 -H"Sec-Fetch-Mode: navigate" \
 -H"Sec-Fetch-User: ?1" \
 -H"Sec-Fetch-Dest: iframe" \
 -H"Accept-Encoding: gzip, deflate, br" \
 -H"Accept-Language: en-US,en;q=0.9" \
 -H"Cookie: ASP.NET_SessionId=1l3bjqhhybtymbbi5vyj1od5"
# Trying to make the header set as re-usable as possible (by removing specifics):
# -H"Referer: https://stats.oecd.org/modalexports.aspx?exporttype=bulk&FirstDataPointIndexPerPage=undefined&SubSessionId=c8892a66-41aa-41f4-8f58-6f3d408fb75c&Random=0.7738299555831478" \

# WUT: Somehow the extra cookis below make the result in GZIP (even though we have "Accept-Encoding: gzip, deflate, br")
# -H"Cookie: ASP.NET_SessionId=1l3bjqhhybtymbbi5vyj1od5; cX_S=kaa30l97w0xuhl5r; cX_P=kaa30l99bstzcn4x; _ga=GA1.2.248993569.1589660834; _gid=GA1.2.964676318.1589660834; _gat_UA-136634323-1=1; _ga=GA1.3.248993569.1589660834; _gid=GA1.3.964676318.1589660834; _gat=1; cX_G=cx%3Ar0xp8i9lz7df3w0xeeoy13tnw%3A1gyq4vvjaw04q"
# echo "Decompress with gzip"
# gzip -d output.csv.gz
```

The key finding was to inspect element on the **Download** form click and see the `application/x-www-form-urlencoded` form params on the `modalexports.aspx` pre query to reveal itself:
```
hiddenSdmxJsonUrl: https://stats.oecd.org/SDMX-JSON/data/WEALTH/AUS+AUT+BEL+CAN+CHL+DNK+EST+FIN+FRA+DEU+GRC+HUN+IRL+ITA+JPN+KOR+LVA+LUX+NLD+NZL+NOR+POL+PRT+SVK+SVN+ESP+GBR+USA.T1C5+MNWI+T3AC2+T3AC3+M2MR+T4C5+T4C4+T1C7+PIH+PIH75+PIHR3+T6C2+T6C3+T6C6+T6C7+ST1+ST5+ST10+SB60.TP/all?startTime=2009&endTime=2016
```
Which then lead me to the [SDMX-JSON documentation](https://data.oecd.org/api/sdmx-json-documentation/) :facepalm:. 

##### Second Chapter
Was trying to generate schema from the SDMX spec,
gave up and went into downloading it,
had troubles understanding the results, so yet again a query of "Python SDMX" lead to `pandaSDMX`, which seems to have all this functionality already implemented.