#!/usr/bin/env python
"""
This scripts creates the overall jobs report for monitoring in SSB
Should be set as a cron job @15 min
Creates a json file
"""

import sys,os,re,urllib,urllib2,subprocess,time
from datetime import datetime
try:
    import json
except ImportError:
    import simplejson as json

collectors = ['vocms97.cern.ch', 'vocms165.cern.ch']

relvalAgents = ['vocms142.cern.ch', 'cmssrv113.fnal.gov']

baseSiteList = {} # Site list
baseSitePledges = {} # Site pledges list
overview_running = {} # Running per site/task
temp_pending = [] # temporal pending jobs variable
overview_pending = {} # Pending per site/task
totalRunningSite = {} # Total running per site
jobs_failedTypeLogic = {} # Jobs that failed the type logic assignment
json_name = "SSB_siteInfo.json" # Output json file name
site_link = "http://dashb-ssb.cern.ch/dashboard/templates/sitePendingRunningJobs.html?site="
overalls_link = "http://dashb-ssb-dev.cern.ch/dashboard/templates/sitePendingRunningJobs.html?site=All%20T3210"


jobTypes = ['Processing', 'Production', 'Skim', 'Harvest', 'Merge', 'LogCollect', 'Cleanup', 'RelVal', 'T0']
t0Types = ['Repack', 'Express', 'Reco']

def createSiteList():
    """
    Creates a initial site list with the data from site status in Dashboard
    """
    url_site_status = 'http://dashb-ssb.cern.ch/dashboard/request.py/getplotdata?columnid=158&batch=1&lastdata=1'
    sites = urllib2.urlopen(url_site_status).read()
    try:
        site_status = json.read(sites)['csvdata']
    except:
        site_status = json.loads(sites)['csvdata']
    
    for site in site_status:
        name = site['VOName']
        status = site['Status']
        if siteName(name):
            baseSiteList[name] = status

def getSitePledge():
    """
    Get the expected pledge to use from Dashboard
    """
    url_site_status = 'http://dashb-ssb.cern.ch/dashboard/request.py/getplotdata?columnid=159&batch=1&lastdata=1'
    sites = urllib2.urlopen(url_site_status).read()
    try:
        site_pledges = json.read(sites)['csvdata']
    except:
        site_pledges = json.loads(sites)['csvdata']
    
    for site in site_pledges:
        name = site['VOName']
        if site['Value'] == None:
            value = 0
        else:
            value = int(site['Value'])
        if siteName(name):
            baseSitePledges[name] = value

def initJobPerSite():
    """
    This creates the dictionaries of running/pending jobs for each site in the baseSiteList
    """
    for site in baseSiteList.keys():
        if '_Disk' not in site: # Avoid _Disk suffixes
            overview_running[site] = dict()
            for type in jobTypes:
                overview_running[site][type] = 0.0
            overview_pending[site] = dict()
            for type in jobTypes:
                overview_pending[site][type] = 0.0

def siteName(candidate):
    """
    Check candidate as a site name. Should pass:
        T#_??_*
    Returns True if it is a site name
    """
    regexp = "^T[0-3%](_[A-Z]{2}(_[A-Za-z0-9]+)*)$"
    if re.compile(regexp).match(candidate) != None:
        return True
    else:
        return False

def addSite(site):
    """
    Add a site to all the dictionaries
    """
    print "DEBUG: Adding site %s to base lists" % site
    if site not in overview_running.keys():
        overview_running[site] = dict()
        for type in jobTypes:
            overview_running[site][type] = 0.0
    
    if site not in overview_pending.keys():
        overview_pending[site] = dict()
        for type in jobTypes:
            overview_pending[site][type] = 0.0
    
    if site not in baseSiteList.keys():
        baseSiteList[site] = 'on'
    

def increaseRunning(site,type):
    """
    Increase the number of running jobs for the given site and type
    This always increase job count by 1
    """
    if site in overview_running.keys():
        overview_running[site][type] += 1
    else:
        addSite(site)
        overview_running[site][type] += 1
        
def increasePending(site,type,num):
    """
    Increase the number of pending jobs for the given site and type
    This handles smart counting: sum the relative pending 'num'
    """
    if site in overview_pending.keys():
        overview_pending[site][type] += num
    else:
        addSite(site)
        overview_pending[site][type] += num

def findTask(id,sched,typeToExtract):
    """
    This deduces job type from given info about scheduler and taskName
    """
    type = ''
    if sched.strip() in relvalAgents:
        type = 'RelVal'
    elif 'Cleanup' in typeToExtract:
        type = 'Cleanup'
    elif 'Merge' in typeToExtract:
        type = 'Merge'
    elif 'LogCollect' in typeToExtract:
        type = 'LogCollect'
    elif 'skim' in typeToExtract.lower():
        type = 'Skim'
    elif 'harvest' in typeToExtract.lower():
        type = 'Harvest'
    elif 'Production' in typeToExtract or 'MonteCarloFromGEN' in typeToExtract:
        type = 'Production'
    elif 'Processing' in typeToExtract or 'StepOneProc' in typeToExtract or 'StepTwoProc' in typeToExtract:
        type = 'Processing'
    elif 'StoreResults' in typeToExtract:
        type = 'Merge'
    elif any([x in typeToExtract for x in t0Types]):
        type = 'T0'
    else:
        type = 'Processing'
        jobs_failedTypeLogic[id]=dict(scheduler = sched, BaseType = typeToExtract)
    return type

def fixArray(array):
    """
    Sometimes (I dont know why) condor return different formats. Parse all to string
    """
    fixexArray = []
    for entry in array:
        fixexArray.append(str(entry))
    return fixexArray

def relativePending(siteToExtract):
    """
    Return the remaining slots available (in principle) to run jobs for the given sites
    If there is no slots available, ruturn the same value for all the given (same chance to run)
    """
    relative = {}
    total = 0.0
    for site in siteToExtract:
        if site in totalRunningSite.keys():
            running = totalRunningSite[site]
        else:
            running = 0.0
        if site in baseSitePledges.keys():
            pledge = baseSitePledges[site]
        else:
            pledge = 0.0
        
        relative[site] = pledge - running
        if relative[site] < 0.0:
            relative[site] = 0.0
        total += relative[site]
    
    # if total = 0, it means that there is not available slots for any site, set the same for all sites
    if total == 0.0:
        total = len(siteToExtract)
        for site in relative.keys():
            relative[site] = 1.0
    
    return relative, total
    
    
def fixOverviews():
    """
    Add the sites that has pending but not running to overview_running,
    or sites that has running but not pending to overview_pending
    """
    sites_running = overview_running.keys()
    sites_pending = overview_pending.keys()
    
    for site in sites_running:
        if site not in sites_pending:
            print "DEBUG: Adding info of site %s to pending jobs for sites" % site
            overview_pending[site] = dict()
            for type in jobTypes:
                overview_pending[site][type] = 0.0
            
    for site in sites_pending:
        if site not in sites_running:
            print "DEBUG: Adding info of site %s to running jobs for sites" % site
            overview_running[site] = dict()
            for type in jobTypes:
                overview_running[site][type] = 0.0

def handleDict(dict, description, date, hour):
    """
    1. Prints a report for the given dictionary
    2. Dashboard cannot read from the json file created for the site plots...
       So we need to create a text file for each column in SSB running/pending views
    """
    sorted = dict.keys()
    sorted.sort()
    
    overall_type = {}
    # Init overalls per type
    for type in jobTypes:
        overall_type[type] = 0.0
        # Init text output files
        file = open('./'+description+type+'.txt', 'w+')
        file.close()
    file = open('./'+description+"Total"+'.txt', 'w+')
    file.close()
    
    # print Titles
    line1 = "| %25s |" % description
    line2 = "| %25s |" % ('-'*25)
    for type in jobTypes:
        line1 += " %10s |" % type
        line2 += " %10s |" % ('-'*10)
    line1 += " %10s |" % 'Total'
    line2 += " %10s |" % ('-'*10)
    print line2, '\n', line1, '\n', line2
    
    # Print jobs per site
    for site in sorted: 
        sum = 0.0
        lineSite = "| %25s |" % site
        for type in jobTypes:
            lineSite += " %10s |" % int(dict[site][type])
            sum += dict[site][type]
            overall_type[type] += dict[site][type]
            
            # add site jobs per type to 'description''type' file
            file = open('./'+description+type+'.txt', 'a')
            file.write( "%s %s\t%s\t%s\t%s\t%s%s\n" % (date, hour, site, str(int(dict[site][type])), 'green', site_link, site ))
            
        lineSite += " %10s |" % int(sum)
        
        # add site total jobs to 'description'Total file
        file = open('./'+description+"Total"+'.txt', 'a')
        file.write( "%s %s\t%s\t%s\t%s\t%s%s\n" % (date, hour, site, str(int(sum)), 'green', site_link, site ))
        
        print lineSite
    
    # Print overalls
    overalls = "| %25s |" % 'Overalls'
    total = 0.0
    for type in jobTypes:
        total += overall_type[type]
        overalls += " %10s |" % int(overall_type[type])
        
        # add overalls to 'description''type' file
        file = open('./'+description+type+'.txt', 'a')
        file.write( "%s %s\t%s\t%s\t%s\t%s\n" % (date, hour, 'Overall', str(int(overall_type[type])), 'green' , overalls_link ))
        
    overalls += " %10s |" % int(total)
    file = open('./'+description+"Total"+'.txt', 'a')
    file.write( "%s %s\t%s\t%s\t%s\t%s\n" % (date, hour, 'Overall', str(int(total)), 'green', overalls_link ))
    print line2, '\n', overalls, '\n', line2, '\n'

def jsonDict(json_name,currTime,date,hour):
    """
    This creates a json form text and writes it into the json_name output file
    """
    sorted_run = overview_running.keys() # Running and pending keys must be the same after fixOverviews()
    sorted_run.sort()
    
    jsonfile = open(json_name,'w+')
    update = {"UPDATE" : {"Date" : date, "Time" : hour}, "Sites" : []}
    
    for site in sorted_run:
        # Get site status
        s_status = 'on' # Default for sites that has been added (not in baseSiteList)
        if site in baseSiteList.keys():
            s_status = baseSiteList[site]
         
        sumPending = 0.0
        sumRunning = 0
        for type in jobTypes:
            sumPending += overview_pending[site][type]
            sumRunning += overview_running[site][type]
            
        json_site = dict()
        json_site["site"] = str(site)
        json_site["Pending"] = str(int(sumPending))
        json_site["TimeDate"] = str(currTime.strip())
        json_site["Running"] = str(int(sumRunning))
        json_site["RunProc"] = str(int(overview_running[site]['Processing']))
        json_site["RunProd"] = str(int(overview_running[site]['Production']))
        json_site["RunSkim"] = str(int(overview_running[site]['Skim']))
        json_site["RunHarvest"] = str(int(overview_running[site]['Harvest']))
        json_site["RunMerge"] = str(int(overview_running[site]['Merge']))
        json_site["RunClean"] = str(int(overview_running[site]['Cleanup']))
        json_site["RunLog"] = str(int(overview_running[site]['LogCollect']))
        json_site["RunRelval"] = str(int(overview_running[site]['RelVal']))
        json_site["RunT0"] = str(int(overview_running[site]['T0']))
        json_site["PenProc"] = str(int(overview_pending[site]['Processing']))
        json_site["PenProd"] = str(int(overview_pending[site]['Production']))
        json_site["PenSkim"] = str(int(overview_pending[site]['Skim']))
        json_site["PenHarvest"] = str(int(overview_pending[site]['Harvest']))
        json_site["PenMerge"] = str(int(overview_pending[site]['Merge']))
        json_site["PenClean"] = str(int(overview_pending[site]['Cleanup']))
        json_site["PenLog"] = str(int(overview_pending[site]['LogCollect']))
        json_site["PenRelval"] = str(int(overview_pending[site]['RelVal']))
        json_site["PenT0"] = str(int(overview_pending[site]['T0']))
        json_site["Status"] = str(s_status)
        
        update["Sites"].append(json_site)
              
    jsonfile.write(json.dumps(update,sort_keys=True, indent=3))
    jsonfile.close()

def main():
    """
    Main algorithm
    """
    starttime=datetime.now()
    print 'INFO: Script started on: ', starttime
    
    #get time (date and hour)
    currTime = time.strftime("%Y-%m-%dh%H:%M:%S")
    date = currTime.split('h')[0]
    hour = currTime.split('h')[1]
    
    #Create base dictionaries for running/pending jobs per site
    createSiteList() # Sites from SSB
    getSitePledge() # Get pledges by site from SSB
    initJobPerSite() # Init running/pending dictionaries
    
    #Going through each collector and process a job list for each scheduler
    for col in collectors:
        # Get the list of scheduler for the given collector
        listschedds=[]
        listcommand="condor_status -pool "+col+" -schedd -format \"%s \n\" Name"
        proc = subprocess.Popen(listcommand, stderr = subprocess.PIPE,stdout = subprocess.PIPE, shell = True)
        out, err = proc.communicate()
        for line in err.split('\n') :
            if 'Error' in line:
                listcommand="bash send_email.sh %s ; " % col
                proc = subprocess.Popen(listcommand, stderr = subprocess.PIPE,stdout = subprocess.PIPE, shell = True)
                out2, err2 = proc.communicate()
                print 'ERROR: I find a problem while getting schedulers for collector %s, I will send an email' % col
                #print out2, '\n', "Error: ", '\n', err2
                break
        for line in out.split('\n') :
    	    if ('cern' in line) or ('fnal' in line):
    		    listschedds.append(line)
        print "INFO: Condor status on collector %s has been started" % col
        
        # Get the running/pending jobs from condor for the given scheduler
        for sched in listschedds:
            command='condor_q -pool '+col+' -name ' + sched
            command=command+"""  -format "%i." ClusterID -format "%s||" ProcId  -format "%i||" JobStatus  -format "%s||" WMAgent_SubTaskName -format "%s||" DESIRED_Sites -format "\%s||" WMAgent_SubTaskType -format "%s||" MATCH_EXP_JOBGLIDEIN_CMSSite -format "\n" Owner"""
            proc = subprocess.Popen(command, stderr = subprocess.PIPE,stdout = subprocess.PIPE, shell = True)
            out, err = proc.communicate()
            print "INFO: Handling condor_q on collector: %s scheduler: %s" % (col, sched)
            
            for line in out.split('\n') :
                if line == "" : 
                    continue # remove empty lines
                
                array = line.split("||")
                if len(array) < 5: 
                    continue # ignore bad lines (incomplete info lines)
                array = fixArray(array)
                
                # array[0] ClusterID.ProcId
                # array[1] JobStatus
                # array[2] WMAgent_SubTaskName
                # array[3] DESIRED_Sites
                    # only when it is the new software: array[4] WMAgent_SubTaskType
                    # only when job is already running: array[5] MATCH_EXP_JOBGLIDEIN_CMSSite
                # array[6] ''    --> nothing
                # --> standard len(array) {5,6} depending if the job is already running in a site
                # --> new software len(array) ={6,7} depending if the job is already running in a site
                id = array[0]
                status = array[1]
                task = array[2].split('/')[-1]
                siteToExtract = array[3].replace(' ', '').split(",")
                
                typeToExtract = task
                # Task Extraction
                #if array[4] is not a site it is the type, only for new software (len(array)>5)
                if len(array) > 5 and not siteName(array[4]) and array[4] != "":
                    typeToExtract = array[4]
                type = findTask(id,sched,typeToExtract)
                
                # Site Extraction
                # use array[5]/[4] if it is a site name (depending on new/old software)
                if len(array) > 5 :
                    if len(array) == 7 and siteName(array[5]):
                        siteToExtract = [array[5]]
                    elif siteName(array[4]):
                        siteToExtract = [array[4]]
                
                if status == "2":
                    increaseRunning(siteToExtract[0],type) # I assume one job can only run at one site
                elif status == "1":
                    temp_pending.append([type,siteToExtract])
                else: # We do not care about jobs in another status (condor job status: https://htcondor-wiki.cs.wisc.edu/index.cgi/wiki?p=MagicNumbers)
                    continue
    print "INFO: Full condor status pooling is done"
    
    # Get total running
    for site in overview_running.keys():
        totalRunningSite[site] = 0.0
        for type in overview_running[site].keys():
            totalRunningSite[site] += overview_running[site][type]
    
    # Now process pending jobs
    for job in temp_pending:
        type = job[0]
        siteToExtract = []
        # Remove "_Disk" from sites (job will not run there)
        for site in job[1]:
            siteToExtract.append(site.replace('_Disk',''))
        siteToExtract = list(set(siteToExtract)) # remove duplicates
        
        relative, total = relativePending(siteToExtract) # total != 0 always
        for penSite in siteToExtract:
            relative_pending = relative[penSite]/total # calculate relative pending weight
            increasePending(penSite, type, relative_pending) 
    print "INFO: Smart pending site counting done \n"
    
    # Handling jobs that failed task extraction logic
    if jobs_failedTypeLogic != {}:
        command="bash failedLogic_email.sh \"%s\"" % str(jobs_failedTypeLogic)
        proc = subprocess.Popen(command, stderr = subprocess.PIPE,stdout = subprocess.PIPE, shell = True)
        out, err = proc.communicate()
        print 'ERROR: I find jobs that failed the type assignment logic, I will send an email'
        #print out, '\n', "Error: ", '\n', err
    
    # Adding sites not in either of running/pending overviews
    fixOverviews()
    
    print 'INFO: Creating reports...'
    
    # Prints a report and creates Dashboard feeder files (SSB can't take info from json for runnnig/pending views...)
    handleDict( overview_running, "Running", date, hour)
    handleDict( overview_pending, "Pending", date, hour)
    
    # Creates json file (This is needed for plots per site)
    jsonDict( json_name, currTime, date, hour)
    
    print 'INFO: The script has finished after: ', datetime.now()-starttime

if __name__ == "__main__":
    main()

