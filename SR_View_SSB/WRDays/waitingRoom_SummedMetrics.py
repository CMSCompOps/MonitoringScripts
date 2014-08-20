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
   print calendar.monthrange(year,month)[1]
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

# function needed to fetch a list of all sites from metric 153
def fetch_all_sites(jsn):
  site_T2 = []
  for row in jsn['csvdata']:
    if row['VOName'][0:2] == 'T2':
      site_T2.append(row['VOName'])
  return site_T2
#_______________________________________________________________________

def main_function(outputfile_txt, submonths):
  print outputfile_txt
  columnnumber='153'
  enddate=date.today() # query date
  startdate=addmonths(enddate,submonths) # query date
  start=startdate.strftime("%Y-%m-%d") # as string field to query
  end=enddate.strftime("%Y-%m-%d") # as string field to query
  jsn=extractJson(columnnumber, start, end) # results from dashboard extracts into JSON file
  allSites = fetch_all_sites(jsn) 
  # sum @ days 
  days_per_site={}
  for site in allSites: # Read all sites from allsites variable
    wrDays = 0 # keeps number of wrDays per Site
    days = 0  # keeps temporary wrDays
    temp = 0  
    for k in jsn['csvdata']: # JSON file reads.
      if k['VOName'] != site: continue
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
      			temp = days.days
			if endtime.date() > enddate: temp = temp - 1
			wrDays+= temp
      	elif startdate <= starttime.date():
      		days = endtime.date() - starttime.date()
		temp = days.days
		if endtime.date() > enddate: temp = temp - 1
      		wrDays+= temp
      	days_per_site[site] = wrDays 
#******************************************************************************************************************************
    days_per_site[site] = wrDays
    if wrDays != 0 : 
    	print ('%s : %i') % (site , wrDays)
    	print '------------------------------'
  print days_per_site

  # write to file
  f1=open('./'+outputfile_txt, 'w+')
  f1.write('# This txt goes into SSB and shows the number of days a site has been in the Waiting Room for X months --> See filename)\n')
  f1.write('# Readme:\n# https://raw.githubusercontent.com/CMSCompOps/MonitoringScripts/master/SR_View_SSB/WRDays/Readme.txt\n')
  now_write = time.strftime('%Y-%m-%d %H:%M:%S')
  print "Local current time :", now_write
  link="https://dashb-ssb.cern.ch/dashboard/request.py/siteviewhistorywithstatistics?columnid=153#time=2184&start_date=&end_date=&use_downtimes=false&merge_colors=false&sites=all"
  for key, number in days_per_site.iteritems():
    color='green'
    if number !=0: color='red'
    print key, number, color, link
    f1.write(now_write+'\t'+key+'\t'+str(number)+'\t'+color+'\t'+link+'\n')
#_______________________________________________________________________

# run program for last month, last 2 months and last 3 months
if __name__ == '__main__':
  outputfile_txt=sys.argv[1]
  print 'starting to fetch all sites from siteDB'
  main_function(outputfile_txt+'1MonthSum.txt',-1)
  print '__________________________________________________'
  print '__________________________________________________'
  main_function(outputfile_txt+'2MonthSum.txt',-2)
  print '__________________________________________________'
  print '__________________________________________________'
  main_function(outputfile_txt+'3MonthSum.txt',-3)


