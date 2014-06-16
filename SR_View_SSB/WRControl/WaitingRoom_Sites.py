import os, sys, errno
import urllib2
import simplejson
from datetime import datetime
from datetime import timedelta
import time
from pprint import pprint
import string
import urllib, httplib, re, urllib2
import pickle 
import simplejson as json
#extract nonwaitingroommsites from ActiveSites script output
url2 = "http://dashb-ssb.cern.ch/dashboard/request.py/getplotdata?columnid=39&time=24&dateFrom=&dateTo=&site=T2_AT_Vienna&sites=all&clouds=undefined&batch=1"

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


def main_function(outputfile_txt):
  # non-waitingroom sites
  print 'Fetchting all the sites that are not in waitingroom'
  nonWaitingRoom_Sites = getNonWaitingRoomSites(url2)
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
  #write to file for SSB
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
    if not k in waitingRoom_sites:
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