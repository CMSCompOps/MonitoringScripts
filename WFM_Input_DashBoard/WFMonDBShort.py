#!/usr/bin/env python

# script that files the WM database. It is called every 15 min and creates a json file
import sys,os
import subprocess
import tempfile
from datetime import datetime

#collectors = ['vocms97.cern.ch', 'vocms165.cern.ch', 'cmssrv119.fnal.gov']
collectors = ['vocms97.cern.ch', 'vocms165.cern.ch']

#____________________________________________________________________________________________________

#def weighted random 
import random
def weighted_pick(dic):
     total = sum(dic.itervalues())
     pick = random.randint(0, total-1)
     tmp = 0
     for key, weight in dic.iteritems():
         tmp += weight
         if pick < tmp:
             return key

#____________________________________________________________________________________________________

# Extract json with keyword Site, with pledge , Pledge is 0 when status is drain, skip, down, ..;
def getSitePledgeList(filename):
  crs = open(filename, "r")
  list={}
  for columns in ( raw.strip().split() for raw in crs ):  
    if len(columns) ==3:  # has word drain skip down, ... skip it
       list[columns[0]]=0
    else: 
       if columns[1].isdigit():
         list[columns[0]]=int(columns[1])
       else :
         print "The following site has no pledge !!! Ask Edgar for a fix in the file: http://cmst1.web.cern.ch/CMST1/wmaconfig/slot-limits.conf;"
         print columns
         list[columns[0]]=1

    #print ': ', columns
  crs.close()
  return list

#____________________________________________________________________________________________________

# Filling the dictionaries
def increaseCounterInDict(dict,site,type):
    if site in dict.keys():
        dict[site][type] += 1
    else :
        tmp = {
        'Processing': 0,
        'Production': 0,
        'Merge': 0,
        'Cleanup': 0,
        'LogCollect': 0,
        'RelVal': 0,
        }
        dict[site] = tmp
        dict[site][type] += 1

#____________________________________________________________________________________________________

# Fill the sites that have no information atm, but are in the database, with 0's
def fillBrokenSites(sitelist,dict):
    f = open(sitelist,'r')
    #print dict.keys()
    for site in f:
       stripped_site = site.strip()
       if not stripped_site in dict.keys():
         tmp = {
          'Processing': 0,
          'Production': 0,
          'Merge': 0,
          'Cleanup': 0,
          'LogCollect': 0,
          'RelVal': 0,
         }
         dict[stripped_site] = tmp
         #print "site ", stripped_site

#____________________________________________________________________________________________________

# Removing all sites that have *_XYZ and add them to *
def removePostFixSites(dict,postFix):
   for key_site,value in dict.items():
        if postFix in key_site:
            print key_site,value
            key_site_NoPostFix = key_site.replace(postFix,'')
            #print key_site_NoPostFix
            #print dict[key_site_NoPostFix]
            if key_site_NoPostFix in dict.keys():
                     print key_site_NoPostFix, dict[key_site_NoPostFix]
                     # sum the two dict items: key_site and key_site_NoPostFix
                     dict[key_site_NoPostFix]['Processing'] += dict[key_site]['Processing']
                     dict[key_site_NoPostFix]['Production'] += dict[key_site]['Production']
                     dict[key_site_NoPostFix]['Merge'] += dict[key_site]['Merge']
                     dict[key_site_NoPostFix]['Cleanup'] += dict[key_site]['Cleanup']
                     dict[key_site_NoPostFix]['LogCollect'] += dict[key_site]['LogCollect']
                     dict[key_site_NoPostFix]['RelVal'] += dict[key_site]['RelVal']
                     #delete the "_Long" entry
                     del dict[key_site]
            else:
                     dict[key_site_NoPostFix] = dict[key_site]
                     del dict[key_site]

            #Results in:
            print 'There should be no lines / sites listed between this line and the word END'
            for key_site,value in dict.items():
              if postFix in key_site:
                print key_site,value
            print 'End'

#____________________________________________________________________________________________________

#Printing function for debugging
def printDict(dict,description):
    sorted = dict.keys()
    sorted.sort()
    print '------------------------------------------------------------------------------------------------------------------'
    print '| %20s | Processing | Production | Merge      | Cleanup    | LogCollect | RelVal     | Total      |' % description
    print '------------------------------------------------------------------------------------------------------------------'
    for site in sorted:
        print '| %20s | %10d | %10d | %10d | %10d | %10d | %10d | %10d |' % (site,dict[site]['Processing'],dict[site]['Production'],dict[site]['Merge'],dict[site]['Cleanup'],dict[site]['LogCollect'],dict[site]['RelVal'],dict[site]['Processing']+dict[site]['Production']+dict[site]['Merge']+dict[site]['Cleanup']+dict[site]['LogCollect']+dict[site]['RelVal'])
    print '------------------------------------------------------------------------------------------------------------------'

#____________________________________________________________________________________________________

#Writing json file
def jsonDict(dict_run,dict_pen,json_name,date,hour):
    print 'run '+str(len(dict_run))
    print 'pen '+str(len(dict_pen))

    sorted_run = dict_run.keys()
    sorted_run.sort()
    #remove empty list entry
    while '' in sorted_run:
	sorted_run.remove('')
    print sorted_run
    json_part= '{\"UPDATE\":{\"Date\":\"'+date+'\",\"Time\":\"'+hour+'\"},\"Sites\":['
   
    first=True
    for site in sorted_run:
	#get site status and pledge
  	writecommand="bash get_SiteStatus.sh %s %s" % (site_slot_status,site)
	proc = subprocess.Popen(writecommand, stderr = subprocess.PIPE,stdout = subprocess.PIPE, shell = True)
        out, err = proc.communicate()
	print err 
        #remove the \n at the end of the line
	out=out.strip()  
        #split the string and put it in a list
	output_list=out.split(" ")
	pledge=output_list[1]
	s_status=output_list[2]
        
        if first:
	   startingComma=""
	   first=False
	else:
	   startingComma=","
        print 'startingComma '+startingComma
        #print dict_pen
        print '--------------------------------'		
        #print dict_run
        print 'site: '+site
        print 'site: '+str(site)
        print dict_run[site]
        print '--------------'
        print dict_pen[site]
        print 'rest'
        json_site_part= startingComma+"{\"site\":\""+str(site)+"\""      \
              +",\"Pending\":\""+str(dict_pen[site]['Processing']+dict_pen[site]['Production']+dict_pen[site]['Merge']+dict_pen[site]['Cleanup']+dict_pen[site]['LogCollect']+dict_pen[site]['RelVal'])+"\""        \
              +",\"TimeDate\":\""+str(currTime.strip())+"\"" \
             +",\"Running\":\""+str(dict_run[site]['Processing']+dict_run[site]['Production']+dict_run[site]['Merge']+dict_run[site]['Cleanup']+dict_run[site]['LogCollect']+dict_run[site]['RelVal'])+"\""        \
              +",\"RunProc\":\""+str(dict_run[site]['Processing'])+"\""      \
              +",\"RunProd\":\""+str(dict_run[site]['Production'])+"\""      \
              +",\"RunMerge\":\""+str(dict_run[site]['Merge'])+"\""          \
              +",\"RunClean\":\""+str(dict_run[site]['Cleanup'])+"\""        \
              +",\"RunLog\":\""+str(dict_run[site]['LogCollect'])+"\""       \
              +",\"RunRelVal\":\""+str(dict_run[site]['RelVal'])+"\""       \
              +",\"PenProc\":\""+str(dict_pen[site]['Processing'])+"\""      \
              +",\"PenProd\":\""+str(dict_pen[site]['Production'])+"\""      \
              +",\"PenMerge\":\""+str(dict_pen[site]['Merge'])+"\""          \
              +",\"PenClean\":\""+str(dict_pen[site]['Cleanup'])+"\""        \
              +",\"PenLog\":\""+str(dict_pen[site]['LogCollect'])+"\""       \
              +",\"PenRelVal\":\""+str(dict_pen[site]['RelVal'])+"\""       \
              +",\"Status\":\""+str(s_status)+"\""       \
              +"}"
        json_site_part_str=str(json_site_part).replace("('","").replace("')","")
        print json_site_part_str
	json_part += json_site_part_str
	#json_part += str(tuple(json_site_part))
#{"Site":"T1_DE_KIT","Pending":"0","TimeDate":"2012-12-04h11:01:01","Running":"19","Pledge":"1200","Status":"on","Ratio":"0.0158333","InstantAlarm":"OK","x1hAlarm":"OK","x24hAlarm":"ALARM","InstantGlideInAlarm":"OK","x1hGlideInAlarm":"OK","x24hGlideInAlarm":"OK","RunProc":"15","RunProd":"0","RunMerge":"3","RunClean":"0","RunLog":"1","PenProc":"0","PenProd":"0","PenMerge":"0","PenClean":"0","PenLog":"0"},
# sentence.replace(" ", "")
    print '----------------------------------------------------------------------------------------------------'
    json_part+= ']}' 
    json_part.replace(" ", "")
    print json_part
    #overwrite file
    json_file=open(json_name,"w")
    json_file.write(json_part)
    json_file.close() 


#____________________________________________________________________________________________________

#################################################################

print 'The new low level script.'
starttime=datetime.now()
print starttime
json_name="SSB_siteInfo.json"
tf= tempfile.NamedTemporaryFile()
site_slot_status=tf.name+"site_slotLimit_status.txt"
#site_slot_status="site_slotLimit_status.txt"
print site_slot_status

#Start of the program: Creating 3 empty dictionaries
overview_running = {}
overview_pending = {}
overview_other = {}

#get time
gettime="sqlite3 fakedatabase \"select datetime('now');\" "
currTime = subprocess.Popen(gettime, stdout=subprocess.PIPE, shell=True).communicate()[0]
currTime_list=currTime.split(" ")
date=currTime_list[0]
hour=currTime_list[1]
hour=hour.replace("\n"," ")
currTime=currTime.replace(' ','h')
print currTime

#create new site_list and check for new sites (is file_sitelist is filled at the end of the next for loop)
site_list_prev="site_list_prev.txt"
site_list="site_list.txt"
file_sitelist = open(site_list,'w')
file_sitelist.close()

# get file with the slots per site
slotcommand="wget -O %s -q http://cmst1.web.cern.ch/CMST1/wmaconfig/slot-limits.conf;" % (site_slot_status)
proc_slot = subprocess.Popen(slotcommand, stderr = subprocess.PIPE,stdout = subprocess.PIPE, shell = True)
out_slot, err_slot = proc_slot.communicate()
print out_slot
print err_slot
# create a json with keyword for every site with the pledge, if the status is DOWN, .... then the pledge of that site is 0
list_sitePledge=getSitePledgeList(site_slot_status)
print 'Fetched list of all the pledges for everysite. (Pledge=0 if site has a bad status)'
print list_sitePledge
print '-------------------------------------------------------------------------'

# making a txt file with all the jobs that are failing the type assignment logic
file_jobs_failedType=open("jobs_failingTypeAssignmentLogic.txt","w")

#Extracting the site's information and adding it to dictionaries
#command='condor_q -format "%i." ClusterID -format "%s " ProcId -format " %i " JobStatus  -format " %d " ServerTime-EnteredCurrentStatus -format "%s" UserLog -format " %s" DESIRED_Sites -format " %s" RemoveReason -format " %i\n" NumJobStarts'
#command="""condor_q -format "%i." ClusterID -format "%s " ProcId -format " %i " JobStatus  -format " %d " ServerTime-JobStartDate -format "%s" UserLog -format " %s" DESIRED_Sites -format " %s" RemoveReason -format " %i\n" NumJobStarts | awk '{if ($2!= 1) print $0}'"""
# condor_status -pool cmssrv119.fnal.gov  -schedd
# condor_status -pool vocms97.cern.ch  -schedd
for col in collectors:
  listschedds=[]
  listcommand="condor_status -pool "+col+" -schedd -format \"%s \n\" Name"
  print listcommand
  proc = subprocess.Popen(listcommand, stderr = subprocess.PIPE,stdout = subprocess.PIPE, shell = True)
  out, err = proc.communicate()
  for line in err.split('\n') :
        if 'Error' in line:
              listcommand="bash send_email.sh %s ; "% (col)
              print "Called:   "+listcommand
              proc = subprocess.Popen(listcommand, stderr = subprocess.PIPE,stdout = subprocess.PIPE, shell = True)
              out2, err2 = proc.communicate()
              print out2
              print "error: "
              print err2
              break
  for line in out.split('\n') :
	if ('cern' in line) or ('fnal' in line):
		listschedds.append(line)

  print out
  print "Passed condor_status on collector: "+ col
  
#  For debugging
#  f = open('EXAMPLE_OUTPUT_nomiddle.txt','r')
#  for out in f:
#        print out
  for schedd in listschedds:
  	command='condor_q -pool '+col+' -name ' + schedd
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
        proc = subprocess.Popen(command, stderr = subprocess.PIPE,stdout = subprocess.PIPE, shell = True)
	out, err = proc.communicate()
	for line in out.split('\n') :
            # remove empty lines
	    if line == "" : continue
	    # fix for sleep.log problem lines
            if 'sleep.log' in line: continue
            # All jobs to monitor have the word jobCache in there logfilename, otherwise it are some testjobs that we don't want to monitor
            if 'JobCache' not in line:
                #print array
                #print "No JobCache in line: "+line
                continue


            array = line.split("||")
            id = array[0]
	    status = int(array[1])
            log =array[2]
            siteToExtract = array[3]
            #print array
            #print len(array)

            # TYPE
            type = ''
            # to know if we have a site, we check if we have TX_XXX, we check the T and the first _
            typeToExtract = log
            #if array[4] it not a site it is the type !
            if len(array) > 5 :
              if  not ( array[4][0] == 'T' and array[4][2] == '_'  ) :
                typeToExtract = array[4]
                if typeToExtract == "" :
                  typeToExtract = log

            # now go through the group assignment
            if schedd.count('cmssrv113') > 0 :
                type = 'RelVal'
            elif typeToExtract.count('Merge') > 0 :
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
            elif typeToExtract.count('StepOneProc') > 0 :
                type = 'Processing'
            else :
                type = 'Processing'
                file_jobs_failedType.write(line)
                file_jobs_failedType.write('\n')
            # SITE extraction  
            # if old software, take DESIRED_Sites, if new software take MATCH_EXP_JOBGLIDEIN_CMSSite, or take random one if last variable doesn't exist, so if the job is still pending
            #if len(array) > 5 :
            #   print array
               #if len(array) >= 6:
            site = 'UNDEF' 



#            if len(array) > 5 and array[5] != '' :
#                  #if array[5] != '' : #CHECK STILL
#                  site = array[5]  #MATCH_EXP_JOBGLIDEIN_CMSSite
#            elif siteToExtract.count(',') == 0 :   #only 1 desired site in the list, so even if its down, the job will go to this site
#                  site = siteToExtract
#            else :

            if len(array) > 5 :
               # the site could be not yet assigned then the variable is empty
               if  array[5] != '' :
                    site = array[5]
               # array[4] can be the jobtype variable or the sitevariable. (or empty) Check for the site name signature
               elif  array[4][0] == 'T' and array[4][2] == '_'   :
                    siteToExtract = array[4]
               # if above not true then job is pending and array[3] got 1 or more sites to choose from
               else :
                  siteToExtract = array[3]


            # check if we have 1 site or multiple sites in our siteToExtract
            if siteToExtract.count(',') == 0 :   #only 1 desired site in the list, so even if its down, the job will go to this site
                  site = siteToExtract
            else :


                  # take random site from the DESIRED_Sites, site_splitted here  by the pledge of the active sites
                  site_splitted = siteToExtract.split(",")
                  site_splitted = [x.strip(' ') for x in site_splitted]
                  # extract random site based on pledge 
                  site_weight_dict = {}
                  # make a dict that contains the sites and their number of slots
                  for s in site_splitted:
                     # fetch the pledge, if its not in the list, use 0 instead of giving an error
                     site_weight_dict[s]=list_sitePledge.get(s,0)
                  # weighted random fetching of a site that is not disabled 
                     # if all sites are in down, we cant take a weighted random, we do a normal/uniform random
                  if sum(site_weight_dict.itervalues()) == 0:
                     print "========================================================="
                     print "Going to a uniform random instead of a weighted random since all sites in the sitelist are DOWN"
                     print "Sitelist: "+str(site_splitted)
                     for key in site_weight_dict.keys():
                        site_weight_dict[key] = 1
                  site = weighted_pick(site_weight_dict)
            str(site).replace(' ', '')
            # if site.count(',') != 0: print '||||', len(array), '||||', site, ':', siteToExtract, ':'
           
            # REMOVE SOME JOBS, dunno why
	    if 'JobCache' not in line:
                #print array
		#print "No JobCache in line: "+line
		continue
	    #workflow = log.split("/JobCache/")[1].split('/')[0]


	    if status == 2:
		increaseCounterInDict(overview_running,site,type)
	    elif status == 1:
		increaseCounterInDict(overview_pending,site,type)
#	    else :
#                print status
#		 increaseCounterInDict(overview_other,site,type)
	    
	    #fill all found sites into the site list file.
	    if not site in open(site_list).read():
		file_sitelist = open(site_list,'a')
	        #print>>file_sitelist, site

                site_write=site
                if '_Long' in site:
                    site_write=site.replace('_Long','')
                    if not site_write in open(site_list).read():
                         print>>file_sitelist, site_write
                elif '_Disk' in site:
                    site_write=site.replace('_Disk','')
                    if not site_write in open(site_list).read():
                         print>>file_sitelist, site_write
                else:
	            print>>file_sitelist, site
		file_sitelist.close()

#Check the site list and add a new site when necessary
#Checking if there might be a new site. If so, a new table is added. voBoxes without data will be kept here, so that the fillBrokenSites() function can still fill them with 0's. 
listcommand="bash update_sitelist.sh %s %s; "% (site_list_prev,site_list)
proc = subprocess.Popen(listcommand, stderr = subprocess.PIPE,stdout = subprocess.PIPE, shell = True)
out, err = proc.communicate()
print out
print err

print "passed full condor_status pooling"

#Adding the sites to the 2 dicts that are not in the overview list. They are added with 0's
fillBrokenSites(site_list,overview_running) 
fillBrokenSites(site_list,overview_pending) 

#Adding the _Long and _Disk job information to the site itself and remove the _Long and _Disk sites
print "Running"
removePostFixSites(overview_running,'_Long')
removePostFixSites(overview_running,'_Disk')
print "Pending"
removePostFixSites(overview_pending,'_Long')
removePostFixSites(overview_pending,'_Disk')


#Writing the json file
printDict(overview_running,"running")
printDict(overview_pending,"pending")
jsonDict(overview_running,overview_pending,json_name,date,hour)

# closing a file
file_jobs_failedType.close()

os.remove(site_slot_status)
print '__________________-'
print 'THE PROGRAM IS FINISHED AFTER', datetime.now()-starttime
