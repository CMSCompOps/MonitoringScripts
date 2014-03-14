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
  url='http://dashb-ssb.cern.ch/dashboard/request.py/getplotdata?columnid='+col+'&time=custom&dateFrom='+startDate+'&dateTo='+endDate+'&sites=T2&batch=1'
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
  #print inputjson
  jn = simplejson.loads(inputjson)
  conn.close()

  #result json form:
  #{"desc": {"columns": ["type", "site_name", "alias"]}, 
  # "result": [
  #             ["cms", "ASGC", "T1_TW_ASGC"],
  #             ["cms", "BY-NCPHEP", "T3_BY_NCPHEP"]
  #            ...
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
  return site_T2

#_______________________________________________________________________

def main_function(outputfile_txt, submonths,allSites):

  # waitingroomextracting, base url without date
  columnnumber='153'
  enddate=date.today()
  startdate=addmonths(enddate,submonths)
  start=startdate.strftime("%Y-%m-%d")
  end=enddate.strftime("%Y-%m-%d")
             
  jsn=extractJson(columnnumber, start, end)
  f=open('tmpjson.json','w')
  f.write(unicode(simplejson.dumps(jsn, ensure_ascii=False)))
  f.close()

  # sum @ days 
  days_per_site={}
  for site in allSites:
    nb_days=0
    # initialse date_check with the date of the previous month. If date[k] == date_check that will be ignored
    # since we already checked the yes or no for this day...
    date_check = addmonths(  datetime(*(time.strptime(jsn['csvdata'][0]['Time'],'%Y-%m-%dT%H:%M:%S')[0:6]))  ,-1)
    #print date_check
    for k in jsn['csvdata']:
      #print k
      if k['VOName'] != site: continue
      elif k['COLORNAME'] == 'green': continue
      elif k['COLORNAME'] == 'white' : continue #white ..
      # startime of entry
   
#-------------------------------------------------------------------------------------------------------------------------------------------
#*************************************************************** Modification****************************************************************
#-------------------------------------------------------------------------------------------------------------------------------------------------

      starttime = datetime(*(time.strptime( k['Time'] ,'%Y-%m-%dT%H:%M:%S')[0:6]))
      endtime=datetime(*(time.strptime( k['EndTime'] ,'%Y-%m-%dT%H:%M:%S')[0:6]))
      day_string = endtime.strftime('%Y-%m-%d %H:%M:%S')
      date_string  = day_string.split(" ")[0].split('-') #date split.
      time_string  = day_string.split(" ")[1]
      gMonth = date_string[1]
     #_______________________________________________________________________________________________________________________________ 
      # if metric is 1 month, things which is to do
      if submonths == -1:
        if gMonth == '01':
          date_string[0] = str(int(date_string[0]) - 1)
          dateMonth = '12'
        else:
          dateMonth = int(date_string[1]) - 1
     #_______________________________________________________________________________________________________________________________ 
      # if metric is 2 months, things which is to do
      if submonths == -2:
        if gMonth == '01':
          dateMonth = '11'
          date_string[0] = str(int(date_string[0]) - 1)
        elif gMonth == '02':
          dateMonth = '12'
          date_string[0] = str(int(date_string[0]) - 1)
        else:
          dateMonth = int(date_string[1]) - 2
     #_______________________________________________________________________________________________________________________________     
       # if metric is 3 months, things which is to do
      if submonths == -3:
        if gMonth == '01':
          dateMonth = '10'
          date_string[0] = str(int(date_string[0]) - 1)
        elif gMonth == '02':
          dateMonth = '11'
          date_string[0] = str(int(date_string[0]) - 1)
        elif gMonth == '03':
          dateMonth = '12'
          date_string[0] = str(int(date_string[0]) - 1)
        else:
          dateMonth = int(date_string[1]) - 3
      #_____________________________________________________________________________________________________________________________
      if len(str(dateMonth)) < 2: date_string[1] = '0' + str(dateMonth)
      else: date_string[1] = str(dateMonth)
      realDate = date_string[0] + '-' + date_string[1] + '-' + str(int(date_string[2]) + 1) + 'T' + time_string
      starttime = datetime(*(time.strptime( realDate , '%Y-%m-%dT%H:%M:%S') [0:6]))

#---------------------------------------------------------------------------------------------------------------------------------------------



      # it means we had the interval Time TimeEnd for a few days, and the loop is not yet past this last day,
      # where we already counted a yes
      if date_check >=  starttime.date() : continue  
      # so IF CLORNAME==RED
      # count the first day if its not the same as the last day from the previous entry
      if date_check != starttime.date(): nb_days+=1   
      # Then if this state stays the same for multiple days,: # days for EndTime -Time, and then update date_check to EndTime
      delta = endtime.date() - starttime.date()
      nb_days+=delta.days
      #print delta, delta.days
      print starttime, endtime
      date_check=endtime.date()
    if nb_days != 0: 
      print site, ': ', nb_days
      print '---------------------------------------'
    days_per_site[site]=nb_days  
  print days_per_site

  # write to file
  f1=open('./'+outputfile_txt, 'w+')
  f1.write('# This txt goes into SSB and shows the number of days a site has been in the waiting list for X months (seefilename)\n')
  f1.write('# Readme: https://cmsdoc.cern.ch/cms/LCG/SiteComm/MonitoringScripts/SR_View_SSB/WRDays/README.txt\n')
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

