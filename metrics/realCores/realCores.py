from lib import dashboard, sites, url
from datetime import datetime, timedelta
import time
import json
import urllib
import os, sys

dateStart = datetime.now() 
dateEnd = dateStart + timedelta(days = 1)
dateStartStr = dateStart.strftime("%Y-%m-%d")
dateEndStr = dateEnd.strftime("%Y-%m-%d")

# Column IDs.
REALCORES_COLUMN_ID = 136
MAXUSED_URL = "http://cms-gwmsmon.cern.ch/totalview/json/maxused"

#Output file
OUTPUT_FILE_NAME = os.path.join(sys.argv[1],"real.txt")


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

#Getting all the metrics
realCoresMetric  = getJSONMetricforAllSitesForDate(REALCORES_COLUMN_ID, dateStartStr, dateEndStr)
# Get Json file for maxused
response = urllib.urlopen(MAXUSED_URL)
maxUsedData = json.loads(response.read())
newEntries = []
for site in realCoresMetric.getSites():
    entry= realCoresMetric.getLatestEntry(site)
    try :
        currentValue = int(entry.value)
        isNa = False
    except ValueError:
        currentValue = entry.value
        isNa = True 
    siteMaxUsedData = maxUsedData.get(site, {}).get('onemonth',0)
    if isNa == False:
        newValue = max(currentValue, siteMaxUsedData)
    else :
        newValue = currentValue
    entry.value=newValue
    entry.date = int(time.time())
    newEntries.append(entry)

if len(newEntries) > 1:
    outputFile = open(OUTPUT_FILE_NAME, 'w')
    for site in newEntries:
        outputFile.write(str(site) + '\n')
        print str(site)
    print "\n--Output written to %s, %d lines" % (OUTPUT_FILE_NAME, len(newEntries))
    outputFile.close()

