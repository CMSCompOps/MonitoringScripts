import urllib2, time, re, sys
from datetime import *
try: import json
except ImportError: import simplejson as json
try: import xml.etree.ElementTree as ET
except ImportError: from elementtree import ElementTree as ET

urlSRRanking   = "http://cms-site-readiness.web.cern.ch/cms-site-readiness/SiteReadiness/toSSB/SiteReadinessRanking_SSBfeed_last15days.txt"
urlWaitingRoom = "https://cmsdoc.cern.ch/cms/LCG/SiteComm/T2WaitingList/WasCommissionedT2ForSiteMonitor.txt"
urlMetric      = "https://dashb-ssb.cern.ch/dashboard/request.py/sitereadinessrank?columnid=45#time=2184&start_date=&end_date=&sites=T0/1/2"

def write(data, fileName):
    fh = open(fileName, 'w')
    fh.write(data)
    fh.close()

def urlRead(url):
    """read content from the web"""
    urlObj = urllib2.urlopen(url)
    data   = urlObj.read()
    return data

def getT2Sites():
    """return all T2 site names"""
    xml   = urlRead('http://dashb-cms-vo-feed.cern.ch/dashboard/request.py/cmssitemapbdii')
    xml   = ET.fromstring(xml)
    sites = xml.findall('atp_site')
    ret   = []
    for site in sites:
        groups   = site.findall('group')
        t2Flag = False
        tName  = None
        for group in groups:
            # set the t2 flag if it is tier 2
            if group.attrib['name'] == 'Tier-2': t2Flag = True
            # find the tier name
            if group.attrib['type'] == 'CMS_Site': tName = group.attrib['name']
        # if it is tier-2 side, push it the ret list
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

def parseMetric(url):
    """return parsed metric entries in the class structure"""
    # get the metric content
    urlObj  = urllib2.urlopen(url)
    data    = urlObj.read()
    # parse the metric
    parsed  = re.findall(r'(.*?)\t(.*?)\t(.*?)\t(.*?)\t(.*?)\n', data, re.M)
    entries = []
    for i in parsed:
        entry = dashboardEntry(i)
        entries.append(entry) 
    entries.sort(key=lambda x: x.name)
    return entries

srRanking = parseMetric(urlSRRanking)
def isRedInSRRanking(siteName):
    """return true if the site is marked as red in SRRanking metric"""
    for site in srRanking:
        # find the site and if it is marked as red in SRRanking, return True
        if site.name == siteName and site.color == 'red': return True
    return False

wr        = parseMetric(urlWaitingRoom)
def isInWaitingRoom(siteName):
    """return true if the site is not in the waiting room"""
    for site in wr:
        if site.name == siteName and site.color == 'green': return False
    return True

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

    buffer  = '# This txt goes into SSB and marks sites red when the site is in the waiting room:\n'
    buffer  = buffer + '# Readme:\n# https://raw.githubusercontent.com/CMSCompOps/MonitoringScripts/master/SR_View_SSB/WRControl/Readme.txt\n'
    buffer  = buffer + '\n'.join(str(i) for i in entries)
    if fileName: write(buffer, fileName)
    else: print buffer

if __name__ == '__main__':
   if len(sys.argv) > 1: main(sys.argv[1])
   else: main()
