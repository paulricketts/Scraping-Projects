import requests
from bs4 import BeautifulSoup
import jsbeautifier

test_run = requests.get('http://www.gmodules.com/gadgets/js/core:core.io.js?container=default&nocache=0&debug=0&c=0&v=650957114d7abe7daa627fb89efd8c64&sv=10&jsload=0')
js = jsbeautifer.beautify(test_run.content)

print(js)
