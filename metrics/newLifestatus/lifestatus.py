'''
Created on Oct 6, 2015

@author: gastonlp
'''
from lib import dashboard, sites, url
from datetime import datetime, timedelta, time
import json
from time import strftime
import os
import sys
import pytz
import dateutil.parser

# Date for generating the daily Metric value
if sys.argv[1] is not None and sys.argv[1] != "" : 
    try:
        datetmp = dateutil.parser.parse(sys.argv[1], ignoretz=True)
    except:
        print "Unable to parse input date, format is %Y-%m-%dT%H:%M:%SZ"
        raise
dayToProcess = datetmp
dayToProcessStr  = dayToProcess.strftime("%Y-%m-%d")

dayToProcessMinus15 = dayToProcess + timedelta(days = -15)
dayToProcessMinus15Str = dayToProcessMinus15.strftime("%Y-%m-%d")
dayToProcessMinus30 = dayToProcess + timedelta(days = -30)
dayToProcessMinus30Str = dayToProcessMinus30.strftime("%Y-%m-%d")

#Variables
LIFE_STATUS_COLUMN_NUMBER = 235
LIFE_STATUS_MANUAL_OVERRIDE_COLUMN_NUMBER = 232
SITE_READINESS_COLUMN_NUMBER = 234
STATUS_OK = "OK"
STATUS_WAITING_ROOM_OLD = "Waiting Room"
STATUS_WAITING_ROOM = "Waiting_Room"
STATUS_WAITING_ROOM_ARRAY = [STATUS_WAITING_ROOM_OLD, STATUS_WAITING_ROOM]
STATUS_MORGUE = "Morgue"
STATUS_READY = "Ok"
STATUS_NOTREADY = "Error"
STATUS_DOWNTIME = "Downtime"
COLOR_OK = "cOk"
COLOR_WAITING_ROOM = "cWaitingRoom"
COLOR_MORGUE = "cMorgue"
OUTPUT_FILE_LIFESTATUS_NAME = os.path.join(sys.argv[2],"lifeStatus.txt")
OUTPUT_FILE_WAITING_ROOM_NAME = os.path.join(sys.argv[2],"waitingRoom.txt") 
OUTPUT_FILE_MORGUE_NAME = os.path.join(sys.argv[2],"morgue.txt")
OUTPUT_FILE_ACTIVE_T2s_NAME = os.path.join(sys.argv[2],"activeT2s.txt") 
OUTPUT_FILE_LOGFILE = os.path.join(sys.argv[2],"lifeStatus_log.txt")
DAYS_IN_MORGUE_THRESHOLD = 30
LOGFILE_URL = "https://twiki.cern.ch/twiki/bin/view/CMSPublic/CurrentWaitingRoomAndMorgue"
LOG_HEADER =  "|*Site Name*|*Current Life Status*|*%OK in last week*|*%OK last 3 months*|*Days in Waiting Room in last 3 months*|*Days in Morgue in last 2 weeks*|"
todayAtMidnight = dayToProcess.replace(hour=0, minute=0, second=1, microsecond=0).strftime("%Y-%m-%d %H:%M:%S")
print todayAtMidnight

# Reads a metric from SSB
def getJSONMetric(metricNumber, hoursToRead, sitesStr, sitesVar, dateStart="2000-01-01", dateEnd=datetime.now().strftime('%Y-%m-%d')):
    urlstr = "http://dashb-ssb.cern.ch/dashboard/request.py/getplotdata?columnid=" + str(metricNumber) + "&time=" + str(hoursToRead) + "&dateFrom=" + dateStart + "&dateTo=" + dateEnd + "&site=" + sitesStr + "&sites=" + sitesVar + "&clouds=all&batch=1"
    print urlstr
    try:
        metricData = url.read(urlstr)
        return dashboard.parseJSONMetric(metricData)
    except:
        return None

def getJSONMetricforSite(metricNumber, hoursToRead, sitesStr):
    return getJSONMetric(metricNumber, hoursToRead, sitesStr, "one")

def getJSONMetricforAllSites(metricNumber,dateStart, dateEnd):
    return getJSONMetric(metricNumber, "custom", "", "all", dateStart, dateEnd)

def getJSONMetricforAllSitesHours(metricNumber,houstoRead):
    return getJSONMetric(metricNumber, houstoRead, "", "all")

# Class to hold the results
class SiteData:
    name = None
    badDaysin15days = 0
    goodLast3 = 0
    goodLast5 = 0
    lastDay = "Unknown"
    currentLifeStatus = "OK"
    daysInWaitingRoom = 0
    manualOverride = "No"
    daysInMorgue=0
    newlifeStatus = "Unknown"

    def __init__(self, siteName, bad15, good3, good5, lastDay, siteCurrentLifeStatus, siteManualOverride, siteDaysInWaitingRoom, siteDaysInMorgue):
        self.name = siteName
        self.badDaysin15days = int(bad15)
        self.goodLast3 = int(good3)
        self.goodLast5 = int(good5)
        self.lastDay = lastDay
        self.currentLifeStatus = siteCurrentLifeStatus
        self.daysInWaitingRoom = siteDaysInWaitingRoom
        self.manualOverride = siteManualOverride
        self.daysInMorgue = siteDaysInMorgue
        self.newlifeStatus = self.calculateSiteStatus()
        
    def calculateSiteStatus(self):
        if self.manualOverride is None and self.currentLifeStatus is None:
            return None
        elif self.manualOverride is not None and self.manualOverride.strip() == STATUS_OK:
            print "Site %s life status manually overriden to %s" % (self.name, self.manualOverride)
            return STATUS_OK
        elif self.manualOverride is not None and self.manualOverride.strip() in STATUS_WAITING_ROOM_ARRAY:
            print "Site %s life status manually overriden to %s" % (self.name, self.manualOverride)
            return STATUS_WAITING_ROOM
        elif self.manualOverride is not None and self.manualOverride.strip() == STATUS_MORGUE:
            print "Site %s life status manually overriden to %s" % (self.name, self.manualOverride)
            return STATUS_MORGUE
        elif self.currentLifeStatus.lower().strip() == STATUS_OK.lower():
            if (self.badDaysin15days >= 5 and self.lastDay == STATUS_NOTREADY):
                return STATUS_WAITING_ROOM
            else:
                return STATUS_OK
        elif self.currentLifeStatus.strip() in STATUS_WAITING_ROOM_ARRAY:
            if (self.goodLast3 >= 3 and self.lastDay == STATUS_READY and self.daysInMorgue < 1):
                return STATUS_OK
            elif (self.daysInWaitingRoom > DAYS_IN_MORGUE_THRESHOLD):
                return STATUS_MORGUE
            else:
                return STATUS_WAITING_ROOM 
        elif self.currentLifeStatus.lower().strip() == STATUS_MORGUE.lower():
            if self.goodLast5 >= 5:
                return STATUS_WAITING_ROOM
            else :
                return STATUS_MORGUE
        else :
            return self.currentLifeStatus
    def __str__(self):
        '''Site Name|Current Life Status|%OK in last week|%OK last 3 months|No. days in Waiting Room in last 3 months|No. days in Morgue in last 2 weeks'''
        return "|*%s*|%s|%d|%d|%s|%s|" % (self.name, self.currentLifeStatus, self.goodLast3, self.goodLast5, str(self.daysInWaitingRoom) , str(self.daysInMorgue))

def binSiteEntries(daysInArray, siteEntries, dateEnd):
    dayBin= {}
    for x in range(1,daysInArray+1):
        dayBin[dateEnd.replace(hour=12, minute=0, second=1, microsecond=0) + timedelta (days= -1*x)] = "NoneYet"
    for day, value in dayBin.iteritems():
        for endDateUnix, entry in siteEntries.iteritems():
            endDate = datetime.utcfromtimestamp(endDateUnix)
            startDate = datetime.utcfromtimestamp(entry.date)
            if day > startDate and day < endDate:
                dayBin[day] = entry.value
    stats = {}
    stats_NoWeekend = {}
    dayBin2= dayBin.copy()
    keys = dayBin2.keys()
    for day in keys:
        if day.weekday() == 6 or day.weekday() == 5:
            del dayBin2[day]

    for i in set(dayBin.values()): 
        stats[i] = dayBin.values().count(i)
    
    for i in set(dayBin2.values()): 
        stats_NoWeekend[i] = dayBin2.values().count(i)
    
    return stats, stats_NoWeekend, dayBin, dayBin2, len(dayBin), len(dayBin2)


#Main
print "--Getting current columns"
# Get Last 30 days of lifeStatus. 
currentLifeStatus = getJSONMetricforAllSites(LIFE_STATUS_COLUMN_NUMBER, dayToProcessMinus30Str, dayToProcessStr)
# last 15 days readiness
fifteenDaysReadiness = getJSONMetricforAllSites(SITE_READINESS_COLUMN_NUMBER, dayToProcessMinus15Str, dayToProcessStr)
# Get current manual Life Status . (Last 1 hours) 
currentManualLifeStatus = getJSONMetricforAllSitesHours(LIFE_STATUS_MANUAL_OVERRIDE_COLUMN_NUMBER,1 )
# Get site info from SiteDB
sitesfromSSB = sites.getSites()
# Get a list of all sites
allsites = (set(sitesfromSSB.keys())).union(set(currentLifeStatus.getSites()))
allsites = allsites.union(set(currentManualLifeStatus.getSites()))
allSitesInfo ={}

for site in allsites:
    #Get current life status
    siteCurrentStatus = currentLifeStatus.getLatestEntry(site).value if currentLifeStatus.getLatestEntry(site) is not None else None
    #Get current manual life status
    siteCurrentManualoverride = currentManualLifeStatus.getLatestEntry(site).value if currentManualLifeStatus.getLatestEntry(site) is not None else None
    siteFifteenDaysReadiness = fifteenDaysReadiness.getSiteEntries(site)
    #Get site time in Waiting Room
    siteDaysinWaitingRoom = 0
    siteDaysMorgue = 0
    siteLifeStatusHistory = currentLifeStatus.getSiteEntries(site)
    if siteLifeStatusHistory is not None:
        daysInWaitingroomStats = binSiteEntries(30, siteLifeStatusHistory, dayToProcess)[0]
        daysInMorgueStats = binSiteEntries(14, siteLifeStatusHistory, dayToProcess)[0]
        siteDaysinWaitingRoom = daysInWaitingroomStats.get(STATUS_WAITING_ROOM, 0) + daysInWaitingroomStats.get(STATUS_WAITING_ROOM_OLD,0)
        siteDaysMorgue = daysInMorgueStats.get(STATUS_MORGUE,0)
    if siteFifteenDaysReadiness is not None:
        # Bad days in 15 days without weekends!
        siteBadDaysInLast2weeks = (binSiteEntries(15, siteFifteenDaysReadiness, dayToProcess)[1]).get(STATUS_NOTREADY, 0)
        # Good days in the last 3 days with weekends.
        siteGoodDaysInLast3days= (binSiteEntries(3, siteFifteenDaysReadiness, dayToProcess)[0]).get(STATUS_READY, 0)
        # Good days in the last 5 days with weekends, for Morgue sites.
        siteGoodDaysInLast5days= (binSiteEntries(5, siteFifteenDaysReadiness, dayToProcess)[0]).get(STATUS_READY, 0)
        siteLastDays = fifteenDaysReadiness.getLatestEntry(site)
    siteInfo = SiteData(site,  siteBadDaysInLast2weeks, siteGoodDaysInLast3days, siteGoodDaysInLast5days, siteLastDays, siteCurrentStatus, siteCurrentManualoverride, siteDaysinWaitingRoom, siteDaysMorgue)
    allSitesInfo[site] = siteInfo

waitingRoomEntries =[]
morgueEntries =[]
lifeStatusEntries = []
print "\n\n--Calculating new life status."

for sitename, siteInfo in allSitesInfo.iteritems():
    newlifeStatus = siteInfo.calculateSiteStatus()
    if newlifeStatus == STATUS_MORGUE:
        siteColor = COLOR_MORGUE
        morgueColor = "red"
        waitingRoomColor = "red"
        morgueValue = "in"
        waitingRoomValue = "in"
    elif newlifeStatus == STATUS_WAITING_ROOM:
        siteColor = COLOR_WAITING_ROOM
        morgueColor = "green"
        waitingRoomColor = "red"
        morgueValue = "out"
        waitingRoomValue = "in"
    elif newlifeStatus == STATUS_OK:
        siteColor = COLOR_OK
        morgueColor = "green"
        waitingRoomColor = "green"
        morgueValue = "out"
        waitingRoomValue = "out"
    if newlifeStatus is not None: lifeStatusEntries.append(dashboard.entry(date = todayAtMidnight, name = siteInfo.name, value = newlifeStatus, color = siteColor, url = LOGFILE_URL))
    if newlifeStatus is not None: morgueEntries.append(dashboard.entry(date = todayAtMidnight, name = siteInfo.name, value = morgueValue, color = morgueColor, url = LOGFILE_URL))
    if newlifeStatus is not None: waitingRoomEntries.append(dashboard.entry(date = todayAtMidnight, name = siteInfo.name, value = waitingRoomValue, color = waitingRoomColor, url = LOGFILE_URL))


logOutputFile = open(OUTPUT_FILE_LOGFILE, 'w')
logOutputFile.write(LOG_HEADER+'\n')
lifeStatusOutputFile = open(OUTPUT_FILE_LIFESTATUS_NAME, 'w')
for site in lifeStatusEntries:
    lifeStatusOutputFile.write(str(site) + '\n')
    if site.value != STATUS_OK:
        logline = str(allSitesInfo.get(site.name, ""))
        logOutputFile.write(logline + '\n')
logOutputFile.write("Output generated at %s \n" % todayAtMidnight)
print "\n--Life Status Output written to %s" % OUTPUT_FILE_LIFESTATUS_NAME
print "\n--Log Output written to %s" % OUTPUT_FILE_LOGFILE
lifeStatusOutputFile.close()
logOutputFile.close()

morgueOutputFile = open(OUTPUT_FILE_MORGUE_NAME, 'w')
for site in morgueEntries:
    morgueOutputFile.write(str(site) + '\n')
print "\n--Morgue output written to %s" % OUTPUT_FILE_MORGUE_NAME
morgueOutputFile.close()

waitingRoomOutputFile = open(OUTPUT_FILE_WAITING_ROOM_NAME, 'w')
for site in waitingRoomEntries:
    waitingRoomOutputFile.write(str(site) + '\n')
print "\n--Waiting Room output written to %s" % OUTPUT_FILE_WAITING_ROOM_NAME
waitingRoomOutputFile.close()


