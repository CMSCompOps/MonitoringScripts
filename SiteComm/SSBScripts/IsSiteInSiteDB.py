#!/usr/bin/python

""" @author: Josep Flix (jflix@pic.es) """

import sys, xml.dom.minidom, os, datetime, time, pprint
from xml import xpath

today=datetime.datetime.utcnow()
todaystamp=today.strftime("%Y-%m-%d")
todaystampfile=today.strftime("%Y-%m-%d %H:%M:%S")
todaystampfileSSB=today.strftime("%Y-%m-%d 00:00:01")
todaystamptofile=today.strftime("%Y%m%d_%H")
todaystamptotxt=today.strftime("%Y%m%d %H")

reptime="# - Report made on %s (UTC)\n" % todaystampfile


path_out = '/var/www/html/cms/SitesInSiteDB/'
SiteDB_url="https://cmsweb.cern.ch/sitedb/reports/showXMLReport?reportid=naming_convention.ini"
SiteDB_sites=[]
fileSiteDB="/tmp/sitedb.txt"

print "Getting the url %s" % SiteDB_url
os.system("curl -k -H 'Accept: text/xml'  '%s' > %s" % (SiteDB_url,fileSiteDB))
	
f=file(fileSiteDB,'r')
t= xml.dom.minidom.parse(f)
f.close()

for urls in xpath.Evaluate('/report/result/item', t):

	info={}
	for target in xpath.Evaluate("cms", urls):
      		if target.hasChildNodes():
		      	s=target.firstChild.nodeValue.encode('ascii')
	       	else:
	      		s=""

		if s not in SiteDB_sites:
			SiteDB_sites.append(s)

#pprint.pprint(SiteDB_sites)

ssbout="%sIsSiteInSiteDB_SSBfeed.txt" % path_out

f=file(ssbout,'w')
f.write('# Is Site in SiteDB?\n')
f.write('# Information taken daily from SiteDB: https://cmsweb.cern.ch/sitedb/reports/showXMLReport?reportid=naming_convention.ini\n')
f.write('#\n')
f.write(reptime)
f.write('#\n')

SiteDB_sites.sort()

for i in SiteDB_sites:
	site=i
	status="true"
	color="green"
	link = SiteDB_url
	f.write('%s\t%s\t%s\t%s\t%s\n' % (todaystampfileSSB, site, status, color, link))

f.close()
						
sys.exit(0)
