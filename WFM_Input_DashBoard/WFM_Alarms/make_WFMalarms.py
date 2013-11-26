#!/usr/bin/env python
import db_Initialize, db_ExtractStatusEntry, db_time_converter
import shutil, time, urllib, urllib2
from datetime import datetime, timedelta


print "Importing list of python file:",
try:
    import db_Initialize, db_ExtractStatusEntry, db_time_converter
except ImportError:
    print "Could not import some python file, please check the directory"
print"Done"

# copy list of site
print "Copying site_list_prev.txt:",
shutil.copy( "/afs/cern.ch/user/c/cmst1/scratch0/WFM_Input_DashBoard/site_list_prev.txt", "sitelist_prev_copy.txt")
print "Done"

sitelist="sitelist_prev_copy.txt"
pledgejson="tmp_pledge.json"
statusjson="tmp_status.json"


#call db_Inititalize
print 'Initializing jason file:',
print 'python db_Initialize.py',pledgejson,statusjson  #<<====Why do you want to do this?
db_Initialize.initialize(pledgejson,statusjson)
OUTPUTJSON="SSB_alarms.json"
print"Done"

#gets the curren date and time
dateTime = time.strftime("%Y-%m-%dT%H:%M:%S")

# thresholds for the alarm state of the normal alarm
thresh_alarm=0.7
thresh_warning=0.9
#for loop over sites, get site list
firstSite=1
# #sitelist goes into this loop at the end of the loop

#read site list
sites = [line.strip() for line in open(sitelist).readlines()]

#for each site
for site in sites:
    print site
    #don't do this when the site contains "_Long", we don't want info for that
    if site.endswith("_Long"):
        print "been here, will skip: site", site
        continue
    # First 2 letters of the site (T1, T2 or T3)
    siteTier = site[:2]
    # fetching the pledge numbers
    pledge = db_ExtractStatusEntry.getSiteStatusEntry(site, dateTime, pledgejson)
    pledge_SafeDivision = pledge
    if pledge_SafeDivision == 0:
        pledge_SafeDivision=1

    # fetching site information numbers of the last 24 hours 
    tmp_csv_merg="temp_site_RunAndPend.csv"
    #RUNNING
    url_filledwithsite=("http://dashb-cms-prod.cern.ch/dashboard/request.py/"         
                    "condorjobnumberscsv?sites="+site+"&sitesSort=1&"
                    "jobTypes=&start=null&end=null&timeRange=last24&"
                    "granularity=15%20Min&sortBy=3&series=All&type=r")

    print url_filledwithsite
    #get content from url_filledwithsite to tmp_cvs_run    
    tmp_csv_run= urllib2.urlopen(url_filledwithsite).read()
    print 'fetched running csv of',site, 'succesfully'

    #PENDING
    url_filledwithsite=("http://dashb-cms-prod.cern.ch/dashboard/request.py/"
                    "condorjobnumberscsv?sites="+site+"&sitesSort=1&"
                    "jobTypes=&start=null&end=null&timeRange=last24&"
                    "granularity=15%20Min&sortBy=3&series=All&type=p")
    print url_filledwithsite
    tmp_csv_pen= urllib2.urlopen(url_filledwithsite).read()
    print 'fetched pending csv of',site, 'succesfully'
    

    #MERGE the TWO list togther with paste and put a "," between the two instead of an endline symbol
    tmp_csv_merg = tmp_csv_run + '\n' + tmp_csv_pen

    nb_Run_Clean="-1"
    nb_Run_Log="-1"
    nb_Run_Merge="-1"
    nb_Run_RelVal="-1"
    nb_Run_Proc="-1"
    nb_Run_Prod="-1"
    nb_Pen_Clean="-1"
    nb_Pen_Log="-1"
    nb_Pen_Merge="-1"
    nb_Pen_RelVal="-1"
    nb_Pen_Proc="-1"
    nb_Pen_Prod="-1"
    
    for line in tmp_csv_merg.split('\n'):
        args = line.split(',')      
        jobtype = args[2]
        if jobtype == 'Clean':
            nb_Run_Clean =  args[0]
            nb_Pen_Clean = args[4]
        elif jobtype == 'Log':
            nb_Run_Clean =  args[0]
            nb_Pen_Clean = args[4]
        elif jobtype == 'Merge':
            nb_Run_Clean =  args[0]
            nb_Pen_Clean = args[4]
        elif jobtype == 'RelVal':
            nb_Run_Clean =  args[0]
            nb_Pen_Clean = args[4]
        elif jobtype == 'Proc':
            nb_Run_Clean =  args[0]
            nb_Pen_Clean = args[4]
        elif jobtype == 'Prod':
            nb_Run_Clean =  args[0]
            nb_Pen_Clean = args[4]

