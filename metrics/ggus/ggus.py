#!/usr/bin/python

# aaltunda - ali.mehmet.altundag@cern.ch
import sys, time
from lib import fileOps, dashboard, sites
try: import xml.etree.ElementTree as ET
except ImportError: from elementtree import ElementTree as ET

if len(sys.argv) < 4:
    print 'not enough parameters'
    sys.exit(1)

tickets = fileOps.read(sys.argv[1])
tickets = ET.fromstring(tickets)

parsed  = {}

for ticket in tickets.findall('ticket'):
    cmsSite = ticket.find('cms_site').text
    subject = ticket.find('subject').text
    id      = ticket.find('request_id').text
    if not cmsSite: continue
    if not parsed.has_key(cmsSite):
        parsed[cmsSite] = {}
    parsed[cmsSite][id] = subject

# generate output for twiki meeting page 
ticketURL  = "https://ggus.eu/?mode=ticket_info&ticket_id="
twikiTable = "\n| *CMS Site* | *Number of Tickets* | * Tickets* |\n"
sum        = 0
for site in parsed:
    url = ""
    sum = sum + len(parsed[site])
    for id in parsed[site]:
        url = url + "[[%s][%s]] " % (ticketURL + id, id)
    twikiTable = twikiTable + "| %s | %d | %s |\n" % (site, len(parsed[site]), url)
dateStamp = time.strftime("%d/%b/%Y %H:%M:%S (GMT)", time.gmtime())
twikiTable = twikiTable + "| *<i>generated on %s</i>, Total number of tickets: %s* |||" % (dateStamp, sum)
fileOps.write(sys.argv[2], twikiTable)

# generate text file for the dashboard metric
metric    = dashboard.metric()
allSites  = sites.getSites().keys()
url       = "https://ggus.eu/?mode=ticket_search&cms_site=%s&timeframe=any&status=open&search_submit=GO%%21"
for site in parsed:
    value = len(parsed[site])
    metric.append(dashboard.entry(None, site, value, dashboard.red, url % site))
for site in allSites:
    if site in parsed.keys(): continue
    metric.append(dashboard.entry(None, site, 0, dashboard.green, url % site))
fileOps.write(sys.argv[3], str(metric))
