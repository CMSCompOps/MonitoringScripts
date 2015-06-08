#!/usr/bin/env python26

import sys,re
import urllib
import time
import calendar
from optparse import OptionParser
from datetime import datetime
from xml.dom import minidom

def getText(nodelist):
    rc = []
    for node in nodelist:
        if node.nodeType == node.TEXT_NODE:
            rc.append(node.data)
    return ''.join(rc)

def getTag(node,tagname):
    return getText(node.getElementsByTagName(tagname)[0].childNodes)

current = datetime.utcnow()
current_unix = int(calendar.timegm(current.timetuple()))

parser = OptionParser(add_help_option=False)
parser.add_option("-h", "--help", action="help")
parser.add_option("-i", "--input", dest="inFile",
                  help="(Optional) Input XML file, under http, containing all the savannah information")
parser.add_option("-o", "--output", dest="outFile",
                  help="(Mandatory) HTML file containing the output of this script")
(options, args) = parser.parse_args()

if options.outFile == None:
    parser.error("You must provide the output file name (use -o option) or consult --help\n")
if options.inFile == None:
    url='https://savannah.cern.ch/export/cmscompinfrasup/gutsche/526.xml'
    input = urllib.urlopen(url)
else:
    input = urllib.urlopen(options.inFile)

RE_XML_ILLEGAL = u'([\u0000-\u0008\u000b-\u000c\u000e-\u001f\ufffe-\uffff])' + \
                 u'|' + \
                 u'([%s-%s][^%s-%s])|([^%s-%s][%s-%s])|([%s-%s]$)|(^[%s-%s])' % \
                  (unichr(0xd800),unichr(0xdbff),unichr(0xdc00),unichr(0xdfff),
                   unichr(0xd800),unichr(0xdbff),unichr(0xdc00),unichr(0xdfff),
                   unichr(0xd800),unichr(0xdbff),unichr(0xdc00),unichr(0xdfff))
x = re.sub(RE_XML_ILLEGAL, "?", input.read())
xmldoc = minidom.parseString(x)

# for savannah in xmldoc.childNodes :
#     for item in savannah.childNodes:
#         f.write(item.getElementsByTagName('item_id')[0]

tickets = {}
squads = {}

savaneexport = xmldoc.getElementsByTagName('savaneexport')[0]
items = savaneexport.getElementsByTagName('item')
for item in items:
    id =  int(getTag(item,'item_id'))
    category = getTag(item,'category')
    summary = getTag(item,'summary')
    squad = getTag(item,'assigned_to')
    site = getTag(item,'custom_select_box_1')
    submitted_on = int(getTag(item,'submitted_on'))
    open_since = int((current_unix-submitted_on)/86400)
    ggus_field = getTag(item,'custom_select_box_2')
    if ggus_field == 'Yes' :
        ggus = True
    else :
        ggus = False
    ggus_url = getTag(item,'custom_text_field_1')
    history = item.getElementsByTagName('history')
    last_modification = open_since
    if len(history) > 0:
        events = history[0].getElementsByTagName('event')
        date = submitted_on
        for event in events:
            date = int(getTag(event, 'date'))
        last_modification = int((current_unix-date)/86400)
    #f.write("id: %i, category: %s, squad: %s, summary: %s, last_mod: %4i days" % (id,category,squad, summary, last_modification)
    if category not in tickets.keys(): tickets[category] = {}
    tickets[category][id] = {'summary':summary,'squad':squad,'site':site,'submitted_on':submitted_on,'open_since':open_since,'last_modified':last_modification,'ggus':ggus,'ggus_url':ggus_url}
    if squad not in squads.keys(): squads[squad] = 0
    squads[squad] += 1

categories = tickets.keys()
categories.sort()

f = open(options.outFile, 'w')

f.write('<html>')
f.write('<pre>')
f.write('--------------------------------------------------------------------------------<br>')
f.write('Report generated on %s UTC<br>' % current)
f.write('--------------------------------------------------------------------------------<br>')

f.write('<br>')
f.write('Summary: open tickets per category<br>')
f.write('--------------------------------------------------------------------------------<br>')
f.write('<br>')
for category in categories:
    f.write("%40s: %5i open tickets<br>" % (category,len(tickets[category].keys())))

f.write('<br>')
f.write('Summary: open tickets per squad<br>')
f.write('--------------------------------------------------------------------------------<br>')
f.write('<br>')

sorted_squads = squads.keys()
sorted_squads.sort()
for squad in sorted_squads:
    f.write("%40s: %5i open tickets<br>" % (squad,squads[squad]))

for category in categories:
    f.write('<br>')
    f.write(category)
    f.write('<br>--------------------------------------------------------------------------------<br>')
    f.write('<br>')
    timemap = {}
    for id in tickets[category].keys():
        if tickets[category][id]['open_since'] not in timemap.keys(): timemap[tickets[category][id]['open_since']] = []
        timemap[tickets[category][id]['open_since']].append(id)
    times = timemap.keys()
    times.sort(reverse=True)
    for time in times:
        for id in timemap[time]:
            try:
                ggus_id = int(tickets[category][id]['ggus_url'].split('=')[1])
            except:
                ggus_id = 0
            if ggus_id == 0:
                f.write("<a href='http://savannah.cern.ch/support/index.php?%i'>SAV:%i</a> open since %4i days and last modified %4i days ago in squad: %35s at site: %20s and summary: %s<br>" % (id,id,time,tickets[category][id]['last_modified'],tickets[category][id]['squad'],tickets[category][id]['site'],tickets[category][id]['summary']))
            else :
                f.write("<a href='https://ggus.eu/ws/ticket_info.php?ticket=%i'>GGUS:%i</a> open since %4i days and last modified %4i days ago in squad: %35s at site: %20s and summary: %s<br>" % (ggus_id,ggus_id,time,tickets[category][id]['last_modified'],tickets[category][id]['squad'],tickets[category][id]['site'],tickets[category][id]['summary']))
f.write('</pre>')
f.write('</html>')
f.close()
