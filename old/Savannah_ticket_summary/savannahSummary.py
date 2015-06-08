#!/usr/bin/env python26
'''
Created on Dec 10, 2012

@author: dballest
'''

import sys
import re
import urllib
import codecs
from xml.dom import minidom
from datetime import datetime
from calendar import timegm
from optparse import OptionParser

#Allows to write utf-8 when redirecting output
sys.stdout = codecs.getwriter('utf-8')(sys.stdout)

def getText(nodelist):
    rc = []
    for node in nodelist:
        if node.nodeType == node.TEXT_NODE:
            rc.append(node.data)
    return ''.join(rc)

def getTag(node, tagname):
    return getText(node.getElementsByTagName(tagname)[0].childNodes)

def getFirstSquadAssigned(item):
    history = item.getElementsByTagName('history')
    if len(history) > 0:
        events = history[0].getElementsByTagName('event')
        for event in events:
            fields = event.getElementsByTagName('field')
            for field in fields:
                name = getTag(field, 'field_name')
                if name == 'Assigned_to':
                    return getTag(field, 'old_value')
    return

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

def main():
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
                      (unichr(0xd800), unichr(0xdbff), unichr(0xdc00), unichr(0xdfff),
                       unichr(0xd800), unichr(0xdbff), unichr(0xdc00), unichr(0xdfff),
                       unichr(0xd800), unichr(0xdbff), unichr(0xdc00), unichr(0xdfff))
    x = re.sub(RE_XML_ILLEGAL, "?", input.read()) # takes ages
    # Remove broken control unicode chars
    brokenControl = '\xc2([^\x80-\xbf])'
    x = re.sub(brokenControl, '?\g<1>', x)
    xmldoc = minidom.parseString(x)


    savanaexport = xmldoc.getElementsByTagName('savaneexport')[0]
    items = savanaexport.getElementsByTagName('item')

    outf.write('<html>\n')
    outf.write('<pre>\n')
    outf.write('<meta http-equiv="Content-Type" content="text/html; charset=UTF-8"/>\n')
    outf.write('--------------------------------------------------------------------------------\n')
    outf.write('Report generated on ' + str(current) + ' UTC\n')
    outf.write('--------------------------------------------------------------------------------\n')

    for item in items:
        squad = getTag(item, 'assigned_to')
        submitted_on = float(getTag(item, 'submitted_on'))
        firstResponseOn = getTimeOfFirstMeaningfulResponse(item)
        firstResponseDelay = firstResponseOn - submitted_on
        firstSquadAssigned = getFirstSquadAssigned(item)
        site = getTag(item, 'custom_select_box_1')
        ticketId = getTag(item, 'item_id')
        url = 'https://savannah.cern.ch/support/?%s' % ticketId
        if firstSquadAssigned and firstSquadAssigned != 'None':
            squad = firstSquadAssigned
        if (current_unix - submitted_on) > (options.openedInTheLastNDays * 86400):
            continue
        outf.write("Ticket URL: %s First assigned squad: %32s Site: %20s First response time: %5.1f hours\n" % (url, squad, site, firstResponseDelay / 3600))

    outf.write('</pre>\n')
    outf.write('</html>\n')
if __name__ == '__main__':
    main()
