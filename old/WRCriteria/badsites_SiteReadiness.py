import os, sys, errno
import urllib2
import simplejson
from datetime import datetime
from datetime import timedelta
import time
from pprint import pprint
import string

#T1+T2
#url = "http://dashb-ssb.cern.ch/dashboard/request.py/getsitereadinessrankdata?columnid=45&time=%s"
#only T2
url = "http://dashb-ssb.cern.ch/dashboard/request.py/getsitereadinessrankdata?columnid=45&time=%s&sites=T2"
percentageThreshold = 0.8


def getData(url, headers=None):
    request = urllib2.Request(url, headers = headers)
    response = urllib2.urlopen(request)
    data = response.read()
    rows = simplejson.loads(data)
    return rows

def extractSitesUnderPercentage(dataRows, percentageThreshold):
    sites = []
    for row in dataRows['data']:
	siteName = row[0].split(' ')[0]
	sitePercentage = float(row[1][0][1])
	if sitePercentage < percentageThreshold:
	    sites.append(siteName)
    return sites

def main_function(outputfile_txt):
  oneWeekDataRows = getData(url % '168', headers={"Accept":"application/json"})
  threeMonthsDataRows = getData(url % '2184', headers={"Accept":"application/json"})

  oneWeekBadSites = extractSitesUnderPercentage(oneWeekDataRows, percentageThreshold)
  threeMonthsBadSites = extractSitesUnderPercentage(threeMonthsDataRows, percentageThreshold)

  #all sites
  allSites = extractSitesUnderPercentage(threeMonthsDataRows, 10)
  print allSites 
    
  badSites = [val for val in oneWeekBadSites if val in threeMonthsBadSites]
  print badSites

  #write to file for SSB
  f1=open('./'+outputfile_txt, 'w+')
  now_write=(datetime.utcnow()).strftime("%Y-%m-%d %H:%M:%S")

  f1.write('# This txt goes into SSB and marks sites red when the following condition is true:\n')
  f1.write('# Site Readiness percentage for both [last 1 week && last 3 months] < 80%\n')
  f1.write('# Readme:\n# https://raw.githubusercontent.com/CMSCompOps/MonitoringScripts/master/SR_View_SSB/WRCriteria/Readme.txt\n')
  print "Local current time :", now_write
  link="https://dashb-ssb.cern.ch/dashboard/request.py/sitereadinessrank?columnid=45#time=2184&start_date=&end_date=&sites=T0/1/2"
  for k in badSites:
    print k, 'true', 'red', link
    f1.write(now_write+'\t')        # timestamp
    f1.write(''.join(k))            # sitename
    f1.write('\ttrue')              # value
    f1.write('\tred\t')             # color
    f1.write(''.join(link))         # link
    f1.write('\n')
  for k in allSites: 
    if not k in badSites:
      print k, 'false', 'green', link
      f1.write(now_write+'\t')        # timestamp
      f1.write(''.join(k))            # sitename
      f1.write('\tfalse')             # value
      f1.write('\tgreen\t')           # color
      f1.write(''.join(link))         # link
      f1.write('\n')
if __name__ == '__main__':
  outputfile_txt=sys.argv[1]
  main_function(outputfile_txt)