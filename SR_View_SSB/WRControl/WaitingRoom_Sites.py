import os, sys, errno
import simplejson
from datetime import datetime
from datetime import timedelta
import time
from pprint import pprint
import string
import urllib, httplib, re, urllib2
import pickle 
import simplejson as json

#extract nonwaitingroommsites from ActiveSites SSB metric 39 output
url2 = "http://dashb-ssb.cern.ch/dashboard/request.py/getplotdata?columnid=39&time=24&dateFrom=&dateTo=&site=T2_AT_Vienna&sites=all&clouds=undefined&batch=1"
url2t = "https://cmsdoc.cern.ch/cms/LCG/SiteComm/T2WaitingList/WasCommissionedT2ForSiteMonitor.txt"
urlSRRanking = "http://cms-site-readiness.web.cern.ch/cms-site-readiness/SiteReadiness/toSSB/SiteReadinessRanking_SSBfeed_last15days.txt"

# Read SSB metric 45 to get complete list of sites considered in SR Status
def extractJson():
  url = "http://dashb-ssb.cern.ch/dashboard/request.py/getplotdata?columnid=45&time=24&dateFrom=&dateTo=&site=T1_CH_CERN&sites=all&clouds=undefined&batch=1"
  print "Getting the url %s" % url
  request = urllib2.Request(url, headers = {"Accept":"application/json"})
  response = urllib2.urlopen(request)
  data = response.read()
  rows = simplejson.loads(data)
  return rows

# function needed to fetch a list of all sites from metric
def fetch_all_sites(jsn):
  site_T2 = []
  for row in jsn['csvdata']:
    if row['VOName'][0:2] == 'T2':
      if not row['VOName'] in site_T2:
        site_T2.append(row['VOName'])
  return site_T2

def getNonWaitingRoomSites(url):
  print "Getting the url %s" % url
  request = urllib2.Request(url, headers = {"Accept":"application/json"})
  response = urllib2.urlopen(request)
  data = response.read()
  rows = simplejson.loads(data)
  sites = []
  for row in rows['csvdata']:
    sites.append(row['VOName'])
  return sites
  
def getNonWaitingRoomSitesText(url): #function to read info from txt file
  print "Getting the txt %s" % url
  sites = []
  for line in urllib2.urlopen(url).readlines():
    row = line.split("\t")
    if len(row) == 5 :
        siteName = row[1]
        sites.append(siteName) 
  return sites

# dashboard entry structure
class Entry:
  def __init__(self, row = (None, None, None, None, None)):
    self.Date  = row[0]
    self.Name  = row[1]
    self.Value = row[2]
    self.Color = row[3]
    self.URL   = row[4]

# returns parsed metric entries in the class structure
def ParseMetric(url):
  # get the metric content
  urlObj  = urllib2.urlopen(url)
  data    = urlObj.read()
  # parse the metric
  parsed  = re.findall(r'(.*?)\t(.*?)\t(.*?)\t(.*?)\t(.*?)\n', data, re.M)
  entries = []
  for i in parsed:
    entry = Entry(i)
    entries.append(entry) 
  entries.sort(key=lambda x: x.Name)
  return entries

SRRanking = ParseMetric(urlSRRanking)
def IsMarkedRed(siteName):
  for site in SRRanking:
    # find the site and if it is marked as red in SRRanking, return True
    if site.Name == siteName and site.Color == 'red': return True
  return False

def main_function(outputfile_txt):
  # non-waitingroom sites
  print 'Fetchting all the sites that are not in waitingroom'
  nonWaitingRoom_Sites = getNonWaitingRoomSitesText(url2t)
  print 'number of non waiting room  sites: ', len(nonWaitingRoom_Sites)
  print nonWaitingRoom_Sites
  print '------------------------------------------'
  # all sites
  print 'starting to fetch all sites from metric'
  site_T2= fetch_all_sites(extractJson())
  print '--------------------------------------------------------'
  print 'Sites in waiting room:'
  waitingRoom_sites = [ site for site in site_T2 if not site in nonWaitingRoom_Sites]
  print waitingRoom_sites

  # write to file for SSB
  f1=open('./'+outputfile_txt, 'w+')
  now_write=(datetime.utcnow()).strftime("%Y-%m-%d %H:%M:%S")


  # write file that can be loaded in SSB
  f1.write('# This txt goes into SSB and marks sites red when the site is in the waiting room:\n')
  f1.write('# Readme:\n# https://raw.githubusercontent.com/CMSCompOps/MonitoringScripts/master/SR_View_SSB/WRControl/Readme.txt\n')
  print "Local current time :", now_write
  link = "https://dashb-ssb.cern.ch/dashboard/request.py/sitereadinessrank?columnid=45#time=2184&start_date=&end_date=&sites=T0/1/2"
  for k in waitingRoom_sites:
    print k, 'in', 'red'
    f1.write(now_write+'\t')        # timestamp
    f1.write(''.join(k))            # sitename
    f1.write('\tin')                # value
    f1.write('\tred\t')             # color
    f1.write(''.join(link))         # link
    f1.write('\n')
  for k in site_T2:
    # skip the site if it is in the waiting room
    if k in waitingRoom_sites: continue
    # if the site marked as red in SRRanking metric
    if IsMarkedRed(k):
      print k, 'w', 'yellow'
      f1.write(now_write+'\t')    # timestamp
      f1.write(''.join(k))        # sitename
      f1.write('\tw')             # value
      f1.write('\tyellow\t')      # color
      f1.write(''.join(link))     # link
      f1.write('\n')
      continue
    print k, 'out', 'green'
    f1.write(now_write+'\t')    # timestamp
    f1.write(''.join(k))        # sitename
    f1.write('\tout')           # value
    f1.write('\tgreen\t')       # color
    f1.write(''.join(link))     # link
    f1.write('\n')

if __name__ == '__main__':
  outputfile_txt=sys.argv[1]
  main_function(outputfile_txt)
