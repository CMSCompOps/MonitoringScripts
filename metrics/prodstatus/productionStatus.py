#!/usr/bin/python

''''
This script calculates the Production status of a site based on 
    - Downtimes: If a site has a declared downtime in the next 24h that is longer than 24h it'll be drained
    - Waiting Room / Morgue : If a site is in the waiting room or morgue, or any state not 'OK' it'll be set on drain
    - Manual override : If a site is overriden to any status [drain, down, on] it'll get this value
    - Site Readiness :  If a site was on drain 0.66 T of bad readiness on a 72 hour readiness value, it'll be marked on drain.
                        If a site is on drain and has >48 h days of good SR, it'll be out of drain

Inputs: Starting Timestamp in format "YYYY-mm-dd-hh-mm", Directory in which to output data
Output: Text file in current directory, named Hammercloud.txt

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
        print urlstr
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
OUTPUT_P_FILE_NAME = os.path.join(sys.argv[1],"primalProdStatus.txt")
COLORS = {}
DRAIN_STATUS = 'drain'
COLORS[DRAIN_STATUS] = 'yellow'

DOWN_STATUS = 'disabled'
COLORS[DOWN_STATUS] = 'red'

ON_STATUS = 'enabled'
COLORS[ON_STATUS] = 'green'

TIER0_STATUS = 'test'
COLORS[TIER0_STATUS] = 'green'

BAD_LIFESTATUS = ['Waiting_Room', 'Morgue', 'waiting_room', 'morgue', 'waitingroom']
DOWNTIMECOLOR = 'saddlebrown'
SITEREADINESS_OK = 'Ok'
SITEREADINESS_BAD = 'Error'


#Downtimes from last week to next year
downtimeStart = datetime.utcnow() - timedelta(weeks = 1)
downtimeEnd = datetime.utcnow() + timedelta(weeks = 1)
downtimes = getJSONMetricforAllSitesForDate(121, formatDate(downtimeStart),formatDate(downtimeEnd))
print'Got Downtimes'
#Site Readiness from last 7 days
srStart = datetime.utcnow() - timedelta(days = 7)
srEnd = datetime.utcnow() 
srStatus = getJSONMetricforAllSitesForDate(234, formatDate(srStart),formatDate(srEnd))
print 'Got Readiness'
#LifeStatus
lfStart = datetime.utcnow() - timedelta(days = 2)
lfEnd = datetime.utcnow() 
lfStatus = getJSONMetricforAllSitesForDate(235, formatDate(lfStart),formatDate(lfEnd))
print 'Got LifeStatus'
#Current value prod_status
pdStart = datetime.utcnow() - timedelta(days = 1)
pdEnd = datetime.utcnow() 
pdStatus = getJSONMetricforAllSitesForDate(237, formatDate(pdStart),formatDate(pdEnd))

allsites = set(srStatus.getSites()).union(set(lfStatus.getSites())).union(set(downtimes.getSites()))

allsitesMetric = []
for site in allsites:
    tier = sites.getTier(site)
    siteCurrentLifeStatus = lfStatus.getLatestEntry(site)
    flagLifeStatus = False
    if siteCurrentLifeStatus is not None and (siteCurrentLifeStatus.value in BAD_LIFESTATUS):
        flagLifeStatus = True
    siteSiteReadiness = srStatus.getSiteEntries(site)
    siteCurrentProd_Status = pdStatus.getLatestEntry(site) 
    siteDowntimes = downtimes.getSiteEntries(site)
    if tier == 2 or tier ==1: 
        #Check if the site will be on downtime in 24 hours or is on downtime 
        flagDowntime = False
        for key, value in siteDowntimes.iteritems():
            if value.color == 'saddlebrown':
                dateEnd = datetime.utcfromtimestamp(key)
                dateStart = datetime.utcfromtimestamp(value.date)
                intersection = 0 
                if timedelta_total_seconds(dateEnd - dateStart) > 86400:
                    currenttime = datetime.utcnow()
                    twodays = currenttime + timedelta(days = 2)
                    latest_start = max(dateStart, currenttime)
                    earliest_end = min(dateEnd, twodays)
                    intersection = timedelta_total_seconds(earliest_end - latest_start)
                if intersection > 0:
                    flagDowntime = True
        #Check SR last 3 days
        siteSiteReadinessTotal = {}
        siteSiteReadiness2day = {}
        for key, value in siteSiteReadiness.iteritems():
            dateEnd = datetime.fromtimestamp(key)
            dateStart = datetime.fromtimestamp(value.date)
            #print str(dateStart) + " to " + str(dateEnd)
            status = value.value
            # last day
            dayloop = 0
            days = []
            currentDayEnd = datetime.utcnow().replace(hour=00, minute=00, second=00, microsecond=00)
            for x in range(1, 7):
                day_end = currentDayEnd - timedelta(days = x) 
                day_start = currentDayEnd - timedelta(days = x + 1) 
                day = [day_start , day_end]
                days.append(day)
#            for day in days:
#                print str(day[0]) + " " + str(day[1])
            counter = 0 
            for day in days:
                if counter > 1:
                    break
                if day[0].weekday() < 8:
                    siteSiteReadiness2day[status] = siteSiteReadiness2day.get(status, 0 ) +secondsofIntersection(dateStart, dateEnd, day[0], day[1])
                    counter +=  1
                else:
                    continue
            counter = 0 
            for day in days:
                if counter > 2:
                    break
                if day[0].weekday() < 6:
                    siteSiteReadinessTotal[status] = siteSiteReadinessTotal.get(status, 0 ) +secondsofIntersection(dateStart, dateEnd, day[0], day[1])
                    counter +=  1
                else:
                    continue
        totalseconds = 0
        for key, value in siteSiteReadinessTotal.iteritems():
            if key == 'Ok' or key == 'Error' or key == 'OK':
                totalseconds += value
        if totalseconds > 0 :
            print (siteSiteReadinessTotal.get('Ok', 0.0) +  siteSiteReadinessTotal.get('OK', 0.0))
            readinessScore  = (siteSiteReadinessTotal.get('Ok', 0.0) +  siteSiteReadinessTotal.get('OK', 0.0)) / totalseconds
        else:
            readinessScore = -1.0 
        totalseconds2 = 0
        for key, value in siteSiteReadiness2day.iteritems():
            if key == 'Ok' or key == 'Error' or key == 'OK':
                totalseconds2 += value
        if totalseconds > 0 :
            print (siteSiteReadiness2day.get('Ok', 0.0) +  siteSiteReadiness2day.get('OK', 0.0))
            readinessScore2day  = (siteSiteReadiness2day.get('Ok', 0.0) +  siteSiteReadiness2day.get('OK', 0.0)) / totalseconds2
        else:
            readinessScore2day = -1.0 
        #Logic to calculate new prod status
        print "site + " + site + " 2 day = " + str(readinessScore2day) +" ," + str(totalseconds2) + " 3 day = " + str(readinessScore) + " , " + str(totalseconds2)
        newProdStatus = 'unknown'
        if siteCurrentProd_Status != None and siteCurrentProd_Status.value == TIER0_STATUS:
            newProdStatus = TIER0_STATUS
        if siteCurrentProd_Status != None and siteCurrentProd_Status.value == DOWN_STATUS:
            newProdStatus = DOWN_STATUS
        if siteCurrentProd_Status != None and siteCurrentProd_Status.value == ON_STATUS:
            if (flagDowntime or flagLifeStatus) or (readinessScore < 0.6):
                newProdStatus = DRAIN_STATUS
            else:
                newProdStatus = ON_STATUS
        if siteCurrentProd_Status != None and siteCurrentProd_Status.value == DRAIN_STATUS:
            if not flagDowntime and not flagLifeStatus and readinessScore2day > 0.9:
                newProdStatus = ON_STATUS
            else:
                newProdStatus = DRAIN_STATUS
	if siteCurrentProd_Status == None and newProdStatus == 'unknown':
		if (flagDowntime or flagLifeStatus) or readinessScore < 0.6:
			newProdStatus = DRAIN_STATUS
		elif readinessScore2day > 0.9:
			newProdStatus = ON_STATUS
                else:
                        newProdStatus = DRAIN_STATUS
        if newProdStatus != 'unknown':
        	allsitesMetric.append(dashboard.entry(date = datetime.now().strftime("%Y-%m-%d %H:%M:%S"), name = site, value = newProdStatus, color = COLORS.get(newProdStatus, 'white'), url = 'https://twiki.cern.ch/twiki/bin/view/CMS/SiteSupportSiteStatusSiteReadiness'))

if len(allsitesMetric) > 1:
    outputFileP = open(OUTPUT_P_FILE_NAME, 'w')
    for site in allsitesMetric:
        outputFileP.write(str(site) + '\n')
    print "\n--Output written to %s" % OUTPUT_P_FILE_NAME
    outputFileP.close()
