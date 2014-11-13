import os,sys,time
from xml.dom.minidom import parse, parseString
import simplejson
import simplejson as json
import  httplib
import operator

#_______________________________________________________________
def getJSONfromSiteDB():
  headers = {"Accept": "application/json"}
  url = "cmsweb.cern.ch"
  api = "/sitedb/data/prod/site-names"
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
  return jn

#______________________________________________________________
def convertLCGtoCMS(jn, getlcgName, mode):
  lcgNames = {}
  for row in jn['result']:
    if row[0] == 'lcg':
      lcgNames[row[2]] = row[1]
  siteNames = {}
  for row in jn['result']:
    if row[0] == 'cms':
      siteNames[row[1]] = row[2]
  lcgtoCms = {}

  for lcgName in lcgNames:
    if siteNames.has_key(lcgNames[lcgName]):
      lcgtoCms[lcgName] = siteNames[lcgNames[lcgName]]

  if mode != 'cms':
    if not lcgtoCms.has_key(getlcgName):
      return 'cms'
    else:
      return lcgtoCms[getlcgName]
  else:
    return lcgtoCms

#______________________________________________________________
def ReadXML(fileName):
  fileHandle = open(fileName)
  data  = fileHandle.read()
  if "&ldquo;" in data:
    data = data.replace("&ldquo;" , " ")
  if "&rdquo;" in data:
    data = data.replace("&rdquo;" , " ")
  fileHandle.close()
  return data

#______________________________________________________________
def getTicketNumbers(dom, lcgName):
  tag  = dom.getElementsByTagName('tickets')[0].childNodes
  count = len(tag)
  ticketlist = []
  for i in range(count):
    try:
      siteName = dom.getElementsByTagName('tickets')[0].getElementsByTagName('ticket')[i].getElementsByTagName('affected_site')[0].firstChild.nodeValue
    except AttributeError:
      continue
    if siteName == lcgName:
      ticketNumber = dom.getElementsByTagName('tickets')[0].getElementsByTagName('ticket')[i].getElementsByTagName('request_id')[0].firstChild.nodeValue
      url = "https://ggus.eu/?mode=ticket_info&ticket_id=" + ticketNumber
      ticketURL = "[" + "[" + url +  "]" + "[" + ticketNumber +  "]" + "]"
      ticketlist.append(ticketURL)
  return ticketlist
#______________________________________________________________

if __name__ == '__main__':
  json = getJSONfromSiteDB()
  text = ReadXML('/afs/cern.ch/user/c/cmst1/scratch0/MonitoringScripts/GGUS/tickets.xml')
  dom  = parseString(text)
  tag  = dom.getElementsByTagName('tickets')[0].childNodes
  count = len(tag)
  sites = {}
  #________________________get ticket information and calculate number of tickets______________________________
  for i in range(count):
    try:
      siteName = dom.getElementsByTagName('tickets')[0].getElementsByTagName('ticket')[i].getElementsByTagName('affected_site')[0].firstChild.nodeValue
    except AttributeError:
      continue
    if not sites.has_key(siteName): sites[siteName] = 0
    sites[siteName] += 1
  #____________________________________________________________________________________________________________
  saveTime = time.strftime('%Y-%m-%d %H:%M:%S')
  fileOp   = open("/afs/cern.ch/user/c/cmst1/scratch0/MonitoringScripts/GGUS/ggusticketmetrics.txt" , "w")
  fileMeet = open("/afs/cern.ch/user/c/cmst1/scratch0/MonitoringScripts/GGUS/ggusticketmeeting.txt" , "w")
  fileMeet.write("| *Order* | *SiteName* | *Ticket Count* | *Tickets* |" + "\n")
  lcgNames =  convertLCGtoCMS(json, '', 'cms')
  order    = 0
  for lcgName in lcgNames:
    color = "green"
    if sites.has_key(lcgName):
      cmsSiteName = convertLCGtoCMS(json, lcgName, 'lcg')
      ticketCount = sites[lcgName]
      order = order + 1
      #________________________To write Tickets List for CompOps Meeting______________________________
      fileMeet.write(" | " + str(order) + " | "  + cmsSiteName + " | " + str(ticketCount) + " | " + ' , '.join(getTicketNumbers(dom, lcgName)) + " | " + "\n")
      #_______________________________________________________________________________________________
    else:
      cmsSiteName = lcgNames[lcgName]
      ticketCount = 0
    url = "https://ggus.eu/?mode=ticket_search&cms_site=" + cmsSiteName + "&timeframe=any&status=open&search_submit=GO%21"
    if ticketCount > 0 : color = "red"
    i = i + 1
     #________________________To write sites for metricg______________________________    
    fileOp.write(saveTime + "\t" + cmsSiteName + "\t" + str(ticketCount) + "\t" + color + "\t" +  url + "\n" )
    #________________________________________________________________________________
  fileMeet.close()
  fileOp.close()