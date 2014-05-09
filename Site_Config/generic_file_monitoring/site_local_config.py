#!/usr/bin/python
import os, sys
import time
import urllib, httplib, urllib2
import string
import simplejson
from xml.dom.minidom import parse, parseString
from xml import xpath
#_____________________________________________________________________________

siteList = {}
T1Count = 0
T2Count = 0
#________________________________________________________________________________________
# functions fetchs all siteName and gets all xml file.
def fetch_all_sites(url, api):
  #________________fetch all siteName from siteDB v2________________________________
  headers = {"Accept": "application/json"}
  if 'X509_USER_PROXY' in os.environ:
    conn = httplib.HTTPSConnection(url, cert_file = os.getenv('X509_USER_PROXY'), key_file = os.getenv('X509_USER_PROXY'))
  r1=conn.request("GET",api, None, headers)
  r2=conn.getresponse()
  inputjson=r2.read()
  jn = simplejson.loads(inputjson)
  conn.close()
  sitesList=[]
  for site in jn['result']:
    sitesList.append(site[3])    
  #______________________________________________________________________________________
  # To get all site-local-config information.
  for siteName in sitesList:
    xml = getXmlfromURL('cmsweb.cern.ch','/gitweb/?p=siteconf/.git;a=blob_plain;f=' + siteName + '/JobConfig/site-local-config.xml;hb=HEAD')
    match(xml, siteName)
#__________________________________________________________________________________________
# function calculates the number of T1s and T2s counts and writes results to console and file.
def match(xml, siteName):
  global T1Count, T2Count, file, jsonCode
  findTxt = "404 - Cannot find file"
  saveTime = time.strftime('%Y-%m-%d %H:%M:%S')
  url = "https://cmsweb.cern.ch/gitweb/?p=siteconf/.git;a=blob_plain;f=" + siteName + "/JobConfig/site-local-config.xml;hb=HEAD"
  if (findTxt in xml) == False:
    dom  = parseString(xml)
    tag  = dom.getElementsByTagName('site-local-config')[0].getElementsByTagName('site')[0].getElementsByTagName('statistics-destination')
    if len(tag):
      print saveTime + "\t" + siteName + "\t" + "yes" + "\t" + "green" + "\t" + url
      file.write(saveTime + "\t" + siteName + "\t" + "yes" + "\t" + "green" + "\t" + url + "\n")
      jsonCode = jsonCode + "{" + '"siteName":"' + siteName + '", "yes_no":' + '"yes"' + ',' + '"color":"green' + '",' + '"url":"' + url + '"},'    
      if (siteName[0:2] == "T1") : T1Count = T1Count + 1
      if (siteName[0:2] == "T2") : T2Count = T2Count + 1
    else:
      print saveTime + "\t" + siteName + "\t" + "no" + "\t" + "red" + "\t" + url
      file.write(saveTime + "\t" + siteName + "\t" + "no" + "\t" + "red" + "\t" + url + "\n")
      jsonCode = jsonCode + "{" + '"siteName":"' + siteName + '", "yes_no":' + '"no"' + ',' + '"color":"red' + '",' + '"url":"' + url + '"},' 
  else:
    print saveTime + "\t" + siteName + "\t" + "no" + "\t" + "red" + "\t" + url
    file.write(saveTime + "\t" + siteName + "\t" + "no" + "\t" + "red" + "\t" + url + "\n")
    jsonCode = jsonCode + "{" + '"siteName":"' + siteName + '", "yes_no":' + '"no"' + ',' + '"color":"red' + '",' + '"url":"' + url + '"},'
#_______________________________________________________________________________
# function reads  your certificate and gets site-local-config.xml from URL
def getXmlfromURL(url,api):
  headers = {"Accept": "application/xml"}
  if 'X509_USER_PROXY' in os.environ:
      #print 'X509_USER_PROXY found'
      conn = httplib.HTTPSConnection(url, cert_file = os.getenv('X509_USER_PROXY'), key_file = os.getenv('X509_USER_PROXY'))
  elif 'X509_USER_CERT' in os.environ and 'X509_USER_KEY' in os.environ:
      #print 'X509_USER_CERT and X509_USER_KEY found'
      conn = httplib.HTTPSConnection(url, cert_file = os.getenv('X509_USER_CERT'), key_file = os.getenv('X509_USER_KEY'))
  else:
      #print 'You need a valid proxy or cert/key files'
      sys.exit()
  r1=conn.request("GET",api, None, headers)
  r2=conn.getresponse()
  xml = r2.read()
  return xml
#_____________________________________________________________________________
if __name__ == '__main__':
  outputfile_txt=sys.argv[1]
  print 'starting to fetch all site and calculate the number of T1s and T2s counts.'
  file = open(outputfile_txt + ".txt", "w")
  jsonFile = open(outputfile_txt + ".json", "w")
  jsonCode = '{ "site_local_config":['
  jsonCodeEnd = ']}'
  fetch_all_sites('cmsweb.cern.ch','/sitedb/data/prod/federations-sites')
  saveTime = time.strftime('%Y-%m-%d %H:%M:%S')
  url = "https://cmsweb.cern.ch/gitweb/?p=siteconf/.git;a=tree"
  print saveTime + "\t" + "T1s" + "\t" + str(T1Count) + "\t" + "green" + "\t" + url
  print saveTime + "\t" + "T2s" + "\t" + str(T2Count) + "\t" + "green" + "\t" + url
  file.write(saveTime + "\t" + "T1s" + "\t" + str(T1Count) + "\t" + "green" + "\t" + url + "\n")
  file.write(saveTime + "\t" + "T2s" + "\t" + str(T2Count) + "\t" + "green" + "\t" + url + "\n")
  file.close()
  jsonCode = jsonCode + "{" + '"T1s":' + str(T1Count)  + ',' + '"color":"green' + '",' + '"url":"' + url + '"},'
  jsonCode = jsonCode + "{" + '"T2s":' + str(T2Count)  + ',' + '"color":"green' + '",' + '"url":"' + url + '"},'
  jsonCode = (jsonCode + jsonCodeEnd).replace("},]}", "}]}")
  jsonFile.write(jsonCode)
  jsonFile.close()
