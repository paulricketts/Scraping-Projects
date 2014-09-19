from datetime import datetime
overallStartTime = datetime.now()

import os
import requests
from bs4 import BeautifulSoup
import sys
import json
import math
import pprint
import csv
import re
import mechanize
import string
import nltk

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

def create_area_dict(region_dict):
    startTime = datetime.now()
    base_string = 'http://wango.org/resources.aspx'
    search_params = {
        'section': 'ngodir',
        'sub': 'region',
        'regionID': str(region_dict[0]['id'])
    }
    tr_html, tr_encoding = fetch_raw_html(base_string,search_params)
    top_region_soup = parse_html(tr_html, tr_encoding)
    # Create area_dict if it does not yet exist
    if 'area_dict' not in locals():
        print("""Creating area dictionary...""")
        areas = top_region_soup.find('select',attrs={'id': 'InterestAreas'}).find_all('option')
        area_dict = []
        area_dict = dict(enumerate(area.attrs.get('value','') for area in areas if area.attrs.get('value','') != 'ALL'))
    print("""Created area dictionary.  Run time was """+str(datetime.now()-startTime))
    return area_dict

def get_pagecount(soup):
    startTime = datetime.now()
    top_tags = soup.find_all('em')
    raw_hits_info = []
    for emtag in top_tags:
        raw_hits_info.extend(emtag.find_all('b'))
    if raw_hits_info == [] or raw_hits_info[1].string == '1 - 0':
        pages = 1
    else:
        pages = int(math.ceil(float(raw_hits_info[0].string)/float(raw_hits_info[1].string[4::])))

    print("""'get_pagecount' executed.  Run time: """+str(datetime.now()-startTime))
    return pages

def create_directory(regionName):
    startTime = datetime.now()
    if not os.path.exists("""C:\\Users\\Lenddo\\Scraping-Projects\\Scraping-Projects\\wango-scraped-html\\"""+regionName):
        os.makedirs("""C:\\Users\\Lenddo\\Scraping-Projects\\Scraping-Projects\\wango-scraped-html\\"""+regionName)
    print("""Completed directory validation for """+regionName+""".  Run time was """+str(datetime.now()-startTime))

def add_area_html_pages(br,top_area_html,pages):
    startTime = datetime.now()
    for i in range(pages-1):
        br.select_form(nr=0)
        br.set_all_readonly(False)
        br["currpage"]=str(i+2)
        br.submit()
        top_area_html = top_area_html + br.response().read()
    print("""'add_area_html_pages' executed.  Run time: """+str(datetime.now()-startTime))
    return top_area_html

def render_area_html(area,tr_base_string):
    startTime = datetime.now()
    br = mechanize.Browser()
    br.addheaders = [('User-Agent', 'Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.9.0.1) Gecko/2008071615 Fedora/3.0.1-1.fc9 Firefox/3.0.1'),
                 ('Accept','*/*'),
                 ('Accept-Encoding','gzip,deflate,sdch'),
                 ('Accept-Language','en-US,en;q=0.8,es;q=0.6'),
                 ('Cache-Control','max-age=0'),
                 ('Connection','keep-alive'),
                 ('DNT','1'),
                 ('Host','www.gmodules.com')]
    br.open(tr_base_string)
    br.select_form(nr=0)
    br.set_all_readonly(False)
    br["InterestAreas"] = area['value']
    br["currpage"] = '1'
    br.submit()
    top_area_html = br.response().read()
    top_area_soup = parse_html(top_area_html)
    pages = get_pagecount(top_area_soup)
    if pages > 1:
        top_area_html = add_area_html_pages(br,top_area_html,pages)
        top_area_soup = parse_html(top_area_html)
    exec("""html_file = open('C:\\Users\\Lenddo\\Scraping-Projects\\Scraping-Projects\\wango-scraped-html\\"""+regionName+"""\\wango."""+area['value'].replace('/','')+""".html','w')""")
    html_file.write(str(top_area_soup))
    html_file.close()
    print("""'render_area_html' for """+area['value']+""" in """+regionName+""" executed.  Run time: """+str(datetime.now()-startTime))

def render_region_directory(region,area_dict):
    startTime = datetime.now()
    regionName = region['name']
    regionID = region['id']
    # Check to see if directory exists; if not, create it
    create_directory(regionName)
    # Iterate through areas and pages
    tr_base_string = "http://www.wango.org/resources.aspx?section=ngodir&sub=region&regionID="+str(regionID)
    for area in area_dict:
        render_area_html(area,tr_base_string)
    print("""'render_region_directory' for """+regionName+""" executed.  Run time: """+str(datetime.now()-startTime))

def clean_locale_string(locale_string):
    startTime = datetime.now()
    locale_string = locale_string.replace('\n','').replace(',,',',')
    regex_i = re.compile('\d*,')
    if regex_i.match(locale_string) != None:
        locale_string = locale_string.replace(',','',1)
    regex_ii = re.compile('\s\D{2,}[a-z]+\D*\s[A-Z]{2,}')
    if regex_ii.search(locale_string) != None:
        exp = regex_ii.search(locale_string)
        replaced = locale_string[exp.start():exp.end():].lstrip().rstrip()
        replacing = replaced.replace(' ',', ')
        locale_string = locale_string.replace(replaced,replacing)
    regex_iii = re.compile(',')
    if len(regex_iii.findall(locale_string)) > 2:
        locale_string = locale_string.replace(',','',len(regex_iii.findall(locale_string))-2)
    locales = locale_string.split(',')
    regex_iv = re.compile('^\d+$')
    regex_vi = re.compile('\s*\d+\s')
    for locale in locales:
        if regex_iv.match(locale) != None:
            locales.remove(locale)
    if len(locales) == 3:
        street_address = locales[0]
        city = locales[1]
        country = locales[2]
    elif len(locales) == 2:
        regex_v = re.compile('\s')
        if len(regex_v.findall(locales[0])) > 1 and regex_vi.search(locales[1]) != None:
            street_address = locales[0]
            city = ''
            country = locales[1]
        else:
            street_address = ''
            city = locales[0]
            country = locales[1]
    else:
        street_address = ''
        city = ''
        country = locales[0]
    if regex_vi.search(city) != None:
        city = city.replace(city[regex_vi.search(city).start():regex_vi.search(city).end():],'')
    street_address = street_address.strip()
    city = city.strip()
    country = country.strip()
    print("""'clean_locale_string' executed.  Run time: """+str(datetime.now()-startTime))
    return street_address, city, country

def normalize_string(input_string):
    startTime = datetime.now()
    preps = [' of ',' in ',' to ',' for ',' with ',' on ',' at ',' from ',' by ',' as ']
    input_string = input_string.lower().strip().replace('  ',' ')
    for p in string.punctuation:
        input_string = input_string.replace(p,'')
    for prep in preps:
        input_string = input_string.replace(prep,' ')
    print("""'normalize_string' executed.  Run time: """+str(datetime.now()-startTime))
    return input_string

def generate_output():
    startTime = datetime.now()
    top_string = """C:\\Users\\Paul\\Scraping-Projects\\wango-scraped-html\\"""
    top_dir = os.listdir(top_string)
    output = [['id','name','street_address','city','country','region','interest_area']]
    ids = []
    interest_areas = [['org_id','area_id']]
    for infile in top_dir:
        regionName = infile
        sub_dir = os.listdir(top_string+infile)
        for html in sub_dir:
            interestArea = html[6:len(html)-5:]
            with open(top_string+infile+"""\\"""+html, 'rb') as read_file:
                html_file = read_file.read()
            sub_soup = parse_html(html_file)
            orgs = sub_soup.find_all(href=re.compile("javascript:loadOrg"))
            for org in orgs:
                locale_string = org.next_sibling.next_sibling.next_sibling.next_sibling.text
                street_address, city, country = clean_locale_string(locale_string)
                try:
                    if org.get('href')[20:len(str(org.get('href')))-3:] not in ids:
                        output.append([
                            (org.get('href'))[20:len(str(org.get('href')))-3:].encode('utf-8'),
                            org.find('b').text.replace("\\","\\\\").encode('utf-8'),
                            street_address.replace("\\","\\\\").encode('utf-8'),
                            city.replace("\\","\\\\").encode('utf-8'),
                            country.replace("\\","\\\\").encode('utf-8'),
                            regionName.replace("\\","\\\\").encode('utf-8'),
                            interestArea.replace("\\","\\\\").encode('utf-8')
                        ])
                        ids.append(org.get('href')[20:len(str(org.get('href')))-3:])
                    interest_areas.append([
                        (org.get('href'))[20:len(str(org.get('href')))-3:].encode('utf-8'),
                        interestArea.replace("\\","\\\\").encode('utf-8')
                    ])
                except TypeError:
                    print(regionName)
                    print(interestArea)
                    print(org)
                    print(locales)
                    print("""There was an error.  'generate_output' ran for """+str(datetime.now()-startTime)+""" s.""")
                    break
    print("""'generate_output' executed.  Run time: """+str(datetime.now()-startTime))
    return output, interest_areas

def pull_place_ids(output):
    potential_matches = [['org_id','org_name','org_name_normalized','match_name','match_name_normalized','place_id','edit_distance']]
    for i in range(1,len(output)-1):
        query_string = (normalize_string(output[i][1])+' near '+normalize_string(output[i][3])+' '+normalize_string(output[i][4])).replace(' ','+')
        print("""map_hits = requests.get('https://maps.googleapis.com/maps/api/place/textsearch/json?query='"""+query_string+"""'&key=AIzaSyAuoBD1ABjNi3wwXSxQ-FdeJChk1UYqHSM')""")
        map_hits = requests.get('https://maps.googleapis.com/maps/api/place/textsearch/json?query='+query_string+'&key=AIzaSyAuoBD1ABjNi3wwXSxQ-FdeJChk1UYqHSM')
        data = json.loads(map_hits.text)
        if 'results' in data.keys():
            for item in data['results']:
                potential_matches.append([
                    output[i][0],
                    output[i][1],
                    normalize_string(output[i][0]),
                    item['name'],
                    normalize_string(item['name']),
                    item['place_id'],
                    nltk.edit_distance(normalize_string(output[i][0]),normalize_string(item['name']))
                ])
                print(potential_matches[i])
        

def write_output(output,interest_areas):
    startTime = datetime.now()
    with open("""C:\\Users\\Paul\\Scraping-Projects\\wango_outputs\\wango_output.csv""",'w') as outfile:
        writer = csv.writer(outfile,lineterminator='\n')
        for item in output:
            writer.writerow(item)
    print("""'generate_output' executed.  Run time: """+str(datetime.now()-startTime))
            

if __name__ == '__main__':
    #top_base_string = 'http://wango.org/resources.aspx?section=ngodir'
    #top_html, top_encoding = fetch_raw_html(top_base_string)
    #top_soup = parse_html(top_html,top_encoding)
    #region_dict = generate_region_dict(top_soup)
    #area_dict = create_area_dict(region_dict)
    output, interest_areas = generate_output()
    pull_place_ids(output)
