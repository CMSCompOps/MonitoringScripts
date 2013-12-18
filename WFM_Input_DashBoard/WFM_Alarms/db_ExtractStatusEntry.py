import os,sys
from datetime import datetime
from datetime import timedelta
import time
import urllib, json as simplejson
from pprint import pprint

#Extracting the site STATUS or the site PLEDGE, both work. Will choose depending on the input json that you pass to this script
def getSiteStatusEntry(site, testtime, inputfile):
#  print "searching for:",site, testtime, "in", inputfile
  #INPUT
  #site="T1_DE_KIT" 
  #testtime="2013-01-20T17:15:57"

  #FIX python 2.4 versus 2.6 issue
  if hasattr(datetime, 'strptime'):
     #python 2.6
     strptime = datetime.strptime
  else:
     #python 2.4 equivalent
     strptime = lambda date_string, format: datetime(*(time.strptime(date_string, format)[0:6]))


  #OUTPUT: default is set to DOWN for status and 0 for pledge
  out_status="DOWN"
  if "pledge" in inputfile:
        out_status=0
  #did we find the interval? Needed to able to print error message
  out_status_found=0
  timeformat="%Y-%m-%dT%H:%M:%S"
  timeTest=strptime(testtime,timeformat)

  jsonfile = open(inputfile).read()
  output_json = simplejson.loads(jsonfile)
  ##print the list entries in the json. if only when, it prints [0] then it would print [1] if it exists
  #for i in output_json['csvdata']:
  #    print i

  #loop over all sites and also loop over multiple entries of a site, if the status changed recently. It will search for the correct time interval and it will give back the correct status
  for x in output_json['csvdata']:
      vosite=x["VOName"]
      if vosite==site:
        #print x["VOName"], x["Status"], x["Time"],x["EndTime"]
        timeBegin=strptime(x["Time"],timeformat)
        #print timeBegin
        timeEnd=strptime(x["EndTime"],timeformat)
        #print timeEnd 
        #needed for the possibility that the time that you are searching for will fall between 2 intervals.. Then you take the previous interval. Then the loop will stil check the next interval, so if it overlaps with the extended time, it will still use the correct interval if it falls into it.
        timeEndExtended=timeEnd + timedelta(minutes=10)
        #print timeEndExtended 
        if timeTest > timeBegin:
           if timeEnd > timeTest:
	      #print "interval found"   
	      out_status=x["Status"]
              out_status_found=1
           elif timeEndExtended > timeTest:
              #print "interval found inbetween intervals, fixed to prev."
	      out_status=x["Status"]
              out_status_found=1
  #if out_status_found==0:
    #print "site status/pledge not found for the following timeinterval and jsonfile:", site, testtime,inputfile


 
  return out_status


########################################

if __name__ == '__main__':
    site = sys.argv[1]
    timetotest = sys.argv[2]
    inputfile = sys.argv[3]
    #THE OUTPUT don't comment this line !!!!
    print getSiteStatusEntry(site,timetotest,inputfile)
