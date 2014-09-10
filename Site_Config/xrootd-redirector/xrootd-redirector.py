#!/usr/bin/python
import os, sys
import time
import urllib, httplib, urllib2
import string
import simplejson
from xml.dom.minidom import parse, parseString
#_____________________________________________________________________________
siteList = {}
global findText1
global findText2
T1Count = 0     # number of sites without the findText in site-local-config 
T2Count = 0
#________________________________________________________________________________________
# functions fetchs all siteName and gets all xml file.
def fetch_all_sites(url, api):
    #________________fetch all siteName from siteDB v2________________________________
    headers = {"Accept": "application/json"}
    if 'X509_USER_PROXY' in os.environ:
      print 'X509_USER_PROXY found'
      conn = httplib.HTTPSConnection(url, cert_file = os.getenv('X509_USER_PROXY'), key_file = os.getenv('X509_USER_PROXY'))
    elif 'X509_USER_CERT' in os.environ and 'X509_USER_KEY' in os.environ:
        print 'X509_USER_CERT and X509_USER_KEY found'
        conn = httplib.HTTPSConnection(url, cert_file = os.getenv('X509_USER_CERT'), key_file = os.getenv('X509_USER_KEY'))
    elif os.path.isfile('/data/certs/servicecert.pem') and os.path.isfile('/data/certs/servicekey.pem'):
        conn = httplib.HTTPSConnection(url, cert_file = '/data/certs/servicecert.pem', key_file = '/data/certs/servicekey.pem')
    else:
        print 'You need a valid proxy or cert/key files'
        sys.exit()
    r1=conn.request("GET",api, None, headers)
    r2=conn.getresponse()
    inputjson=r2.read()
    jn = simplejson.loads(inputjson)
    conn.close()
    sitesList=[]
    for site in jn['result']:
        if site[3][0:2] != 'T3':
            sitesList.append(site[3])
    #______________________________________________________________________________________
    # To get all site-local-config information.
    for siteName in sitesList:
        xml = getXmlfromURL('cmsweb.cern.ch','/gitweb/?p=siteconf/.git;a=blob_plain;f=' + siteName + '/PhEDEx/storage.xml;hb=HEAD')   
        match(xml, siteName, findText1, findText2)
#__________________________________________________________________________________________
# function calculates the number of T1s and T2s counts and writes results to console and file.
def match(xml, siteName, findText1, findText2):
    global T1Count, T2Count, file, jsonCode
    findTxt = "404 - Cannot find file"
    saveTime = time.strftime('%Y-%m-%d %H:%M:%S')
    url = "https://cmsweb.cern.ch/gitweb/?p=siteconf/.git;a=blob_plain;f=" + siteName + "/PhEDEx/storage.xml;hb=HEAD"
    n = 0
    while n < 3:
        if (findTxt in xml) == False:       # site-local-config file found
            dom = parseString(xml)
            tag = dom.getElementsByTagName('lfn-to-pfn')
            val = 0
            for s in tag:
                if (findText1 in s.getAttribute('result')) or (findText2 in s.getAttribute('result')):
                    val = 1
            if val == 1:                    # findText found in file
                n = 3
                print saveTime + "\t" + siteName + "\t" + "yes" + "\t" + "green" + "\t" + url
                file.write(saveTime + "\t" + siteName + "\t" + "yes" + "\t" + "green" + "\t" + url + "\n")    
            else:                           # findText not found in file
                if (siteName[0:2] == "T1"): n = n + 1
                else: n = 3
                
                if n == 1:
                    xml = getXmlfromURL('cmsweb.cern.ch','/gitweb/?p=siteconf/.git;a=blob_plain;f=' + siteName + '/PhEDEx/storage-disk.xml;hb=HEAD')
                    url = "https://cmsweb.cern.ch/gitweb/?p=siteconf/.git;a=blob_plain;f=" + siteName + "/PhEDEx/storage-disk.xml;hb=HEAD"
                elif n == 2:
                    xml = getXmlfromURL('cmsweb.cern.ch','/gitweb/?p=siteconf/.git;a=blob_plain;f=' + siteName + '/PhEDEx/storage_disk.xml;hb=HEAD')
                    url = "https://cmsweb.cern.ch/gitweb/?p=siteconf/.git;a=blob_plain;f=" + siteName + "/PhEDEx/storage_disk.xml;hb=HEAD"
                else:
                    print saveTime + "\t" + siteName + "\t" + "no" + "\t" + "red" + "\t" + url
                    file.write(saveTime + "\t" + siteName + "\t" + "no" + "\t" + "red" + "\t" + url + "\n")
                    if (siteName[0:2] == "T1") : T1Count = T1Count + 1
                    if (siteName[0:2] == "T2") : T2Count = T2Count + 1 
        else:                             # couldn't find site-local-config file
            if (siteName[0:2] == "T1"): n = n + 1
            else: n = 3
            
            if n == 1:
                xml = getXmlfromURL('cmsweb.cern.ch','/gitweb/?p=siteconf/.git;a=blob_plain;f=' + siteName + '/PhEDEx/storage-disk.xml;hb=HEAD')
                url = "https://cmsweb.cern.ch/gitweb/?p=siteconf/.git;a=blob_plain;f=" + siteName + "/PhEDEx/storage-disk.xml;hb=HEAD"
            elif n == 2:
                xml = getXmlfromURL('cmsweb.cern.ch','/gitweb/?p=siteconf/.git;a=blob_plain;f=' + siteName + '/PhEDEx/storage_disk.xml;hb=HEAD')
                url = "https://cmsweb.cern.ch/gitweb/?p=siteconf/.git;a=blob_plain;f=" + siteName + "/PhEDEx/storage_disk.xml;hb=HEAD"
            else:
                print saveTime + "\t" + siteName + "\t" + "no" + "\t" + "white" + "\t" + url
                file.write(saveTime + "\t" + siteName + "\t" + "no" + "\t" + "white" + "\t" + url + "\n")
                if (siteName[0:2] == "T1") : T1Count = T1Count + 1
                if (siteName[0:2] == "T2") : T2Count = T2Count + 1
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
  elif os.path.isfile('/data/certs/servicecert.pem') and os.path.isfile('/data/certs/servicekey.pem'):
      conn = httplib.HTTPSConnection(url, cert_file = '/data/certs/servicecert.pem', key_file = '/data/certs/servicekey.pem')
  else:
      print 'You need a valid proxy or cert/key files'
      sys.exit()
  r1=conn.request("GET",api, None, headers)
  r2=conn.getresponse()
  xml = r2.read()
  return xml
#_____________________________________________________________________________
if __name__ == '__main__':
  outputfile_txt=sys.argv[1]
  print outputfile_txt
  findText1=sys.argv[2]
  findText2=sys.argv[3]
  print findText1
  print findText2
  print 'starting to fetch all site and calculate the number of T1s and T2s counts.'
  file = open(outputfile_txt + ".txt", "w")
  fetch_all_sites('cmsweb.cern.ch','/sitedb/data/prod/federations-sites')
  saveTime = time.strftime('%Y-%m-%d %H:%M:%S')
  url = "https://cmsweb.cern.ch/gitweb/?p=siteconf/.git;a=tree"
  print saveTime + "\t" + "T1s" + "\t" + str(T1Count) + "\t" + "red" + "\t" + url
  print saveTime + "\t" + "T2s" + "\t" + str(T2Count) + "\t" + "red" + "\t" + url
  file.write(saveTime + "\t" + "T1s" + "\t" + str(T1Count) + "\t" + "red" + "\t" + url + "\n")
  file.write(saveTime + "\t" + "T2s" + "\t" + str(T2Count) + "\t" + "red" + "\t" + url + "\n")
  file.close()