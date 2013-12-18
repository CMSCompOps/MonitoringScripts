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
OUTPUTJSON="SSB_alarms2.json"
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

first = True
#for each site
for site in sites:
    print '=========================================================================================='
    print site
    #don't do this when the site contains "_Long", we don't want info for that
    if site.endswith("_Long"):
        print "been here, will skip: site", site
        continue
    # First 2 letters of the site (T1, T2 or T3)
    siteTier = site[:2]
    # fetching the pledge numbers
    pledge = int(db_ExtractStatusEntry.getSiteStatusEntry(site, dateTime, pledgejson))
    print "pledge:", pledge  
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
    tmp_csv_merg = [run+','+pen for run,pen in zip(tmp_csv_run.splitlines(),tmp_csv_pen.splitlines())]
    print 'merged the csv to one csv'
    nb_Run_Clean=-1
    nb_Run_Log=-1
    nb_Run_Merge=-1
    nb_Run_RelVal=-1
    nb_Run_Proc=-1
    nb_Run_Prod=-1
    nb_Pen_Clean=-1
    nb_Pen_Log=-1
    nb_Pen_Merge=-1
    nb_Pen_RelVal=-1
    nb_Pen_Proc=-1
    nb_Pen_Prod=-1
    #read each line
    #tmp_all a new list of results
    tmp_all = []
    for line in tmp_csv_merg:
        args = line.split(',')
        #print line
        jobtype = args[2]
        if jobtype == 'Clean':
            nb_Run_Clean = int(args[0])
            nb_Pen_Clean = int(args[3])
        if jobtype == 'Log':
            nb_Run_Log = int(args[0])
            nb_Pen_Log = int(args[3])
        if jobtype == 'Merge':
            nb_Run_Merge = int(args[0])
            nb_Pen_Merge = int(args[3])
        if jobtype == 'RelVal':
            nb_Run_RelVal = int(args[0])
            nb_Pen_RelVal = int(args[3])
        if jobtype == 'Proc':
            nb_Run_Proc = int(args[0])
            nb_Pen_Proc = int(args[3])
        if jobtype == 'Prod':
            nb_Run_Prod = int(args[0])
            nb_Pen_Prod = int(args[3])
            #this is also the last of the 5 variables that I have to read, so we write away our set and reset all the others
            nb_SUMRun = nb_Run_Clean + nb_Run_Log + nb_Run_Merge  + nb_Run_RelVal + nb_Run_Proc +nb_Run_Prod
            nb_SUMPen = nb_Pen_Clean + nb_Pen_Log + nb_Pen_Merge + nb_Pen_RelVal + nb_Pen_Proc + nb_Pen_Prod
            #get time and transform format
            timePoint=datetime.strptime(args[1],"%d-%b-%y %H:%M:%S")
            timePointS=timePoint.strftime("%Y-%m-%dT%H:%M:%S")

            # fetching the status number per time_point
            status= db_ExtractStatusEntry.getSiteStatusEntry( site, timePointS ,statusjson )

            Ratio = float(nb_SUMRun)/pledge_SafeDivision
            PerfectRatio=1
            SeventyRatio=0.7
            #we check if site is tier 1, or is on
            Condition= (siteTier=="T1") or (status=="on")
            GL_AL=Condition and (nb_SUMPen>=10) and (nb_SUMRun==0)
            GL_UNDEF= not Condition
            GL_OK=(GL_AL==False) or (GL_UNDEF==False)
            #warning if condition, and ratio between alarm and warning threshold
            A_WARN=Condition and (thresh_alarm =< Ratio < thresh_warning) and (nb_SUMPen>10)
            #Alarm if condition and ratio less than alarm threshold
            A_AL=Condition and (Ratio<thresh_alarm) and (nb_SUMPen>10)
            #Alarm is undef if not condition            
            A_UNDEF=(not Condition)
            #Alarm is ok if not warning, not alarm  and not undefined
            A_OK=(not A_AL) and (not A_WARN) and (not A_UNDEF)
            SPEC_Cond=Condition and (nb_SUMPen>=10)
            if SPEC_Cond:
                SPEC_SUMRun=nb_SUMRun
            else:
                SPEC_SUMRun=0
            if SPEC_Cond:
                SPEC_Pledge=pledge_SafeDivision
            else:
                SPEC_Pledge=0

             #format of data.dat: dateTime State SUMRun SUMPen Pledge Ratio 1.0 0.7 ALARM_OK ALARM_WARNING ALARM_ALARM ALARM_UNDEFINED GLIDEIN_OK GLIDEIN_ALARM GLIDEIN_UNDEF SPEC_SUMRun SPEC_Pledge SPEC_CondCanBeRemoved
             #store int tmp_all
            timePointS=timePoint.strftime("%d-%b-%yT%H:%M:%S")
            tmp_all.append (timePointS + ' ' + str(status) + ' ' + str(nb_SUMRun) + ' ' + str(nb_SUMPen) +
                    ' ' + str(pledge_SafeDivision) + ' ' + str(Ratio) + ' ' + str(PerfectRatio) + 
                    ' ' + str(SeventyRatio) +
                    ' ' + str(A_OK)+ ' ' + str(A_WARN) +' '+ str(A_AL)+ ' ' +str(A_UNDEF)+ 
                    ' ' +str(GL_OK)+ ' ' + str(GL_AL)+ ' ' +str(GL_UNDEF)+ 
                    ' ' +str(SPEC_SUMRun)+ ' ' +str(SPEC_Pledge) +
                    ' ' + str(SPEC_Cond))
            nb_Run_Clean=-1
            nb_Run_Log=-1
            nb_Run_Merge=-1
            nb_Run_RelVal=-1
            nb_Run_Proc=-1
            nb_Run_Prod=-1
            nb_Pen_Clean=-1
            nb_Pen_Log=-1
            nb_Pen_Merge=-1
            nb_Pen_RelVal=-1
            nb_Pen_Proc=-1
            nb_Pen_Prod=-1
    # Looping over the 4 alarms: instant, 1h, 8h, 24h
    index=0
    GlideInAlarm = ['' for i in range(4)]
    NEW_ALARM = ['' for i in range(4)]
    #four alarms    
    for nb_entries in [1, 4, 32, 96]:
        #get last nb_entrues in tmp_all
        part_dat = tmp_all[-nb_entries:]
        
        #GLIDE IN
        #count everything
        GlideIn_UNDEF = 0
        GlideIn_OK = 0
        GlideIn_ALARM = 1
        
        nom = 0
        denom = 0
        sum_ = 0
        for line in part_dat:
            if nb_entries == 1:            
                print line
            parts = line.split()
            #glidein    
            GlideIn_UNDEF += (1 if parts[14] == 'True' else 0)
            GlideIn_OK += (1 if parts[12] == 'True' else 0)
            GlideIn_ALARM *= (1 if parts[13] == 'True' else 0)
            #count ratio
            #print 'parts',parts[15],parts[16]
                
            nom +=  int(parts[15])
            denom += int(parts[16])
            #
            sum_ += int(parts[3])
            res = parts[1]
            #needed for json
            if nb_entries == 1:
                #Timetmp=parts[0]+'T'+parts[1]
                Timetmp=parts[0]
                Ratiotmp=parts[15]
                print Timetmp
        
        #decide glide in alarm
        if GlideIn_UNDEF > 0:
            GlideInAlarm[index] = "UNDEF"
        elif  GlideIn_OK > 0:
            GlideInAlarm[index]="OK"
        elif GlideIn_ALARM == 1:
            GlideInAlarm[index]="ALARM"
        else:
            GlideInAlarm[index]="MIS_OPT"
    
        # new alarm
        #sum all SPEC_SUMRun  and sum all SPEC_Pledge
  
        #compute ratio (safe division)
        ratioTmp = float(nom) / float(denom) if denom != 0 else 0
        print nb_entries        
        print 'ratio: ',ratioTmp
        #if ratio below thresholds:
        if ratioTmp < thresh_alarm:
            NEW_ALARM[index]="ALARM"
        elif ratioTmp < thresh_warning:
            NEW_ALARM[index]="WARNING"
        else:
            NEW_ALARM[index]="OK"
        
        if sum_ <= 10:
            NEW_ALARM[index]="OK"
        # T1 or on??
        if not (res == 'on' or siteTier == 'T1'):
            NEW_ALARM[index]="UNDEF"
        
        index+=1
    
    print "GLIDE IN :"+(", ".join(GlideInAlarm))+"   "  
    print "NEW ALARM: "+(", ".join(NEW_ALARM))+"   "   
    
    if first:
        first = False
    else:
        outputJson.write(',')

    string = ''
    #writing instand data to json + 1h 24h alarms (the 1h alarm is calculated above, but it is not used below 
    string =('{"Site":"'+site+'","TimeDate":"'+Timetmp+'","Ratio":"'+Ratiotmp+
            '","InstantAlarm":"'+NEW_ALARM[0]+'","x8hAlarm":"'+NEW_ALARM[2]+
            '","x24hAlarm":"'+NEW_ALARM[3]+'","InstantGlideInAlarm":"'+GlideInAlarm[0]+
            '","x1hGlideInAlarm":"'+GlideInAlarm[1]+'","x8hGlideInAlarm":"'+GlideInAlarm[2]+
            '","x24hGlideInAlarm":"'+GlideInAlarm[3]+'"}\n')
        
    #print string
    outputJson.write(string)

outputJson.write("]}")
outputJson.close()
print "finished"
