#!/usr/bin/python
import urllib2
import simplejson
import time
from datetime import datetime
from datetime import timedelta
from datetime import date

urlDrain  = "http://dashb-ssb.cern.ch/dashboard/request.py/getplotdata?columnid=158&time=24&dateFrom=&dateTo=&site=T0_CH_CERN&sites=all&clouds=undefined&batch=1"
urlManual = "http://dashb-ssb.cern.ch/dashboard/request.py/getplotdata?columnid=139&time=24&dateFrom=&dateTo=&site=T0_CH_CERN&sites=all&clouds=undefined&batch=1"
urlWr     = "http://dashb-ssb.cern.ch/dashboard/request.py/getplotdata?columnid=153&time=24&dateFrom=&dateTo=&site=T2_AT_Vienna&sites=all&clouds=undefined&batch=1"
urlWrTxt  = "https://cmst1.web.cern.ch/CMST1/WFMon/WaitingRoom_Sites.txt"
urlSR     = "http://dashb-ssb.cern.ch/dashboard/request.py/getplotdata?columnid=45&time=168&dateFrom=&dateTo=&site=T1_DE_KIT&sites=all&clouds=undefined&batch=1"
urlSD     = "http://dashb-ssb.cern.ch/dashboard/request.py/getplotdata?columnid=121&time=24&dateFrom=&dateTo=&site=T0_CH_CERN&sites=all&clouds=undefined&batch=1"
urlSDTxt  = "https://cms-site-readiness.web.cern.ch/cms-site-readiness/SiteReadinessAnalysis/toSSB/UsableSites_SSBfeed.txt"
urlMorgue = "http://dashb-ssb.cern.ch/dashboard/request.py/getplotdata?columnid=199&time=24&dateFrom=&dateTo=&site=T2_AT_Vienna&sites=all&clouds=undefined&batch=1"

daysBrown    = {}  # keeps down days count
daysGreen    = {}  # keeps ready days count
daysWhite    = {}  # keeps noinfo days count
tmpDrainList = []  # keeps Temporary Drain List after condition process
tmpDownList  = []  # keeps Temporary Down List after condition process
newDrainList = {}  # keeps new Drain List


#______________________function returns json code from url________________________

def extractJson(url): 
  print "Getting the url %s" % url
  request = urllib2.Request(url, headers = {"Accept":"application/json"})
  response = urllib2.urlopen(request)
  data = response.read()
  rows = simplejson.loads(data)
  return rows

#_________________function returns siteList by using your parameter________________

def getList(url, status): # status could have in, down, drain, SD, *
    rows = extractJson(url)
    todaydate = date.today()
    
    value = datetime.fromtimestamp(time.time() + 1 * 24 * 60 * 60)
    timeStamp = value.strftime('%Y-%m-%d').split("-")
    startdate = date(int(timeStamp[0]), int(timeStamp[1]), int(timeStamp[2]))   # +1 day from today

    site_list = []
    for row in rows['csvdata']:
        if status == "SD":
            if row['VOName'][0:2] != 'T3':
                starttime = datetime(*(time.strptime( row['Time'] ,'%Y-%m-%dT%H:%M:%S')[0:6]))  # starttime from JSON
                endtime = datetime(*(time.strptime(row['EndTime'] ,'%Y-%m-%dT%H:%M:%S')[0:6]))  # endtime from JSON
                if (starttime.date() <= startdate) and (endtime.date() >= todaydate) and (endtime.date() > starttime.date()):
                    if (row['COLORNAME'] == "saddlebrown") or (row['COLORNAME'] == "grey"):
                        if not row['VOName'] in site_list: site_list.append(row["VOName"])
                    else:
                        if row['VOName'] in site_list: site_list.remove(row["VOName"])
        elif status == "*":
            if not row['VOName'] in site_list: site_list.append(row["VOName"])
        else:
            if row['Status'] == status:
                if not row['VOName'] in site_list: site_list.append(row["VOName"])
    return site_list

#___________________function to read info from txt file___________________________________________
def getTxtList(url, status):
  print "Getting the url %s" % url
  sites_in_txt = []
  for line in urllib2.urlopen(url).readlines():
    row = line.split("\t")
    if len(row) == 5 :
        siteName = row[1]
        value    = row[2]
        
        if value == status:
            if not siteName in sites_in_txt: sites_in_txt.append(siteName) 
  return sites_in_txt

#_________________________the function calculates day counts in last week_____________________________

  # In this algorithm, startdate and enddate are search borders. Script finds the records which are between startdate and enddate.
  
  #       <-----------------------7 days----------------------->
  #       |----------------------------------------------------|
  #   startdate                                          enddate(today)
  
  # Because records have date and time information, these informations are called starttime and endtime

def getDayCounts(url, status):
  #________________________________definition of time and variable___________________________________

  enddate  = date.today()                                                               # gives today date. 
  value = datetime.fromtimestamp(time.time() - 7 * 24 * 60 * 60)                        # to get 7 days ago from today
  timeStamp = value.strftime('%Y-%m-%d').split("-")
  startdate = date(int(timeStamp[0]), int(timeStamp[1]), int(timeStamp[2]))      		# 7 days ago from today
  jsn=extractJson(url)                                                                  # results from dashboard extracts into JSON file
  allSites = getList(url, "*")                                                          # gets allsite list from getList function
  days_per_site={} 																		# keeps all siteNames and its day informations

  #_______________________________________________day calculation process_______________________________________________________
  
  for site in allSites:
    daysCount = 0 # keeps totalday count
    tmp_days  = 0 # keeps temp day count
    temp 	  = 0 # keeps endtime
    for row in jsn['csvdata']:
      if row['VOName'] != site: continue
      elif row['COLORNAME'] == status: 
      	starttime = datetime(*(time.strptime( row['Time'] ,'%Y-%m-%dT%H:%M:%S')[0:6]))       # starttime of record which comes JSON
      	endtime   = datetime(*(time.strptime( row['EndTime'] ,'%Y-%m-%dT%H:%M:%S')[0:6]))    # endtime of record which comes JSON
      	if startdate > starttime.date():
      		if startdate > endtime.date(): continue
      		elif startdate < endtime.date():
      			if startdate > starttime.date():
      				tmp_days = endtime.date() - startdate
      			elif startdate <= starttime.date():
      				tmp_days = endtime.date() - starttime.date()
      			temp = tmp_days.days
			if endtime.date() > enddate: temp = temp - 1                                     # I can use "tmp_days -= 1" but When I used this I encountered "readonly attribute error"
			daysCount+= temp
      	elif startdate <= starttime.date():
      		tmp_days = endtime.date() - starttime.date()
		temp = tmp_days.days
		if endtime.date() > enddate: temp = temp - 1                                         # I can use "tmp_days -= 1" but When I used this I encountered "readonly attribute error"
      	daysCount+= temp
      	days_per_site[site] = daysCount
    if daysCount == 0:
        days_per_site[site] = 0

  return days_per_site
#___________________________the function calculates Site Readiness Rate per site ___________________

# SiteReadiness = (Ready(G) + Warning(Y)) / (totalDays - scheduleDowntime(B) - NoInfo(W))
# but because this metric is so sensitive, Warning days can be ignored. We need perfect readiness

def CalSiteReadRate(allSites, daysGreen, daysBrown, daysWhite, daysYellow):
    average_per_site = {}                                                           # keeps all siteNames and their site readiness rate
    for site in allSites:
        readiness = 0.0
        if site in daysGreen:  
            green  = daysGreen[site]
            brown  = daysBrown[site]
            white  = daysWhite[site]
            yellow = daysYellow[site]
            den = brown + white
            if den != 7 :                                                         # if den = 7 => script encounters "ZeroDivisionError" 
                readiness = (green + yellow) / float(7 - den) 
        average_per_site[site] = readiness
    return average_per_site

#__________________________________________________________________________________________________

def writeFile(siteList):
    saveTime = time.strftime('%Y-%m-%d %H:%M:%S')
    filename = "drain"
    url = "https://cmst1.web.cern.ch/CMST1/SST/drain_log.txt"
    f = open(filename + ".txt", "w")
    for rows in siteList:
        color = "green"
        if siteList[rows] == "drain" : color = "yellow"
        if siteList[rows] == "down" : color  = "red"
        f.write(saveTime + "\t" + rows + "\t" + siteList[rows] + "\t" + color + "\t" + url + "\n")
    print "\n*** List has been created successfully ***"


#________________________________________________________________________


def getAllInformation():
    #________________________________getting oldDrainList, manualDrain, oldDownList, wr list, morgue list, sr=SD List, full site list__________________________

    fullSiteList  = getList(urlManual, "*")         # gets full site list from metric 139
    wrList        = getTxtList(urlWrTxt, "in")      # gets current waiting room list from metric 153 txt file
    morgueList    = getList(urlMorgue, "in")        # gets current morgue list from metric 199
    oldDrainList  = getList(urlDrain, "drain")      # gets old drain list from metric 158
    manualDrain   = getList(urlManual, "drain")     # gets manual drain list from metric 139
    oldDownList   = getList(urlDrain, "down")       # gets old down list from metric 158
    manualDown    = getList(urlManual, "down")      # gets manual down list from metric 139
    tier0List     = getList(urlDrain, "tier0")      # gets tier0 list from metric 158
    manualTier0   = getList(urlManual, "tier0")     # gets manual tier0 list from metric 139
    srStatusList  = getList(urlSD, "SD")            # gets downtime status from metric 121
    
    print 'starting to fetch all sites from DashBoard'
    daysBrown  = getDayCounts(urlSR, "brown")
    daysWhite  = getDayCounts(urlSR, "white")
    daysGreen  = getDayCounts(urlSR, "green")
    daysYellow = getDayCounts(urlSR, "yellow")
    
    #_______________________________ calculates site readiness ranking for last week per site. __________________________
    
    average_per_site = CalSiteReadRate(fullSiteList, daysGreen, daysBrown, daysWhite, daysYellow) 

    return (fullSiteList, wrList, morgueList, oldDrainList, manualDrain, tmpDrainList, oldDownList, manualDown, tmpDownList, tier0List, manualTier0, srStatusList, average_per_site)


if __name__ == '__main__':
    fullSiteList, wrList, morgueList, oldDrainList, manualDrain, tmpDrainList, oldDownList, manualDown, tmpDownList, tier0List, manualTier0, srStatusList, average_per_site = getAllInformation()
    
    print "\n*** Previous (drain) & SR last 7 days (if SR < 0.8 = drain) ***"
    for site in oldDrainList:                   # firstly add old drain list
        if site[0:2] != 'T3':                   # do not consider T3s because they don't have SR ranking
            print "%s\t\t\t%s" % (site, average_per_site[site])
            if average_per_site[site] < 0.8 :   # if last week siteRanking < 80% keep in drainList
                if not site in tmpDrainList: tmpDrainList.append(site)
        else:
            print site

    print "\n*** Manual (drain) ***"
    for site in manualDrain:                    # add site into drainNewList if in Prod status Manual metric
        print site
        if not site in tmpDrainList: tmpDrainList.append(site)
    
    print "\n*** WR (drain) ***"
    for site in wrList:                         # add site into drainNewList if wr = in for site
        print site
        if not site in tmpDrainList: tmpDrainList.append(site)
    
    print "\n*** SD & UD Downtime (drain) ***"
    for site in srStatusList:                   # add site into drainNewList if srstatus = sd for site
        print site
        if not site in tmpDrainList: tmpDrainList.append(site)

    print "\n*** Manual (down) ***"
    for site in manualDown:                     # add site into downNewList if in Prod status Manual metric
        print site
        if not site in tmpDownList: tmpDownList.append(site)
        
    print "\n*** MORGUE (down) ***"
    for site in morgueList:                     # add site into downNewList if morgue = in for site
        print site
        if not site in tmpDownList: tmpDownList.append(site)

    print "\n*** tier0 (manual) ***"
    for site in manualTier0:                    # add site into tier0List if in Prod status Manual metric
        print site
        if not site in tier0List: tier0List.append(site)

    #________________________________ create new list ______________________________________
    for site in fullSiteList:
        if not site in newDrainList:
            newDrainList[site] = "on"
            
            if site in tmpDrainList:
                newDrainList[site] = "drain"
            
            if site in tier0List:
                newDrainList[site] = "tier0"
                
            if site in tmpDownList:
                newDrainList[site] = "down"

    writeFile(newDrainList) # write process
