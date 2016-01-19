import urllib2
import re
import os
import os.path
from lxml import etree
from datetime import datetime

#get full source code
url = "https://cmsweb.cern.ch/phedex/prod/Components::Agents?pcolumn=NODE_NAME&pcolumn=FILENAME%3ARELEASE%3AREVISION%3ATAG"
response = urllib2.urlopen(url)
html = response.read()

#get table from source code
table = re.search(r'<tbody>.*</tbody>', html, re.DOTALL)
table = table.group(0)

site_n_phedex_version = []

#fetch table
table = etree.XML(table)
rows = iter(table)
for row in rows:
	values = [col.text for col in row]
	if values[2] is not None:
		phedex_version_number = map(int, re.findall(r'\d+', values[2]))
		if phedex_version_number >= [4,1,7]:
			status = "green"
		elif phedex_version_number < [4,1,5]:
			status = "red"
		else:
			status = "yellow"
		item = {
				"TimeStamp": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
				"site": values[0],
				"Phedex_version": values[2],
				"color": status,
				"url": url
			}
		if item not in site_n_phedex_version:
			site_n_phedex_version.append(item)

output = "output.txt"
path = os.path.expanduser("~/www/phedex_version/")
absolute_path = os.path.join(path, output)
if os.path.isfile(absolute_path):
	os.remove(absolute_path)

os.path.expanduser("~")
output = open(absolute_path, "w")
for item in site_n_phedex_version:
	output.write("%s %s %s %s %s\n" %(
		item['TimeStamp'], 
		item['site'], 
		item['Phedex_version'], 
		item['color'], 
		item['url']
		));
output.close()