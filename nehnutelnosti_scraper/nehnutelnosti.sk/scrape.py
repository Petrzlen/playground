"""
Url templates:
https://www.nehnutelnosti.sk/banska-bystrica/3-izbove-byty/prenajom/

Typ:
predaj,prenajom

Paging:


Relevant info:
advertisement-price-panel-unit-price: /m^2 both predaj, prenajom

TODOs:
FIGURE OUT THEIR RATE LIMIT POLICIES

fetched(status=200,retry=True) https://www.nehnutelnosti.sk/brezno/byty/predaj/
log: cannot find inzeraty
Most Likely: <noscript>Please enable JavaScript to view the page content.</noscript> 

https://www.nehnutelnosti.sk/kosice/byty/predaj/?p[page]=5
error: cannot parse price:  [''] could not convert string to float

error:  HTTPSConnectionPool(host='www.nehnutelnosti.sk', port=443): Max retries exceeded with url: /kosice/byty/predaj/?p%5Bpage%5D=11 (Caused by NewConnectionError('<urllib3.connection.VerifiedHTTPSConnection object at 0x10ab78908>: Failed to establish a new connection: [Errno 8] nodename nor servname provided, or not known',))
"""

import json
import requests
from requests_html import HTMLSession
import re
import statistics
import time
from lxml import html, etree
from http import HTTPStatus

# DRUH = "3-izbove-byty"
DRUH = "byty"
HTML_SESSION = HTMLSession()

def construct_url(district, DRUH, action, page=None):
    if page is None or page == 1:
        return 'https://www.nehnutelnosti.sk/{}/{}/{}/'.format(
            district, DRUH, action
        )
    return 'https://www.nehnutelnosti.sk/{}/{}/{}/?p[page]={}'.format(
        district, DRUH, action, page
    )

def has_needed_content(content):
    # TODO improve this 
    # str(content).find('id="inzeraty"') != -1
    return True

# Retry logic as sometimes timeout
def get_save_tree(
    url,
    filename,
    retry=True,
    patience=10,
) :
    global HTML_SESSION

    resp = requests.get(url)
    content = resp.content
    status = resp.status_code

    """
    # http://theautomatic.net/2019/01/19/scraping-data-from-javascript-webpage-python/
    try: 
        resp = HTML_SESSION.get(url)
        resp.html.render()
        content = resp.html.html
        status = HTTPStatus.OK
    except Exception as e:
        print('error: ', e)
        HTML_SESSION = HTMLSession()
        if retry:
            print("sleeping to retry")
            time.sleep(3)
            return get_save_tree(url, filename, False)
        else:
            return None
    """
        

    print("fetched(status={},retry={})".format(status, retry), url)
    if status != HTTPStatus.OK or not has_needed_content(content):
        if retry:
            print("sleeping(15) to retry")
            time.sleep(15)
            return get_save_tree(url, filename, False)
        else:
            print("already retried too many")
            return None
       
    # TODO only save it if bigger (otherwise replaced with JSON)
    if filename:
        with open('data/html/{}.html'.format(filename), 'w') as f:
            f.write(str(content))

    return html.fromstring(content)


class Listing:
    def __init__(self, druh, action, full_price, per_square, total_square, url, location):
        self.druh = druh
        self.action = action
        self.full_price = full_price
        self.total_square = total_square
        self.per_square = per_square
        self.url = url
        self.location = location

    def toJSON(self):
        return self.__dict__
   
def xpath_result_prep(xpath_result):
    if isinstance(xpath_result, list):
        if len(xpath_result) == 0:  
            return None
        return xpath_result_prep(xpath_result[0])
    if not isinstance(xpath_result, str):
        return None
    return xpath_result

# 1 345,56 €/m&sup2
# returns: the float part
def parse_price(raw_price):
    raw_price = xpath_result_prep(raw_price)
    if raw_price is None:
        return None
    raw_price = raw_price.strip()
    findings = re.findall('^[0-9 ,]*', raw_price)
    if len(findings) != 1:
        return None
    try:
        result = float(findings[0].replace(' ', '').replace(',', '.'))
    except Exception as e:
        print('error: cannot parse price: ', findings, e)
        return None
    return result

# "[0-9]{2-3} m^2", "1454 m²"
def parse_square(raw_square):
    raw_square = xpath_result_prep(raw_square)
    if raw_square is None:
        return None
    findings = re.findall('^[0-9]*', raw_square.strip())[0]
    if len(findings) != 1:
        return None
    return int(findings[0])

def parse_url(raw_url):
    raw_url = xpath_result_prep(raw_url)
    if raw_url is None:
        return None
    return raw_url.strip()

def parse_location(raw_location):
    raw_location = xpath_result_prep(raw_location)
    if raw_location is None:
        return None
    return raw_location.strip()

def parse_tree(tree, druh, action):
    if tree is None:
        return []
    CLASS_INZERAT_1 = "advertisement-box-image-main default-column-1 mx-auto mb-4"
    CLASS_INZERAT_2 = "advertisement-box-image-main highlight highlight-column-3 mx-auto mb-4"
    CLASS_DIV = "d-flex align-items-stretch flex-column align-self-stretch w-100"
    CLASS_FULL = "col-auto pl-0 pl-md-3 pr-0 advertisement-price-panel text-right mt-2 mt-md-0 align-self-end"
    # CLASS_FULL = "advertisement-price-panel"
    CLASS_PER_SQUARE = "advertisement-price-panel-unit-price"
    CLASS_TOTAL_SQUARE = "location-text"
    CLASS_URL = "d-block text-truncate"  # href
    CLASS_LOCATION = "location-text d-block text-truncate"  # title
    # CLASS_LOCATION = "location-text"

    listings = []
    inzeraty = tree.xpath('//div[@class="advertisement-component"]')
    if len(inzeraty) == 0:
        print("log: cannot find inzeraty")
        return listings
    print(len(inzeraty[0]))

    for inzerat in inzeraty[0]:
        inzerat_class = str(inzerat.get("class"))  # can be NoneType
        if inzerat_class not in [CLASS_INZERAT_1, CLASS_INZERAT_2]:
            print("log: skipping inzerat class " + inzerat_class)
            continue

        base_path = '//div[@class="{}"]/'.format(CLASS_DIV)
        full_price_path = base_path + 'div[2]/div/div[2]/text()[1]'
        raw_full_price = inzerat.xpath(full_price_path)
        raw_per_square = inzerat.xpath('//span[@class="{}"]/text()'.format(CLASS_PER_SQUARE))
        raw_total_square = inzerat.xpath('//div[@class="{}"]/span/text()'.format(CLASS_TOTAL_SQUARE))
        raw_url = inzerat.xpath('//a[@class="{}"]/@href'.format(CLASS_URL))
        raw_location = inzerat.xpath('//div[@class="{}"]/text()[2]'.format(CLASS_LOCATION))

        full_price = parse_price(raw_full_price),
        total_square = parse_square(raw_total_square)
        per_square = parse_price(raw_per_square)
        if per_square is None:
            if full_price is not None and total_square is not None:
                print(full_price, total_square)
                per_square = full_price / total_square

        if per_square is None:
            print("error: cannot compute per_square:", raw_full_price, raw_per_square, raw_total_square, raw_location, raw_url)
            continue


        listings.append(Listing(
            druh=druh,
            action=action,
            full_price=parse_price(raw_full_price),
            per_square=per_square,
            total_square=parse_price(raw_total_square),
            url=parse_url(raw_url),
            location=parse_location(raw_location),
        ))
    return listings
#    CLASS_DIV = "d-flex align-items-stretch flex-column align-self-stretch w-100"
#    base_path = '//div[@class="{}"]/'.format(CLASS_DIV)
#    full_price_path = base_path + 'div['


def get_listings_median(listings):
    prices = [l.per_square for l in listings]
    result = statistics.median(prices)
    print(result)
    return result

def get_all(district, druh, action, patience=5, retry=True):
    global HTML_SESSION
    print("sleeping", patience, "for patience")
    time.sleep(patience)
    # Recreate the session as a heuristic
    HTML_SESSION = HTMLSession()

    results = []
    for page in range(1, 100):
        url = construct_url(district, DRUH, action, page) 
        tree = get_save_tree(url, district + '-' + action + '-' + str(page))
        new_listings = parse_tree(tree, DRUH, action)
        if len(new_listings) == 0:
            break
        results.extend(new_listings)

    # There should be at least one result, give it an another try with more
    # patience:
    if retry and len(results) == 0:
        return get_all(district, druh, action, 30, retry=False)

    return results
    

class DistrictData:
    def __init__(self, name):
        self.name = name
        self.predaj_data = []
        self.prenajom_data = []
        self.median_predaj = None
        self.median_prenajom = None
        self.navratnost = None


    def fetch_predaj(self):
        global DRUH
        self.predaj_data = get_all(self.name, DRUH, 'predaj')

    def fetch_prenajom(self):
        global DRUH
        self.prenajom_data = get_all(self.name, DRUH, 'prenajom')

    def stats(self):
        if len(self.predaj_data) != 0 and len(self.prenajom_data) != 0:
            self.median_predaj = get_listings_median(self.predaj_data)
            self.median_prenajom = get_listings_median(self.prenajom_data)
            # TODO add fix costs, mortgage interest
            self.navratnost = self.median_predaj/self.median_prenajom

        data = {
          "district": self.name,
          "navratnost": self.navratnost,
          "median_predaj": self.median_predaj,
          "median_prenajom": self.median_prenajom,
          "count_predaj": len(self.predaj_data),
          "count_prenajom": len(self.prenajom_data),
          "predaj_data": [l.toJSON() for l in self.predaj_data],
          "prenajom_data": [l.toJSON() for l in self.prenajom_data],
        }
        return data

    def run(self):
        self.fetch_predaj()
        self.fetch_prenajom()
        stats = self.stats()
        return "\t".join([
            self.name, 
            str(stats["navratnost"]), 
            str(stats["median_predaj"]),
            str(stats["count_predaj"]),
            str(stats["median_prenajom"]), 
            str(stats["count_prenajom"]),
        ])


# Preprocess
# with open('list_pre_slug.txt', 'r') as f:
#    from slugify import slugify
#    for cnt, line in enumerate(f):
#        print(slugify(line))

# Test
# dd = DistrictData('banska-bystrica')
# dd.run()

# Production
with open('list_mesta_todo.txt') as f:
    mesta = f.readlines()
mesta = [mesto.strip() for mesto in mesta]

districts = []
for mesto in mesta:
    dd = DistrictData(mesto)
    summary = dd.run()
    districts.append(dd)

    with open('data/result_{}.txt'.format(DRUH), 'a') as summary_file:
        print(summary)
        summary_file.write(summary + "\n")
    with open('data/district/result_{}_{}.json'.format(DRUH, mesto), 'w') as district_file:
        json.dump(dd.stats(), district_file)

with open('data/result_{}.json'.format(DRUH), 'w') as outfile:
    json.dump([d.stats() for d in districts], outfile)
