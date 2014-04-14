#!/usr/bin/python
import os, sys
import time
import urllib, httplib, urllib2
import string
from xml.dom.minidom import parse, parseString
#_____________________________________________________________________________

siteList = {}
T1Count = 0
T2Count = 0
#________________________________________________________________________________________
# functions fetchs all siteName and gets all xml file.
def fetch_all_site():
  sitesList =  ['T1_TW_ASGC','T1_FR_CCIN2P3','T1_CH_CERN','T1_IT_CNAF','T1_US_FNAL','T1_US_FNAL_Disk','T1_RU_JINR','T1_RU_JINR_Disk','T1_DE_KIT','T1_ES_PIC','T1_UK_RAL','T1_UK_RAL_Disk','T2_IT_Bari','T2_CN_Beijing','T2_UK_SGrid_Bristol','T2_UK_London_Brunel','T2_FR_CCIN2P3','T2_CH_CERN','T2_CH_CERN_AI','T2_CH_CERN_HLT','T2_CH_CERN_T0','T2_ES_CIEMAT','T2_CH_CSCS','T2_TH_CUNSTDA','T2_US_Caltech','T2_DE_DESY','T2_EE_Estonia','T2_US_Florida','T2_FR_GRIF_IRFU','T2_FR_GRIF_LLR','T2_BR_UERJ','T2_FI_HIP','T2_AT_Vienna','T2_HU_Budapest','T2_UK_London_IC','T2_ES_IFCA','T2_RU_IHEP','T2_BE_IIHE','T2_RU_INR', 'T2_FR_IPHC','T2_RU_ITEP','T2_GR_Ioannina','T2_RU_JINR','T2_UA_KIPT','T2_KR_KNU','T2_IT_Legnaro','T2_BE_UCL','T2_TR_METU','T2_US_MIT','T2_PT_NCG_Lisbon','T2_PK_NCP','T2_US_Nebraska','T2_RU_PNPI','T2_IT_Pisa','T2_US_Purdue', 'T2_RU_RRC_KI','T2_DE_RWTH','T2_IT_Rome','T2_UK_SGrid_RALPP','T2_RU_SINP','T2_BR_SPRACE','T2_IN_TIFR','T2_TW_Taiwan','T2_US_UCSD','T2_MY_UPM_BIRUNI', 'T2_US_Vanderbilt','T2_PL_Warsaw','T2_US_Wisconsin']
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
  url = "cmsweb.cern.ch/gitweb/?p=siteconf/.git;a=blob_plain;f=" + siteName + "/JobConfig/site-local-config.xml;hb=HEAD"
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
  fetch_all_site()
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
