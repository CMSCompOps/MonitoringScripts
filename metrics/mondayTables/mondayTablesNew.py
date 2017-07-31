'''
Created on Sep 28, 2015

@author: gastonlp
'''
from lib import dashboard, url
from datetime import datetime, timedelta, time
import os
import sys 
import pytz
# Metric numbers
WAITING_ROOM_COLUMN_ID = 234
MORGUE_COLUMN_ID = 234
GOOD_T2_LINKS_TO_T1s = 79 
GOOD_T2_LINKS_FROM_T1s = 78
DISK_PLEDGE = 104
REAL_CORES = 136
GGUS = 198
HAMMERCLOUD =  135
SAM = 126
WAITING_ROOM_HEADER = '''|#|Site Name|New|Total Weeks Not ready |SAM Availability|Hammercloud|Links|Disk Pledge|Real Cores|GGUS tickets|'''
MORGUE_HEADER = '''|#|Site Name|Total Weeks Not ready|SAM Availability|Hammercloud|Links|Disk Pledge|Real Cores|GGUS tickets|'''
OUTPUT_FILE_NAME = os.path.join(sys.argv[1],"mondayTables.txt")
todayAtMidnight = (datetime.now(pytz.timezone("UTC")) \
            .replace(hour=0, minute=0, second=1, microsecond=0) \
            .astimezone(pytz.utc)).strftime("%Y-%m-%d %H:%M:%S")
# Metric status
IN_WAITING_ROOM = "Waiting_Room"
IN_MORGUE = "Morgue"
OUT_WAITING_ROOM = "OK"

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

def getJSONMetricforAllSites(metricNumber, hoursToRead):
    return getJSONMetric(metricNumber, hoursToRead, "", "all")

def binSiteEntries(daysInArray, siteEntries):
    dayBin= {}
    for x in range(1,daysInArray+1):
        dayBin[datetime.utcnow().replace(hour=12, minute=0, second=1, microsecond=0) + timedelta (days= -1*x)] = "NoneYet"
    for day, value in dayBin.iteritems():
        for endDateUnix, entry in siteEntries.iteritems():
            endDate = datetime.utcfromtimestamp(endDateUnix)
            startDate = datetime.utcfromtimestamp(entry.date)
            if day > startDate and day < endDate:
                if entry.color == "green" or entry.value == "out":
                    dayBin[day] = "green"
                elif entry.color == "red" or entry.value == "in":
                    dayBin[day] = "red"
                else :
                    dayBin[day] = entry.value
    
    days=sorted(dayBin.keys())
    for i in range(1, len(days)):
        if dayBin[days[i]] == "NoneYet":
            dayBin[days[i]]=dayBin[days[i-1]]
    
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


# Get current waiting room. (Last 24 hours) 
currentWaitingRoom = getJSONMetricforAllSites(WAITING_ROOM_COLUMN_ID, 169)
# Get current morgue. (Last 24 hours) 
currentMorgue = getJSONMetricforAllSites(MORGUE_COLUMN_ID, 169)

waitingRoomSites = []
morgueSites = []
outList = []

if currentWaitingRoom != None and currentMorgue != None:
    for site in currentWaitingRoom.getSites():
        currentStatus = currentWaitingRoom.getLatestEntry(site)
        if currentStatus.value == IN_WAITING_ROOM :
            waitingRoomSites.append(site)
    
    for site in currentMorgue.getSites():
        currentStatus = currentMorgue.getLatestEntry(site)
        if currentStatus.value == IN_MORGUE :
            morgueSites.append(site)
    for site in currentWaitingRoom.getSites():
        currentStatus = currentWaitingRoom.getLatestEntry(site)
        if currentStatus.value == OUT_WAITING_ROOM :
            siteStats = binSiteEntries(7, currentWaitingRoom.getSiteEntries(site))[0]
            if siteStats != None:
                if siteStats.get("red", 0) > 1:
                    outList.append(site)
    waitingRoomSites = list(set(waitingRoomSites) ^ set(morgueSites))
    morgueSites = list(set(morgueSites))
    
    # Get WaitingRoom since the beggining of time 
    sitesStr = ",".join(waitingRoomSites)
    sitesStr = sitesStr + "," + (",".join(morgueSites))
    sitesWaitingRoomHistory = getJSONMetric(WAITING_ROOM_COLUMN_ID, "custom", sitesStr, "multiple")
    # get good links
    goodT2LinksToT1s = getJSONMetric(GOOD_T2_LINKS_TO_T1s, "132", sitesStr, "multiple")
    goodT2LinksfromT1s = getJSONMetric(GOOD_T2_LINKS_FROM_T1s, "132", sitesStr, "mulitple")
    diskPledge = getJSONMetric(DISK_PLEDGE, "132", sitesStr, "mulitple")
    realCores = getJSONMetric(REAL_CORES, "1200", sitesStr, "mulitple")
    ggus = getJSONMetric(GGUS, "132", sitesStr, "mulitple")
    hammercloud = getJSONMetric(HAMMERCLOUD, "132", sitesStr, "mulitple")
    sam = getJSONMetric(SAM, "132", sitesStr, "mulitple")
    lifeStatus = getJSONMetric(231, "168", sitesStr, "multiple") 
    
    waitingRoomTable = []
    morgueTable = []
    newInWaitingRoom =[]
    # Calculate weeks in waiting room for sites in waiting room. 
    counterWR = 0
    if sitesWaitingRoomHistory != None :
        for site in waitingRoomSites:
            counterWR += 1
            sitehistory = sitesWaitingRoomHistory.getSiteEntries(site) 
            siteDiskPledge = diskPledge.getLatestEntry(site)
            siteDiskPledgeStr = siteDiskPledge.value if siteDiskPledge is not None else ""
            siteRealCores = realCores.getLatestEntry(site)
            siteRealCoresStr = siteRealCores.value if siteRealCores is not None else ""
            siteGgus = ggus.getLatestEntry(site)
            siteGgusStr = str(siteGgus.value) if siteGgus is not None else ""
            siteGgusStr = "None" if siteGgusStr == "0" else siteGgusStr
            siteGgusUrl = siteGgus.url if siteGgus is not None else ""
            siteGoodT2LinksToT1s = goodT2LinksToT1s.getLatestEntry(site)
            siteGoodT2LinksToT1sStr = "Good T2 Links to T1: " + siteGoodT2LinksToT1s.value if siteGoodT2LinksToT1s is not None else ""
            siteGoodT2LinksfromT1s = goodT2LinksfromT1s.getLatestEntry(site)
            siteGoodT2LinksfromT1sStr = "Good T2 Links from T1: " + siteGoodT2LinksfromT1s.value if siteGoodT2LinksfromT1s is not None else ""
            siteGoodLinksStr = siteGoodT2LinksToT1sStr + "<br>" + siteGoodT2LinksfromT1sStr
            siteSam = sam.getLatestEntry(site)
            siteSamStr= str(siteSam.value) if siteSam is not None else ""
            siteSamStr = "None" if siteSamStr == "0" else siteSamStr
            siteSamUrl = siteSam.url if siteSam is not None else ""
            siteHC = hammercloud.getLatestEntry(site)
            siteHCStr= siteHC.value if siteHC is not None else ""
            siteHCStr = "None" if siteHCStr == "0" else siteHCStr
            siteHCUrl = siteHC.url if siteHC is not None else ""
            daysInWaitingroomBin = binSiteEntries(1300, sitehistory)[2]
            dates = daysInWaitingroomBin.keys()
            dates.sort()
            siteDaysinWaitingRoom = 1
            for i in range(len(dates)-2, 0, -1):
                if ("red" in daysInWaitingroomBin.get(dates[i])) or ("in" in daysInWaitingroomBin.get(dates[i])):
                    siteDaysinWaitingRoom += 1
                elif daysInWaitingroomBin.get(dates[i]) != daysInWaitingroomBin.get(dates[i-1]):
                    break 
            daysOut = binSiteEntries(7, sitehistory)[0]
            daysOutStat = daysOut.get("green", 0)
            if daysOutStat > 1:
                newtag = "X"
                newInWaitingRoom.append(site)
            else:
                newtag = "" 
            weeksInWaitingRoom = siteDaysinWaitingRoom /7
            print site
            '''|No|Site Name| New |Total Weeks Not ready | SAM Availability | Hammercloud | Links | Disk Pledge | Real Cores | GGUS tickets | '''
            waitingRoomTable.append("|%s|%s|%s|%s|[[%s][%s]]|[[%s][%s]]|%s|%s|%s|[[%s][%s]]|" % (counterWR,site, newtag, str(weeksInWaitingRoom), siteSamUrl, siteSamStr, siteHCUrl, siteHCStr, siteGoodLinksStr , siteDiskPledgeStr, siteRealCoresStr, siteGgusUrl, siteGgusStr  )+ "\n") 
        counterMorgue = 0
        for site in morgueSites:
            counterMorgue += 1
            sitehistory = sitesWaitingRoomHistory.getSiteEntries(site) 
            siteDiskPledge = diskPledge.getLatestEntry(site)
            siteDiskPledgeStr = siteDiskPledge.value if siteDiskPledge is not None else ""
            siteRealCores = realCores.getLatestEntry(site)
            siteRealCoresStr = siteRealCores.value if siteRealCores is not None else ""
            siteGgus = ggus.getLatestEntry(site)
            siteGgusStr = str(siteGgus.value) if siteGgus is not None else ""
            siteGgusStr = "None" if siteGgusStr == "0" else siteGgusStr
            siteGgusUrl = siteGgus.url if siteGgus is not None else ""
            siteGoodT2LinksToT1s = goodT2LinksToT1s.getLatestEntry(site)
            siteGoodT2LinksToT1sStr = "Good T2 Links to T1: " + siteGoodT2LinksToT1s.value if siteGoodT2LinksToT1s is not None else ""
            siteGoodT2LinksfromT1s = goodT2LinksfromT1s.getLatestEntry(site)
            siteGoodT2LinksfromT1sStr = "Good T2 Links from T1: " + siteGoodT2LinksfromT1s.value if siteGoodT2LinksfromT1s is not None else ""
            siteGoodLinksStr = siteGoodT2LinksToT1sStr + "<br>" + siteGoodT2LinksfromT1sStr
            siteSam = sam.getLatestEntry(site)
            siteSamStr= str(siteSam.value) if siteSam is not None else ""
            siteSamStr = "None" if siteSamStr == "0" else siteSamStr
            siteSamUrl = siteSam.url if siteSam is not None else "Unknown"
            siteHC = hammercloud.getLatestEntry(site)
            siteHCStr= str(siteHC.value) if siteHC is not None else "Unknown"
            siteHCStr = "None" if siteHCStr == "0" else siteHCStr
            siteHCUrl = siteHC.url if siteHC is not None else "Unknown"
            daysInWaitingroomBin = binSiteEntries(1300, sitehistory)[2]
            dates = daysInWaitingroomBin.keys()
            dates.sort()
            siteDaysinWaitingRoom = 1
            for i in range(len(dates)-2, 0, -1):
                if ("red" in daysInWaitingroomBin.get(dates[i])) or ("w" in daysInWaitingroomBin.get(dates[i])):
                    siteDaysinWaitingRoom += 1
                elif (not ("red" in daysInWaitingroomBin.get(dates[i]))) and (not ("w" in daysInWaitingroomBin.get(dates[i]))):
                    break 
            weeksInWaitingRoom = siteDaysinWaitingRoom /7
            '''|No|Site Name| Total Weeks Not ready | SAM Availability | Hammercloud | Links | Disk Pledge | Real Cores | GGUS tickets | '''
            print site + " " +siteSamStr 
            morgueTable.append("|%s|%s|%s|[[%s][%s]]|[[%s][%s]]|%s|%s|%s|[[%s][%s]]|" % (counterMorgue, site, str(weeksInWaitingRoom), siteSamUrl, siteSamStr, siteHCUrl, siteHCStr, siteGoodLinksStr , siteDiskPledgeStr, siteRealCoresStr, siteGgusUrl, siteGgusStr) + "\n")
        outputFile = open(OUTPUT_FILE_NAME, 'w')
        outputFile.write("---++++ News & Issues\n")
        outputFile.write("* *Into the Waiting Room:* " + ",".join(newInWaitingRoom) + "\n\n")
        outputFile.write("* *Out the Waiting Room:* " + ",".join(outList) + "\n\n") 
        outputFile.write("Sites in Waiting Room: " + str(counterWR) + "\n" )
        outputFile.write("Sites in Morgue: " + str(counterMorgue) + "\n" )
        outputFile.write("\n\n")
        outputFile.write("---++++ Waiting Room\n")
        outputFile.write(WAITING_ROOM_HEADER+'\n')
        outputFile.writelines(waitingRoomTable)   
        outputFile.write("---++++ Morgue\n")
        outputFile.write(MORGUE_HEADER+'\n')
        outputFile.writelines(morgueTable)
        outputFile.write("\n Output generated at: " + todayAtMidnight)
        outputFile.close()
    else:
        print "Could not get history data" 
else :
    print "Could not get current data"

