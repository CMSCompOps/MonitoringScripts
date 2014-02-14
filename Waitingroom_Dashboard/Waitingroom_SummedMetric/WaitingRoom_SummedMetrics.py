#!/usr/bin/python

import os, sys, errno
import urllib2
import simplejson
import time
from datetime import datetime
from datetime import timedelta
from datetime import date
import calendar
#import time
from pprint import pprint
import string
import urllib, httplib, re
import pickle 

#_______________________________________________________________________

def addmonths(sourcedate,months):
   month = sourcedate.month - 1 + months
   year = sourcedate.year + month / 12
   month = month % 12 + 1
   day = min(sourcedate.day,calendar.monthrange(year,month)[1])
   return date(year,month,day)

#_______________________________________________________________________

def extractJson(col, startDate, endDate):
  url='http://dashb-ssb.cern.ch/dashboard/request.py/getplotdata?columnid='+col+'&time=custom&dateFrom='+startDate+'&dateTo='+endDate+'&sites=T1&batch=1'
  print "Getting the url %s" % url
  request = urllib2.Request(url, headers = {"Accept":"application/json"})
  response = urllib2.urlopen(request)
  data = response.read()
  rows = simplejson.loads(data)
  return rows

#_______________________________________________________________________

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
  jn = simplejson.loads(inputjson)
  conn.close()

  site_T2= []
  for i in jn['result']:
    if i[jn['desc']['columns'].index('type')]=='cms':
      sitedbname=i[jn['desc']['columns'].index('alias')]
      if 'T2' in sitedbname:
        site_T2.append(sitedbname)
  return site_T2
#_______________________________________________________________________

def main_function(outputfile_txt, submonths,allSites):
  print outputfile_txt
  columnnumber='153'
  enddate=date.today() # query date
  startdate=addmonths(enddate,submonths) # query date
  start=startdate.strftime("%Y-%m-%d") # as string field to query
  end=enddate.strftime("%Y-%m-%d") # as string field to query
  jsn=extractJson(columnnumber, start, end) # results from dashboard extracts into JSON file
  filename = 'tmpjson' + start + '.json'
  f=open(filename,'w')
  f.write(unicode(simplejson.dumps(jsn, ensure_ascii=False)))
  f.close()
 
  # sum @ days 
  days_per_site={}
  for site in allSites: # Read all sites from allsites variable
    wrDays = 0 # keeps number of wrDays per Site
    days = 0  # keeps temporary wrDays 
    for k in jsn['csvdata']: # JSON file reads.
      if k['VOName'] != site: continue
      elif k['COLORNAME'] == 'green': continue # if the site is green continue
      elif k['COLORNAME'] == 'white' : continue # if the site is white continue
      # startime of entry
#************************************************Modifications**************************************
      elif k['COLORNAME'] == 'red': # if the site is red then calculate wrDays
      	starttime = datetime(*(time.strptime( k['Time'] ,'%Y-%m-%dT%H:%M:%S')[0:6])) # starttime from JSON file
      	endtime   = datetime(*(time.strptime( k['EndTime'] ,'%Y-%m-%dT%H:%M:%S')[0:6])) # endtime from JSON file
      	if startdate > starttime.date():
      		if startdate > endtime.date(): continue
      		elif startdate < endtime.date():
      			if startdate > starttime.date():
      				days = endtime.date() - startdate
      			elif startdate <= starttime.date():
      				days = endtime.date() - starttime.date()
      			wrDays+= days.days
      	elif startdate <= starttime.date():
      		days = endtime.date() - starttime.date()
		if endtime.date() > enddate: days-= 1
      		wrDays+= days.days
      	days_per_site[site] = wrDays 
#******************************************************************************************************************************
    days_per_site[site] = wrDays
    if wrDays != 0 : 
    	print ('%s : %i') % (site , wrDays)
    	print '------------------------------'
  print days_per_site


  # write to file
  f1=open('./'+outputfile_txt, 'w+')
  f1.write('# This txt goes into SSB and shows the number of days a site has been in the waiting list for X months (seefilename)\n')
  now_write=(datetime.utcnow()).strftime("%Y-%m-%d %H:%M:%S")
  print "Local current time :", now_write
  url2='http://dashb-ssb.cern.ch/dashboard/request.py/getplotdata?columnid=153'
  for key, number in days_per_site.iteritems():
    color='green'
    if number !=0: color='red'
    print key, number, color, url2
    f1.write(now_write+' '+key+' '+str(number)+' '+ color+' '+url2+'\n')

#_______________________________________________________________________

# run program for last month, last 2 months and last 3 months
if __name__ == '__main__':
  outputfile_txt=sys.argv[1]
  print 'starting to fetch all sites from siteDB'
  allSitesList = fetch_all_sites('cmsweb.cern.ch','/sitedb/data/prod/site-names')
  main_function(outputfile_txt+'1MonthSum.txt',-1,allSitesList)
  print '__________________________________________________'
  print '__________________________________________________'
  main_function(outputfile_txt+'2MonthSum.txt',-2,allSitesList)
  print '__________________________________________________'
  print '__________________________________________________'
  main_function(outputfile_txt+'3MonthSum.txt',-3,allSitesList)

