#!/data/cmssst/packages/bin/python3.9
# ########################################################################### #
# python script to query the CMS job history in ElasticSearch via the MonIT  
#    grafana front-end for HammerCloud jobs, evaluate HC site status, and
#    upload new/changed results to MonIT HDFS. The script checks/updates
#    15 min, 1 hour, 6 hour, and 1 day results, depending on the execution
#    time.
#
# 2018-Dec-19   Stephan Lammel
# ########################################################################### #
# 'data': {
#      'name':     "T1_US_FNAL",
#      'status':   "ok | warning | error | unknown",
#      'value':    0.984,
#      'detail':   "4 Success [...] [...] [...] [...]\n
#                   2 Success, %d HTCondor retries [...] ...\n
#                   1 Failed, ExitCode %s [...]\n
#                   1 Failed, GlobalPool periodic cleanup [...]\n
#                   1 Failed, %s [...]"
# }
# https://cmsweb.cern.ch/crabserver/ui/task/<CRAB Workflow>
# https://cmsweb.cern.ch/scheddmon/0122/sciaba/<CRAB Workflow>/job_out.15.0.txt
#                               <schedd#>            <CRAB_Id>.<CRAB_Retry>.txt
# globalJobId   = crab3@vocms0107.cern.ch#36373065.0#1552585123
# CRAB_Workflow = 190314_153237:sciaba_crab_HC-98-T2_AT_Vienna-72573-20190313044506
# CRAB_Id       = 25
# CRAB_Retry    = 0



import os, sys
import pwd
import argparse
import logging
import time, calendar
import socket
import ssl
import http
import urllib.request, urllib.error
import xml.etree.ElementTree
import json
import re
import gzip
import smtplib
from email.mime.text import MIMEText
import subprocess
#
# setup the Java/HDFS/PATH environment for pydoop to work properly:
os.environ["HADOOP_CONF_DIR"] = "/data/cmssst/packages/etc/hadoop.analytix.conf/hadoop.analytix"
os.environ["JAVA_HOME"]       = "/data/cmssst/packages/lib/jvm/java-11-openjdk-11.0.23.0.9-3.el9.x86_64"
os.environ["HADOOP_HOME"]     = "/data/cmssst/packages/hadoop/3.3.5-1ba16/x86_64-el9-gcc11-opt"
os.environ["LD_LIBRARY_PATH"] ="/data/cmssst/packages/hadoop/3.3.5-1ba16/x86_64-el9-gcc11-opt/lib/native"
os.environ["PATH"]            ="/data/cmssst/packages/hadoop/3.3.5-1ba16/x86_64-el9-gcc11-opt/bin:" + os.environ["PATH"]
import pydoop.hdfs
# ########################################################################### #



EVHC_SSB_DIR = "./junk"
#EVHC_SSB_DIR = "/afs/cern.ch/user/c/cmssst/www/hammercloud"
EVHC_MONIT_URL = "http://fail.cern.ch:12012/"
#EVHC_MONIT_URL = "http://monit-metrics.cern.ch:10012/"
EVHC_BACKUP_DIR = "./junk"
#EVHC_BACKUP_DIR = "/data/cmssst/MonitoringScripts/hammercloud/failed"
# ########################################################################### #



evhc_glbl_cmssites = []
    # list of CMS site names
evhc_glbl_templates = {}
    # dictionary: HC-id: {cmssites: ["", "", ...], jobs: True/Fales }
evhc_glbl_jobcondor = []
    # list of dictionaries { 'time', 'site', 'status'}
evhc_glbl_monitdocs = {}
    # dictionary: (path,timebin): [{'name', 'status', 'value', 'detail'}, ... ]
evhc_glbl_evaluations = {}
    # dictionary: (path,timebin): [{'name', 'status', 'value', 'detail'}, ... ]
# ########################################################################### #



def evhc_kerberos_check():
    """function to check we have a valid kerberos ticket"""
    # #################################################################### #
    # check lifetime of krbtgt and email in case less than an hour remains #
    # #################################################################### #
    EVHC_KRBCCFILE = "/tmp/krb5cc_%d" % os.getuid()


    # check/set Kerberos credential cache:
    # ====================================
    if 'KRB5CCNAME' not in os.environ:
        os.environ['KRB5CCNAME'] = "FILE:" + EVHC_KRBCCFILE
        logging.info("Kerberos credential cache set to %s" % EVHC_KRBCCFILE)


    # check lifetime of ticket granting ticket:
    # =========================================
    try:
        cmplProc = subprocess.run(["/usr/bin/klist", "-c"],
                                  stdout=subprocess.PIPE,
                                  stderr=subprocess.DEVNULL, timeout=3)
        cmplProc.check_returncode()
        #
        for myLine in cmplProc.stdout.decode("utf-8").split("\n"):
            myWords = myLine.split()
            if ( len(myWords) <= 4 ):
                continue
            if ( myWords[4] == "krbtgt/CERN.CH@CERN.CH" ):
                myString = myWords[2] + " " + myWords[3]
                if ( len(myString) == 17 ):
                    myTime = time.mktime(time.strptime(myString,
                                                       "%m/%d/%y %H:%M:%S"))
                elif ( len(myString) == 19 ):
                    myTime = time.mktime(time.strptime(myString,
                                                       "%m/%d/%Y %H:%M:%S"))
                else:
                    raise ValueError("bad/unknown klist time format \"%s\"" %
                                     myString)
                secLeft = int( myTime - time.time() )
                if ( secLeft <= 0 ):
                    raise TimeoutError("expired %d sec ago" % abs(secLeft))
                elif ( secLeft < 3600 ):
                    if (( secLeft > 1800 ) and (not sys.stdin.isatty())):
                        myAcnt = pwd.getpwuid(os.getuid()).pw_name
                        myNode = socket.gethostname()
                        myDate = time.strftime("%Y-%b-%d %H:%M:%S UTC",
                                                                 time.gmtime())
                        mimeObj = MIMEText(("%s [C] %s at %s: Kerberos TGT l" +
                                            "ifetime expiring in %d sec") %
                                           (myDate, myAcnt, myNode, secLeft))
                        mimeObj['Subject'] = sys.argv[0] + " Kerberos warning"
                        mimeObj['From'] = "cmssst@cern.ch"
                        mimeObj['To'] = "lammel@fnal.gov"
                        smtpConnection = smtplib.SMTP('localhost')
                        smtpConnection.sendmail(mimeObj['From'], mimeObj['To'],
                                                           mimeObj.as_string())
                        smtpConnection.quit()
                        del smtpConnection
                        del mimeObj
                    raise TimeoutError("expiring in %d sec" % secLeft)
                return True
        raise LookupError("Kerberos klist parsing")
    except Exception as excptn:
        logging.error("Kerberos TGT lifetime check failed, %s" % str(excptn))

    return False
# ########################################################################### #



def evhc_vofeed():
    """function to fetch site topology information of CMS"""
    # ######################################################### #
    # fill evhc_glbl_cmssites with list of valid CMS site names #
    # ######################################################### #
    global evhc_glbl_cmssites
    FILE_VOFEED = "/afs/cern.ch/user/c/cmssst/www/vofeed/vofeed.xml"
    URL_VOFEED = "http://dashb-cms-vo-feed.cern.ch/dashboard/request.py/cmssitemapbdii"

    # read VO-feed file and fallback to URL in case of failure:
    # =========================================================
    logging.info("Querying VO-feed for CMS site information")
    try:
        with open(FILE_VOFEED, 'r') as myFile:
            myData = myFile.read()
    except Exception as excptn:
        logging.error("Failed to read VO-feed file, %s" % str(excptn))

        try:
            with urllib.request.urlopen(URL_VOFEED) as urlHndl:
                myCharset = urlHndl.headers.get_content_charset()
                if myCharset is None:
                    myCharset = "utf-8"
                myData = urlHndl.read().decode( myCharset )
                del myCharset
        except Exception as excptn:
            logging.critical("Failed to read VO-feed URL, %s" % str(excptn))
            return False


    # unpack XML data of the VO-feed:
    # ===============================
    vofeed = xml.etree.ElementTree.fromstring( myData )
    del myData


    # loop over site elements and fill CMS sites into global list:
    # ============================================================
    for atpsite in vofeed.findall('atp_site'):
        cmssite = None
        for group in atpsite.findall('group'):
            if 'type' in group.attrib:
                if ( group.attrib['type'] == "CMS_Site" ):
                    cmssite = group.attrib['name']
                    break
        if cmssite is None:
            continue;
        #
        if cmssite not in evhc_glbl_cmssites:
            evhc_glbl_cmssites.append( cmssite )

    # sanity check:
    cnt_t0 = 0
    cnt_t1 = 0
    cnt_t2 = 0
    cnt_t3 = 0
    for cmssite in evhc_glbl_cmssites:
        if ( cmssite[0:3] == "T3_" ):
            cnt_t3 += 1
        elif ( cmssite[0:3] == "T2_" ):
            cnt_t2 += 1
        elif ( cmssite[0:3] == "T1_" ):
            cnt_t1 += 1
        elif ( cmssite[0:3] == "T0_" ):
            cnt_t0 += 1
    if (( cnt_t0 < 1 ) or ( cnt_t1 < 5 ) or ( cnt_t2 < 35 ) or ( cnt_t3 < 24 )):
        logging.critical("Too few sites in VO-feed, %d/%d/%d/%d" %
                         (cnt_t0, cnt_t1, cnt_t2, cnt_t3))
        return False

    logging.info("   %d/%d/%d/%d CMS sites" % (cnt_t0, cnt_t1, cnt_t2, cnt_t3))
    return True
# ########################################################################### #



def evhc_template_cfg():
    """function to fetch Hammer Cloud template configuration of CMS"""
    # ##################################################################### #
    # fill evhc_glbl_templates with CMS site information and init jobs flag #
    # ##################################################################### #
    global evhc_glbl_templates
    URL_TEMPLATE = "https://hc-ai-core.cern.ch/testdirs/cms/cms.templates.json"


    # fetch template configuration from Hammer Cloud server:
    # =========================================================
    logging.info("Fetching template configuration from HammerCloud")
    try:
        urlRequest = urllib.request.Request(URL_TEMPLATE,
                                         headers={'Accept':'application/json'})
        with urllib.request.urlopen( urlRequest ) as urlHandle:
            urlCharset = urlHandle.headers.get_content_charset()
            if urlCharset is None:
                urlCharset = "utf-8"
            myData = urlHandle.read().decode( urlCharset )
            del urlCharset
        #
        # sanity check:
        if ( len(myData) < 1024 ):
            raise IOError("HammerCloud template config failed sanity check")
    except Exception as excptn:
        logging.critical("Failed to fetch HammerCloud template config, %s" %
                                                                   str(excptn))
        return


    # unpack JSON:
    # ============
    hcConf = json.loads( myData )
    del myData


    # use is_golden flagged templates in case of empty template list:
    # ===============================================================
    if ( len( evhc_glbl_templates ) == 0 ):
        for tmpltID in hcConf:
            try:
                if ( hcConf[tmpltID]['is_golden'] == True ):
                    evhc_glbl_templates[tmpltID] = {}
            except KeyError as excptn:
                logging.warning("Incomplete template dictionary, id=%s, %s" %
                                                        (tmpltID, str(excptn)))


    # loop over predefined template ids and fill site list and jobs flag:
    # ===================================================================
    for tmpltID in evhc_glbl_templates:
        try:
            for myEntry in hcConf[tmpltID]['dependencies::TemplateSite.site']:
                try:
                    mySite = myEntry['name']
                    if ( mySite not in evhc_glbl_cmssites ):
                        continue
                    #
                    if ( 'cmssites' not in evhc_glbl_templates[ tmpltID ] ):
                        evhc_glbl_templates[ tmpltID ]['cmssites'] = set()
                    evhc_glbl_templates[ tmpltID ]['cmssites'].add( mySite )
                    evhc_glbl_templates[ tmpltID ]['jobs'] = False
                except KeyError as excptn:
                    logging.warning("Incomplete template site entry, id=%s, %s"
                                                      % (tmpltID, str(excptn)))
        except KeyError as excptn:
            logging.warning("Incomplete template dictionary, id=%s, %s" %
                                                        (tmpltID, str(excptn)))

    myCnt = 0
    for tmpltID in evhc_glbl_templates:
        if ( 'cmssites' in evhc_glbl_templates[ tmpltID ] ):
            evhc_glbl_templates[ tmpltID ]['cmssites'] = \
                           sorted( evhc_glbl_templates[ tmpltID ]['cmssites'] )
            myCnt += len( evhc_glbl_templates[ tmpltID ]['cmssites'] )
    logging.info("   %d CMS sites in HC template config" % myCnt)
    return
# ########################################################################### #



def evhc_grafana_jobs(startTIS, limitTIS):
    """function to fetch HammerCloud HTCondor job records via Grafana"""
    # ############################################################# #
    # fill global HTCondor list with job records from ElasticSearch #
    # ############################################################# #
    global evhc_glbl_jobcondor
    URL_GRAFANA = "https://monit-grafana.cern.ch/api/datasources/proxy/8787/_msearch"
    HDR_GRAFANA = {'Authorization': "Bearer eyJrIjxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxjoxMX0=", 'Content-Type': "application/json; charset=UTF-8"}
    #
    logging.info("Fetching job records via Grafana, %d (%s) to %d (%s)" %
                 (startTIS, time.strftime("%Y-%m-%d %H:%M",
                                          time.gmtime(startTIS)),
                  limitTIS, time.strftime("%Y-%m-%d %H:%M",
                                          time.gmtime(limitTIS))))


    # prepare Lucene ElasticSearch query:
    # ===================================
    queryString = ("{\"search_type\":\"query_then_fetch\",\"index\":[\"monit" +
                   "_prod_condor_raw_metric*\"]}\n{\"query\":{\"bool\":{\"mu" +
                   "st\":[{\"match_phrase\":{\"data.metadata.spider_source\"" +
                   ":\"condor_history\"}},{\"match_phrase\":{\"data.CRAB_Use" +
                   "rHN\":\"sciaba\"}}],\"filter\":{\"range\":{\"data.Record" +
                   "Time\":{\"gte\":%d,\"lt\":%d,\"format\":\"epoch_second\"" +
                   "}}}}},\"_source\":{\"includes\":[\"data.GlobalJobId\",\"" +
                   "data.Site\",\"data.Status\",\"data.NumRestarts\",\"data." +
                   "RemoveReason\",\"data.Chirp_CRAB3_Job_ExitCode\",\"data." +
                   "ExitCode\",\"data.CRAB_Workflow\",\"data.CRAB_Id\",\"dat" +
                   "a.CRAB_Retry\",\"data.RecordTime\"]},\"track_total_hits" +
                   "\":true,\"size\":8192,\"search_after\":[%%d],\"sort\":[{" +
                   "\"data.RecordTime\":\"asc\"}]}\n") % (startTIS, limitTIS)

    # prepare regular expression for HammerCloud CRAB workflow name match:
    # ====================================================================
    wfRegex = \
        re.compile(r"^\d+_\d+:\w+_crab_HC-(\d+)-(T\d_[A-Z]{2,2}_\w+)-\d+-\d+$")

    # loop and fetch 10k docs at a time to get around ElasticSearch limit:
    # ====================================================================
    nHitsHdr = None
    nHitsCnt = 0
    afterTImS = 0
    while ( afterTImS < limitTIS * 1000 ):
        #
        # fetch chunk job records from ElasticSearch:
        # ===========================================
        try:
            requestObj = urllib.request.Request(URL_GRAFANA,
                         data=(queryString % afterTImS).encode("utf-8"),
                         headers=HDR_GRAFANA, method="POST")
            responseObj = urllib.request.urlopen( requestObj, timeout=60 )
            #
            myCharset = responseObj.headers.get_content_charset()
            if myCharset is None:
                myCharset = "utf-8"
            myData = responseObj.read().decode( myCharset )
            del myCharset
            responseObj.close()
        except urllib.error.URLError as excptn:
            logging.error("Failed to query ElasticSearch via Grafana, %s" %
                          str(excptn))
            return
        logging.log(15, "   ES chunk starting at %d (%s) retrieved" %
                        (afterTImS, time.strftime("%Y-%m-%d %H:%M:%S",
                                            time.gmtime(int(afterTImS/1000)))))

        # unpack response JSON data:
        # ==========================
        jobrecords = json.loads( myData )
        del myData

        # fill job records into global HTCondor list:
        # ===========================================
        previous_TImS = None
        for response in jobrecords['responses']:
            try:
                if nHitsHdr is None:
                    nHitsHdr = response['hits']['total']['value']
                elif ( nHitsHdr != response['hits']['total']['value'] ):
                    logging.warning("Changed job record count, %d versus %d" %
                                (nHitsHdr, response['hits']['total']['value']))
                lastTImS = response['hits']['hits'][-1] \
                                   ['_source']['data']['RecordTime']

                for hit in response['hits']['hits']:
                    try:
                        hitData = hit['_source']['data']
                        currentTImS = hitData['RecordTime']
                        if (( currentTImS == lastTImS ) and
                            ( previous_TImS is not None )):
                            break;
                        CRABworkflow = hitData['CRAB_Workflow']
                        nHitsCnt += 1
                        matchObj = wfRegex.match(CRABworkflow)
                        if matchObj is not None:
                            status = None
                            tmpltID = matchObj.group(1)
                            siteName = matchObj.group(2)
                            if (( tmpltID not in evhc_glbl_templates ) or
                                ( siteName not in evhc_glbl_cmssites )):
                                pass
                            elif ( hitData['Status'] == "Completed" ):
                                evhc_glbl_templates[ tmpltID ]['jobs'] = True
                                if 'Site' not in hitData:
                                   hitData['Site'] == ""
                                if ((( hitData['Site'] != "Unknown" ) and
                                     ( hitData['Site'] != "-" ) and
                                     ( hitData['Site'] != "" )) and
                                    ( hitData['Site'] != siteName )):
                                    logging.error(("Job %s executed at wrong" +
                                                   " site, %s, workflow %s") %
                                                  (hitData['GlobalJobId'],
                                                   hitData['Site'],
                                                   CRABworkflow))
                                elif 'Chirp_CRAB3_Job_ExitCode' in hitData:
                                    eCode = hitData['Chirp_CRAB3_Job_ExitCode']
                                    try:
                                        nRestart = hitData['NumRestarts']
                                    except KeyError:
                                        nRestart = 0
                                    if (( eCode == 0 ) and ( nRestart == 0 )):
                                        status = "Success"
                                    elif ( eCode == 0 ):
                                        status = ("Success, %d HTCondor retr" +
                                                  "ies") % nRestart
                                    else:
                                        status = "Failed, ExitCode %s" % eCode
                                elif 'ExitCode' in hitData:
                                    eCode = hitData['ExitCode']
                                    if ( eCode == 0 ):
                                        # stage-out or HTCondor Chirp failure
                                        status = "Success, no Chirp ExitCode"
                                    else:
                                        status = "Failed, ExitCode %s" % eCode
                                else:
                                    logging.error(("Job %s completed at %s w" +
                                                   "ithout ExitCode") %
                                                  (hitData['GlobalJobId'],
                                                   hitData['Site']))
                            elif ( hitData['Status'] == "Removed" ):
                                evhc_glbl_templates[ tmpltID ]['jobs'] = True
                                try:
                                    rReason = hitData['RemoveReason']
                                    if ( rReason.find("condor_rm") != -1 ):
                                        # job cancelled by HammerCloud itself
                                        pass
                                    elif ( rReason.find("ython-initiated action") != -1 ):
                                        # job cancelled by HammerCloud itself
                                        pass
                                    elif ( rReason.find("due to proxy expiration") != -1 ):
                                        # HammerCloud certificate issue
                                        pass
                                    elif ( rReason.find("SYSTEM_PERIODIC_REMOVE") != -1 ):
                                        status = "Failed, GlobalPool periodic cleanup"
                                    else:
                                        status = "Failed, %s" % rReason
                                except KeyError:
                                    logging.error(("Job %s for %s removed wi" +
                                                   "thout HTCondor RemoveRea" +
                                                   "son") %
                                                  (hitData['GlobalJobId'],
                                                   siteName))
                            else:
                                evhc_glbl_templates[ tmpltID ]['jobs'] = True
                                try:
                                    eCode = hitData['Chirp_CRAB3_Job_ExitCode']
                                    try:
                                        nRestart = hitData['NumRestarts']
                                    except KeyError:
                                        nRestart = 0
                                    if (( eCode == 0 ) and ( nRestart == 0 )):
                                        status = "Success"
                                    elif ( eCode == 0 ):
                                        status = ("Success, %d HTCondor retr" +
                                                  "ies") % nRestart
                                    else:
                                        status = "Failed, ExitCode %s" % eCode
                                except KeyError:
                                    try:
                                        eCode = hitData['ExitCode']
                                        if ( eCode == 0 ):
                                            # stage-out/HTCondor Chirp failure
                                            status = ("Success, no Chirp Exi" +
                                                      "tCode")
                                        else:
                                            status = "Failed, ExitCode %s" % \
                                                     eCode
                                    except KeyError:
                                        pass
                                logging.warning(("Job %s for site %s with st" +
                                                 "atus %s") %
                                                (hitData['GlobalJobId'],
                                                 siteName, hitData['Status']))
                            if status is not None:
                                refid = "%s %s %s %s" % \
                                        (hitData['GlobalJobId'], CRABworkflow,
                                     hitData['CRAB_Id'], hitData['CRAB_Retry'])
                                #
                                evhc_glbl_jobcondor.append(
                                     { 'time': int(hitData['RecordTime']/1000),
                                       'site': siteName,
                                       'status': status,
                                       'refid': refid} )
                                logging.log(9, "      adding %s %s %s (%s)" %
                                               (time.strftime("%Y-%m-%d %H:%M",
                                                              time.gmtime(
                                             int(hitData['RecordTime']/1000))),
                                     siteName, status, hitData['GlobalJobId']))
                        if ( currentTImS != lastTImS ):
                            previous_TImS = currentTImS
                    except KeyError:
                        logging.error("No or incomplete job record in query " +
                                      "hit")
            except KeyError:
                logging.error("No query hits keys in ElasticSearch response")

        # prepare for next query:
        # =======================
        if previous_TImS is not None:
            afterTImS = previous_TImS
        else:
            break

    # double check we have all job records:
    # =====================================
    if ( nHitsCnt != nHitsHdr ):
        logging.error("Incomplete job records, %d Header versus %d Hit Count" %
                      (nHitsHdr, nHitsCnt))

    logging.info("   %d matching job records found" % len(evhc_glbl_jobcondor))
    return
# ########################################################################### #



def evhc_monit_fetch(tbins15m, tbins1h, tbins6h, tbins1d):
    """function to fetch HammerCloud metric docs from MonIT/HDFS"""
    # ###################################################################### #
    # fill global document list with HammerCloud metric documents from MonIT #
    # ###################################################################### #
    global evhc_glbl_monitdocs
    PATH_HDFS_PREFIX = "/project/monitoring/archive/cmssst/raw/ssbmetric/"

    # prepare HDFS subdirectory list:
    # ===============================
    logging.info("Retrieving HammerCloud metric docs from MonIT HDFS")
    #
    tisDay = 24*60*60
    now = int( time.time() )
    startTmpArea = calendar.timegm( time.gmtime( now - (6 * tisDay) ) )
    limitLocalTmpArea = calendar.timegm( time.localtime( now ) ) + tisDay
    #
    dirList = []
    #
    if ( len(tbins15m) > 0 ):
        logging.log(15, "   15 min time bins %d (%s), ..., %d (%s)" %
                        (tbins15m[0], time.strftime("%Y-%b-%d %H:%M",
                                                 time.gmtime(tbins15m[0]*900)),
                         tbins15m[-1], time.strftime("%Y-%b-%d %H:%M",
                                               time.gmtime(tbins15m[-1]*900))))
        for tbin in tbins15m:
            dirString = time.strftime("hc15min/%Y/%m/%d",
                                      time.gmtime( tbin * 900 ))
            if dirString not in dirList:
                dirList.append( dirString )
        for dirDay in range(startTmpArea, limitLocalTmpArea, tisDay):
            dirList.append( time.strftime("hc15min/%Y/%m/%d.tmp",
                                          time.gmtime( dirDay )) )
    #
    if ( len(tbins1h) > 0 ):
        logging.log(15, "   1 hour time bins %d (%s), ..., %d (%s)" %
                        (tbins1h[0], time.strftime("%Y-%b-%d %H:%M",
                                                 time.gmtime(tbins1h[0]*3600)),
                         tbins1h[-1], time.strftime("%Y-%b-%d %H:%M",
                                               time.gmtime(tbins1h[-1]*3600))))
        for tbin in tbins1h:
            dirString = time.strftime("hc1hour/%Y/%m/%d",
                                      time.gmtime( tbin * 3600 ))
            if dirString not in dirList:
                dirList.append( dirString )
        for dirDay in range(startTmpArea, limitLocalTmpArea, tisDay):
            dirList.append( time.strftime("hc1hour/%Y/%m/%d.tmp",
                                          time.gmtime( dirDay )) )
    if ( len(tbins6h) > 0 ):
        logging.log(15, "   6 hour time bins %d (%s), ..., %d (%s)" %
                        (tbins6h[0], time.strftime("%Y-%b-%d %H:%M",
                                                time.gmtime(tbins6h[0]*21600)),
                         tbins6h[-1], time.strftime("%Y-%b-%d %H:%M",
                                              time.gmtime(tbins6h[-1]*21600))))
        for tbin in tbins6h:
            dirString = time.strftime("hc6hour/%Y/%m/%d",
                                      time.gmtime( tbin * 21600 ))
            if dirString not in dirList:
                dirList.append( dirString )
        for dirDay in range(startTmpArea, limitLocalTmpArea, tisDay):
            dirList.append( time.strftime("hc6hour/%Y/%m/%d.tmp",
                                          time.gmtime( dirDay )) )
    if ( len(tbins1d) > 0 ):
        logging.log(15, "   1 day  time bins %d (%s), ..., %d (%s)" %
                        (tbins1d[0], time.strftime("%Y-%b-%d %H:%M",
                                                time.gmtime(tbins1d[0]*86400)),
                         tbins1d[-1], time.strftime("%Y-%b-%d %H:%M",
                                              time.gmtime(tbins1d[-1]*86400))))
        for tbin in tbins1d:
            dirString = time.strftime("hc1day/%Y/%m/%d",
                                      time.gmtime( tbin * 86400 ))
            if dirString not in dirList:
                dirList.append( dirString )
        for dirDay in range(startTmpArea, limitLocalTmpArea, tisDay):
            dirList.append( time.strftime("hc1day/%Y/%m/%d.tmp",
                                          time.gmtime( dirDay )) )
    if ( len(dirList) == 0 ):
        return
    del dirDay

    tmpDict = {}
    try:
        with pydoop.hdfs.hdfs() as myHDFS:
            fileHndl = None
            fileObj = None
            fileName = None
            fileNames = None
            for subDir in dirList:
                logging.debug("   checking HDFS subdirectory %s" % subDir)
                if not myHDFS.exists( PATH_HDFS_PREFIX + subDir ):
                    continue
                # get list of files in directory:
                myList = myHDFS.list_directory( PATH_HDFS_PREFIX + subDir )
                fileNames = [ d['name'] for d in myList
                          if (( d['kind'] == "file" ) and ( d['size'] != 0 )) ]
                del myList
                for fileName in fileNames:
                    logging.debug("   file %s" % os.path.basename(fileName))
                    fileHndl = None
                    fileObj  = None
                    try:
                        if ( os.path.splitext(fileName)[-1] == ".gz" ):
                            fileHndl = myHDFS.open_file(fileName)
                            fileObj = gzip.GzipFile(fileobj=fileHndl)
                        else:
                            fileObj = myHDFS.open_file(fileName)
                        # read documents and add relevant records to list:
                        for myLine in fileObj:
                            myJson = json.loads(myLine.decode('utf-8'))
                            if (( 'metadata' not in myJson ) or
                                ( 'data' not in myJson )):
                                continue
                            if ( "monit_hdfs_path" not in myJson['metadata'] ):
                                if ( "path" in myJson['metadata'] ):
                                    myJson['metadata']['monit_hdfs_path'] = \
                                                     myJson['metadata']['path']
                                else:
                                    continue
                            if (( 'timestamp' not in myJson['metadata'] ) or
                                ( 'kafka_timestamp' not in myJson['metadata'] ) or
                                (( 'name' not in myJson['data'] ) and
                                 ( 'site' not in myJson['data'] )) or
                                ( 'status' not in myJson['data'] )):
                                continue
                            tis = int(myJson['metadata']['timestamp']/1000)
                            if ( myJson['metadata']['monit_hdfs_path'] ==
                                                                   "hc15min" ):
                                tbin = int( tis / 900 )
                                if tbin not in tbins15m:
                                    continue
                            elif ( myJson['metadata']['monit_hdfs_path'] ==
                                                                   "hc1hour" ):
                                tbin = int( tis / 3600 )
                                if tbin not in tbins1h:
                                    continue
                            elif ( myJson['metadata']['monit_hdfs_path'] ==
                                                                   "hc6hour" ):
                                tbin = int( tis / 21600 )
                                if tbin not in tbins6h:
                                    continue
                            elif ( myJson['metadata']['monit_hdfs_path'] ==
                                                                    "hc1day" ):
                                tbin = int( tis / 86400 )
                                if tbin not in tbins1d:
                                    continue
                            else:
                                    continue
                            #
                            if 'name' not in myJson['data']:
                                myJson['data']['name'] = myJson['data']['site']
                            if 'value' not in myJson['data']:
                                myJson['data']['value'] = None
                            if 'detail' not in myJson['data']:
                                myJson['data']['detail'] = None
                            #
                            version = myJson['metadata']['kafka_timestamp']
                            #
                            key = ( myJson['metadata']['monit_hdfs_path'],
                                    tbin,
                                    myJson['data']['name'] )
                            val = { 'v': version,
                                    'd': myJson['data'] }
                            if key in tmpDict:
                                if ( version <= tmpDict[key]['v'] ):
                                    continue
                            #
                            tmpDict[key] = val

                    except json.decoder.JSONDecodeError as excptn:
                        logging.error("JSON decoding failure, file %s: %s" %
                                                       (fileName, str(excptn)))
                    except FileNotFoundError as excptn:
                        logging.error("HDFS file not found, %s: %s" %
                                                       (fileName, str(excptn)))
                    except IOError as excptn:
                        logging.error("HDFS access failure, file %s: %s" %
                                                       (fileName, str(excptn)))
                    finally:
                        if fileObj is not None:
                            fileObj.close()
                        if fileHndl is not None:
                            fileHndl.close()
            del fileHndl
            del fileObj
            del fileName
            del fileNames
    except:
        logging.error("Failed to fetch CMS HC metric docs from MonIT HDFS")

    # convert temporary dictionary into global dictionary of arrays:
    for longKey in tmpDict:
        shortKey = ( longKey[0], longKey[1] )
        if shortKey not in evhc_glbl_monitdocs:
            evhc_glbl_monitdocs[shortKey] = []
        evhc_glbl_monitdocs[shortKey].append( tmpDict[longKey]['d'] )
        logging.log(9, "      adding %s (%d) of %s" %
                       (longKey[0], longKey[1], longKey[2]))
    #
    logging.info("   found %d relevant CMS HC metric docs in MonIT" %
                 len(tmpDict))
    del tmpDict
    #
    return
# ########################################################################### #



def evhc_evaluate_sites(metric, timebin):
    """function to evaluate HammerCloud site status for a given time bin"""
    # ############################################################# #
    # fill global HC evaluation with site status of metric/time bin #
    # ############################################################# #
    global evhc_glbl_evaluations
    myKey = (metric, timebin)

    # time bin boundaries:
    # ====================
    if ( metric == "hc15min" ):
        startTIS = timebin * 900
        limitTIS = startTIS + 900
    elif ( metric == "hc1hour" ):
        startTIS = timebin * 3600
        limitTIS = startTIS + 3600
    elif ( metric == "hc6hour" ):
        startTIS = timebin * 21600
        limitTIS = startTIS + 21600
    elif ( metric == "hc1day" ):
        startTIS = timebin * 86400
        limitTIS = startTIS + 86400
    else:
        logging.error("HC evaluation for \"%s\" not implemented" % metric)
        return
    logging.info("Evaluating HC site status \"%s\" %d (%s)" %
                 (metric, timebin, time.strftime("%Y-%b-%d %H:%M",
                                                 time.gmtime(startTIS))))

    # loop over global HTCondor list and count the various stati of HC jobs:
    # ======================================================================
    hc_evals = {}
    for jobRec in evhc_glbl_jobcondor:
        if ( jobRec['time'] < startTIS ):
            continue
        if ( jobRec['time'] >= limitTIS ):
            continue
        site = jobRec['site']
        if site not in hc_evals:
            hc_evals[ site ] = {}
        status = jobRec['status']
        if status not in hc_evals[ site ]:
            hc_evals[ site ][ status ] = {}
            hc_evals[ site ][ status ]['cnt'] = 1
            hc_evals[ site ][ status ]['jobs'] = []
        else:
            hc_evals[ site ][ status ]['cnt'] += 1
        try:
            hc_evals[ site ][ status ]['jobs'].append( jobRec['refid'] )
        except KeyError:
            pass
        logging.log(9, "   counting job of %s at %d with %s" %
                    (site, jobRec['time'], status))


    siteSet = set( hc_evals.keys() )
    for tmpltID in evhc_glbl_templates:
        if (( 'cmssites' in evhc_glbl_templates[ tmpltID ] ) and
            ( evhc_glbl_templates[ tmpltID ]['jobs'] == True )):
            siteSet.update( evhc_glbl_templates[ tmpltID ]['cmssites'] )


    # loop over sites and evaluate status:
    # ====================================
    counts = [0, 0, 0, 0]
    for site in sorted( siteSet ):
        successJobs = 0
        totalJobs = 0
        detail = ""
        if site in hc_evals:
            for status in hc_evals[ site ]:
                if ( status[0:7] == "Success" ):
                    successJobs += hc_evals[ site ][ status ]['cnt']
                totalJobs += hc_evals[ site ][ status ]['cnt']
                if ( len(detail) != 0 ):
                    detail += "\n%d %s" % \
                                    (hc_evals[ site ][ status ]['cnt'], status)
                else:
                    detail += "%d %s" % \
                                    (hc_evals[ site ][ status ]['cnt'], status)
                for refid in hc_evals[ site ][ status ]['jobs']:
                    detail += " [%s]" % refid
                    if ( metric != "hc15min" ):
                        detail += "..."
                        break
        if ( totalJobs <= 0 ):
            value = None
            status = "unknown"
            counts[0] += 1
            logging.debug("   site %s: %d jobs, value None, status %s" %
                          (site, totalJobs, status))
        else:
            value = round(successJobs / totalJobs, 3)
            if ( value >= 0.900 ):
                status = "ok"
                counts[1] += 1
            elif ( value < 0.800 ):
                status = "error"
                counts[3] += 1
            else:
                tier = site[1:2]
                if (( tier == "0" ) or ( tier == "1" )):
                    status = "error"
                    counts[3] += 1
                else:
                    status = "warning"
                    counts[2] += 1
            logging.log(15, "   site %s: %d / %d jobs, value %.3f, status %s" %
                        (site, successJobs, totalJobs, value, status))
        if myKey not in evhc_glbl_evaluations:
            evhc_glbl_evaluations[ myKey ] = []
        evhc_glbl_evaluations[ myKey ].append( {'name': site,
                                                'status': status,
                                                'value': value,
                                                'detail': detail} )

    del hc_evals
    logging.info("   HC results: %d ok, %d warning, %d error, %d unknown" %
                 (counts[1], counts[2], counts[3], counts[0]))
    return
# ########################################################################### #



def evhc_compose_json():
    """function to compose a JSON string from the global evaluations"""
    # ########################################################### #
    # compose a JSON string from results in evhc_glbl_evaluations #
    # ########################################################### #

    # convert global evaluation dictionary into JSON document array string:
    # =====================================================================
    jsonString = "["
    commaFlag = False
    #
    for metric in ["hc15min", "hc1hour", "hc6hour", "hc1day"]:
        if ( metric == "hc15min" ):
           interval = 900
        elif ( metric == "hc1hour" ):
           interval = 3600
        elif ( metric == "hc6hour" ):
           interval = 21600
        else:
           interval = 86400
        #
        for timebin in sorted([ t[1] for t in evhc_glbl_evaluations
                                                          if t[0] == metric ]):
            #logging.log(9, "   %s for %d (%s)" %
            #              (metric, timebin, time.strftime("%Y-%b-%d %H:%M:%S",
            #                                  time.gmtime(timebin*interval))))
            key = (metric, timebin)
            hdrString = ((",\n {\n   \"producer\": \"cmssst\",\n" +
                                 "   \"type\": \"ssbmetric\",\n" +
                                 "   \"monit_hdfs_path\": \"%s\",\n" +
                                 "   \"timestamp\": %d,\n" +
                                 "   \"type_prefix\": \"raw\",\n" +
                                 "   \"data\": {\n") %
                          (metric, ((timebin*interval) + (interval/2)) * 1000))
            #
            for result in sorted(evhc_glbl_evaluations[ key ],
                                 key=lambda k: k['name']):
                #logging.log(9, "      %s status: %s" % (result['name'],
                #                                            result['status']))
                if commaFlag:
                    jsonString += hdrString
                else:
                    jsonString += hdrString[1:]
                jsonString += (("      \"name\": \"%s\",\n" +
                                "      \"status\": \"%s\",\n") %
                               (result['name'], result['status']))
                if result['value'] is not None:
                    jsonString += ("      \"value\": %.3f,\n" %
                                   result['value'])
                else:
                    jsonString += "      \"value\": null,\n"
                if result['detail'] is not None:
                    jsonString += ("      \"detail\": \"%s\"\n   }\n }" %
                                   result['detail'].replace('\n','\\n'))
                else:
                    jsonString += "      \"detail\": null\n   }\n }"
                commaFlag = True
    jsonString += "\n]\n"

    return jsonString



def evhc_monit_upload():
    """function to upload CMS HC site status to MonIT/HDFS"""
    # ############################################################## #
    # upload evhc_glbl_evaluations as JSON metric documents to MonIT #
    # ############################################################## #
    EVHC_MONIT_HDR = {'Content-Type': "application/json; charset=UTF-8"}
    #
    logging.info("Composing JSON array and uploading to MonIT")


    # compose JSON array string:
    # ==========================
    jsonString = evhc_compose_json()
    if ( jsonString == "[\n]\n" ):
        logging.warning("skipping upload of document-devoid JSON string")
        return False
    cnt_15min = jsonString.count("\"monit_hdfs_path\": \"hc15min\"")
    cnt_1hour = jsonString.count("\"monit_hdfs_path\": \"hc1hour\"")
    cnt_6hour = jsonString.count("\"monit_hdfs_path\": \"hc6hour\"")
    cnt_1day  = jsonString.count("\"monit_hdfs_path\": \"hc1day\"")
    #
    jsonString = jsonString.replace("ssbmetric", "metrictest")


    # upload string with JSON document array to MonIT/HDFS:
    # =====================================================
    docs = json.loads(jsonString)
    ndocs = len(docs)
    successFlag = True
    for myOffset in range(0, ndocs, 2048):
        # MonIT upload channel can handle at most 10,000 docs at once
        dataString = json.dumps( docs[myOffset:min(ndocs,myOffset+2048)] )
        #
        try:
            # MonIT needs a document array and without newline characters:
            requestObj = urllib.request.Request(EVHC_MONIT_URL,
                         data=dataString.encode("utf-8"),
                         headers=EVHC_MONIT_HDR, method="POST")
            responseObj = urllib.request.urlopen( requestObj, timeout=90 )
            if ( responseObj.status != http.HTTPStatus.OK ):
                logging.error(("Failed to upload JSON [%d:%d] string to MonI" +
                               "T, %d \"%s\"") %
                              (myOffset, min(ndocs,myOffset+2048),
                               responseObj.status, responseObj.reason))
                successFlag = False
            responseObj.close()
        except urllib.error.URLError as excptn:
            logging.error("Failed to upload JSON [%d:%d], %s" %
                             (myOffset, min(ndocs,myOffset+2048), str(excptn)))
    del docs

    if ( successFlag ):
        logging.log(25, ("JSON string with %d(15m)/%d(1h)/%d(6h)/%d(1d) docs" +
                         " uploaded to MonIT") %
                        (cnt_15min, cnt_1hour, cnt_6hour, cnt_1day))
    return successFlag



def evhc_monit_write(filename=None):
    """function to write CMS HC site status JSON to a file"""
    # ############################################################## #
    # write evhc_glbl_evaluations as JSON metric documents to a file #
    # ############################################################## #

    if filename is None:
        filename = "%s/eval_hc_%s.json" % (EVHC_BACKUP_DIR,
                                    time.strftime("%Y%m%d%H%M", time.gmtime()))
    logging.info("Writing JSON array to file %s" % filename)

    # compose JSON array string:
    # ==========================
    jsonString = evhc_compose_json()
    if ( jsonString == "[\n]\n" ):
        logging.warning("skipping writing of document-devoid JSON string")
        return False
    cnt_docs = jsonString.count("\"producer\": \"cmssst\"")


    # write string to file:
    # =====================
    try:
        with open(filename, 'w') as myFile:
            myFile.write( jsonString )
        logging.log(25, "JSON array with %d docs written to file" % cnt_docs)
    except OSError as excptn:
        logging.error("Failed to write JSON array, %s" % str(excptn))

    return
# ########################################################################### #



def evhc_compose_ssb(tuple):
    """function to compose an SSB metric string from the global evaluations"""
    # ################################################################## #
    # compose an SSB metric string from results in evhc_glbl_evaluations #
    # ################################################################## #
    if ( tuple[0] == "hc15min" ):
       interval = 900
       label = "15 Minutes"
    elif ( tuple[0] == "hc1hour" ):
       interval = 3600
       label = "1 Hour"
    elif ( tuple[0] == "hc6hour" ):
       interval = 21600
       label = "6 Hours"
    else:
       interval = 86400
       label = "1 Day"
    #
    now = time.strftime("%Y-%b-%d %H:%M:%S UTC", time.gmtime())
    #
    #startUTC = time.strftime("%Y-%m-%d+%H:%M", time.gmtime(tuple[1] *interval))
    #endUTC   = time.strftime("%Y-%m-%d+%H:%M",
    #                                    time.gmtime((tuple[1] + 1) * interval))
    #URL_JOB_DASHBOARD = "http://dashb-cms-job.cern.ch/dashboard/templates/web-job2/#user=&refresh=0&table=Jobs&p=1&records=25&activemenu=0&usr=&site=%%s&submissiontool=&application=&activity=hctest&status=&check=terminated&tier=&date1=%s&date2=%s&sortby=ce&scale=linear&bars=20&ce=&rb=&grid=&jobtype=&submissionui=&dataset=&submissiontype=&task=&subtoolver=&genactivity=&outputse=&appexitcode=&accesstype=" % (startUTC, endUTC)
    #
    URL_JOB_DASHBOARD = "https://monit-grafana.cern.ch/d/cmsTMGlobal/cms-tasks-monitoring-globalview?orgId=11&from=%d000&to=%d000&var-user=sciaba&var-site=All&var-task=All&var-Filters=data.CRAB_Workflow|=~|.*-%%s-.*" % ((tuple[1] *interval), ((tuple[1] + 1) * interval))


    # convert list in global evaluation dictionary into an SSB metric string:
    # =======================================================================
    ssbString = ("#txt\n#\n# Site Support Team, HammerCloud %s Metric\n#    " +
                 "written at %s by %s\n#    in account %s on node %s\n#    m" +
                 "aintained by cms-comp-ops-site-support-team@cern.ch\n#    " +
                 "https://twiki.cern.ch/twiki/bin/view/CMSPublic/CMSHammerCl" +
                 "oud\n# ===================================================" +
                 "=============\n#\n") % (label, now, sys.argv[0],
                       pwd.getpwuid(os.getuid()).pw_name, socket.gethostname())
    #
    timeStrng = time.strftime("%Y-%m-%d %H:%M:%S",
                                               time.gmtime(tuple[1] *interval))
    #
    for result in sorted(evhc_glbl_evaluations[ tuple ],
                         key=lambda k: k['name']):
        if result['value'] is not None:
            value = result['value'] * 100.0
        else:
            value = -1.0
        if ( result['status'] == "ok" ):
            colour = "green"
        elif ( result['status'] == "warning" ):
            colour = "yellow"
        elif ( result['status'] == "error" ):
            colour = "red"
        else:
            colour = "white"
        url = URL_JOB_DASHBOARD % result['name']
        #
        ssbString += "%s\t%s\t%.1f\t%s\t%s\n" % (timeStrng, result['name'],
                                                            value, colour, url)

    return ssbString



def evhc_ssb_write(tuple, filename=None):
    """function to write CMS HC site status SSB metric to a file"""
    # ########################################################## #
    # write evhc_glbl_evaluations[tuple] as SSB metric to a file #
    # ########################################################## #

    if filename is None:
        filename = "%s/%s.txt" % (EVHC_SSB_DIR, tuple[0])
    logging.info("Writing SSB metric for %d to file %s" % (tuple[1], filename))

    # compose SSB metric string:
    # ==========================
    ssbString = evhc_compose_ssb(tuple)
    cnt_docs = ssbString.count("0\tT")
    if ( cnt_docs <= 0 ):
        logging.warning("skipping writing of site-status-devoid SSB string")
        return False


    # write string to file:
    # =====================
    try:
        with open(filename, 'w') as myFile:
            myFile.write( ssbString )
        logging.log(25, "SSB metric with %d sites written to file" % cnt_docs)
    except OSError as excptn:
        logging.error("Failed to write SSB metric, %s" % str(excptn))

    return
# ########################################################################### #



if __name__ == '__main__':
    #
    parserObj = argparse.ArgumentParser(description="Script to evaluate Hamm" +
        "erCloud status of sites for the 15 minute (1 hour, 6 hours, and 1 d" +
        "ay) bin that started 30 minutes ago. HC status for a specific time " +
        "bin or time interval are evaluated in case of of one or two argumen" +
        "ts.")
    parserObj.add_argument("-q", dest="qhour", action="store_true",
                                 help="restrict evaluation to 15 min results")
    parserObj.add_argument("-1", dest="hour", action="store_true",
                                 help="restrict evaluation to 1 hour results")
    parserObj.add_argument("-6", dest="qday", action="store_true",
                                 help="restrict evaluation to 6 hours results")
    parserObj.add_argument("-d", dest="day", action="store_true",
                                 help="restrict evaluation to 1 day results")
    parserObj.add_argument("-U", dest="upload", default=True,
                                 action="store_false",
                                 help="do not upload to MonIT but print HC e" +
                                 "valuations")
    parserObj.add_argument("-v", action="count", default=0,
                                 help="increase verbosity")
    parserObj.add_argument("timeSpec", nargs="?",
                                 metavar="time-specification",
                                 help=("time specification in UTC, either an" +
                                       " integer with the time in seconds si" +
                                       "nce the epoch or time in the format " +
                                       "\"YYYY-Mmm-dd HH:MM\""))
    parserObj.add_argument("lastSpec", nargs="?",
                                 metavar="end-time",
                                 help=("end time specification in UTC, eithe" +
                                       "r an integer with the time in second" +
                                       "s since the epoch or time in the for" +
                                       "mat \"YYYY-Mmm-dd HH:MM\""))
    argStruct = parserObj.parse_args()
    #
    if not ( argStruct.qhour or argStruct.hour or argStruct.qday or
             argStruct.day ):
        argStruct.qhour = True
        argStruct.hour = True
        argStruct.qday = True
        argStruct.day = True


    # configure the message logger:
    # =============================
    logging.addLevelName(25, "NOTICE")
    logging.addLevelName(15, "debug")
    logging.addLevelName(9, "XDEBUG")
    if ( argStruct.v >= 5 ):
        logging.basicConfig(datefmt="%Y-%b-%d %H:%M:%S",
                            format="%(asctime)s [%(levelname).1s] %(message)s",
                            level=9)
    elif ( argStruct.v == 4 ):
        logging.basicConfig(datefmt="%Y-%b-%d %H:%M:%S",
                            format="%(asctime)s [%(levelname).1s] %(message)s",
                            level=logging.DEBUG)
    elif ( argStruct.v == 3 ):
        logging.basicConfig(datefmt="%Y-%b-%d %H:%M:%S",
                            format="%(asctime)s [%(levelname).1s] %(message)s",
                            level=15)
    elif ( argStruct.v == 2 ):
        logging.basicConfig(datefmt="%Y-%b-%d %H:%M:%S",
                            format="%(asctime)s [%(levelname).1s] %(message)s",
                            level=logging.INFO)
    elif ( argStruct.v == 1 ):
        logging.basicConfig(datefmt="%Y-%b-%d %H:%M:%S",
                            format="%(asctime)s [%(levelname).1s] %(message)s",
                            level=25)
    else:
        logging.basicConfig(datefmt="%Y-%b-%d %H:%M:%S",
                            format="%(asctime)s [%(levelname).1s] %(message)s",
                            level=logging.WARNING)


    # check we have a valid Kerberos ticket available:
    # ================================================
    if not evhc_kerberos_check():
        sys.exit(1)


    # time period for which we need to get/evaluate HammerCloud status:
    # =================================================================
    now15m = int( time.time() / 900 )
    if argStruct.timeSpec is None:
        # evaluate HC for time bins that ended 15 min, 1h, 2h, and 3 hour ago:
        frst15m = now15m - 13
        last15m = now15m - 2
        #
        if (( argStruct.day ) and ( now15m % 96 == 12 )):
            # need HC job records from 24+2 hours ago:
            startTIS = ( now15m - 108 ) * 900
        elif (( argStruct.qday ) and ( now15m % 24 == 12 )):
            # need HC job records from 6+2 hours ago:
            startTIS = ( now15m - 36 ) * 900
        elif (( argStruct.hour ) and ( now15m % 4 == 0 )):
            # need HC job records from 1+2 hours ago:
            startTIS = ( now15m - 16 ) * 900
        else:
            # need HC job records from 15 min + 3 hours ago:
            startTIS = ( now15m - 13 ) * 900
        # evaluate HC 15min results for time bin that started 30 min ago
        limitTIS = ( last15m + 1 ) * 900
    else:
        if ( argStruct.timeSpec.isdigit() ):
            # argument should be time in seconds of first 15 min time bin
            frst15m = int( argStruct.timeSpec / 900 )
        else:
            # argument should be the time in "YYYY-Mmm-dd HH:MM" format
            frst15m = int( calendar.timegm( time.strptime("%s UTC" %
                           argStruct.timeSpec, "%Y-%b-%d %H:%M %Z") ) / 900 )
        last15m = frst15m
        if ( argStruct.day ):
            startTIS = int( frst15m / 96 ) * 86400
            limitTIS = startTIS + 86400
        elif ( argStruct.qday ):
            startTIS = int( frst15m / 24 ) * 21600
            limitTIS = startTIS + 21600
        elif ( argStruct.hour ):
            startTIS = int( frst15m / 4 ) * 3600
            limitTIS = startTIS + 3600
        else:
            startTIS = frst15m * 900
            limitTIS = startTIS + 900
        # ElasticSearch has only data of the last 40 days:
        if ( (now15m - int(startTIS/900)) >= 3840 ):
            logging.critical("Start time outside ElasticSearch data range (" +
                             "last 40 days)")
            sys.exit(1)


    # last timebin for which we should evaluate HammerCloud status:
    # =============================================================
    if argStruct.lastSpec is not None:
        if ( argStruct.lastSpec.isdigit() ):
            # argument should be time in seconds of last 15 min time bin
            last15m = int( argStruct.lastSpec / 900 )
        else:
            # argument should be the time in "YYYY-Mmm-dd HH:MM" format
            last15m = int( calendar.timegm( time.strptime("%s UTC" %
                           argStruct.lastSpec, "%Y-%b-%d %H:%M %Z") ) / 900 )
        if ( argStruct.day ):
            limitTIS = max( limitTIS, ( int( last15m / 96 ) * 86400 ) + 86400 )
        elif ( argStruct.qday ):
            limitTIS = max( limitTIS, ( int( last15m / 24 ) * 21600 ) + 21600 )
        elif ( argStruct.hour ):
            limitTIS = max( limitTIS, ( int( last15m / 4 ) * 3600 ) + 3600 )
        else:
            limitTIS = max( limitTIS, ( last15m * 900 ) + 900 )

    if ( frst15m == last15m ):
        logging.info("Evaluating HC status for time bin %s" %
                  time.strftime("%Y-%m-%d %H:%M", time.gmtime(frst15m * 900)))
    else:
        logging.info(("Evaluating HC status for time bins from %s t" +
                      "o %s") %
                     (time.strftime("%Y-%m-%d %H:%M",
                                    time.gmtime(frst15m * 900)),
                      time.strftime("%Y-%m-%d %H:%M",
                                    time.gmtime(last15m * 900))))


    # fetch list of CMS sites:
    # ========================
    successFlag = evhc_vofeed()
    if not successFlag:
        sys.exit(1)


    # fetch HC template configuration:
    # ================================
    if ( (now15m - frst15m) <= 192 ):
        # consider template information only for evaluation within 2 days:
        evhc_template_cfg()


    # fetch relevant HammerCloud jobs records:
    # ========================================
    evhc_grafana_jobs(startTIS, limitTIS)


    # evaluate HammerCloud site status and prepare MonIT JSON for time bins:
    # ======================================================================
    if ( argStruct.qhour ):
        if argStruct.timeSpec is None:
            # evaluate HC site status for time bin that started 30 min ago
            tbin = now15m - 2
            evhc_evaluate_sites("hc15min", tbin)
            # check/update HC site status for time bin that ended 1h,2h,3h ago
            evhc_evaluate_sites("hc15min", now15m - 5 )
            evhc_evaluate_sites("hc15min", now15m - 9 )
            evhc_evaluate_sites("hc15min", now15m - 13 )
        else:
            for tbin in range(frst15m, last15m + 1):
                # check/update HC site status for time bins
                evhc_evaluate_sites("hc15min", tbin)
    #
    if ( argStruct.hour ):
        if argStruct.timeSpec is None:
            if ( now15m % 4 == 0 ):
                # evaluate HC 1 hour status for time bin that ended 3 hours ago
                tbin = int( ( now15m - 16 ) / 4 )
                evhc_evaluate_sites("hc1hour", tbin)
        else:
            for tbin in range( int(frst15m/4), int(last15m/4) + 1):
                # check/update HC 1 hour status for time bins
                evhc_evaluate_sites("hc1hour", tbin)
    #
    if ( argStruct.qday ):
        if argStruct.timeSpec is None:
            if ( now15m % 24 == 12 ):
                # evaluate HC 6 hour status for time bin that ended 3 hours ago
                tbin = int( ( now15m - 36 ) / 24 )
                evhc_evaluate_sites("hc6hour", tbin)
        else:
            for tbin in range( int(frst15m/24), int(last15m/24) + 1):
                # check/update HC 1 hour status for time bins
                evhc_evaluate_sites("hc6hour", tbin)
    #
    if ( argStruct.day ):
        if argStruct.timeSpec is None:
            if ( now15m % 96 == 12 ):
                # evaluate HC 1 day status for time bin that ended 3 hours ago
                tbin = int( ( now15m - 108 ) / 96 )
                evhc_evaluate_sites("hc1day", tbin)
        else:
            for tbin in range( int(frst15m/96), int(last15m/96) + 1):
                # check/update HC 1 day status for time bins
                evhc_evaluate_sites("hc1day", tbin)


    # filter out metric/time bin entries with existing, identical docs in MonIT
    # =========================================================================
    tbins15min = []
    tbins1hour = []
    tbins6hour = []
    tbins1day = []
    for tuple in evhc_glbl_evaluations:
        if ( tuple[0] == "hc15min" ):
            tbins15min.append( tuple[1] )
        elif ( tuple[0] == "hc1hour" ):
            tbins1hour.append( tuple[1] )
        elif ( tuple[0] == "hc6hour" ):
            tbins6hour.append( tuple[1] )
        elif ( tuple[0] == "hc1day" ):
            tbins1day.append( tuple[1] )
        else:
            logging.error("Bad metric \"%s\" in global HC evaluation dict" %
                          tuple[0])
    #
    # fetch relevant HammerCloud metric docs from MonIT
    evhc_monit_fetch(tbins15min, tbins1hour, tbins6hour, tbins1day)
    #
    # filter out metric/time bin entries with identical entries in MonIT
    cnt_docs = 0
    for tuple in sorted(evhc_glbl_evaluations.keys()):
        if tuple in evhc_glbl_monitdocs:
            for index in range(len(evhc_glbl_evaluations[tuple])-1,-1,-1):
                result = evhc_glbl_evaluations[tuple][index]
                if result in evhc_glbl_monitdocs[tuple]:
                    logging.debug(("filtering out %s (%d) %s as identical en" +
                                   "try exists in MonIT") % (tuple[0],
                                   tuple[1], result['name']))
                    del evhc_glbl_evaluations[tuple][index]
                else:
                    cnt_docs += 1
            if ( len(evhc_glbl_evaluations[tuple]) == 0 ):
                # no result left in metric/time-bin:
                del evhc_glbl_evaluations[tuple]
        else:
            cnt_docs += len( evhc_glbl_evaluations[tuple] )


    # upload HammerCloud metric docs to MonIT:
    # ========================================
    if ( cnt_docs > 0 ):
        if ( argStruct.upload ):
            successFlag = evhc_monit_upload()
        else:
            successFlag = False
        #
        if ( not successFlag ):
            evhc_monit_write()
    #
    # write SSB metric file as needed:
    if (( argStruct.qhour ) and ( argStruct.timeSpec is None )):
        tbin = now15m - 2
        if ("hc15min", tbin) in evhc_glbl_evaluations:
            evhc_ssb_write( ("hc15min", tbin) )
    if (( argStruct.day ) and ( argStruct.timeSpec is None )):
        if ( now15m % 96 == 12 ):
            tbin = int( ( now15m - 108 ) / 96 )
            if ("hc1day", tbin) in evhc_glbl_evaluations:
                evhc_ssb_write( ("hc1day", tbin) )

    #import pdb; pdb.set_trace()
