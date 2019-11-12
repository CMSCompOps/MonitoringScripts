#!/eos/user/c/cmssst/packages/bin/python3.7
# ########################################################################### #
# python script to retrieve SAM-ETF logs and CMS SSB metric documents from
#    CERN MonIT HDFS. The cmssst log retrieval Bourne shell script will use
#    this script to retrieve, format as HTML table, and write to a file in a
#    web cache area the document(s).
#
# 2019-Feb-23   Stephan Lammel
# ########################################################################### #
#
# PATH_INFO supported:
# ====================
#   /etf15min  / 1550923650     / T0_CH_CERN  / site           / 0+0
#    down15min / 201902231200   / ce07.pic.es / CE             /
#    sam15min  / 20190223120730 / all         / SE-xrootd-read /
#    sam1hour                                                  /
#    sam6hour                                                  /
#    sam1day                                                   / debug
#    hc15min     "HammerCloud"
#    hc1hour
#    hc6hour
#    hc1day
#    fts15min    "FTS transfers/links"
#    fts1hour
#    fts6hour
#    fts1day
#    sr15min     "Site Readiness"
#    sr1hour
#    sr16hour
#    sr1day
#    sts15min    "Site Status, i.e. LifeStatus/ProdStatus/CrabStatus"
#
# QUERY_STRING REMOTE_USER ADFS_LOGIN ADFS_FULLNAME ADFS_GROUP



import os, sys
import time, calendar
import logging
import argparse
import re
import json
import gzip
#
# setup the Java/HDFS/PATH environment for pydoop to work properly:
os.environ["HADOOP_CONF_DIR"] = "/eos/home-c/cmssst/packages/etc/hadoop/conf/hadoop.analytix"
os.environ["JAVA_HOME"]       = "/eos/user/c/cmssst/packages/lib/jvm/java-1.8.0-openjdk-1.8.0.201.b09-2.el7_6.x86_64/jre"
os.environ["HADOOP_PREFIX"]   = "/eos/home-c/cmssst/packages/hadoop/hadoop-2.7.5"
import pydoop.hdfs
# ########################################################################### #



LFTCH_PROBE_ORDER = [ "CONDOR-JobSubmit",
                      "WN-env",
                      "WN-basic",
                      "WN-cvmfs",
                      "WN-isolation",
                      "WN-frontier",
                      "WN-squid",
                      "WN-xrootd-access",
                      "WN-xrootd-fallback",
                      "WN-analysis",
                      "WN-mc",
                      "WN-remotestageout",
                      "SRM-GetPFNFromTFC",
                      "SRM-VOPut",
                      "SRM-VOGet",
                      "SE-xrootd-connection",
                      "SE-xrootd-version",
                      "SE-xrootd-read",
                      "SE-xrootd-contain" ]
LFTCH_SERVICE_ORDER = [ "site", "CE", "SRM", "XROOTD", "perfSONAR" ]
LFTCH_TRANSFER_ORDER = [ "site", "destination", "source", "link" ]
LFTCH_SUPERSEDED = 1000
LFTCH_METRICS_DEFINED = {
    'etf15min': {
        'title': "SAM ETF",
        'period': 900,
        'hdfs': "/project/monitoring/archive/sam3/raw/metric/",
        'dfltwin': "2+0" },
    'down15min': {
        'title': "Downtime(s)",
        'period': 900,
        'hdfs': "/project/monitoring/archive/cmssst/raw/ssbmetric/down15min/",
        'dfltwin': "day+0" },
    'sam15min': {
        'title': "SAM 15 min",
        'period': 900,
        'hdfs': "/project/monitoring/archive/cmssst/raw/ssbmetric/sam15min/",
        'dfltwin': "1+1" },
    'sam1hour': {
        'title': "SAM 1 hour", 
        'period': 3600,
        'hdfs': "/project/monitoring/archive/cmssst/raw/ssbmetric/sam1hour/",
        'dfltwin': "0+0" },
    'sam6hour': { 
        'title': "SAM 6 hours", 
        'period': 21600,
        'hdfs': "/project/monitoring/archive/cmssst/raw/ssbmetric/sam6hour/",
        'dfltwin': "0+0" },
    'sam1day': { 
        'title': "SAM 1 day",
        'period': 86400,
        'hdfs': "/project/monitoring/archive/cmssst/raw/ssbmetric/sam1day/",
        'dfltwin': "0+0" },
    'hc15min': { 
        'title': "HC 15 min", 
        'period': 900,
        'hdfs': "/project/monitoring/archive/cmssst/raw/ssbmetric/hc15min/",
        'dfltwin': "1+1" },
    'hc1hour': { 
        'title': "HC 1 hour", 
        'period': 3600,
        'hdfs': "/project/monitoring/archive/cmssst/raw/ssbmetric/hc1hour/",
        'dfltwin': "0+0" },
    'hc6hour': { 
        'title': "HC 6 hours", 
        'period': 21600,
        'hdfs': "/project/monitoring/archive/cmssst/raw/ssbmetric/hc6hour/",
        'dfltwin': "0+0" },
    'hc1day': { 
        'title': "HC 1 day", 
        'period': 86400,
        'hdfs': "/project/monitoring/archive/cmssst/raw/ssbmetric/hc1day/",
        'dfltwin': "0+0" },
    'fts15min': {
        'title': "FTS 15 min",
        'period': 900,
        'hdfs': "/project/monitoring/archive/cmssst/raw/ssbmetric/fts15min/",
        'dfltwin': "1+1" },
    'fts1hour': {
        'title': "FTS 1 hour",
        'period': 3600,
        'hdfs': "/project/monitoring/archive/cmssst/raw/ssbmetric/fts1hour/",
        'dfltwin': "0+0" },
    'fts6hour': {
        'title': "FTS 6 hours",
        'period': 21600,
        'hdfs': "/project/monitoring/archive/cmssst/raw/ssbmetric/fts6hour/",
        'dfltwin': "0+0" },
    'fts1day': {
        'title': "FTS 1 day",
        'period': 86400,
        'hdfs': "/project/monitoring/archive/cmssst/raw/ssbmetric/fts1day/",
        'dfltwin': "0+0" },
    'sr15min': {
        'title': "SiteReadiness 15 min",
        'period': 900,
        'hdfs': "/project/monitoring/archive/cmssst/raw/ssbmetric/sr15min/",
        'dfltwin': "1+1" },
    'sr1hour': {
        'title': "SiteReadiness 1 hour",
        'period': 3600,
        'hdfs': "/project/monitoring/archive/cmssst/raw/ssbmetric/sr1hour/",
        'dfltwin': "0+0" },
    'sr6hour': {
        'title': "SiteReadiness 6 hours",
        'period': 21600,
        'hdfs': "/project/monitoring/archive/cmssst/raw/ssbmetric/sr6hour/",
        'dfltwin': "0+0" },
    'sr1day': {
        'title': "SiteReadiness 1 day",
        'period': 86400,
        'hdfs': "/project/monitoring/archive/cmssst/raw/ssbmetric/sr1day/",
        'dfltwin': "0+0" },
    'sts15min': { 
        'title': "SiteStatus 15 min", 
        'period': 900,
        'hdfs': "/project/monitoring/archive/cmssst/raw/ssbmetric/sts15min/",
        'dfltwin': "day+0" }
    }
LFTCH_SERVICE_TYPES = { 'CE': "CE",
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
                        'SRM.nearline': "SRM",
                        'globus-GRIDFTP': "SRM",
                        'GridFtp': "SRM",
                        'XROOTD': "XROOTD",
                        'XRootD': "XROOTD",
                        'XRootD.Redirector': "XROOTD",
                        'XRootD origin server': "XROOTD",
                        'XRootD component': "XROOTD",
                        'org.squid-cache.Squid': "",
                        'webdav': "",
                        'perfSONAR': "perfSONAR",
                        'net.perfSONAR.Bandwidth': "perfSONAR",
                        'net.perfSONAR.Latency': "perfSONAR",
                        'site': "site" }
# ########################################################################### #



def lftch_monit_fetch(cfg):
    """function to fetch relevant documents from MonIT/HDFS"""
    # #################################################################### #
    # return dictionary with list of documents from MonIT for each timebin #
    # #################################################################### #
    #
    startTIS = cfg['time'] - ( cfg['period'] * cfg['before'] )
    limitTIS = cfg['time'] + ( cfg['period'] * ( cfg['after'] + 1 ) )
    #
    logging.info("Retrieving %s docs from MonIT HDFS" % cfg['title'])
    logging.log(15, "   time range %s to %s" %
                    (time.strftime("%Y-%b-%d %H:%M", time.gmtime(startTIS)),
                     time.strftime("%Y-%b-%d %H:%M", time.gmtime(limitTIS))))


    # prepare HDFS subdirectory list:
    # ===============================
    tisDay = 24*60*60
    ts = time.gmtime( startTIS )
    startMidnight = calendar.timegm( ts[:3] + (0, 0, 0) + ts[6:] )
    startTmpArea = max( int(time.time()) - (6 * tisDay), startTIS - tisDay)
    limitLocalTmpArea = calendar.timegm( time.localtime() ) + tisDay
    #
    dirList = []
    for dirDay in range(startMidnight, limitTIS, tisDay):
        dirList.append( time.strftime("%Y/%m/%d", time.gmtime( dirDay )) )
    for dirDay in range(startTmpArea, limitLocalTmpArea, tisDay):
        dirList.append( time.strftime("%Y/%m/%d.tmp", time.gmtime( dirDay )) )
    del(dirDay)


    # scan HDFS subdirectories and retrieve relevant documents:
    # =========================================================
    lftch_monitdocs = {}
    prevDir = ""
    try:
        with pydoop.hdfs.hdfs() as myHDFS:
            logging.log(25, "HDFS connection established")
            fileHndl = None
            fileObj = None
            fileName = None
            fileNames = None
            for subDir in dirList:
                if ( subDir[-3:] != prevDir ):
                    if ( prevDir == "" ):
                        logging.log(25, "   Accessing primary document area")
                    elif ( subDir[-3:] == "tmp" ):
                        logging.log(25, "   Accessing document update areas")
                    prevDir = subDir[-3:]
                logging.debug("   checking HDFS directory %s" % subDir)
                if not myHDFS.exists( cfg['hdfs'] + subDir ):
                    continue
                # get list of files in directory:
                myList = myHDFS.list_directory( cfg['hdfs'] + subDir )
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
                            if (( 'kafka_timestamp' not in myJson['metadata'] ) or
                                ( '_id' not in myJson['metadata'] )):
                                continue
                            logging.log(9, "   document %s" %
                                                     myJson['metadata']['_id'])
                            if ( cfg['metric'][:3] == "etf" ):
                                # check document has required SAM-ETF keys:
                                if (( 'topic' not in myJson['metadata'] ) or
                                    ( 'timestamp' not in myJson['data'] ) or
                                    ( 'dst_hostname' not in myJson['data'] ) or
                                    ( 'service_flavour' not in myJson['data'] ) or
                                    ( 'metric_name' not in myJson['data'] ) or
                                    ( 'status' not in myJson['data'] ) or
                                    ( 'vo' not in myJson['data'] )):
                                    continue
                                if (( myJson['metadata']['topic'] !=
                                      "sam3_raw_metric" ) or
                                    ( myJson['data']['vo'] != "cms" )):
                                    continue
                                tis = int(myJson['data']['timestamp']/1000)
                                if ( tis < startTIS ):
                                    continue
                                if ( tis >= limitTIS ):
                                    continue
                                logging.log(9, "      %s within time range" %
                                                   myJson['metadata']['topic'])
                                myName = myJson['data']['dst_hostname'].lower()
                                if ( cfg['name'] != "*" ):
                                    if ( myName != cfg['name'] ):
                                        continue
                                myType = myJson['data']['service_flavour']
                                if myType not in LFTCH_SERVICE_TYPES:
                                    ctgry = ""
                                else:
                                    ctgry = LFTCH_SERVICE_TYPES[ myType ]
                                myMetric = myJson['data']['metric_name']
                                if ( cfg['type'] == "*" ):
                                    pass
                                elif ( myType == cfg['type'] ):
                                    pass
                                elif ( ctgry == cfg['type'] ):
                                    pass
                                elif ( cfg['type'] == "CE" ):
                                    if (( myMetric[:15] != "org.sam.CONDOR-" ) and
                                        ( myMetric[:11] != "org.cms.WN-" )):
                                        continue
                                elif ( cfg['type'] == "SRM" ):
                                    if ( myMetric[:12] != "org.cms.SRM-" ):
                                        continue
                                elif ( cfg['type'] == "XROOTD" ):
                                    if ( myMetric[:17] != "org.cms.SE-xrootd" ):
                                        continue
                                elif ( cfg['type'][:4] == "org." ):
                                    if (( myMetric.lower() != cfg['type'].lower() ) and
                                        ( myMetric.split("-/cms/Role=",1)[0].lower() != cfg['type'].lower() )):
                                        continue
                                else:
                                    if (( myMetric[8:].lower() != cfg['type'].lower() ) and
                                        ( myMetric[8:].split("-/cms/Role=",1)[0].lower() != cfg['type'].lower() )):
                                        continue
                                myStatus = myJson['data']['status']
                            elif ( cfg['metric'][:4] == "down" ):
                                # check document has required downtime keys:
                                if (( 'path' not in myJson['metadata'] ) or
                                    ( 'timestamp' not in myJson['metadata'] ) or
                                    ( 'name' not in myJson['data'] ) or
                                    ( 'type' not in myJson['data'] ) or
                                    ( 'status' not in myJson['data'] ) or
                                    ( 'duration' not in myJson['data'] )):
                                    continue
                                if ( myJson['metadata']['path'] != "down15min" ):
                                    continue
                                tis = int(myJson['metadata']['timestamp']/1000)
                                if ( tis < startTIS ):
                                    continue
                                if ( tis >= limitTIS ):
                                    continue
                                myName = myJson['data']['name']
                                if ( cfg['name'] != "*" ):
                                    if ( myName != cfg['name'] ):
                                        continue
                                myType = myJson['data']['type']
                                if ( cfg['type'] != "*" ):
                                    if myType not in LFTCH_SERVICE_TYPES:
                                        ctgry = ""
                                    else:
                                        ctgry = LFTCH_SERVICE_TYPES[ myType ]
                                    if (( myType != cfg['type'] ) and
                                        ( ctgry != cfg['type'] )):
                                        continue
                                myStatus = myJson['data']['status']
                            elif ( cfg['metric'][:3] == "sam" ):
                                # check document has required CMS-SAM keys:
                                if (( 'path' not in myJson['metadata'] ) or
                                    ( 'timestamp' not in myJson['metadata'] ) or
                                    ( 'name' not in myJson['data'] ) or
                                    ( 'type' not in myJson['data'] ) or
                                    ( 'status' not in myJson['data'] )):
                                    continue
                                if ( myJson['metadata']['path'] !=
                                     cfg['metric'] ):
                                    continue
                                tis = int(myJson['metadata']['timestamp']/1000)
                                if ( tis < startTIS ):
                                    continue
                                if ( tis >= limitTIS ):
                                    continue
                                myName = myJson['data']['name']
                                if ( cfg['name'] != "*" ):
                                    if ( myName != cfg['name'] ):
                                        continue
                                myType = myJson['data']['type']
                                if ( cfg['type'] != "*" ):
                                    if ( myType != cfg['type'] ):
                                        continue
                                myStatus = myJson['data']['status']
                            elif ( cfg['metric'][:2] == "hc" ):
                                # check document has required CMS-HC keys:
                                if (( 'path' not in myJson['metadata'] ) or
                                    ( 'timestamp' not in myJson['metadata'] ) or
                                    ( 'site' not in myJson['data'] ) or
                                    ( 'status' not in myJson['data'] )):
                                    continue
                                if ( myJson['metadata']['path'] !=
                                     cfg['metric'] ):
                                    continue
                                tis = int(myJson['metadata']['timestamp']/1000)
                                if ( tis < startTIS ):
                                    continue
                                if ( tis >= limitTIS ):
                                    continue
                                myName = myJson['data']['site']
                                if ( cfg['name'] != "*" ):
                                    if ( myName != cfg['name'] ):
                                        continue
                                myType = "site"
                                myStatus = myJson['data']['status']
                            elif ( cfg['metric'][:3] == "fts" ):
                                # check document has required CMS-FTS keys:
                                if (( 'path' not in myJson['metadata'] ) or
                                    ( 'timestamp' not in myJson['metadata'] ) or
                                    ( 'name' not in myJson['data'] ) or
                                    ( 'type' not in myJson['data'] ) or
                                    ( 'status' not in myJson['data'] )):
                                    continue
                                if ( myJson['metadata']['path'] !=
                                     cfg['metric'] ):
                                    continue
                                tis = int(myJson['metadata']['timestamp']/1000)
                                if ( tis < startTIS ):
                                    continue
                                if ( tis >= limitTIS ):
                                    continue
                                myName = myJson['data']['name']
                                if ( cfg['name'] != "*" ):
                                    if ( myName != cfg['name'] ):
                                        continue
                                myType = myJson['data']['type']
                                if ( cfg['type'] != "*" ):
                                    if ( myType != cfg['type'] ):
                                        continue
                                myStatus = myJson['data']['status']
                            elif ( cfg['metric'][:2] == "sr" ):
                                # check document has SiteReadiness keys:
                                if (( 'path' not in myJson['metadata'] ) or
                                    ( 'timestamp' not in myJson['metadata'] ) or
                                    ( 'name' not in myJson['data'] ) or
                                    ( 'status' not in myJson['data'] )):
                                    continue
                                if ( myJson['metadata']['path'] !=
                                     cfg['metric'] ):
                                    continue
                                tis = int(myJson['metadata']['timestamp']/1000)
                                if ( tis < startTIS ):
                                    continue
                                if ( tis >= limitTIS ):
                                    continue
                                myName = myJson['data']['name']
                                if ( cfg['name'] != "*" ):
                                    if ( myName != cfg['name'] ):
                                        continue
                                myType = "site"
                                myStatus = myJson['data']['status']
                            elif ( cfg['metric'][:3] == "sts" ):
                                # check document has required SiteStatus keys:
                                if (( 'path' not in myJson['metadata'] ) or
                                    ( 'timestamp' not in myJson['metadata'] ) or
                                    ( 'name' not in myJson['data'] ) or
                                    ( 'status' not in myJson['data'] ) or
                                    ( 'prod_status' not in myJson['data'] ) or
                                    ( 'crab_status' not in myJson['data'] )):
                                    continue
                                if ( myJson['metadata']['path'] !=
                                     cfg['metric'] ):
                                    continue
                                tis = int(myJson['metadata']['timestamp']/1000)
                                if ( tis < startTIS ):
                                    continue
                                if ( tis >= limitTIS ):
                                    continue
                                myName = myJson['data']['name']
                                if ( cfg['name'] != "*" ):
                                    if ( myName != cfg['name'] ):
                                        continue
                                myType = "site"
                                myStatus = myJson['data']['status']
                            else:
                                continue
                            version = myJson['metadata']['kafka_timestamp']
                            docid = myJson['metadata']['_id']
                            tbin = int( tis / cfg['period'] )
                            #
                            myJson['data']['***VERSION***'] = version
                            myJson['data']['***DOCID***'] = docid
                            #
                            if tbin not in lftch_monitdocs:
                                lftch_monitdocs[ tbin ] = []
                            lftch_monitdocs[tbin].append( myJson['data'] )
                            #
                            logging.log(15, "   adding [%d] %s / %s : %s" %
                                              (tbin, myName, myType, myStatus))

                    except json.decoder.JSONDecodeError as excptn:
                        logging.error("JSON decoding failure, %s: %s" %
                                                       (fileName, str(excptn)))
                    except FileNotFoundError as excptn:
                        logging.error("HDFS file not found, %s: %s" %
                                                       (fileName, str(excptn)))
                    except IOError as excptn:
                        logging.error("HDFS access failure, %s: %s" %
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
        logging.error("Failed to fetch MonIT documents from HDFS")

    if ( logging.getLogger().level <= 20 ):
        no_docs = 0
        for tbin in lftch_monitdocs:
            no_docs += len( lftch_monitdocs[tbin] )
        logging.info("found %d relevant docs in %d timebins in MonIT" %
                                               (no_docs, len(lftch_monitdocs)))

    return lftch_monitdocs
# ########################################################################### #



def lftch_compose_etf(cfg, docs):
    """function to compose a JSON string from the provided ETF documents"""
    # #################################################################### #
    # compose an annotated JSON string from the provided SAM ETF documents #
    # #################################################################### #


    # organize documents by timebin and hostname/probe within:
    # ========================================================
    myDocs = {}
    for tbin in docs:
        # order documents in timebin:
        for myDoc in docs[tbin]:
            myProbe = myDoc['metric_name'].split("-/cms/Role=",1)[0]
            try:
                myDoc['***ORDER***'] = LFTCH_PROBE_ORDER.index( myProbe[8:] )
            except ValueError:
                myDoc['***ORDER***'] = len( LFTCH_PROBE_ORDER )
        myDocs[tbin] = sorted(docs[tbin],
             key=lambda k: [k['dst_hostname'],k['***ORDER***'],k['timestamp']])


    # convert document dictionary into annotated JSON array string:
    # =============================================================
    jsonString = "["
    commaFlag = False
    #
    for tbin in sorted( myDocs.keys() ):
        #logging.log(9, "   %s for %d (%s)" %
        #              (cfg['metric'], tbin, time.strftime("%Y-%b-%d %H:%M:%S",
        #                                    time.gmtime(tbin*cfg['period']))))
        if ( commaFlag ):
            jsonString += "\n\n\n"
        #
        hdrString = ((",\n {\n   \"metric\": \"%s\",\n" +
                             "   \"time-bin\": %d,   # %s\n" +
                             "   \"version\": \"%%d.%%3.3d\",   # %%s\n" +
                             "   \"doc-id\": \"%%s\",\n" +
                             "   \"data\": {\n") %
                     (cfg['metric'], tbin, time.strftime("%Y-%b-%d %H:%M UTC",
                                             time.gmtime(tbin*cfg['period']))))

        for myDoc in myDocs[tbin]:
            #logging.log(9, "      %s / %s status: %s" % (myDoc['name'],
            #                                  myDoc['type'], myDoc['status']))
            if commaFlag:
                jsonString += hdrString % (int(myDoc['***VERSION***']/1000),
                    myDoc['***VERSION***'] % 1000,
                    time.strftime("%Y-%b-%d %H:%M:%S UTC",
                                time.gmtime(int(myDoc['***VERSION***']/1000))),
                    myDoc['***DOCID***'])
            else:
                jsonString += hdrString[1:] % (int(myDoc['***VERSION***']/1000),
                    myDoc['***VERSION***'] % 1000,
                    time.strftime("%Y-%b-%d %H:%M:%S UTC",
                                time.gmtime(int(myDoc['***VERSION***']/1000))),
                    myDoc['***DOCID***'])
            #
            jsonString += (("      \"dst_hostname\": \"%s\",\n" +
                            "      \"service_flavour\": \"%s\",\n" +
                            "      \"metric_name\": \"%s\",\n" +
                            "      \"status\": \"%s\",\n" +
                            "      \"timestamp\": \"%d.%3.3d\",   # %s\n") %
                           (myDoc['dst_hostname'], myDoc['service_flavour'],
                            myDoc['metric_name'], myDoc['status'],
                            int(myDoc['timestamp']/1000), 
                            myDoc['timestamp'] % 1000,
                            time.strftime("%Y-%m-%d %H:%M:%S UTC",
                                   time.gmtime(int(myDoc['timestamp']/1000)))))
            if 'details' in myDoc:
                jsonString += ("      \"details\": \"%s\",\n" %
                                          myDoc['details'].replace('\n','\\n'))
            for key in myDoc:
                if key not in ["dst_hostname", "service_flavour",
                               "metric_name", "status", "timestamp", "details",
                               "summary", "***VERSION***", "***DOCID***",
                               "***ORDER***" ]:
                    jsonString += ("      \"%s\": \"%s\",\n" % (key,
                                                              str(myDoc[key])))
            if 'summary' in myDoc:
                jsonString += (",\n      \"summary\": \"%s\"\n   }\n }" %
                                                              myDoc['summary'])
            else:
                jsonString += (",\n      \"summary\": null\n   }\n }")
            commaFlag = True
    jsonString += "\n]\n"

    return jsonString



def lftch_compose_down(cfg, docs):
    """function to compose a JSON string from the provided downtime docs"""
    # ##################################################################### #
    # compose an annotated JSON string from the provided downtime documents #
    # ##################################################################### #


    # organize documents by timebin and site/CE/SRM/XROOTD/perfSONAR within:
    # ======================================================================
    myDocs = {}
    for tbin in docs:
        # identify superseded documents:
        highestVersion = 0
        for myDoc in docs[tbin]:
            if ( myDoc['***VERSION***'] > highestVersion ):
                highestVersion = myDoc['***VERSION***']
        # order documents in timebin:
        for myDoc in docs[tbin]:
            try:
                ctgry = LFTCH_SERVICE_TYPES[ myDoc['type'] ]
                myOrder = LFTCH_SERVICE_ORDER.index( ctgry )
            except (KeyError, ValueError):
                myOrder = len( LFTCH_SERVICE_ORDER )
           # allow 5 min for MonIT importer processing
            if ( (highestVersion - myDoc['***VERSION***']) > 300000 ):
                myOrder += LFTCH_SUPERSEDED + \
                        int( (highestVersion - myDoc['***VERSION***'])/300000 )
            myDoc['***ORDER***'] = myOrder
        myDocs[tbin] = sorted(docs[tbin],
                 key=lambda k: [k['***ORDER***'], k['name'], k['duration'][0]])


    # convert document dictionary into annotated JSON array string:
    # =============================================================
    jsonString = "["
    commaFlag = False
    #
    for tbin in sorted( myDocs.keys() ):
        #logging.log(9, "   %s for %d (%s)" %
        #              (cfg['metric'], tbin, time.strftime("%Y-%b-%d %H:%M:%S",
        #                                    time.gmtime(tbin*cfg['period']))))
        if ( commaFlag ):
            jsonString += "\n\n\n"
        #
        hdrString = ((",\n {\n   \"metric\": \"%s\",\n" +
                             "   \"time-bin\": %d,   # %s\n" +
                             "   \"version\": \"%%d.%%3.3d\",  # %%s\n" +
                             "   \"doc-id\": \"%%s\",\n" +
                             "   \"data\": {\n") %
                     (cfg['metric'], tbin, time.strftime("%Y-%b-%d %H:%M",
                                             time.gmtime(tbin*cfg['period']))))

        for myDoc in myDocs[tbin]:
            #logging.log(9, "      %s / %s status: %s" % (myDoc['name'],
            #                                  myDoc['type'], myDoc['status']))
            if commaFlag:
                jsonString += hdrString % (int(myDoc['***VERSION***']/1000),
                    myDoc['***VERSION***'] % 1000,
                    time.strftime("%Y-%b-%d %H:%M:%S UTC",
                                time.gmtime(int(myDoc['***VERSION***']/1000))),
                    myDoc['***DOCID***'])
            else:
                jsonString += hdrString[1:] % (int(myDoc['***VERSION***']/1000),
                    myDoc['***VERSION***'] % 1000,
                    time.strftime("%Y-%b-%d %H:%M:%S UTC",
                                time.gmtime(int(myDoc['***VERSION***']/1000))),
                    myDoc['***DOCID***'])
            #
            jsonString += (("      \"name\": \"%s\",\n" +
                            "      \"type\": \"%s\",\n" +
                            "      \"status\": \"%s\",\n" +
                            "      \"duration\": [%d, %d],\n") %
                           (myDoc['name'], myDoc['type'], myDoc['status'],
                            myDoc['duration'][0], myDoc['duration'][1]))
            if 'detail' in myDoc:
                jsonString += ("      \"detail\": \"%s\"" %
                                           myDoc['detail'].replace('\n','\\n'))
            else:
                jsonString += ("      \"detail\": null")
            if 'author' in myDoc:
                if myDoc['author'] is not None:
                    jsonString += (",\n      \"author\": \"%s\"" %
                                                               myDoc['author'])
            jsonString += "\n   }\n }"
            commaFlag = True
    jsonString += "\n]\n"

    return jsonString



def lftch_compose_sam(cfg, docs):
    """function to compose a JSON string from the provided SAM documents"""
    # #################################################################### #
    # compose an annotated JSON string from the provided CMS SAM documents #
    # #################################################################### #


    # organize documents by timebin and site/CE/SRM/XROOTD/perfSONAR within:
    # ======================================================================
    myDocs = {}
    for tbin in docs:
        # identify superseded documents:
        highestVersions = {}
        for myDoc in docs[tbin]:
            key = ( myDoc['name'], myDoc['type'] )
            if key not in highestVersions:
                highestVersions[key] = myDoc['***VERSION***']
            elif ( myDoc['***VERSION***'] > highestVersions[key] ):
                highestVersions[key] = myDoc['***VERSION***']
        # order documents in timebin:
        for myDoc in docs[tbin]:
            key = ( myDoc['name'], myDoc['type'] )
            try:
                myOrder = LFTCH_SERVICE_ORDER.index( myDoc['type'] )
            except ValueError:
                myOrder = len( LFTCH_SERVICE_ORDER )
            if ( myDoc['***VERSION***'] < highestVersions[key] ):
                myOrder += LFTCH_SUPERSEDED + \
                    int( (highestVersions[key]-myDoc['***VERSION***'])/300000 )
            myDoc['***ORDER***'] = myOrder
        myDocs[tbin] = sorted(docs[tbin],
                                   key=lambda k: [k['***ORDER***'], k['name']])


    # convert document dictionary into annotated JSON array string:
    # =============================================================
    jsonString = "["
    commaFlag = False
    #
    for tbin in sorted( myDocs.keys() ):
        #logging.log(9, "   %s for %d (%s)" %
        #              (cfg['metric'], tbin, time.strftime("%Y-%b-%d %H:%M:%S",
        #                                    time.gmtime(tbin*cfg['period']))))
        if ( commaFlag ):
            jsonString += "\n\n\n"
        #
        hdrString = ((",\n {\n   \"metric\": \"%s\",\n" +
                             "   \"time-bin\": %d,   # %s\n" +
                             "   \"version\": \"%%d.%%3.3d\",  # %%s\n" +
                             "   \"doc-id\": \"%%s\",\n" +
                             "   \"data\": {\n") %
                     (cfg['metric'], tbin, time.strftime("%Y-%b-%d %H:%M UTC",
                                             time.gmtime(tbin*cfg['period']))))
        #
        for myDoc in myDocs[tbin]:
            #logging.log(9, "      %s / %s status: %s" % (myDoc['name'],
            #                                  myDoc['type'], myDoc['status']))
            if commaFlag:
                jsonString += hdrString % (int(myDoc['***VERSION***']/1000),
                    myDoc['***VERSION***'] % 1000,
                    time.strftime("%Y-%b-%d %H:%M:%S UTC",
                                time.gmtime(int(myDoc['***VERSION***']/1000))),
                    myDoc['***DOCID***'])
            else:
                jsonString += hdrString[1:] % (int(myDoc['***VERSION***']/1000),
                    myDoc['***VERSION***'] % 1000,
                    time.strftime("%Y-%b-%d %H:%M:%S UTC",
                                time.gmtime(int(myDoc['***VERSION***']/1000))),
                    myDoc['***DOCID***'])
            #
            jsonString += (("      \"name\": \"%s\",\n" +
                            "      \"type\": \"%s\",\n" +
                            "      \"status\": \"%s\",\n") %
                           (myDoc['name'], myDoc['type'], myDoc['status']))
            if 'availability' in myDoc:
                if myDoc['availability'] is not None:
                    jsonString += ("      \"availability\": %.3f,\n" %
                                   myDoc['availability'])
                else:
                    jsonString += ("      \"availability\": null,\n")
            else:
                jsonString += ("      \"availability\": null,\n")
            if 'reliability' in myDoc:
                if myDoc['reliability'] is not None:
                    jsonString += ("      \"reliability\": %.3f,\n" %
                                   myDoc['reliability'])
                else:
                    jsonString += ("      \"reliability\": null,\n")
            elif ( myDoc['type'] == "site" ):
                jsonString += ("      \"reliability\": null,\n")
            if 'detail' in myDoc:
                jsonString += ("      \"detail\": \"%s\"" %
                               myDoc['detail'].replace('\n','\\n'))
            else:
                jsonString += ("      \"detail\": null")
            if 'author' in myDoc:
                if myDoc['author'] is not None:
                    jsonString += (",\n      \"author\": \"%s\"" %
                                                               myDoc['author'])
            jsonString += "\n   }\n }"
            commaFlag = True
    jsonString += "\n]\n"

    return jsonString



def lftch_compose_hc(cfg, docs):
    """function to compose a JSON string from the provided HC documents"""
    # ################################################################### #
    # compose an annotated JSON string from the provided CMS HC documents #
    # ################################################################### #


    # organize documents by timebin and version within:
    # =================================================
    myDocs = {}
    for tbin in docs:
        # identify superseded documents:
        highestVersions = {}
        for myDoc in docs[tbin]:
            if myDoc['site'] not in highestVersions:
                highestVersions[ myDoc['site'] ] = myDoc['***VERSION***']
            elif ( myDoc['***VERSION***'] > highestVersions[ myDoc['site'] ] ):
                highestVersions[ myDoc['site'] ] = myDoc['***VERSION***']
        # order documents in timebin:
        for myDoc in docs[tbin]:
            myDoc['***ORDER***'] = highestVersions[myDoc['site']] - \
                                                         myDoc['***VERSION***']
        myDocs[tbin] = sorted(docs[tbin],
                                   key=lambda k: [k['site'], k['***ORDER***']])


    # convert document dictionary into annotated JSON array string:
    # =============================================================
    jsonString = "["
    commaFlag = False
    #
    for tbin in sorted( myDocs.keys() ):
        #logging.log(9, "   %s for %d (%s)" %
        #              (cfg['metric'], tbin, time.strftime("%Y-%b-%d %H:%M:%S",
        #                                    time.gmtime(tbin*cfg['period']))))
        if ( commaFlag ):
            jsonString += "\n\n\n"
        #
        hdrString = ((",\n {\n   \"metric\": \"%s\",\n" +
                             "   \"time-bin\": %d,   # %s\n" +
                             "   \"version\": \"%%d.%%3.3d\",  # %%s\n" +
                             "   \"doc-id\": \"%%s\",\n" +
                             "   \"data\": {\n") %
                     (cfg['metric'], tbin, time.strftime("%Y-%b-%d %H:%M UTC",
                                             time.gmtime(tbin*cfg['period']))))
        #
        for myDoc in myDocs[tbin]:
            #logging.log(9, "      %s / %s status: %s" % (myDoc['name'],
            #                                  myDoc['type'], myDoc['status']))
            if commaFlag:
                jsonString += hdrString % (int(myDoc['***VERSION***']/1000),
                    myDoc['***VERSION***'] % 1000,
                    time.strftime("%Y-%b-%d %H:%M:%S UTC",
                                time.gmtime(int(myDoc['***VERSION***']/1000))),
                    myDoc['***DOCID***'])
            else:
                jsonString += hdrString[1:] % (int(myDoc['***VERSION***']/1000),
                    myDoc['***VERSION***'] % 1000,
                    time.strftime("%Y-%b-%d %H:%M:%S UTC",
                                time.gmtime(int(myDoc['***VERSION***']/1000))),
                    myDoc['***DOCID***'])
            #
            jsonString += (("      \"site\": \"%s\",\n" +
                            "      \"status\": \"%s\",\n") %
                           (myDoc['site'], myDoc['status']))
            if 'value' in MyDoc:
                if myDoc['value'] is not None:
                    jsonString += ("      \"value\": %.3f,\n" %
                                   myDoc['value'])
                else:
                    jsonString += ("      \"value\": null,\n")
            if 'detail' in myDoc:
                jsonString += ("      \"detail\": \"%s\"" %
                               myDoc['detail'].replace('\n','\\n'))
            if 'author' in myDoc:
                if myDoc['author'] is not None:
                    jsonString += (",\n      \"author\": \"%s\"" %
                                                               myDoc['author'])
            jsonString += "\n   }\n }"
            commaFlag = True
    jsonString += "\n]\n"

    return jsonString



def lftch_compose_fts(cfg, docs):
    """function to compose a JSON string from the provided FTS documents"""
    # #################################################################### #
    # compose an annotated JSON string from the provided CMS FTS documents #
    # #################################################################### #


    # organize documents by timebin and site/destination/source/link within:
    # ======================================================================
    myDocs = {}
    for tbin in docs:
        # identify superseded documents:
        highestVersions = {}
        for myDoc in docs[tbin]:
            key = ( myDoc['name'], myDoc['type'] )
            if key not in highestVersions:
                highestVersions[key] = myDoc['***VERSION***']
            elif ( myDoc['***VERSION***'] > highestVersions[key] ):
                highestVersions[key] = myDoc['***VERSION***']
        # order documents in timebin:
        for myDoc in docs[tbin]:
            key = ( myDoc['name'], myDoc['type'] )
            try:
                myOrder = LFTCH_TRANSFER_ORDER.index( myDoc['type'] )
            except ValueError:
                myOrder = len( LFTCH_TRANSFER_ORDER )
            if ( myDoc['***VERSION***'] < highestVersions[key] ):
                myOrder += LFTCH_SUPERSEDED + \
                    int( (highestVersions[key]-myDoc['***VERSION***'])/300000 )
            myDoc['***ORDER***'] = myOrder
        myDocs[tbin] = sorted(docs[tbin],
                                   key=lambda k: [k['***ORDER***'], k['name']])


    # convert document dictionary into annotated JSON array string:
    # =============================================================
    jsonString = "["
    commaFlag = False
    #
    for tbin in sorted( myDocs.keys() ):
        #logging.log(9, "   %s for %d (%s)" %
        #              (cfg['metric'], tbin, time.strftime("%Y-%b-%d %H:%M:%S",
        #                                    time.gmtime(tbin*cfg['period']))))
        if ( commaFlag ):
            jsonString += "\n\n\n"
        #
        hdrString = ((",\n {\n   \"metric\": \"%s\",\n" +
                             "   \"time-bin\": %d,   # %s\n" +
                             "   \"version\": \"%%d.%%3.3d\",  # %%s\n" +
                             "   \"doc-id\": \"%%s\",\n" +
                             "   \"data\": {\n") %
                     (cfg['metric'], tbin, time.strftime("%Y-%b-%d %H:%M UTC",
                                             time.gmtime(tbin*cfg['period']))))
        #
        for myDoc in myDocs[tbin]:
            #logging.log(9, "      %s / %s status: %s" % (myDoc['name'],
            #                                  myDoc['type'], myDoc['status']))
            if commaFlag:
                jsonString += hdrString % (int(myDoc['***VERSION***']/1000),
                    myDoc['***VERSION***'] % 1000,
                    time.strftime("%Y-%b-%d %H:%M:%S UTC",
                                time.gmtime(int(myDoc['***VERSION***']/1000))),
                    myDoc['***DOCID***'])
            else:
                jsonString += hdrString[1:] % (int(myDoc['***VERSION***']/1000),
                    myDoc['***VERSION***'] % 1000,
                    time.strftime("%Y-%b-%d %H:%M:%S UTC",
                                time.gmtime(int(myDoc['***VERSION***']/1000))),
                    myDoc['***DOCID***'])
            #
            jsonString += (("      \"name\": \"%s\",\n" +
                            "      \"type\": \"%s\",\n" +
                            "      \"status\": \"%s\",\n") %
                           (myDoc['name'], myDoc['type'], myDoc['status']))
            if 'quality' in myDoc:
                if myDoc['quality'] is not None:
                    jsonString += ("      \"quality\": %.3f,\n" %
                                   myDoc['quality'])
                else:
                    jsonString += ("      \"quality\": null,\n")
            else:
                jsonString += ("      \"quality\": null,\n")
            if 'detail' in myDoc:
                if myDoc['detail'] is not None:
                    jsonString += ("      \"detail\": \"%s\"" %
                                   myDoc['detail'].replace('\n','\\n'))
                else:
                    jsonString += ("      \"detail\": null,\n")
            else:
                jsonString += ("      \"detail\": null")
            if 'author' in myDoc:
                if myDoc['author'] is not None:
                    jsonString += (",\n      \"author\": \"%s\"" %
                                                               myDoc['author'])
            jsonString += "\n   }\n }"
            commaFlag = True
    jsonString += "\n]\n"

    return jsonString



def lftch_compose_sr(cfg, docs):
    """function to compose a JSON string from the provided SR documents"""
    # ##################################################################### #
    # compose an annotated JSON string from the provided SiteReadiness docs #
    # ##################################################################### #


    # organize documents by timebin and version within:
    # =================================================
    myDocs = {}
    for tbin in docs:
        # identify superseded documents:
        highestVersions = {}
        for myDoc in docs[tbin]:
            if myDoc['name'] not in highestVersions:
                highestVersions[ myDoc['name'] ] = myDoc['***VERSION***']
            elif ( myDoc['***VERSION***'] > highestVersions[ myDoc['name'] ] ):
                highestVersions[ myDoc['name'] ] = myDoc['***VERSION***']
        # order documents in timebin:
        for myDoc in docs[tbin]:
            myDoc['***ORDER***'] = highestVersions[myDoc['name']] - \
                                                         myDoc['***VERSION***']
        myDocs[tbin] = sorted(docs[tbin],
                                   key=lambda k: [k['name'], k['***ORDER***']])


    # convert document dictionary into annotated JSON array string:
    # =============================================================
    jsonString = "["
    commaFlag = False
    #
    for tbin in sorted( myDocs.keys() ):
        #logging.log(9, "   %s for %d (%s)" %
        #              (cfg['metric'], tbin, time.strftime("%Y-%b-%d %H:%M:%S",
        #                                    time.gmtime(tbin*cfg['period']))))
        if ( commaFlag ):
            jsonString += "\n\n\n"
        #
        hdrString = ((",\n {\n   \"metric\": \"%s\",\n" +
                             "   \"time-bin\": %d,   # %s\n" +
                             "   \"version\": \"%%d.%%3.3d\",  # %%s\n" +
                             "   \"doc-id\": \"%%s\",\n" +
                             "   \"data\": {\n") %
                     (cfg['metric'], tbin, time.strftime("%Y-%b-%d %H:%M UTC",
                                             time.gmtime(tbin*cfg['period']))))
        #
        for myDoc in myDocs[tbin]:
            #logging.log(9, "      %s / %s status: %s" % (myDoc['name'],
            #                                  myDoc['type'], myDoc['status']))
            if commaFlag:
                jsonString += hdrString % (int(myDoc['***VERSION***']/1000),
                    myDoc['***VERSION***'] % 1000,
                    time.strftime("%Y-%b-%d %H:%M:%S UTC",
                                time.gmtime(int(myDoc['***VERSION***']/1000))),
                    myDoc['***DOCID***'])
            else:
                jsonString += hdrString[1:] % (int(myDoc['***VERSION***']/1000),
                    myDoc['***VERSION***'] % 1000,
                    time.strftime("%Y-%b-%d %H:%M:%S UTC",
                                time.gmtime(int(myDoc['***VERSION***']/1000))),
                    myDoc['***DOCID***'])
            #
            jsonString += (("      \"name\": \"%s\",\n" +
                            "      \"status\": \"%s\",\n") %
                           (myDoc['name'], myDoc['status']))
            if 'value' in MyDoc:
                if myDoc['value'] is not None:
                    jsonString += ("      \"value\": %.3f,\n" %
                                   myDoc['value'])
                else:
                    jsonString += ("      \"value\": null,\n")
            else:
                jsonString += ("      \"value\": null,\n")
            if 'detail' in myDoc:
                if myDoc['detail'] is not None:
                    jsonString += ("      \"detail\": \"%s\"" %
                                   myDoc['detail'].replace('\n','\\n'))
                else:
                    jsonString += ("      \"detail\": null,\n")
            else:
                jsonString += ("      \"detail\": null")
            if 'author' in myDoc:
                if myDoc['author'] is not None:
                    jsonString += (",\n      \"author\": \"%s\"" %
                                                               myDoc['author'])
            jsonString += "\n   }\n }"
            commaFlag = True
    jsonString += "\n]\n"

    return jsonString



def lftch_compose_sts(cfg, docs):
    """function to compose a JSON string from the provided STS documents"""
    # ####################################################################### #
    # compose an annotated JSON string from the provided SiteStatus documents #
    # ####################################################################### #


    # organize documents by timebin and version within:
    # =================================================
    myDocs = {}
    for tbin in docs:
        # identify superseded documents:
        highestVersions = {}
        for myDoc in docs[tbin]:
            if myDoc['name'] not in highestVersions:
                highestVersions[ myDoc['name'] ] = myDoc['***VERSION***']
            elif ( myDoc['***VERSION***'] > highestVersions[ myDoc['name'] ] ):
                highestVersions[ myDoc['name'] ] = myDoc['***VERSION***']
        # order documents in timebin:
        for myDoc in docs[tbin]:
            myDoc['***ORDER***'] = highestVersions[myDoc['name']] - \
                                                         myDoc['***VERSION***']
        myDocs[tbin] = sorted(docs[tbin],
                                   key=lambda k: [k['name'], k['***ORDER***']])


    # convert document dictionary into annotated JSON array string:
    # =============================================================
    jsonString = "["
    commaFlag = False
    #
    for tbin in sorted( myDocs.keys() ):
        #logging.log(9, "   %s for %d (%s)" %
        #              (cfg['metric'], tbin, time.strftime("%Y-%b-%d %H:%M:%S",
        #                                    time.gmtime(tbin*cfg['period']))))
        if ( commaFlag ):
            jsonString += "\n\n\n"
        #
        hdrString = ((",\n {\n   \"metric\": \"%s\",\n" +
                             "   \"time-bin\": %d,   # %s\n" +
                             "   \"version\": \"%%d.%%3.3d\",  # %%s\n" +
                             "   \"doc-id\": \"%%s\",\n" +
                             "   \"data\": {\n") %
                     (cfg['metric'], tbin, time.strftime("%Y-%b-%d %H:%M UTC",
                                             time.gmtime(tbin*cfg['period']))))
        #
        for myDoc in myDocs[tbin]:
            #logging.log(9, "      %s / %s status: %s" % (myDoc['name'],
            #                                  myDoc['type'], myDoc['status']))
            if commaFlag:
                jsonString += hdrString % (int(myDoc['***VERSION***']/1000),
                    myDoc['***VERSION***'] % 1000,
                    time.strftime("%Y-%b-%d %H:%M:%S UTC",
                                time.gmtime(int(myDoc['***VERSION***']/1000))),
                    myDoc['***DOCID***'])
            else:
                jsonString += hdrString[1:] % (int(myDoc['***VERSION***']/1000),
                    myDoc['***VERSION***'] % 1000,
                    time.strftime("%Y-%b-%d %H:%M:%S UTC",
                                time.gmtime(int(myDoc['***VERSION***']/1000))),
                    myDoc['***DOCID***'])
            #
            jsonString += (("      \"site\": \"%s\",\n" +
                            "      \"status\": \"%s\",\n" +
                            "      \"prod_status\": \"%s\",\n" +
                            "      \"crab_status\": \"%s\",\n") %
                           (myDoc['name'], myDoc['status'],
                            myDoc['prod_status'], myDoc['crab_status']))
            if 'detail' in myDoc:
                if myDoc['detail'] is not None:
                    jsonString += ("      \"detail\": \"%s\"" %
                                   myDoc['detail'].replace('\n','\\n'))
                else:
                    jsonString += ("      \"detail\": null,\n")
            else:
                jsonString += ("      \"detail\": null")
            if 'author' in myDoc:
                if myDoc['author'] is not None:
                    jsonString += (",\n      \"author\": \"%s\"" %
                                                               myDoc['author'])
            jsonString += "\n   }\n }"
            commaFlag = True
    jsonString += "\n]\n"

    return jsonString



def lftch_write_json(cfg, docs):
    """function to write documents as easy readable JSON to a file"""
    # ###################################################### #
    # write the documents as annotated JSON according to cfg #
    # ###################################################### #

    if ( cfg['metric'][:3] == "etf" ):
        jsonString = lftch_compose_etf(cfg, docs)
    elif ( cfg['metric'][:4] == "down" ):
        jsonString = lftch_compose_down(cfg, docs)
    elif ( cfg['metric'][:3] == "sam" ):
        jsonString = lftch_compose_sam(cfg, docs)
    elif ( cfg['metric'][:2] == "hc" ):
        jsonString = lftch_compose_hc(cfg, docs)
    elif ( cfg['metric'][:3] == "fts" ):
        jsonString = lftch_compose_fts(cfg, docs)
    elif ( cfg['metric'][:2] == "sr" ):
        jsonString = lftch_compose_sr(cfg, docs)
    elif ( cfg['metric'][:3] == "sts" ):
        jsonString = lftch_compose_sts(cfg, docs)
    #
    if ( jsonString == "[\n]\n" ):
        logging.warning("Skipping writing of document-devoid JSON string")
        return 1


    try:
        with open(cfg['json'], 'wt') as myFile:
            myFile.write( jsonString )
        try:
            os.chmod(cfg['json'], 0o644)
        except (IOError, OSError) as excptn:
            logging.warning("Failed to chmod annotated JSON file, %s" %
                                                                   str(excptn))
        logging.log(25, "JSON array written to file %s" % cfg['json'])
    except (IOError, OSError) as excptn:
        logging.critical("Writing of annotated JSON failed, %s" % str(excptn))
        try:
            os.unlink( cfg['json'] )
        except:
            pass
        return 1

    return 0



def lftch_print_json(cfg, docs):
    """function to print documents as easy readable JSON to stdout"""
    # ###################################################### #
    # print the documents as annotated JSON according to cfg #
    # ###################################################### #

    if ( cfg['metric'][:3] == "etf" ):
        jsonString = lftch_compose_etf(cfg, docs)
    elif ( cfg['metric'][:4] == "down" ):
        jsonString = lftch_compose_down(cfg, docs)
    elif ( cfg['metric'][:3] == "sam" ):
        jsonString = lftch_compose_sam(cfg, docs)
    elif ( cfg['metric'][:2] == "hc" ):
        jsonString = lftch_compose_hc(cfg, docs)
    elif ( cfg['metric'][:3] == "fts" ):
        jsonString = lftch_compose_fts(cfg, docs)
    elif ( cfg['metric'][:2] == "sr" ):
        jsonString = lftch_compose_sr(cfg, docs)
    elif ( cfg['metric'][:3] == "sts" ):
        jsonString = lftch_compose_sts(cfg, docs)
    #
    if ( jsonString == "[\n]\n" ):
        logging.warning("Skipping writing of document-devoid JSON string")
        return 1


    sys.stderr.flush()
    print(jsonString)
    sys.stdout.flush()
    logging.log(25, "JSON array printed to stdout")

    return 0
# ########################################################################### #



def lftch_maindvi_etf(cfg, docs):
    """function to write ETF documents as HTML table to a file"""
    # ################################################################# #
    # prepare mainDVI section with SAM ETF information according to cfg #
    # ################################################################# #


    # organize documents by timebin and hostname/probe within:
    # ========================================================
    myDocs = {}
    mx_docs = 0
    for tbin in docs:
        no_docs = len( docs[tbin] )
        if ( no_docs > mx_docs ):
            mx_docs = no_docs
        # 
        # order documents in timebin:
        for myDoc in docs[tbin]:
            myProbe = myDoc['metric_name'].split("-/cms/Role=",1)[0]
            try:
                myDoc['***ORDER***'] = LFTCH_PROBE_ORDER.index( myProbe[8:] )
            except ValueError:
                myDoc['***ORDER***'] = len( LFTCH_PROBE_ORDER )
        myDocs[tbin] = sorted(docs[tbin],
             key=lambda k: [k['dst_hostname'],k['***ORDER***'],k['timestamp']])


    # write mainDVI ETF HTML section:
    # ===============================
    myHTML = cfg['html'] + "_wrk"
    #
    try:
        with open(myHTML, 'wt') as myFile:
            ncols = len( myDocs )
            tbins = sorted( myDocs.keys() )
            #
            myFile.write("<TABLE BORDER=\"0\" CELLPADDING=\"0\" CELLSPACING=" +
                         "\"16\">\n<TR>\n")
            for tbin in tbins:
                sTIS = tbin * cfg['period']
                eTIS = sTIS + cfg['period']
                myFile.write("   <TH>Timebin %d (<B>%s</B> to %s UTC)\n" %
                    (tbin, time.strftime("%Y-%m-%d %H:%M", time.gmtime(sTIS)),
                                    time.strftime("%H:%M", time.gmtime(eTIS))))
            #
            for indx in range(mx_docs):
                #
                myFile.write("<TR ALIGN=\"left\" VALIGN=\"top\">\n")
                for tbin in tbins:
                    #
                    if ( indx < len( myDocs[tbin] ) ):
                        myFile.write("   <TD>\n      <TABLE WIDTH=\"100%\" B" +
                                     "ORDER=\"1\" CELLPADDING=\"2\" CELLSPAC" +
                                     "ING=\"0\">\n      <TR>\n         <TH>D" +
                                     "escription\n         <TH>Value\n")
                        myDoc = myDocs[tbin][indx]
                        if ( myDoc['status'] == "OK" ):
                            myColour = "#CDFFD4"
                        elif ( myDoc['status'] == "WARNING" ):
                            myColour = "#FFFFCC"
                        elif ( myDoc['status'] == "CRITICAL" ):
                            myColour = "#FFCCCC"
                        else:
                            myColour = "#FFFFFF"
                        myFile.write(("      <TR>\n         <TD NOWRAP>Host " +
                                      "name\n         <TD BGCOLOR=\"%s\" NOW" +
                                      "RAP>%s\n") %
                                     (myColour, myDoc['dst_hostname']))
                        myFile.write(("      <TR>\n         <TD NOWRAP>Probe" +
                                      " name\n         <TD BGCOLOR=\"%s\" NO" +
                                      "WRAP>%s\n") %
                                     (myColour, myDoc['metric_name']))
                        if 'summary' in myDoc:
                            myFile.write(("      <TR>\n         <TD NOWRAP>S" +
                                          "ummary\n         <TD BGCOLOR=\"%s" +
                                          "\" NOWRAP>%s\n") %
                                         (myColour, myDoc['summary']))
                        myFile.write(("      <TR>\n         <TD NOWRAP>Servi" +
                                      "ce flavour\n         <TD BGCOLOR=\"%s" +
                                      "\" NOWRAP>%s\n") %
                                     (myColour, myDoc['service_flavour']))
                        myFile.write(("      <TR>\n         <TD NOWRAP>Time " +
                                      "test finished\n         <TD BGCOLOR=" +
                                      "\"%s\" NOWRAP>%d.%3.3d (%s UTC)\n") %
                                     (myColour, int(myDoc['timestamp']/1000),
                                      myDoc['timestamp']%1000,
                                      time.strftime("%Y-%m-%d %H:%M:%S",
                                   time.gmtime(int(myDoc['timestamp']/1000)))))
                        if 'details' in myDoc:
                            myStrng = myDoc['details'].replace("\n", "<BR>")
                            myFile.write(("      <TR>\n         <TD NOWRAP>D" +
                                          "etails\n         <TD STYLE=\"word" +
                                          "-wrap: break-word;\" BGCOLOR=\"%s" +
                                          "\">%s\n") % (myColour, myStrng))
                        for key in myDoc:
                            if key not in ["dst_hostname", "service_flavour",
                                           "metric_name", "status",
                                           "timestamp", "details", "summary",
                                           "***VERSION***", "***DOCID***",
                                           "***ORDER***" ]:
                                myFile.write(("      <TR>\n         <TD NOWR" +
                                              "AP>%s\n         <TD STYLE=\"w" +
                                              "ord-wrap: break-word;\" BGCOL" +
                                              "OR=\"%s\">%s\n") %
                                             (key, myColour, str(myDoc[key])))
                        myFile.write(("      <TR>\n         <TD NOWRAP>Statu" +
                                      "s\n         <TD BGCOLOR=\"%s\" NOWRAP" +
                                      "><B>%s</B>\n") %
                                     (myColour, myDoc['status']))
                        myFile.write(("      <TR>\n         <TD NOWRAP>Versi" +
                                      "on number<BR>(= insert time)\n       " +
                                      "  <TD BGCOLOR=\"%s\" NOWRAP>%d.%3.3d " +
                                      "(%s UTC)\n") %
                                     (myColour,
                                      int(myDoc['***VERSION***']/1000),
                                      myDoc['***VERSION***']%1000,
                                      time.strftime("%Y-%m-%d %H:%M:%S",
                               time.gmtime(int(myDoc['***VERSION***']/1000)))))
                        myFile.write(("      <TR>\n         <TD NOWRAP>Docum" +
                                      "ent id\n         <TD BGCOLOR=\"%s\" N" +
                                      "OWRAP>%s\n") %
                                     (myColour, myDoc['***DOCID***']))
                        myFile.write("      </TABLE>\n      <BR>\n")
                    else:
                        myFile.write("   <TD>&nbsp;\n")
            myFile.write("</TABLE>\n")
        #
        try:
            os.chmod(myHTML, 0o644)
        except (IOError, OSError) as excptn:
            logging.warning("Failed to chmod ETF mainDVI section file, %s" %
                                                                   str(excptn))
        os.rename(myHTML, cfg['html'])

    except (IOError, OSError) as excptn:
        logging.critical("Writing of ETF mainDVI section failed, %s" %
                                                                   str(excptn))
        try:
            os.unlink( myHTML )
        except:
            pass
        return 1

    logging.log(25, "ETF docs as HTML table written to %s" %
                                                    cfg['html'].split("/")[-1])
    return 0



def lftch_maindvi_down(cfg, docs):
    """function to write downtime documents as HTML table to a file"""
    # ################################################################## #
    # prepare mainDVI section with downtime information according to cfg #
    # ################################################################## #


    # organize documents by timebin and site/CE/SRM/XROOTD/perfSONAR within:
    # ======================================================================
    myDocs = {}
    mx_docs = 0
    for tbin in docs:
        no_docs = len( docs[tbin] )
        if ( no_docs > mx_docs ):
            mx_docs = no_docs
        # 
        # identify superseded documents:
        highestVersion = 0
        for myDoc in docs[tbin]:
            if ( myDoc['***VERSION***'] > highestVersion ):
                highestVersion = myDoc['***VERSION***']
        # order documents in timebin:
        for myDoc in docs[tbin]:
            try:
                ctgry = LFTCH_SERVICE_TYPES[ myDoc['type'] ]
                myOrder = LFTCH_SERVICE_ORDER.index( ctgry )
            except (KeyError, ValueError):
                myOrder = len( LFTCH_SERVICE_ORDER )
            # allow 5 min for MonIT importer processing
            if ( (highestVersion - myDoc['***VERSION***']) > 300000 ):
                myOrder += LFTCH_SUPERSEDED + \
                        int( (highestVersion - myDoc['***VERSION***'])/300000 )
            myDoc['***ORDER***'] = myOrder
        myDocs[tbin] = sorted(docs[tbin],
                 key=lambda k: [k['***ORDER***'], k['name'], k['duration'][0]])


    # write mainDVI downtime HTML section:
    # ====================================
    myHTML = cfg['html'] + "_wrk"
    #
    try:
        with open(myHTML, 'wt') as myFile:
            ncols = len( myDocs )
            tbins = sorted( myDocs.keys() )
            #
            myFile.write("<TABLE BORDER=\"0\" CELLPADDING=\"0\" CELLSPACING=" +
                         "\"16\">\n<TR>\n")
            for tbin in tbins:
                sTIS = tbin * cfg['period']
                eTIS = sTIS + cfg['period']
                myFile.write("   <TH>Timebin %d (<B>%s</B> to %s UTC)\n" %
                    (tbin, time.strftime("%Y-%m-%d %H:%M", time.gmtime(sTIS)),
                                    time.strftime("%H:%M", time.gmtime(eTIS))))
            #
            for indx in range(mx_docs):
                #
                myFile.write("<TR ALIGN=\"left\" VALIGN=\"top\">\n")
                for tbin in tbins:
                    #
                    if ( indx < len( myDocs[tbin] ) ):
                        myFile.write("   <TD>\n      <TABLE WIDTH=\"100%\" B" +
                                     "ORDER=\"1\" CELLPADDING=\"2\" CELLSPAC" +
                                     "ING=\"0\">\n      <TR>\n         <TH>D" +
                                     "escription\n         <TH>Value\n")
                        myDoc = myDocs[tbin][indx]
                        if ( myDoc['***ORDER***'] > LFTCH_SUPERSEDED ):
                            myColour = "#DCDCDC"
                        elif ( myDoc['status'] == "ok" ):
                            myColour = "#CDFFD4"
                        elif ( myDoc['status'] == "downtime" ):
                            myColour = "#80AAFF"
                        elif ( myDoc['status'] == "partial" ):
                            myColour = "#CCDDFF"
                        else:
                            myColour = "#FFFFFF"
                        myFile.write(("      <TR>\n         <TD NOWRAP>Site/" +
                                      "Host name\n         <TD BGCOLOR=\"%s" +
                                      "\" NOWRAP>%s\n") %
                                     (myColour, myDoc['name']))
                        myFile.write(("      <TR>\n         <TD NOWRAP>Servi" +
                                      "ce type\n         <TD BGCOLOR=\"%s\" " +
                                      "NOWRAP>%s\n") %
                                     (myColour, myDoc['type']))
                        myFile.write(("      <TR>\n         <TD NOWRAP>Downt" +
                                      "ime state\n         <TD BGCOLOR=\"%s" +
                                      "\" NOWRAP><B>%s</B>\n") %
                                     (myColour, myDoc['status']))
                        myFile.write(("      <TR>\n         <TD NOWRAP>Durat" +
                                      "ion<BR>(from/to)\n         <TD BGCOLO" +
                                      "R=\"%s\" NOWRAP>%d (%s UTC)<BR>%d (%s" +
                                      " UTC)\n") %
                                     (myColour, myDoc['duration'][0],
                                      time.strftime("%Y-%m-%d %H:%M:%S",
                                            time.gmtime(myDoc['duration'][0])),
                                      myDoc['duration'][1],
                                      time.strftime("%Y-%m-%d %H:%M:%S",
                                           time.gmtime(myDoc['duration'][1]))))
                        if 'detail' in myDoc:
                            if (( myDoc['detail'] is not None ) and
                                ( myDoc['detail'] != "" )):
                                myGrid = myDoc['detail'].split(":")[0]
                                if ( myGrid == "EGI" ):
                                    myRef = int(myDoc['detail'].split(":")[1])
                                    myStrng = ("<A HREF=\"https://goc.egi.eu" +
                                               "/portal/index.php?Page_Type=" +
                                               "Downtime&id=%d\">%s</A>") % \
                                                       (myRef, myDoc['detail'])
                                else:
                                    myStrng = myDoc['detail']
                            else:
                                myStrng = "\"\""
                            myFile.write(("      <TR>\n         <TD NOWRAP>D" +
                                          "etail\n         <TD BGCOLOR=\"%s" +
                                          "\">%s\n") % (myColour, myStrng))
                        myFile.write(("      <TR>\n         <TD NOWRAP>Versi" +
                                      "on number<BR>(= insert time)\n       " +
                                      "  <TD BGCOLOR=\"%s\" NOWRAP>%d.%3.3d " +
                                      "(%s UTC)\n") %
                                     (myColour,
                                      int(myDoc['***VERSION***']/1000),
                                      myDoc['***VERSION***']%1000,
                                      time.strftime("%Y-%m-%d %H:%M:%S",
                               time.gmtime(int(myDoc['***VERSION***']/1000)))))
                        myFile.write(("      <TR>\n         <TD NOWRAP>Docum" +
                                      "ent id\n         <TD BGCOLOR=\"%s\" N" +
                                      "OWRAP>%s\n") %
                                     (myColour, myDoc['***DOCID***']))
                        myFile.write("      </TABLE>\n")
                    else:
                        myFile.write("   <TD>&nbsp;\n")
            myFile.write("</TABLE>\n")
        #
        try:
            os.chmod(myHTML, 0o644)
        except (IOError, OSError) as excptn:
            logging.warning("Failed to chmod downtime mainDVI section file, %s"
                                                                 % str(excptn))
        os.rename(myHTML, cfg['html'])

    except (IOError, OSError) as excptn:
        logging.critical("Writing of downtime mainDVI section failed, %s" %
                                                                   str(excptn))
        try:
            os.unlink( myHTML )
        except:
            pass
        return 1

    logging.log(25, "Downtime docs as HTML table written to %s" %
                                                    cfg['html'].split("/")[-1])
    return 0



def lftch_maindvi_sam(cfg, docs):
    """function to write CMS SAM documents as HTML table to a file"""
    # ################################################################ #
    # prepare mainDVI section with CMS SAM evaluation according to cfg #
    # ################################################################ #


    # organize documents by timebin and site/CE/SRM/XROOTD/perfSONAR within:
    # ======================================================================
    myDocs = {}
    mx_docs = 0
    for tbin in docs:
        no_docs = len( docs[tbin] )
        if ( no_docs > mx_docs ):
            mx_docs = no_docs
        # 
        # identify superseded documents:
        highestVersions = {}
        for myDoc in docs[tbin]:
            key = ( myDoc['name'], myDoc['type'] )
            if key not in highestVersions:
                highestVersions[key] = myDoc['***VERSION***']
            elif ( myDoc['***VERSION***'] > highestVersions[key] ):
                highestVersions[key] = myDoc['***VERSION***']
        # order documents in timebin:
        for myDoc in docs[tbin]:
            key = ( myDoc['name'], myDoc['type'] )
            try:
                myOrder = LFTCH_SERVICE_ORDER.index( myDoc['type'] )
            except ValueError:
                myOrder = len( LFTCH_SERVICE_ORDER )
            if ( myDoc['***VERSION***'] < highestVersions[key] ):
                myOrder += LFTCH_SUPERSEDED + \
                    int( (highestVersions[key]-myDoc['***VERSION***'])/300000 )
            myDoc['***ORDER***'] = myOrder
        myDocs[tbin] = sorted(docs[tbin],
                                   key=lambda k: [k['***ORDER***'], k['name']])


    # write mainDVI SAM HTML section:
    # ===============================
    myHTML = cfg['html'] + "_wrk"
    #
    try:
        with open(myHTML, 'wt') as myFile:
            ncols = len( myDocs )
            tbins = sorted( myDocs.keys() )
            #
            myFile.write("<TABLE BORDER=\"0\" CELLPADDING=\"0\" CELLSPACING=" +
                         "\"16\">\n<TR>\n")
            for tbin in tbins:
                sTIS = tbin * cfg['period']
                eTIS = sTIS + cfg['period']
                myFile.write("   <TH>Timebin %d (<B>%s</B> to %s UTC)\n" %
                    (tbin, time.strftime("%Y-%m-%d %H:%M", time.gmtime(sTIS)),
                                    time.strftime("%H:%M", time.gmtime(eTIS))))
            #
            for indx in range(mx_docs):
                #
                myFile.write("<TR ALIGN=\"left\" VALIGN=\"top\">\n")
                for tbin in tbins:
                    #
                    if ( indx < len( myDocs[tbin] ) ):
                        myFile.write("   <TD>\n      <TABLE WIDTH=\"100%\" B" +
                                     "ORDER=\"1\" CELLPADDING=\"2\" CELLSPAC" +
                                     "ING=\"0\">\n      <TR>\n         <TH>D" +
                                     "escription\n         <TH>Value\n")
                        myDoc = myDocs[tbin][indx]
                        if ( myDoc['***ORDER***'] > LFTCH_SUPERSEDED ):
                            myColour = "#DCDCDC"
                        elif ( myDoc['status'] == "ok" ):
                            myColour = "#CDFFD4"
                        elif ( myDoc['status'] == "warning" ):
                            myColour = "#FFFFCC"
                        elif ( myDoc['status'] == "error" ):
                            myColour = "#FFCCCC"
                        elif ( myDoc['status'] == "downtime" ):
                            myColour = "#CCD6FF"
                        else:
                            myColour = "#FFFFFF"
                        myFile.write(("      <TR>\n         <TD NOWRAP>Site/" +
                                      "Host name\n         <TD BGCOLOR=\"%s" +
                                      "\" NOWRAP>%s\n") %
                                     (myColour, myDoc['name']))
                        myFile.write(("      <TR>\n         <TD NOWRAP>Servi" +
                                      "ce type\n         <TD BGCOLOR=\"%s\" " +
                                      "NOWRAP>%s\n") %
                                     (myColour, myDoc['type']))
                        if 'availability' in myDoc:
                            if myDoc['availability'] is not None:
                                myStrng = "%.3f" % myDoc['availability']
                            else:
                                myStrng = "<I>not set</I>"
                        else:
                            myStrng = "<I>not set</I>"
                        myFile.write(("      <TR>\n         <TD NOWRAP>Avail" +
                                      "ability\n         <TD BGCOLOR=\"%s\" " +
                                      "NOWRAP>%s\n") % (myColour, myStrng))
                        if 'reliability' in myDoc:
                            if myDoc['reliability'] is not None:
                                myStrng = "%.3f" % myDoc['reliability']
                            else:
                                myStrng = "<I>not set</I>"
                        elif ( myDoc['type'] == "site" ):
                            myStrng = "<I>not set</I>"
                        else:
                            myStrng = None
                        if myStrng is not None:
                            myFile.write(("      <TR>\n         <TD NOWRAP>R" +
                                          "eliability\n         <TD BGCOLOR=" +
                                          "\"%s\" NOWRAP>%s\n") %
                                         (myColour, myStrng))
                        if 'detail' in myDoc:
                            if (( myDoc['detail'] is not None ) and
                                ( myDoc['detail'] != "" )):
                                myStrng = myDoc['detail'].replace("\n", "<BR>")
                            else:
                                myStrng = "\"\""
                            myFile.write(("      <TR>\n         <TD NOWRAP>D" +
                                          "etail\n         <TD STYLE=\"word" +
                                          "-wrap: break-word;\" BGCOLOR=\"%s" +
                                          "\">%s\n") % (myColour, myStrng))
                        myFile.write(("      <TR>\n         <TD NOWRAP>Statu" +
                                      "s\n         <TD BGCOLOR=\"%s\" NOWRAP" +
                                      "><B>%s</B>\n") %
                                     (myColour, myDoc['status']))
                        myFile.write(("      <TR>\n         <TD NOWRAP>Versi" +
                                      "on number<BR>(= insert time)\n       " +
                                      "  <TD BGCOLOR=\"%s\" NOWRAP>%d.%3.3d " +
                                      "(%s UTC)\n") %
                                     (myColour,
                                      int(myDoc['***VERSION***']/1000),
                                      myDoc['***VERSION***']%1000,
                                      time.strftime("%Y-%m-%d %H:%M:%S",
                               time.gmtime(int(myDoc['***VERSION***']/1000)))))
                        myFile.write(("      <TR>\n         <TD NOWRAP>Docum" +
                                      "ent id\n         <TD BGCOLOR=\"%s\" N" +
                                      "OWRAP>%s\n") %
                                     (myColour, myDoc['***DOCID***']))
                        myFile.write("      </TABLE>\n      <BR>\n")
                    else:
                        myFile.write("   <TD>&nbsp;\n")
            myFile.write("</TABLE>\n")
        #
        try:
            os.chmod(myHTML, 0o644)
        except (IOError, OSError) as excptn:
            logging.warning("Failed to chmod CMS SAM mainDVI section file, %s"
                                                                 % str(excptn))
        os.rename(myHTML, cfg['html'])

    except (IOError, OSError) as excptn:
        logging.critical("Writing of CMS SAM mainDVI section failed, %s" %
                                                                   str(excptn))
        try:
            os.unlink( myHTML )
        except:
            pass
        return 1

    logging.log(25, "CMS SAM docs as HTML table written to %s" %
                                                    cfg['html'].split("/")[-1])
    return 0



def lftch_url4hc(inputString):
    """function to substitute job references with hyperlinks in a string"""
    # ####################################################################### #
    # replace brackets with a job job reference with hyperlink to the job log #
    # ####################################################################### #
    LFTCH_HCJOB_URL = ("https://cmsweb.cern.ch/scheddmon/%s/" +
                                                 "cmsprd/%s/job_out.%s.%s.txt")
    brRegex = re.compile(r"^\w+@[a-zA-Z_-]+(\d+)\.\S+ (\S+) (\d+) (\d+)$")
    #
    myHTML = ""

    # handle new lines:
    myStrng = inputString.replace("\n", "<BR>")

    indx = 0
    j = myStrng.find("[")
    while ( j >= 0 ):
        k = myStrng[indx+j:].find("]")
        if ( k > 0 ):
            # copy over anything before the bracket:
            myHTML += myStrng[indx:indx+j]
            #
            # parse job reference inside the bracket:
            matchObj = brRegex.match( myStrng[indx+j+1:indx+j+k] )
            try:
                myURL = LFTCH_HCJOB_URL % (matchObj.group(1),
                       matchObj.group(2), matchObj.group(3), matchObj.group(4))
                myHTML += "[<A HREF=\"%s\">%s</A>]" % (myURL,
                                                    myStrng[indx+j+1:indx+j+k])
            except (AttributeError, IndexError):
                myHTML += "[%s]" % myStrng[indx+j+1:indx+j+k]
            #
            # advance parsing:
            indx += j + k + 1
        else:
            break
        #
        j = myStrng[indx:].find("[")
    #
    # copy remainder of string:
    myHTML += myStrng[indx:]

    return myHTML



def lftch_maindvi_hc(cfg, docs):
    """function to write CMS HC documents as HTML table to a file"""
    # ############################################################### #
    # prepare mainDVI section with CMS HC evaluation according to cfg #
    # ############################################################### #


    # organize documents by timebin and version within:
    # =================================================
    myDocs = {}
    mx_docs = 0
    for tbin in docs:
        no_docs = len( docs[tbin] )
        if ( no_docs > mx_docs ):
            mx_docs = no_docs
        # 
        # identify superseded documents:
        highestVersions = {}
        for myDoc in docs[tbin]:
            if myDoc['site'] not in highestVersions:
                highestVersions[ myDoc['site'] ] = myDoc['***VERSION***']
            elif ( myDoc['***VERSION***'] > highestVersions[ myDoc['site'] ] ):
                highestVersions[ myDoc['site'] ] = myDoc['***VERSION***']
        # order documents in timebin:
        for myDoc in docs[tbin]:
            myDoc['***ORDER***'] = highestVersions[myDoc['site']] - \
                                                         myDoc['***VERSION***']
        myDocs[tbin] = sorted(docs[tbin],
                                   key=lambda k: [k['site'], k['***ORDER***']])


    # write mainDVI HC HTML section:
    # ==============================
    myHTML = cfg['html'] + "_wrk"
    #
    try:
        with open(myHTML, 'wt') as myFile:
            ncols = len( myDocs )
            tbins = sorted( myDocs.keys() )
            #
            myFile.write("<TABLE BORDER=\"0\" CELLPADDING=\"0\" CELLSPACING=" +
                         "\"16\">\n<TR>\n")
            for tbin in tbins:
                sTIS = tbin * cfg['period']
                eTIS = sTIS + cfg['period']
                myFile.write("   <TH>Timebin %d (<B>%s</B> to %s UTC)\n" %
                    (tbin, time.strftime("%Y-%m-%d %H:%M", time.gmtime(sTIS)),
                                    time.strftime("%H:%M", time.gmtime(eTIS))))
            #
            for indx in range(mx_docs):
                #
                myFile.write("<TR ALIGN=\"left\" VALIGN=\"top\">\n")
                for tbin in tbins:
                    #
                    if ( indx < len( myDocs[tbin] ) ):
                        myFile.write("   <TD>\n      <TABLE WIDTH=\"100%\" B" +
                                     "ORDER=\"1\" CELLPADDING=\"2\" CELLSPAC" +
                                     "ING=\"0\">\n      <TR>\n         <TH>D" +
                                     "escription\n         <TH>Value\n")
                        myDoc = myDocs[tbin][indx]
                        if ( myDoc['***ORDER***'] > 0 ):
                            myColour = "#DCDCDC"
                        elif ( myDoc['status'] == "ok" ):
                            myColour = "#CDFFD4"
                        elif ( myDoc['status'] == "warning" ):
                            myColour = "#FFFFCC"
                        elif ( myDoc['status'] == "error" ):
                            myColour = "#FFCCCC"
                        else:
                            myColour = "#FFFFFF"
                        myFile.write(("      <TR>\n         <TD NOWRAP>Site " +
                                      "name\n         <TD BGCOLOR=\"%s\" NOW" +
                                      "RAP>%s\n") % (myColour, myDoc['site']))
                        if 'value' in myDoc:
                            if myDoc['value'] is not None:
                                myStrng = "%.3f" % myDoc['value']
                            else:
                                myStrng = "<I>not set</I>"
                            myFile.write(("      <TR>\n         <TD NOWRAP>V" +
                                          "alue\n         <TD BGCOLOR=\"%s\"" +
                                          " NOWRAP>%s\n") %
                                         (myColour, myStrng))
                        if 'detail' in myDoc:
                            if (( myDoc['detail'] is not None ) and
                                ( myDoc['detail'] != "" )):
                                myStrng = lftch_url4hc( myDoc['detail'] )
                            else:
                                myStrng = "\"\""
                            myFile.write(("      <TR>\n         <TD NOWRAP>D" +
                                          "etail\n         <TD STYLE=\"word" +
                                          "-wrap: break-word;\" BGCOLOR=\"%s" +
                                          "\">%s\n") % (myColour, myStrng))
                        myFile.write(("      <TR>\n         <TD NOWRAP>Statu" +
                                      "s\n         <TD BGCOLOR=\"%s\" NOWRAP" +
                                      "><B>%s</B>\n") %
                                     (myColour, myDoc['status']))
                        myFile.write(("      <TR>\n         <TD NOWRAP>Versi" +
                                      "on number<BR>(= insert time)\n       " +
                                      "  <TD BGCOLOR=\"%s\" NOWRAP>%d.%3.3d " +
                                      "(%s UTC)\n") %
                                     (myColour,
                                      int(myDoc['***VERSION***']/1000),
                                      myDoc['***VERSION***']%1000,
                                      time.strftime("%Y-%m-%d %H:%M:%S",
                               time.gmtime(int(myDoc['***VERSION***']/1000)))))
                        myFile.write(("      <TR>\n         <TD NOWRAP>Docum" +
                                      "ent id\n         <TD BGCOLOR=\"%s\" N" +
                                      "OWRAP>%s\n") %
                                     (myColour, myDoc['***DOCID***']))
                        myFile.write("      </TABLE>\n      <BR>\n")
                    else:
                        myFile.write("   <TD>&nbsp;\n")
            myFile.write("</TABLE>\n")
        #
        try:
            os.chmod(myHTML, 0o644)
        except (IOError, OSError) as excptn:
            logging.warning("Failed to chmod CMS HC mainDVI section file, %s"
                                                                 % str(excptn))
        os.rename(myHTML, cfg['html'])

    except (IOError, OSError) as excptn:
        logging.critical("Writing of CMS HC mainDVI section failed, %s" %
                                                                   str(excptn))
        try:
            os.unlink( myHTML )
        except:
            pass
        return 1

    logging.log(25, "CMS HC docs as HTML table written to %s" %
                                                    cfg['html'].split("/")[-1])
    return 0



def lftch_maindvi_fts(cfg, docs):
    """function to write CMS FTS documents as HTML table to a file"""
    # ################################################################ #
    # prepare mainDVI section with CMS FTS evaluation according to cfg #
    # ################################################################ #


    # organize documents by timebin and site/destination/source/link within:
    # ======================================================================
    myDocs = {}
    mx_docs = 0
    for tbin in docs:
        no_docs = len( docs[tbin] )
        if ( no_docs > mx_docs ):
            mx_docs = no_docs
        # 
        # identify superseded documents:
        highestVersions = {}
        for myDoc in docs[tbin]:
            key = ( myDoc['name'], myDoc['type'] )
            if key not in highestVersions:
                highestVersions[key] = myDoc['***VERSION***']
            elif ( myDoc['***VERSION***'] > highestVersions[key] ):
                highestVersions[key] = myDoc['***VERSION***']
        # order documents in timebin:
        for myDoc in docs[tbin]:
            key = ( myDoc['name'], myDoc['type'] )
            try:
                myOrder = LFTCH_TRANSFER_ORDER.index( myDoc['type'] )
            except ValueError:
                myOrder = len( LFTCH_TRANSFER_ORDER )
            if ( myDoc['***VERSION***'] < highestVersions[key] ):
                myOrder += LFTCH_SUPERSEDED + \
                    int( (highestVersions[key]-myDoc['***VERSION***'])/300000 )
            myDoc['***ORDER***'] = myOrder
        myDocs[tbin] = sorted(docs[tbin],
                                   key=lambda k: [k['***ORDER***'], k['name']])


    # write mainDVI SAM HTML section:
    # ===============================
    myHTML = cfg['html'] + "_wrk"
    #
    try:
        with open(myHTML, 'wt') as myFile:
            ncols = len( myDocs )
            tbins = sorted( myDocs.keys() )
            #
            myFile.write("<TABLE BORDER=\"0\" CELLPADDING=\"0\" CELLSPACING=" +
                         "\"16\">\n<TR>\n")
            for tbin in tbins:
                sTIS = tbin * cfg['period']
                eTIS = sTIS + cfg['period']
                myFile.write("   <TH>Timebin %d (<B>%s</B> to %s UTC)\n" %
                    (tbin, time.strftime("%Y-%m-%d %H:%M", time.gmtime(sTIS)),
                                    time.strftime("%H:%M", time.gmtime(eTIS))))
            #
            for indx in range(mx_docs):
                #
                myFile.write("<TR ALIGN=\"left\" VALIGN=\"top\">\n")
                for tbin in tbins:
                    #
                    if ( indx < len( myDocs[tbin] ) ):
                        myFile.write("   <TD>\n      <TABLE WIDTH=\"100%\" B" +
                                     "ORDER=\"1\" CELLPADDING=\"2\" CELLSPAC" +
                                     "ING=\"0\">\n      <TR>\n         <TH>D" +
                                     "escription\n         <TH>Value\n")
                        myDoc = myDocs[tbin][indx]
                        if ( myDoc['***ORDER***'] > LFTCH_SUPERSEDED ):
                            myColour = "#DCDCDC"
                        elif ( myDoc['status'] == "ok" ):
                            myColour = "#CDFFD4"
                        elif ( myDoc['status'] == "warning" ):
                            myColour = "#FFFFCC"
                        elif ( myDoc['status'] == "error" ):
                            myColour = "#FFCCCC"
                        else:
                            myColour = "#FFFFFF"
                        myFile.write(("      <TR>\n         <TD NOWRAP>Site/" +
                                      "Host/Link name\n         <TD BGCOLOR=" +
                                      "\"%s\" NOWRAP>%s\n") %
                                     (myColour, myDoc['name']))
                        myFile.write(("      <TR>\n         <TD NOWRAP>Evalu" +
                                      "ation type\n         <TD BGCOLOR=\"%s" +
                                      "\" NOWRAP>%s\n") %
                                     (myColour, myDoc['type']))
                        if 'quality' in myDoc:
                            if myDoc['quality'] is not None:
                                myStrng = "%.3f" % myDoc['quality']
                            else:
                                myStrng = "<I>not set</I>"
                        else:
                            myStrng = "<I>not set</I>"
                        myFile.write(("      <TR>\n         <TD NOWRAP>Quali" +
                                      "ty\n         <TD BGCOLOR=\"%s\" NOWRA" +
                                      "P>%s\n") % (myColour, myStrng))
                        if 'detail' in myDoc:
                            if (( myDoc['detail'] is not None ) and
                                ( myDoc['detail'] != "" )):
                                myStrng = myDoc['detail'].replace("\n", "<BR>")
                            else:
                                myStrng = "\"\""
                            myFile.write(("      <TR>\n         <TD NOWRAP>D" +
                                          "etail\n         <TD STYLE=\"word" +
                                          "-wrap: break-word;\" BGCOLOR=\"%s" +
                                          "\">%s\n") % (myColour, myStrng))
                        myFile.write(("      <TR>\n         <TD NOWRAP>Statu" +
                                      "s\n         <TD BGCOLOR=\"%s\" NOWRAP" +
                                      "><B>%s</B>\n") %
                                     (myColour, myDoc['status']))
                        myFile.write(("      <TR>\n         <TD NOWRAP>Versi" +
                                      "on number<BR>(= insert time)\n       " +
                                      "  <TD BGCOLOR=\"%s\" NOWRAP>%d.%3.3d " +
                                      "(%s UTC)\n") %
                                     (myColour,
                                      int(myDoc['***VERSION***']/1000),
                                      myDoc['***VERSION***']%1000,
                                      time.strftime("%Y-%m-%d %H:%M:%S",
                               time.gmtime(int(myDoc['***VERSION***']/1000)))))
                        myFile.write(("      <TR>\n         <TD NOWRAP>Docum" +
                                      "ent id\n         <TD BGCOLOR=\"%s\" N" +
                                      "OWRAP>%s\n") %
                                     (myColour, myDoc['***DOCID***']))
                        myFile.write("      </TABLE>\n      <BR>\n")
                    else:
                        myFile.write("   <TD>&nbsp;\n")
            myFile.write("</TABLE>\n")
        #
        try:
            os.chmod(myHTML, 0o644)
        except (IOError, OSError) as excptn:
            logging.warning("Failed to chmod CMS FTS mainDVI section file, %s"
                                                                 % str(excptn))
        os.rename(myHTML, cfg['html'])

    except (IOError, OSError) as excptn:
        logging.critical("Writing of CMS FTS mainDVI section failed, %s" %
                                                                   str(excptn))
        try:
            os.unlink( myHTML )
        except:
            pass
        return 1

    logging.log(25, "CMS FTS docs as HTML table written to %s" %
                                                    cfg['html'].split("/")[-1])
    return 0



def lftch_url4sr(inputString, cfg, tbin, site):
    """function to substitute SiteReadiness SAM,HC,FTS refs with hyperlinks"""
    # ##################################################################### #
    # replace SR SAM,HC,FTS references with hyperlink to the evaluation log #
    # ##################################################################### #
    LFTCH_LOG_URL = "https://test-cmssst.web.cern.ch/cgi-bin/log"
    #
    myHTML = ""

    # loop over lines in inputString:
    # ===============================
    newlineFlag = False
    for myLine in inputString.splitlines():
        if ( newlineFlag == True ):
            myHTML += "<BR>"
        #
        if ( myLine == "downtime: no scheduled downtime" ):
            t15bin = tbin * cfg['period'] / 900
            myHTML += ("<A HREF=\"%s/%s/%d/all/any/day+0\">%s</A>" %
                       (LFTCH_LOG_URL, "down15min", t15bin, myLine))
        elif ( myLine[0:10] == "downtime: " ):
            t15bin = tbin * cfg['period'] / 900
            myHTML += ("<A HREF=\"%s/%s/%d/%s/site/day+0\">%s</A>" %
                       (LFTCH_LOG_URL, "down15min", t15bin, site, myLine))
        elif ( myLine[0:5] == "SAM: " ):
            myHTML += ("<A HREF=\"%s/sam%s/%d/%s/site/0+0\">%s</A>" % 
                       (LFTCH_LOG_URL, cfg['metric'][2:], tbin, site, myLine))
        elif ( myLine[0:4] == "HC: " ):
            myHTML += ("<A HREF=\"%s/hc%s/%d/%s/site/0+0\">%s</A>" %
                       (LFTCH_LOG_URL, cfg['metric'][2:], tbin, site, myLine))
        elif ( myLine[0:5] == "FTS: " ):
            myHTML += ("<A HREF=\"%s/fts%s/%d/%s/site/0+0\">%s</A>" %
                       (LFTCH_LOG_URL, cfg['metric'][2:], tbin, site, myLine))
        else:
            myHTML += myLine
        newlineFlag = True

    return myHTML



def lftch_maindvi_sr(cfg, docs):
    """function to write CMS SiteReadiness documents as HTML table to a file"""
    # ############################################################### #
    # prepare mainDVI section with CMS SR evaluation according to cfg #
    # ############################################################### #


    # organize documents by timebin and version within:
    # =================================================
    myDocs = {}
    mx_docs = 0
    for tbin in docs:
        no_docs = len( docs[tbin] )
        if ( no_docs > mx_docs ):
            mx_docs = no_docs
        # 
        # identify superseded documents:
        highestVersions = {}
        for myDoc in docs[tbin]:
            if myDoc['name'] not in highestVersions:
                highestVersions[ myDoc['name'] ] = myDoc['***VERSION***']
            elif ( myDoc['***VERSION***'] > highestVersions[ myDoc['name'] ] ):
                highestVersions[ myDoc['name'] ] = myDoc['***VERSION***']
        # order documents in timebin:
        for myDoc in docs[tbin]:
            myDoc['***ORDER***'] = highestVersions[myDoc['name']] - \
                                                         myDoc['***VERSION***']
        myDocs[tbin] = sorted(docs[tbin],
                                   key=lambda k: [k['name'], k['***ORDER***']])


    # write mainDVI SR HTML section:
    # ==============================
    myHTML = cfg['html'] + "_wrk"
    #
    try:
        with open(myHTML, 'wt') as myFile:
            ncols = len( myDocs )
            tbins = sorted( myDocs.keys() )
            #
            myFile.write("<TABLE BORDER=\"0\" CELLPADDING=\"0\" CELLSPACING=" +
                         "\"16\">\n<TR>\n")
            for tbin in tbins:
                sTIS = tbin * cfg['period']
                eTIS = sTIS + cfg['period']
                myFile.write("   <TH>Timebin %d (<B>%s</B> to %s UTC)\n" %
                    (tbin, time.strftime("%Y-%m-%d %H:%M", time.gmtime(sTIS)),
                                    time.strftime("%H:%M", time.gmtime(eTIS))))
            #
            for indx in range(mx_docs):
                #
                myFile.write("<TR ALIGN=\"left\" VALIGN=\"top\">\n")
                for tbin in tbins:
                    #
                    if ( indx < len( myDocs[tbin] ) ):
                        myFile.write("   <TD>\n      <TABLE WIDTH=\"100%\" B" +
                                     "ORDER=\"1\" CELLPADDING=\"2\" CELLSPAC" +
                                     "ING=\"0\">\n      <TR>\n         <TH>D" +
                                     "escription\n         <TH>Value\n")
                        myDoc = myDocs[tbin][indx]
                        if ( myDoc['***ORDER***'] > 0 ):
                            myColour = "#DCDCDC"
                        elif ( myDoc['status'] == "ok" ):
                            myColour = "#CDFFD4"
                        elif ( myDoc['status'] == "warning" ):
                            myColour = "#FFFFCC"
                        elif ( myDoc['status'] == "error" ):
                            myColour = "#FFCCCC"
                        else:
                            myColour = "#FFFFFF"
                        myFile.write(("      <TR>\n         <TD NOWRAP>Site " +
                                      "name\n         <TD BGCOLOR=\"%s\" NOW" +
                                      "RAP>%s\n") % (myColour, myDoc['name']))
                        if 'value' in myDoc:
                            if myDoc['value'] is not None:
                                myStrng = "%.3f" % myDoc['value']
                            else:
                                myStrng = "<I>not set</I>"
                            myFile.write(("      <TR>\n         <TD NOWRAP>V" +
                                          "alue\n         <TD BGCOLOR=\"%s\"" +
                                          " NOWRAP>%s\n") %
                                         (myColour, myStrng))
                        if 'detail' in myDoc:
                            if (( myDoc['detail'] is not None ) and
                                ( myDoc['detail'] != "" )):
                                myStrng = lftch_url4sr( myDoc['detail'], 
                                                     cfg, tbin, myDoc['name'] )
                            else:
                                myStrng = "\"\""
                            myFile.write(("      <TR>\n         <TD NOWRAP>D" +
                                          "etail\n         <TD STYLE=\"word" +
                                          "-wrap: break-word;\" BGCOLOR=\"%s" +
                                          "\">%s\n") % (myColour, myStrng))
                        myFile.write(("      <TR>\n         <TD NOWRAP>Statu" +
                                      "s\n         <TD BGCOLOR=\"%s\" NOWRAP" +
                                      "><B>%s</B>\n") %
                                     (myColour, myDoc['status']))
                        myFile.write(("      <TR>\n         <TD NOWRAP>Versi" +
                                      "on number<BR>(= insert time)\n       " +
                                      "  <TD BGCOLOR=\"%s\" NOWRAP>%d.%3.3d " +
                                      "(%s UTC)\n") %
                                     (myColour,
                                      int(myDoc['***VERSION***']/1000),
                                      myDoc['***VERSION***']%1000,
                                      time.strftime("%Y-%m-%d %H:%M:%S",
                               time.gmtime(int(myDoc['***VERSION***']/1000)))))
                        myFile.write(("      <TR>\n         <TD NOWRAP>Docum" +
                                      "ent id\n         <TD BGCOLOR=\"%s\" N" +
                                      "OWRAP>%s\n") %
                                     (myColour, myDoc['***DOCID***']))
                        myFile.write("      </TABLE>\n      <BR>\n")
                    else:
                        myFile.write("   <TD>&nbsp;\n")
            myFile.write("</TABLE>\n")
        #
        try:
            os.chmod(myHTML, 0o644)
        except (IOError, OSError) as excptn:
            logging.warning("Failed to chmod CMS SR mainDVI section file, %s"
                                                                 % str(excptn))
        os.rename(myHTML, cfg['html'])

    except (IOError, OSError) as excptn:
        logging.critical("Writing of CMS SR mainDVI section failed, %s" %
                                                                   str(excptn))
        try:
            os.unlink( myHTML )
        except:
            pass
        return 1

    logging.log(25, "CMS SR docs as HTML table written to %s" %
                                                    cfg['html'].split("/")[-1])
    return 0



def lftch_maindvi_sts(cfg, docs):
    """function to write CMS SiteStatus documents as HTML table to a file"""
    # ################################################################ #
    # prepare mainDVI section with CMS STS evaluation according to cfg #
    # ################################################################ #


    # organize documents by timebin and version within:
    # =================================================
    myDocs = {}
    mx_docs = 0
    for tbin in docs:
        no_docs = len( docs[tbin] )
        if ( no_docs > mx_docs ):
            mx_docs = no_docs
        # 
        # identify superseded documents:
        highestVersions = {}
        for myDoc in docs[tbin]:
            if myDoc['name'] not in highestVersions:
                highestVersions[ myDoc['name'] ] = myDoc['***VERSION***']
            elif ( myDoc['***VERSION***'] > highestVersions[ myDoc['name'] ] ):
                highestVersions[ myDoc['name'] ] = myDoc['***VERSION***']
        # order documents in timebin:
        for myDoc in docs[tbin]:
            myDoc['***ORDER***'] = highestVersions[myDoc['name']] - \
                                                         myDoc['***VERSION***']
        myDocs[tbin] = sorted(docs[tbin],
                                   key=lambda k: [k['name'], k['***ORDER***']])


    # write mainDVI STS HTML section:
    # ===============================
    myHTML = cfg['html'] + "_wrk"
    #
    try:
        with open(myHTML, 'wt') as myFile:
            ncols = len( myDocs )
            tbins = sorted( myDocs.keys() )
            #
            myFile.write("<TABLE BORDER=\"0\" CELLPADDING=\"0\" CELLSPACING=" +
                         "\"16\">\n<TR>\n")
            for tbin in tbins:
                sTIS = tbin * cfg['period']
                eTIS = sTIS + cfg['period']
                myFile.write("   <TH>Timebin %d (<B>%s</B> to %s UTC)\n" %
                    (tbin, time.strftime("%Y-%m-%d %H:%M", time.gmtime(sTIS)),
                                    time.strftime("%H:%M", time.gmtime(eTIS))))
            #
            for indx in range(mx_docs):
                #
                myFile.write("<TR ALIGN=\"left\" VALIGN=\"top\">\n")
                for tbin in tbins:
                    #
                    if ( indx < len( myDocs[tbin] ) ):
                        myFile.write("   <TD>\n      <TABLE WIDTH=\"100%\" B" +
                                     "ORDER=\"1\" CELLPADDING=\"2\" CELLSPAC" +
                                     "ING=\"0\">\n      <TR>\n         <TH>D" +
                                     "escription\n         <TH>Value\n")
                        myDoc = myDocs[tbin][indx]
                        if ( myDoc['***ORDER***'] > 0 ):
                            myColour = "#DCDCDC"
                        elif ( myDoc['status'] == "enabled" ):
                            myColour = "#CDFFD4"
                        elif ( myDoc['status'] == "waiting_room" ):
                            myColour = "#FFFFCC"
                        elif ( myDoc['status'] == "morgue" ):
                            myColour = "#FFCCCC"
                        else:
                            myColour = "#FFFFFF"
                        myFile.write(("      <TR>\n         <TD NOWRAP>Site " +
                                      "name\n         <TD BGCOLOR=\"%s\" NOW" +
                                      "RAP>%s\n") % (myColour, myDoc['name']))
                        myFile.write(("      <TR>\n         <TD NOWRAP>Statu" +
                                      "s\n         <TD BGCOLOR=\"%s\" NOWRAP" +
                                      "><B>%s</B>\n") %
                                     (myColour, myDoc['status']))
                        if ( myDoc['***ORDER***'] > 0 ):
                            myColor = "#DCDCDC"
                        elif ( myDoc['prod_status'] == "enabled" ):
                            myColor = "#CDFFD4"
                        elif ( myDoc['prod_status'] == "drain" ):
                            myColor = "#FFFFCC"
                        elif ( myDoc['prod_status'] == "disabled" ):
                            myColor = "#FFCCCC"
                        else:
                            myColor = "#FFFFFF"
                        myFile.write(("      <TR>\n         <TD NOWRAP>Produ" +
                                      "ction Status\n         <TD BGCOLOR=\"" +
                                      "%s\" NOWRAP>%s\n") %
                                     (myColor, myDoc['prod_status']))
                        if ( myDoc['***ORDER***'] > 0 ):
                            myColor = "#DCDCDC"
                        elif ( myDoc['crab_status'] == "enabled" ):
                            myColor = "#CDFFD4"
                        elif ( myDoc['crab_status'] == "disabled" ):
                            myColor = "#FFCCCC"
                        else:
                            myColor = "#FFFFFF"
                        myFile.write(("      <TR>\n         <TD NOWRAP>Analy" +
                                      "sis Status\n         <TD BGCOLOR=\"%s" +
                                      "\" NOWRAP>%s\n") %
                                     (myColor, myDoc['crab_status']))
                        if 'detail' in myDoc:
                            if (( myDoc['detail'] is not None ) and
                                ( myDoc['detail'] != "" )):
                                myStrng = myDoc['detail'].replace("\n", "<BR>")
                            else:
                                myStrng = "\"\""
                            myFile.write(("      <TR>\n         <TD NOWRAP>D" +
                                          "etail\n         <TD STYLE=\"word" +
                                          "-wrap: break-word;\" BGCOLOR=\"%s" +
                                          "\">%s\n") % (myColour, myStrng))
                        myFile.write(("      <TR>\n         <TD NOWRAP>Versi" +
                                      "on number<BR>(= insert time)\n       " +
                                      "  <TD BGCOLOR=\"%s\" NOWRAP>%d.%3.3d " +
                                      "(%s UTC)\n") %
                                     (myColour,
                                      int(myDoc['***VERSION***']/1000),
                                      myDoc['***VERSION***']%1000,
                                      time.strftime("%Y-%m-%d %H:%M:%S",
                               time.gmtime(int(myDoc['***VERSION***']/1000)))))
                        myFile.write(("      <TR>\n         <TD NOWRAP>Docum" +
                                      "ent id\n         <TD BGCOLOR=\"%s\" N" +
                                      "OWRAP>%s\n") %
                                     (myColour, myDoc['***DOCID***']))
                        myFile.write("      </TABLE>\n      <BR>\n")
                    else:
                        myFile.write("   <TD>&nbsp;\n")
            myFile.write("</TABLE>\n")
        #
        try:
            os.chmod(myHTML, 0o644)
        except (IOError, OSError) as excptn:
            logging.warning("Failed to chmod CMS STS mainDVI section file, %s"
                                                                 % str(excptn))
        os.rename(myHTML, cfg['html'])

    except (IOError, OSError) as excptn:
        logging.critical("Writing of CMS STS mainDVI section failed, %s" %
                                                                   str(excptn))
        try:
            os.unlink( myHTML )
        except:
            pass
        return 1

    logging.log(25, "CMS STS docs as HTML table written to %s" %
                                                    cfg['html'].split("/")[-1])
    return 0
# ########################################################################### #



if __name__ == '__main__':
    lftch_cfg = {}
    rc = 0
    #
    os.umask(0o022)
    #
    parserObj = argparse.ArgumentParser(description="Script to retrieve SAM-" +
        "ETF log and CMS-SSB metric documents from MonIT HDFS and format and" +
        " write the information as HTML table or JSON file. HTTP log retriev" +
        "al path or metric/name/type/time-stamps can be used to select the d" +
        "ocuments of interest.")
    parserObj.add_argument("-p", dest="path", action="store",
                                 metavar="URL-path",
                                 help=("log URL-path specifying document sel" +
                                       "ection"))
    parserObj.add_argument("-m", dest="metric", action="store",
                                 metavar="metric-name",
                                 help="retrieve document(s) of metric-name")
    parserObj.add_argument("-b", dest="timebin", action="store",
                                 metavar="timebin",
                                 help=("UTC timebin specification, either a " +
                                       "<=8-digit integer (timebin number), " +
                                       "10-digit integer (time in seconds si" +
                                       "nce the epoch), or time in the forma" +
                                       "t \"YYYY-Mmm-dd HH:MM\""))
    parserObj.add_argument("-n", dest="name", action="store",
                                 metavar="site/host-name",
                                 help=("select only documents with matching " +
                                       "site/host-name"))
    parserObj.add_argument("-t", dest="type", action="store",
                                 metavar="service-type",
                                 help=("select only documents with matching " +
                                       "service-type"))
    parserObj.add_argument("-w", dest="window", action="store",
                                 metavar="tbin-window",
                                 help=("specify documents of additional time" +
                                       "bins before and after timebin to be " +
                                       "selected, format is before+after"))
    parserObj.add_argument("-J", dest="json", action="store",
                                 metavar="JSON-file",
                                 help=("write document(s) information in JSO" +
                                       "N format to file JSON-file"))
    parserObj.add_argument("-H", dest="html", action="store",
                                 metavar="HTML-file",
                                 help=("write document(s) information as HTM" +
                                       "L table to file HTML-file"))
    parserObj.add_argument("-L", dest="logging", action="store",
                                 metavar="log-file",
                                 help=("write logging messages not to stdout" +
                                       " but log-file"))
    parserObj.add_argument("-v", action="count", default=0,
                                 help="increase logging verbosity")
    argStruct = parserObj.parse_args()



    # configure message logging:
    # ==========================
    logging.addLevelName(25, "NOTICE")
    logging.addLevelName(15, "debug")
    logging.addLevelName(9, "XDEBUG")
    #
    if ( argStruct.v >= 5 ):
        logLevel = 9
        logFormat = "%(asctime)s [%(levelname).1s] %(message)s"
    elif ( argStruct.v == 4 ):
        logLevel = logging.DEBUG
        logFormat = "%(asctime)s [%(levelname).1s] %(message)s"
    elif ( argStruct.v == 3 ):
        logLevel = 15
        logFormat = "%(asctime)s [%(levelname).1s] %(message)s"
    elif ( argStruct.v == 2 ):
        logLevel = logging.INFO
        logFormat = "[%(levelname).1s] %(message)s"
    elif ( argStruct.v == 1 ):
        logLevel = 25
        logFormat = "[%(levelname).1s] %(message)s"
    else:
        logLevel = logging.WARNING
        logFormat = "[%(levelname).1s] %(message)s"
    #
    if argStruct.logging is not None:
        logging.basicConfig(datefmt="%Y-%b-%d %H:%M:%S",
                            format=logFormat, level=logLevel,
                            filename=argStruct.logging, filemode="wt")
    else:
        logging.basicConfig(datefmt="%Y-%b-%d %H:%M:%S",
                            format=logFormat, level=logLevel)
    #
    logging.log(25, "Python interpreter, modules, and script loaded")



    # parse/check arguments not related to logging:
    # =============================================
    #
    allowedCharRegex = re.compile("[^a-zA-Z0-9_.=/+*-]")
    siteRegex = re.compile(r"T\d_[A-Z]{2,2}_\w+")
    bBin = None
    aBin = None
    #
    if argStruct.path is not None:
        compList = allowedCharRegex.sub("", argStruct.path ).split("/")
        if (( len(compList) < 5 ) or ( len(compList) > 7 )):
            logging.critical("Bad URL-path specification \"%s\"" %
                                     allowedCharRegex.sub("", argStruct.path ))
            sys.exit(1)
        if ( compList[0] != "" ):
            logging.critical("URL-path must start with \"/\"")
            sys.exit(1)
        if compList[1] not in LFTCH_METRICS_DEFINED:
            logging.critical("Unknown metric \"%s\"" % compList[1])
            sys.exit(1)
        else:
            lftch_cfg.update( LFTCH_METRICS_DEFINED[ compList[1] ] )
            lftch_cfg['metric'] = compList[1]
        if( compList[2].isdigit() ):
            if ( len(compList[2]) == 10 ):
                lftch_cfg['time'] = int( compList[2] )
            elif ( len(compList[2]) == 12 ):
                lftch_cfg['time'] = calendar.timegm(
                                     time.strptime(compList[2], "%Y%m%d%H%M") )
            elif ( len(compList[2]) == 14 ):
                lftch_cfg['time'] = calendar.timegm(
                                   time.strptime(compList[2], "%Y%m%d%H%M%S") )
            else:
                logging.critical(("Bad date/time specification \"%s\" in URL" +
                                  "-path") % compList[2])
                sys.exit(1)
        else:
            logging.critical(("Non-numeric date/time specification \"%s\" in" +
                              " URL-path") % compList[2])
            sys.exit(1)
        if (( compList[3].lower() == "all" ) or ( compList[3] == "*" )):
            lftch_cfg['name'] = "*"
        else:
            if (( siteRegex.match( compList[3] ) is None ) and
                ( compList[3].count(".") < 2 )):
                logging.critical(("Bad site/node specification \"%s\" in URL" +
                                                        "-path") % compList[3])
                sys.exit(1)
            lftch_cfg['name'] = compList[3]
        if (( compList[4].lower() == "any" ) or ( compList[4] == "*" ) or
            ( compList[4] == "" )):
            lftch_cfg['type'] = "*"
        elif ( compList[4].upper() == "CE" ):
            lftch_cfg['type'] = "CE"
        elif (( compList[4].upper() == "SRM" ) or
              ( compList[4].upper() == "SE" )):
            lftch_cfg['type'] = "SRM"
        elif ( compList[4].upper() == "XROOTD" ):
            lftch_cfg['type'] = "XROOTD"
        elif ( compList[4].lower() == "site" ):
            lftch_cfg['type'] = "site"
        elif compList[4] in LFTCH_PROBE_ORDER:
            lftch_cfg['type'] = compList[4]
        elif compList[4][8:] in LFTCH_PROBE_ORDER:
            lftch_cfg['type'] = compList[4][8:]
        else:
            logging.critical("Unknown service type \"%s\" in URL-path" %
                                                                   compList[4])
            sys.exit(1)
        if ( len(compList) >= 6 ):
            if ( compList[5].find("+") > 0 ):
                bBin,aBin = compList[5].split("+")[0:2]
            else:
                logging.critical(("Bad timebin window parameter \"%s\" in UR" +
                                                       "L-path") % compList[5])
                sys.exit(1)
        else:
            bBin,aBin = lftch_cfg['dfltwin'].split("+")[0:2]
        if ( len(compList) == 7 ):
            if ( compList[6] != "" ):
                logging.critical("URL-path with non-empty sixth field")
                sys.exit(1)
    #
    if argStruct.metric is not None:
        if argStruct.metric not in LFTCH_METRICS_DEFINED:
            logging.critical("Unknown metric \"%s\"" % argStruct.metric)
            sys.exit(1)
        else:
            lftch_cfg.update( LFTCH_METRICS_DEFINED[ argStruct.metric ] )
            lftch_cfg['metric'] = argStruct.metric
    elif argStruct.path is None:
        logging.critical("No document metric specified")
        sys.exit(1)
    #
    if argStruct.timebin is not None:
        if( argStruct.timebin.isdigit() ):
            if ( len(argStruct.timebin) == 10 ):
                lftch_cfg['time'] = int( argStruct.timebin )
            elif ( len(argStruct.timebin) == 12 ):
                lftch_cfg['time'] = calendar.timegm(
                               time.strptime(argStruct.timebin, "%Y%m%d%H%M") )
            elif ( len(argStruct.timebin) == 14 ):
                lftch_cfg['time'] = calendar.timegm(
                             time.strptime(argStruct.timebin, "%Y%m%d%H%M%S") )
            else:
                logging.critical("Bad date/time specification \"%s\"" %
                                                             argStruct.timebin)
                sys.exit(1)
        else:
            logging.critical("Non-numeric date/time specification \"%s\"" %
                                                             argStruct.timebin)
            sys.exit(1)
    elif argStruct.path is None:
        logging.critical("No timebin specified")
        sys.exit(1)
    #
    if argStruct.name is not None:
        if (( argStruct.name.lower() == "all" ) or ( argStruct.name == "*" )):
            lftch_cfg['name'] = "*"
        else:
            if (( siteRegex.match( argStruct.name ) is None ) and
                ( argStruct.name.count(".") < 2 )):
                logging.critical("Bad site/node specification \"%s\"" %
                                                                   compList[3])
                sys.exit(1)
            lftch_cfg['name'] = argStruct.name
    elif argStruct.path is None:
        lftch_cfg['name'] = "*"
    #
    if argStruct.type is not None:
        if (( argStruct.type.lower() == "any" ) or ( argStruct.type == "*" )):
            lftch_cfg['type'] = "*"
        elif ( argStruct.type.upper() == "CE" ):
            lftch_cfg['type'] = "CE"
        elif (( argStruct.type.upper() == "SRM" ) or
              ( argStruct.type.upper() == "SE" )):
            lftch_cfg['type'] = "SRM"
        elif ( argStruct.type.upper() == "XROOTD" ):
            lftch_cfg['type'] = "XROOTD"
        elif ( argStruct.type.lower() == "site" ):
            lftch_cfg['type'] = "site"
        elif argStruct.type in LFTCH_PROBE_ORDER:
            lftch_cfg['type'] = argStruct.type
        elif argStruct.type[8:] in LFTCH_PROBE_ORDER:
            lftch_cfg['type'] = argStruct.type[8:]
        elif argStruct.type[8:].split("-/cms/Role=",1)[0] in LFTCH_PROBE_ORDER:
            lftch_cfg['type'] = argStruct.type[8:].split("-/cms/Role=",1)[0]
        else:
            logging.critical("Unknown service type \"%s\"" % argStruct.type)
            sys.exit(1)
    elif argStruct.path is None:
        lftch_cfg['type'] = "*"
    #
    if argStruct.window is not None:
        if ( argStruct.window.find("+") > 0 ):
            bBin,aBin = compList[5].split("+")[0:2]
        else:
            logging.critical("Bad timebin window parameter \"%s\"" %
                                                              argStruct.window)
            sys.exit(1)
    elif argStruct.path is None:
        bBin,aBin = lftch_cfg['dfltwin'].split("+")[0:2]
    #
    if ( bBin == "day" ):
        lftch_cfg['before'] = int( (lftch_cfg['time'] % 86400) /
                                                          lftch_cfg['period'] )
    elif ( bBin.isdigit() ):
        lftch_cfg['before'] = int(bBin)
    elif (( bBin is None ) or ( bBin == "" )):
        lftch_cfg['before'] = 0
    else:
        logging.critical("Bad before-timebin window parameter \"%s\"" % bBin)
        sys.exit(1)
    if ( aBin == "day" ):
        lftch_cfg['after'] = int( ( 86400 - (lftch_cfg['time'] % 86400) ) /
                                                      lftch_cfg['period'] ) - 1
    elif ( aBin.isdigit() ):
        lftch_cfg['after'] = int(aBin)
    elif (( aBin is None ) or ( aBin == "" )):
        lftch_cfg['after'] = 0
    else:
        logging.critical("Bad after-timebin window parameter \"%s\"" % aBin)
        sys.exit(1)
    #
    if argStruct.json is not None:
        lftch_cfg['json'] = allowedCharRegex.sub("", argStruct.json )
    #
    if argStruct.html is not None:
        lftch_cfg['html'] = allowedCharRegex.sub("", argStruct.html )



    # fetch relevant MonIT documents:
    # ===============================
    lftch_monitdocs = lftch_monit_fetch(lftch_cfg)



    # write docs in annotated JSON format to file:
    # ============================================
    if 'json' in lftch_cfg:
        rc += lftch_write_json(lftch_cfg, lftch_monitdocs)



    # write docs in HTML table format as mainDVI section to file:
    # ===========================================================
    if 'html' in lftch_cfg:
        if ( lftch_cfg['metric'][:3] == "etf" ):
            rc += lftch_maindvi_etf(lftch_cfg, lftch_monitdocs)
        elif ( lftch_cfg['metric'][:4] == "down" ):
            rc += lftch_maindvi_down(lftch_cfg, lftch_monitdocs)
        elif ( lftch_cfg['metric'][:3] == "sam" ):
            rc += lftch_maindvi_sam(lftch_cfg, lftch_monitdocs)
        elif ( lftch_cfg['metric'][:2] == "hc" ):
            rc += lftch_maindvi_hc(lftch_cfg, lftch_monitdocs)
        elif ( lftch_cfg['metric'][:3] == "fts" ):
            rc += lftch_maindvi_fts(lftch_cfg, lftch_monitdocs)
        elif ( lftch_cfg['metric'][:2] == "sr" ):
            rc += lftch_maindvi_sr(lftch_cfg, lftch_monitdocs)
        elif ( lftch_cfg['metric'][:3] == "sts" ):
            rc += lftch_maindvi_sts(lftch_cfg, lftch_monitdocs)



    # print docs in annotated JSON format to stdout:
    # ==============================================
    if (( 'json' not in lftch_cfg ) and ( 'html' not in lftch_cfg )):
        rc += lftch_print_json(lftch_cfg, lftch_monitdocs)



    #import pdb; pdb.set_trace()
    if ( rc != 0 ):
        sys.exit(1)
    sys.exit(0)