#!/usr/bin/python

import sys, time, urllib
#from lib import fileOps, url, dashboard, sites
from datetime import datetime
#try: import json
#except ImportError: import simplejson as json
#try: import xml.etree.ElementTree as ET
#except ImportError: from elementtree import ElementTree as ET

#metric = dashboard.metric()

f=open("open.txt", "r")
file_list = f.readlines()
file_list = map(lambda s: s.strip(), file_list)

g=open("read.txt", "r")
file_list_r = g.readlines()
file_list_r = map(lambda s: s.strip(), file_list_r)

opentest="/afs/cern.ch/user/e/eeren/www/aaa-textFiles/aaa-open-test.txt"
readtest="/afs/cern.ch/user/e/eeren/www/aaa-textFiles/aaa-read-test.txt"

def loop_it ( list, file_path):
	wr=open(file_path,"w")
	for i in list:
		fields=i.strip().split()
		if (fields[3] == "OK"):
			wr.write(datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
			sitename=fields[4].split("-")[0]
			leftover=fields[4].split("-")[-1]
			if (len(leftover) > 15):
				wr.write('\t')
				wr.write(sitename)
				wr.write("-")
				leftover=leftover.split("_")[0]
				wr.write(leftover)
			else:
				wr.write('\t')
				wr.write(sitename)
			wr.write('\t')
			wr.write(fields[3])
			wr.write('\t')
			wr.write('green')
			wr.write('\t')
			wr.write("http://www.pd.infn.it/~fanzago/TEST/"+fields[4]+".html")
			wr.write('\n')
		
		elif (fields[3] == "WARNING"):
			wr.write(datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
			wr.write('\t')
			sitename=fields[-1].split("-")[0]
			leftover=fields[-1].split("-")[-1]
			if (len(leftover) > 15):
				wr.write(sitename)
				wr.write("-")
				leftover=leftover.split("_")[0]
				wr.write(leftover)
			else:
				wr.write(sitename)
			wr.write('\t')
			wr.write(fields[3])
			wr.write('\t')
			wr.write('yellow')
			wr.write('\t')
			wr.write("http://www.pd.infn.it/~fanzago/TEST/"+fields[-1]+".html")
			wr.write('\n')
		elif (fields[3] == "PROBLEM"):
			wr.write(datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
			wr.write('\t')
			sitename=fields[-1].split("-")[0]
			leftover=fields[-1].split("-")[-1]
			if (len(leftover) > 15):
				wr.write(sitename)
				wr.write("-")
				leftover=leftover.split("_")[0]
				wr.write(leftover)
			else:
				wr.write(sitename)

			wr.write('\t')
			wr.write(fields[3])
			wr.write('\t')
			wr.write('red')
			wr.write('\t')
			wr.write("http://www.pd.infn.it/~fanzago/TEST/"+fields[-1]+".html")
			wr.write('\n')

     		elif (fields[3] == "FAILED"):
			wr.write(datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
			wr.write('\t')
			sitename=fields[-1].split("-")[0]
			leftover=fields[-1].split("-")[-1]
			if (len(leftover) > 15):
				wr.write(sitename)
				wr.write("-")
				leftover=leftover.split("_")[0]
				wr.write(leftover)
			else:
				wr.write(sitename)


			wr.write('\t')
			wr.write(fields[3])
			wr.write('\t')
			wr.write('orange')
			wr.write('\t')
			wr.write("http://www.pd.infn.it/~fanzago/TEST/"+fields[-1]+".html")
			wr.write('\n')



	wr.close()
	return

loop_it(file_list,opentest)
loop_it(file_list_r,readtest)
