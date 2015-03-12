#!/usr/bin/python


""" @author: Josep Flix (jflix@pic.es) """


import sys, xml.dom.minidom, os, datetime, time, pprint
from xml import xpath

today=datetime.datetime.utcnow()
todaystamp=today.strftime("%Y-%m-%d")
todaystampfile=today.strftime("%Y-%m-%d %H:%M:%S")
todaystamptofile=today.strftime("%Y%m%d_%H")
todaystamptotxt=today.strftime("%Y%m%d %H")

#GetURLs=False
GetURLs=True

path_out = '/var/www/html/cms/SiteReadinessAnalysis/' 

hours=1 # Number of hours to get info from SSB

# URLs with SSB inputs --------------------------------------------------------------------------------------

#webserver_devel="http://dashb-ssb-devel.cern.ch"
webserver="http://dashb-ssb.cern.ch"

Downtimes_sam= webserver + '/dashboard/request.py/siteviewhistory?columnid=71&time=' + str(hours) + "&fullstatus=1"
Ranking= webserver + '/dashboard/request.py/siteviewhistory?columnid=96&time=' + str(hours) + "&fullstatus=1"
CE_sam= webserver + '/dashboard/request.py/siteviewhistory?columnid=4&time=' + str(hours) + "&fullstatus=1"
SRM_sam= webserver + '/dashboard/request.py/siteviewhistory?columnid=5&time=' + str(hours) + "&fullstatus=1"

ColumnMatrix = {}  # SSB URLs Matrix
ColumnMatrix['Downtimes_sam']=Downtimes_sam
ColumnMatrix['CE_sam']=CE_sam
ColumnMatrix['SRM_sam']=SRM_sam
ColumnMatrix['Ranking']=Ranking

# -----------------------------------------------------------------------------------------------------------

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

		SiteDB_sites.append(s)

#pprint.pprint(SiteDB_sites)

########################################################
# Reading data from SSB
########################################################

sites={}

ColumnItems = ColumnMatrix.keys()
ColumnItems.sort()
ColumnItems.reverse()

for col in ColumnItems:
	
#	print col
	
	url=ColumnMatrix[col]

	fileN="/tmp/"+col

	if GetURLs == True:
		print "Getting the url %s" % url
		os.system("curl -H 'Accept: text/xml'  '%s' > %s" % (url,fileN))
	
	f=file(fileN,'r')
	t= xml.dom.minidom.parse(f)
	f.close()

	for urls in xpath.Evaluate('/siteviewhistory/data/item', t):

                info={}
		for option in ('Status', "COLOR", 'Time', 'EndTime','VOName'):
			for target in xpath.Evaluate(option, urls):
				if target.hasChildNodes():
					s=target.firstChild.nodeValue.encode('ascii')
				else:
					s=""
				info[option]=s

		if not sites.has_key(info['VOName']):
			sites[info['VOName']]={}
		if not sites[info['VOName']].has_key(col):
			sites[info['VOName']][col]={}
		sites[info['VOName']][col][info['Time']]=info


filetxt= path_out + 'UsableSites_' + todaystamptofile + ".txt"

fileHandle = open ( filetxt , 'w' )    

reptime="# Usable Sites Report made on %s (UTC)\n" % todaystampfile

fileHandle.write("#\n")
fileHandle.write(reptime)
fileHandle.write("#\n")
fileHandle.write("# Usability procedure described in: https://twiki.cern.ch/twiki/bin/view/CMS/FacOps_Tier2UsableForAnalysis\n")
fileHandle.write("#\n\n")

site = sites.keys()
site.sort()

usability={}
usable={}
not_usable={}

for sitename in site:
	
	if sitename.find("T3_") == 0 or sitename.find("T0_") == 0 or sitename.find("T1_") == 0: continue
       	if not sitename in SiteDB_sites: continue
       	if sitename.find("T2_CH_CAF") == 0 or sitename.find("T2_PT_LIP_Coimbra") == 0: continue

	useit=1

	for col in ColumnMatrix:

		if not sites[sitename].has_key(col):
			continue
		
		items = sites[sitename][col].keys()
		items.sort()
			
		lastState= ""
		lastBegin= ""
		lastEnd= ""
		for i in items:
			lastState=sites[sitename][col][i]['Status']
			lastBegin=sites[sitename][col][i]['Time']
			lastEnd=sites[sitename][col][i]['EndTime']
		if lastState != "":

			if col == "Ranking":
				if lastState == "n/a":
					useit=0
					continue
				if sitename.find("T1_") == 0 and int(lastState)<90:
					useit=0
				if sitename.find("T2_") == 0 and int(lastState)<80:
					useit=0
		      	if col == "CE_sam" and lastState != "OK":
				useit=0
	       	      	if col == "SRM_sam" and lastState != "OK":
			       	useit=0
		      	if col == "Downtimes_sam" and lastState != "":
			       	useit=0

	usability[sitename]=useit
       	if usability[sitename] == 1:		
		if not usable.has_key(sitename): usable[sitename]=1
       	else:
		if not not_usable.has_key(sitename): not_usable[sitename]=0


############################################################
		
fileHandle.write("---------- USABLE SITES FOR ANALYSIS ---------- \n\n")

siteus = usable.keys()
siteus.sort()

for sitename in siteus: fileHandle.write(sitename+"\n")

fileHandle.write("\n---------- *NOT* USABLE SITES FOR ANALYSIS ---------- \n\n")

sitenous = not_usable.keys()
sitenous.sort()

for sitename in sitenous: fileHandle.write(sitename+"\n")

############################################################

totalsites=len(usable)+len(not_usable)

fileHandle.write("\n--------- Statistics ---------- \n\n")
fileHandle.write(todaystamptotxt + " / " + str(len(usable)) + " usable sites" + " / " + str(len(not_usable)) + " not usable sites\n\n")

fileHandle.write("\n--------- Detailed Site Status ---------- \n\n")

for sitename in site:
	
	if sitename.find("T3_") == 0 or sitename.find("T0_") == 0 or sitename.find("T1_") == 0: continue
       	if not sitename in SiteDB_sites:
#     		fileHandle.write("Site is not on SiteDB\n\n")
		continue
       	if sitename.find("T2_CH_CAF") == 0 or sitename.find("T2_PT_LIP_Coimbra") == 0:
#		fileHandle.write("Site shall be skipped\n\n")
		continue
	
	for col in ColumnMatrix:

		if not sites[sitename].has_key(col):
			continue
		
		items = sites[sitename][col].keys()
		items.sort()
			
		lastState= ""
		lastBegin= ""
		lastEnd= ""
		for i in items:
			lastState=sites[sitename][col][i]['Status']
			lastBegin=sites[sitename][col][i]['Time']
			lastEnd=sites[sitename][col][i]['EndTime']
		if lastState != "":
			if col == "Ranking":
				mes = sitename + "," + col + " : " + lastState + "%\n" 
			else:
				mes = sitename + "," + col + " : " + lastState + "\n" 
		       	fileHandle.write(mes)
       	if usability[sitename] == 1:		
		fileHandle.write(sitename + " is usable\n\n")
       	else:
		fileHandle.write(sitename + " is *not* usable\n\n")

#pprint.pprint(usable)
#pprint.pprint(not_usable)

fileHandle.close()

sys.exit(0)
