#!/usr/bin/env python

# script that fills the WM database. It is called every 15 min and the database itself is 1time created with create_WMdatabase.db
# script calls a bash function to write the database because only sqlite 1.1.7 is available in python ( <--> sqlite3 in bash )

import sys,os
import subprocess
from datetime import datetime

collectors = ['vocms97.cern.ch', 'vocms165.cern.ch', 'cmssrv119.fnal.gov']
#collectors = ['vocms97.cern.ch', 'vocms165.cern.ch']

# Filling the dictionaries
def increaseCounterInDict(dict,key,type):
    if key in dict.keys():
        dict[key][type] += 1
    else :
        tmp = {
        'Processing': 0,
        'Production': 0,
        'Merge': 0,
        'Cleanup': 0,
        'LogCollect': 0,
        'TestJobs' : 0,
        }
        dict[key] = tmp
        dict[key][type] += 1

# Fill the sites/vobox that have no information atm, but are in the database, with 0's
def fillBrokenSites(sitelist,dict):
    f=open(sitelist,'r')
    #print dict.keys()
    for site in f:
       stripped_site=site.strip()
       if not stripped_site in dict.keys():
         tmp = {
          'Processing': 0,
          'Production': 0,
          'Merge': 0,
          'Cleanup': 0,
          'LogCollect': 0,
          'TestJobs' : 0,
         }
         dict[stripped_site] = tmp
         #print "site ", stripped_site

#Printing function for debugging
def printDict(dict,description):
    sorted = dict.keys()
    sorted.sort()
    print '------------------------------------------------------------------------------------------------------------------'
    print '| %35s | Processing | Production | Merge      | Cleanup    | LogCollect |  TestJobs   |   Total      |' % description
    print '-------------------------------------------------------------------------------------------------------------------'
    for site in sorted:
        print '| %35s | %10d | %10d | %10d | %10d | %10d | %10d | %10d |' % (site,dict[site]['Processing'],dict[site]['Production'],dict[site]['Merge'],dict[site]['Cleanup'],dict[site]['LogCollect'],dict[site]['TestJobs'],dict[site]['Processing']+dict[site]['Production']+dict[site]['Merge']+dict[site]['Cleanup']+dict[site]['LogCollect']+dict[site]['TestJobs'])
    print '----------------------------------------------------------------------------------------------------'

#Writing json file
def jsonDict(dict_run,dict_pen,json_name,date,hour,location):
    sorted_run = dict_run.keys()
    sorted_run.sort()
    #remove empty list entry
    while '' in sorted_run:
        sorted_run.remove('')
    print sorted_run
    json_part= '{\"UPDATE\":{\"Date\":\"'+date+'\",\"Time\":\"'+hour+'\"},\"'+location+'\":['
    writecommand="wget -O collectorUptime.txt -q  https://cmst1.web.cern.ch/CMST1/wmaconfig/AgentStatus.txt;"
    proc = subprocess.Popen(writecommand, stderr = subprocess.PIPE,stdout = subprocess.PIPE, shell = True)
    out, err = proc.communicate()
    print out
    print err

    #site is here a voBox
    first=True
    for site in sorted_run:
	#get voBox status out of collectorUptime.txt
        writecommand="bash get_voBoxStatus.sh collectorUptime.txt "+site
	proc = subprocess.Popen(writecommand, stderr = subprocess.PIPE,stdout = subprocess.PIPE, shell = True)
        out, err = proc.communicate()
        print err
        #remove the \n at the end of the line
        out=out.strip()
        #split the string and put it in a list
        output_list=out.split(" ")
        s_status=output_list[1]

        if first:
           startingComma=""
	   first=False
        else:
           startingComma=","
        json_site_part= startingComma+"{\"VOBox\":\""+str(site)+"\""      \
              +",\"Pending\":\""+str(dict_pen[site]['Processing']+dict_pen[site]['Production']+dict_pen[site]['Merge']+dict_pen[site]['Cleanup']+dict_pen[site]['LogCollect']+dict_run[site]['TestJobs'])+"\""        \
              +",\"TimeDate\":\""+str(currTime.strip())+"\"" \
              +",\"Running\":\""+str(dict_run[site]['Processing']+dict_run[site]['Production']+dict_run[site]['Merge']+dict_run[site]['Cleanup']+dict_run[site]['LogCollect']+dict_pen[site]['TestJobs'])+"\""        \
              +",\"Status\":\""+str(s_status)+"\""   \
              +",\"RunProc\":\""+str(dict_run[site]['Processing'])+"\""      \
              +",\"RunProd\":\""+str(dict_run[site]['Production'])+"\""      \
              +",\"RunMerge\":\""+str(dict_run[site]['Merge'])+"\""  \
              +",\"RunClean\":\""+str(dict_run[site]['Cleanup'])+"\""        \
              +",\"RunLog\":\""+str(dict_run[site]['LogCollect'])+"\""       \
              +",\"RunTestJobs\":\""+str(dict_run[site]['TestJobs'])+"\""       \
              +",\"PenProc\":\""+str(dict_pen[site]['Processing'])+"\""      \
              +",\"PenProd\":\""+str(dict_pen[site]['Production'])+"\""      \
              +",\"PenMerge\":\""+str(dict_pen[site]['Merge'])+"\""  \
              +",\"PenClean\":\""+str(dict_pen[site]['Cleanup'])+"\""        \
              +",\"PenLog\":\""+str(dict_pen[site]['LogCollect'])+"\""       \
              +",\"PenTestJobs\":\""+str(dict_pen[site]['TestJobs'])+"\""       \
              +"}"
        json_site_part_str=str(json_site_part).replace("('","").replace("')","")
        print json_site_part_str
        json_part += json_site_part_str
        #json_part += str(tuple(json_site_part))
#{"Site":"T1_DE_KIT","Pending":"0","TimeDate":"2012-12-04h11:01:01","Running":"19","Pledge":"1200","Status":"on","Ratio":"0.0158333","InstantAlarm":"OK","x1hAlarm":"OK","x24hAlarm":"ALARM","InstantGlideInAlarm":"OK","x1hGlideInAlarm":"OK","x24hGlideInAlarm":"OK","RunProc":"15","RunProd":"0","RunMerge":"3","RunClean":"0","RunLog":"1","PenProc":"0","PenProd":"0","PenMerge":"0","PenClean":"0","PenLog":"0"},
# sentence.replace(" ", "")
    print '----------------------------------------------------------------------------------------------------'
    os.remove("collectorUptime.txt")
    json_part+= ']}'
    json_part.replace(" ", "")
    print json_part
    #overwrite file
    json_file=open(json_name,"w")
    json_file.write(json_part)

#################################################################

#Timing the script
starttime=datetime.now()

jsonCERN_name="SSBCERN_voBoxInfo.json"

#Start of the program: Creating 3 empty dictionaries
overview_running = {}
overview_pending = {}
#overview_other = {}

#get time
gettime="sqlite3 fakedatabase \"select datetime('now');\" "
currTime = subprocess.Popen(gettime, stdout=subprocess.PIPE, shell=True).communicate()[0]
currTime_list=currTime.split(" ")
date=currTime_list[0]
hour=currTime_list[1]
hour=hour.replace("\n"," ")
currTime=currTime.replace(' ','h')
print currTime


#Extracting the schedulars list from all collectors
#command='condor_q -format "%i." ClusterID -format "%s " ProcId -format " %i " JobStatus  -format " %d " ServerTime-EnteredCurrentStatus -format "%s" UserLog -format " %s" DESIRED_Sites -format " %s" RemoveReason -format " %i\n" NumJobStarts'
#command="""condor_q -format "%i." ClusterID -format "%s " ProcId -format " %i " JobStatus  -format " %d " ServerTime-JobStartDate -format "%s" UserLog -format " %s" DESIRED_Sites -format " %s" RemoveReason -format " %i\n" NumJobStarts | awk '{if ($2!= 1) print $0}'"""
# keep track of which schedd as keyword is attached to which col
dict_col_with_schedd={}
listschedds=[]
for col in collectors:
   listcommand="condor_status -pool "+col+" -schedd -format \"%s \n\" Name"
   print listcommand
   proc = subprocess.Popen(listcommand, stderr = subprocess.PIPE,stdout = subprocess.PIPE, shell = True)
   out, err = proc.communicate()
   # we don't have to send an email when there is an error (collector not reachable), since it is already done in the script per site
   for line in err.split('\n') :
        if 'Error' in line:
              print "Called:   "+listcommand
              print "Col: "+col+" is offline"
              break
   for line in out.split('\n') :
	if ('cern' in line) or ('fnal' in line):
		listschedds.append(line)
                dict_col_with_schedd[line]=col

print "Passed condor_status pool of all collectors."
print "Dict of dict['schedd']=col:"
print dict_col_with_schedd

#copy lists and change . to _ in the naming
#words = [w.replace('[br]', '<br />') for w in words]
listschedds_fix = [schedd.replace('.','_') for schedd in listschedds]
#print listschedds_fix

#create list of voboxes
print "listschedds"
print  listschedds_fix
print "----------------------"
print "----------------------"
#previous list:
vobox_list_prev="voboxlist_prev.txt"

vobox_list="voboxlist.txt"
file_vobox = open(vobox_list,'w')
for schedd in listschedds_fix:
  print>>file_vobox, schedd
file_vobox.close()

print "update collector list "
#Check the voBox list and add a new voBox when necessary
#Checking if there might be a new site. If so, a new table is added. voBoxes without data will be kept here, so that the fillBrokenSites() function can still fill them with 0's. 
# .sh script will copy .txt to _prev.txt
listcommand="bash update_voBoxlist.sh %s %s"% (vobox_list_prev,vobox_list)
print listcommand
proc = subprocess.Popen(listcommand, stderr = subprocess.PIPE,stdout = subprocess.PIPE, shell = True)
out, err = proc.communicate()
print out
print err
print "collector list update complete"

for schedd in listschedds:
        schedd_fix = schedd.replace('.',"_")
        schedd_fix = schedd_fix.strip(' ')
        # Issue, need to know which col + which schedd
        command='condor_q -pool '+dict_col_with_schedd[schedd]+' -name ' + schedd
       #  condor_q -pool vocms97.cern.ch  -name vocms216.cern.ch  
        command=command+"""  -format "%i." ClusterID -format "%s||" ProcId  -format "%i||" JobStatus  -format "%s||" UserLog -format "%s||" DESIRED_Sites -format "\%s||" WMAgent_SubTaskType -format "%s||" MATCH_EXP_JOBGLIDEIN_CMSSite -format "\n" Owner"""
        # array[0] ClusterID.ProcId
        # array[1] JobStatus
        # array[2] UserLog
        # array[3] DESIRED_Sites
          # only when its the new software
          # array[4] WMAgent_SubTaskType
              # only when job is already running
              # array[5] MATCH_EXP_JOBGLIDEIN_CMSSite
        # array[6] ''    --> happens always  dunno why
        # --> standard len(array) = 5
        # --> new osftware len(array ) ={5,6} depending if the job is already assigned to a site

        print command
#	command=command+""" -format "%i." ClusterID -format "%s " ProcId -format " %i " JobStatus  -format " %d " ServerTime -format " %d " JobStartDate -format " %d" EnteredCurrentStatus -format " %s" UserLog -format " %s" DESIRED_Sites -format " %s" RemoveReason -format " %i\n" NumJobStarts"""
	proc = subprocess.Popen(command, stderr = subprocess.PIPE,stdout = subprocess.PIPE, shell = True)
	out, err = proc.communicate()
	for line in out.split('\n') :
	    if line == "" : continue
	    # fix for sleep.log problem lines
            if 'sleep.log' in line: continue
            array = line.split("||")
            id = array[0]
            status = int(array[1])
            log =array[2]
            #siteToExtract = array[3]
            #print array
            #print len(array)

            # TYPE
            type = ''
            #the new software has the type as a "name", otherwise extract it from the Log line
            if len(array)>5:
              typeToExtract = array[4]
              if typeToExtract == "" :
                typeToExtract = log
            else :
              typeToExtract = log
            # now go through the group assignment
            if typeToExtract.count('Merge') > 0 :
                type = 'Merge'
            elif typeToExtract.count('Cleanup') > 0 :
                type = 'Cleanup'
            elif typeToExtract.count('LogCollect') > 0 :
                type = 'LogCollect'
            elif typeToExtract.count('Production') > 0 :
                type = 'Production'
            elif typeToExtract.count('MonteCarloFromGEN') > 0 :
                type = 'Production'
            elif typeToExtract.count('Skim') > 0 :
                type = 'Production'
#                 type = 'Skim'
            elif typeToExtract.count('Harvest') > 0 :
#                type = 'Harveset'
               type = 'Production'
            elif typeToExtract.count('Processing') > 0 :
                type = 'Processing'
            # HC/TestJobs
            elif schedd.count('vocms228') > 0 :
                type = 'TestJobs'  
            else :
                type = 'Processing'


            # SITE extraction  
            # not needed...

            # check if production jobs with JobCache, or HC/TestJobs with condor 
	    if 'JobCache' not in line and 'vocms228' not in schedd:
		continue

            # Increase/append the dictionarry
	    if status == 2:
		increaseCounterInDict(overview_running,schedd_fix,type)
	    elif status == 1:
		increaseCounterInDict(overview_pending,schedd_fix,type)
#	    else :
#		increaseCounterInDict(overview_other,schedd_fix,type)

#Adding the voboxes to the 2 dicts that are not in the overview list. At the moment they are added with 0's
fillBrokenSites(vobox_list,overview_running) 
fillBrokenSites(vobox_list,overview_pending) 

print overview_running
printDict(overview_running,'Running')
print ""
print overview_pending
printDict(overview_pending,'Pending')

#Writing the json file
jsonDict(overview_running,overview_pending,jsonCERN_name,date,hour,"CERN")

print '__________________-'
print 'THE PROGRAM IS FINISHED AFTER', datetime.now()-starttime
