from datetime import datetime
overallStartTime = datetime.now()

import requests
from bs4 import BeautifulSoup
import sys
import json
import math
import pprint
import csv
import re
import mechanize

def fetch_raw_html(base_string,search_params={}):
    startTime = datetime.now()

    if search_params == {}:
        resp = requests.get(base_string, timeout=3)
    else:
        resp = requests.get(base_string, params=search_params, timeout=3)

    resp.raise_for_status

    print("""'fetch_raw_html' executed.  Run time: """+str(datetime.now()-startTime))
    return resp.content, resp.encoding
    
def parse_html(html,encoding='utf-8'):
    startTime = datetime.now()
    soup = BeautifulSoup(html, from_encoding=encoding)

    print("""'parse_html' executed. Run time: """+str(datetime.now()-startTime))
    return soup

def generate_region_dict(soup):
    startTime = datetime.now()
    regions = soup.find('select', attrs={'name': 'search_regionID', 'onchange': 'changeRegion(this.value);'}).find_all('option')
    region_dict = []
    for region in regions:
        this_region = {
            'id': int(region.attrs.get('value','')),
            'name': region.string
        }
        if this_region['id'] > 0:
            region_dict.append(this_region)
            
    print("""'generate_region_dict' executed. Run time: """+str(datetime.now()-startTime))
    return region_dict

def get_pagecount(soup):
    top_tags = soup.find_all('em')
    raw_hits_info = []
    for emtag in top_tags:
        raw_hits_info.extend(emtag.find_all('b'))
    print raw_hits_info
    if raw_hits_info[1].string == '1 - 0':
        pages = 1
    else:
        print """"int(math.ceil(int("""+str(raw_hits_info[0])+""".string)/int("""+str(raw_hits_info[1])+""".string[4::])))"""
        print """int(math.ceil("""+str(float(raw_hits_info[0].string))+"""/"""+str(float(raw_hits_info[1].string[4::]))+"""))"""
        print """int(math.ceil("""+str(float(raw_hits_info[0].string)/float(raw_hits_info[1].string[4::]))+"""))"""
        print """int("""+str(math.ceil(float(raw_hits_info[0].string)/float(raw_hits_info[1].string[4::])))+""")"""
        pages = int(math.ceil(float(raw_hits_info[0].string)/float(raw_hits_info[1].string[4::])))
    print pages

    return pages

def render_region_listings(region):
    startTime = datetime.now()
    # Create top level soup
    regionID = region['id']
    base_string = 'http://wango.org/resources.aspx'
    search_params = {
        'section': 'ngodir',
        'sub': 'region',
        'regionID': str(regionID)
    }
    tr_html, tr_encoding = fetch_raw_html(base_string,search_params)
    top_region_soup = parse_html(tr_html, tr_encoding)
    # Create area_dict if it does not yet exist
    if 'area_dict' not in locals():
        areas = top_region_soup.find('select',attrs={'id': 'InterestAreas'}).find_all('option')
        area_dict = []
        for area in areas:
            this_area = {
                'value': area.attrs.get('value','')
            }
            if this_area['value'] != 'ALL':
                area_dict.append(this_area)
    # Iterate through areas and pages
    br = mechanize.Browser()
    br.addheaders = [('User-Agent', 'Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.9.0.1) Gecko/2008071615 Fedora/3.0.1-1.fc9 Firefox/3.0.1'),
                 ('Accept','*/*'),
                 ('Accept-Encoding','gzip,deflate,sdch'),
                 ('Accept-Language','en-US,en;q=0.8,es;q=0.6'),
                 ('Cache-Control','max-age=0'),
                 ('Connection','keep-alive'),
                 ('DNT','1'),
                 ('Host','www.gmodules.com')]
    top_region_mch_base_string = br.open("http://www.wango.org/resources.aspx?section=ngodir&sub=region&regionID="+str(regionID))
    for area in area_dict:
        br.select_form(nr=0)
        br.set_all_readonly(False)
        br["InterestAreas"] = area['value']
        br["currpage"] = '1'
        br.submit()
        top_area_html = br.response().read()
        top_area_soup = parse_html(top_area_html)
        pages = get_pagecount(top_area_soup)
        if pages > 1:
            for i in range(pages-1):
                br.select_form(nr=0)
                br.set_all_readonly(False)
                br["currpage"]=str(i+2)
                br.submit()
            top_area_soup.body.append(parse_html(br.response().read()).body)
        listings = top_area_soup.find_all('a',attrs={'href': 'javascript:loadorg('})
        for listing in listings:
            #yield listing
            return listing
    
def generate_iteration_params(region):
    startTime = datetime.now()
    regionID = region['id']
    regionName = region['name']
    base = 'http://wango.org/resources.aspx'
    search_params = {
        'section': 'ngodir',
        'sub': 'region',
        'regionId': str(regionID)
    }
    reg_listings_raw = requests.get(base, params=search_params, timeout=3)
    rglst_soup = BeautifulSoup(reg_listings_raw.content, from_encoding=reg_listings_raw.encoding)
    top_tags = rglst_soup.find_all('em')
    raw_hits_info = []
    
    for emtag in top_tags:
        raw_hits_info.extend(emtag.find_all('b'))
    pages = int(math.ceil(int(raw_hits_info[0].string)/int(raw_hits_info[1].string.lstrip('1 - '))))

    areas = rglst_soup.find('select', attrs={'id': 'InterestAreas'}).find_all('option')
    area_dict = []
    for area in areas:
        this_area = {
            'value': area.attrs.get('value','')
        }
        if this_area['value'] != 'ALL':
            area_dict.append(this_area)
    
    return pages, area_dict

if __name__ == '__main__':
    top_base_string = 'http://wango.org/resources.aspx?section=ngodir'
    top_html, top_encoding = fetch_raw_html(top_base_string)
    top_soup = parse_html(top_html,top_encoding)
    regions = generate_region_dict(top_soup)
    pprint.pprint(render_region_listings(regions[0]))
