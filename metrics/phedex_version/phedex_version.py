import urllib2
import re
import os
import HTMLParser
from datetime import datetime


class TableParser(HTMLParser.HTMLParser):
	def __init__(self, decode_html_entities=False, data_separator=''):
		HTMLParser.HTMLParser.__init__(self)

		self._parse_html_entities = decode_html_entities
		self._data_separator = data_separator

		self._in_td = False
		self._in_th = False
		self._current_table = []
		self._current_row = []
		self._current_cell = []
		self.tables = []

	def handle_starttag(self, tag, attrs):
		if tag == 'td':
			self._in_td = True
		if tag == 'th':
			self._in_th = True

	def handle_data(self, data):
		if self._in_td or self._in_th:
			self._current_cell.append(data.strip())

	def handle_charref(self, name):
		""" Handle HTML encoded characters """
		if self._parse_html_entities:
			self.handle_data(self.unescape('&#{};'.format(name)))

	def handle_endtag(self, tag):
		if tag == 'td':
			self._in_td = False
		elif tag == 'th':
			self._in_th = False

		if tag in ['td', 'th']:
			final_cell = self._data_separator.join(self._current_cell).strip()
			self._current_row.append(final_cell)
			self._current_cell = []
		elif tag == 'tr':
			self._current_table.append(self._current_row)
			self._current_row = []
		elif tag == 'tbody':
			self.tables.append(self._current_table)
			self._current_table = []

#get full source code
url = "https://cmsweb.cern.ch/phedex/prod/Components::Agents?pcolumn=NODE_NAME&pcolumn=FILENAME%3ARELEASE%3AREVISION%3ATAG"
response = urllib2.urlopen(url)
html = response.read()

#get table from source code
table = re.search(r'<tbody>.*</tbody>', html, re.DOTALL)
table = table.group(0)
site_n_phedex_version = []

parsed_table = TableParser()
parsed_table.feed(table)
parsed_data = parsed_table.tables[0]

for row in parsed_data:
	if row[2]:
		phedex_version_number = map(int, re.findall(r'\d+', row[2]))
		if phedex_version_number >= [4,2,0]:
			status = "green"
		elif phedex_version_number < [4,1,5]:
			status = "red"
		else:
			status = "yellow"

		item = {
			"TimeStamp": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
			"site": row[0],
			"Phedex_version": row[2],
			"color": status,
			"url": url
		}
		if item not in site_n_phedex_version:
			site_n_phedex_version.append(item)

output = "output.txt"
if os.path.isfile(output):
	os.remove(output)

header = """#txt
#
# Site Support Team, Phedex version Metric
#    written at %s by /data/cmssst/MonitoringScripts/metrics/Phedex_version/run.sh
#    in account cmssst on node vocms077.cern.ch
#    maintained by cms-comp-ops-site-support-team@cern.ch
# =======================================================
#
"""%datetime.now().strftime('%Y-%m-%d %H:%M:%S')

os.path.expanduser("~")
output = open(output, "w")
output.write(header)
for item in site_n_phedex_version:
	output.write("%s %s %s %s %s\n" %(
		item['TimeStamp'], 
		item['site'], 
		item['Phedex_version'], 
		item['color'], 
		item['url']
		));
output.close()