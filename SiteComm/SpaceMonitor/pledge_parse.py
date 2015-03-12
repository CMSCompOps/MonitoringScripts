#!/usr/bin/python
import string, os
import xml.dom.minidom
from xml import xpath

def getChildValue(element, child):
  child = element.getElementsByTagName(child)[0].firstChild
  if child is not None:
    return str(child.nodeValue)
  return None


pid=os.getpid()
namesUrl= 'https://cmsweb.cern.ch/sitedb/sitedb/reports/showXMLReport/?reportid=naming_convention.ini'

fileN="/tmp/sitelist.%i" % pid


os.system('wget -q --no-check-certificate -O  %s %s' % (fileN, namesUrl))
f=file(fileN,'r')
t= xml.dom.minidom.parse(f)
f.close()

Sites={}
for url in xpath.Evaluate('report/result/item', t):
  samName=getChildValue(url, 'sam')
  cmsName=getChildValue(url, 'cms')
  numId=getChildValue(url, 'id')
  if cmsName not in Sites.keys():
    Sites[cmsName]=numId

sortedSites=Sites.keys()
sortedSites.sort()

pledgeBaseUrl="https://cmsweb.cern.ch/sitedb/sitedb/xml/index/Pledge?site="
for site in sortedSites:
    id=Sites[site]
    pledgeUrl= pledgeBaseUrl + id
    pledgeBaseUrl="https://cmsweb.cern.ch/sitedb/sitedb/xml/index/Pledge?site="
    curlcommand='curl -ks "'+pledgeUrl+'"'
    SiteDBData='\n'.join(os.popen(curlcommand).readlines())
    pledgeDataXML = xml.dom.minidom.parseString(SiteDBData)
    pledgeDataElement = xpath.Evaluate('SiteDB', pledgeDataXML)[0]
    disk = getChildValue (pledgeDataElement, 'disk_store_-_TB')
    disk=int(float(disk))
    tape = getChildValue (pledgeDataElement, 'tape_store_-_TB')
    tape = int(float(tape))
    slots = getChildValue (pledgeDataElement, 'job_slots_-_')
    slots=int(float(slots))
    print id, site, slots, disk, tape
