#!/usr/bin/env python26

import sys
import re
import time
import urllib
import codecs
from xml.dom import minidom
from datetime import datetime
from math import sqrt, fabs
from calendar import timegm
from optparse import OptionParser

#Allows to write utf-8 when redirecting output
sys.stdout = codecs.getwriter('utf-8')(sys.stdout)

#print u'%35s %50s %6s' % ("Squad", "Time to close a ticket".center(50), "Closed tickets")
#print u'%35s %25s  %25s %6s' % ("", "Median".center(25), "Average".center(25), "")
#print u'%35s %10.2f \u00B1 %6.2f %5s %10.2f \u00B1 %6.2f %13i' % ("cmscompinfrasup-t2plcracow", 0.054, 0.02, "", 0.29, 0.09, 27)
#sys.exit()

def getText(nodelist):
    rc = []
    for node in nodelist:
        if node.nodeType == node.TEXT_NODE:
            rc.append(node.data)
    return ''.join(rc)

def getTag(node,tagname):
    return getText(node.getElementsByTagName(tagname)[0].childNodes)

def getTimeOfFirstMeaningfulResponse(item):
    submitter = getTag(item, 'submitted_by')
    history = item.getElementsByTagName('history')
    if len(history) > 0:
        backup_date = 0
        first_event_date = 0
        events = history[0].getElementsByTagName('event')
        for event in events:
                if first_event_date == 0:
                    first_event_date = float(getTag(event, 'date'))
                fields = event.getElementsByTagName('field')
                for field in fields:
                    name = getTag(field, 'field_name')
                    modified_by = getTag(field, 'modified_by')
                    if modified_by != submitter and name == 'Original_Submission':
                        return float(getTag(event, 'date'))
                    elif backup_date == 0 and name == 'Original_Submission':
                        backup_date = float(getTag(event, 'date'))
        if backup_date != 0:
            return backup_date
        else:
            return first_event_date

    return float(getTag(item, 'submitted_on'))

def median(x):
    if len(x) < 1:
        raise Exception('Empty array')
    if len(x) == 1:
        return x[0]
    x = sorted(x)
    if len(x) % 2 == 0:
        return (x[len(x)/2] + x[len(x)/2 - 1])/2
    return x[(len(x) - 1)/2]

def mad(x, m):
    deviations = []
    for i in x:
        deviations.append(fabs(i - m))
    return median(deviations)

def meanstdev(x):
    if len(x) < 1:
        raise Exception('Empty array')
    if len(x) == 1:
        return (x[0], 0.0)
    i = 0
    M = 0.0
    S = 0.0
    for value in x:
        i += 1
        delta = value - M
        M += delta/i
        S += delta*(value - M)
    stdev = sqrt(S/(i-1))
    mean = M
    return (mean, stdev)

current = datetime.utcnow()
current_unix = timegm(current.timetuple())

parser = OptionParser(add_help_option=False)
parser.add_option("-h", "--help", action="help")
parser.add_option("-i", "--input", dest="inFile",
                  help="(Optional) Input XML file, under http, containing all the savannah information")
parser.add_option("-o", "--output", dest="outFile",
                  help="(Mandatory) HTML file containing the output of this script")
parser.add_option("-d", "--days", dest="openedInTheLastNDays", type="int",
                  help="(Mandatory) Number of days to look at")
(options, args) = parser.parse_args()

if options.outFile == None:
    parser.error("You must provide the output file name (use -o option) or consult --help\n")
if options.inFile == None:
    url='https://savannah.cern.ch/export/cmscompinfrasup/gutsche/535.xml'
    input = urllib.urlopen(url)
else:
    input = urllib.urlopen(options.inFile)
if options.openedInTheLastNDays == None:
    parser.error("You must provide the number of days to look at")

outf = open(options.outFile, 'w')

RE_XML_ILLEGAL = u'([\u0000-\u0008\u000b-\u000c\u000e-\u001f\ufffe-\uffff])' + \
                 u'|' + \
                 u'([%s-%s][^%s-%s])|([^%s-%s][%s-%s])|([%s-%s]$)|(^[%s-%s])' % \
                  (unichr(0xd800),unichr(0xdbff),unichr(0xdc00),unichr(0xdfff),
                   unichr(0xd800),unichr(0xdbff),unichr(0xdc00),unichr(0xdfff),
                   unichr(0xd800),unichr(0xdbff),unichr(0xdc00),unichr(0xdfff))
x = re.sub(RE_XML_ILLEGAL, "?", input.read()) # takes ages
# Remove broken control unicode chars
brokenControl = '\xc2([^\x80-\xbf])'
x = re.sub(brokenControl, '?\g<1>', x)
xmldoc = minidom.parseString(x)

savanaexport = xmldoc.getElementsByTagName('savaneexport')[0]
items = savanaexport.getElementsByTagName('item')

squads = {}
tickets = {}
tickets = {'close_times': [], 'response_times': [], 'median_close_time': 0.0, 'median_response_time': 0.0, 'close_time_error': 0.0, 'response_time_error': 0.0, 'avg_close_time': 0.0, 'avg_response_time': 0.0, 'stdev_close_time': 0.0, 'stdev_response_time': 0.0}

for item in items:
    squad = getTag(item, 'assigned_to')
    submitted_on = float(getTag(item, 'submitted_on'))
    closed_on = float(getTag(item, 'closed_on'))
    first_response_on = getTimeOfFirstMeaningfulResponse(item)
    if (current_unix - submitted_on) > (options.openedInTheLastNDays*86400):
        continue

    if squad not in squads.keys():
        squads[squad] = {'close_times': [], 'response_times': [], 'median_close_time': 0.0, 'median_response_time': 0.0, 'close_time_error': 0.0, 'response_time_error': 0.0, 'avg_close_time': 0.0, 'avg_response_time': 0.0, 'stdev_close_time': 0.0, 'stdev_response_time': 0.0}

    time_until_closed = closed_on - submitted_on
    time_until_first_response = first_response_on - submitted_on

    squads[squad]['close_times'].append(time_until_closed)
    squads[squad]['response_times'].append(time_until_first_response)

    tickets['close_times'].append(time_until_closed)
    tickets['response_times'].append(time_until_first_response)


tickets['median_close_time'] = median(tickets['close_times'])
tickets['median_response_time'] = median(tickets['response_times'])
tickets['close_time_error'] = mad(tickets['close_times'], tickets['median_close_time'])
tickets['response_time_error'] = mad(tickets['response_times'], tickets['median_response_time'])
(tickets['avg_close_time'], tickets['stdev_close_time']) = meanstdev(tickets['close_times'])
(tickets['avg_response_time'], tickets['stdev_response_time']) = meanstdev(tickets['response_times'])

for squad in squads.keys():
    squads[squad]['median_close_time'] = median(squads[squad]['close_times'])
    squads[squad]['median_response_time'] = median(squads[squad]['response_times'])
    squads[squad]['close_time_error'] = mad(squads[squad]['close_times'], squads[squad]['median_close_time'])
    squads[squad]['response_time_error'] = mad(squads[squad]['response_times'], squads[squad]['median_response_time'])
    (squads[squad]['avg_close_time'], squads[squad]['stdev_close_time']) = meanstdev(squads[squad]['close_times'])
    (squads[squad]['avg_response_time'], squads[squad]['stdev_response_time']) = meanstdev(squads[squad]['response_times'])

outf.write('<html>\n')
outf.write('<pre>\n')
outf.write('<meta http-equiv="Content-Type" content="text/html; charset=UTF-8"/>\n')
outf.write('--------------------------------------------------------------------------------\n')
outf.write('Report generated on ' + str(current) + ' UTC\n')
outf.write('--------------------------------------------------------------------------------\n')

outf.write('--------------------------------------------------------------------------------\n')
outf.write('Summary: average time to close tickets per squad\n')
outf.write('--------------------------------------------------------------------------------\n')
outf.write(u'%35s %50s %6s' % ("Squad", "Time to close a ticket".center(50), "Closed tickets\n"))
outf.write(u'%35s %25s  %25s %6s' % ("", "Median".center(25), "Average".center(25), "\n"))
sorted_squads = sorted(squads.items(), key = lambda x: x[1]['median_close_time'], reverse = True)
for (squad,d) in sorted_squads:
    error_close_time_squad = squads[squad]['close_time_error']/86400
    median_close_time_squad = squads[squad]['median_close_time']/86400
    stdev_close_time_squad = squads[squad]['stdev_close_time']/86400
    mean_close_time_squad = squads[squad]['avg_close_time']/86400
    outstr = u'%35s %10.2f \u00B1 %6.2f %5s %10.2f \u00B1 %6.2f %13i\n' % (squad.replace("cmscompinfrasup-",""), median_close_time_squad, error_close_time_squad, "", mean_close_time_squad, stdev_close_time_squad, len(squads[squad]['close_times']))
    outf.write(outstr.encode('utf8'))

outf.write('--------------------------------------------------------------------------------\n')
outf.write('Summary: average time to first response to a ticket per squad\n')
outf.write('--------------------------------------------------------------------------------\n')
outf.write(u'%35s %50s %6s' % ("Squad", "Time to respond to a ticket".center(50), "Closed tickets\n"))
outf.write(u'%35s %25s  %25s %6s' % ("", "Median".center(25), "Average".center(25), "\n"))
sorted_squads = sorted(squads.items(), key = lambda x: x[1]['median_response_time'], reverse = True)
for (squad,d) in sorted_squads:
    error_response_time_squad = squads[squad]['response_time_error']/86400
    median_response_time_squad = squads[squad]['median_response_time']/86400
    stdev_response_time_squad = squads[squad]['stdev_response_time']/86400
    mean_response_time_squad = squads[squad]['avg_response_time']/86400
    outstr = u'%35s %10.2f \u00B1 %6.2f %5s %10.2f \u00B1 %6.2f %13i\n' % (squad.replace("cmscompinfrasup-",""), median_response_time_squad, error_response_time_squad, "", mean_response_time_squad, stdev_response_time_squad, len(squads[squad]['response_times']))
    outf.write(outstr.encode('utf8'))

outf.write('--------------------------------------------------------------------------------\n')
outf.write('Summary: closed tickets summary\n')
outf.write('--------------------------------------------------------------------------------\n')
error_response_time_total = tickets['response_time_error']/86400
error_close_time_total = tickets['close_time_error']/86400
median_close_time_total = tickets['median_close_time']/86400
median_response_time_total = tickets['median_response_time']/86400
stdev_response_time_total = tickets['stdev_response_time']/86400
stdev_close_time_total = tickets['stdev_close_time']/86400
mean_close_time_total = tickets['avg_close_time']/86400
mean_response_time_total = tickets['avg_response_time']/86400
outf.write(unicode('Total number of closed tickets: %i\n' % (len(tickets['close_times']))))
outf.write((u'Median time to close a ticket:                  %6.2f \u00B1 %6.2f days\n' % (median_close_time_total, error_close_time_total)).encode('utf8'))
outf.write((u'Median time to the first response to a ticket:  %6.2f \u00B1 %6.2f days\n' % (median_response_time_total, error_response_time_total)).encode('utf8'))
outf.write((u'Average time to close a ticket:                 %6.2f \u00B1 %6.2f days\n' % (mean_close_time_total, stdev_close_time_total)).encode('utf8'))
outf.write((u'Average time to the first response to a ticket: %6.2f \u00B1 %6.2f days\n' %(mean_response_time_total, stdev_response_time_total)).encode('utf8'))
outf.write('</pre>\n')
outf.write('</html>\n')
outf.close()
