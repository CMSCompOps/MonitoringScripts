import os, sys, errno
import urllib2
import json as simplejson
from datetime import datetime
from datetime import timedelta
import time
from pprint import pprint
import string

# Criteria
percentageThreshold = 0.8

#T1+T2
#url = "http://dashb-ssb.cern.ch/dashboard/request.py/getsitereadinessrankdata?columnid=45&time=%s"
#only T2s
url = "http://dashb-ssb.cern.ch/dashboard/request.py/getsitereadinessrankdata?columnid=45&time=%s&sites=T2"

def getData(url, headers=None):
    request = urllib2.Request(url, headers = headers)
    response = urllib2.urlopen(request)
    data = response.read()
    rows = simplejson.loads(data)
    return rows

def extractSitesAboveThreshold(dataRows, percentageThreshold):
    sites = []
    for row in dataRows['data']:
        siteName = row[0].split(' ')[0]
        sitePercentage = float(row[1][0][1])
        if sitePercentage >= percentageThreshold:
            sites.append(siteName)
    return sites

oneWeekDataRows = getData(url % '168', headers={"Accept":"application/json"})
threeMonthsDataRows = getData(url % '2184', headers={"Accept":"application/json"})

# Active Sites = SR >=60% for last week OR last 3 months
oneWeek = extractSitesAboveThreshold(oneWeekDataRows, percentageThreshold)
threeMonths = extractSitesAboveThreshold(threeMonthsDataRows, percentageThreshold)
activeSites = oneWeek
activeSites.extend(x for x in threeMonths if not x in oneWeek)

#write to file in the SSB feed format
outFile="WasCommissionedT2ForSiteMonitor.txt"
f1=open('./'+outFile, 'a')
now_write=(datetime.utcnow()).strftime("%Y-%m-%d %H:%M:%S")
print "ActiveSites.py results:", now_write
for k in activeSites:
    print ''.join(k)
    f1.write(now_write+'\t')    # timestamp
    f1.write(''.join(k))        # sitename
    f1.write('\t1')             # value
    f1.write('\tgreen')         # color
                                # link
    f1.write('\thttps://cmsdoc.cern.ch/cms/LCG/SiteComm/T2WaitingList/WasCommissionedT2ForSiteMonitor.txt\n')