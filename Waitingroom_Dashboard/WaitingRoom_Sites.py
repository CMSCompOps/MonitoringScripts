import os, sys, errno
import urllib2
import simplejson
from datetime import datetime
from datetime import timedelta
import time
from pprint import pprint
import string
import urllib, httplib, re
import pickle 

#extract nonwaitingroommsites
url2 = "https://cmsdoc.cern.ch/cms/LCG/SiteComm/T2WaitingList/WasCommissionedT2ForSiteMonitor.txt"

# function needed to fetch a list of all sites from siteDB
def fetch_all_sites(url,api):
  # examples in:
  # https://github.com/gutsche/old-scripts/blob/master/SiteDB/extract_site_executive_mail_addresses.py
  # https://github.com/dballesteros7/dev-scripts/blob/master/src/reqmgr/input-blocks.py
  # https://twiki.cern.ch/twiki/bin/view/CMSPublic/CompOpsWorkflowOperationsWMAgentScripts#Resubmit
  headers = {"Accept": "application/json"}
  if 'X509_USER_PROXY' in os.environ:
      print 'X509_USER_PROXY found'
      conn = httplib.HTTPSConnection(url, cert_file = os.getenv('X509_USER_PROXY'), key_file = os.getenv('X509_USER_PROXY'))
  elif 'X509_USER_CERT' in os.environ and 'X509_USER_KEY' in os.environ:
      print 'X509_USER_CERT and X509_USER_KEY found'
      conn = httplib.HTTPSConnection(url, cert_file = os.getenv('X509_USER_CERT'), key_file = os.getenv('X509_USER_KEY'))
  else:
      print 'You need a valid proxy or cert/key files'
      sys.exit()
  print 'conn found in if else structure'
  r1=conn.request("GET",api, None, headers)
  print 'r1 passed'
  r2=conn.getresponse()
  print 'r2 passed'
  inputjson=r2.read()
  print '-------------------------------------------------------------'
  #print inputjson
  result = simplejson.loads(inputjson)
  conn.close()
  return result

def getNonWaitingRoomSites(url):
    tmp_sites = []
    request = urllib2.Request(url)
    response = urllib2.urlopen(request)
    data = response.read()
    d_split = data.split('\n')
     
    for row in d_split:
      if not row.strip().startswith("#"):
        split_row = row.split('\t')
        if len(split_row)>1:
          #print split_row
          #print split_row[1] 
          tmp_sites.append(split_row[1]) 
    return tmp_sites

def main_function(outputfile_txt):
  # non-waitingroom sites
  print 'Fetchting all the sites that are not in waitingroom'
  nonWaitingRoom_Sites = getNonWaitingRoomSites(url2)
  print 'number of non waiting room  sites: ', len(nonWaitingRoom_Sites)
  print nonWaitingRoom_Sites
  print '------------------------------------------'

  # all sites
  print 'starting to fetch all sites from siteDB'
  jn = fetch_all_sites('cmsweb.cern.ch','/sitedb/data/prod/site-names') 
  #json form:
  #{"desc": {"columns": ["type", "site_name", "alias"]}, 
  # "result": [
  #             ["cms", "ASGC", "T1_TW_ASGC"],
  #             ["cms", "BY-NCPHEP", "T3_BY_NCPHEP"]
  #            ...
  
  # match the information 

  #print jn['result']
  #site_T1= []
  site_T2= []
  #site_T3= []
  #print 'printing i'
  for i in jn['result']:
    if i[jn['desc']['columns'].index('type')]=='cms':
      sitedbname=i[jn['desc']['columns'].index('alias')]
      #print sitedbname
      #if 'T1' in sitedbname: 
      #  site_T1.append(sitedbname)
      if 'T2' in sitedbname:
        site_T2.append(sitedbname)
      #if 'T3' in sitedbname: 
      #   site_T3.append(sitedbname)

  
  #print site_T2

  print '--------------------------------------------------------'
  print 'Sites in waiting room:'
  waitingRoom_sites = [ site for site in site_T2 if not site in nonWaitingRoom_Sites]
  print waitingRoom_sites
  #write to file for SSB
  f1=open('./'+outputfile_txt, 'w+')
  now_write=(datetime.utcnow()).strftime("%Y-%m-%d %H:%M:%S")


  # write file that can be loaded in SSB
  f1.write('# This txt goes into SSB and marks sites red when the site is in the waiting room:\n')
  f1.write('# This file should be updated once a day.\n')

  print "Local current time :", now_write
  for k in waitingRoom_sites:
    print k, 'yes', 'red', url2
    f1.write(now_write+' '+k+' yes red '+url2+'\n')
  for k in site_T2: 
    if not k in waitingRoom_sites:
      print k, 'no', 'green', url2 
      f1.write(now_write+' '+k+' no green '+url2+'\n')

if __name__ == '__main__':
  outputfile_txt=sys.argv[1]
  main_function(outputfile_txt)
