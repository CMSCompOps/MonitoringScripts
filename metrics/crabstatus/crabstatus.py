#!/usr/bin/python

''''
This script calculates the  CRAB status of a site based on 
    - Morgue : If a site is in the morgue, it'll be set to disabled 
    - HammerCloud : If a site does not have at least a green entry on the last 3 days of HC entries, it'll be set to enabled.
    - Manual CRAB Status Metric: If a site is a T3 site, it's in this list,  and has no bad HC it'll be enabled
Inputs: Starting Timestamp in format "YYYY-mm-dd-hh-mm", Directory in which to output data
Output: Text file in output directory, named crabstatus.txt

'''

from lib import dashboard, sites, url 
from datetime import datetime, timedelta
import os
import dateutil.parser
import json
from optparse import OptionParser
import sys

# Reads a metric from SS1B
def getJSONMetric(metricNumber, hoursToRead, sitesStr, sitesVar, dateStart="2000-01-01", dateEnd=datetime.now().strftime('%Y-%m-%d')):
    urlstr = "http://dashb-ssb.cern.ch/dashboard/request.py/getplotdata?columnid=" + str(metricNumber) + "&time=" + str(hoursToRead) + "&dateFrom=" + dateStart + "&dateTo=" + dateEnd + "&site=" + sitesStr + "&sites=" + sitesVar + "&clouds=all&batch=1"
    try:
        metricData = url.read(urlstr)
        return dashboard.parseJSONMetric(metricData)
    except:
        return None

def getJSONMetricforSite(metricNumber, hoursToRead, sitesStr):
    return getJSONMetric(metricNumber, hoursToRead, sitesStr, "one")

def getJSONMetricforAllSitesForDate(metricNumber, dateStart, dateEnd):
    return getJSONMetric(metricNumber, "custom", "", "all", dateStart, dateEnd)

# Filters a dashboard metric between times
def filterMetric(metric, dateStart, dateEnd):
    resultDict = {}
    if metric is not None:
        if metric.iteritems() != None:
            for key, value in metric.iteritems():
                metricEndTime = datetime.fromtimestamp(float(key))
                metricStartTime = datetime.fromtimestamp(float(value.date))
                bool1 = dateStart > metricStartTime
                bool2 = metricStartTime < metricEndTime
                bool3 = metricEndTime > dateEnd
                if ( bool1 and bool2 and bool3) :
                    resultDict[key] = value
    return resultDict

def formatDate(datetoFormat):
    return datetoFormat.strftime("%Y-%m-%d")
print '1'


def timedelta_total_seconds(timedelta):
    try:
        return (
        timedelta.microseconds + 0.0 +
        (timedelta.seconds + timedelta.days * 24 * 3600) * 10 ** 6) / 10 ** 6
    except:
        return 0 

def secondsofIntersection(t1start, t1end, t2start, t2end):
    latest_start = max(t1start, t2start)
    earliest_end = min(t1end, t2end)
    intersection = max(timedelta_total_seconds(earliest_end - latest_start),0)
    return intersection
#Contants 
OUTPUT_P_FILE_NAME = os.path.join(sys.argv[1],"primalCrabStatus.txt")
COLORS = {}

DISABLED_STATUS = 'disabled'
COLORS[DISABLED_STATUS] = 'red'

ENABLED_STATUS = 'enabled'
COLORS[ENABLED_STATUS] = 'green'

BAD_LIFESTATUS = ['Morgue', 'morgue', 'waiting_room', 'WaitingRoom', "Waiting_Room"]
HAMMERCLOUD_OK_COLOR = 'green'
URL_ENTRY = 'https://cmssst.web.cern.ch/cmssst/crabstatus/CrabStatus.txt'

#Hammercloud from last 3 days
hcStart = datetime.utcnow() - timedelta(days = 2)
hcEnd = datetime.utcnow() + timedelta(days = 1)
hcStatus = getJSONMetricforAllSitesForDate(135, formatDate(hcStart),formatDate(hcEnd))
print '3'
#LifeStatus
lfStart = datetime.utcnow() - timedelta(days = 1)
lfEnd = datetime.utcnow() 
lfStatus = getJSONMetricforAllSitesForDate(235, formatDate(lfStart),formatDate(lfEnd))

allsites = list(set(hcStatus.getSites()))

allsitesMetric = []
for site in allsites:
    if "_Disk" in site or "_Buffer" in site or "_MSS" in site:
        continue
    print site
    tier = sites.getTier(site)
    siteCurrentLifeStatus = lfStatus.getLatestEntry(site)
    flagBadLifeStatus = False
    flagGoodHC = False
    newCrabStatus = 'unknown'
    if siteCurrentLifeStatus is not None and (siteCurrentLifeStatus.value in BAD_LIFESTATUS):
        flagBadLifeStatus = True
    siteHC = hcStatus.getSiteEntries(site).values()
    #Check HC for the last 3 days
    for entry in siteHC:
        if entry.color == HAMMERCLOUD_OK_COLOR:
            flagGoodHC = True 
    if flagBadLifeStatus == False and flagGoodHC == True:
        newCrabStatus = ENABLED_STATUS 
    if flagBadLifeStatus == True and flagGoodHC == True:
        newCrabStatus = DISABLED_STATUS 
    elif flagGoodHC == False:
        newCrabStatus = DISABLED_STATUS
    print site + " flagGoodHC :" + str(flagGoodHC) + " flagBadLifeStatus :" + str(flagBadLifeStatus)+ "New crabstatus: " + newCrabStatus     
    if newCrabStatus != 'unknown':
        	allsitesMetric.append(dashboard.entry(date = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"), name = site, value = newCrabStatus, color = COLORS.get(newCrabStatus, 'white'), url = URL_ENTRY))

if len(allsitesMetric) > 1:
    outputFileP = open(OUTPUT_P_FILE_NAME, 'w')
    outputFileP.write(dashboard.printHeader(scriptName = "LifeStatus", documentationUrl=""))
    for site in allsitesMetric:
        outputFileP.write(str(site) + '\n')
    print "\n--Output written to %s" % OUTPUT_P_FILE_NAME
    outputFileP.close()
