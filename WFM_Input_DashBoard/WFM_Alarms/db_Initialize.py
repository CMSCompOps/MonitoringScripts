import os, sys, errno
#import urllib, json
import urllib
from datetime import datetime
from pprint import pprint

#Extract from dashboard 2 json files, 1 with the pledge and 1 with the status
def initialize(pledge_json, status_json):
  #call function (see below) to remove file, before we fetch the file
  silentremove(pledge_json)
  silentremove(status_json)

  #extract the PLEDGE json file
  #urlstr="http://dashb-ssb-dev.cern.ch/dashboard/request.py/getplotdata?columnid=10080&time=24&dateFrom=&dateTo=&site=&sites=all&clouds=undefined&batch=1&lastdata=1"
  urlstr="http://dashb-ssb.cern.ch/dashboard/request.py/getplotdata?columnid=159&time=24&dateFrom=&dateTo=&site=&sites=all&clouds=undefined&batch=1&lastdata=1"
  #print urlstr
  u = urllib.urlopen(urlstr)
  localFile = open(pledge_json, 'w')
  localFile.write(u.read())
  localFile.close()

  #extract the STATUS json file
  #urlstr2="http://dashb-ssb-dev.cern.ch/dashboard/request.py/getplotdata?columnid=10075&time=24&site=&sites=all&batch=1"
  urlstr2="http://dashb-ssb.cern.ch/dashboard/request.py/getplotdata?columnid=158&time=24&site=&sites=all&batch=1"
  #print urlstr
  u2 = urllib.urlopen(urlstr2)
  #u = urllib.urlopen("http://dashb-ssb-dev.cern.ch/dashboard/request.py/getplotdata?columnid=10075&time=48&dateFrom=&dateTo=&site=T1_DE_KIT&sites=all&clouds=undefined&batch=1")
  localFile2 = open(status_json, 'w')
  localFile2.write(u2.read())
  localFile2.close()


######################################

def silentremove(filename):
    try:
        os.remove(filename)
    except OSError, e:
        if e.errno != errno.ENOENT: # errno.ENOENT = no such file or directory
            raise # re-raise exception if a different error occured

#######################################

if __name__ == '__main__':
   pledge_json=sys.argv[1]
   status_json=sys.argv[2]
   initialize(pledge_json, status_json)
