#!/usr/bin/python
import xml.dom.minidom
import os
from xml import xpath
import re
import datetime
import string
# waiting for SiteDB, map of PhEDEx Buffers to site name

today=datetime.datetime.utcnow()
timestamp=today.strftime("%Y-%m-%d %H:%M:%S")

pid=os.getpid()

def getTierNumber(name):
	l=re.match("^T(\d+)",name);
	if not l:
		print "Error getting the Tier number from %s" % name
		return
	return l.group(1)

def Buff2CMS(unicode_buffer):
	buffer=str(unicode_buffer)
	name=buffer
	i=string.find(buffer,"_Buffer")
	if i>0:
		name=buffer[0:i]
	i=string.find(buffer,"_MSS")
	if i>0:
		name=buffer[0:i]
	i=string.find(buffer,"_Disk")
	if i>0:
		name=buffer[0:i]
	i=string.find(buffer,"_Export")
	if i>0:
		name=buffer[0:i]
	return name

linksUrl= 'http://t2.unl.edu/phedex/xml/enabled?conn=Prod/NEBRASKA'
linksUrl= '"http://t2.unl.edu/phedex/xml/enabled?from_node=.*&excludefrom=MSS&excludeto=MSS&to_node=.*&conn=Prod/NEBRASKA"'

fileN="/tmp/siteviewtext.%i" % pid

fullPage="EnabledLinksStatus.html"
metricPage="EnabledLinksForSiteMonitor.txt"

#cmd='wget -q -O  %s %s' % (fileN, linksUrl)
cmd='curl --silent %s --output %s' % (linksUrl, fileN)
os.system(cmd)

f=file(fileN,'r')
t= xml.dom.minidom.parse(f)
f.close()

sites={}
siteStatus={}
for url in xpath.Evaluate('/graphtool/query/data/pivot', t):
	sourceBuffer=url.getAttribute("name")
	sourceName=Buff2CMS(sourceBuffer)
	if sourceName[0:2]=="XT": continue
	if sourceName=="": continue
	if sourceName=="T2_KIPT": continue
	if sourceName=="T2_CUKUROVA": continue
	if sourceName=="T1_ES_PIC_Disk": continue
	if sourceName=="T2_FR_GRIF_LAL": continue
	if sourceName=="T2_FR_GRIF_LPNHE": continue
	if sourceName=="T1_IT_CNAF_Disk": continue
	sourceTier=getTierNumber(sourceName)
	if not sourceTier: continue
	if not sites.has_key(sourceName):
		sites[sourceName]={'upT0':[], 'downT0':[],'upT1':[], 'downT1':[], 'upT2':[], 'downT2':[], 'upT3':[], 'downT3':[]}
	for target in xpath.Evaluate('group', url):
		targetBuffer=target.getAttribute("value")
		targetName=Buff2CMS(targetBuffer)
		if targetName[0:2]=="XT": continue
		if targetName=="": continue
		if targetName=="T1_ES_PIC_Disk": continue
		if targetName=="T1_IT_CNAF_Disk": continue
		targetTier=getTierNumber(targetName)
		if not targetTier: continue
		if sourceTier=="1" and targetName=="T1_CH_CERN":
			targetTier="0"
		if sourceName =="T1_CH_CERN" and targetTier=="1":
			sourceTier="0"
		if sourceName == "T1_CH_CERN": sourceName="T0_CH_CERN"
		if targetName == "T1_CH_CERN": targetName="T0_CH_CERN"
		value=xpath.Evaluate('d', target)
		ok=value[0].firstChild.nodeValue
		if (ok =='y'):
#			print "There is a link from %s to %s" % (sourceName, targetName)
			if not sites.has_key(targetName):
				sites[targetName]={'upT0':[], 'downT0':[],'upT1':[], 'downT1':[], 'upT2':[], 'downT2':[], 'upT3':[], 'downT3':[]}
			uplink='upT%s' % targetTier
			downlink='downT%s' % sourceTier
			sites[sourceName][uplink].append(targetName)
			sites[targetName][downlink].append(sourceName)


#print sites["T2_UK_SGrid_RALPP"]

keys=sites.keys()
keys.sort()


f=file(fullPage,'w')

f.write('<html>\n')
f.write('<head></head>\n')
f.write('<body>\n')
f.write('<h1>Site Status from Enabled Links</h1>\n')
f.write('Links status is from <a href="%s">%s</a>' % (linksUrl, linksUrl))
f.write(' &nbsp;&nbsp -- &nbsp;&nbsp ')
f.write('this page updated on %s UTC\n' % timestamp)
f.write('<p>\n')
#f.write('Site status is computed with following algorithm\n')
#f.write('<ul>\n')
#f.write('<li> CERN is always OK\n')
#f.write('<p>\n')
#f.write('<li> if a T1 has not up+down links from T0: error\n')
#f.write('<li> if a T1 has <4 up (down) links to the other 6 T1s: error\n')
#f.write('<li> if a T1 has <10 down links to T2s: error\n')
#f.write('<p>\n')
#f.write('<li> if a T2 has <1 up links to T1s: error\n')
#f.write('<li> if a T2 has <2 down links from T1s: error\n')
#f.write('</ul>\n')
f.write('Ony links to/from T0/T1/T2 are counted\n')
f.write('<p>\n')
f.write('Scroll down for links list\n')
f.write('<p>\n')
f.write('<table border=1>\n')
f.write('<tr><td>Site Name</td><td>To T0</td><td>From T0</td><td>To T1</td><td>From T1</td><td>To T2</td><td>From T2</td><td>Nup/Ndown</td></tr>\n')
for i in range(0,len(keys)):
	site=keys[i]
	if site=="T1_CH_CERN": continue
	if site=="T2_CH_CAF": continue
	isT1=0
	isT2=0
	isT3=0
	if site[1]=="1": isT1=1
	if site[1]=="2": isT2=1
	if site[1]=="3": isT3=1
	toT0=len(sites[site]["upT0"])
	fromT0=len(sites[site]["downT0"])
	toT1=len(sites[site]["upT1"])
	fromT1=len(sites[site]["downT1"])
	toT2=len(sites[site]["upT2"])
	fromT2=len(sites[site]["downT2"])
	
#	if isT1:
#		status="ok"
#		if toT0<1:   status="err"
#		if fromT0<1: status="err"
#		if toT1<4:   status="err"
#		if fromT1<4: status="err"
#		if toT2<10:  status="err"
#	if isT2:
#		status="ok"
#		if toT1<1:   status="err"
#		if fromT1<2: status="err"
#
#	if site=="T1_CH_CERN": status="ok"
#	if site=="T0_CH_CERN": status="ok"

	Nup=toT0+toT1+toT2
	Ndown=fromT0+fromT1+fromT2
	status=('%2d/%2d')%(Nup,Ndown)

	siteStatus[site]=status
	
	f.write('<tr>\n')
	f.write('<td>%20s</td>\n' %  site)
	f.write('<td>%2d</td>\n' % toT0)
	f.write('<td>%2d</td>\n' % fromT0)
	f.write('<td>%2d</td>\n' % toT1)
	f.write('<td>%2d</td>\n' % fromT1)
	f.write('<td>%2d</td>\n' % toT2)
	f.write('<td>%2d</td>\n' % fromT2)
	f.write('<td>%10s</td>\n' % status)
	
	f.write('</tr>\n')

f.write('</table>\n')

f.write('<hr>\n')

f.write('<table border=1>\n')
f.write('<tr><td>Site Name<td>UPlinks to T1</td><td>DOWNlinks from T1</td><td>UPlinks to T2</td><td>DOWNlinks from T2</td></tr>\n')
for i in range(0,len(keys)):
	f.write('<tr>\n')
	site=keys[i]
	if site=="T1_CH_CERN": continue
	if site=="T2_CH_CAF": continue
	f.write('<td>%20s</td>\n' %  site)
	f.write('<td>%s</td>\n' % sites[site]["upT1"])
	f.write('<td>%s</td>\n' % sites[site]["downT1"])
	f.write('<td>%s</td>\n' % sites[site]["upT2"])
	f.write('<td>%s</td>\n' % sites[site]["downT2"])
	f.write('</tr>\n')

f.write('</table>\n')

f.write('<p>\n')
f.write('This page is made by an acrontab on lxplus.cern.ch which executes the script\n')
f.write('<pre>/afs/cern.ch/user/s/samcms/COMP/SITECOMM/SSBScripts/EnabledLinkForSiteMonitor.sh</pre>\n')
f.write('Direct link to the python script in CVS that writes this HTML page \n')
f.write('and the metric page for the Site Status Board \n')
f.write('is <a href="http://cmssw.cvs.cern.ch/cgi-bin/cmssw.cgi/COMP/SITECOMM/SSBScripts/EnabledLinksForSiteMonitor.py">here</a> .\n')
f.write('<p>\n')

f.write('</body>\n')
f.write('</html>\n')
f.close()



f=file(metricPage,'w')
f.write('# status of enabled PhEDEx links in Production for each site\n')
f.write('# this file is a fragment of the information in the full page\n')
f.write('# indicated in the link field at right\n')
f.write('# refer to that page for additional info \n')
f.write('#\n')
for i in range(0,len(keys)):
	site=keys[i]
	if site=="T1_CH_CERN": continue
	if site=="T2_CH_CAF": continue
	status=siteStatus[site]
	color="white"
	link="http://cmsdoc.cern.ch/cms/LCG/SiteComm/EnabledLinksStatus.html"
	f.write('%s\t%s\t%s\t%s\t%s\t%s\n' % (timestamp, site, status, color, link,status))
	
f.close()
