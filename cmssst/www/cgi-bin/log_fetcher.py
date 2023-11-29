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
#    sam1hour                                 / srgroup        /
#    sam6hour                                   rrgroup        /
#    sam1day                                    argroup        / debug
#    hc15min     "HammerCloud"                  vrgroup
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
#    links15min  "Easy view FTS transfers/links"
#    links1hour
#    links6hour
#    links1day



import os, sys
import time, calendar
import logging
import argparse
import re
import json
import gzip
#
# setup the Java/HDFS/PATH environment for pydoop to work properly:
os.environ["HADOOP_CONF_DIR"] = "/eos/user/c/cmssst/packages/etc/hadoop/conf/hadoop.analytix"
os.environ["JAVA_HOME"]       = "/eos/user/c/cmssst/packages/lib/jvm/java-1.8.0-openjdk-1.8.0.201.b09-2.el7_6.x86_64/jre"
os.environ["HADOOP_PREFIX"]   = "/eos/user/c/cmssst/packages/hadoop/hadoop-2.7.5"
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
LFTCH_SERVICE_ORDER = [ "site", "CE", "SRM", "WEBDAV", "XROOTD", "perfSONAR" ]
LFTCH_TRANSFER_ORDER = [ "site", "rse", "GSIFTP-destination", "GSIFTP-source",
                         "WEBDAV-destination", "WEBDAV-source", "destination",
                         "source", "GSIFTP-link", "WEBDAV-link", "link" ]
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
        'dfltwin': "day+0" },
    'links15min': {
        'title': "Links 15 min",
        'period': 900,
        'hdfs': "/project/monitoring/archive/cmssst/raw/ssbmetric/fts15min/",
        'dfltwin': "1+1" },
    'links1hour': {
        'title': "Links 1 hour",
        'period': 3600,
        'hdfs': "/project/monitoring/archive/cmssst/raw/ssbmetric/fts1hour/",
        'dfltwin': "0+0" },
    'links6hour': {
        'title': "Links 6 hours",
        'period': 21600,
        'hdfs': "/project/monitoring/archive/cmssst/raw/ssbmetric/fts6hour/",
        'dfltwin': "0+0" },
    'links1day': {
        'title': "Links 1 day",
        'period': 86400,
        'hdfs': "/project/monitoring/archive/cmssst/raw/ssbmetric/fts1day/",
        'dfltwin': "0+0" }
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
LFTCH_SITE_GROUPS = {
    'AllSites':        [ "T" ],
    'All12Sites':      [ "T1", "T2" ],
    'American12Sites': [ "T1_US", "T2_BR", "T2_US" ],
    'Asian12Sites':    [ "T2_CN", "T2_IN", "T2_KR", "T2_PK", "T2_TR", "T2_TW" ],
    'Eurasian12Sites': [ "T0_CH",
                         "T1_DE", "T1_ES", "T1_FR", "T1_IT", "T1_RU", "T1_UK",
                         "T2_AT", "T2_BE", "T2_CH", "T2_CN", "T2_DE", "T2_EE",
                         "T2_ES", "T2_FI", "T2_FR", "T2_GR", "T2_HU", "T2_IN",
                         "T2_IT", "T2_KR", "T2_LV", "T2_PK", "T2_PL", "T2_PT",
                         "T2_RU", "T2_TR", "T2_TW", "T2_UA", "T2_UK" ],
    'European12Sites': [ "T0_CH",
                         "T1_DE", "T1_ES", "T1_FR", "T1_IT", "T1_RU", "T1_UK",
                         "T2_AT", "T2_BE", "T2_CH", "T2_DE", "T2_EE", "T2_ES",
                         "T2_FI", "T2_FR", "T2_GR", "T2_HU", "T2_IT", "T2_LV",
                         "T2_PL", "T2_PT", "T2_RU", "T2_UA", "T2_UK" ],
    'Tier1Sites':      [ "T1" ],
    'Tier2Sites':      [ "T2" ],
    'Tier3Sites':      [ "T3" ]
    }
# ########################################################################### #



def lftch_monit_fetch(cfg):
    """function to fetch relevant documents from MonIT/HDFS"""
    # #################################################################### #
    # return dictionary with list of documents from MonIT for each timebin #
    # #################################################################### #
    #
    siteRegex = re.compile(r"T\d_[A-Z]{2,2}_\w+")
    #
    timebin  = int( cfg['time'] / cfg['period'] )
    startTIS = cfg['time'] - ( cfg['period'] * cfg['before'] )
    limitTIS = cfg['time'] + ( cfg['period'] * ( cfg['after'] + 1 ) )
    #
    if ( cfg['type'][1:] == "rgroup" ):
        matchList = LFTCH_SITE_GROUPS[ cfg['name'] ]
        matchLen  = len( matchList[0] )
    else:
        matchList = None
        matchLen = 0
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
                                if (( myJson['metadata']['topic'][-15:] !=
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
                                if ( "monit_hdfs_path" not in
                                                          myJson['metadata'] ):
                                    if ( "path" in myJson['metadata'] ):
                                        myJson['metadata']['monit_hdfs_path'] \
                                                   = myJson['metadata']['path']
                                    else:
                                        continue
                                # check document has required downtime keys:
                                if (( 'timestamp' not in myJson['metadata'] ) or
                                    ( 'name' not in myJson['data'] ) or
                                    ( 'type' not in myJson['data'] ) or
                                    ( 'status' not in myJson['data'] ) or
                                    ( 'duration' not in myJson['data'] )):
                                    continue
                                if ( myJson['metadata']['monit_hdfs_path'] !=
                                                                 "down15min" ):
                                    continue
                                tis = int(myJson['metadata']['timestamp']/1000)
                                if ( tis < startTIS ):
                                    continue
                                if ( tis >= limitTIS ):
                                    continue
                                myName = myJson['data']['name']
                                if (( siteRegex.match(cfg['name']) \
                                                              is not None ) and
                                    ( cfg['type'] == "*" )):
                                    if (( myName != cfg['name'] ) and
                                        ( myName.count(".") < 2 )):
                                        continue
                                elif ( cfg['name'] != "*" ):
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
                                if ( "monit_hdfs_path" not in
                                                          myJson['metadata'] ):
                                    if ( "path" in myJson['metadata'] ):
                                        myJson['metadata']['monit_hdfs_path'] \
                                                   = myJson['metadata']['path']
                                    else:
                                        continue
                                # check document has required CMS-SAM keys:
                                if (( 'timestamp' not in myJson['metadata'] ) or
                                    ( 'name' not in myJson['data'] ) or
                                    ( 'type' not in myJson['data'] ) or
                                    ( 'status' not in myJson['data'] )):
                                    continue
                                if ( myJson['metadata']['monit_hdfs_path'] !=
                                     cfg['metric'] ):
                                    continue
                                tis = int(myJson['metadata']['timestamp']/1000)
                                if ( tis < startTIS ):
                                    continue
                                if ( tis >= limitTIS ):
                                    continue
                                myName = myJson['data']['name']
                                if ( matchList is not None ):
                                    if ( myName[:matchLen] not in matchList ):
                                        continue
                                elif (( siteRegex.match(cfg['name']) \
                                                              is not None ) and
                                      ( cfg['type'] == "*" )):
                                    if (( myName != cfg['name'] ) and
                                        ( myName.count(".") < 2 )):
                                        continue
                                elif ( cfg['name'] != "*" ):
                                    if ( myName != cfg['name'] ):
                                        continue
                                myType = myJson['data']['type']
                                if ( cfg['type'][1:] == "rgroup" ):
                                    if ( myType != "site" ):
                                        continue
                                elif ( cfg['type'] != "*" ):
                                    if ( myType != cfg['type'] ):
                                        continue
                                myStatus = myJson['data']['status']
                            elif ( cfg['metric'][:2] == "hc" ):
                                if ( "monit_hdfs_path" not in
                                                          myJson['metadata'] ):
                                    if ( "path" in myJson['metadata'] ):
                                        myJson['metadata']['monit_hdfs_path'] \
                                                   = myJson['metadata']['path']
                                    else:
                                        continue
                                # check document has required CMS-HC keys:
                                if (( 'timestamp' not in myJson['metadata'] ) or
                                    (( 'name' not in myJson['data'] ) and
                                     ( 'site' not in myJson['data'] )) or
                                    ( 'status' not in myJson['data'] )):
                                    continue
                                if ( myJson['metadata']['monit_hdfs_path'] !=
                                     cfg['metric'] ):
                                    continue
                                tis = int(myJson['metadata']['timestamp']/1000)
                                if ( tis < startTIS ):
                                    continue
                                if ( tis >= limitTIS ):
                                    continue
                                if 'name' not in myJson['data']:
                                    myJson['data']['name'] = myJson['data']['site']
                                myName = myJson['data']['name']
                                if ( matchList is not None ):
                                    if ( myName[:matchLen] not in matchList ):
                                        continue
                                elif ( cfg['name'] != "*" ):
                                    if ( myName != cfg['name'] ):
                                        continue
                                myType = "site"
                                myStatus = myJson['data']['status']
                            elif ( cfg['metric'][:3] == "fts" ):
                                if ( "monit_hdfs_path" not in
                                                          myJson['metadata'] ):
                                    if ( "path" in myJson['metadata'] ):
                                        myJson['metadata']['monit_hdfs_path'] \
                                                   = myJson['metadata']['path']
                                    else:
                                        continue
                                # check document has required CMS-FTS keys:
                                if (( 'timestamp' not in myJson['metadata'] ) or
                                    ( 'name' not in myJson['data'] ) or
                                    ( 'type' not in myJson['data'] ) or
                                    ( 'status' not in myJson['data'] )):
                                    continue
                                if ( myJson['metadata']['monit_hdfs_path'] !=
                                     cfg['metric'] ):
                                    continue
                                tis = int(myJson['metadata']['timestamp']/1000)
                                if ( tis < startTIS ):
                                    continue
                                if ( tis >= limitTIS ):
                                    continue
                                myName = myJson['data']['name']
                                if ( matchList is not None ):
                                    if ( myName[:matchLen] not in matchList ):
                                        continue
                                elif (( siteRegex.match(cfg['name']) \
                                                              is not None ) and
                                      ( cfg['type'] == "*" )):
                                    myLength = len(cfg['name'])
                                    if (( myName[:myLength] != cfg['name'] ) and
                                        ( myName.count(".") < 2 )):
                                        continue
                                elif ( cfg['name'] != "*" ):
                                    if ( myName != cfg['name'] ):
                                        continue
                                myType = myJson['data']['type']
                                if ( cfg['type'][1:] == "rgroup" ):
                                    if ( myType != "site" ):
                                        continue
                                elif ( cfg['type'] != "*" ):
                                    if ( myType != cfg['type'] ):
                                        continue
                                myStatus = myJson['data']['status']
                            elif ( cfg['metric'][:2] == "sr" ):
                                if ( "monit_hdfs_path" not in
                                                          myJson['metadata'] ):
                                    if ( "path" in myJson['metadata'] ):
                                        myJson['metadata']['monit_hdfs_path'] \
                                                   = myJson['metadata']['path']
                                    else:
                                        continue
                                # check document has SiteReadiness keys:
                                if (( 'timestamp' not in myJson['metadata'] ) or
                                    ( 'name' not in myJson['data'] ) or
                                    ( 'status' not in myJson['data'] )):
                                    continue
                                if ( myJson['metadata']['monit_hdfs_path'] !=
                                     cfg['metric'] ):
                                    continue
                                tis = int(myJson['metadata']['timestamp']/1000)
                                if ( tis < startTIS ):
                                    continue
                                if ( tis >= limitTIS ):
                                    continue
                                myName = myJson['data']['name']
                                if ( matchList is not None ):
                                    if ( myName[:matchLen] not in matchList ):
                                        continue
                                elif ( cfg['name'] != "*" ):
                                    if ( myName != cfg['name'] ):
                                        continue
                                myType = "site"
                                myStatus = myJson['data']['status']
                            elif ( cfg['metric'][:3] == "sts" ):
                                if ( "monit_hdfs_path" not in
                                                          myJson['metadata'] ):
                                    if ( "path" in myJson['metadata'] ):
                                        myJson['metadata']['monit_hdfs_path'] \
                                                   = myJson['metadata']['path']
                                    else:
                                        continue
                                # check document has required SiteStatus keys:
                                if (( 'timestamp' not in myJson['metadata'] ) or
                                    ( 'name' not in myJson['data'] ) or
                                    ( 'status' not in myJson['data'] ) or
                                    ( 'prod_status' not in myJson['data'] ) or
                                    ( 'crab_status' not in myJson['data'] )):
                                    continue
                                if ( myJson['metadata']['monit_hdfs_path'] !=
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
                            elif ( cfg['metric'][:5] == "links" ):
                                if ( "monit_hdfs_path" not in
                                                          myJson['metadata'] ):
                                    if ( "path" in myJson['metadata'] ):
                                        myJson['metadata']['monit_hdfs_path'] \
                                                   = myJson['metadata']['path']
                                    else:
                                        continue
                                # check document has required CMS-FTS keys:
                                if (( 'timestamp' not in myJson['metadata'] ) or
                                    ( 'name' not in myJson['data'] ) or
                                    ( 'type' not in myJson['data'] ) or
                                    ( 'status' not in myJson['data'] )):
                                    continue
                                if ( myJson['metadata']['monit_hdfs_path'] !=
                                     ("fts" + cfg['metric'][5:]) ):
                                    continue
                                tis = int(myJson['metadata']['timestamp']/1000)
                                tbin = int( tis / cfg['period'] )
                                if ( tbin != timebin ):
                                    continue
                                myName = myJson['data']['name']
                                myType = myJson['data']['type']
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
                            if ( cfg['type'][1:] == "rgroup" ):
                                try:
                                    if ( cfg['type'][0] == "s" ):
                                        if (( myStatus == "ok" ) or
                                            ( myStatus == "warning" )):
                                            myCntrbt = 1.000
                                        else:
                                            myCntrbt = 0.000
                                    elif ( cfg['type'][0] == "r" ):
                                        myCntrbt = myJson['data']['reliability']
                                    elif ( cfg['type'][0] == "a" ):
                                        myCntrbt = myJson['data']['availability']
                                    else:
                                        if ( cfg['metric'][:3] == "fts" ):
                                            myCntrbt = myJson['data']['quality']
                                        else:
                                            myCntrbt = myJson['data']['value']
                                    myDowntime = False
                                    if (( cfg['metric'][:3] == "sam" ) or
                                        ( cfg['metric'][:2] == "sr" )):
                                        if ( myStatus == "downtime" ):
                                            myDowntime = True
                                except KeyError:
                                    myCntrbt = 0
                                    myDowntime = False
                                lftch_monitdocs[tbin].append( { 'name': myName,
                                        'vrsn': version, 'cntrbt': myCntrbt,
                                                       'dwnflg': myDowntime } )
                            else:
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
    #
    siteRegex = re.compile(r"T\d_[A-Z]{2,2}_\w+")


    # filter out services selected in excess:
    # =======================================
    if (( siteRegex.match(cfg['name']) is not None ) and
        ( cfg['type'] == "*" )):
        selectSet = set()
        for tbin in docs:
            for myDoc in docs[tbin]:
                if ( myDoc['type'] != "site" ):
                    continue
                try:
                    myDetail = myDoc['detail']
                except KeyError:
                    continue
                for myWord in myDetail.split():
                    if ( myWord[0] == "(" ):
                        myWord = myWord[1:]
                    if ( myWord[-1] == ")" ):
                        myWord = myWord[:-1]
                    myWord = myWord.split(",")[0]
                    myWord = myWord.split("/")[0]
                    if (( myWord.count(".") < 2 ) or ( len(myWord) <= 6 )):
                        continue
                    selectSet.add( myWord )
        for tbin in docs:
            for indx in range(len(docs[tbin])-1,-1,-1):
                if ( docs[tbin][indx]['type'] == "site" ):
                    continue
                else:
                    if ( docs[tbin][indx]['name'] in selectSet ):
                        continue
                del docs[tbin][indx]


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
    #
    siteRegex = re.compile(r"T\d_[A-Z]{2,2}_\w+")


    # filter out services selected in excess:
    # =======================================
    lineRegex = re.compile(r"^((([a-z0-9\-]+)\.)+[a-z0-9\-]+)/\w* \(\w*\)\s*$")
    if (( siteRegex.match(cfg['name']) is not None ) and
        ( cfg['type'] == "*" )):
        selectSet = set()
        for tbin in docs:
            for myDoc in docs[tbin]:
                if ( myDoc['type'] != "site" ):
                    continue
                try:
                    myDetail = myDoc['detail']
                except KeyError:
                    continue
                for myLine in myDetail.splitlines():
                    matchObj = lineRegex.match( myLine )
                    if matchObj is None:
                        continue
                    selectSet.add( matchObj[1] )
        for tbin in docs:
            for indx in range(len(docs[tbin])-1,-1,-1):
                if ( docs[tbin][indx]['type'] == "site" ):
                    continue
                else:
                    if ( docs[tbin][indx]['name'] in selectSet ):
                        continue
                del docs[tbin][indx]


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
                            "      \"status\": \"%s\",\n") %
                           (myDoc['name'], myDoc['status']))
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
    #
    siteRegex = re.compile(r"T\d_[A-Z]{2,2}_\w+")


    # filter out links, sources, and destinations selected in excess:
    # ===============================================================
    olineRegex = re.compile(r"^((([a-z0-9\-]+)\.)+[a-z0-9\-]+): \w*/\w*\s*$")
    nlineRegex = re.compile(r"^[A-Z]+[A-Zh\-]*ost ((([a-z0-9\-]+)\.)+[a-z0-9\-]+): \w*/\w*\s*$")
    if (( siteRegex.match(cfg['name']) is not None ) and
        ( cfg['type'] == "*" )):
        selectSet = set()
        for tbin in docs:
            for myDoc in docs[tbin]:
                if ( myDoc['type'] != "site" ):
                    continue
                try:
                    myDetail = myDoc['detail']
                except KeyError:
                    continue
                for myLine in myDetail.splitlines():
                    matchObj = olineRegex.match( myLine )
                    if matchObj is not None:
                        selectSet.add( matchObj[1] )
                    matchObj = nlineRegex.match( myLine )
                    if matchObj is not None:
                        selectSet.add( matchObj[1] )
        for tbin in docs:
            for indx in range(len(docs[tbin])-1,-1,-1):
                myType = docs[tbin][indx]['type']
                myName = docs[tbin][indx]['name']
                if ( myType[-4:] == "link" ):
                    if ( myName.split("___")[0] in selectSet ):
                        continue
                    if ( myName.split("___")[-1] in selectSet ):
                        continue
                elif (( myType[-6:] == "source" ) or
                      ( myType[-11:] == "destination" )):
                    if ( myName in selectSet ):
                        continue
                elif (( myType == "rse" ) or
                      ( myType == "site" )):
                    continue
                del docs[tbin][indx]


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

    if ( cfg['type'][1:] == "rgroup" ):
        logging.error("Writing of JSON for ranking group not implemented")
        return 1

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

    if ( cfg['type'][1:] == "rgroup" ):
        logging.error("Writing of JSON for ranking group not implemented")
        return 1

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
                            myStrng = myDoc['details'].replace("\\n", "<BR>")
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
    #
    siteRegex = re.compile(r"T\d_[A-Z]{2,2}_\w+")


    # filter out services selected in excess:
    # =======================================
    if (( siteRegex.match(cfg['name']) is not None ) and
        ( cfg['type'] == "*" )):
        selectSet = set()
        for tbin in docs:
            for myDoc in docs[tbin]:
                if ( myDoc['type'] != "site" ):
                    continue
                try:
                    myDetail = myDoc['detail']
                except KeyError:
                    continue
                for myWord in myDetail.split():
                    if ( myWord[0] == "(" ):
                        myWord = myWord[1:]
                    if ( myWord[-1] == ")" ):
                        myWord = myWord[:-1]
                    myWord = myWord.split(",")[0]
                    myWord = myWord.split("/")[0]
                    if (( myWord.count(".") < 2 ) or ( len(myWord) <= 6 )):
                        continue
                    selectSet.add( myWord )
        for tbin in docs:
            for indx in range(len(docs[tbin])-1,-1,-1):
                if ( docs[tbin][indx]['type'] == "site" ):
                    continue
                else:
                    if ( docs[tbin][indx]['name'] in selectSet ):
                        continue
                del docs[tbin][indx]


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



def lftch_url4sam(inputString, cfg, tbin, name, clss):
    """function to enhance SAM 15 min results with hyperlinks"""
    # ############################################################### #
    # enhance SAM 15 min results with hyperlink to the evaluation log #
    # ############################################################### #
    LFTCH_LOG_URL = "https://cmssst.web.cern.ch/cgi-bin/log"
    #
    myHTML = ""

    # loop over lines in inputString:
    # ===============================
    lineRegex = re.compile(r"^((([a-z0-9\-]+)\.)+[a-z0-9\-]+)/(\w*) \(\w*\)\s*$")
    newlineFlag = False
    for myLine in inputString.splitlines():
        if ( newlineFlag == True ):
            myHTML += "<BR>"
        #
        if ( myLine[:18] == "15min evaluations:" ):
            t15bin = tbin * cfg['period'] / 900
            n15bin = max(0, int( cfg['period'] / 900 ) - 1)
            if ( clss == "site" ):
                myType = "*"
            else:
                myType = clss
            myHTML += ("<A HREF=\"%s/sam15min/%d/%s/%s/0+%d\">%s</A>" %
                         (LFTCH_LOG_URL, t15bin, name, myType, n15bin, myLine))
        elif (( clss == "site" ) and ( cfg['period'] == 900 )):
            matchObj = lineRegex.match( myLine )
            if ( matchObj is not None ):
                myName = matchObj[1]
                myType = matchObj[matchObj.lastindex]
                if ( cfg['type'] == "*" ):
                    myHTML += ("<A HREF=\"#%s%s\">%s</A>" % (myType, myName,
                                                                       myLine))
                else:
                    myHTML += ("<A HREF=\"%s/sam15min/%d/%s/%s/0+0\">%s</A>" %
                                 (LFTCH_LOG_URL, tbin, myName, myType, myLine))
            else:                        
                myHTML += myLine
        else:
            myHTML += myLine
        newlineFlag = True

    return myHTML



def lftch_maindvi_sam(cfg, docs):
    """function to write CMS SAM documents as HTML table to a file"""
    # ################################################################ #
    # prepare mainDVI section with CMS SAM evaluation according to cfg #
    # ################################################################ #
    LFTCH_SITEMON = "https://monit-grafana.cern.ch/d/m7XtZsEZk4/wlcg-sitemon-historical-tests?orgId=20&var-vo=cms&var-dst_tier=All%s&from=%d000&to=%d000"
    #
    siteRegex = re.compile(r"T\d_[A-Z]{2,2}_\w+")


    # filter out services selected in excess:
    # =======================================
    lineRegex = re.compile(r"^((([a-z0-9\-]+)\.)+[a-z0-9\-]+)/\w* \(\w*\)\s*$")
    if (( siteRegex.match(cfg['name']) is not None ) and
        ( cfg['type'] == "*" )):
        selectSet = set()
        for tbin in docs:
            for myDoc in docs[tbin]:
                if ( myDoc['type'] != "site" ):
                    continue
                try:
                    myDetail = myDoc['detail']
                except KeyError:
                    continue
                for myLine in myDetail.splitlines():
                    matchObj = lineRegex.match( myLine )
                    if matchObj is None:
                        continue
                    selectSet.add( matchObj[1] )
        for tbin in docs:
            for indx in range(len(docs[tbin])-1,-1,-1):
                if ( docs[tbin][indx]['type'] == "site" ):
                    continue
                else:
                    if ( docs[tbin][indx]['name'] in selectSet ):
                        continue
                del docs[tbin][indx]


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
                        myDoc = myDocs[tbin][indx]
                        myFile.write(("   <TD>\n      <A NAME=\"%s%s\"></A>" +
                                      "\n      <TABLE WIDTH=\"100%%\" BORDER" +
                                      "=\"1\" CELLPADDING=\"2\" CELLSPACING=" +
                                      "\"0\">\n      <TR>\n         <TH>Desc" +
                                      "ription\n         <TH>Value\n") %
                                                (myDoc['type'], myDoc['name']))
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
                                myStrng = lftch_url4sam(myDoc['detail'],
                                       cfg, tbin, myDoc['name'], myDoc['type'])
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
                        if ( myDoc['status'] != "unknown" ):
                            sTIS = tbin * cfg['period']
                            eTIS = sTIS + cfg['period']
                            if ( myDoc['type'] == "site" ):
                                sSel = ( "&var-dst_experiment_site=%s&var-ds" +
                                         "t_hostname=All&var-service_flavour" +
                                         "=All" ) % myDoc['name']
                            elif ( myDoc['type'] == "CE" ):
                                sSel = ( "&var-dst_experiment_site=All&var-d" +
                                         "st_hostname=%s&var-service_flavour" +
                                         "=HTCONDOR-CE&var-service_flavour=A" +
                                         "RC-CE" ) % myDoc['name']
                            elif ( myDoc['type'] == "XRD" ):
                                sSel = ( "&var-dst_experiment_site=All&var-d" +
                                         "st_hostname=%s&var-service_flavour" +
                                         "=XROOTD" ) % myDoc['name']
                            else:
                                sSel = ( "&var-dst_experiment_site=All&var-d" +
                                         "st_hostname=%s&var-service_flavour" +
                                         "=%s" ) % (myDoc['name'],
                                                                 myDoc['type'])
                            myFile.write(("      <TR>\n         <TD COLSPAN=" +
                                          "\"2\"><A HREF=\"%s\"><I>Link to t" +
                                          "he WLCG SiteMon Historical Tests " +
                                          "dashboard</I></A>\n") %
                                         (LFTCH_SITEMON %
                                                     (sSel, (sTIS-900), eTIS)))
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
                                                 "sciaba/%s/job_out.%s.%s.txt")
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
    LFTCH_TASKGLBL = "https://monit-grafana.cern.ch/d/cmsTMGlobal/cms-tasks-monitoring-globalview?orgId=11&from=%d000&to=%d000&var-user=sciaba&var-site=All&var-task=All&var-Filters=data.CRAB_Workflow|=~|.*-%s-.*"


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
                        if ( myDoc['status'] != "unknown" ):
                            sTIS = tbin * cfg['period']
                            eTIS = sTIS + cfg['period']
                            myFile.write(("      <TR>\n         <TD COLSPAN=" +
                                          "\"2\"><A HREF=\"%s\"><I>Link to H" +
                                          "C jobs in Grafana task-mon global" +
                                          " view</I></A>\n") %
                                         (LFTCH_TASKGLBL % (sTIS, eTIS,
                                                               myDoc['name'])))
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



def lftch_url4fts(inputString):
    """function to substitute fts references with hyperlinks in a string"""
    # ################################################################### #
    # replace brackets with a FTS reference with hyperlink to the job log #
    # ################################################################### #
    #
    myHTML = ""

    # handle new lines:
    myStrng = inputString.replace("\n", "<BR>")

    indx = 0
    j = myStrng.find("[http")
    while ( j >= 0 ):
        k = myStrng[indx+j:].find("]")
        if ( k > 0 ):
            # copy over anything before the bracket:
            myHTML += myStrng[indx:indx+j]
            #
            # parse job reference inside the bracket:
            myURL = myStrng[indx+j+1:indx+j+k]
            myHost = myURL.split("/")[2].split(":")[0]
            myJob = myURL.split("#")[-1][1:]
            myHTML += "[<A HREF=\"%s\">%s %s</A>]" % (myURL, myHost, myJob)
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



def lftch_maindvi_fts(cfg, docs):
    """function to write CMS FTS documents as HTML table to a file"""
    # ################################################################ #
    # prepare mainDVI section with CMS FTS evaluation according to cfg #
    # ################################################################ #
    LFTCH_FTSDASHB = "https://monit-grafana.cern.ch/d/CIjJHKdGk/fts-transfers?orgId=20&from=%d000&to=%d000&var-group_by=endpnt&var-bin=1h&var-vo=cms&var-src_country=All&var-dst_country=All&var-src_site=All&var-dst_site=All&var-fts_server=All&var-protocol=All&var-staging=All"
    #
    siteRegex = re.compile(r"T\d_[A-Z]{2,2}_\w+")


    # filter out links, sources, and destinations selected in excess:
    # ===============================================================
    olineRegex = re.compile(r"^((([a-z0-9\-]+)\.)+[a-z0-9\-]+): \w*/\w*\s*$")
    nlineRegex = re.compile(r"^[A-Z]+[A-Zh\-]*ost ((([a-z0-9\-]+)\.)+[a-z0-9\-]+): \w*/\w*\s*$")
    if (( siteRegex.match(cfg['name']) is not None ) and
        ( cfg['type'] == "*" )):
        selectSet = set()
        for tbin in docs:
            for myDoc in docs[tbin]:
                if ( myDoc['type'] != "site" ):
                    continue
                try:
                    myDetail = myDoc['detail']
                except KeyError:
                    continue
                for myLine in myDetail.splitlines():
                    matchObj = olineRegex.match( myLine )
                    if matchObj is not None:
                        selectSet.add( matchObj[1] )
                    matchObj = nlineRegex.match( myLine )
                    if matchObj is not None:
                        selectSet.add( matchObj[1] )
        for tbin in docs:
            for indx in range(len(docs[tbin])-1,-1,-1):
                myType = docs[tbin][indx]['type']
                myName = docs[tbin][indx]['name']
                if ( myType[-4:] == "link" ):
                    if ( myName.split("___")[0] in selectSet ):
                        continue
                    if ( myName.split("___")[-1] in selectSet ):
                        continue
                elif (( myType[-6:] == "source" ) or
                      ( myType[-11:] == "destination" )):
                    if ( myName in selectSet ):
                        continue
                elif (( myType == "rse" ) or
                      ( myType == "site" )):
                    continue
                del docs[tbin][indx]


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
                                myStrng = lftch_url4fts( myDoc['detail'] )
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
                        sTIS = 3600 * int( (tbin * cfg['period']) / 3600 )
                        eTIS = 3600 * int( (sTIS + cfg['period']+3599) / 3600 )
                        if ( myDoc['type'] == "site" ):
                            myFile.write(("      <TR>\n         <TD COLSPAN=" +
                                          "\"2\"><A HREF=\"%s&var-include=%s" +
                                          "\"><I>Link to transfers in Grafan" +
                                          "a FTS dashboard</I></A>\n") %
                                         ((LFTCH_FTSDASHB % (sTIS, eTIS)),
                                                                myDoc['name']))
                        elif ( myDoc['type'][-11:] == "destination" ):
                            myFile.write(("      <TR>\n         <TD COLSPAN=" +
                                          "\"2\"><A HREF=\"%s&var-filters=da" +
                                          "ta.dst_hostname|=|%s\"><I>Link to" +
                                          " transfers in Grafana FTS dashboa" +
                                          "rd</I></A>\n") % ((LFTCH_FTSDASHB %
                                                 (sTIS, eTIS)), myDoc['name']))
                        elif ( myDoc['type'][-6:] == "source" ):
                            myFile.write(("      <TR>\n         <TD COLSPAN=" +
                                          "\"2\"><A HREF=\"%s&var-filters=da" +
                                          "ta.src_hostname|=|%s\"><I>Link to" +
                                          " transfers in Grafana FTS dashboa" +
                                          "rd</I></A>\n") % ((LFTCH_FTSDASHB %
                                                 (sTIS, eTIS)), myDoc['name']))
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
    LFTCH_LOG_URL = "https://cmssst.web.cern.ch/cgi-bin/log"
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
            myHTML += ("<A HREF=\"%s/%s/%d/%s/*/day+0\">%s</A>" %
                       (LFTCH_LOG_URL, "down15min", t15bin, site, myLine))
        elif ( myLine[0:5] == "SAM: " ):
            if ( cfg['period'] == 900 ):
                myHTML += ("<A HREF=\"%s/sam%s/%d/%s/*/0+0\">%s</A>" % 
                        (LFTCH_LOG_URL, cfg['metric'][2:], tbin, site, myLine))
            else:
                myHTML += ("<A HREF=\"%s/sam%s/%d/%s/site/0+0\">%s</A>" % 
                        (LFTCH_LOG_URL, cfg['metric'][2:], tbin, site, myLine))
        elif ( myLine[0:4] == "HC: " ):
            myHTML += ("<A HREF=\"%s/hc%s/%d/%s/site/0+0\">%s</A>" %
                       (LFTCH_LOG_URL, cfg['metric'][2:], tbin, site, myLine))
        elif ( myLine[0:5] == "FTS: " ):
            myHTML += ("<A HREF=\"%s/links%s/%d/%s/*/0+0\">%s</A>" %
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



def lftch_maindvi_links(cfg, docs):
    """function to write CMS FTS documents as HTML table to a file"""
    # ################################################################## #
    # prepare mainDVI section with CMS Link evaluations according to cfg #
    # ################################################################## #
    LFTCH_FTSDASHB = "https://monit-grafana.cern.ch/d/CIjJHKdGk/fts-transfers?orgId=20&from=%d000&to=%d000&var-group_by=endpnt&var-bin=1h&var-vo=cms&var-src_country=All&var-dst_country=All&var-src_site=All&var-dst_site=All&var-fts_server=All&var-protocol=All&var-staging=All"
    #
    siteRegex = re.compile(r"T\d_[A-Z]{2,2}_\w+")


    # consider only the main time bin:
    # ================================
    tbin = int( cfg['time'] / cfg['period'] )
    if tbin not in docs:
        docs[tbin] = []
    #
    # discard superseded documents:
    highestVersions = {}
    for myDoc in docs[tbin]:
        key = ( myDoc['name'], myDoc['type'] )
        if key not in highestVersions:
            highestVersions[key] = myDoc['***VERSION***']
        elif ( myDoc['***VERSION***'] > highestVersions[key] ):
            highestVersions[key] = myDoc['***VERSION***']
    #
    # organize documents by type:
    lnkDocs = {}
    w_lDocs = {}
    x_lDocs = {}
    srcDocs = {}
    w_sDocs = {}
    x_sDocs = {}
    dstDocs = {}
    w_dDocs = {}
    x_dDocs = {}
    rseDocs = {}
    siteDocs = {}
    for myDoc in docs[tbin]:
        key = ( myDoc['name'], myDoc['type'] )
        if ( myDoc['***VERSION***'] < highestVersions[key] ):
            continue
        if (( myDoc['type'] == "link" ) or
            ( myDoc['type'] == "GSIFTP-link" )):
            lnkDocs[ myDoc['name'] ] = myDoc
        elif ( myDoc['type'] == "WEBDAV-link" ):
            w_lDocs[ myDoc['name'] ] = myDoc
        elif ( myDoc['type'] == "XROOTD-link" ):
            x_lDocs[ myDoc['name'] ] = myDoc
        elif (( myDoc['type'] == "source" ) or
              ( myDoc['type'] == "GSIFTP-source" )):
            srcDocs[ myDoc['name'] ] = myDoc
        elif ( myDoc['type'] == "WEBDAV-source" ):
            w_sDocs[ myDoc['name'] ] = myDoc
        elif ( myDoc['type'] == "XROOTD-source" ):
            x_sDocs[ myDoc['name'] ] = myDoc
        elif (( myDoc['type']== "destination" ) or
              ( myDoc['type']== "GSIFTP-destination" )):
            dstDocs[ myDoc['name'] ] = myDoc
        elif ( myDoc['type']== "WEBDAV-destination" ):
            w_dDocs[ myDoc['name'] ] = myDoc
        elif ( myDoc['type']== "XROOTD-destination" ):
            x_dDocs[ myDoc['name'] ] = myDoc
        elif ( myDoc['type'] == "rse" ):
            rseDocs[ myDoc['name'] ] = myDoc
        elif ( myDoc['type'] == "site" ):
            siteDocs[ myDoc['name'] ] = myDoc
    #
    # make site -- source/destination host list:
    tplList = set()
    w_tList = set()
    x_tList = set()
    selectSet = set()
    olineRegex = re.compile(r"^((([a-z0-9\-]+)\.)+[a-z0-9\-]+): \w*/\w*\s*$")
    nlineRegex = re.compile(r"^[A-Z]+[A-Zh\-]*ost ((([a-z0-9\-]+)\.)+[a-z0-9\-]+): \w*/\w*\s*$")
    for site in siteDocs:
        try:
            detail = siteDocs[site]['detail']
        except KeyError:
            continue
        for myLine in detail.splitlines():
            matchObj = olineRegex.match( myLine )
            if matchObj is not None:
                tplList.add( (siteDocs[site]['name'], matchObj[1]) )
                if ( cfg['name'] == site ):
                    selectSet.add( matchObj[1] )
            matchObj = nlineRegex.match( myLine )
            if matchObj is not None:
                proto = myLine.split("-")[0]
                if ( len(proto) != 6 ):
                    proto = "GSIFTP"
                if ( proto == "GSIFTP" ):
                    tplList.add( (siteDocs[site]['name'], matchObj[1]) )
                elif ( proto == "WEBDAV" ):
                    w_tList.add( (siteDocs[site]['name'], matchObj[1]) )
                elif ( proto == "XROOTD" ):
                    x_tList.add( (siteDocs[site]['name'], matchObj[1]) )
                if ( cfg['name'] == site ):
                    selectSet.add( matchObj[1] )
    hstList = [ tuple[1] for tuple in tplList ]
    w_hList = [ tuple[1] for tuple in w_tList ]
    x_hList = [ tuple[1] for tuple in x_tList ]
    #
    # make excluded source/destination host list:
    exSrc = []
    for source in srcDocs:
        try:
            detail = srcDocs[source]['detail']
        except KeyError:
            detail = ""
        for myLine in detail.splitlines():
            if ( myLine[:45] == "excluded from destination endpoint evaluation" ):
                exSrc.append( srcDocs[source]['name'] )
        if srcDocs[source]['name'] not in hstList:
            tplList.add( ("T9_CC_Unknown", srcDocs[source]['name']) )
            hstList.append( srcDocs[source]['name'] )
    wxSrc = []
    for source in w_sDocs:
        try:
            detail = w_sDocs[source]['detail']
        except KeyError:
            detail = ""
        for myLine in detail.splitlines():
            if ( myLine[:45] == "excluded from destination endpoint evaluation" ):
                wxSrc.append( w_sDocs[source]['name'] )
        if w_sDocs[source]['name'] not in w_hList:
            w_tList.add( ("T9_CC_Unknown", w_sDocs[source]['name']) )
            w_hList.append( w_sDocs[source]['name'] )
    xxSrc = []
    for source in x_sDocs:
        try:
            detail = x_sDocs[source]['detail']
        except KeyError:
            detail = ""
        for myLine in detail.splitlines():
            if ( myLine[:45] == "excluded from destination endpoint evaluation" ):
                xxSrc.append( x_sDocs[source]['name'] )
        if x_sDocs[source]['name'] not in x_hList:
            x_tList.add( ("T9_CC_Unknown", x_sDocs[source]['name']) )
            x_hList.append( x_sDocs[source]['name'] )
    exDst = []
    for dest in dstDocs:
        try:
            detail = dstDocs[dest]['detail']
        except KeyError:
            detail = ""
        for myLine in detail.splitlines():
            if ( myLine[:40] == "excluded from source endpoint evaluation" ):
                exDst.append( dstDocs[dest]['name'] )
        if dstDocs[dest]['name'] not in hstList:
            tplList.add( ("T9_CC_Unknown", dstDocs[dest]['name']) )
            hstList.append( dstDocs[dest]['name'] )
    wxDst = []
    for dest in w_dDocs:
        try:
            detail = w_dDocs[dest]['detail']
        except KeyError:
            detail = ""
        for myLine in detail.splitlines():
            if ( myLine[:40] == "excluded from source endpoint evaluation" ):
                wxDst.append( w_dDocs[dest]['name'] )
        if w_dDocs[dest]['name'] not in w_hList:
            w_tList.add( ("T9_CC_Unknown", w_dDocs[dest]['name']) )
            w_hList.append( w_dDocs[dest]['name'] )
    xxDst = []
    for dest in x_dDocs:
        try:
            detail = x_dDocs[dest]['detail']
        except KeyError:
            detail = ""
        for myLine in detail.splitlines():
            if ( myLine[:40] == "excluded from source endpoint evaluation" ):
                xxDst.append( x_dDocs[dest]['name'] )
        if x_dDocs[dest]['name'] not in x_hList:
            x_tList.add( ("T9_CC_Unknown", x_dDocs[dest]['name']) )
            x_hList.append( x_dDocs[dest]['name'] )
    del hstList
    del w_hList
    del x_hList
    tplList = sorted( tplList )
    w_tList = sorted( w_tList )
    x_tList = sorted( x_tList )
    noHost = len( tplList )
    woHost = len( w_tList )
    xoHost = len( x_tList )
    #
    timeStrng = time.strftime("%A", time.gmtime(cfg['time']))[:2] + ", " + \
                  time.strftime("%Y-%b-%d %H:%M UTC", time.gmtime(cfg['time']))


    # filter links, sources, destinations, and sites selected in excess:
    # ==================================================================
    myLength = len(cfg['name'])
    if (( siteRegex.match(cfg['name']) is not None ) and
        ( cfg['type'] == "*" )):
        for site in sorted( siteDocs ):
            if ( site != cfg['name'] ):
                del siteDocs[ site ]
        for rse in sorted( rseDocs ):
            if ( rse[:myLength] != cfg['name'] ):
                del rseDocs[ rse ]
        for source in sorted( srcDocs.keys() ):
            if ( source not in selectSet ):
                del srcDocs[ source ]
        for source in sorted( w_sDocs.keys() ):
            if ( source not in selectSet ):
                del w_sDocs[ source ]
        for source in sorted( x_sDocs.keys() ):
            if ( source not in selectSet ):
                del x_sDocs[ source ]
        for dest in sorted( dstDocs.keys() ):
            if ( dest not in selectSet ):
                del dstDocs[ dest ]
        for dest in sorted( w_dDocs.keys() ):
            if ( dest not in selectSet ):
                del w_dDocs[ dest ]
        for dest in sorted( x_dDocs.keys() ):
            if ( dest not in selectSet ):
                del x_dDocs[ dest ]
        for link in sorted( lnkDocs.keys() ):
            if ( link.split("___")[0] in selectSet ):
                continue
            if ( link.split("___")[-1] in selectSet ):
                continue
            del lnkDocs[ link ]
        for link in sorted( w_lDocs.keys() ):
            if ( link.split("___")[0] in selectSet ):
                continue
            if ( link.split("___")[-1] in selectSet ):
                continue
            del w_lDocs[ link ]
        for link in sorted( x_lDocs.keys() ):
            if ( link.split("___")[0] in selectSet ):
                continue
            if ( link.split("___")[-1] in selectSet ):
                continue
            del x_lDocs[ link ]


    # write mainDVI Links HTML section:
    # =================================
    myHTML = cfg['html'] + "_wrk"
    #
    try:
        with open(myHTML, 'wt') as myFile:
            myFile.write("   <STYLE TYPE=\"text/css\">\n      BODY {\n      " +
                         "   background-color: white; color: black;\n      }" +
                         "\n      TD A, TD A:LINK, TD A:VISITED {\n         " +
                         "text-decoration: none; color: black;\n      }\n   " +
                         "   TH.Label {\n         width: 256px; padding: 2px" +
                         ";\n         background-color: white; color: black;" +
                         "\n         text-decoration: none;\n         border" +
                         "-right: 4px solid black;\n         font-size: larg" +
                         "e; font-weight: bold;\n         white-space: nowra" +
                         "p; vertical-align: bottom;\n      }\n" +
                         "      TH.Destination {\n         width: 24px;\n   " +
                         "      background-color: white; color: black;\n    " +
                         "     text-decoration: none;\n         border-botto" +
                         "m: 4px solid black;\n         font-size: medium; f" +
                         "ont-weight: normal;\n         white-space: nowrap;" +
                         " vertical-align: bottom; text-align: left;\n      " +
                         "}\n      TH.Destination DIV {\n         width: 256" +
                         "px;\n         transform: translate(-28px,-86px) ro" +
                         "tate(315deg);\n         overflow: hidden;\n      }" +
                         "\n      TH.Destination A, TH.Destination A:LINK, T" +
                         "H.Destination A:VISITED {\n          text-decorati" +
                         "on: none; color: black;\n      }\n" +
                         "      TH.Source {\n         width: 256px; height: " +
                         "24px; padding-right: 2px;\n         background-col" +
                         "or: white; color: black;\n         text-decoration" +
                         ": none;\n         border-right: 4px solid black;\n" +
                         "         font-size: medium; font-weight: normal;\n" +
                         "         white-space: nowrap; vertical-align: midd" +
                         "le; text-align: right;\n         overflow: hidden;" +
                         "\n      }\n      TH.Source A, TH.Source A:LINK, TH" +
                         ".Source A:VISITED {\n          text-decoration: no" +
                         "ne; color: black;\n      }\n      TD.Eval {\n     " +
                         "     width: 24px; height: 24px;\n          backgro" +
                         "und-color: white;\n      }\n      TD.EvalSelf {\n " +
                         "         width: 24px; height: 24px;\n          bac" +
                         "kground-color: black;\n      }\n      TD.EvalGood " +
                         "{\n          width: 24px; height: 24px;\n         " +
                         " background-color: #80FF80;\n      }\n      TD.Eva" +
                         "lWarn {\n          width: 24px; height: 24px;\n   " +
                         "       background-color: #FFFF00;\n      }\n      " +
                         "TD.EvalBad {\n          width: 24px; height: 24px;" +
                         "\n          background-color: #FF0000;\n      }\n " +
                         "     .qualityTip {\n         display: block;\n    " +
                         "     text-decoration: none; position: relative;\n " +
                         "     }\n      .qualityTip SPAN {\n         display" +
                         ": none;\n         border-radius: 4px;\n      }\n  " +
                         "    .qualityTip:hover SPAN {\n         background-" +
                         "color: white; color: black;\n         white-space:" +
                         " nowrap;\n         display: block;\n         posit" +
                         "ion: absolute;\n         top: 95%; left: 50%;\n   " +
                         "      transform: translateX(-50%);\n         z-ind" +
                         "ex: 1000;\n         width:auto; min-height:16px;\n" +
                         "         border:1px solid black; padding:4px;\n   " +
                         "   }\n" +
                         "      TH.LinkHeader {\n         line-height: 1.5; " +
                         "padding: 2px; padding-left: 10px;\n         backgr" +
                         "ound-color: #6A6A7D; color: white;\n         text-" +
                         "decoration: none;\n         font-size: x-large; fo" +
                         "nt-weight: bold;\n         white-space: nowrap; te" +
                         "xt-align: left;\n      }\n      TH.LinkHeader A, T" +
                         "H.LinkHeader A:LINK, TH.LinkHeader A:VISITED {\n  " +
                         "         text-decoration: none; color: white;\n   " +
                         "    }\n      TH.Description {\n" +
                         "         white-space: nowrap;\n         text-decor" +
                         "ation: none; text-align: left;\n         font-size" +
                         ": medium; font-weight: normal;\n         backgroun" +
                         "d: white; color: black;\n      }\n      TD.Doc {\n" +
                         "         white-space: nowrap;\n         text-decor" +
                         "ation: none; text-align: left;\n         font-size" +
                         ": medium; font-weight: normal;\n         backgroun" +
                         "d: white; color: black;\n      }\n      TD.DocGood" +
                         " {\n         white-space: nowrap;\n         text-d" +
                         "ecoration: none; text-align: left;\n         font-" +
                         "size: medium; font-weight: normal;\n         backg" +
                         "round: #CDFFD4; color: black;\n      }\n      TD.D" +
                         "ocWarn {\n         white-space: nowrap;\n         " +
                         "text-decoration: none; text-align: left;\n        " +
                         " font-size: medium; font-weight: normal;\n        " +
                         " background: #FFFFCC; color: black;\n      }\n    " +
                         "  TD.DocBad {\n         white-space: nowrap;\n    " +
                         "     text-decoration: none; text-align: left;\n   " +
                         "      font-size: medium; font-weight: normal;\n   " +
                         "      background: #FFCCCC; color: black;\n      }" +
                         "\n   </STYLE>\n\n")
            #
            if ( noHost > 0 ):
                # write GSIftp link matrix table:
                noPixel = 2 + 256 + (noHost * (24 + 2)) + 2
                myFile.write(("<TABLE BORDER=\"0\" CELLPADDING=\"0\" CELLSPA" +
                              "CING=\"2\" STYLE=\"width: %dpx; table-layout:" +
                              " fixed;\">\n<TR>\n   <TH CLASS=\"Label\" STYL" +
                              "E=\"border: 4px solid black; text-align: cent" +
                              "er;\">GSIftp:\n<TR HEIGHT=\"128\">\n   <TH CL" +
                              "ASS=\"Label\" STYLE=\"text-align: right;\">De" +
                              "stination:\n") % noPixel)
                for dstTpl in tplList:
                    if dstTpl[1] in exDst:
                        myFile.write(("   <TH ROWSPAN=\"2\" CLASS=\"Destinat" +
                                      "ion\"><DIV STYLE=\"background-color: " +
                                      "#D8D8D8\"><A HREF=\"#DST%s\">%s</A></" +
                                      "DIV>\n") % (dstTpl[1], dstTpl[1]))
                    else:
                        try:
                            status = dstDocs[ dstTpl[1] ]['status']
                        except KeyError:
                            status = "unknown"
                        if ( status == "ok" ):
                            myFile.write(("   <TH ROWSPAN=\"2\" CLASS=\"Dest" +
                                          "ination\"><DIV STYLE=\"background" +
                                          "-color: #CDFFD4\"><A HREF=\"#DST" +
                                          "%s\">%s</A></DIV>\n") % (dstTpl[1],
                                                                    dstTpl[1]))
                        elif ( status == "warning" ):
                            myFile.write(("   <TH ROWSPAN=\"2\" CLASS=\"Dest" +
                                          "ination\"><DIV STYLE=\"background" +
                                          "-color: #FFFFCC\"><A HREF=\"#DST" +
                                          "%s\">%s</A></DIV>\n") % (dstTpl[1],
                                                                    dstTpl[1]))
                        elif ( status == "error" ):
                            myFile.write(("   <TH ROWSPAN=\"2\" CLASS=\"Dest" +
                                          "ination\"><DIV STYLE=\"background" +
                                          "-color: #FFCCCC\"><A HREF=\"#DST" +
                                          "%s\">%s</A></DIV>\n") % (dstTpl[1],
                                                                    dstTpl[1]))
                        else:
                            myFile.write(("   <TH ROWSPAN=\"2\" CLASS=\"Dest" +
                                          "ination\"><DIV><A HREF=\"#DST%s\"" +
                                          ">%s</A></DIV>\n") % (dstTpl[1],
                                                                    dstTpl[1]))
                myFile.write("<TR HEIGHT=\"64\">\n   <TH CLASS=\"Label\" STY" +
                             "LE=\"border-bottom: 4px solid black; text-alig" +
                             "n: left;\">Source:\n")
                for srcTpl in tplList:
                    if srcTpl[1] in exSrc:
                        myFile.write(("<TR>\n      <TH CLASS=\"Source\" STYL" +
                                      "E=\"background-color: #D8D8D8\"><A HR" +
                                      "EF=\"#SRC%s\">%s</A>\n") % (srcTpl[1],
                                                                    srcTpl[1]))
                    else:
                        try:
                            status = srcDocs[ srcTpl[1] ]['status']
                        except KeyError:
                            status = "unknown"
                        if ( status == "ok" ):
                            myFile.write(("<TR>\n      <TH CLASS=\"Source\" " +
                                          "STYLE=\"background-color: #CDFFD4" +
                                          "\"><A HREF=\"#SRC%s\">%s</A>\n") %
                                                        (srcTpl[1], srcTpl[1]))
                        elif ( status == "warning" ):
                            myFile.write(("<TR>\n      <TH CLASS=\"Source\" " +
                                          "STYLE=\"background-color: #FFFFCC" +
                                          "\"><A HREF=\"#SRC%s\">%s</A>\n") %
                                                        (srcTpl[1], srcTpl[1]))
                        elif ( status == "error" ):
                            myFile.write(("<TR>\n      <TH CLASS=\"Source\" " +
                                          "STYLE=\"background-color: #FFCCCC" +
                                          "\"><A HREF=\"#SRC%s\">%s</A>\n") %
                                                        (srcTpl[1], srcTpl[1]))
                        else:
                            myFile.write(("<TR>\n      <TH CLASS=\"Source\">" +
                                          "<A HREF=\"#SRC%s\">%s</A>\n") %
                                                        (srcTpl[1], srcTpl[1]))
                    for dstTpl in tplList:
                        lnkName = srcTpl[1] + "___" + dstTpl[1]
                        try:
                            status = lnkDocs[lnkName]['status']
                        except KeyError:
                            status = "unknown"
                        try:
                            q_strng = "<SPAN>Quality = %.3f</SPAN>" % \
                                                    lnkDocs[lnkName]['quality']
                        except KeyError:
                            q_strng = ""
                        if ( dstTpl[1] == srcTpl[1] ):
                            myFile.write("   <TD CLASS=\"EvalSelf\">\n")
                        elif lnkName not in lnkDocs:
                            myFile.write("   <TD CLASS=\"Eval\">\n")
                        elif ( lnkDocs[lnkName]['status'] == "ok" ):
                            myFile.write(("   <TD CLASS=\"EvalGood\"><A CLAS" +
                                          "S=\"qualityTip\" HREF=\"#%s\">&nb" +
                                          "sp;%s</A>\n") % (lnkName, q_strng))
                        elif ( lnkDocs[lnkName]['status'] == "warning" ):
                            myFile.write(("   <TD CLASS=\"EvalWarn\"><A CLAS" +
                                          "S=\"qualityTip\" HREF=\"#%s\">&nb" +
                                          "sp;%s</A>\n") % (lnkName, q_strng))
                        elif ( lnkDocs[lnkName]['status'] == "error" ):
                            myFile.write(("   <TD CLASS=\"EvalBad\"><A CLASS" +
                                          "=\"qualityTip\" HREF=\"#%s\">&nbs" +
                                          "p;%s</A>\n") % (lnkName, q_strng))
                        else:
                            myFile.write(("   <TD CLASS=\"Eval\"><A CLASS=\"" +
                                          "qualityTip\" HREF=\"#%s\">&nbsp;" +
                                          "%s</A>\n") % (lnkName, q_strng))
                myFile.write("</TABLE>\n<P>\n<HR>\n\n")
            #
            if ( woHost > 0 ):
                # write WebDAV link matrix table:
                noPixel = 2 + 256 + (woHost * (24 + 2)) + 2
                myFile.write(("<TABLE BORDER=\"0\" CELLPADDING=\"0\" CELLSPA" +
                              "CING=\"2\" STYLE=\"width: %dpx; table-layout:" +
                              " fixed;\">\n<TR>\n   <TH CLASS=\"Label\" STYL" +
                              "E=\"border: 4px solid black; text-align: cent" +
                              "er;\">WebDAV:\n<TR HEIGHT=\"128\">\n   <TH CL" +
                              "ASS=\"Label\" STYLE=\"text-align: right;\">De" +
                              "stination:\n") % noPixel)
                for dstTpl in w_tList:
                    if dstTpl[1] in wxDst:
                        myFile.write(("   <TH ROWSPAN=\"2\" CLASS=\"Destinat" +
                                      "ion\"><DIV STYLE=\"background-color: " +
                                      "#D8D8D8\"><A HREF=\"#DST%s\">%s</A></" +
                                      "DIV>\n") % (dstTpl[1], dstTpl[1]))
                    else:
                        try:
                            status = w_dDocs[ dstTpl[1] ]['status']
                        except KeyError:
                            status = "unknown"
                        if ( status == "ok" ):
                            myFile.write(("   <TH ROWSPAN=\"2\" CLASS=\"Dest" +
                                          "ination\"><DIV STYLE=\"background" +
                                          "-color: #CDFFD4\"><A HREF=\"#DST" +
                                          "%s\">%s</A></DIV>\n") % (dstTpl[1],
                                                                    dstTpl[1]))
                        elif ( status == "warning" ):
                            myFile.write(("   <TH ROWSPAN=\"2\" CLASS=\"Dest" +
                                          "ination\"><DIV STYLE=\"background" +
                                          "-color: #FFFFCC\"><A HREF=\"#DST" +
                                          "%s\">%s</A></DIV>\n") % (dstTpl[1],
                                                                    dstTpl[1]))
                        elif ( status == "error" ):
                            myFile.write(("   <TH ROWSPAN=\"2\" CLASS=\"Dest" +
                                          "ination\"><DIV STYLE=\"background" +
                                          "-color: #FFCCCC\"><A HREF=\"#DST" +
                                          "%s\">%s</A></DIV>\n") % (dstTpl[1],
                                                                    dstTpl[1]))
                        else:
                            myFile.write(("   <TH ROWSPAN=\"2\" CLASS=\"Dest" +
                                          "ination\"><DIV><A HREF=\"#DST%s\"" +
                                          ">%s</A></DIV>\n") % (dstTpl[1],
                                                                    dstTpl[1]))
                myFile.write("<TR HEIGHT=\"64\">\n   <TH CLASS=\"Label\" STY" +
                             "LE=\"border-bottom: 4px solid black; text-alig" +
                             "n: left;\">Source:\n")
                for srcTpl in w_tList:
                    if srcTpl[1] in wxSrc:
                        myFile.write(("<TR>\n      <TH CLASS=\"Source\" STYL" +
                                      "E=\"background-color: #D8D8D8\"><A HR" +
                                      "EF=\"#SRC%s\">%s</A>\n") % (srcTpl[1],
                                                                    srcTpl[1]))
                    else:
                        try:
                            status = w_sDocs[ srcTpl[1] ]['status']
                        except KeyError:
                            status = "unknown"
                        if ( status == "ok" ):
                            myFile.write(("<TR>\n      <TH CLASS=\"Source\" " +
                                          "STYLE=\"background-color: #CDFFD4" +
                                          "\"><A HREF=\"#SRC%s\">%s</A>\n") %
                                                        (srcTpl[1], srcTpl[1]))
                        elif ( status == "warning" ):
                            myFile.write(("<TR>\n      <TH CLASS=\"Source\" " +
                                          "STYLE=\"background-color: #FFFFCC" +
                                          "\"><A HREF=\"#SRC%s\">%s</A>\n") %
                                                        (srcTpl[1], srcTpl[1]))
                        elif ( status == "error" ):
                            myFile.write(("<TR>\n      <TH CLASS=\"Source\" " +
                                          "STYLE=\"background-color: #FFCCCC" +
                                          "\"><A HREF=\"#SRC%s\">%s</A>\n") %
                                                        (srcTpl[1], srcTpl[1]))
                        else:
                            myFile.write(("<TR>\n      <TH CLASS=\"Source\">" +
                                          "<A HREF=\"#SRC%s\">%s</A>\n") %
                                                        (srcTpl[1], srcTpl[1]))
                    for dstTpl in w_tList:
                        lnkName = srcTpl[1] + "___" + dstTpl[1]
                        try:
                            status = w_lDocs[lnkName]['status']
                        except KeyError:
                            status = "unknown"
                        try:
                            q_strng = "<SPAN>Quality = %.3f</SPAN>" % \
                                                    w_lDocs[lnkName]['quality']
                        except KeyError:
                            q_strng = ""
                        if ( dstTpl[1] == srcTpl[1] ):
                            myFile.write("   <TD CLASS=\"EvalSelf\">\n")
                        elif lnkName not in w_lDocs:
                            myFile.write("   <TD CLASS=\"Eval\">\n")
                        elif ( w_lDocs[lnkName]['status'] == "ok" ):
                            myFile.write(("   <TD CLASS=\"EvalGood\"><A CLAS" +
                                          "S=\"qualityTip\" HREF=\"#%s\">&nb" +
                                          "sp;%s</A>\n") % (lnkName, q_strng))
                        elif ( w_lDocs[lnkName]['status'] == "warning" ):
                            myFile.write(("   <TD CLASS=\"EvalWarn\"><A CLAS" +
                                          "S=\"qualityTip\" HREF=\"#%s\">&nb" +
                                          "sp;%s</A>\n") % (lnkName, q_strng))
                        elif ( w_lDocs[lnkName]['status'] == "error" ):
                            myFile.write(("   <TD CLASS=\"EvalBad\"><A CLASS" +
                                          "=\"qualityTip\" HREF=\"#%s\">&nbs" +
                                          "p;%s</A>\n") % (lnkName, q_strng))
                        else:
                            myFile.write(("   <TD CLASS=\"Eval\"><A CLASS=\"" +
                                          "qualityTip\" HREF=\"#%s\">&nbsp;" +
                                          "%s</A>\n") % (lnkName, q_strng))
                myFile.write("</TABLE>\n<P>\n<HR>\n\n")
            #
            if ( xoHost > 0 ):
                # write XRootD link matrix table:
                noPixel = 2 + 256 + (xoHost * (24 + 2)) + 2
                myFile.write(("<TABLE BORDER=\"0\" CELLPADDING=\"0\" CELLSPA" +
                              "CING=\"2\" STYLE=\"width: %dpx; table-layout:" +
                              " fixed;\">\n<TR>\n   <TH CLASS=\"Label\" STYL" +
                              "E=\"border: 4px solid black; text-align: cent" +
                              "er;\">XRootD:\n<TR HEIGHT=\"128\">\n   <TH CL" +
                              "ASS=\"Label\" STYLE=\"text-align: right;\">De" +
                              "stination:\n") % noPixel)
                for dstTpl in x_tList:
                    if dstTpl[1] in xxDst:
                        myFile.write(("   <TH ROWSPAN=\"2\" CLASS=\"Destinat" +
                                      "ion\"><DIV STYLE=\"background-color: " +
                                      "#D8D8D8\"><A HREF=\"#DST%s\">%s</A></" +
                                      "DIV>\n") % (dstTpl[1], dstTpl[1]))
                    else:
                        try:
                            status = x_dDocs[ dstTpl[1] ]['status']
                        except KeyError:
                            status = "unknown"
                        if ( status == "ok" ):
                            myFile.write(("   <TH ROWSPAN=\"2\" CLASS=\"Dest" +
                                          "ination\"><DIV STYLE=\"background" +
                                          "-color: #CDFFD4\"><A HREF=\"#DST" +
                                          "%s\">%s</A></DIV>\n") % (dstTpl[1],
                                                                    dstTpl[1]))
                        elif ( status == "warning" ):
                            myFile.write(("   <TH ROWSPAN=\"2\" CLASS=\"Dest" +
                                          "ination\"><DIV STYLE=\"background" +
                                          "-color: #FFFFCC\"><A HREF=\"#DST" +
                                          "%s\">%s</A></DIV>\n") % (dstTpl[1],
                                                                    dstTpl[1]))
                        elif ( status == "error" ):
                            myFile.write(("   <TH ROWSPAN=\"2\" CLASS=\"Dest" +
                                          "ination\"><DIV STYLE=\"background" +
                                          "-color: #FFCCCC\"><A HREF=\"#DST" +
                                          "%s\">%s</A></DIV>\n") % (dstTpl[1],
                                                                    dstTpl[1]))
                        else:
                            myFile.write(("   <TH ROWSPAN=\"2\" CLASS=\"Dest" +
                                          "ination\"><DIV><A HREF=\"#DST%s\"" +
                                          ">%s</A></DIV>\n") % (dstTpl[1],
                                                                    dstTpl[1]))
                myFile.write("<TR HEIGHT=\"64\">\n   <TH CLASS=\"Label\" STY" +
                             "LE=\"border-bottom: 4px solid black; text-alig" +
                             "n: left;\">Source:\n")
                for srcTpl in x_tList:
                    if srcTpl[1] in xxSrc:
                        myFile.write(("<TR>\n      <TH CLASS=\"Source\" STYL" +
                                      "E=\"background-color: #D8D8D8\"><A HR" +
                                      "EF=\"#SRC%s\">%s</A>\n") % (srcTpl[1],
                                                                    srcTpl[1]))
                    else:
                        try:
                            status = x_sDocs[ srcTpl[1] ]['status']
                        except KeyError:
                            status = "unknown"
                        if ( status == "ok" ):
                            myFile.write(("<TR>\n      <TH CLASS=\"Source\" " +
                                          "STYLE=\"background-color: #CDFFD4" +
                                          "\"><A HREF=\"#SRC%s\">%s</A>\n") %
                                                        (srcTpl[1], srcTpl[1]))
                        elif ( status == "warning" ):
                            myFile.write(("<TR>\n      <TH CLASS=\"Source\" " +
                                          "STYLE=\"background-color: #FFFFCC" +
                                          "\"><A HREF=\"#SRC%s\">%s</A>\n") %
                                                        (srcTpl[1], srcTpl[1]))
                        elif ( status == "error" ):
                            myFile.write(("<TR>\n      <TH CLASS=\"Source\" " +
                                          "STYLE=\"background-color: #FFCCCC" +
                                          "\"><A HREF=\"#SRC%s\">%s</A>\n") %
                                                        (srcTpl[1], srcTpl[1]))
                        else:
                            myFile.write(("<TR>\n      <TH CLASS=\"Source\">" +
                                          "<A HREF=\"#SRC%s\">%s</A>\n") %
                                                        (srcTpl[1], srcTpl[1]))
                    for dstTpl in x_tList:
                        lnkName = srcTpl[1] + "___" + dstTpl[1]
                        try:
                            status = x_lDocs[lnkName]['status']
                        except KeyError:
                            status = "unknown"
                        try:
                            q_strng = "<SPAN>Quality = %.3f</SPAN>" % \
                                                    x_lDocs[lnkName]['quality']
                        except KeyError:
                            q_strng = ""
                        if ( dstTpl[1] == srcTpl[1] ):
                            myFile.write("   <TD CLASS=\"EvalSelf\">\n")
                        elif lnkName not in x_lDocs:
                            myFile.write("   <TD CLASS=\"Eval\">\n")
                        elif ( x_lDocs[lnkName]['status'] == "ok" ):
                            myFile.write(("   <TD CLASS=\"EvalGood\"><A CLAS" +
                                          "S=\"qualityTip\" HREF=\"#%s\">&nb" +
                                          "sp;%s</A>\n") % (lnkName, q_strng))
                        elif ( x_lDocs[lnkName]['status'] == "warning" ):
                            myFile.write(("   <TD CLASS=\"EvalWarn\"><A CLAS" +
                                          "S=\"qualityTip\" HREF=\"#%s\">&nb" +
                                          "sp;%s</A>\n") % (lnkName, q_strng))
                        elif ( x_lDocs[lnkName]['status'] == "error" ):
                            myFile.write(("   <TD CLASS=\"EvalBad\"><A CLASS" +
                                          "=\"qualityTip\" HREF=\"#%s\">&nbs" +
                                          "p;%s</A>\n") % (lnkName, q_strng))
                        else:
                            myFile.write(("   <TD CLASS=\"Eval\"><A CLASS=\"" +
                                          "qualityTip\" HREF=\"#%s\">&nbsp;" +
                                          "%s</A>\n") % (lnkName, q_strng))
                myFile.write("</TABLE>\n<P>\n<HR>\n\n")
            #
            #
            # write site evaluation tables:
            for site in sorted( siteDocs.keys() ):
                try:
                    status = siteDocs[site]['status']
                except KeyError:
                    status = "unknown"
                if ( status == "ok" ):
                    clss = "DocGood"
                elif ( status == "warning" ):
                    clss = "DocWarn"
                elif ( status == "error" ):
                    clss = "DocBad"
                else:
                    clss = "Doc"
                try:
                    q_strng = "%.3f" % siteDocs[site]['quality']
                except KeyError:
                    q_strng = "<I>not set</I>"
                try:
                    d_strng = siteDocs[site]['detail'].replace("\n","<BR>")
                except KeyError:
                    d_strng = "\"\""
                myFile.write(("<P>\n&nbsp;\n<P>\n<TABLE CELLSPACING=\"0\" CE" +
                              "LLPADDING=\"2\" BORDER=\"1\">\n<TR>\n   <TH C" +
                              "OLSPAN=\"2\" CLASS=\"LinkHeader\"><A NAME=\"" +
                              "%s\">%s</A> :\n<TR>\n   <TH CLASS=\"Descripti" +
                              "on\">Site/Host/Link name\n   <TD CLASS=\"%s\"" +
                              ">%s\n<TR>\n   <TH CLASS=\"Description\">Evalu" +
                              "ation type\n   <TD CLASS=\"%s\">%s\n<TR>\n   " +
                              "<TH CLASS=\"Description\">Quality\n   <TD CLA" +
                              "SS=\"%s\">%s\n<TR>\n   <TH CLASS=\"Descriptio" +
                              "n\">Detail\n   <TD CLASS=\"%s\">%s\n<TR>\n   " +
                              "<TH CLASS=\"Description\">Status\n   <TD CLAS" +
                              "S=\"%s\" STYLE=\"font-weight: bold;\">%s\n<TR" +
                              ">\n   <TH CLASS=\"Description\">Version numbe" +
                              "r<br>(= insert time)\n   <TD CLASS=\"%s\">%d." +
                              "%3.3d (%s UTC)\n<TR>\n   <TH CLASS=\"Descript" +
                              "ion\">Document id\n   <TD CLASS=\"%s\">%s\n") %
                             (site, site, clss, siteDocs[site]['name'],
                              clss, siteDocs[site]['type'],
                              clss, q_strng,
                              clss, d_strng,
                              clss, status,
                              clss, int(siteDocs[site]['***VERSION***']/1000),
                                    siteDocs[site]['***VERSION***']%1000,
                                    time.strftime("%Y-%m-%d %H:%M:%S",
                       time.gmtime(int(siteDocs[site]['***VERSION***']/1000))),
                              clss, siteDocs[site]['***DOCID***']))
                sTIS = 3600 * int( (tbin * cfg['period']) / 3600 )
                eTIS = 3600 * int( (sTIS + cfg['period'] + 3599) / 3600 )
                myFile.write(("      <TR>\n         <TD COLSPAN=\"2\"><A HRE" +
                              "F=\"%s&var-include=%s\"><I>Link to transfers " +
                              "in Grafana FTS dashboard</I></A>\n") %
                             ((LFTCH_FTSDASHB % (sTIS, eTIS)),
                                                       siteDocs[site]['name']))
                myFile.write("</TABLE>\n\n")
            myFile.write("<P>\n<HR>\n\n")
            #
            # write RSE evaluation tables:
            for rse in sorted( rseDocs.keys() ):
                try:
                    status = rseDocs[rse]['status']
                except KeyError:
                    status = "unknown"
                if ( status == "ok" ):
                    clss = "DocGood"
                elif ( status == "warning" ):
                    clss = "DocWarn"
                elif ( status == "error" ):
                    clss = "DocBad"
                else:
                    clss = "Doc"
                try:
                    q_strng = "%.3f" % rseDocs[rse]['quality']
                except KeyError:
                    q_strng = "<I>not set</I>"
                try:
                    d_strng = rseDocs[rse]['detail'].replace("\n","<BR>")
                except KeyError:
                    d_strng = "\"\""
                myFile.write(("<P>\n&nbsp;\n<P>\n<TABLE CELLSPACING=\"0\" CE" +
                              "LLPADDING=\"2\" BORDER=\"1\">\n<TR>\n   <TH C" +
                              "OLSPAN=\"2\" CLASS=\"LinkHeader\"><A NAME=\"" +
                              "%s\">%s</A> :\n<TR>\n   <TH CLASS=\"Descripti" +
                              "on\">Site/Host/Link name\n   <TD CLASS=\"%s\"" +
                              ">%s\n<TR>\n   <TH CLASS=\"Description\">Evalu" +
                              "ation type\n   <TD CLASS=\"%s\">%s\n<TR>\n   " +
                              "<TH CLASS=\"Description\">Quality\n   <TD CLA" +
                              "SS=\"%s\">%s\n<TR>\n   <TH CLASS=\"Descriptio" +
                              "n\">Detail\n   <TD CLASS=\"%s\">%s\n<TR>\n   " +
                              "<TH CLASS=\"Description\">Status\n   <TD CLAS" +
                              "S=\"%s\" STYLE=\"font-weight: bold;\">%s\n<TR" +
                             ">\n   <TH CLASS=\"Description\">Version numbe" +
                              "r<br>(= insert time)\n   <TD CLASS=\"%s\">%d." +
                              "%3.3d (%s UTC)\n<TR>\n   <TH CLASS=\"Descript" +
                              "ion\">Document id\n   <TD CLASS=\"%s\">%s\n") %
                             (rse, rse, clss, rseDocs[rse]['name'],
                              clss, rseDocs[rse]['type'],
                              clss, q_strng,
                              clss, d_strng,
                              clss, status,
                              clss, int(rseDocs[rse]['***VERSION***']/1000),
                                    rseDocs[rse]['***VERSION***']%1000,
                                    time.strftime("%Y-%m-%d %H:%M:%S",
                         time.gmtime(int(rseDocs[rse]['***VERSION***']/1000))),
                              clss, rseDocs[rse]['***DOCID***']))
                myFile.write("</TABLE>\n\n")
            myFile.write("<P>\n<HR>\n\n")
            #
            # write source host evaluation tables:
            for source in sorted( srcDocs.keys() ):
                try:
                    status = srcDocs[source]['status']
                except KeyError:
                    status = "unknown"
                if ( status == "ok" ):
                    clss = "DocGood"
                elif ( status == "warning" ):
                    clss = "DocWarn"
                elif ( status == "error" ):
                    clss = "DocBad"
                else:
                    clss = "Doc"
                try:
                    q_strng = "%.3f" % srcDocs[source]['quality']
                except KeyError:
                    q_strng = "<I>not set</I>"
                try:
                    d_strng = srcDocs[source]['detail'].replace("\n","<BR>")
                except KeyError:
                    d_strng = "\"\""
                myFile.write(("<P>\n&nbsp;\n<P>\n<TABLE CELLSPACING=\"0\" CE" +
                              "LLPADDING=\"2\" BORDER=\"1\">\n<TR>\n   <TH C" +
                              "OLSPAN=\"2\" CLASS=\"LinkHeader\"><A NAME=\"" +
                              "SRC%s\">%s &#10140;</A> :\n<TR>\n   <TH CLASS" +
                              "=\"Description\">Site/Host/Link name\n   <TD " +
                              "CLASS=\"%s\">%s\n<TR>\n   <TH CLASS=\"Descrip" +
                              "tion\">Evaluation type\n   <TD CLASS=\"%s\">" +
                              "%s\n<TR>\n   <TH CLASS=\"Description\">Qualit" +
                              "y\n   <TD CLASS=\"%s\">%s\n<TR>\n   <TH CLASS" +
                              "=\"Description\">Detail\n   <TD CLASS=\"%s\">" +
                              "%s\n<TR>\n   <TH CLASS=\"Description\">Status" +
                              "\n   <TD CLASS=\"%s\" STYLE=\"font-weight: bo" +
                              "ld;\">%s\n<TR>\n   <TH CLASS=\"Description\">" +
                              "Version number<br>(= insert time)\n   <TD CLA" +
                              "SS=\"%s\">%d.%3.3d (%s UTC)\n<TR>\n   <TH CLA" +
                              "SS=\"Description\">Document id\n   <TD CLASS=" +
                              "\"%s\">%s\n") %
                             (source, source, clss, srcDocs[source]['name'],
                              clss, srcDocs[source]['type'],
                              clss, q_strng,
                              clss, d_strng,
                              clss, status,
                              clss, int(srcDocs[source]['***VERSION***']/1000),
                                    srcDocs[source]['***VERSION***']%1000,
                                    time.strftime("%Y-%m-%d %H:%M:%S",
                      time.gmtime(int(srcDocs[source]['***VERSION***']/1000))),
                              clss, srcDocs[source]['***DOCID***']))
                sTIS = 3600 * int( (tbin * cfg['period']) / 3600 )
                eTIS = 3600 * int( (sTIS + cfg['period'] + 3599) / 3600 )
                myFile.write(("      <TR>\n         <TD COLSPAN=\"2\"><A HRE" +
                              "F=\"%s&var-filters=data.src_hostname|=|%s\"><" +
                              "I>Link to transfers in Grafana FTS dashboard<" +
                              "/I></A>\n") % ((LFTCH_FTSDASHB % (sTIS, eTIS)),
                                                      srcDocs[source]['name']))
                myFile.write("</TABLE>\n\n")
            myFile.write("<P>\n<HR>\n\n")
            #
            # write destination host evaluation tables:
            for dest in sorted( dstDocs.keys() ):
                try:
                    status = dstDocs[dest]['status']
                except KeyError:
                    status = "unknown"
                if ( status == "ok" ):
                    clss = "DocGood"
                elif ( status == "warning" ):
                    clss = "DocWarn"
                elif ( status == "error" ):
                    clss = "DocBad"
                else:
                    clss = "Doc"
                try:
                    q_strng = "%.3f" % dstDocs[dest]['quality']
                except KeyError:
                    q_strng = "<I>not set</I>"
                try:
                    d_strng = dstDocs[dest]['detail'].replace("\n","<BR>")
                except KeyError:
                    d_strng = "\"\""
                myFile.write(("<P>\n&nbsp;\n<P>\n<TABLE CELLSPACING=\"0\" CE" +
                              "LLPADDING=\"2\" BORDER=\"1\">\n<TR>\n   <TH C" +
                              "OLSPAN=\"2\" CLASS=\"LinkHeader\"><A NAME=\"" +
                              "DST%s\">&#10140; %s</A> :\n<TR>\n   <TH CLASS" +
                              "=\"Description\">Site/Host/Link name\n   <TD " +
                              "CLASS=\"%s\">%s\n<TR>\n   <TH CLASS=\"Descrip" +
                              "tion\">Evaluation type\n   <TD CLASS=\"%s\">" +
                              "%s\n<TR>\n   <TH CLASS=\"Description\">Qualit" +
                              "y\n   <TD CLASS=\"%s\">%s\n<TR>\n   <TH CLASS" +
                              "=\"Description\">Detail\n   <TD CLASS=\"%s\">" +
                              "%s\n<TR>\n   <TH CLASS=\"Description\">Status" +
                              "\n   <TD CLASS=\"%s\" STYLE=\"font-weight: bo" +
                              "ld;\">%s\n<TR>\n   <TH CLASS=\"Description\">" +
                              "Version number<br>(= insert time)\n   <TD CLA" +
                              "SS=\"%s\">%d.%3.3d (%s UTC)\n<TR>\n   <TH CLA" +
                              "SS=\"Description\">Document id\n   <TD CLASS=" +
                              "\"%s\">%s\n") %
                             (dest, dest, clss, dstDocs[dest]['name'],
                              clss, dstDocs[dest]['type'],
                              clss, q_strng,
                              clss, d_strng,
                              clss, status,
                              clss, int(dstDocs[dest]['***VERSION***']/1000),
                                    dstDocs[dest]['***VERSION***']%1000,
                                    time.strftime("%Y-%m-%d %H:%M:%S",
                        time.gmtime(int(dstDocs[dest]['***VERSION***']/1000))),
                              clss, dstDocs[dest]['***DOCID***']))
                sTIS = 3600 * int( (tbin * cfg['period']) / 3600 )
                eTIS = 3600 * int( (sTIS + cfg['period'] + 3599) / 3600 )
                myFile.write(("      <TR>\n         <TD COLSPAN=\"2\"><A HRE" +
                              "F=\"%s&var-filters=data.dst_hostname|=|%s\"><" +
                              "I>Link to transfers in Grafana FTS dashboard<" +
                              "/I></A>\n") % ((LFTCH_FTSDASHB % (sTIS, eTIS)),
                                                        dstDocs[dest]['name']))
                myFile.write("</TABLE>\n\n")
            myFile.write("<P>\n<HR>\n\n")
            #
            # write WebDAV source host evaluation tables:
            for source in sorted( w_sDocs.keys() ):
                try:
                    status = w_sDocs[source]['status']
                except KeyError:
                    status = "unknown"
                if ( status == "ok" ):
                    clss = "DocGood"
                elif ( status == "warning" ):
                    clss = "DocWarn"
                elif ( status == "error" ):
                    clss = "DocBad"
                else:
                    clss = "Doc"
                try:
                    q_strng = "%.3f" % w_sDocs[source]['quality']
                except KeyError:
                    q_strng = "<I>not set</I>"
                try:
                    d_strng = w_sDocs[source]['detail'].replace("\n","<BR>")
                except KeyError:
                    d_strng = "\"\""
                myFile.write(("<P>\n&nbsp;\n<P>\n<TABLE CELLSPACING=\"0\" CE" +
                              "LLPADDING=\"2\" BORDER=\"1\">\n<TR>\n   <TH C" +
                              "OLSPAN=\"2\" CLASS=\"LinkHeader\"><A NAME=\"" +
                              "SRC%s\">%s &#10140;</A> :\n<TR>\n   <TH CLASS" +
                              "=\"Description\">Site/Host/Link name\n   <TD " +
                              "CLASS=\"%s\">%s\n<TR>\n   <TH CLASS=\"Descrip" +
                              "tion\">Evaluation type\n   <TD CLASS=\"%s\">" +
                              "%s\n<TR>\n   <TH CLASS=\"Description\">Qualit" +
                              "y\n   <TD CLASS=\"%s\">%s\n<TR>\n   <TH CLASS" +
                              "=\"Description\">Detail\n   <TD CLASS=\"%s\">" +
                              "%s\n<TR>\n   <TH CLASS=\"Description\">Status" +
                              "\n   <TD CLASS=\"%s\" STYLE=\"font-weight: bo" +
                              "ld;\">%s\n<TR>\n   <TH CLASS=\"Description\">" +
                              "Version number<br>(= insert time)\n   <TD CLA" +
                              "SS=\"%s\">%d.%3.3d (%s UTC)\n<TR>\n   <TH CLA" +
                              "SS=\"Description\">Document id\n   <TD CLASS=" +
                              "\"%s\">%s\n") %
                             (source, source, clss, w_sDocs[source]['name'],
                              clss, w_sDocs[source]['type'],
                              clss, q_strng,
                              clss, d_strng,
                              clss, status,
                              clss, int(w_sDocs[source]['***VERSION***']/1000),
                                    w_sDocs[source]['***VERSION***']%1000,
                                    time.strftime("%Y-%m-%d %H:%M:%S",
                      time.gmtime(int(w_sDocs[source]['***VERSION***']/1000))),
                              clss, w_sDocs[source]['***DOCID***']))
                sTIS = 3600 * int( (tbin * cfg['period']) / 3600 )
                eTIS = 3600 * int( (sTIS + cfg['period'] + 3599) / 3600 )
                myFile.write(("<TR>\n   <TD COLSPAN=" + "\"2\"><A HREF=\"%s&" +
                              "var-filters=data.src_hostname|=|%s\"><I>Link " +
                              "to transfers in Grafana FTS dashboard</I></A>" +
                              "\n") % ((LGET_FTSDASHB % (sTIS, eTIS)),
                                                      w_sDocs[source]['name']))
                myFile.write("</TABLE>\n\n")
            myFile.write("<P>\n<HR>\n\n")
            #
            # write WebDAV destination host evaluation tables:
            for dest in sorted( w_dDocs.keys() ):
                try:
                    status = w_dDocs[dest]['status']
                except KeyError:
                    status = "unknown"
                if ( status == "ok" ):
                    clss = "DocGood"
                elif ( status == "warning" ):
                    clss = "DocWarn"
                elif ( status == "error" ):
                    clss = "DocBad"
                else:
                    clss = "Doc"
                try:
                    q_strng = "%.3f" % w_dDocs[dest]['quality']
                except KeyError:
                    q_strng = "<I>not set</I>"
                try:
                    d_strng = w_dDocs[dest]['detail'].replace("\n","<BR>")
                except KeyError:
                    d_strng = "\"\""
                myFile.write(("<P>\n&nbsp;\n<P>\n<TABLE CELLSPACING=\"0\" CE" +
                              "LLPADDING=\"2\" BORDER=\"1\">\n<TR>\n   <TH C" +
                              "OLSPAN=\"2\" CLASS=\"LinkHeader\"><A NAME=\"" +
                              "DST%s\">&#10140; %s</A> :\n<TR>\n   <TH CLASS" +
                              "=\"Description\">Site/Host/Link name\n   <TD " +
                              "CLASS=\"%s\">%s\n<TR>\n   <TH CLASS=\"Descrip" +
                              "tion\">Evaluation type\n   <TD CLASS=\"%s\">" +
                              "%s\n<TR>\n   <TH CLASS=\"Description\">Qualit" +
                              "y\n   <TD CLASS=\"%s\">%s\n<TR>\n   <TH CLASS" +
                              "=\"Description\">Detail\n   <TD CLASS=\"%s\">" +
                              "%s\n<TR>\n   <TH CLASS=\"Description\">Status" +
                              "\n   <TD CLASS=\"%s\" STYLE=\"font-weight: bo" +
                              "ld;\">%s\n<TR>\n   <TH CLASS=\"Description\">" +
                              "Version number<br>(= insert time)\n   <TD CLA" +
                              "SS=\"%s\">%d.%3.3d (%s UTC)\n<TR>\n   <TH CLA" +
                              "SS=\"Description\">Document id\n   <TD CLASS=" +
                              "\"%s\">%s\n") %
                             (dest, dest, clss, w_dDocs[dest]['name'],
                              clss, w_dDocs[dest]['type'],
                              clss, q_strng,
                              clss, d_strng,
                              clss, status,
                              clss, int(w_dDocs[dest]['***VERSION***']/1000),
                                    w_dDocs[dest]['***VERSION***']%1000,
                                    time.strftime("%Y-%m-%d %H:%M:%S",
                        time.gmtime(int(w_dDocs[dest]['***VERSION***']/1000))),
                              clss, w_dDocs[dest]['***DOCID***']))
                sTIS = 3600 * int( (tbin * cfg['period']) / 3600 )
                eTIS = 3600 * int( (sTIS + cfg['period'] + 3599) / 3600 )
                myFile.write(("<TR>\n   <TD COLSPAN=" + "\"2\"><A HREF=\"%s&" +
                              "var-filters=data.dst_hostname|=|%s\"><I>Link " +
                              "to transfers in Grafana FTS dashboard</I></A>" +
                              "\n") % ((LGET_FTSDASHB % (sTIS, eTIS)),
                                                        w_dDocs[dest]['name']))
                myFile.write("</TABLE>\n\n")
            myFile.write("<P>\n<HR>\n\n")
            #
            # write XRootD source host evaluation tables:
            for source in sorted( x_sDocs.keys() ):
                try:
                    status = x_sDocs[source]['status']
                except KeyError:
                    status = "unknown"
                if ( status == "ok" ):
                    clss = "DocGood"
                elif ( status == "warning" ):
                    clss = "DocWarn"
                elif ( status == "error" ):
                    clss = "DocBad"
                else:
                    clss = "Doc"
                try:
                    q_strng = "%.3f" % x_sDocs[source]['quality']
                except KeyError:
                    q_strng = "<I>not set</I>"
                try:
                    d_strng = x_sDocs[source]['detail'].replace("\n","<BR>")
                except KeyError:
                    d_strng = "\"\""
                myFile.write(("<P>\n&nbsp;\n<P>\n<TABLE CELLSPACING=\"0\" CE" +
                              "LLPADDING=\"2\" BORDER=\"1\">\n<TR>\n   <TH C" +
                              "OLSPAN=\"2\" CLASS=\"LinkHeader\"><A NAME=\"" +
                              "SRC%s\">%s &#10140;</A> :\n<TR>\n   <TH CLASS" +
                              "=\"Description\">Site/Host/Link name\n   <TD " +
                              "CLASS=\"%s\">%s\n<TR>\n   <TH CLASS=\"Descrip" +
                              "tion\">Evaluation type\n   <TD CLASS=\"%s\">" +
                              "%s\n<TR>\n   <TH CLASS=\"Description\">Qualit" +
                              "y\n   <TD CLASS=\"%s\">%s\n<TR>\n   <TH CLASS" +
                              "=\"Description\">Detail\n   <TD CLASS=\"%s\">" +
                              "%s\n<TR>\n   <TH CLASS=\"Description\">Status" +
                              "\n   <TD CLASS=\"%s\" STYLE=\"font-weight: bo" +
                              "ld;\">%s\n<TR>\n   <TH CLASS=\"Description\">" +
                              "Version number<br>(= insert time)\n   <TD CLA" +
                              "SS=\"%s\">%d.%3.3d (%s UTC)\n<TR>\n   <TH CLA" +
                              "SS=\"Description\">Document id\n   <TD CLASS=" +
                              "\"%s\">%s\n") %
                             (source, source, clss, x_sDocs[source]['name'],
                              clss, x_sDocs[source]['type'],
                              clss, q_strng,
                              clss, d_strng,
                              clss, status,
                              clss, int(x_sDocs[source]['***VERSION***']/1000),
                                    x_sDocs[source]['***VERSION***']%1000,
                                    time.strftime("%Y-%m-%d %H:%M:%S",
                      time.gmtime(int(x_sDocs[source]['***VERSION***']/1000))),
                              clss, x_sDocs[source]['***DOCID***']))
                sTIS = 3600 * int( (tbin * cfg['period']) / 3600 )
                eTIS = 3600 * int( (sTIS + cfg['period'] + 3599) / 3600 )
                myFile.write(("<TR>\n   <TD COLSPAN=" + "\"2\"><A HREF=\"%s&" +
                              "var-filters=data.src_hostname|=|%s\"><I>Link " +
                              "to transfers in Grafana FTS dashboard</I></A>" +
                              "\n") % ((LGET_FTSDASHB % (sTIS, eTIS)),
                                                      x_sDocs[source]['name']))
                myFile.write("</TABLE>\n\n")
            myFile.write("<P>\n<HR>\n\n")
            #
            # write XRootD destination host evaluation tables:
            for dest in sorted( x_dDocs.keys() ):
                try:
                    status = x_dDocs[dest]['status']
                except KeyError:
                    status = "unknown"
                if ( status == "ok" ):
                    clss = "DocGood"
                elif ( status == "warning" ):
                    clss = "DocWarn"
                elif ( status == "error" ):
                    clss = "DocBad"
                else:
                    clss = "Doc"
                try:
                    q_strng = "%.3f" % x_dDocs[dest]['quality']
                except KeyError:
                    q_strng = "<I>not set</I>"
                try:
                    d_strng = x_dDocs[dest]['detail'].replace("\n","<BR>")
                except KeyError:
                    d_strng = "\"\""
                myFile.write(("<P>\n&nbsp;\n<P>\n<TABLE CELLSPACING=\"0\" CE" +
                              "LLPADDING=\"2\" BORDER=\"1\">\n<TR>\n   <TH C" +
                              "OLSPAN=\"2\" CLASS=\"LinkHeader\"><A NAME=\"" +
                              "DST%s\">&#10140; %s</A> :\n<TR>\n   <TH CLASS" +
                              "=\"Description\">Site/Host/Link name\n   <TD " +
                              "CLASS=\"%s\">%s\n<TR>\n   <TH CLASS=\"Descrip" +
                              "tion\">Evaluation type\n   <TD CLASS=\"%s\">" +
                              "%s\n<TR>\n   <TH CLASS=\"Description\">Qualit" +
                              "y\n   <TD CLASS=\"%s\">%s\n<TR>\n   <TH CLASS" +
                              "=\"Description\">Detail\n   <TD CLASS=\"%s\">" +
                              "%s\n<TR>\n   <TH CLASS=\"Description\">Status" +
                              "\n   <TD CLASS=\"%s\" STYLE=\"font-weight: bo" +
                              "ld;\">%s\n<TR>\n   <TH CLASS=\"Description\">" +
                              "Version number<br>(= insert time)\n   <TD CLA" +
                              "SS=\"%s\">%d.%3.3d (%s UTC)\n<TR>\n   <TH CLA" +
                              "SS=\"Description\">Document id\n   <TD CLASS=" +
                              "\"%s\">%s\n") %
                             (dest, dest, clss, x_dDocs[dest]['name'],
                              clss, x_dDocs[dest]['type'],
                              clss, q_strng,
                              clss, d_strng,
                              clss, status,
                              clss, int(x_dDocs[dest]['***VERSION***']/1000),
                                    x_dDocs[dest]['***VERSION***']%1000,
                                    time.strftime("%Y-%m-%d %H:%M:%S",
                        time.gmtime(int(x_dDocs[dest]['***VERSION***']/1000))),
                              clss, x_dDocs[dest]['***DOCID***']))
                sTIS = 3600 * int( (tbin * cfg['period']) / 3600 )
                eTIS = 3600 * int( (sTIS + cfg['period'] + 3599) / 3600 )
                myFile.write(("<TR>\n   <TD COLSPAN=" + "\"2\"><A HREF=\"%s&" +
                              "var-filters=data.dst_hostname|=|%s\"><I>Link " +
                              "to transfers in Grafana FTS dashboard</I></A>" +
                              "\n") % ((LGET_FTSDASHB % (sTIS, eTIS)),
                                                        x_dDocs[dest]['name']))
                myFile.write("</TABLE>\n\n")
            myFile.write("<P>\n<HR>\n\n")
            #
            # write link evaluation tables:
            for link in sorted( lnkDocs.keys() ):
                source = link.split("___")[0]
                dest = link.split("___")[-1]
                try:
                    status = lnkDocs[link]['status']
                except KeyError:
                    status = "unknown"
                if ( status == "ok" ):
                    clss = "DocGood"
                elif ( status == "warning" ):
                    clss = "DocWarn"
                elif ( status == "error" ):
                    clss = "DocBad"
                else:
                    clss = "Doc"
                try:
                    q_strng = "%.3f" % lnkDocs[link]['quality']
                except KeyError:
                    q_strng = "<I>not set</I>"
                try:
                    d_strng = lftch_url4fts( lnkDocs[link]['detail'] )
                except KeyError:
                    d_strng = "\"\""
                myFile.write(("<P>\n&nbsp;\n<P>\n<TABLE CELLSPACING=\"0\" CE" +
                              "LLPADDING=\"2\" BORDER=\"1\">\n<TR>\n   <TH C" +
                              "OLSPAN=\"2\" CLASS=\"LinkHeader\"><A NAME=\"" +
                              "%s\">%s &#10140; %s</A> :\n<TR>\n   <TH CLASS" +
                              "=\"Description\">Site/Host/Link name\n   <TD " +
                              "CLASS=\"%s\">%s\n<TR>\n   <TH CLASS=\"Descrip" +
                              "tion\">Evaluation type\n   <TD CLASS=\"%s\">" +
                              "%s\n<TR>\n   <TH CLASS=\"Description\">Qualit" +
                              "y\n   <TD CLASS=\"%s\">%s\n<TR>\n   <TH CLASS" +
                              "=\"Description\">Detail\n   <TD CLASS=\"%s\">" +
                              "%s\n<TR>\n   <TH CLASS=\"Description\">Status" +
                              "\n   <TD CLASS=\"%s\" STYLE=\"font-weight: bo" +
                              "ld;\">%s\n<TR>\n   <TH CLASS=\"Description\">" +
                              "Version number<br>(= insert time)\n   <TD CLA" +
                              "SS=\"%s\">%d.%3.3d (%s UTC)\n<TR>\n   <TH CLA" +
                              "SS=\"Description\">Document id\n   <TD CLASS=" +
                              "\"%s\">%s\n</TABLE>\n\n") %
                             (link, source, dest, clss, lnkDocs[link]['name'],
                              clss, lnkDocs[link]['type'],
                              clss, q_strng,
                              clss, d_strng,
                              clss, status,
                              clss, int(lnkDocs[link]['***VERSION***']/1000),
                                    lnkDocs[link]['***VERSION***']%1000,
                                    time.strftime("%Y-%m-%d %H:%M:%S",
                        time.gmtime(int(lnkDocs[link]['***VERSION***']/1000))),
                              clss, lnkDocs[link]['***DOCID***']))
            myFile.write("<P>\n&nbsp;\n<P>\n")
            #
            # write WebDAV link evaluation tables:
            for link in sorted( w_lDocs.keys() ):
                source = link.split("___")[0]
                dest = link.split("___")[-1]
                try:
                    status = w_lDocs[link]['status']
                except KeyError:
                    status = "unknown"
                if ( status == "ok" ):
                    clss = "DocGood"
                elif ( status == "warning" ):
                    clss = "DocWarn"
                elif ( status == "error" ):
                    clss = "DocBad"
                else:
                    clss = "Doc"
                try:
                    q_strng = "%.3f" % w_lDocs[link]['quality']
                except KeyError:
                    q_strng = "<I>not set</I>"
                try:
                    d_strng = lget_url4fts( w_lDocs[link]['detail'] )
                except KeyError:
                    d_strng = "\"\""
                myFile.write(("<P>\n&nbsp;\n<P>\n<TABLE CELLSPACING=\"0\" CE" +
                              "LLPADDING=\"2\" BORDER=\"1\">\n<TR>\n   <TH C" +
                              "OLSPAN=\"2\" CLASS=\"LinkHeader\"><A NAME=\"" +
                              "%s\">%s &#10140; %s</A> :\n<TR>\n   <TH CLASS" +
                              "=\"Description\">Site/Host/Link name\n   <TD " +
                              "CLASS=\"%s\">%s\n<TR>\n   <TH CLASS=\"Descrip" +
                              "tion\">Evaluation type\n   <TD CLASS=\"%s\">" +
                              "%s\n<TR>\n   <TH CLASS=\"Description\">Qualit" +
                              "y\n   <TD CLASS=\"%s\">%s\n<TR>\n   <TH CLASS" +
                              "=\"Description\">Detail\n   <TD CLASS=\"%s\">" +
                              "%s\n<TR>\n   <TH CLASS=\"Description\">Status" +
                              "\n   <TD CLASS=\"%s\" STYLE=\"font-weight: bo" +
                              "ld;\">%s\n<TR>\n   <TH CLASS=\"Description\">" +
                              "Version number<br>(= insert time)\n   <TD CLA" +
                              "SS=\"%s\">%d.%3.3d (%s UTC)\n<TR>\n   <TH CLA" +
                              "SS=\"Description\">Document id\n   <TD CLASS=" +
                              "\"%s\">%s\n</TABLE>\n\n") %
                             (link, source, dest, clss, w_lDocs[link]['name'],
                              clss, w_lDocs[link]['type'],
                              clss, q_strng,
                              clss, d_strng,
                              clss, status,
                              clss, int(w_lDocs[link]['***VERSION***']/1000),
                                    w_lDocs[link]['***VERSION***']%1000,
                                    time.strftime("%Y-%m-%d %H:%M:%S",
                        time.gmtime(int(w_lDocs[link]['***VERSION***']/1000))),
                              clss, w_lDocs[link]['***DOCID***']))
            myFile.write("<P>\n&nbsp;\n<P>\n")
            #
            # write XRootD link evaluation tables:
            for link in sorted( x_lDocs.keys() ):
                source = link.split("___")[0]
                dest = link.split("___")[-1]
                try:
                    status = x_lDocs[link]['status']
                except KeyError:
                    status = "unknown"
                if ( status == "ok" ):
                    clss = "DocGood"
                elif ( status == "warning" ):
                    clss = "DocWarn"
                elif ( status == "error" ):
                    clss = "DocBad"
                else:
                    clss = "Doc"
                try:
                    q_strng = "%.3f" % x_lDocs[link]['quality']
                except KeyError:
                    q_strng = "<I>not set</I>"
                try:
                    d_strng = lget_url4fts( x_lDocs[link]['detail'] )
                except KeyError:
                    d_strng = "\"\""
                myFile.write(("<P>\n&nbsp;\n<P>\n<TABLE CELLSPACING=\"0\" CE" +
                              "LLPADDING=\"2\" BORDER=\"1\">\n<TR>\n   <TH C" +
                              "OLSPAN=\"2\" CLASS=\"LinkHeader\"><A NAME=\"" +
                              "%s\">%s &#10140; %s</A> :\n<TR>\n   <TH CLASS" +
                              "=\"Description\">Site/Host/Link name\n   <TD " +
                              "CLASS=\"%s\">%s\n<TR>\n   <TH CLASS=\"Descrip" +
                              "tion\">Evaluation type\n   <TD CLASS=\"%s\">" +
                              "%s\n<TR>\n   <TH CLASS=\"Description\">Qualit" +
                              "y\n   <TD CLASS=\"%s\">%s\n<TR>\n   <TH CLASS" +
                              "=\"Description\">Detail\n   <TD CLASS=\"%s\">" +
                              "%s\n<TR>\n   <TH CLASS=\"Description\">Status" +
                              "\n   <TD CLASS=\"%s\" STYLE=\"font-weight: bo" +
                              "ld;\">%s\n<TR>\n   <TH CLASS=\"Description\">" +
                              "Version number<br>(= insert time)\n   <TD CLA" +
                              "SS=\"%s\">%d.%3.3d (%s UTC)\n<TR>\n   <TH CLA" +
                              "SS=\"Description\">Document id\n   <TD CLASS=" +
                              "\"%s\">%s\n</TABLE>\n\n") %
                             (link, source, dest, clss, x_lDocs[link]['name'],
                              clss, x_lDocs[link]['type'],
                              clss, q_strng,
                              clss, d_strng,
                              clss, status,
                              clss, int(x_lDocs[link]['***VERSION***']/1000),
                                    x_lDocs[link]['***VERSION***']%1000,
                                    time.strftime("%Y-%m-%d %H:%M:%S",
                        time.gmtime(int(x_lDocs[link]['***VERSION***']/1000))),
                              clss, x_lDocs[link]['***DOCID***']))
            myFile.write("<P>\n&nbsp;\n<P>\n")
        #
        try:
            os.chmod(myHTML, 0o644)
        except (IOError, OSError) as excptn:
            logging.warning(("Failed to chmod CMS links mainDVI section file" +
                                                         ", %s") % str(excptn))
        os.rename(myHTML, cfg['html'])

    except (IOError, OSError) as excptn:
        logging.critical("Writing of CMS links mainDVI section failed, %s" %
                                                                   str(excptn))
        try:
            os.unlink( myHTML )
        except:
            pass
        return 1

    logging.log(25, "CMS links doc as HTML table written to %s" %
                                                    cfg['html'].split("/")[-1])
    return 0
# ########################################################################### #



def lftch_maindvi_rank(cfg, docs):
    """function to write site ranking as HTML table with canvas to a file"""
    # ###################################################################### #
    # prepare mainDVI section with site ranking table/graph according to cfg #
    # ###################################################################### #

    # prepare site ranking counters:
    normalizer = 0.000
    rankingDict = {}

    # sum up site values (documents may contain superseded versions):
    for tbin in docs:
        normalizer += 1.000
        #
        # filter out superseded versions:
        myDict = {}
        for myDoc in docs[tbin]:
            if ( myDoc['name'] not in myDict ):
                myDict[ myDoc['name'] ] = myDoc
            elif ( myDoc['vrsn'] > myDict[ myDoc['name'] ]['vrsn'] ):
                myDict[ myDoc['name'] ] = myDoc
        #
        for mySite in myDict:
            if ( mySite not in rankingDict ):
                rankingDict[ mySite ] = [ 0.000, 0.000, 0.000 ]
            rankingDict[ mySite ][0] += myDict[ mySite ]['cntrbt']
            #
            if ( myDict[ mySite ]['dwnflg'] == False ):
                rankingDict[ mySite ][1] += myDict[ mySite ]['cntrbt']
                rankingDict[ mySite ][2] += 1.000
    #
    if ( normalizer > 0.000 ):
        for mySite in rankingDict:
            rankingDict[ mySite ][0] = rankingDict[ mySite ][0] / normalizer
            if ( rankingDict[ mySite ][2] > 0.000 ):
                rankingDict[ mySite ][1] = rankingDict[ mySite ][1] / \
                                                       rankingDict[ mySite ][2]


    # write mainDVI ETF HTML section:
    # ===============================
    myHTML = cfg['html'] + "_wrk"
    #
    try:
        with open(myHTML, 'wt') as myFile:
            #
            myFile.write("<TABLE BORDER=\"0\" CELLPADDING=\"0\" CELLSPACING=" +
                         "\"8\">\n<TR>\n")
            if ( cfg['type'] == "srgroup" ):
                valueStrng = "Status Value"
            elif ( cfg['type'] == "rrgroup" ):
                valueStrng = "Reliability"
            elif ( cfg['type'] == "argroup" ):
                valueStrng = "Availability"
            elif ( cfg['type'] == "vrgroup" ):
                if ( cfg['metric'][:3] == "fts" ):
                    valueStrng = "Avg. Quality"
                else:
                    valueStrng = "Avg. Value"
            if (( cfg['metric'][:3] == "sam" ) or
                ( cfg['metric'][:2] == "sr" )):
                myFile.write(("   <TH STYLE=\"font-size: large; font-weight:" +
                              " bold;\"><B>Site:</B>\n   <TH STYLE=\"font-si" +
                              "ze: large; font-weight: bold;\">Bar Graph:\n " +
                              "  <TH STYLE=\"font-size: large; font-weight: " +
                              "bold;\">%s:\n   <TH STYLE=\"font-size: large;" +
                              "font-weight: normal;\">outside downtime:\n<TR" +
                              " HEIGHT=\"3\">\n   <TD COLSPAN=\"4\" STYLE=\"" +
                              "background-color: black\">\n") % valueStrng)
            else:
                myFile.write(("   <TH STYLE=\"font-size: large; font-weight:" +
                              " bold;\"><B>Site:</B>\n   <TH STYLE=\"font-si" +
                              "ze: large; font-weight: bold;\">Bar Graph:\n " +
                              "  <TH STYLE=\"font-size: large; font-weight: " +
                              "bold;\">%s:\n<TR HEIGHT=\"3\">\n   <TD COLSPA" +
                              "N=\"3\" STYLE=\"background-color: black\">\n") %
                             valueStrng)
            #
            for mySite in sorted(rankingDict.keys(),
                                 key=lambda k: rankingDict[k][0],
                                                                 reverse=True):
                myPercnt = int( 500.0 * (rankingDict[mySite][0] + 0.001) )/5.0
                if ( rankingDict[mySite][0] >= 0.900 ):
                    myColour = "#80FF80"
                elif ( rankingDict[mySite][0] < 0.800 ):
                    myColour = "#FF0000"
                else:
                    myColour = "#FFFF00"
                if (( cfg['metric'][:3] == "sam" ) or
                    ( cfg['metric'][:2] == "sr" )):
                    myFile.write(("<TR>\n   <TD STYLE=\"text-align: right; f" +
                                  "ont-weight: bold; white-space: nowrap;\">" +
                                  "%s\n   <TD STYLE=\"width: 500px; text-ali" +
                                  "gn: left; background-color: #F4F4F4; whit" +
                                  "e-space: nowrap;\"><DIV STYLE=\"width: " +
                                  "%.1f%%; background-color: %s;\">&nbsp;</D" +
                                  "IV>\n   <TD STYLE=\"text-align: center; f" +
                                  "ont-weight: bold; white-space: nowrap;\">" +
                                  "%.3f\n   <TD STYLE=\"text-align: center; " +
                                  "white-space: nowrap;\">%.3f\n") % (mySite,
                                    myPercnt, myColour, rankingDict[mySite][0],
                                                       rankingDict[mySite][1]))
                else:
                    myFile.write(("<TR>\n   <TD STYLE=\"text-align: right; f" +
                                  "ont-weight: bold; white-space: nowrap;\">" +
                                  "%s\n   <TD STYLE=\"width: 500px; text-ali" +
                                  "gn: left; background-color: #F4F4F4; whit" +
                                  "e-space: nowrap;\"><DIV STYLE=\"width: " +
                                  "%.1f%%; background-color: %s;\">&nbsp;</D" +
                                  "IV>\n   <TD STYLE=\"text-align: center; w" +
                                  "hite-space: nowrap;\">%.3f\n") % (mySite,
                                   myPercnt, myColour, rankingDict[mySite][0]))
            #
            if (( cfg['metric'][:3] == "sam" ) or
                ( cfg['metric'][:2] == "sr" )):
                myFile.write("<TR HEIGHT=\"3\">\n   <TD COLSPAN=\"4\" STYLE=" +
                             "\"background-color: black\">\n</TABLE>\n")
            else:
                myFile.write("<TR HEIGHT=\"3\">\n   <TD COLSPAN=\"3\" STYLE=" +
                             "\"background-color: black\">\n</TABLE>\n")
        #
        try:
            os.chmod(myHTML, 0o644)
        except (IOError, OSError) as excptn:
            logging.warning("Failed to chmod ranking mainDVI section file, %s" %
                                                                   str(excptn))
        os.rename(myHTML, cfg['html'])

    except (IOError, OSError) as excptn:
        logging.critical("Writing of ranking mainDVI section failed, %s" %
                                                                   str(excptn))
        try:
            os.unlink( myHTML )
        except:
            pass
        return 1

    logging.log(25, "ranking as HTML table written to %s" %
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
            if ( len(compList[2]) <= 8 ):
                lftch_cfg['time'] = int( compList[2] ) * lftch_cfg['period']
            elif ( len(compList[2]) == 10 ):
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
        elif ( compList[3] in LFTCH_SITE_GROUPS ):
            # site group alias
            lftch_cfg['name'] = compList[3]
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
        elif (( compList[4][1:].lower() == "rgroup" ) and
              ( compList[4][0].lower() in [ "s", "r", "a", "v" ] )):
            lftch_cfg['type'] = compList[4].lower()
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
            if ( len(argStruct.timebin) <= 8 ):
                lftch_cfg['time'] = int( argStruct.timebin ) * \
                                                            lftch_cfg['period']
            elif ( len(argStruct.timebin) == 10 ):
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
        elif ( argStruct.name in LFTCH_SITE_GROUPS ):
            lftch_cfg['name'] = argStruct.name
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
        elif (( argStruct.type[1:].lower() == "rgroup" ) and
              ( argStruct.type[0].lower() in [ "s", "r", "a", "v" ] )):
            lftch_cfg['type'] = argStruct.type.lower()
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
        if ( lftch_cfg['type'][1:] == "rgroup" ):
            rc += lftch_maindvi_rank(lftch_cfg, lftch_monitdocs)
        elif ( lftch_cfg['metric'][:3] == "etf" ):
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
        elif ( lftch_cfg['metric'][:5] == "links" ):
            rc += lftch_maindvi_links(lftch_cfg, lftch_monitdocs)



    # print docs in annotated JSON format to stdout:
    # ==============================================
    if (( 'json' not in lftch_cfg ) and ( 'html' not in lftch_cfg )):
        rc += lftch_print_json(lftch_cfg, lftch_monitdocs)



    #import pdb; pdb.set_trace()
    if ( rc != 0 ):
        sys.exit(1)
    sys.exit(0)
