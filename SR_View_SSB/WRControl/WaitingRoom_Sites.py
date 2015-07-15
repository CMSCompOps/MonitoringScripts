import urllib2, time, re, sys, os, errno
from datetime import *
try: import json as simplejson
except ImportError: import simplejson as json
try: import xml.etree.ElementTree as ET
except ImportError: from elementtree import ElementTree as ET

WRThreshold = 0.8
MorgueThreshold = 1.0
urlSRStatus = "http://dashb-ssb.cern.ch/dashboard/request.py/getsitereadinessrankdata?columnid=45&time=%s&sites=T2"
urlSRRanking = "http://cms-site-readiness.web.cern.ch/cms-site-readiness/SiteReadiness/toSSB/SiteReadinessRanking_SSBfeed_last15days.txt"
urlManualWR = "http://dashb-ssb.cern.ch/dashboard/request.py/getplotdata?columnid=220&time=24&dateFrom=&dateTo=&site=T2_AT_Vienna&sites=all&clouds=undefined&batch=1"
urlMorgue = "http://dashb-ssb.cern.ch/dashboard/request.py/getsitereadinessrankdata?columnid=199&time=%s&sites=all"
urlMetric = "https://cmst1.web.cern.ch/CMST1/SST/wr_log.txt"

# function to read data from txt url
def urlRead(url):
    """read content from the web"""
    urlObj = urllib2.urlopen(url)
    data   = urlObj.read()
    return data

# function to read json code from url
def extractJson(url, headers=None):
    request = urllib2.Request(url, headers = headers)
    response = urllib2.urlopen(request)
    data = response.read()
    rows = simplejson.loads(data)
    response.close()
    return rows

# function to read precentages from ssb ranking plots data
def extractSitesUnderPercentage(dataRows, percentageThreshold):
    sites = []
    for row in dataRows['data']:
        siteName = row[0].split(' ')[0]
        sitePercentage = float(row[1][0][1])
        if sitePercentage < percentageThreshold:
            sites.append(siteName)
    return sites

# function returns siteList that meet specified status
def getList(url, status): # status depends on the metric used
    rows = extractJson(url, headers={"Accept":"application/json"})
    site_list = []
    for row in rows['csvdata']:
        if row['Status'] == status:
            if not row['VOName'] in site_list: site_list.append(row["VOName"])
    return site_list

def write(data, fileName):
    fh = open(fileName, 'w')
    fh.write(data)
    fh.close()
    print "\n*** List has been created successfully ***"

def getT2Sites():
    """return all T2 site names"""
    xml   = urlRead('http://dashb-cms-vo-feed.cern.ch/dashboard/request.py/cmssitemapbdii')
    xml   = ET.fromstring(xml)
    sites = xml.findall('atp_site')
    ret   = []
    for site in sites:
        groups = site.findall('group')
        t2Flag = False
        tName  = None
        for group in groups:
            # set the t2 flag if it is tier 2
            if group.attrib['name'] == 'Tier-2': t2Flag = True
            # find the tier name
            if group.attrib['type'] == 'CMS_Site': tName = group.attrib['name']
        # if it is tier-2 site, push it the ret list
        if t2Flag: ret.append(tName)
    ret.sort()
    return ret

# dashboard entry structure
class dashboardEntry:
    def __init__(self, row = (None, None, None, None, None)):
        self.date  = row[0]
        self.name  = row[1]
        self.value = row[2]
        self.color = row[3]
        self.url   = row[4]

    def __str__(self):
        return "%s\t%s\t%s\t%s\t%s" % (self.date, self.name, self.value, self.color, self.url)

def parseMetric(data):
    """return parsed metric entries in the class structure"""
    # remove python style comments
    data    = re.sub(re.compile(r'#.*$', re.MULTILINE), "", data)
    # parse the metric
    parsed  = re.findall(r'(.*?)\t(.*?)\t(.*?)\t(.*?)\t(.*?)\n', data, re.M)
    entries = []
    for i in parsed:
        entry = dashboardEntry(i)
        entries.append(entry) 
    entries.sort(key=lambda x: x.name)
    return entries

# WR list
print "WAITING ROOM CONTROL LIST\n"
print "--------------------------\n"

    # 1. Criteria (IN if SR<80% 1week & 3months)
oneWeekDataRows = extractJson(urlSRStatus % '168', headers={"Accept":"application/json"})
threeMonthsDataRows = extractJson(urlSRStatus % '2184', headers={"Accept":"application/json"})
oneWeekBadSites = extractSitesUnderPercentage(oneWeekDataRows, WRThreshold)
threeMonthsBadSites = extractSitesUnderPercentage(threeMonthsDataRows, WRThreshold)
print "\n*** Criteria (IN if SR<80% 1week & 3months) ***"
WRdata = [val for val in oneWeekBadSites if val in threeMonthsBadSites]
for site in WRdata:
    print site

    # 2. Recently in Morgue (IN if >0 days in last 2weeks)
twoWeeksMorgueDataRows = extractJson(urlMorgue % '336', headers={"Accept":"application/json"})
twoWeeksMorgueSites = extractSitesUnderPercentage(twoWeeksMorgueDataRows, MorgueThreshold)
print "\n*** Recently in Morgue (IN if >0 days in last 2weeks) ***"
for site in twoWeeksMorgueSites:
    print site
    if not site in WRdata:
        WRdata.append(site)

    # 3. Manual WR
manualWR = getList(urlManualWR, "in")     # gets manual WR list from metric 220
print "\n*** Manual WR list (SSB metric 220) ***"
for site in manualWR:
    print site
    if not site in WRdata:
        WRdata.append(site)

def isInWaitingRoom(siteName):
    """return true if the site is IN the waiting room"""
    for site in WRdata:
        if site == siteName: return True
    return False

dataSRR = urlRead(urlSRRanking)
srRanking = parseMetric(dataSRR)
def isRedInSRRanking(siteName):
    """return true if the site is marked as red in SRRanking metric txt"""
    for site in srRanking:
        if site.name == siteName and site.color == 'red': return True
    return False

def main(fileName = None):
    entries = []
    t2Sites = getT2Sites()
    for i in t2Sites:
        entry = dashboardEntry()
        entry.name  = i
        entry.url   = urlMetric
        entry.date  = (datetime.utcnow()).strftime("%Y-%m-%d %H:%M:%S")
        if isInWaitingRoom(i):
            entry.color = 'red'
            entry.value = 'in'
        elif isRedInSRRanking(i):
            entry.color = 'yellow'
            entry.value = 'w'
        else:
            entry.color = 'green'
            entry.value = 'out'
        entries.append(entry)

    buffer  = '# This txt goes into SSB and marks sites red when the site is IN the Waiting Room:\n'
    buffer  = buffer + '# Readme:\n# https://raw.githubusercontent.com/CMSCompOps/MonitoringScripts/master/SR_View_SSB/WRControl/Readme.txt\n'
    buffer  = buffer + '\n'.join(str(i) for i in entries)
    if fileName: write(buffer, fileName)
    else: print buffer

if __name__ == '__main__':
   if len(sys.argv) > 1: main(sys.argv[1])
   else: main()
