import os, sys, errno
#import urllib, json
import urllib, simplejson
from datetime import datetime
from datetime import timedelta
import time
from pprint import pprint

#Extract from dashboard 2 json files with the 24h average value, 1 for sites and 1 for voboxes 
def initialize(sites_json, voboxes_json):
  #call function (see below) to remove file, before we fetch the file
  silentremove(sites_json)
  silentremove(voboxes_json)

  print "Retrieving the jsons"
  #extract the sites json file
  urlstr="http://dashb-cms-prod.cern.ch/dashboard/request.py/condorlastdayavg?type=sites"
  #print urlstr
  u = urllib.urlopen(urlstr)
  localFile = open(sites_json, 'w')
  localFile.write(u.read())
  localFile.close()

  #extract the voboxes json file
  urlstr2="http://dashb-cms-prod.cern.ch/dashboard/request.py/condorlastdayavg?type=servers"
  #print urlstr
  u2 = urllib.urlopen(urlstr2)
  localFile = open(voboxes_json, 'w')
  localFile.write(u2.read())
  localFile.close()

#____________________________________________________________________________________________
# sometimes multiple sites are listed in k['S_SITE']; this function divides the #pen and #run over these 3 sites in the same json. 
# the list 
def resum(jsonfile):
  for k in jsonfile['stats']:
     if "," in k['S_SITE']:
         numberofsites=k['S_SITE'].count(',')+1  #count comma's so do +1 for #sites
         print '#sites: ', numberofsites, ' :  ',  k['S_SITE'], ' : dividing number: ', str(k['SUM_NRUN']), str(k['SUM_NPEND'])
         pend_split=k['SUM_NPEND']/3 
         run_split=k['SUM_NRUN']/3
         for site in k['S_SITE'].split(','):
            site=site.strip()
            for reloop_k in jsonfile['stats']:
              if "," in reloop_k['S_SITE']: continue
              if site == reloop_k['S_SITE']:
                  print 'old:  ',reloop_k['S_SITE'],reloop_k['SUM_NPEND'],reloop_k['SUM_NRUN']
                  reloop_k['SUM_NPEND']+=pend_split
                  reloop_k['SUM_NRUN']+=run_split
                  print 'new:  ',reloop_k['S_SITE'],reloop_k['SUM_NPEND'],reloop_k['SUM_NRUN']

#____________________________________________________________________________________________

def generateoutputfiles(sites_json,voboxes_json,running_out_txt,pending_out_txt):
  #'now' in time format
  now=(datetime.utcnow()).strftime("%Y-%m-%d %H:%M:%S")
  print "Local current time :", now

  print "Loading the jsons"
  #get jsons
  file_sites=open(sites_json,'r+')
  input_sites=file_sites.read()
  file_sites.close()
  file_voboxes=open(voboxes_json,'r+')
  input_voboxes=file_voboxes.read()
  file_voboxes.close()
 
  json_sites=simplejson.loads(input_sites,)
  json_voboxes=simplejson.loads(input_voboxes)

  print "resumming json when there are multiple sites in S_SITE"
  resum(json_sites)
  resum(json_voboxes)
  #NOTE: the list elements with multiple sites are still in the list we just ignore the entry now, since the corresponding sites are
  #already resummed

  print "Writing txt files for SSB"
  #open text files
  f1=open('./'+running_out_txt, 'w+')
  f2=open('./'+pending_out_txt, 'w+')
  f1.write('# Average of the number of running jobs of the last 24 hours\n')
  f1.write('# https://cmst1.web.cern.ch/CMST1/WFMon/avg24hjobs_running.txt\n')
  f2.write('# Average of the number of pending jobs of the last 24 hours\n')
  f2.write('# https://cmst1.web.cern.ch/CMST1/WFMon/avg24hjobs_pending.txt\n')
  print json_sites
  #filling the text files
  for k in json_sites['stats']+json_voboxes['stats']:
     if ',' in k['S_SITE']: continue
     #print k['S_SITE'],str(k['SUM_NRUN']),str(k['SUM_NPEND'])
     f1.write(now+' '+k['S_SITE']+' '+str(trunc(k['SUM_NRUN'],0))+' green http://cmst1.web.cern.ch/CMST1/WFMon/avg24hjobs_running.txt \n')
     f2.write(now+' '+k['S_SITE']+' '+str(trunc(k['SUM_NPEND'],0))+' green http://cmst1.web.cern.ch/CMST1/WFMon/avg24hjobs_pending.txt\n')
     
  f1.close()
  f2.close()
  print "Program finished"

######################################

def silentremove(filename):
    try:
        os.remove(filename)
    except OSError, e:
        if e.errno != errno.ENOENT: # errno.ENOENT = no such file or directory
            raise # re-raise exception if a different error occured

######################################

def trunc(f, n):
     '''Truncates/pads a float f to n decimal places without rounding'''
     return ('%.*f' % (n + 1, f))[:-1]

#######################################

if __name__ == '__main__':
   running_out_txt=sys.argv[1]
   pending_out_txt=sys.argv[2]
   sites_json="sites_24hAvg.json"
   voboxes_json="voboxes_24hAvg.json"
   initialize(sites_json,voboxes_json)
   generateoutputfiles(sites_json,voboxes_json,running_out_txt,pending_out_txt)
