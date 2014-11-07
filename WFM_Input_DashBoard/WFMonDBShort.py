#!/usr/bin/env python
"""
This scripts creates the overall job reports for monitoring in SSB
Should be set as a cronjob @15 min
Creates the following files: SSB_siteInfo.json, SSB_voBoxInfo.json, CondorJobs_Workflows.json, Running*.txt and Pending*.txt ( * in types )
"""

import sys,os,re,urllib,urllib2,subprocess,time,smtplib,os
from datetime import datetime
from email.MIMEMultipart import MIMEMultipart
from email.MIMEBase import MIMEBase
from email.MIMEText import MIMEText
from email.Utils import COMMASPACE, formatdate
from email import Encoders
try:
    import json
except ImportError:
    import simplejson as json

## Job Collectors (Condor pools)
collectors = ['vocms97.cern.ch', 'vocms097.cern.ch', 'vocms099.cern.ch']

## The following machines should be ignored (Crab Schedulers)
crab_scheds = ['vocms83.cern.ch','stefanovm.cern.ch']

##The following groups should be updated according to https://twiki.cern.ch/twiki/bin/view/CMSPublic/CompOpsWorkflowTeamWmAgentRealeases
relvalAgents = ['vocms142.cern.ch']
testAgents = ['cmssrv94.fnal.gov', 'cmssrv101.fnal.gov', 'vocms230.cern.ch', 'vocms231.cern.ch', '_condor@vocms227.cern.ch']

## Counting by site
baseSiteList = {} # Site list
baseSitePledges = {} # Site pledges list
overview_running = {} # Running per site/task
temp_pending = [] # temporal pending jobs variable
overview_pending = {} # Pending per site/task
totalRunningSite = {} # Total running per site
jobs_failedTypeLogic = {} # Jobs that failed the type logic assignment
json_name_sites = "SSB_siteInfo.json" # Output json file name

##Counting by vobox
overview_running_vobox = {}# Running per vobox
overview_pending_vobox = {}# Pending per vobox
json_name_vobox = "SSBCERN_voBoxInfo.json" # Output json file name

##Counting Workflows
overview_workflows = {}
json_name_workflows = "CondorJobs_Workflows.json" # Output json file name

##SSB plot links
site_link = "http://dashb-ssb.cern.ch/dashboard/templates/sitePendingRunningJobs.html?site="
overalls_link = "http://dashb-ssb-dev.cern.ch/dashboard/templates/sitePendingRunningJobs.html?site=All%20"

## Job expected types
jobTypes = ['Processing', 'Production', 'Skim', 'Harvest', 'Merge', 'LogCollect', 'Cleanup', 'RelVal', 'T0']
t0Types = ['Repack', 'Express', 'Reco']
backfillTypes = ['SMP', 'RECO', 'DIGI', 'Prod', 'MinBias']

# Mailing list for notifications
mailingSender = 'noreply@cern.ch'
mailingList = ['luis89@fnal.gov','dmason@fnal.gov']
#mailingList = ['cms-comp-ops-workflow-team@cern.ch']

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

def addVoBox(VoBox):
    """
    Add a VoBox to all the VoBox dictionaries
    """
    print "INFO: Adding VoBox %s" % VoBox
    overview_running_vobox[VoBox] = dict()
    for type in jobTypes:
        overview_running_vobox[VoBox][type] = 0
    
    overview_pending_vobox[VoBox] = dict()
    for type in jobTypes:
        overview_pending_vobox[VoBox][type] = 0

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

def increaseRunningVoBox(sched,type):
    """
    Increase the number of running jobs for the given sched and type
    This always increase job count by 1
    """
    overview_running_vobox[sched][type] += 1

def increasePendingVoBox(sched,type):
    """
    Increase the number of pending jobs for the given sched and type
    This always increase job count by 1
    """
    overview_pending_vobox[sched][type] += 1

def increaseRunningWorkflow(workflow,siteToExtract):
    """
    Increases the number of running jobs per workflow
    """
    if workflow not in overview_workflows.keys():
        addWorkflow(workflow)
        if siteToExtract in overview_workflows[workflow]['runningJobs'].keys():
            overview_workflows[workflow]['runningJobs'][siteToExtract] += 1
            overview_workflows[workflow]['condorJobs'] += 1
        else:
            overview_workflows[workflow]['runningJobs'][siteToExtract] = 1
            overview_workflows[workflow]['condorJobs'] += 1
    else:
        if siteToExtract in overview_workflows[workflow]['runningJobs'].keys():
            overview_workflows[workflow]['runningJobs'][siteToExtract] += 1
            overview_workflows[workflow]['condorJobs'] += 1
        else:
            overview_workflows[workflow]['runningJobs'][siteToExtract] = 1
            overview_workflows[workflow]['condorJobs'] += 1
    
def increasePendingWorkflow(workflow,siteToExtract):
    """
    Increases the number of pending jobs per workflow
    """
    if workflow not in overview_workflows.keys():
        addWorkflow(workflow)
        overview_workflows[workflow]['condorJobs'] += 1
        overview_workflows[workflow]['pendingJobs'] += 1
        overview_workflows[workflow]['desiredSites'] = overview_workflows[workflow]['desiredSites'].union(set(siteToExtract))
    else:
        overview_workflows[workflow]['condorJobs'] += 1
        overview_workflows[workflow]['pendingJobs'] += 1
        overview_workflows[workflow]['desiredSites'] = overview_workflows[workflow]['desiredSites'].union(set(siteToExtract))

def addWorkflow(workflow):
    """
    Add a new workflow to overview_workflows
    """
    overview_workflows[workflow] = {
                                    'condorJobs' : 0,
                                    'runningJobs' : {},
                                    'pendingJobs' : 0,
                                    'desiredSites' : set()
                                    }

def findTask(id,sched,typeToExtract):
    """
    This deduces job type from given info about scheduler and taskName
    """
    type = ''
    if sched in relvalAgents:
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
    elif any([x in typeToExtract for x in ['Processing','StepOneProc','StepTwoProc','StepThreeProc']]):
        type = 'Processing'
    elif 'StoreResults' in typeToExtract:
        type = 'Merge'
    elif any([x in typeToExtract for x in t0Types]):
        type = 'T0'
    elif sched in testAgents or any(x in typeToExtract for x in backfillTypes):
        type = 'Processing'
    else:
        type = 'Processing'
        jobs_failedTypeLogic[id]=dict(scheduler = sched, BaseType = typeToExtract)
    return type

def fixArray(array):
    """
    Sometimes (I dont know why) condor return different formats. Parse all to string
    """
    strings_array = []
    for entry in array:
        strings_array.append(str(entry))
    return strings_array

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

def handleDict(dict, description, date, hour, server):
    """
    1. Prints a report for the given dictionary
    2. Dashboard cannot read from the json file created for the site plots...
       So we need to create a text file for each column in SSB running/pending views
    """
    sorted = dict.keys()
    sorted.sort()
    
    # Assign plot names
    if server:
        endpoint_entry = "&server"
        entry_overall = "Servers"
        endpoint_overall = "Servers"
    else:
        endpoint_entry = ""
        entry_overall = "Sites"
        endpoint_overall = "T3210"
    
    overall_type = {}
    # Init overalls per type
    for type in jobTypes:
        overall_type[type] = 0.0
        # Init text output files
        if not server:
            file = open('./'+description+type+'.txt', 'w+')
            file.close()
    if not server:
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
    
    # Print jobs per site/scheduler
    for entry in sorted: 
        sum = 0.0
        lineSite = "| %25s |" % entry
        for type in jobTypes:
            lineSite += " %10s |" % int(dict[entry][type])
            sum += dict[entry][type]
            overall_type[type] += dict[entry][type]
            
            # add site/scheduler jobs per type to 'description''type' file
            file = open('./'+description+type+'.txt', 'a')
            file.write( "%s %s\t%s\t%s\t%s\t%s%s%s\n" % (date, hour, entry, str(int(dict[entry][type])), 'green', site_link, entry, endpoint_entry ))
            
        lineSite += " %10s |" % int(sum)
        
        # add site/scheduler total jobs to 'description'Total file
        file = open('./'+description+"Total"+'.txt', 'a')
        file.write( "%s %s\t%s\t%s\t%s\t%s%s%s\n" % (date, hour, entry, str(int(sum)), 'green', site_link, entry, endpoint_entry ))
        
        print lineSite
    
    # Print overalls
    overalls = "| %25s |" % 'Overalls'
    total = 0.0
    for type in jobTypes:
        total += overall_type[type]
        overalls += " %10s |" % int(overall_type[type])
        
        # add overalls to 'description''type' file
        file = open('./'+description+type+'.txt', 'a')
        file.write( "%s %s\t%s%s\t%s\t%s\t%s%s\n" % (date, hour, 'Overall', entry_overall, str(int(overall_type[type])), 'green' , overalls_link, endpoint_overall ))
        
    overalls += " %10s |" % int(total)
    file = open('./'+description+"Total"+'.txt', 'a')
    file.write( "%s %s\t%s%s\t%s\t%s\t%s%s\n" % (date, hour, 'Overall', entry_overall, str(int(total)), 'green', overalls_link, endpoint_overall ))
    print line2, '\n', overalls, '\n', line2, '\n'

def jsonDict(json_name,currTime,date,hour,key):
    """
    This creates a json form text and writes it into the json_name output file
    """
    if key == 'site':
        location = "Sites"
        running = overview_running
        pending = overview_pending
    elif key == 'VOBox':
        location = "CERN"
        running = overview_running_vobox
        pending = overview_pending_vobox
    
    sorted_run = running.keys() # Running and pending keys must be the same after fixOverviews()
    sorted_run.sort()
    
    jsonfile = open(json_name,'w+')
    update = {"UPDATE" : {"Date" : date, "Time" : hour}, location : []}
    
    for entry in sorted_run:
        # Get site/scheduler status
        s_status = 'on' # Default for sites/schedulers
        # TODO: How to get scheduler status, don't use default
        if entry in baseSiteList.keys() and key == 'site': # only when key is "site"
            s_status = baseSiteList[entry]
         
        sumPending = 0.0
        sumRunning = 0
        for type in jobTypes:
            sumPending += pending[entry][type]
            sumRunning += running[entry][type]
            
        json_entry = dict()
        json_entry[key] = str(entry)
        json_entry["Pending"] = str(int(sumPending))
        json_entry["TimeDate"] = str(currTime.strip())
        json_entry["Running"] = str(int(sumRunning))
        json_entry["RunProc"] = str(int(running[entry]['Processing']))
        json_entry["RunProd"] = str(int(running[entry]['Production']))
        json_entry["RunSkim"] = str(int(running[entry]['Skim']))
        json_entry["RunHarvest"] = str(int(running[entry]['Harvest']))
        json_entry["RunMerge"] = str(int(running[entry]['Merge']))
        json_entry["RunClean"] = str(int(running[entry]['Cleanup']))
        json_entry["RunLog"] = str(int(running[entry]['LogCollect']))
        json_entry["RunRelval"] = str(int(running[entry]['RelVal']))
        json_entry["RunT0"] = str(int(running[entry]['T0']))
        json_entry["PenProc"] = str(int(pending[entry]['Processing']))
        json_entry["PenProd"] = str(int(pending[entry]['Production']))
        json_entry["PenSkim"] = str(int(pending[entry]['Skim']))
        json_entry["PenHarvest"] = str(int(pending[entry]['Harvest']))
        json_entry["PenMerge"] = str(int(pending[entry]['Merge']))
        json_entry["PenClean"] = str(int(pending[entry]['Cleanup']))
        json_entry["PenLog"] = str(int(pending[entry]['LogCollect']))
        json_entry["PenRelval"] = str(int(pending[entry]['RelVal']))
        json_entry["PenT0"] = str(int(pending[entry]['T0']))
        json_entry["Status"] = str(s_status)
        
        update[location].append(json_entry)
              
    jsonfile.write(json.dumps(update,sort_keys=True, indent=3))
    jsonfile.close()

def send_mail(send_from, send_to, subject, text, files=[], server="localhost"):
    """
    Method to send emails
    """
    assert isinstance(send_to, list)
    assert isinstance(files, list)

    msg = MIMEMultipart()
    msg['From'] = send_from
    msg['To'] = COMMASPACE.join(send_to)
    msg['Date'] = formatdate(localtime=True)
    msg['Subject'] = subject

    msg.attach( MIMEText(text) )

    for f in files:
        part = MIMEBase('application', "octet-stream")
        part.set_payload( open(f,"rb").read() )
        Encoders.encode_base64(part)
        part.add_header('Content-Disposition', 'attachment; filename="%s"' % os.path.basename(f))
        msg.attach(part)

    smtp = smtplib.SMTP(server)
    smtp.sendmail(send_from, send_to, msg.as_string())
    smtp.close()

def set_default(obj):
    """
    JSON enconder doesnt support sets, parse them to lists
    """
    if isinstance(obj, set):
        return list(obj)
    raise TypeError

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
        schedds={}
        listcommand="condor_status -pool "+col+""" -schedd -format "%s||" Name -format "%s||" CMSGWMS_Type -format "\n" Owner"""
        proc = subprocess.Popen(listcommand, stderr = subprocess.PIPE,stdout = subprocess.PIPE, shell = True)
        out, err = proc.communicate()
        for line in err.split('\n') :
            if 'Error' in line:
                body_text = 'There is a problem with one of the collectors! The monitoring script may give false information. These are the logs:\n\n'
                body_text += err
                body_text += '\nSee the log file in this directory for more output logs:\n\n'
                body_text += '    /afs/cern.ch/user/c/cmst1/scratch0/MonitoringScripts/WFM_Input_DashBoard\n'
                send_mail(mailingSender,
                          mailingList,
                          '[Monitoring] Condor Collector %s Error' % col,
                          body_text)
                print 'ERROR: I find a problem while getting schedulers for collector %s, I will send an email to: %s' % (col, str(mailingList))
                #print out2, '\n', "Error: ", '\n', err2
                break
        for line in out.split('\n'):
            if not line: continue # remove empty lines from split('\n')
            schedd_info = line.split("||")
            # schedd_info[0] is the Schedd Name
            # schedd_info[1] is the Schedd type if available, if not is set ''
            schedds[schedd_info[0].strip()] = schedd_info[1].strip()
                
        print "INFO: Condor status on collector %s has been started" % col
        print "DEBUG: Schedulers ", schedds.keys()
        
        # Get the running/pending jobs from condor for the given scheduler
        for sched in schedds.keys():
            
            # Ignore Analysis schedulers 
            if 'crabschedd' == schedds[sched] or sched in crab_scheds or 'crab' in sched:
                print "DEBUG: Ignoring crab scheduler ", sched
                continue
            
            # Get all the jobs for the given scheduler
            command='condor_q -pool '+col+' -name ' + sched
            command=command+"""  -format "%i." ClusterID -format "%s||" ProcId  -format "%i||" JobStatus  -format "%s||" WMAgent_SubTaskName -format "%s||" DESIRED_Sites -format "%s||" MATCH_EXP_JOBGLIDEIN_CMSSite -format "\n" Owner"""
            proc = subprocess.Popen(command, stderr = subprocess.PIPE,stdout = subprocess.PIPE, shell = True)
            out, err = proc.communicate()
            print "INFO: Handling condor_q on collector: %s scheduler: %s" % (col, sched)
            
            if not sched in overview_running_vobox.keys():
                addVoBox(sched.replace(".","_"))
            
            for line in out.split('\n'):
                if not line: continue # remove empty lines from split('\n')
                
                array = line.split("||")
                if len(array) < 5: 
                    continue # ignore bad lines (incomplete info lines)
                array = fixArray(array)
                
                # array[0] ClusterID.ProcId
                # array[1] JobStatus
                # array[2] WMAgent_SubTaskName
                # array[3] DESIRED_Sites
                    # only when job is already running: array[4] MATCH_EXP_JOBGLIDEIN_CMSSite
                # array[5] ''    --> nothing
                # --> standard len(array) {5,6} depending if the job is already running in a site
                id = array[0]
                status = array[1]
                workflow = array[2].split('/')[1]
                task = array[2].split('/')[-1]
                siteToExtract = array[3].replace(' ', '').split(",")
                
                # Task Extraction
                type = findTask(id,sched,task)
                
                # Site Extraction
                # use array[5]/[4] if it is a site name (depending on new/old software)
                if siteName(array[4]):
                    siteToExtract = [array[4]]
                
                if status == "2":
                    increaseRunning(siteToExtract[0],type) # I assume one job can only run at one site
                    increaseRunningVoBox(sched.replace(".","_"),type)
                    increaseRunningWorkflow(workflow,siteToExtract[0])
                elif status == "1":
                    temp_pending.append([type,siteToExtract])
                    increasePendingVoBox(sched.replace(".","_"),type)
                    increasePendingWorkflow(workflow,siteToExtract)
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
        body_text = 'There is a problem with the logic to deduce job type from the condor data.\n'
        body_text += 'Please have a look to the following jobs:\n\n %s'% str(jobs_failedTypeLogic)
        send_mail(mailingSender,
                  mailingList,
                  '[Monitoring] Failed task type logic problem',
                  body_text)
        print 'ERROR: I find jobs that failed the type assignment logic, I will send an email to: %s' % str(mailingList)
        #print out, '\n', "Error: ", '\n', err
    
    # Adding sites not in either of running/pending overviews
    fixOverviews()
    
    print 'INFO: Creating reports...'
    
    # Prints a report and fills Dashboard feeder files (SSB can't take info from json for runnnig/pending views...)
    # This handles jobs per site. This must run before handleDict for servers (this creates *.txt files)
    handleDict( overview_running, "Running", date, hour, False)
    handleDict( overview_pending, "Pending", date, hour, False)
    
    # Prints a report for jobs per vobox and fills Dashboard feeder files (for schedulers)
    handleDict( overview_running_vobox, "Running", date, hour, True)
    handleDict( overview_pending_vobox, "Pending", date, hour, True)
    
    # Creates json file for jobs per vobox
    jsonDict( json_name_vobox, currTime, date, hour, 'VOBox')
    
    # Creates json file (This is needed for plots per site)
    jsonDict( json_name_sites, currTime, date, hour, 'site')
    
    # Creates json file for jobs per workflow
    jsonfile = open(json_name_workflows,'w+')
    jsonfile.write(json.dumps(overview_workflows, default=set_default, sort_keys=True, indent=4))
    jsonfile.close()
    
    print 'INFO: The script has finished after: ', datetime.now()-starttime

if __name__ == "__main__":
    main()