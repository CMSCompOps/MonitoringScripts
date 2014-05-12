#!/usr/bin/python
import os, sys
import simplejson
import simplejson as json
import time
import urllib, httplib, urllib2
import string
#_____________________________________________________________________________

# function needed to fetch a list of all pledges values from siteDB
def fetch_all_pledges(url,api):
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
  jsn = simplejson.loads(inputjson)
  pledges= {}
  pledgesSites = {}
  count = 0
  pledgeCurTime = int(time.strftime("%Y"))
  for i in jsn['result']:
    #_____________________________
    print i
    pledgeDate     = i[2]
    pledgeTime     = i[1]
    pledgeSiteName = i[0]
    #pledgeCpuValue = i[3]
    #_____________________________
    if pledgeDate == pledgeCurTime:
      current = time.time()
      diff = current - pledgeTime
      if pledges.has_key(pledgeSiteName):
        pledges[pledgeSiteName][diff] = {"time":i[1], "cpu":i[3] * 100}
      else:
        pledges[pledgeSiteName] = {diff:{"time":i[1], "cpu":i[3] * 100}}
  for site in pledges.keys():
    min_site = min(pledges[site].keys())
    pledgesSites[site] = pledges[site][min_site]['cpu']
  return pledgesSites
#_____________________________________________________________________________

# function matchs pledges values gets from siteDB with SiteName

def matchPledges(pledgeList):
  #_______________________fetch all siteName : FederationName because Pledges is defined by federation name not siteName._____________________
  headers = {"Accept": "application/json"}
  url = "cmsweb.cern.ch"
  api = "/sitedb/data/prod/federations-sites"
  sitesList=[]
  matchList = {}
  if 'X509_USER_PROXY' in os.environ:
    print 'X509_USER_PROXY found'
    conn = httplib.HTTPSConnection(url, cert_file = os.getenv('X509_USER_PROXY'), key_file = os.getenv('X509_USER_PROXY'))
  r1=conn.request("GET",api, None, headers)
  r2=conn.getresponse()
  inputjson=r2.read()
  jn = simplejson.loads(inputjson)
  conn.close()

  for siteName in jn['result']:
      if siteName[3][0:2] != 'T3':
         matchList[siteName[3]] = siteName[2]
         sitesList.append(siteName[3])
  #___________________________________________________________________________________________________________________________
  pledges = {}
#_____________________________________________________________________________
  for site in matchList:
    if pledgeList.has_key(matchList[site]):
    	valPos = str(pledgeList[matchList[site]]).find('.') 
    	pledges[site] = int(str(pledgeList[matchList[site]])[0:valPos])
    else:
      	pledges[site] = "n/a"
  return pledges
#____________________function creates JSON TXT file________________
def savetoFile(pledges, outputfile_txt):
  saveTime = time.strftime('%Y-%m-%d %H:%M:%S')
  url = "https://cmsweb.cern.ch/sitedb/prod/pledges "
  #_______________JSON__________________________________________________
  filename = outputfile_txt + ".json"
  fileOp = open(filename, "w")
  fileOp.write(unicode(simplejson.dumps(pledges, ensure_ascii=False)))
  fileOp.close()
  #_______________the List_____________________________________________
  filename = outputfile_txt + ".txt"
  fileOp = open(filename, "w")
  for tmpPledges in pledges:
      if (pledges[tmpPledges]      == 0)     : color = 'yellow'
      if (pledges[tmpPledges]      > 0)      : color = 'green'
      if (str(pledges[tmpPledges]) == 'n/a') : color = 'white'
      fileOp.write(saveTime + "\t" + tmpPledges + "\t" + str(pledges[tmpPledges]) + "\t" + color + "\t" +  url + "\n" )
  fileOp.close()

if __name__ == '__main__':
  outputfile_txt=sys.argv[1]
  print 'starting to fetch all pledges from siteDB'
  allPledgeList = fetch_all_pledges('cmsweb.cern.ch','/sitedb/data/prod/resource-pledges')
  pledges       = matchPledges(allPledgeList)
  savetoFile(pledges, outputfile_txt)
