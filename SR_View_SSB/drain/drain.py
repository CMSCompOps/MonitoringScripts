#!/usr/bin/python
import urllib2
import simplejson
import time
from datetime import datetime
from datetime import timedelta
from datetime import date
#_______________________________________________________________________

def extractJson(url):
  print "Getting the url %s" % url
  request = urllib2.Request(url, headers = {"Accept":"application/json"})
  response = urllib2.urlopen(request)
  data = response.read()
  rows = simplejson.loads(data)
  return rows

#_______________________________________________________________________

def getList(url, status):
    rows = extractJson(url)
    site_list = []
    for row in rows['csvdata']:
        if  status != "*":
            if row["Status"] == status:
                if not row["VOName"] in site_list: site_list.append(row["VOName"])
        else:
            if row["VOName"][0:2] != 'T3':
                if not row["VOName"] in site_list: site_list.append(row["VOName"])
    return site_list

#_______________________________________________________________________

def calculateDays(url, status):
  enddate  = date.today()
  value = datetime.fromtimestamp(time.time() - 7 * 24 * 60 * 60)
  timeStamp = value.strftime('%Y-%m-%d').split("-")
  startdate = date(int(timeStamp[0]), int(timeStamp[1]), int(timeStamp[2]))
  print "End Date : ", enddate
  print "Start Date : ", startdate
  jsn=extractJson(url) # results from dashboard extracts into JSON file
  allSites = getList(url, "*")
  # sum @ days 
  days_per_site={}
  for site in allSites: # Read all sites from allsites variable
    wrDays = 0         # keeps number of wrDays per Site
    days  = 0             # keeps temporary wrDays
    temp = 0  
    for k in jsn['csvdata']: # JSON file reads.
      if k['VOName'] != site: continue
#************************************************Modifications**************************************
      elif k['COLORNAME'] == status: # if the site is red then calculate wrDays
      	starttime = datetime(*(time.strptime( k['Time'] ,'%Y-%m-%dT%H:%M:%S')[0:6])) # starttime from JSON file
      	endtime   = datetime(*(time.strptime( k['EndTime'] ,'%Y-%m-%dT%H:%M:%S')[0:6])) # endtime from JSON file
      	if startdate > starttime.date():
      		if startdate > endtime.date(): continue
      		elif startdate < endtime.date():
      			if startdate > starttime.date():
      				days = endtime.date() - startdate
      			elif startdate <= starttime.date():
      				days = endtime.date() - starttime.date()
      			temp = days.days
			if endtime.date() > enddate: temp = temp - 1
			wrDays+= temp
      	elif startdate <= starttime.date():
      		days = endtime.date() - starttime.date()
		temp = days.days
		if endtime.date() > enddate: temp = temp - 1
      	wrDays+= temp
      	days_per_site[site] = wrDays
    if wrDays == 0:
        days_per_site[site] = 0
  return days_per_site
#_______________________________________________________________________

def calculateSR(allSites, daysGreen, daysYellow, daysBrown, daysWhite):
    average_per_site = {}
    readiness = 0.0
    for site in allSites:
        if (site in daysGreen) and (site in daysYellow) and (site in daysBrown) and (site in daysWhite) :  
            green  = daysGreen[site]
            yellow = daysYellow[site]
            brown = daysBrown[site]
            white = daysWhite[site]
            readiness = 0.0
            if brown != 7 :
                readiness = (green + yellow) / float(7 - brown - white)
            average_per_site[site] = readiness
    return average_per_site

#_______________________________________________________________________

def writeFile(siteList):
    saveTime = time.strftime('%Y-%m-%d %H:%M:%S')
    filename = "drain"
    path = ""
    #path = "/afs/cern.ch/user/c/cmst1/scratch0/MonitoringScripts/SR_View_SSB/drain/"
    url = "https://cmst1.web.cern.ch/CMST1/SST/drain.txt"
    f = open(path + filename + ".txt", "w")
    for rows in siteList:
        color = "green"
        if siteList[rows] == "drain" : color = "yellow"
        if siteList[rows] == "down" : color = "brown"
        f.write(saveTime + "\t" + rows + "\t" + siteList[rows] + "\t" + color + "\t" + url + "\n")
    print "List has been created successfully"


#________________________________________________________________________


# run program for last month, last 2 months and last 3 months
if __name__ == '__main__':
    urlDrain     = "http://dashb-ssb.cern.ch/dashboard/request.py/getplotdata?columnid=158&time=24&dateFrom=&dateTo=&site=T0_CH_CERN&sites=all&clouds=undefined&batch=1"
    urlWr         = "http://dashb-ssb.cern.ch/dashboard/request.py/getplotdata?columnid=153&time=24&dateFrom=&dateTo=&site=T2_AT_Vienna&sites=all&clouds=undefined&batch=1"
    urlSR         = "http://dashb-ssb.cern.ch/dashboard/request.py/getplotdata?columnid=45&time=168&dateFrom=&dateTo=&site=T1_DE_KIT&sites=all&clouds=undefined&batch=1"
    urlSD         = "http://dashb-ssb.cern.ch/dashboard/request.py/getplotdata?columnid=45&time=24&dateFrom=&dateTo=&site=T1_DE_KIT&sites=all&clouds=undefined&batch=1"
    urlMorgue  = "http://dashb-ssb.cern.ch/dashboard/request.py/getplotdata?columnid=199&time=24&dateFrom=&dateTo=&site=T2_AT_Vienna&sites=all&clouds=undefined&batch=1"

    daysBrown = {}
    daysYellow = {}
    daysGreen = {}
    daysWhite  = {}
    newDrainList = []
    newDownList = []
    newList = {}
    
    #________________________________getting oldDrainList, oldDownList, wr list, morgue list, sr=SD List, full site list__________________________
    
    fullSiteList       = getList(urlDrain, "*")
    wrList              = getList(urlWr, "in")
    morgueList      = getList(urlMorgue, "in")
    oldDownList    = getList(urlDrain, "down")
    oldDrainList     = getList(urlDrain, "drain")
    srStatusList     = getList(urlSD, "SD")
    
    print 'starting to fetch all sites from siteDB'
    daysBrown     = calculateDays(urlSR, "brown")
    daysYellow = calculateDays(urlSR, "yellow")
    daysWhite  = calculateDays(urlSR, "white")
    daysGreen = calculateDays(urlSR, "green")
    
    #_______________________________calculates site readiness ranking for last week per site._____________________________________________
    
    average_per_site = calculateSR(fullSiteList, daysGreen, daysYellow, daysBrown, daysWhite) 
    
    #_____________________________find drain and down sites_______________________________
    
    
    #________________________________drain process_____________________________________
    
    for site in oldDrainList:
        if not average_per_site[site] >= 0.8 : # if last week siteRanking > 80% remove from drainList
            if not site in newDrainList: newDrainList.append(site)

    for site in fullSiteList:
        if site in wrList: # add site into drainNewList if wr = in for site
            if not site in newDrainList: newDrainList.append(site)
        if site in srStatusList: # add site into drainNewList if srstatus = sd for site
            if not site in newDrainList: newDrainList.append(site)

    #________________________________________________________________________________

    #________________________________down process_____________________________________

    for site in oldDownList: 
        if not site in newDownList: newDownList.append(site)

    for site in fullSiteList:
        if site in morgueList: # add site into downNewList if morgue = in for site
            if not site in newDownList: newDownList.append(site)

    #________________________________________________________________________________
            
    #________________________________crate new list______________________________________
    for site in fullSiteList:
        if not site in newList:
            if site in newDrainList:
                newList[site] = "drain"
            else:
                newList[site] = "on"
            
            if site in newDownList:
                newList[site] = "down"
                
    writeFile(newList) #write process
    
    
    
    
    
    