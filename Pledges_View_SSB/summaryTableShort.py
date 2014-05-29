#!/usr/bin/env python
#
################################################################################
#
# Sara Alderweireldt
# Universiteit Antwerpen / CERN
# sara.alderweireldt@cern.ch
# 2013-02-18
#
################################################################################
#
# Extract summary table for workflow processing (WMA group)
#
################################################################################

import os
import re
import sys
import json
import decimal
from glob import glob
from types import *
from string import Template as template
from datetime import datetime,timedelta
from optparse import OptionParser
from copy import deepcopy as dupli

####################################################################################################
####################################################################################################
def fetch(link):
	name = "tmp.json"
	os.system("curl '%s' -o %s"%(link,name))
	file = open(name,'r+')
	input = file.read()
	file.close()
	os.remove(name)
	jsonout = json.loads(input,parse_float=decimal.Decimal,encoding='utf-8')
	return jsonout

def fetchtxt(link):
	if 'http' in link:
		name = 'tmp.html'
		os.system("curl '%s' -o %s"%(link,name))
	else: name = link	
	file = open(name,'r+')
	content = file.read()
	file.close()
	if 'http' in link: os.remove(name)
	return content

####################################################################################################
####################################################################################################
def fillup(mdict):
	# site name
	for k,v in mdict.iteritems():
		if not 'site' in v: v['site'] = k
		if not 'tier' in v: v['tier'] = re.search('T([0-9]{1})_',k).group(1)
	# other
	allkeys = []
	for i in mdict.keys():
		for j in mdict[i].keys():
			if not j in allkeys: allkeys += [j]
	fillkeys = {'pledge':str(-1),'status':'MISSING','running':int(-1),'pending':int(-1),'Run':int(-1),'Pen':int(-1),'Rat':float(-1),'Alarm':'MISSING','ratio':str(-1.0),'workmc':str(0.0),'workmc-split':str(0.0),'workt1':str(0.0),'proc':str(-1.0)}
	for k,v in mdict.iteritems():
		for k2 in allkeys:
			if not k2 in v: 
				if 'Alarm' in k2: v[k2] = fillkeys['Alarm']
				elif 'Run' in k2: v[k2] = fillkeys['Run']
				elif 'Pen' in k2: v[k2] = fillkeys['Pen']
				elif 'Rat' in k2: v[k2] = fillkeys['Rat']
				elif 'workt1' in k2: v[k2] = fillkeys['workt1']
				elif '-proc' in k2: v[k2] = fillkeys['proc']
				else: v[k2] = fillkeys[k2]

	return mdict

####################################################################################################
####################################################################################################
def sumup(mdict):
	# get T1 and T2 totals
	mdict["T1_TOTAL"] = {}
	mdict["T2_TOTAL"] = {}
	fields = ['PenProc', 'PenProd', 'pending', 'pledge', 'RunProc', 'RunProd', 'running', 'PenAve', 'RunAve', 'workmc', 'workmc-split', 'workt1', 'workt1-running', 'workt1-acquired', 'workt1-assignment-approved']#, '5_workt1-other'
	for f in fields:
		mdict["T1_TOTAL"][f] = sum([float(mdict[x][f]) for x in mdict if (f in mdict[x] and not 'TOTAL' in x and mdict[x]['tier']=='1')])
		mdict["T2_TOTAL"][f] = sum([float(mdict[x][f]) for x in mdict if (f in mdict[x] and not 'TOTAL' in x and mdict[x]['tier']=='2')])

	return mdict

####################################################################################################
####################################################################################################
def process_workmc(mdict,json):
	# full loop
	workdict1 = {}
	for line in json:
		for custodial in line['custodialsites']:
			# warnings
			oksites = [x for x in line['sites'] if x in mdict]
			noksites = [x for x in line['sites'] if not x in mdict]
			if len(noksites)>0: print "There are issues for: ",noksites
			# prepare container
			if not custodial in workdict1: workdict1[custodial] = [{}]
			else: workdict1[custodial] += [{}]
			# change the last in the list
			workdict1[custodial][-1]['team']     = line['team']
			workdict1[custodial][-1]['priority'] = line['priority']
			workdict1[custodial][-1]['days']     = line['realremainingcpudays']
			workdict1[custodial][-1]['sites']    = line['sites']
			workdict1[custodial][-1]['name']     = line['requestname']
			workdict1[custodial][-1]['slots']    = [float(mdict[x]['pledge']) for x in oksites]
			workdict1[custodial][-1]['perc']     = [float(mdict[x]['pledge'])/sum([float(mdict[y]['pledge']) for y in oksites]) for x in oksites]
			workdict1[custodial][-1]['daysperc'] = [float(workdict1[custodial][-1]['days'])*float(workdict1[custodial][-1]['perc'][ix]) for ix,x in enumerate(oksites)]
	
	# get work per custodial site
	workdict2 = {}
	for custodial in workdict1.keys()+['T2_only']:

		if not custodial in workdict2: workdict2[custodial] = {'sumbyteam':{}, 'sumbypriority':{}, 'sumtotal':0.0}
	# loop over custodials and workflows
	for custodial in workdict1.iterkeys():
		for workflow in workdict1[custodial]:
			# order
			t2only = False if any([("T1" in x) for x in workflow['sites']]) else True
			label  = 'T2_only' if t2only else custodial
			team   = workflow['team']
			prio   = workflow['priority']
			# prepare container
			if not team in workdict2[label]['sumbyteam']: workdict2[label]['sumbyteam'][team] = 0.0
			if not prio in workdict2[label]['sumbypriority']: workdict2[label]['sumbypriority'][prio] = 0.0
			# fill
			workdict2[label]['sumbyteam'][team]     += float(workflow['days'])
			workdict2[label]['sumbypriority'][prio] += float(workflow['days'])
		workdict2[label]['sumtotal'] = sum([round(x,3) for x in workdict2[label]['sumbyteam'].itervalues()])

	# get work per site
	workdict3 = {}
	# loop over custodials and workflows
	for custodial in workdict1.iterkeys():
		for workflow in workdict1[custodial]:
			# warnings
			oksites = [x for x in workflow['sites'] if x in mdict]
			noksites = [x for x in workflow['sites'] if not x in mdict]
			if len(noksites)>0: print "There are issues for: ",noksites
			# order
			t2only = False if any([("T1" in x) for x in workflow['sites']]) else True
			work   = dict((x,float(workflow['days'])*workflow['slots'][ix]/sum(workflow['slots'])) for ix,x in enumerate(oksites)) 
			for i in work:
				workdict3[i] = work[i] if (not i in workdict3) else (workdict3[i]+work[i])

	# update mdict
	for site in workdict2.keys():
		if not site in mdict: mdict[site] = {}
		mdict[site]['workmc'] = round(workdict2[site]['sumtotal'],3)
	for site in workdict3.keys():
		if not site in mdict: mdict[site] = {}
		mdict[site]['workmc-split'] = round(workdict3[site],4)

	return mdict

####################################################################################################
####################################################################################################
def process_workt1(mdict):
	links8=["","","",""]
	links8[0]="http://www.gridpp.rl.ac.uk/cms/reprocessingcampaigns_totals.html" # repr
	links8[1]="http://www.gridpp.rl.ac.uk/cms/reprocessingcampaigns_acquired.html" # repr
	links8[2]="http://www.gridpp.rl.ac.uk/cms/reprocessingcampaigns_assignment-approved.html" # repr
	links8[3]="http://www.gridpp.rl.ac.uk/cms/reprocessingcampaigns_running.html" # repr
	contents=[None,None,None,None]
	for fi,f in enumerate(links8):
		contents[fi] = fetchtxt(f)
	labels8=["acquired","assignment-approved","running","totals"]
	workdictt1 = {}
	# loop over work input files
	for content in contents:
		# loop over lines in file
		for iline,line in enumerate(content.split('\n')):
			names = []
			vals = []
			prevwasname=False
			# split lines of table
			for isub,subline in enumerate(line.split('</tr>')):
				# read site name
				if "colspan" in subline:
					names.append(re.findall(r"scope=\"col\">([A-Za-z0-9 ]*)</td>",subline+"</tr>")[0])
					# insert dummy if no value entry was found for site
					if prevwasname: vals.append('0.0')
					prevwasname=True
					continue
				# try to read values if site name read
				if prevwasname:
					if len(re.findall(r"</td><td> *([0-9]{1,}.[0-9]{1,})</td></tr>",subline+"</tr>"))>0: vals.append(re.findall(r"</td><td> *([0-9]{1,}.[0-9]{1,})</td></tr>",subline+"</tr>")[0])
					else: vals.append(0.0)
					# flag if value entry was found for site
					prevwasname=False

			rename = {"ASGC":"T1_TW_ASGC","CERN":"T2_CH_CERN","CNAF":"T1_IT_CNAF","KIT":"T1_DE_KIT","IN2P3":"T1_FR_CCIN2P3","PIC":"T1_ES_PIC","RAL":"T1_UK_RAL","FNAL":"T1_US_FNAL","US Tier2s":"T2_USminUSCD","UCSD":"T2_US_UCSD"}
			# loop over sites & values
			for jj,j in enumerate(names):
				for l in labels8:
					if "State: <b>%s</b>"%l in line:
						if not rename[j] in workdictt1: workdictt1[rename[j]] = {}
						workdictt1[rename[j]][l] = float(vals[jj])
		
	# update mdict
	for k,v in workdictt1.iteritems():
		if k=='unknown': continue
		if not k in mdict: mdict[k] = {}
		mdict[k]['workt1']         = v['totals']
		mdict[k]['workt1-running'] = v['running']
		mdict[k]['workt1-acquired'] = v['acquired']
		mdict[k]['workt1-assignment-approved'] = v['assignment-approved']
	#maindict[k]['5_workt1-other']   = sum([dict5[k][x] for x in dict5[k] if not (x=='running' or x=='totals')])
	#sumt1 = sum([maindict[x]['3_workmc'] for x in maindict if (("T1" in x or "T0" in x) and ("3_workmc" in maindict[x]))])

	return mdict

####################################################################################################
####################################################################################################
def main():
	parser = OptionParser()
	parser.add_option("-m","--mail",help="Printout summary mail.",default=False,action="store_true",dest="mail")

	opts,args = parser.parse_args()

	# master dict
	mdict = {}

	# pledges
	json0=fetch("http://dashb-ssb.cern.ch/dashboard/request.py/getplotdata?columnid=136&time=24&dateFrom=&dateTo=&site=&sites=all&clouds=undefined&batch=1&lastdata=1")
	dict0={}
	for k in json0['csvdata']:
		key = k['VOName']
		if not key in mdict: mdict[key] = {}
		mdict[key]['site'] = k['VOName']
		mdict[key]['pledge'] = k['Value']
		mdict[key]['tier'] = str(k['Tier'])
	mdict = fillup(mdict)

	# alarms
	json1=fetch("https://cmst1.web.cern.ch/CMST1/WFMon/SSB_alarms.json")
	for k in json1['Sites']:
		key = k['Site']
		if not key in mdict: mdict[key] = {}
		mdict[key]['x1hGlideInAlarm'] = k['x1hGlideInAlarm']
		mdict[key]['x8hAlarm'] = k['x8hAlarm']
		mdict[key]['ratio'] = str(float(k['Ratio'])/100.)
	mdict = fillup(mdict)

	# site info
	json2=fetch("https://cmst1.web.cern.ch/CMST1/WFMon/SSB_siteInfo.json")
	tags = ['Proc','Prod','Merge','Clean','Log','RelVal']
	for k in json2['Sites']:
		key = k['site']
		if not key in mdict: 
			mdict[key] = {}
			mdict = fillup(mdict)
		for tag in tags:
			mdict[key]['Run%s'%tag] = k['Run%s'%tag]
			mdict[key]['Pen%s'%tag] = k['Pen%s'%tag]
		mdict[key]['pending'] = k['Pending']
		mdict[key]['running'] = k['Running']
		mdict[key]['status']  = k['Status']
		mdict[key]['RunOther'] = round(sum([int(mdict[key]['Run%s'%x]) for x in tags if not x in ['Prod','Proc']]),1)
		mdict[key]['PenOther'] = round(sum([int(mdict[key]['Pen%s'%x]) for x in tags if not x in ['Prod','Proc']]),1)
		mdict[key]['RatProc'] = float(round(float(mdict[key]['RunProc']) / float(mdict[key]['pledge']),1)) if not mdict[key]['pledge']==-1 else float(-1)
		mdict[key]['RatProd'] = float(round(float(mdict[key]['RunProd']) / float(mdict[key]['pledge']),1)) if not float(mdict[key]['pledge'])==-1 else float(0.0)
	mdict = fillup(mdict)

	# average info
	info3=fetchtxt("/afs/cern.ch/user/c/cmst1/www/WFMon/avg24hjobs_running.txt")
	info4=fetchtxt("/afs/cern.ch/user/c/cmst1/www/WFMon/avg24hjobs_pending.txt")
	for line in [x.strip() for x in info3.split('\n')]:
		if line=='': continue
		if not re.search('T[0-9]{1}_',line): continue
		site = line.split(' ')[2]
		avgr = line.split(' ')[3]
		if not site in mdict: mdict[site] = {}
		mdict[site]['RunAve'] = int(float(avgr))
	for line in [x.strip() for x in info4.split('\n')]:
		if line=='': continue
		if not re.search('T[0-9]{1}_',line): continue
		site = line.split(' ')[2]
		avgp = line.split(' ')[3]
		if not site in mdict: mdict[site] = {}
		mdict[site]['PenAve'] = int(float(avgp))
	mdict = fillup(mdict)

	# work info (mc)
	json5=fetch("http://spinoso.web.cern.ch/spinoso/mc/data.json")
	mdict=process_workmc(mdict,json5)
	mdict=fillup(mdict)

	# success info (interactive view)
	info6=fetchtxt("/afs/cern.ch/user/c/cmst1/www/WFMon/JobSuccess_app_proc_out.txt")
	info7=fetchtxt("/afs/cern.ch/user/c/cmst1/www/WFMon/JobSuccess_grid_proc_out.txt")
	for line in [x.strip() for x in info6.split('\n')]:
		if line=='': continue
		if not re.search('T[0-9]{1}_',line): continue
		site = line.split(' ')[2]
		vala = line.split(' ')[3]
		if not site in mdict: mdict[site] = {}
		mdict[site]['app-proc'] = vala
	for line in [x.strip() for x in info7.split('\n')]:
		if line=='': continue
		if not re.search('T[0-9]{1}_',line): continue
		site = line.split(' ')[2]
		valg = line.split(' ')[3]
		if not site in mdict: mdict[site] = {}
		mdict[site]['grid-proc'] = valg

	# work info (t1)
	mdict=process_workt1(mdict)
	mdict=fillup(mdict)

	# sum info
	mdict=sumup(mdict)

	##################################################	
#	# show everything
#	first=True
#	for k,v in sorted(mdict.iteritems()):
#		if first: 
#			for i in sorted(v.iterkeys()):
#				print "%10s"%i,
#			print
#		for i in sorted(v.iterkeys()):
#			print "%10s"%v[i],
#		print
#		first=False

	# get header fields
	header = []
	for k1 in mdict.keys():
		for k2 in mdict[k1].keys():
			if not k2 in header: header += [k2]

	################################################################################
	# PRINT
	# print header
	allfieldsordered = ['pledge','pending','running','PenAve','RunAve','PenProc','RunProc','RatProc','PenProd','RunProd','RatProd','status','x1hGlideInAlarm','x8hAlarm','app-proc','grid-proc','workt1','workt1-running','workt1-acquired','workt1-assignment-approved','workmc','workmc-split'] #'1_Pending', '1_Running',
	split = [0,1,3,5,8,11,12,14,16,20]
	print "\033[0;43m",
	for fi,f in enumerate(['site']+allfieldsordered):
		if fi==0:
			print "%20s"%f,
		else:
			print "%9.8s"%f,
		if fi in split:
			print "|",
	print "\033[m"

	intfields = ['PenProc', 'PenProd', 'pending', 'pledge', 'RunProc', 'RunProd', 'running', 'PenAve', 'RunAve']
	fields2 = ['RatProc','RatProd','app-proc','grid-proc','workt1','workt1-running','workt1-acquired','workt1-assignment-approved']
	fields4 = ['workmc','workmc-split']

	# print values
	for ik,k in enumerate(\
	 sorted([x for x in mdict.keys() if (('status' in mdict[x]) and (mdict[x]['status']=='on' or (mdict[x]['status']=='drain' and not 'T2' in x)))]) \
	+sorted([x for x in mdict.keys() if (('status' in mdict[x]) and (mdict[x]['status']!='on' and not (mdict[x]['status']=='drain' and not 'T2' in x)))]) \
	+sorted([x for x in mdict.keys() if not 'status' in mdict[x]])):
		if ik%2==0:
			print "\033[0;47m",
		else:
			print "",
		print "%20s |"%k,
		for fi,f in enumerate(allfieldsordered):
			if f in mdict[k]:
				val = mdict[k][f]
				# special situations
				if (f=='app-proc' or f=='grid-proc') and val<90:
					print "%s%9.2f%s"%("\033[0;41;37m",val,("\033[m\033[47m" if ik%2==0 else "\033[m")),
				elif (f=='RatProc' or f=='RatProd') and val<0.7 and val>0.005:
					print "%s%9.2f%s"%("\033[0;41;37m",val,("\033[m\033[47m" if ik%2==0 else "\033[m")),
				# normal situations
				elif type(val) == FloatType and f in intfields:
					print "%9.f"%val,
				elif type(val) == FloatType and f in fields2 and val>=0.005:
					print "%9.2f"%val,
				elif type(val) == FloatType and f in fields4 and abs(val)>=0.00005:
					print "%9.4f"%val,
				elif type(val) == FloatType and val == 0.0:
					print "%9s"%"",
				elif type(val) == FloatType and val == -1.0:
					print "%9s"%"",
#				elif type(val) == FloatType:
#					print "%9.4f"%val,
				elif type(val) == IntType:
					print "%9d"%val,
				elif type(val) == UnicodeType:
					print "%9s"%val,
				elif type(val) == StringType:
					print "%9s"%val,
#				else:
#					print "%9s"%"",
				else:
					print "\nNot found ",val,type(val),"\n"
			else:
				print "%9s"%"",
			if fi+1 in split:
				print "|",
		print "\033[m"

################################################################################
# MAIL
	if opts.mail:
		print
		date = datetime.now().strftime("%A %d/%m")
		print "T1/T2 status -- %s"%(date)
		print
#		print "Hi,\n"
		keys = ['workt1','workmc','pledge','PenAve','RunAve','app-proc','grid-proc']
		for isite,site in enumerate(sorted(mdict.keys())):
			if site == "T1_TOTAL":
				continue
			if not ("T1" in site or "T2_TOTAL" in site):
				continue
			print site if ("T1" in site) else "\nT2_TOTAL"
			if 'app-proc' in mdict[site] and 'grid-proc' in mdict[site]:
				print "Job success rate --> %s"%("OK." if ("T1" in site and (float(mdict[site]['app-proc'])>85 and float(mdict[site]['grid-proc'])>85)) else "?"*10)
			else:
				print "Job success rate --> %s"%("?"*10)
			work = 0
			if 'workmc' in mdict[site]:
				work += float(mdict[site]['workmc'])
			if 'workmc-split' in mdict[site]:
				work += float(mdict[site]['workmc-split'])
			if 'workt1' in mdict[site]:
				work += float(mdict[site]['workt1'])
			if work > 0:
				print "Work assigned --> %s"%("Yes, %.2f days."%(work))
			else:
				print "Work assigned --> %s"%("No.")
			print "Current number of running jobs: %10.f"%(float(mdict[site]['RunProd'])+float(mdict[site]['RunProc']))
			print "Average number of running jobs: %10.f"%(mdict[site]['RunAve'] if "RunAve" in mdict[site].keys() else 0)
			print "Average number of pending jobs: %10.f"%(mdict[site]['PenAve'] if "PenAve" in mdict[site].keys() else 0)
			if "T1" in site:
				print "Pledge: %10d slots"%float(mdict[site]['pledge'])
	
#		print
#		print "Cheers,\nSara"
	
	rmlist = glob('tmp*.*')
	for i in rmlist:
		os.remove(i)

if __name__=="__main__":
	main()
