#!/data/cmssst/packages/bin/python3.7
# ########################################################################### #
# python script to query the SAM ETF test results in MonIT, evaluate SAM
#    host service and site availability and reliability and to upload new
#    or changed result to MonIT HDFS. The script checks/updates 15 min,
#    1 hour, 6 hour, and 1 day results, depending on the execution time.
#
# 2019-Jan-24   Stephan Lammel
# ########################################################################### #
# "data": {
#      "name":     "T1_US_FNAL" | "cmsdcadisk01.fnal.gov",
#      "type":     "site" | "CE" | "SRM" | XRD",
#      "status":   "ok" | "warning" | "error" | "downtime" | "unknown"
#      "availability": 0.000 | null,
#      "reliability":  1.000 | null,
#      "detail": "cmsdcadisk01/SRM(ok), cmsdcatape01/SRM(ok), cmseos-gridftp/SRM(unknown)"
#      "detail": "15 min sum: ok = 44, unknown = 1, error = 2"
# }



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
import gzip
import smtplib
from email.mime.text import MIMEText
import subprocess
#
# setup the Java/HDFS/PATH environment for pydoop to work properly:
os.environ["HADOOP_CONF_DIR"] = "/opt/hadoop/conf/etc/analytix/hadoop.analytix"
os.environ["JAVA_HOME"]       = "/etc/alternatives/jre"
os.environ["HADOOP_PREFIX"]   = "/usr/hdp/hadoop"
import pydoop.hdfs
# ########################################################################### #



#EVSAM_BACKUP_DIR = "./junk"
EVSAM_BACKUP_DIR = "/data/cmssst/MonitoringScripts/sam/failed"
#
EVSAM_SERVICE_PROBES = {
    'CE':     [ "org.sam.CONDOR-JobSubmit-/cms/Role=lcgadmin",
                "org.cms.WN-env-/cms/Role=lcgadmin",
                "org.cms.WN-basic-/cms/Role=lcgadmin",
# !!!!!!!!!!!!! "org.cms.WN-cvmfs-/cms/Role=lcgadmin",
                "org.cms.WN-isolation-/cms/Role=lcgadmin",
                "org.cms.WN-frontier-/cms/Role=lcgadmin",
                "org.cms.WN-squid-/cms/Role=lcgadmin",
                "org.cms.WN-xrootd-access-/cms/Role=lcgadmin",
                "org.cms.WN-xrootd-fallback-/cms/Role=lcgadmin",
# !!!!!!!!!!!!! "org.cms.WN-remotestageout-/cms/Role=lcgadmin",
                "org.cms.WN-analysis-/cms/Role=lcgadmin",
                "org.cms.WN-mc-/cms/Role=lcgadmin" ],
    'SRM':    [ "org.cms.SRM-GetPFNFromTFC-/cms/Role=production",
                "org.cms.SRM-VOPut-/cms/Role=production",
                "org.cms.SRM-VOGet-/cms/Role=production" ],
    'XRD':    [ "org.cms.SE-xrootd-connection",
                "org.cms.SE-xrootd-version",
                "org.cms.SE-xrootd-read",
                "org.cms.SE-xrootd-contain" ]
    }
# ########################################################################### #



evsam_glbl_topology = {}
    # site dictionary of array with {'host', 'type', 'prod', 'ctgry'}
evsam_glbl_types = { 'CE': "CE",
                     'GLOBUS': "CE",
                     'gLite-CE': "CE",
                     'ARC-CE': "CE",
                     'CREAM-CE': "CE",
                     'org.opensciencegrid.htcondorce': "CE",
                     'HTCONDOR-CE': "CE",
                     'SE': "SRM",
                     'SRM': "SRM",
                     'SRMv2': "SRM",
                     'SRMv1': "SRM",
                     'globus-GRIDFTP': "SRM",
                     'GridFtp': "SRM",
                     'XRD': "XRD",
                     'XROOTD': "XRD",
                     'XRootD': "XRD",
                     'XRootD.Redirector': "XRD",
                     'XRootD origin server': "XRD",
                     'XRootD component': "XRD",
                     'org.squid-cache.Squid': "",
                     'webdav': "",
                     'perfSONAR': "perfSONAR",
                     'net.perfSONAR.Bandwidth': "perfSONAR",
                     'net.perfSONAR.Latency': "perfSONAR",
                     'gLExec': "" }
evsam_glbl_etf = {}
    # (time, host, type, probe)-tuple dictionary of status
evsam_glbl_downtimes = {}
    # 15min timebin dictionary of array with CMS downtime dictionaries
evsam_glbl_monitdocs = {}
    # (metric, timebin)-tuple dictionary of array with CMS SAM JSON dictionary
evsam_glbl_evaluations = {}
    # (metric, timebin)-tuple dictionary of array with CMS SAM JSON dictionary
# ########################################################################### #



def evsam_kerberos_check():
    """function to check we have a valid kerberos ticket"""
    # #################################################################### #
    # check lifetime of krbtgt and email in case less than an hour remains #
    # #################################################################### #
    EVSAM_KRBCCFILE = "/tmp/krb5cc_%d" % os.getuid()


    # check/set Kerberos credential cache:
    # ====================================
    if 'KRB5CCNAME' not in os.environ:
        os.environ['KRB5CCNAME'] = "FILE:" + EVSAM_KRBCCFILE
        logging.info("Kerberos credential cache set to %s" % EVSAM_KRBCCFILE)


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



def evsam_vofeed():
    """function to fetch site topology information of CMS"""
    # ########################################################## #
    # fill evsam_glbl_topology with CMS site/service information #
    # ########################################################## #
    global evsam_glbl_topology
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
                del(myCharset)
        except Exception as excptn:
            logging.critical("Failed to read VO-feed URL, %s" % str(excptn))
            return False


    # unpack XML data of the VO-feed:
    # ===============================
    vofeed = xml.etree.ElementTree.fromstring( myData )
    del myData


    # loop over site elements (multiple entries per grid and CMS site possible):
    # ============================================================
    for atpsite in vofeed.findall('atp_site'):
        cmssite = None
        for group in atpsite.findall('group'):
            if 'type' in group.attrib:
                if ( group.attrib['type'] == "CMS_Site" ):
                    cmssite = group.attrib['name']
                    break
        if cmssite is None:
            continue
        if cmssite not in evsam_glbl_topology:
            evsam_glbl_topology[ cmssite ] = []
        #
        for service in atpsite.findall('service'):
            if 'hostname' not in service.attrib:
                continue
            host = service.attrib['hostname'].lower()
            #
            if 'flavour' not in service.attrib:
                continue
            type = service.attrib['flavour']
            #
            if 'production_status' not in service.attrib:
                prod = True
            elif ( service.attrib['production_status'].lower() == "false" ):
                prod = False
            else:
                prod = True
            #
            if type not in evsam_glbl_types:
                ctgry = ""
            else:
                ctgry = evsam_glbl_types[ type ]
            #
            myDict = { 'host': host, 'type': type,
                       'prod': prod, 'ctgry': ctgry }
            if myDict not in evsam_glbl_topology[ cmssite ]:
                evsam_glbl_topology[ cmssite ].append( myDict )

    cnt_srv = 0
    cnt_t0 = 0
    cnt_t1 = 0
    cnt_t2 = 0
    cnt_t3 = 0
    for cmssite in evsam_glbl_topology:
        if ( cmssite[0:3] == "T3_" ):
            cnt_t3 += 1
        elif ( cmssite[0:3] == "T2_" ):
            cnt_t2 += 1
        elif ( cmssite[0:3] == "T1_" ):
            cnt_t1 += 1
        elif ( cmssite[0:3] == "T0_" ):
            cnt_t0 += 1
        cnt_srv += len( evsam_glbl_topology[ cmssite ] )

    # sanity check:
    if (( cnt_srv < 140 ) or ( cnt_t0 < 1 ) or ( cnt_t1 < 5 ) or
                             ( cnt_t2 < 35 ) or ( cnt_t3 < 24 )):
        logging.critical("Too few services/sites in VO-feed, %d, %d/%d/%d/%d" %
                         (cnt_srv, cnt_t0, cnt_t1, cnt_t2, cnt_t3))
        return False

    logging.info("   %d CMS services at %d/%d/%d/%d sites" %
                 (cnt_srv, cnt_t0, cnt_t1, cnt_t2, cnt_t3))
    return True
# ########################################################################### #



def evsam_monit_etf(startTIS, limitTIS):
    """function to fetch SAM ETF probe results from MonIT/HDFS"""
    # ############################################################## #
    # fill evsam_glbl_etf with SAM ETF probe results of CMS services #
    # ############################################################## #
    global evsam_glbl_etf
    PATH_HDFS_PREFIX = "/project/monitoring/archive/sam3/raw/metric/"

    # prepare service hostname list:
    # ==============================
    hostnames = []
    for cmssites in evsam_glbl_topology:
        for service in evsam_glbl_topology[ cmssites ]:
            if service['host'] not in hostnames:
                hostnames.append( service['host'] )

    # prepare HDFS subdirectory list:
    # ===============================
    logging.info("Retrieving SAM ETF probe result docs from MonIT HDFS")
    logging.log(15, "   starting %s, limit %s" %
                    (time.strftime("%Y-%b-%d %H:%M", time.gmtime(startTIS)),
                     time.strftime("%Y-%b-%d %H:%M", time.gmtime(limitTIS))))
    #
    tisDay = 24*60*60
    ts = time.gmtime( startTIS )
    startMidnight = calendar.timegm( ts[:3] + (0, 0, 0) + ts[6:] )
    now = int( time.time() )
    startTmpArea = max( calendar.timegm( time.gmtime( now - (6 * tisDay) ) ),
                        startTIS - tisDay)
    limitLocalTmpArea = calendar.timegm( time.localtime( now ) ) + tisDay
    #
    dirList = []
    for dirDay in range(startMidnight, limitTIS, tisDay):
        dirList.append( time.strftime("%Y/%m/%d", time.gmtime( dirDay )) )
    for dirDay in range(startTmpArea, limitLocalTmpArea, tisDay):
        dirList.append( time.strftime("%Y/%m/%d.tmp", time.gmtime( dirDay )) )
    del(dirDay)

    versions = {}
    try:
        with pydoop.hdfs.hdfs() as myHDFS:
            fileHndl = None
            fileObj = None
            fileName = None
            fileNames = None
            for subDir in dirList:
                logging.debug("   checking HDFS directory %s" % subDir)
                if not myHDFS.exists( PATH_HDFS_PREFIX + subDir ):
                    continue
                # get list of files in directory:
                myList = myHDFS.list_directory( PATH_HDFS_PREFIX + subDir )
                fileNames = [ d['name'] for d in myList
                          if (( d['kind'] == "file" ) and ( d['size'] != 0 )) ]
                del(myList)
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
                            if (( 'topic' not in myJson['metadata'] ) or
                                ( 'kafka_timestamp' not in myJson['metadata'] ) or
                                ( 'timestamp' not in myJson['data'] ) or
                                ( 'dst_hostname' not in myJson['data'] ) or
                                ( 'service_flavour' not in myJson['data'] ) or
                                ( 'metric_name' not in myJson['data'] ) or
                                ( 'status' not in myJson['data'] ) or
                                ( 'vo' not in myJson['data'] )):
                                continue
                            if ( myJson['metadata']['topic'] != "sam3_raw_metric" ):
                                continue
                            #
                            if ( myJson['data']['vo'] != "cms" ):
                                continue
                            #
                            probeTIS = int(myJson['data']['timestamp']/1000)
                            if ( probeTIS < startTIS ):
                                continue
                            if ( probeTIS >= limitTIS ):
                                continue
                            #
                            if myJson['data']['dst_hostname'] not in hostnames:
                                continue
                            #
                            key = ( probeTIS,
                                    myJson['data']['dst_hostname'],
                                    myJson['data']['service_flavour'],
                                    myJson['data']['metric_name'] )
                            version = myJson['metadata']['kafka_timestamp']
                            if key in versions:
                                if ( version <= versions[key] ):
                                    continue
                            #
                            versions[key] =  version
                            logging.log(9, ("      adding %s result of %s / " +
                                            "%s") %
                                            (key[3].split("-/cms/Role=",1)[0],
                                             key[1], key[2]))
                            evsam_glbl_etf[key] = myJson['data']['status']

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
            del(fileHndl)
            del(fileObj)
            del(fileName)
            del(fileNames)
    except IOError:
        logging.error("Failed to fetch SAM ETF probe results from MonIT HDFS")

    logging.info("   found %d relevant SAM ETF probe results in MonIT" %
                 len(evsam_glbl_etf))
    return
# ########################################################################### #



def evsam_monit_downtime(startTIS, limitTIS):
    """function to fetch CMS downtime information documents from MonIT/HDFS"""
    # ################################################################## #
    # fill evsam_glbl_down with CMS downtime information from MonIT/HDFS #
    # ################################################################## #
    global evsam_glbl_downtimes
    PATH_HDFS_PREFIX = "/project/monitoring/archive/cmssst/raw/ssbmetric/"

    # prepare HDFS subdirectory list:
    # ===============================
    logging.info("Retrieving CMS downtime docs from MonIT HDFS")
    logging.log(15, "   starting %s, limit %s" %
                    (time.strftime("%Y-%b-%d %H:%M", time.gmtime(startTIS)),
                     time.strftime("%Y-%b-%d %H:%M", time.gmtime(limitTIS))))
    #
    tisDay = 24*60*60
    ts = time.gmtime( startTIS )
    startTISmidnight = calendar.timegm( ts[:3] + (0, 0, 0) + ts[6:] )
    now = int( time.time() )
    startTmpArea = max( calendar.timegm( time.gmtime( now - (6 * tisDay) ) ),
                        startTIS - tisDay)
    limitLocalTmpArea = calendar.timegm( time.localtime( now ) ) + tisDay
    #
    dirList = []
    for dirDay in range(startTISmidnight, limitTIS, tisDay):
        dirList.append( time.strftime("down15min/%Y/%m/%d",
                                      time.gmtime( dirDay )) )
    for dirDay in range(startTmpArea, limitLocalTmpArea, tisDay):
        dirList.append( time.strftime("down15min/%Y/%m/%d.tmp",
                                      time.gmtime( dirDay )) )
    del(dirDay)

    tmpDict = {}
    try:
        with pydoop.hdfs.hdfs() as myHDFS:
            fileHndl = None
            fileObj = None
            fileName = None
            fileNames = None
            for subDir in dirList:
                logging.debug("   checking HDFS directory %s" % subDir)
                if not myHDFS.exists( PATH_HDFS_PREFIX + subDir ):
                    continue
                # get list of files in directory:
                myList = myHDFS.list_directory( PATH_HDFS_PREFIX + subDir )
                fileNames = [ d['name'] for d in myList
                          if (( d['kind'] == "file" ) and ( d['size'] != 0 )) ]
                del(myList)
                for fileName in fileNames:
                    logging.debug("   file %s" % os.path.basename(fileName))
                    try:
                        if ( os.path.splitext(fileName)[-1] == ".gz" ):
                            fileHndl = myHDFS.open_file(fileName)
                            fileObj = gzip.GzipFile(fileobj=fileHndl)
                        else:
                            fileHndl = None
                            fileObj = myHDFS.open_file(fileName)
                        # read documents and add relevant records to list:
                        for myLine in fileObj:
                            myJson = json.loads(myLine.decode('utf-8'))
                            if (( 'metadata' not in myJson ) or
                                ( 'data' not in myJson )):
                                continue
                            if (( 'timestamp' not in myJson['metadata'] ) or
                                ( 'kafka_timestamp' not in myJson['metadata'] ) or
                                ( 'path' not in myJson['metadata'] ) or
                                ( 'name' not in myJson['data'] ) or
                                ( 'type' not in myJson['data'] ) or
                                ( 'status' not in myJson['data'] ) or
                                ( 'duration' not in myJson['data'] )):
                                continue
                            #
                            if ( myJson['metadata']['path'] != "down15min" ):
                                continue
                            #
                            tis = int(myJson['metadata']['timestamp']/1000)
                            if ( tis < startTISmidnight ):
                                continue
                            if ( tis >= limitTIS ):
                                continue
                            #
                            t15bin = int( tis / 900 )
                            if t15bin not in tmpDict:
                                tmpDict[ t15bin ] = []
                            tmpDict[ t15bin ].append(
                                { 'v': myJson['metadata']['kafka_timestamp'],
                                  'd': myJson['data'] } )

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
                            fileObj  = None
                        if fileHndl is not None:
                            fileHndl.close()
                            fileHndl = None
            del(fileHndl)
            del(fileObj)
            del(fileName)
            del(fileNames)
    except:
        logging.error("Failed to fetch CMS downtime docs from MonIT HDFS")


    # convert temp into global dictionary and filter out superseded versions:
    cnt = 0
    evsam_glbl_downtimes = {}
    for t15bin in tmpDict:
        # find latest MonIT document version:
        newest = 0
        for entry in tmpDict[ t15bin ]:
            if ( entry['v'] > newest ):
                newest = entry['v']
        #
        evsam_glbl_downtimes[ t15bin ] = []
        #
        # fill downtime entries of latest MonIT document version:
        for entry in tmpDict[ t15bin ]:
            # allow 5 min for MonIT importer processing
            if ( (newest - entry['v']) <= 300000 ):
                # add category in case of known service:
                if entry['d']['type'] in evsam_glbl_types:
                    entry['d']['ctgry'] = evsam_glbl_types[ entry['d']['type'] ]
                else:
                    entry['d']['ctgry'] = ""
                evsam_glbl_downtimes[ t15bin ].append( entry['d'] )
                cnt += 1
                logging.log(9, "      adding %d %s of %s / %s" %
                               (t15bin, entry['d']['status'],
                                entry['d']['name'], entry['d']['ctgry']))
    del(tmpDict)
    #
    logging.info("   found %d CMS site downtimes in %d timebins in MonIT" %
                 (cnt, len(evsam_glbl_downtimes)))
    #
    return
# ########################################################################### #



def evsam_monit_fetch(t15bins, t1bins, t6bins, t24bins):
    """function to fetch CMS SAM site/service status from MonIT/HDFS"""
    # ##################################################################### #
    # fill evsam_glbl_monitdocs with site/service status of CMS sites/hosts #
    # ##################################################################### #
    global evsam_glbl_monitdocs
    PATH_HDFS_PREFIX = "/project/monitoring/archive/cmssst/raw/ssbmetric/"

    # prepare HDFS subdirectory list:
    # ===============================
    logging.info("Retrieving CMS SAM site/service status docs from MonIT HDFS")
    #
    tisDay = 24*60*60
    now = int( time.time() )
    startTmpArea = calendar.timegm( time.gmtime( now - (6 * tisDay) ) )
    limitLocalTmpArea = calendar.timegm( time.localtime( now ) ) + tisDay
    #
    dirList = []
    #
    if ( len(t15bins) > 0 ):
        logging.log(15, "   15 min time bins %d (%s), ..., %d (%s)" %
                        (t15bins[0], time.strftime("%Y-%b-%d %H:%M:%S",
                                                  time.gmtime(t15bins[0]*900)),
                         t15bins[-1], time.strftime("%Y-%b-%d %H:%M:%S",
                                          time.gmtime((t15bins[-1]*900)+899))))
        lowestTbin = now
        for tbin in t15bins:
            if ( tbin < lowestTbin ):
                lowestTbin = tbin
            dirString = time.strftime("sam15min/%Y/%m/%d",
                                      time.gmtime( tbin * 900 ))
            if dirString not in dirList:
                dirList.append( dirString )
        for dirDay in range(max( startTmpArea, lowestTbin - tisDay ),
                            limitLocalTmpArea, tisDay):
            dirList.append( time.strftime("sam15min/%Y/%m/%d.tmp",
                                          time.gmtime( dirDay )) )
    #
    if ( len(t1bins) > 0 ):
        logging.log(15, "   1 hour time bins %d (%s), ..., %d (%s)" %
                        (t1bins[0], time.strftime("%Y-%b-%d %H:%M",
                                                  time.gmtime(t1bins[0]*3600)),
                         t1bins[-1], time.strftime("%Y-%b-%d %H:%M",
                                         time.gmtime((t1bins[-1]*3600)+3599))))
        lowestTbin = now
        for tbin in t1bins:
            if ( tbin < lowestTbin ):
                lowestTbin = tbin
            dirString = time.strftime("sam1hour/%Y/%m/%d",
                                      time.gmtime( tbin * 3600 ))
            if dirString not in dirList:
                dirList.append( dirString )
        for dirDay in range(max( startTmpArea, lowestTbin - tisDay ),
                            limitLocalTmpArea, tisDay):
            dirList.append( time.strftime("sam1hour/%Y/%m/%d.tmp",
                                          time.gmtime( dirDay )) )
    if ( len(t6bins) > 0 ):
        logging.log(15, "   6 hour time bins %d (%s), ..., %d (%s)" %
                        (t6bins[0], time.strftime("%Y-%b-%d %H:%M",
                                                 time.gmtime(t6bins[0]*21600)),
                         t6bins[-1], time.strftime("%Y-%b-%d %H:%M",
                                       time.gmtime((t6bins[-1]*21600)+21599))))
        lowestTbin = now
        for tbin in t6bins:
            if ( tbin < lowestTbin ):
                lowestTbin = tbin
            dirString = time.strftime("sam6hour/%Y/%m/%d",
                                      time.gmtime( tbin * 21600 ))
            if dirString not in dirList:
                dirList.append( dirString )
        for dirDay in range(max( startTmpArea, lowestTbin - tisDay ),
                            limitLocalTmpArea, tisDay):
            dirList.append( time.strftime("sam6hour/%Y/%m/%d.tmp",
                                          time.gmtime( dirDay )) )
    if ( len(t24bins) > 0 ):
        logging.log(15, "   1 day  time bins %d (%s), ..., %d (%s)" %
                        (t24bins[0], time.strftime("%Y-%b-%d %H:%M",
                                                time.gmtime(t24bins[0]*86400)),
                         t24bins[-1], time.strftime("%Y-%b-%d %H:%M",
                                      time.gmtime((t24bins[-1]*86400)+86399))))
        lowestTbin = now
        for tbin in t24bins:
            if ( tbin < lowestTbin ):
                lowestTbin = tbin
            dirString = time.strftime("sam1day/%Y/%m/%d",
                                      time.gmtime( tbin * 86400 ))
            if dirString not in dirList:
                dirList.append( dirString )
        for dirDay in range(max( startTmpArea, lowestTbin - tisDay ),
                            limitLocalTmpArea, tisDay):
            dirList.append( time.strftime("sam1day/%Y/%m/%d.tmp",
                                          time.gmtime( dirDay )) )
    if ( len(dirList) == 0 ):
        return
    del(dirDay)

    tmpDict = {}
    try:
        with pydoop.hdfs.hdfs() as myHDFS:
            fileHndl = None
            fileObj = None
            fileName = None
            fileNames = None
            for subDir in dirList:
                logging.debug("   checking HDFS directory %s" % subDir)
                if not myHDFS.exists( PATH_HDFS_PREFIX + subDir ):
                    continue
                # get list of files in directory:
                myList = myHDFS.list_directory( PATH_HDFS_PREFIX + subDir )
                fileNames = [ d['name'] for d in myList
                          if (( d['kind'] == "file" ) and ( d['size'] != 0 )) ]
                del(myList)
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
                        # read documents and add relevant records to global:
                        for myLine in fileObj:
                            myJson = json.loads(myLine.decode('utf-8'))
                            if (( 'metadata' not in myJson ) or
                                ( 'data' not in myJson )):
                                continue
                            if (( 'timestamp' not in myJson['metadata'] ) or
                                ( 'kafka_timestamp' not in myJson['metadata'] ) or
                                ( 'path' not in myJson['metadata'] ) or
                                ( 'name' not in myJson['data'] ) or
                                ( 'type' not in myJson['data'] ) or
                                ( 'status' not in myJson['data'] )):
                                continue
                            #
                            tis = int(myJson['metadata']['timestamp']/1000)
                            if ( myJson['metadata']['path'] == "sam15min" ):
                                tbin = int( tis / 900 )
                                if tbin not in t15bins:
                                    continue
                            elif ( myJson['metadata']['path'] == "sam1hour" ):
                                tbin = int( tis / 3600 )
                                if tbin not in t1bins:
                                    continue
                            elif ( myJson['metadata']['path'] == "sam6hour" ):
                                tbin = int( tis / 21600 )
                                if tbin not in t6bins:
                                    continue
                            elif ( myJson['metadata']['path'] == "sam1day" ):
                                tbin = int( tis / 86400 )
                                if tbin not in t24bins:
                                    continue
                            else:
                                continue
                            #
                            if 'availability' not in myJson['data']:
                                myJson['data']['availability'] = None
                            if 'reliability' not in myJson['data']:
                                myJson['data']['reliability'] = None
                            if 'detail' not in myJson['data']:
                                myJson['data']['detail'] = None
                            #
                            version = myJson['metadata']['kafka_timestamp']
                            #
                            key = ( myJson['metadata']['path'],
                                    tbin,
                                    myJson['data']['name'],
                                    myJson['data']['type'] )
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
            del(fileHndl)
            del(fileObj)
            del(fileName)
            del(fileNames)
    except:
        logging.error("Failed to fetch CMS SAM metric docs from MonIT HDFS")

    # convert temporary dictionary into global dictionary of arrays:
    for longKey in tmpDict:
        shortKey = ( longKey[0], longKey[1] )
        if shortKey not in evsam_glbl_monitdocs:
            evsam_glbl_monitdocs[shortKey] = []
        evsam_glbl_monitdocs[shortKey].append( tmpDict[longKey]['d'] )
        logging.log(9, "      adding %s (%d) of %s / %s" %
                       (longKey[0], longKey[1], longKey[2], longKey[3]))
    #
    logging.info("   found %d relevant CMS SAM metric docs in MonIT" %
                 len(tmpDict))
    del(tmpDict)
    #
    return



def evsam_monit_fetch15m(frst15cms, last15cms):
    #
    t15bins = []
    for tbin in range(frst15cms, last15cms + 1):
        t15bins.append( tbin )
    #
    evsam_monit_fetch(t15bins, [], [], [])
    #
    return
# ########################################################################### #



def evsam_add_evaluation(metric, timebin, name, type, status,
                         availability, reliability, detail):
    """function to add a service/site status to the global evaluation list"""
    # ##################################################### #
    # add a status dictionary to the global evaluation list #
    # ##################################################### #
    global evsam_glbl_evaluations

    if ( name == "" ):
        return

    key = ( metric, timebin )
    evaluation = {'name': name, 'type': type, 'status': status,
                  'availability': availability, 'reliability': reliability,
                  'detail': detail}

    if key not in evsam_glbl_evaluations:
        evsam_glbl_evaluations[ key ] = []
    if evaluation not in evsam_glbl_evaluations[ key ]:
        evsam_glbl_evaluations[ key ].append( evaluation )
        logging.info("   added %s (%d) evaluation for %s / %s: %s (%s)" %
             (metric, timebin, name, type, status, detail.replace('\n','\\n')))
    else:
        logging.info("   skipping duplicate entry %s (%d) %s / %s" %
                     (metric, timebin, name, type))

    return
# ########################################################################### #



def evsam_evaluate_service_status(etfResults, service):
    """function to evaluate CMS SAM service status"""
    # ##################################################################### #
    # return CMS SAM service status based on provided SAM ETF probe results #
    # ##################################################################### #
    status = None
    detail = "no known probes for service type"

    logging.debug("   evaluating SAM service status for %s / %s" %
                  (service['host'], service['ctgry']))

    if service['ctgry'] not in EVSAM_SERVICE_PROBES:
        return status, "service type unknown"

    srvKey = ( service['host'], service['ctgry'] )
    for probe in EVSAM_SERVICE_PROBES[ service['ctgry'] ]:
        try:
            noInside = len( etfResults['inside'][srvKey][probe] )
        except KeyError:
            noInside = 0
        try:
            noBefore = len( etfResults['before'][srvKey][probe] )
        except KeyError:
            noBefore = 0
        logging.log(9, "       |%d][%d] results for %s" %
                       (noBefore, noInside, probe.split("-/cms/Role=",1)[0]))
        #
        pStat = None
        if ( noInside == 1 ):
            pStat = etfResults['inside'][srvKey][probe][0]['status']
        elif ( noInside >= 2 ):
            # moderate between known statuses
            cnt_ok = cnt_warn = cnt_err = 0
            for result in etfResults['inside'][srvKey][probe]:
                if ( result['status'] == "ok" ):
                    cnt_ok += 1
                elif ( result['status'] == "warning" ):
                    cnt_warn += 1
                elif ( result['status'] != "error" ):
                    cnt_err += 1
            if ( (cnt_ok + cnt_warn + cnt_err) == 0 ):
                pStat = "unknown"
            elif ( cnt_err == 0 ):
                if ( cnt_ok >= cnt_warn ):
                    pStat = "ok"
                else:
                    pStat = "warning"
            elif ( (cnt_ok + cnt_warn) == 0 ):
                pStat = "error"
            elif ( (cnt_ok + cnt_warn) >= cnt_err ):
                pStat = "warning"
            else:
                pStat = "error"
        elif ( noBefore == 1 ):
            pStat = etfResults['before'][srvKey][probe][0]['status']
        elif ( noBefore >= 2 ):
            # consider last result, even if unknown
            max_time = 0
            for result in etfResults['before'][srvKey][probe]:
                if ( result['time'] > max_time ):
                    pStat = result['status']
                    max_time = result['time']
        else:
            pStat = "unknown"

        #-LML patch for xrootd overload of PIC
        if (( service['host'].find(".pic.es") > 0 ) and
            (( probe == "org.cms.SE-xrootd-connection" ) or
             ( probe == "org.cms.SE-xrootd-version" ) or
             ( probe == "org.cms.SE-xrootd-read" ) or
             ( probe == "org.cms.SE-xrootd-contain" ) or
             ( probe == "org.cms.WN-xrootd-access-/cms/Role=lcgadmin" ) or
             ( probe == "org.cms.WN-xrootd-fallback-/cms/Role=lcgadmin" )) and
            (( pStat == "error" ) or ( pStat == "unknown" ))):
            pStat = "warning"
        #-LML patch for xrootd overload of PIC

        logging.log(9, "       probe status: %s" % pStat)
        #
        #
        if ( pStat == status ):
            if ( pStat != "ok" ):
                detail = "%s, %s" % (probe.split("-/cms/Role=",1)[0], detail)
        else:
            if status is None:
                status = pStat
                if ( pStat == "ok" ):
                   detail = "all ok"
                else:
                   detail = "%s (%s)" % (probe.split("-/cms/Role=",1)[0], pStat)
            elif ( pStat == "error" ):
                status = "error"
                detail = "%s (error)" % probe.split("-/cms/Role=",1)[0]
            elif (( pStat == "unknown" ) and ( status != "error" )):
                status = "unknown"
                detail = "%s (unknown)" % probe.split("-/cms/Role=",1)[0]
            elif (( pStat == "warning" ) and ( status == "ok" )):
                status = "warning"
                detail = "%s (warning)" % probe.split("-/cms/Role=",1)[0]

    logging.debug("      service status: %s" % status)

    return status, detail



def evsam_check_service_downtime(service, time15bin):
    """function to check if a service is in a scheduled downtime"""
    # ##################################################################### #
    # check global downtime information if service is in scheduled downtime #
    # ##################################################################### #
    startTIS = time15bin * 900
    limitTIS = startTIS + 900

    # reverse loop over downtime boundaries:
    for tbin in sorted( evsam_glbl_downtimes.keys(), reverse=True ):
        # relevant downtimes are in boundary at or before timebin:
        if ( tbin <= time15bin ):
            for downInfo in evsam_glbl_downtimes[tbin]:
                # check service match:
                if ( downInfo['name'] != service['host'] ):
                    continue
                if ( downInfo['ctgry'] != service['ctgry'] ):
                    continue
                if ( downInfo['status'] == "ok" ):
                    continue
                if ( limitTIS <= downInfo['duration'][0] ):
                    continue
                if ( startTIS >= downInfo['duration'][1] ):
                    continue
                return downInfo['status']
            break

    return "ok"



def evsam_check_site_downtime(site, time15bin):
    """function to check if a site is in a scheduled downtime"""
    # ################################################################## #
    # check global downtime information if site is in scheduled downtime #
    # ################################################################## #
    startTIS = time15bin * 900
    limitTIS = startTIS + 900

    # reverse loop over downtime boundaries:
    for tbin in sorted( evsam_glbl_downtimes.keys(), reverse=True ):
        # relevant downtimes are in boundary at or before timebin:
        if ( tbin <= time15bin ):
            for downInfo in evsam_glbl_downtimes[tbin]:
                # check service match:
                if ( downInfo['name'] != site ):
                    continue
                if ( downInfo['type'] != "site" ):
                    continue
                if ( downInfo['status'] == "ok" ):
                    continue
                if ( limitTIS <= downInfo['duration'][0] ):
                    continue
                if ( startTIS >= downInfo['duration'][1] ):
                    continue
                return downInfo['status'], downInfo['detail']
            break

    return "ok", "no known downtime"



def evsam_check_site_downtime_range(site, start15bin, limit15bin):
    """function to check if a site is in a scheduled downtime"""
    # ################################################################## #
    # check global downtime information if site is in scheduled downtime #
    # ################################################################## #
    downCount = 0

    time15bin = limit15bin - 1

    # reverse loop over downtime boundaries:
    for tbin in sorted( evsam_glbl_downtimes.keys(), reverse=True ):
        while (( tbin <= time15bin ) and ( time15bin >= start15bin )):
            startTIS = time15bin * 900
            limitTIS = startTIS + 900
            # relevant downtimes are in boundary at or before timebin:
            for downInfo in evsam_glbl_downtimes[tbin]:
                # check service match:
                if ( downInfo['name'] != site ):
                    continue
                if ( downInfo['type'] != "site" ):
                    continue
                if ( downInfo['status'] != "downtime" ):
                    continue
                if ( limitTIS <= downInfo['duration'][0] ):
                    continue
                if ( startTIS >= downInfo['duration'][1] ):
                    continue
                downCount += 1
                break
            time15bin -= 1
        if ( time15bin < start15bin ):
            break

    if ( downCount >= ((limit15bin - start15bin) / 2) ):
        return "downtime", "%dh%dm" % (int(downCount/4), 15*(downCount%4))

    return "ok", "0h0m"



def evsam_evaluate(timebin):
    """function to evaluate CMS SAM service/site status for a given time bin"""
    # ###################################################################### #
    # fill global CMS SAM metric with service/site status of 15 min time bin #
    # ###################################################################### #
    startTIS = timebin * 900
    limitTIS = startTIS + 900
    beforeTIS = startTIS - ( 900 + 450 )
    #
    kwnCnt = 0

    logging.info("Evaluating SAM service/site status for %s" %
                 time.strftime("%Y-%b-%d %H:%M:%S", time.gmtime(startTIS)))

    # extract ETF probe results for timebin from evsam_glbl_etf
    # =========================================================
    etfResults = {'inside': {}, 'before': {} }
    for key in evsam_glbl_etf:
        probeTIS = key[0]
        if ( probeTIS < beforeTIS ):
            continue
        if ( probeTIS >= limitTIS ):
            continue
        if ( probeTIS >= startTIS ):
            binKey = 'inside'
        else:
            binKey = 'before'
        host = key[1]
        type = key[2]
        if type not in evsam_glbl_types:
            continue
        ctgry = evsam_glbl_types[ type ]
        srvKey = ( host, ctgry )
        probeKey = key[3]
        # translate ETF status codes to the names CMS uses:
        etfStatus = evsam_glbl_etf[key].upper()
        if ( etfStatus == "OK" ):
           myStatus = "ok"
        elif ( etfStatus == "WARNING" ):
           myStatus = "warning"
        elif ( etfStatus == "CRITICAL" ):
           myStatus = "error"
        elif ( etfStatus == "UNKNOWN" ):
           myStatus = "unknown"
        else:
           logging.error("Unknown/illegal ETF status \"%s\" encountered" %
               evsam_glbl_etf[key])
           myStatus = "unknown"
        valueDict = { 'time': probeTIS,
                      'status': myStatus }
        if srvKey not in etfResults[binKey]:
            etfResults[binKey][srvKey] = {}
        if probeKey not in etfResults[binKey][srvKey]:
            etfResults[binKey][srvKey][probeKey] = []
        etfResults[binKey][srvKey][probeKey].append( valueDict )

    #for myKey in {**etfResults['inside'], **etfResults['before']}:
    #    if myKey in etfResults['before']:
    #        myBefore = len( etfResults['before'][myKey] )
    #    else:
    #        myBefore = 0
    #    if myKey in etfResults['inside']:
    #        myInside = len( etfResults['inside'][myKey] )
    #    else:
    #        myInside = 0
    #    logging.log(9, "   filled |%d][%d] probes results for host %s / %s" %
    #                                (myBefore, myInside, myKey[0], myKey[1]))


    # loop over topology and evaluate CMS SAM service and site status
    # ===============================================================
    for site in sorted( evsam_glbl_topology.keys() ):
        siteDetail = ""
        ceStatus = None
        srmStatus = None
        xrootdStatus = None
        for service in sorted(evsam_glbl_topology[site],
                              key=lambda k: [k['ctgry'], k['host'], k['type']]):
            #
            # evaluate service status:
            myStatus, myDetail = evsam_evaluate_service_status(etfResults,
                                                               service)
            #
            # add service evaluation to evsam_glbl_evaluations:
            if myStatus is not None:
                evsam_add_evaluation("sam15min", timebin,
                    service['host'], service['ctgry'], myStatus,
                    None, None, myDetail)
                #
                downStatus = evsam_check_service_downtime(service, timebin)
                #
                if service['prod']:
                    if (( downStatus == "downtime" ) and
                        (( myStatus == "error" ) or ( myStatus == "unknown" ))):
                        siteDetail += "%s/%s (%s)\n" % (service['host'],
                                                  service['ctgry'], downStatus)
                    else:
                        siteDetail += "%s/%s (%s)\n" % (service['host'],
                                                    service['ctgry'], myStatus)
                    if ( service['ctgry'] == "CE" ):
                        # one CE needs to be working:
                        if (( downStatus == "downtime" ) and
                            (( myStatus == "error" ) or
                             ( myStatus == "unknown" ))):
                            pass
                        elif ceStatus is None:
                            ceStatus = myStatus
                        elif ( myStatus == "ok" ):
                            ceStatus = "ok"
                        elif (( myStatus == "warning" ) and
                              ( ceStatus != "ok" )):
                            ceStatus = "warning"
                        elif (( myStatus == "error" ) and
                              ( ceStatus == "unknown" )):
                            ceStatus = "error"
                    elif ( service['ctgry'] == "SRM" ):
                        # all SRM endpoints must be working:
                        if (( downStatus == "downtime" ) and
                            (( myStatus == "error" ) or
                             ( myStatus == "unknown" ))):
                            pass
                        elif srmStatus is None:
                            srmStatus = myStatus
                        elif ( myStatus == "error" ):
                            srmStatus = "error"
                        elif (( myStatus == "unknown" ) and
                              (( srmStatus == "warning" ) or
                               ( srmStatus == "ok" ))):
                            srmStatus = "unknown"
                        elif (( myStatus == "warning" ) and
                              ( srmStatus == "ok" )):
                            srmStatus = "warning"
                    elif ( service['ctgry'] == "XRD" ):
                        # one xrootd-endpoint must be working:
                        if (( downStatus == "downtime" ) and
                            (( myStatus == "error" ) or
                             ( myStatus == "unknown" ))):
                            pass
                        elif xrootdStatus is None:
                            xrootdStatus = myStatus
                        elif ( myStatus == "ok" ):
                            xrootdStatus = "ok"
                        elif (( myStatus == "warning" ) and
                              ( xrootdStatus != "ok" )):
                            xrootdStatus = "warning"
                        elif (( myStatus == "error" ) and
                              ( xrootdStatus == "unknown" )):
                            xrootdStatus = "error"
        #
        # add site evaluation to evsam_glbl_evaluations:
        myStatus = None
        myAvailability = None
        if (( ceStatus == "error" ) or ( srmStatus == "error" ) or
                                       ( xrootdStatus == "error" )):
            myStatus = "error"
            myAvailability = 0.000
        elif (( ceStatus == "unknown" ) or ( srmStatus == "unknown" ) or
                                           ( xrootdStatus == "unknown" )):
            myStatus = "unknown"
            myAvailability = None
        elif (( ceStatus == "warning" ) or ( srmStatus == "warning" ) or
                                           ( xrootdStatus == "warning" )):
            myStatus = "warning"
            myAvailability = 1.000
        elif (( ceStatus == "ok" ) or ( srmStatus == "ok" ) or
                                      ( xrootdStatus == "ok" )):
            myStatus = "ok"
            myAvailability = 1.000
        myReliability = myAvailability
        #
        # check for downtime:
        downStatus, downDetail = evsam_check_site_downtime(site, timebin)
        if ( downStatus != "ok" ):
            siteDetail = "%s: %s\n%s" % (downStatus, downDetail, siteDetail)
            if ( downStatus == "downtime" ):
                if (( myStatus == "error" ) or ( myStatus == "unknown" )):
                    myStatus = "downtime"
                myReliability = None
        #
        # add site evaluation to evsam_glbl_evaluations:
        if ( siteDetail[-1:] == "\n" ):
            siteDetail = siteDetail[:-1]
        if myStatus is not None:
            evsam_add_evaluation("sam15min", timebin, site, "site", myStatus,
                myAvailability, myReliability, siteDetail)
            if ( myStatus != "unknown" ):
                kwnCnt += 1

    if ( kwnCnt == 0 ):
        logging.warning("SAM status evaluated to all unknown for %s (%s)" %
            (startTIS, time.strftime("%Y-%b-%d %H:%M", time.gmtime(startTIS))))
    else:
        logging.log(25, "SAM status evaluated for %s (%s)" % (startTIS,
                       time.strftime("%Y-%b-%d %H:%M", time.gmtime(startTIS))))
    #
    return
# ########################################################################### #



def evsam_calculate(metric, timebin):
    """function to calculate CMS SAM service/site status for a given timebin"""
    # ################################################################## #
    # fill global CMS SAM metric with calculation of service/site status #
    # ################################################################## #
    if ( metric == "sam1hour" ):
        no15min = 4
    elif ( metric == "sam6hour" ):
        no15min = 24
    elif ( metric == "sam1day" ):
        no15min = 96
    else:
        return
    start15m = timebin * no15min
    limit15m = start15m + no15min

    logging.info("Calculating SAM %s service/site status for %s" %
                 (metric[3:],
                time.strftime("%Y-%b-%d %H:%M:%S", time.gmtime(start15m*900))))

    # loop over topology and calculate CMS SAM service and site status
    # ================================================================
    for site in sorted( evsam_glbl_topology.keys() ):
        #
        for service in sorted(evsam_glbl_topology[site],
                              key=lambda k: [k['ctgry'], k['host'], k['type']]):
            #
            # calculate service status:
            cnt_ok = cnt_warn = cnt_err = 0
            cnt_unknown = 0
            for t15bin in range(start15m, limit15m):
                t15status = None
                key = ("sam15min", t15bin)
                #
                if key in evsam_glbl_evaluations:
                    for result in evsam_glbl_evaluations[ key ]:
                        if (( result['name'] == service['host'] ) and
                            ( result['type'] == service['ctgry'] )):
                            t15status = result['status']
                            break
                #
                if (( t15status is None ) and ( key in evsam_glbl_monitdocs )):
                    for result in evsam_glbl_monitdocs[ key ]:
                        if (( result['name'] == service['host'] ) and
                            ( result['type'] == service['ctgry'] )):
                            t15status = result['status']
                            break
                if t15status is not None:
                    if ( t15status == "ok" ):
                        cnt_ok += 1
                    elif ( t15status == "warning" ):
                        cnt_warn += 1
                    elif ( t15status == "error" ):
                        cnt_err += 1
                    elif ( t15status == "unknown" ):
                        cnt_unknown += 1
            if ( (cnt_ok + cnt_warn + cnt_err + cnt_unknown) == 0 ):
                myStatus = None
            elif ( (cnt_ok + cnt_warn + cnt_err) == 0 ):
                myStatus = "unknown"
                myAvailability = None
            else:
                myAvailability = round( (cnt_ok + cnt_warn) /
                                        (cnt_ok + cnt_warn + cnt_err), 3)
                if ( cnt_unknown > (cnt_ok + cnt_warn + cnt_err) ):
                    myStatus = "unknown"
                elif ( myAvailability >= 0.900 ):
                    myStatus = "ok"
                elif ( myAvailability < 0.800 ):
                    myStatus = "error"
                else:
                    myStatus = "warning"
            myDetail = ("15min evaluations: %d ok, %d warning, %d error, %d " +
                        "unknown") % (cnt_ok, cnt_warn, cnt_err, cnt_unknown)
            # add service calculation to evsam_glbl_evaluations:
            if myStatus is not None:
                evsam_add_evaluation(metric, timebin,
                    service['host'], service['ctgry'], myStatus,
                    myAvailability, None, myDetail)
        #
        # calculate site status:
        sum_availability = 0.000
        sum_reliability = 0.000
        cnt_availability = 0
        cnt_reliability = 0
        cnt_ok = cnt_warn = cnt_err = 0
        cnt_unknown = 0
        cnt_downtime = 0
        for t15bin in range(start15m, limit15m):
            t15status = None
            key = ("sam15min", t15bin)
            #
            if key in evsam_glbl_evaluations:
                for result in evsam_glbl_evaluations[ key ]:
                    if (( result['name'] == site ) and
                        ( result['type'] == "site" )):
                        t15status = result['status']
                        if 'availability' in result:
                            if result['availability'] is not None:
                                sum_availability += result['availability']
                                cnt_availability += 1
                        if 'reliability' in result:
                            if result['reliability'] is not None:
                                sum_reliability += result['reliability']
                                cnt_reliability += 1
                        break
            #
            if (( t15status is None ) and ( key in evsam_glbl_monitdocs )):
                for result in evsam_glbl_monitdocs[ key ]:
                    if (( result['name'] == site ) and
                        ( result['type'] == "site" )):
                        t15status = result['status']
                        if 'availability' in result:
                            if result['availability'] is not None:
                                sum_availability += result['availability']
                                cnt_availability += 1
                        if 'reliability' in result:
                            if result['reliability'] is not None:
                                sum_reliability += result['reliability']
                                cnt_reliability += 1
                        break
            if t15status is not None:
                if ( t15status == "ok" ):
                    cnt_ok += 1
                elif ( t15status == "warning" ):
                    cnt_warn += 1
                elif ( t15status == "error" ):
                    cnt_err += 1
                elif ( t15status == "unknown" ):
                    cnt_unknown += 1
                elif ( t15status == "downtime" ):
                    cnt_downtime += 1
        #
        if ( (cnt_ok + cnt_warn + cnt_err + cnt_unknown + cnt_downtime) == 0 ):
            myStatus = None
            myAvailability = None
            myReliability = None
        elif ( cnt_availability == 0 ):
            myStatus = "unknown"
            myAvailability = None
            myReliability = None
        elif ( cnt_reliability == 0 ):
            myStatus = "unknown"
            myAvailability = round(sum_availability / cnt_availability, 3)
            myReliability = None
        else:
            myAvailability = round(sum_availability / cnt_availability, 3)
            #
            myReliability = round(sum_reliability / cnt_reliability, 3)
            #
            if ( cnt_unknown > (cnt_ok + cnt_warn + cnt_err) ):
                myStatus = "unknown"
            elif ( myReliability >= 0.900 ):
                myStatus = "ok"
            elif ( myReliability < 0.800 ):
                myStatus = "error"
            elif (( site[0:3] == "T0_" ) or ( site[0:3] == "T1_" )):
                myStatus = "error"
            else:
                myStatus = "warning"
        downStatus, downDetail = evsam_check_site_downtime_range(site,
                                                            start15m, limit15m)
        #
        if ( downStatus == "downtime" ):
            if (( myStatus is None ) or
                ( myStatus == "error" ) or ( myStatus == "unknown" )):
                myStatus = "downtime"
        #
        myDetail = ("15min evaluations: %d ok, %d warning, %d error, %d unkn" +
                    "own, %d downtime (%s)") % (cnt_ok, cnt_warn, cnt_err,
                                         cnt_unknown, cnt_downtime, downDetail)
        # add site calculation to evsam_glbl_evaluations:
        if myStatus is not None:
            evsam_add_evaluation(metric, timebin, site, "site", myStatus,
                                       myAvailability, myReliability, myDetail)
# ########################################################################### #



def evsam_compose_json():
    """function to compose a JSON string from the global evaluations"""
    # ############################################################ #
    # compose a JSON string from results in evsam_glbl_evaluations #
    # ############################################################ #

    # convert global evaluation dictionary into JSON document array string:
    # =====================================================================
    jsonString = "["
    commaFlag = False
    #
    for metric in ["sam15min", "sam1hour", "sam6hour", "sam1day"]:
        if ( metric == "sam15min" ):
           interval = 900
        elif ( metric == "sam1hour" ):
           interval = 3600
        elif ( metric == "sam6hour" ):
           interval = 21600
        else:
           interval = 86400
        #
        for timebin in sorted([ t[1] for t in evsam_glbl_evaluations
                                                          if t[0] == metric ]):
            #logging.log(9, "   %s for %d (%s)" %
            #              (metric, timebin, time.strftime("%Y-%b-%d %H:%M:%S",
            #                                  time.gmtime(timebin*interval))))
            key = (metric, timebin)
            hdrString = ((",\n {\n   \"producer\": \"cmssst\",\n" +
                                 "   \"type\": \"ssbmetric\",\n" +
                                 "   \"path\": \"%s\",\n" +
                                 "   \"timestamp\": %d,\n" +
                                 "   \"type_prefix\": \"raw\",\n" +
                                 "   \"data\": {\n") %
                         (metric, ((timebin*interval) + (interval/2)) * 1000))
            #
            for result in evsam_glbl_evaluations[ key ]:
                #logging.log(9, "      %s / %s status: %s" % (result['name'],
                #                            result['type'], result['status']))
                if commaFlag:
                    jsonString += hdrString
                else:
                    jsonString += hdrString[1:]
                jsonString += (("      \"name\": \"%s\",\n" +
                                "      \"type\": \"%s\",\n" +
                                "      \"status\": \"%s\",\n") %
                               (result['name'], result['type'],
                                result['status']))
                if result['availability'] is not None:
                    jsonString += ("      \"availability\": %.3f,\n" %
                                   result['availability'])
                elif ( result['type'] == "site" ):
                    jsonString += ("      \"availability\": null,\n")
                if result['reliability'] is not None:
                    jsonString += ("      \"reliability\": %.3f,\n" %
                                   result['reliability'])
                elif ( result['type'] == "site" ):
                    jsonString += ("      \"reliability\": null,\n")
                if result['detail'] is not None:
                    jsonString += ("      \"detail\": \"%s\"\n   }\n }" %
                                   result['detail'].replace('\n','\\n'))
                else:
                    jsonString += ("      \"detail\": null\n   }\n }")
                commaFlag = True
    jsonString += "\n]\n"

    return jsonString



def evsam_monit_upload():
    """function to upload CMS SAM service/site status to MonIT/HDFS"""
    # ############################################################### #
    # upload evsam_glbl_evaluations as JSON metric documents to MonIT #
    # ############################################################### #
    #MONIT_URL = "http://monit-metrics.cern.ch:10012/"
    MONIT_URL = "http://fail.cern.ch:10012/"
    MONIT_HDR = {'Content-Type': "application/json; charset=UTF-8"}
    #
    logging.info("Composing JSON array and uploading to MonIT")


    # compose JSON array string:
    # ==========================
    jsonString = evsam_compose_json()
    if ( jsonString == "[\n]\n" ):
        logging.warning("skipping upload of document-devoid JSON string")
        return False
    cnt_15min = jsonString.count("\"path\": \"sam15min\"")
    cnt_1hour = jsonString.count("\"path\": \"sam1hour\"")
    cnt_6hour = jsonString.count("\"path\": \"sam6hour\"")
    cnt_1day  = jsonString.count("\"path\": \"sam1day\"")
    #
    jsonString = jsonString.replace("ssbmetric", "metrictest")


    # upload string with JSON document array to MonIT/HDFS:
    # =====================================================
    docs = json.loads(jsonString)
    ndocs = len(docs)
    successFlag = True
    for myOffset in range(0, ndocs, 8192):
        # MonIT upload channel can handle at most 10,000 docs at once
        dataString = json.dumps( docs[myOffset:min(ndocs,myOffset+8192)] )
        #
        try:
            # MonIT needs a document array and without newline characters:
            requestObj = urllib.request.Request(MONIT_URL,
                         data=dataString.encode("utf-8"),
                         headers=MONIT_HDR, method="POST")
            responseObj = urllib.request.urlopen( requestObj, timeout=90 )
            if ( responseObj.status != http.HTTPStatus.OK ):
                logging.error(("Failed to upload JSON [%d:%d] string to MonI" +
                               "T, %d \"%s\"") %
                              (myOffset, min(ndocs,myOffset+8192),
                               responseObj.status, responseObj.reason))
                successFlag = False
            responseObj.close()
        except urllib.error.URLError as excptn:
            logging.error("Failed to upload JSON [%d:%d], %s" %
                             (myOffset, min(ndocs,myOffset+8192), str(excptn)))
            successFlag = False
    del docs

    if ( successFlag ):
        logging.log(25, ("JSON string with %d(15m)/%d(1h)/%d(6h)/%d(1d) docs" +
                         " uploaded to MonIT") %
                        (cnt_15min, cnt_1hour, cnt_6hour, cnt_1day))
    return successFlag



def evsam_monit_write(filename=None):
    """function to write CMS SAM service/site status JSON to a file"""
    # ############################################################### #
    # write evsam_glbl_evaluations as JSON metric documents to a file #
    # ############################################################### #

    if filename is None:
        filename = "%s/eval_sam_%s.json" % (EVSAM_BACKUP_DIR,
                                    time.strftime("%Y%m%d%H%M", time.gmtime()))
    logging.info("Writing JSON array to file %s" % filename)

    # compose JSON array string:
    # ==========================
    jsonString = evsam_compose_json()
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



if __name__ == '__main__':
    #
    parserObj = argparse.ArgumentParser(description="Script to evaluate SAM " +
        "host-service and site status for the 15 minute (1 hour, 6 hours, an" +
        "d 1 day) bin that started 30 minutes ago. SAM status for a specific" +
        " time bin or time interval are evaluated in case of of one or two a" +
        "rguments.")
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
                                 help="do not upload to MonIT but print SAM " +
                                 "evaluations")
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
    if not evsam_kerberos_check():
        sys.exit(1)


    # first time bin for which we need to evaluate SAM status:
    # ========================================================
    now15m = int( time.time() / 900 )
    if argStruct.timeSpec is None:
        #
        # evaluate SAM for time bins that ended 15 min, 1h, 2h, and 3 hour ago:
        frst15etf = now15m - 13
        last15etf = now15m - 2
        #
        # calculate SAM (from 15 min metric) as needed:
        if (( argStruct.day ) and ( now15m % 96 == 12 )):
            frst15cms = now15m - 108
            last15cms = now15m - 13
        elif (( argStruct.qday ) and ( now15m % 24 == 12 )):
            frst15cms = now15m - 36
            last15cms = now15m - 13
        elif (( argStruct.hour ) and ( now15m % 4 == 0 )):
            frst15cms = now15m - 16
            last15cms = now15m - 13
        else:
            frst15cms = now15m - 13
            last15cms = now15m - 5
    else:
        if ( argStruct.timeSpec.isdigit() ):
            # argument should be time in seconds of first 15 min time bin
            frst15etf = int( argStruct.timeSpec / 900 )
        else:
            # argument should be the time in "YYYY-Mmm-dd HH:MM" format
            frst15etf = int( calendar.timegm( time.strptime("%s UTC" %
                             argStruct.timeSpec, "%Y-%b-%d %H:%M %Z") ) / 900 )
        last15etf = frst15etf
        #
        # calculate SAM (from 15 min metric) as needed:
        if ( argStruct.day ):
            frst15cms = int( frst15etf / 96 ) * 96
            last15cms = frst15cms + 95
        elif ( argStruct.qday ):
            frst15cms = int( frst15etf / 24 ) * 24
            last15cms = frst15cms + 23
        elif ( argStruct.hour ):
            frst15cms = int( frst15etf / 4 ) * 4
            last15cms = frst15cms + 3
        else:
            frst15cms = frst15etf
            last15cms = frst15cms


    # last timebin for which we should evaluate SAM status:
    # =====================================================
    if argStruct.lastSpec is None:
        logging.info("Evaluating SAM status for time bin %s" %
                 time.strftime("%Y-%b-%d %H:%M", time.gmtime(frst15etf * 900)))
    else:
        if ( argStruct.lastSpec.isdigit() ):
            # argument should be time in seconds of last 15 min time bin
            last15etf = int( argStruct.lastSpec / 900 )
        else:
            # argument should be the time in "YYYY-Mmm-dd HH:MM" format
            last15etf = int( calendar.timegm( time.strptime("%s UTC" %
                             argStruct.lastSpec, "%Y-%b-%d %H:%M %Z") ) / 900 )
        #
        # calculate SAM (from 15 min metric) as needed:
        if ( argStruct.day ):
            last15cms = ( int( last15etf / 96 ) * 96 ) + 95
        elif ( argStruct.qday ):
            last15cms = ( int( last15etf / 24 ) * 24 ) + 23
        elif ( argStruct.hour ):
            last15cms = ( int( last15etf / 4 ) * 4 ) + 3
        else:
            last15cms = last15etf
        logging.info("Evaluating SAM status for time bins %s to %s" %
                     (time.strftime("%Y-%b-%d %H:%M",
                                    time.gmtime(frst15etf * 900)),
                      time.strftime("%Y-%b-%d %H:%M",
                                    time.gmtime(last15etf * 900))))


    # fetch service information of sites:
    # ===================================
    successFlag = evsam_vofeed()
    if not successFlag:
        sys.exit(1)


    # fetch SAM ETF probe results:
    # ============================
    evsam_monit_etf( (frst15etf * 900) - 1350, (last15etf * 900) + 900)


    # fetch CMS downtime information:
    # ===============================
    evsam_monit_downtime((frst15etf * 900), (last15etf * 900) + 900)


    # fetch CMS SAM 15 min service/site evaluations:
    # ==============================================
    evsam_monit_fetch15m(frst15cms, last15cms)


    # evaluate CMS SAM status of services/sites:
    # ==========================================
    if ( argStruct.qhour ):
        if argStruct.timeSpec is None:
            # evaluate SAM status for time bin that started 30 min ago
            tbin = now15m - 2
            evsam_evaluate(tbin)
            # check/update SAM status for time bins that ended 1h,2h,3h ago
            evsam_evaluate( now15m - 5 )
            evsam_evaluate( now15m - 9 )
            evsam_evaluate( now15m - 13 )
        else:
            for tbin in range(frst15etf, last15etf + 1):
                # check/update SAM service/site status for time bins
                evsam_evaluate(tbin)
    #
    if ( argStruct.hour ):
        if argStruct.timeSpec is None:
            if ( now15m % 4 == 0 ):
                # calculate SAM status for time bin that ended 3 hours ago
                tbin = int( (now15m - 16) / 4 )
                evsam_calculate("sam1hour", tbin)
        else:
            for tbin in range( int(frst15etf/4), int(last15etf/4)+1):
                # check/update SAM service/site status for time bins
                evsam_calculate("sam1hour", tbin)
    #
    if ( argStruct.qday ):
        if argStruct.timeSpec is None:
            if ( now15m % 24 == 12 ):
                # calculate SAM status for time bin that ended 3 hours ago
                tbin = int( (now15m - 36) / 24 )
                evsam_calculate("sam6hour", tbin)
        else:
            for tbin in range( int(frst15etf/24), int(last15etf/24)+1):
                # check/update SAM service/site status for time bins
                evsam_calculate("sam6hour", tbin)
    #
    if ( argStruct.day ):
        if argStruct.timeSpec is None:
            if ( now15m % 96 == 12 ):
                # calculate SAM status for time bin that ended 3 hours ago
                tbin = int( (now15m - 108) / 96 )
                evsam_calculate("sam1day", tbin)
        else:
            for tbin in range( int(frst15etf/96), int(last15etf/96)+1):
                # check/update SAM service/site status for time bins
                evsam_calculate("sam1day", tbin)


    # filter out metric/time bin entries with existing, identical docs in MonIT
    # =========================================================================
    tbins15min = []
    tbins1hour = []
    tbins6hour = []
    tbins1day = []
    for tuple in evsam_glbl_evaluations:
        if ( tuple[0] == "sam15min" ):
            if tuple not in evsam_glbl_monitdocs:
                tbins15min.append( tuple[1] )
        elif ( tuple[0] == "sam1hour" ):
            tbins1hour.append( tuple[1] )
        elif ( tuple[0] == "sam6hour" ):
            tbins6hour.append( tuple[1] )
        elif ( tuple[0] == "sam1day" ):
            tbins1day.append( tuple[1] )
        else:
            logging.error("Bad metric \"%s\" in global SAM evaluation dict" %
                          tuple[0])
    #
    # fetch relevant SAM metric docs from MonIT
    evsam_monit_fetch(tbins15min, tbins1hour, tbins6hour, tbins1day)
    #
    # filter out metric/time-bin entries with identical entries in MonIT
    cnt_docs = 0
    for tuple in sorted(evsam_glbl_evaluations.keys()):
        if tuple in evsam_glbl_monitdocs:
            for index in range(len(evsam_glbl_evaluations[tuple])-1,-1,-1):
                result = evsam_glbl_evaluations[tuple][index]
                if result in evsam_glbl_monitdocs[tuple]:
                    logging.debug(("filtering out %s (%d) %s / %s as identic" +
                                   "al entry exists in MonIT") % (tuple[0],
                                   tuple[1], result['name'], result['type']))
                    del evsam_glbl_evaluations[tuple][index]
                else:
                    cnt_docs += 1
            if ( len(evsam_glbl_evaluations[tuple]) == 0 ):
                # no result left in metric/time-bin:
                del evsam_glbl_evaluations[tuple]
        else:
            cnt_docs += len( evsam_glbl_evaluations[tuple] )


    # upload SAM metric docs to MonIT:
    # ================================
    if ( cnt_docs > 0 ):
        if ( argStruct.upload ):
            successFlag = evsam_monit_upload()
        else:
            successFlag = False
        #
        if ( not successFlag ):
            evsam_monit_write()

    #import pdb; pdb.set_trace()
