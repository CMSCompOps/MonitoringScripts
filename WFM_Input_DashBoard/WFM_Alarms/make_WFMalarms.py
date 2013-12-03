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
db_Initialize.initialize(pledgejson,statusjson)
OUTPUTJSON="SSB_alarms.json"
outputJson = open(OUTPUTJSON,'w')


print"Done"

#gets the curren date and time
dateTime = time.strftime("%Y-%m-%dT%H:%M:%S")
dateTimeSplit = dateTime.split('T')
#write header
#echo "{\"UPDATE\":{\"Date\":\"$Date\",\"Time\":\"$Time\"},\"Sites\":[" > $OUTPUTJSON
outputJson.write('{"UPDATE":{"Date":"'+dateTimeSplit[0] +'","Time":"'+dateTimeSplit[1]+'"},"Sites":[')


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
    #tmp_csv_merg = [run+','+pen for run,pen in zip(tmp_csv_run.splitlines(),tmp_csv_run.splitlines())]
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
    #read each line
    for line in tmp_csv_merg:
        args = line.split(',')
        jobtype = args[2]
        if jobtype == 'Clean':
            nb_Run_Clean =  args[0]
            nb_Pen_Clean = args[4]
        if jobtype == 'Log':
            nb_Run_Log =  args[0]
            nb_Pen_Log = args[4]
        if jobtype == 'Merge':
            nb_Run_Merge =  args[0]
            nb_Pen_Merge = args[4]
        if jobtype == 'RelVal':
            nb_Run_RelVal =  args[0]
            nb_Pen_RelVal = args[4]
        if jobtype == 'Proc':
            nb_Run_Proc =  args[0]
            nb_Pen_Proc = args[4]
        if jobtype == 'Prod':
            nb_Run_Prod =  args[0]
            nb_Pen_Prod = args[4]
            #this is also the last of the 5 variables that I have to read, so we write away our set and reset all the others
            nb_SUMRun = nb_Run_Clean + nb_Run_Log + nb_Run_Merge  + nb_Run_RelVal + nb_Run_Proc +nb_Run_Prod
            nb_SUMPen = nb_Pen_Clean + nb_Pen_Log + nb_Pen_Merge + nb_Pen_RelVal + nb_Pen_Proc + nb_Pen_Prod
            #get time and transform format
            timePoint=strptime(args[1],"%d-%b-%y %H:%M:%S")
            timePoint=timeTest.strftime("%Y-%m-%dT%H:%M:%S")

            # fetching the status number per time_point
            status= db_ExtractStatusEntry.getSiteStatusEntry( site, timePoint ,statusjson )

            Ratio = float(SUMRun)/pledge_SafeDivision
            PerfectRatio=1
            SeventyRatio=0.7
            Condition= (siteTier=="T1") or (status=="on")
            GL_AL=Condition and (SUMPen>=10) and (SUMRun==0)
            GL_UNDEF= not Condition
            GL_OK=(GL_AL==False) or (GL_UNDEF==False)
            A_WARN=Condition and (Ratio<th_war) and (Ratio>=th_al)&&(SUMPen>10)
            A_AL=Condition and (Ratio<th_al) and (SUMPen>10)
            A_UNDEF=(not Condition)
            A_OK=(A_AL==0) and (A_WARN==0) and (A_UNDEF==0)
            SPEC_Cond=Condition and (SUMPen>=10)
            if SPEC_Cond:
                SPEC_SUMRun=SUMRun
            else:
                SPEC_SUMRun=0
            if SPEC_Cond:
                SPEC_Pledge=pledge_SafeDivision
            else:
                SPEC_Pledge=0
            

             #format of data.dat: dateTime State SUMRun SUMPen Pledge Ratio 1.0 0.7 ALARM_OK ALARM_WARNING ALARM_ALARM ALARM_UNDEFINED GLIDEIN_OK GLIDEIN_ALARM GLIDEIN_UNDEF SPEC_SUMRun SPEC_Pledge SPEC_CondCanBeRemoved
             #store int tmp_all
            tmp_all.append (timePoint + ' ' + status + ' ' + nb_SUMRun + ' ' + nb_SUMPen +
                    ' ' + pledge_SafeDivision + ' ' + Ratio + ' ' + PerfectRatio +
                    ' ' + A_OK+ ' ' +A_WARN,A_AL+ ' ' +A_UNDEF+ ' ' +GL_OK+
                    ' ' + GL_AL+ ' ' +GL_UNDEF+ ' ' +SPEC_SUMRun+ ' ' +SPEC_Pledge +
                    ' '  +SPEC_Cond)


# Looping over the 4 alarms: instant, 1h, 8h, 24h
index=0
GlideInAlarm = {}

for nb_entries in [1, 4, 32, 96]:
    #get last nb_entrues in tmp_all
    part_dat = tmp_all[-nb_entries:]

