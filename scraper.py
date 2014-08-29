# Import requests module - this is an Apache2 licensed HTTP library written in
# python for human beings; it is an improvement on the urllib2 module that makes
# sending HTTP requests more efficient
# (https://pypi.python.org/pypi/requests#downloads)
import requests
# Import BeautifulSoup module - "it works with your favorite parser to provide
# idiomatic ways of navigating, searching and modifying the parse tree.  It
# commonly saves programmers hours or days of work"
# (http://www.crummy.com/software/BeautifulSoup/bs4/doc/)
from bs4 import BeautifulSoup
# Import sys module - this "allows your program to launch other programs and
# communicate with them"
# (https://www.daniweb.com/software-development/python/threads/213333/what-
# does-the-sys-module-do-in-python)
import sys
# Imports json module - "[purpose is to] encode python objects as JSON strings,
# and decode JSON strings into Python objects...The json mdoule provides an API
# similar to pickle for converting in-memory Python objects to a serialized
# representation known as JSON.  Unlike pickle, JSON has the benefit of having
# implementations in many languages (especially JavaScript), making it suitable
# for inter-application communication.  JSON is probably most widely used for
# communicating between the web server and client in an AJAX application, but
# is not limited to that problem domain"
# (http://pymotw.com/2/json/)
import json


# Create function "fetch_results" that takes 4 arguments, all initialized to
# "None"; the arguments are named "query", "minAsk", "maxAsk", and "bedrooms"
def fetch_results(
    query=None, minAsk=None, maxAsk=None, bedrooms=None
):

    # Define a dictionary named search_params that consolidates key-value-pairs 
    # in the local symbol table for which the value is not None
    search_params = {
        key: val for key, val in locals().items() if val is not None
    }
    # If there are no key-value-pairs for which is the value is not None, raise
    # a custom error
    if not search_params:
        raise ValueError("No valid keywords")

    # Create string variable containing url for Seattle apts/housing for rent
    # listings
    base = 'http://sfbay.craigslist.org/search/sfc/apa'
    # Create a response object from the URL, passing arguments for the URL
    # (base), other possible string parameters, and a timeout parameter of 3
    # seconds
    print(search_params)
    resp = requests.get(base, params=search_params, timeout=3)
    # Set function to raise exceptions for error codes when the request errors
    # out
    resp.raise_for_status()  # no op if status == 200
    # Function finally returns content of the response (in bytes) and the
    # encoding to decode when accessing the text in the response
    return resp.content, resp.encoding

# html_base = fetch_results("South Lake Union", 1500, 2500)
# with open('apartments.html', 'w') as outfile:
#     outfile.write(html_base[0])


# Define a function to return json structured results from pure json section of
# the page - the function accepts an arbitrary of keyword arguments
def fetch_json_results(**kwargs):
    base = 'http://sfbay.craigslist.org/jsonsearch/sfc/apa'
    resp = requests.get(base, params=kwargs)
    resp.raise_for_status()
    # Returns the json-encoded content of the response, if any
    return resp.json()


# Define a function accepting a file argument (initializing to 'apartments.html'
# ) where the file will be binarily (w/o truncation) read; the function returns
# read file and encoding note
def read_search_results(file='apartments.html'):
    with open(file, 'rb') as read_file:
        return read_file.read(), 'utf-8'


# Define parsing function, takes html as a required argument and encoding spec
# as optional argument (defaulting to utf-8); parses html using BeautifulSoup
# and returns that parse
def parse_source(html, encoding='utf-8'):
    parsed = BeautifulSoup(html, from_encoding=encoding)
    return parsed


# Define function that takes a parsed BeautifulSoup HTML object as only
# (required) argument
def extract_listings(parsed):
    # Create an array containing all content inside <p> tags with CSS class
    # 'row'
    listings = parsed.find_all('p', class_='row')
    # Iterate over newly created array; for each array item...
    for listing in listings:
        # Define a link variable containing first string nested inside a <span>
        # tag, with CSS class 'pl'; within this text, find the first string
        # nested inside an <a> tag
        link = listing.find('span', class_='pl').find('a')
        # Define a price_span variable containing first string nested inside a
        # <span> tag with CSS class 'price'
        price_span = listing.find('span', class_='price')
        # Create a dictionary, with following elements:
        this_listing = {
            # Pull back attributes inside the last found tag (in this case <p>)
            # , find value for the key data-pid (using the dict.get() method;
            # if not found, empty string)and store in the new dictionary with
            # the key 'pid'
            'pid': listing.attrs.get('data-pid', ''),
            # For the link, pull back attributes inside the last found tag (in
            # this case, <a>), store value for href attribute in the new
            # dictionary with the key 'link'
            'link': link.attrs['href'],
            # For the link, pull back the text inside the last found tag (in
            # this case, <a>), store stripped string in the new dictionary with
            # the key 'description'
            'description': link.string.strip(),
            # For the price span, pull back the integer / text in the last found
            # tag (in this case, <a>), store stripped string in the new
            # dictionary with the key 'price'
            'price': price_span.string.strip(),
            # Navigate over to the next tree element (in this html, the next
            # element is the size) and strip spaces, carriage returns, dashes
            # and or backslashes from the beginning and end of that string;
            # store what is left in the new dictionary with the key 'size'
            'size': price_span.next_sibling.strip(' \n-/')
        }
        yield this_listing


# Define a function taking two arguments, "listing" and "search"; if value for
# key "pid" in listing is in "search" parameter, add key-value pair with key
# "location" into listing; the value will be a dictionary holding the latitude
# and longitude of the location; otherwise return False
def add_location(listing, search):
    """True if listing can be located, otherwise False"""
    if listing['pid'] in search:
        match = search[listing['pid']]
        listing['location'] = {
            'data-latitude': match.get('Latitude', ''),
            'data-longitude': match.get('Longitude', ''),
        }
        return True
    return False


# Add address to listing dictionary
def add_address(listing):
    # Create URL string w/ url of google geocode maps api
    api_url = 'http://maps.googleapis.com/maps/api/geocode/json'
    # Pull 'location' value out of listing dictionary and store it in 'loc'
    # variable
    loc = listing['location']
    # Create a text template for data-latitude and data-longitude
    lactlng_tmpl = "{data-latitude},{data-longitude}"
    # Create new dictionary 'parameters' setting 'sensor' value to False
    parameters = {
        'sensor': 'false',
        # Store latlng key-value pair in which pieces of the text template
        # delimited by curly braces are replaced by the respective element in
        # the 'loc' dictionary
        'latlng': lactlng_tmpl.format(**loc),
    }
    # Create a response object from the api_url using newly created parameters
    resp = requests.get(api_url, params=parameters)
    # Set function to raise exceptions for error codes when the request errors
    # out
    resp.raise_for_status()
    # The content of the new response, in unicode, is converted from JSON into
    # a python dictionary object called "data"
    data = json.loads(resp.text)
    # If value for new dictionary key (from the response) "status" is equal to
    # 'OK'...
    if data['status'] == 'OK':
        # Store first element of dictionary element 'results' into new variable
        # 'best'
        best = data['results'][0]
        # Create new listing element "address" and store 'formatted_address'
        # element of newly created 'best' dictionary into this new element
        listing['address'] = best['formatted_address']
    else:
        # Otherwise create new listing element "address" and set value as
        # 'unavailable' before returning the listing
        listing['address'] = 'unavailable'
    return listing


# Run what comes next only if being run by the program itself, not if imported
# from another module
if __name__ == '__main__':
    # Imports pprint module - "contains a 'pretty printer' for producing
    # aesthetically pleasing representations of your data structures.  The
    # formatter produces representations of data structures that can be parsed
    # correctly by the interpreter, and are also easy for a human to read. The
    # output is kept on a single line, if possible, and indented when split
    # across multiple lines"
    # (http://pymotw.com/2/pprint/)
    import pprint
    import csv
    # If the script is being run from scraper_test rather than main script, read
    # the html and encoding from a static doc called 'apartments.html'
    if len(sys.argv) > 1 and sys.argv[1] == 'test':
        html, encoding = read_search_results()
    # If not, get results from the response object and pass through some
    # optional parameters for max and min ask and for # of bedrooms
    else:
        html, encoding = fetch_results(
            minAsk=500, maxAsk=5000, bedrooms=2
        )
    # Parse results w/ BeautifulSoup
    doc = parse_source(html, encoding)
    # Alternately fetch json results from alternative json craigslist site w/
    # keywords for minAsk, maxAsk and bedrooms - store these into 'json_res'
    # object
    json_res = fetch_json_results(minAsk=500, maxAsk=5000, bedrooms=2)
    # Create list expression pulling all of the posting ids out of the json_res
    # object - restructures json_res into new dictionary object search, which
    # index json content to IDs
    search = {j['PostingID']: j for j in json_res[0]}
    # Listings are generated using extract_listings function; for each...
    listings = extract_listings(doc)
    with open('C:\\Users\\Lenddo\\Desktop\\test.csv','w',newline='', encoding='utf-8') as outfile:
        writer = csv.writer(outfile)
        writer.writerow(['address','description','link','data-latitude','data-longitude','pid','price','size'])
        for listing in listings:
            # Determine whether listing is present in search dictionary; if it is,
            # add the address to the listing from Google geocode API...
            if (add_location(listing, search)):
                listing = add_address(listing)
                # ...and print the listing in a pretty way
            pprint.pprint(listing)
            csv_listing = []
            if 'address' in listing:
                csv_listing.append(listing['address'])
            else:
                csv_listing.append('')
            csv_listing.append(listing['description'])
            csv_listing.append(listing['link'])
            if 'location' in listing:
                csv_listing.append(listing['location'].get('data-latitude',''))
                csv_listing.append(listing['location'].get('data-longitude',''))
            else:
                csv_listing.append('')
                csv_listing.append('')
            csv_listing.append(listing['pid'])
            csv_listing.append(listing['price'])
            csv_listing.append(listing['size'])
            print(csv_listing)
            writer.writerow(csv_listing)
                
            

