''' 
This script calculates the daily metric value based on the metrics:
    - Hammercloud
    - Maintenance
    - SAM Availability
    - Good T1 Links to T1s
    - Good T1 Links from T1s
    - Good T1 Links from T2s
    - Good T1 Links to T2s
    - Active Links
The script accepts as input a date for which the daily metric will be calculated and outputs a text file with the calculation.
'''

from lib import dashboard, sites, url
from datetime import datetime, timedelta
import sys, os
import re
import dateutil.parser
import pytz
import random

# Date for generating the daily Metric value

if sys.argv[1] is not None and sys.argv[1] != "" : 
    try:
        datetmp = dateutil.parser.parse(sys.argv[1], ignoretz=True)
    except:
        print "Unable to parse input date, format is %Y-%m-%dT%H:%M:%SZ"
        raise

period = timedelta(days = 1)
realDateStart = datetmp
realDateEnd = realDateStart + timedelta(days = 1)
dateStart = realDateStart + timedelta(days = 1)
dateEnd = dateStart + period
periodStart = dateStart.replace(hour=12, minute= 0)
periodEnd = dateStart.replace(hour=12, minute= 10)
realPeriodStart = realDateStart.replace(hour=12, minute= 0)
realPeriodEnd = realDateStart.replace(hour=12, minute= 10)
realDateStartStr = realDateStart.strftime("%Y-%m-%d")
print realDateStartStr
dateStartStr = dateStart.strftime("%Y-%m-%d")
realDateEndStr = realDateEnd.strftime("%Y-%m-%d")
dateEndStr = dateEnd.strftime("%Y-%m-%d")

atMidnight = (realDateStart\
            .replace(hour=0, minute=random.randint(0,1), second=random.randint(0,59), microsecond=0) \
             ).strftime("%Y-%m-%d %H:%M:%S")

dashboardUrl = "https://dashb-ssb.cern.ch/dashboard/request.py/sitehistory?site=%s#currentView=Site+Readiness&time=custom&start_date="+ realDateStartStr +"&end_date="+ realDateEndStr+"&values=false&spline=false&white=false"

# Column IDs.
SITE_READINESS_COLUMN_NUMBER = 234
HAMMERCLOUD_COLUMN_ID = 135
MAINTENANCE_COLUMN_ID = 121
SAM_COLUMN_ID = 126

GOOD_T1_LINKS_FROM_T0 = 74
GOOD_T1_LINKS_FROM_T1 = 75
GOOD_T1_LINKS_TO_T1 = 77
GOOD_T1_LINKS_TO_T2 = 80
GOOD_T1_LINKS_FROM_T2 = 76
GOOD_T2_LINKS_TO_T1 = 79
GOOD_T2_LINKS_FROM_T1 = 78

ACTIVE_T1_LINKS_FROM_T0 = 33 
ACTIVE_T1_LINKS_TO_FROM_T1 = 35
ACTIVE_T1_LINKS_TO_T2 = 34
ACTIVE_T2_LINKS_FROM_T1 = 37 
ACTIVE_T2_LINKS_TO_T1 = 36

#Output file
OUTPUT_FILE_NAME = os.path.join(sys.argv[2],"siteReadiness.txt")
OUTPUT_FILE_CORRECTIONS = os.path.join(sys.argv[2],"siteReadiness_POSTREQUEST.txt")
#Output status
NOT_READY = "Error"
READY = "Ok"
DOWNTIME = "Downtime"

#Output color
COLOR_NOT_READY = "cError"
COLOR_READY = "cOk"
COLOR_DOWNTIME = "cDowntime"

#Color Map
OUTPUT_COLORS={}
OUTPUT_COLORS[NOT_READY] = COLOR_NOT_READY
OUTPUT_COLORS[READY] = COLOR_READY
OUTPUT_COLORS[DOWNTIME] = COLOR_DOWNTIME

# Reads a metric from SS1B
def getJSONMetric(metricNumber, hoursToRead, sitesStr, sitesVar, dateStart="2000-01-01", dateEnd=datetime.now().strftime('%Y-%m-%d')):
    urlstr = "http://dashb-ssb.cern.ch/dashboard/request.py/getplotdata?columnid=" + str(metricNumber) + "&time=" + str(hoursToRead) + "&dateFrom=" + dateStart + "&dateTo=" + dateEnd + "&site=" + sitesStr + "&sites=" + sitesVar + "&clouds=all&batch=1"
    try:
        print "Getting metric " + str(metricNumber) + ", url :" + urlstr
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

#Getting all the metrics
hammerCloud  = getJSONMetricforAllSitesForDate(HAMMERCLOUD_COLUMN_ID, dateStartStr, dateEndStr)
#Maintenance uses RealDates!!!!
maintenace  = getJSONMetricforAllSitesForDate(MAINTENANCE_COLUMN_ID, realDateStartStr, dateEndStr)
sam  = getJSONMetricforAllSitesForDate(SAM_COLUMN_ID, dateStartStr, dateEndStr)

GoodT1LinksFromT0  = getJSONMetricforAllSitesForDate(GOOD_T1_LINKS_FROM_T0, dateStartStr, dateEndStr)
GoodT1LinksFromT1  = getJSONMetricforAllSitesForDate(GOOD_T1_LINKS_FROM_T1, dateStartStr, dateEndStr)
GoodT1LinksToT1  = getJSONMetricforAllSitesForDate(GOOD_T1_LINKS_TO_T1, dateStartStr, dateEndStr)
GoodT1LinksToT2  = getJSONMetricforAllSitesForDate(GOOD_T1_LINKS_TO_T2, dateStartStr, dateEndStr)
GoodT1LinksFromT2  = getJSONMetricforAllSitesForDate(GOOD_T1_LINKS_FROM_T2, dateStartStr, dateEndStr)
GoodT2LinksFromT1  = getJSONMetricforAllSitesForDate(GOOD_T2_LINKS_FROM_T1, dateStartStr, dateEndStr)
GoodT2LinksToT1  = getJSONMetricforAllSitesForDate(GOOD_T2_LINKS_TO_T1, dateStartStr, dateEndStr)

ActiveT1LinksFromT0  = getJSONMetricforAllSitesForDate(ACTIVE_T1_LINKS_FROM_T0, dateStartStr, dateEndStr)
ActiveT1LinksToFromT1  = getJSONMetricforAllSitesForDate(ACTIVE_T1_LINKS_TO_FROM_T1, dateStartStr, dateEndStr)
ActiveT1LinksToT2  = getJSONMetricforAllSitesForDate(ACTIVE_T1_LINKS_TO_T2, dateStartStr, dateEndStr)
ActiveT2LinksFromT1  = getJSONMetricforAllSitesForDate(ACTIVE_T2_LINKS_FROM_T1, dateStartStr, dateEndStr)
ActiveT2LinksToT1  = getJSONMetricforAllSitesForDate(ACTIVE_T2_LINKS_TO_T1, dateStartStr, dateEndStr)

# A list of regular expressions for sites to ignore.
IGNORE_SITES = [re.compile("T\d.*_Buffer"), re.compile("T\d.*_Disk"), re.compile("T3.*"), re.compile("T\d.*_Export")]
# Get all sites from Hammercloud + Sam + Maintenance
allSites = ()
if sam is not None and hammerCloud is not None and maintenace is not None:
    allSites = set(sam.getSites() + hammerCloud.getSites() + maintenace.getSites() + GoodT1LinksFromT0.getSites() + GoodT1LinksFromT1.getSites())

allsitesMetric = []
if len(allSites) > 0 : 
    for site in allSites:
        isSiteIgnored = False
        for filterRe in IGNORE_SITES:
            if filterRe.match(site) != None:
                isSiteIgnored = True
        if isSiteIgnored:
            continue
        siteSam = sam.getSiteEntries(site)
        siteHammercloud = hammerCloud.getSiteEntries(site)
        siteMaintenance = maintenace.getSiteEntries(site)
        siteGoodT1LinksFromT0 = GoodT1LinksFromT0.getSiteEntries(site)
        siteGoodT1LinksFromT1 = GoodT1LinksFromT1.getSiteEntries(site)
        siteGoodT1LinksToT1 = GoodT1LinksToT1.getSiteEntries(site)
        siteGoodT1LinksToT2 = GoodT1LinksToT2.getSiteEntries(site)
        siteGoodT1LinksFromT2 = GoodT1LinksFromT2.getSiteEntries(site)
        siteGoodT2LinksFromT1 = GoodT2LinksFromT1.getSiteEntries(site)
        siteGoodT2LinksToT1 = GoodT2LinksToT1.getSiteEntries(site)
        siteActiveT1LinksFromT0 = ActiveT1LinksFromT0.getSiteEntries(site)
        siteActiveT1LinksToFromT1 = ActiveT1LinksToFromT1.getSiteEntries(site)
        siteActiveT1LinksToT2 = ActiveT1LinksToT2.getSiteEntries(site)
        siteActiveT2LinksFromT1 = ActiveT2LinksFromT1.getSiteEntries(site)
        siteActiveT2LinksToT1 =ActiveT2LinksToT1.getSiteEntries(site)
        
        # remove data that is not between start time and end time.
        # We do this because the dashboard allows a days granularity only. 
        filteredSam = filterMetric(siteSam, periodStart, periodEnd)
        filteredSiteSam = filterMetric( siteSam ,periodStart,periodEnd)
        filteredSiteHammercloud = filterMetric( siteHammercloud ,periodStart,periodEnd)
        # Maintenance column should be the whole day, and not arround sampling period.
        #filteredSiteMaintenance = filterMetric( siteMaintenance ,realPeriodStart,realPeriodEnd)
        filteredSiteMaintenance = siteMaintenance
        filteredSiteGoodT1LinksFromT0 = filterMetric( siteGoodT1LinksFromT0 ,periodStart,periodEnd)
        filteredSiteGoodT1LinksFromT1 = filterMetric( siteGoodT1LinksFromT1 ,periodStart,periodEnd)
        filteredSiteGoodT1LinksToT1 = filterMetric( siteGoodT1LinksToT1 ,periodStart,periodEnd)
        filteredSiteGoodT1LinksToT2 = filterMetric( siteGoodT1LinksToT2 ,periodStart,periodEnd)
        filteredSiteGoodT1LinksFromT2 = filterMetric( siteGoodT1LinksFromT2 ,periodStart,periodEnd)
        filteredSiteGoodT2LinksFromT1 = filterMetric( siteGoodT2LinksFromT1 ,periodStart,periodEnd)
        filteredSiteGoodT2LinksToT1 = filterMetric( siteGoodT2LinksToT1 ,periodStart,periodEnd)
        filteredSiteActiveT1LinksFromT0 = siteActiveT1LinksFromT0 
        filteredSiteActiveT1LinksToFromT1 = siteActiveT1LinksToFromT1 
        filteredSiteActiveT1LinksToT2 =  siteActiveT1LinksToT2 
        filteredSiteActiveT2LinksFromT1 = siteActiveT2LinksFromT1 
        filteredSiteActiveT2LinksToT1 = siteActiveT2LinksToT1 
        #siteFilteredGoodLinks = [filteredSiteGoodT1LinksFromT0, filteredSiteGoodT1LinksFromT1, filteredSiteGoodT1LinksToT1, filteredSiteGoodT1LinksToT2, filteredSiteGoodT1LinksFromT2, filteredSiteGoodT2LinksFromT1, filteredSiteGoodT2LinksToT1 ]
        siteFilteredGoodLinks = [filteredSiteGoodT1LinksFromT1, filteredSiteGoodT1LinksToT1, filteredSiteGoodT1LinksToT2, filteredSiteGoodT1LinksFromT2, filteredSiteGoodT2LinksFromT1, filteredSiteGoodT2LinksToT1 ]
        hammerCloudNaFlag = True
        samNaFlag = True
        linksFlag = True
        siteTier = sites.getTier(site)
        dailyMetric = READY
        if siteTier == 0:
            #Evaluate Hammercloud for the period. Values between 0 and 100
            # HC must be above 90% for all values
            for key, entry in filteredSiteHammercloud.iteritems():
                if entry.value != "n/a":
                    hammerCloudNaFlag = False
                    try:
                        value = float(entry.value)
                        if value < 90.0 or entry.color == "red":
                            dailyMetric = NOT_READY
                    except:
                        pass
                else:
                    hammerCloudNaFlag = True
            #Evaluate SAM for the period. values between 0 and 100
            # SAM must be above 90% for all sites.
            for key, entry in filteredSiteSam.iteritems():
                if entry.value != "n/a":
                    samNaFlag = False
                    try:
                        value = float(entry.value)
                        if value < 90.0 or entry.color == "red":
                            dailyMetric = NOT_READY
                    except:
                        pass
                else:
                    samNaFlag = True
        elif siteTier == 1:
            #Evaluate Hammercloud for the period. Values between 0 and 100
            # HC must be above 90% for all values
            for key, entry in filteredSiteHammercloud.iteritems():
                if entry.value != "n/a":
                    hammerCloudNaFlag = False
                    try:
                        value = float(entry.value)
                        if value < 90.0 or entry.color == "red":
                            dailyMetric = NOT_READY
                    except:
                        pass
                else:
                    hammerCloudNaFlag = True
            #Evaluate SAM for the period. values between 0 and 100
            # SAM must be above 90% for all sites.
            for key, entry in filteredSiteSam.iteritems():
                if entry.value != "n/a":
                    samNaFlag = False
                    try:
                        value = float(entry.value)
                        if value < 90.0 or entry.color == "red":
                            dailyMetric = NOT_READY
                    except:
                        pass
                else:
                    samNaFlag = True
            #Evaluate links for T1:
            #    Active T1 links from T0 >1
            for key, entry in filteredSiteActiveT1LinksFromT0.iteritems():
                try:
                    if int(entry.value) < 1 or entry.color =="red":
                        dailyMetric = NOT_READY
                except:
                    pass
            #    Active T1 links from/to T1s > 4 for up and two. Data is '26(d)-26(u)'
            for key, entry in filteredSiteActiveT1LinksToFromT1.iteritems():
                try:
                    down, up = re.match("(\d\d)\(d\)-(\d\d)\(u\)", entry.value).groups()
                    up = int(up)
                    down = int(down)
                    color = entry.color
                    if up < 5 or down < 5 or color == "red":
                        dailyMetric = NOT_READY
                except:
                    pass
            #    Active T1 links to T2s > 20            #    Good Links, Half links must be above 50 %. Values between 0 and 100
            for key, entry in filteredSiteActiveT1LinksToT2.iteritems():
                try:
                    value = int(entry.value)
                    color = entry.color
                    if value < 20 or color == "red" :
                        dailyMetric = NOT_READY
                except:
                    pass
            #Good Links
            for link in siteFilteredGoodLinks:
                for key, entry in link.iteritems():
                    try:
                        good, total = re.match("(\d+)/(\d+)", entry.value).groups()
                        good = float(good)
                        total = float(total)
                        if good/total < 0.5 or good<1 or entry.color == "red":
                            dailyMetric = NOT_READY
                    except:
                        pass
        elif siteTier == 2:
            # Evaluate Hammercloud for the period. Values between 0 and 100
            # HC must be above 80% for all values
            for key, entry in filteredSiteHammercloud.iteritems():
                if entry.value != "n/a":
                    hammerCloudNaFlag = False
                    try:
                        value = float(entry.value)
                        color = entry.color
                        if value < 80.0 or color == "red":
                            dailyMetric = NOT_READY
                    except:
                        pass
                else:
                    hammerCloudNaFlag = True
            # Evaluate SAM for the period. values between 0 and 100
            # SAM must be above 80% for all sites.
            for key, entry in filteredSiteSam.iteritems():
                if entry.value != "n/a":
                    samNaFlag = False
                    try:
                        value = float(entry.value)
                        color = entry.color
                        if value < 80.0 or color == "red":
                            dailyMetric = NOT_READY
                    except:
                        pass
                else:
                    samNaFlag = True
            #Evaluate links for T2:
            #    Active T2 links from T1 > 4
            for key, entry in filteredSiteActiveT2LinksFromT1.iteritems():
                try:
                    if int(entry.value) < 4 or entry.color == 'red':
                        dailyMetric = NOT_READY
                except:
                    pass
            #    Active T2 links from T1 > 2
            for key, entry in filteredSiteActiveT2LinksToT1.iteritems():
                try:
                    if int(entry.value) < 2 or entry.color == "red":
                        dailyMetric = NOT_READY
                except:
                    pass
            #Good Links
            for link in siteFilteredGoodLinks:
                for key, entry in link.iteritems():
                    try:
                        good, total = re.match("(\d+)/(\d+)", entry.value).groups()
                        good = float(good)
                        total = float(total)
                        if good/total < 0.5 or good < 1 or total < 1 or entry.color == "red":
                            dailyMetric = NOT_READY
                    except:
                        pass
        elif siteTier == 3: 
            site
        else:
            pass
        if dailyMetric == NOT_READY:
            for key, entry in filteredSiteMaintenance.iteritems():
                try:
                    if entry.color == 'saddlebrown':
                        dailyMetric = DOWNTIME
                except:
                    pass 
        allsitesMetric.append([site, dailyMetric,hammerCloudNaFlag, samNaFlag])
else:
    print "I couldn't find any Sam, Hammercloud, and Maintenance data, Something's wrong, I'm dead Jim"

dailyMetricEntries = []
for metric in allsitesMetric:
        #print metric[1]
    if (not (metric[3] == True and metric[2] == True)):
        dailyMetricEntries.append(dashboard.entry(date = atMidnight, name = metric[0], value = metric[1], color = OUTPUT_COLORS[metric[1]], url = dashboardUrl % metric[0]))

startDateStr = realDateStart.replace(hour=0, minute=0, second=0, microsecond=0).strftime("%Y-%m-%d %H:%M:%S")
endDateStr = (realDateStart.replace(hour=00, minute=00, second=00, microsecond=0) + timedelta(days=1)).strftime("%Y-%m-%d %H:%M:%S")


if len(dailyMetricEntries) > 1:
    outputFile = open(OUTPUT_FILE_NAME, 'w')
    correctionOutputFile = open(OUTPUT_FILE_CORRECTIONS, 'a')
    for site in dailyMetricEntries:
        outputFile.write(str(site) + '\n')
        correctionOutputFile.write(("\t".join([startDateStr, endDateStr, str(SITE_READINESS_COLUMN_NUMBER), site.name, site.value, site.color, site.url, "nvalue=0"]))+"\n")
    print "\n--Output written to %s" % OUTPUT_FILE_NAME
    correctionOutputFile.close()
    outputFile.close()

