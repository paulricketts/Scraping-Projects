import mechanize
br = mechanize.Browser()
br.addheaders = [('User-Agent', 'Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.9.0.1) Gecko/2008071615 Fedora/3.0.1-1.fc9 Firefox/3.0.1'),
                 ('Accept','*/*'),
                 ('Accept-Encoding','gzip,deflate,sdch'),
                 ('Accept-Language','en-US,en;q=0.8,es;q=0.6'),
                 ('Cache-Control','max-age=0'),
                 ('Connection','keep-alive'),
                 ('DNT','1'),
                 ('Host','www.gmodules.com')]

response = br.open("http://www.wango.org/resources.aspx?section=ngodir&sub=region&regionID=5")

html = response.read()
br.select_form(nr=0)
print(br.form)
br.set_all_readonly(False)
br["InterestAreas"] = "Development"
response = br.submit()
print br.response().read()
br.select_form(nr=0)
print br.form

#for i in range(12):
 #   html = response.read()
  #  print "Page %d :" % int(i+1), html
   # br.select_form(nr=0)
    #print(br.form)
    #br.set_all_readonly(False)
    #br["currpage"] = str(i+1)
    #response = br.submit()
    #print response.read
