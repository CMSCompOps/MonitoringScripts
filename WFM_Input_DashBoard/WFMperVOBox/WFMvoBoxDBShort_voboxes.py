#!/usr/bin/env python

# script that fills the WM database. It is called every 15 min and the database itself is 1time created with create_WMdatabase.db
# script calls a bash function to write the database because only sqlite 1.1.7 is available in python ( <--> sqlite3 in bash )

import sys,os
import subprocess
from datetime import datetime
import urllib2
#collectors = ['vocms97.cern.ch', 'vocms165.cern.ch', 'cmssrv119.fnal.gov']
collectors = ['vocms97.cern.ch', 'vocms165.cern.ch']

schedd_status_url = r'https://cmst1.web.cern.ch/CMST1/wmaconfig/AgentStatus.txt'

#previous list:
schedd_file_prev = "voboxlist_prev.txt"
    
#write list of schedulers to vobox file    
schedd_file = "voboxlist.txt"

currTime = None

# Filling the dictionaries
def increaseCounterInDict(dictionary, schedd, jobType):
    if schedd in dictionary:
        dictionary[schedd][jobType] += 1
    else:
        tmp = {
        'Processing': 0,
        'Production': 0,
        'Merge': 0,
        'Cleanup': 0,
        'LogCollect': 0,
        'TestJobs' : 0,
        }
        dictionary[schedd] = tmp
        dictionary[schedd][jobType] += 1

# Fill the sites/vobox that have no information atm, but are in the database, with 0's
def fillBrokenSites(schedd_list, dictionary):
    #print dict.keys()
    for schedd in schedd_list:
        stripped_site = schedd.strip()
        if not stripped_site in dictionary:
            tmp = {
            'Processing': 0,
            'Production': 0,
            'Merge': 0,
            'Cleanup': 0,
            'LogCollect': 0,
            'TestJobs' : 0,
            }
            dictionary[stripped_site] = tmp

#Printing function for debugging
def printDict(dictionary, description):
    sortedKeys = dictionary.keys()
    sortedKeys.sort()
    print '-'*114
    print '| %35s | Processing | Production | Merge      | Cleanup    | LogCollect |  TestJobs   |   Total      |' % description
    print '-'*114
    for site in sortedKeys:
        print '| %35s | %10d | %10d | %10d | %10d | %10d | %10d | %10d |' % (site, dictionary[site]['Processing'],
                            dictionary[site]['Production'], dictionary[site]['Merge'],
                            dictionary[site]['Cleanup'], dictionary[site]['LogCollect'], dictionary[site]['TestJobs'],
                            dictionary[site]['Processing'] + dictionary[site]['Production'] + dictionary[site]['Merge']      
                            +dictionary[site]['Cleanup'] + dictionary[site]['LogCollect'] + dictionary[site]['TestJobs'])
    print '-'*114

def getScheddStatus():
    """
    retrieves the collector announced time
    and creates a dictionary
    """        
    out = urllib2.urlopen(schedd_status_url).read()
    schedd_status = {}
     
    for line in out.split('\n'):
        #ignore empty lines
        if not line.strip():
            continue
        print line
        arr = line.split()
        schedd = line[0]
        status = line[1]
        schedd_status[schedd] = status
    return schedd_status
    
#Writing json file
def jsonDict(dict_run, dict_pen, json_name, date, hour, location):
    #sort scheddulers
    schedd_list = dict_run.keys()
    schedd_list.sort()
    #get the shceduler status
    schedd_status = getScheddStatus()
    
    #header
    json_part = '{\"UPDATE\":{\"Date\":\"'+date+'\",\"Time\":\"'+hour+'\"},\"'+location+'\":['
    
    #site is here a voBox
    first = True
    for schedd in schedd_list:
        #get the schedd status if available, 'up' otherwise
        if schedd in schedd_status:
            s_status = schedd_status[schedd]
        else:
            s_status = 'up'
        #only first comma        
        if first:
           startingComma = ""
           first = False
        else:
           startingComma = ","

        #adapt schedd to format
        schedd_fix = schedd.replace('.',"_")
        schedd_fix = schedd_fix.strip(' ')

        #schedd data
        json_schedd_part = startingComma+"{\"VOBox\":\""+str(schedd_fix)+"\""  \
              +",\"Pending\":\""+str(dict_pen[schedd]['Processing']
                                    +dict_pen[schedd]['Production']
                                    +dict_pen[schedd]['Merge']
                                    +dict_pen[schedd]['Cleanup']
                                    +dict_pen[schedd]['LogCollect']
                                    +dict_run[schedd]['TestJobs'])+"\""        \
              +",\"TimeDate\":\""+str(currTime.strip())+"\"" \
              +",\"Running\":\""+str(dict_run[schedd]['Processing']
                                    +dict_run[schedd]['Production']
                                    +dict_run[schedd]['Merge']
                                    +dict_run[schedd]['Cleanup']
                                    +dict_run[schedd]['LogCollect']
                                    +dict_pen[schedd]['TestJobs'])+"\""        \
              +",\"Status\":\""+str(s_status)+"\""   \
              +",\"RunProc\":\""+str(dict_run[schedd]['Processing'])+"\""      \
              +",\"RunProd\":\""+str(dict_run[schedd]['Production'])+"\""      \
              +",\"RunMerge\":\""+str(dict_run[schedd]['Merge'])+"\""  \
              +",\"RunClean\":\""+str(dict_run[schedd]['Cleanup'])+"\""        \
              +",\"RunLog\":\""+str(dict_run[schedd]['LogCollect'])+"\""       \
              +",\"RunTestJobs\":\""+str(dict_run[schedd]['TestJobs'])+"\""       \
              +",\"PenProc\":\""+str(dict_pen[schedd]['Processing'])+"\""      \
              +",\"PenProd\":\""+str(dict_pen[schedd]['Production'])+"\""      \
              +",\"PenMerge\":\""+str(dict_pen[schedd]['Merge'])+"\""  \
              +",\"PenClean\":\""+str(dict_pen[schedd]['Cleanup'])+"\""        \
              +",\"PenLog\":\""+str(dict_pen[schedd]['LogCollect'])+"\""       \
              +",\"PenTestJobs\":\""+str(dict_pen[schedd]['TestJobs'])+"\""       \
              +"}"
        #remove parenthesis 
        json_schedd_part = str(json_schedd_part).replace("('","").replace("')","")

        #print json_schedd_part_str
        json_part += json_schedd_part

    json_part += ']}'
    #remove spaces
    json_part.replace(" ", "")

    print '-'*114
    #print json_part
    #overwrite file
    json_file = open(json_name,"w")
    json_file.write(json_part)
    json_file.close()
#################################################################


def getSchedulersFromCollector(collector):
    """
    Gets a scheduler lists from a collector
    """
    result = []
    #Extracting the schedulars list from all collectors
    dict_col_with_schedd={}

    #run condor command to check schedulers
    listcommand="condor_status -pool "+collector+" -schedd -format \"%s \n\" Name"
    print listcommand
    proc = subprocess.Popen(listcommand, stderr = subprocess.PIPE,stdout = subprocess.PIPE, shell = True)
    out, err = proc.communicate()

    # we don't have to send an email when there is an error (collector not reachable), since it is already done in the script per schedd
    for line in err.split('\n') :
        if 'Error' in line:
            print "Called:   "+listcommand
            print "Col: "+collector+" is offline"
            break
    #append server names
    for line in out.split('\n') :
        if ('cern' in line) or ('fnal' in line):
            result.append(line.strip())
    return result

def updateScheddList(schedd_list):
    """
    Updates schedulers lists
    """
    #read from file previous list
    try:
        schedd_list_prev = [l.strip() for l in open(schedd_file, 'r') if l.strip()]
    except:
        #if errors list is empty
        schedd_list_prev = []
    print "update collector list "
    #merge both lists:
    for schedd in schedd_list:
        #if not in previous list, add it
        if schedd not in schedd_list_prev:
            schedd_list_prev.append(schedd)

    schedd_list = schedd_list_prev

    #write resulting list to file 
    sched_file_w = open(schedd_file,'w')
    for schedd in schedd_list:
        sched_file_w.write(schedd+'\n')
    sched_file_w.close()

    #return the merged list
    return schedd_list


def countJobsForSchedd(coll, schedd, dict_running, dict_pending):
    # Issue, need to know which col + which schedd
    command = 'condor_q -pool ' + coll + ' -name ' + schedd
    command += (' -format "%i." ClusterID -format "%s||" ProcId -format "%i||" JobStatus'+
                ' -format "%s||" UserLog -format "%s||" WMAgent_SubTaskType'+
                r' -format "\n" ProcId')
    # array[0] ClusterID.ProcId
    # array[1] JobStatus
    # only when its the new software
    # array[2] UserLog
    # array[3] WMAgent_SubTaskType

    print command
    #command line
    proc = subprocess.Popen(command, stderr = subprocess.PIPE,stdout = subprocess.PIPE, shell = True)
    out, err = proc.communicate()

    #process output
    for line in out.split('\n') :
        if line == "" :
            continue
        # skip sleep.log problem lines
        if 'sleep.log' in line:
            continue
        array = line.split("||")
        procId = array[0]
        jobStatus = int(array[1])
        userLog = array[2]
        if len(array) > 3:
            subTaskType = array[3] 
        else:
             subTaskType = None
        #extract type from task name, if not available, from logname
        if subTaskType:
            typeToExtract = subTaskType 
        else:
            typeToExtract = userLog
        jobType = ''

        # now go through the group assignment
        if typeToExtract.count('Merge') > 0 :
            jobType = 'Merge'
        elif typeToExtract.count('Cleanup') > 0 :
            jobType = 'Cleanup'
        elif typeToExtract.count('LogCollect') > 0 :
            jobType = 'LogCollect'
        elif typeToExtract.count('Production') > 0 :
            jobType = 'Production'
        elif typeToExtract.count('MonteCarloFromGEN') > 0 :
            jobType = 'Production'
        elif typeToExtract.count('Skim') > 0 :
            jobType = 'Production'
            #jobType = 'Skim'
        elif typeToExtract.count('Harvest') > 0 :
            #jobType = 'Harveset'
           jobType = 'Production'
        elif typeToExtract.count('Processing') > 0 :
            jobType = 'Processing'
        # HC/TestJobs
        elif schedd.count('vocms228') > 0 :
            jobType = 'TestJobs'  
        else :
            jobType = 'Processing'

        # skip production jobs with JobCache, or HC/TestJobs with condor 
        if 'JobCache' not in line and 'vocms228' not in schedd:
            continue
        
        # Increase/append the dictionarry
        #running
        if jobStatus == 2:
            increaseCounterInDict(dict_running, schedd, jobType)
        #pending
        elif jobStatus == 1:
            increaseCounterInDict(dict_pending, schedd, jobType)
        #else :
        #increaseCounterInDict(overview_other,schedd_fix,type)


def main():
    global currTime
    #Timing the script
    starttime = datetime.now()
    #split utc time
    currTime = datetime.utcnow().strftime("%Y-%m-%dh%H:%M:%S ")
    

    jsonCERN_name="SSBCERN_voBoxInfo.json"

    #Start of the program: Creating 3 empty dictionaries
    overview_running = {}
    overview_pending = {}
    #overview_other = {}

    date, hour = currTime.split('h')    
    
    #map - collector - schedulers    
    coll_schedd = {}
        
    listschedds = []
    #get a list if schedulers and the reference to each collector
    for col in collectors:
        schedds = getSchedulersFromCollector(col)
        coll_schedd[col] = schedds
        listschedds += schedds
    
    print "Passed condor_status pool of all collectors."
    print "Dict of dict['col']= [schedds]:"
    print coll_schedd
    
    #saves a schedduler lists to keep in file
    listschedds = updateScheddList(listschedds)

    for coll in coll_schedd.keys():
        for schedd in coll_schedd[coll]:
            #count jobs for each schedduler and fill running and pending jobs.
            countJobsForSchedd(coll, schedd, overview_running, overview_pending)
            

    #Adding the voboxes to the 2 dicts that are not in the overview list. At the moment they are added with 0's
    fillBrokenSites(listschedds, overview_running) 
    fillBrokenSites(listschedds, overview_pending) 

    #print overview_running
    printDict(overview_running,'Running')
    print ""
    #print overview_pending
    printDict(overview_pending,'Pending')

    #Writing the json file
    jsonDict(overview_running, overview_pending, jsonCERN_name, date, hour, "CERN")

    print '__________________-'
    print 'THE PROGRAM IS FINISHED AFTER', datetime.now()-starttime

if __name__ == '__main__':
    main()
