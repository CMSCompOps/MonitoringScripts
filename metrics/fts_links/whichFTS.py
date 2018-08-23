#!/usr/bin/python

from __future__ import division

import dateutil.parser
import getpass, socket
import traceback
import time, calendar
from optparse import OptionParser
import requests
from decimal import *
from datetime import datetime, timedelta
import sys, os
import simplejson as json
import urllib3
import pprint
import shlex

def fetch(writeFile):
  if writeFile:
      urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
      response = json.loads(json.dumps(requests.get('https://cmsweb.cern.ch/phedex/datasvc/json/prod/agentlogs?node=T*', verify=False).json()))
      with open('data.json', 'w+') as f:
         json.dump(response, f)
      f.close()
      with open('data.json') as f:
         data = json.load(f)  
      return populate(data)
  else:
      urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
      response = json.loads(json.dumps(requests.get('https://cmsweb.cern.ch/phedex/datasvc/json/prod/agentlogs?node=T*', verify=False).json()))
      return populate(response)

#with open('data.json') as f:
#  data = json.load(f)  

hosts={}

def add(node,ftsServer):
    try:
        hosts[node]=ftsServer
    except Exception:
        print(traceback.format_exc())
    except:
        return

def populate(data):
    for agent in data['phedex']['agent']:
        for log in agent['log']:
            current = log['message']['$t']
            if 'FTS3' not in current:
                continue
            else:
                splt = current.split('-nodes')
                node = splt[1].split('-')[0].strip()
                ftsServer = splt[1].split('-service')[1].split('-')[0].strip()
                add(node,ftsServer)
    return hosts

def getFTSserver(sitename):
  return whichFTS.hosts[sitename]

def countTier(sList):
    tier = {}
    tier['0'] = 0
    tier['1'] = 0
    tier['2'] = 0
    tier['3'] = 0
    for site in sList:
        if 'T0' in site:
            tier['0'] += 1
        elif 'T1' in site:
            tier['1'] += 1
        elif 'T2' in site:
            tier['2'] += 1
        else:
            tier['3'] += 1
    return tier

def writefile(param='list',file=sys.stdout):
  now = time.strftime("%Y-%b-%d %H:%M:%S UTC", time.gmtime())
  file.write(("#\n# List of FTS servers curr"
    "ently being used by CMS PhEDEx endpoints. \n# @author macostaf \n# Written at %s by %s\n#" +
    " in account %s on node %s\n# " +
    " Maintained by cms-comp-ops-site-support-team@NOSPAMPLEASE.cern.ch\n"+
    "# ===========================================\n\n") %
    (now, sys.argv[0], getpass.getuser(), socket.gethostname()))
  if 'server' in param:
      fnal = []
      cern = []
      ral = []
      for k in sorted(hosts.iterkeys()):
          if 'fnal.gov' in hosts[k]:
              fnal.append(k)
              continue
          elif 'cern.ch' in hosts[k]:
              cern.append(k)
              continue
          else:
              ral.append(k)
      #Process FNAL
      file.write("# ==== FNAL FTS ==== #"+
                 "\n T0s: "+ str(countTier(fnal)['0'])+
                 "\n T1s: "+ str(countTier(fnal)['1'])+
                 "\n T2s: "+ str(countTier(fnal)['2'])+
                 "\n T3s: "+ str(countTier(fnal)['3'])+
                 "\n Total: "+ str(len(fnal))+'\n\n')
      for site in fnal:
          file.write("%s\n" % site)
      file.write("\n")

      file.write("# ==== CERN FTS ==== #"+
                 "\n T0s: "+ str(countTier(cern)['0'])+
                 "\n T1s: "+ str(countTier(cern)['1'])+
                 "\n T2s: "+ str(countTier(cern)['2'])+
                 "\n T3s: "+ str(countTier(cern)['3'])+
                 "\n Total: "+ str(len(cern))+'\n\n')
      for site in cern:
          file.write("%s\n" % site)
      file.write("\n")

      file.write("# ==== RAL FTS ==== #"+
                 "\n T0s: "+ str(countTier(ral)['0'])+
                 "\n T1s: "+ str(countTier(ral)['1'])+
                 "\n T2s: "+ str(countTier(ral)['2'])+
                 "\n T3s: "+ str(countTier(ral)['3'])+
                 "\n Total: "+ str(len(ral))+'\n\n')
      for site in ral:
          file.write("%s\n" % site)
      file.write("\n")



  elif 'list' in param:
      for k in sorted(hosts.iterkeys()):
          file.write("%s\t%s\n" % (k,hosts[k]))

def whichFTS(sitename):
    populate()
    return hosts(sitename)

#fetch(True)
fetch(False)
#writefile('server')
writefile()



