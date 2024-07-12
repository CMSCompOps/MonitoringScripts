#!/data/cmssst/packages/bin/python3.9
# ########################################################################### #
# python script to fetch selected MonIT documents, provide them to the user
#    for updating/changing, and upload any changes to MonIT.
#    Supported metrics: down15min (all downtimes in the timebin need to be/
#                                  will be uploaded in case of a change)
#                       hc15min, hc1hour, hc6hour, hc1day
#                       sam15min, sam1hour, sam6hour, sam1day
#
# 2019-Mar-26 Stephan Lammel
# ########################################################################### #



import os, sys
import pwd
import argparse
import logging
import time, calendar
import socket
import http
import urllib.request, urllib.error
import subprocess
import json
import gzip
#
# setup the Java/HDFS/PATH environment for pydoop to work properly:
os.environ["HADOOP_CONF_DIR"] = "/data/cmssst/packages/etc/hadoop.analytix.conf/hadoop.analytix"
os.environ["JAVA_HOME"]       = "/data/cmssst/packages/lib/jvm/java-11-openjdk-11.0.23.0.9-3.el9.x86_64"
os.environ["HADOOP_HOME"]     = "/data/cmssst/packages/hadoop/3.3.5-1ba16/x86_64-el9-gcc11-opt"
os.environ["LD_LIBRARY_PATH"] ="/data/cmssst/packages/hadoop/3.3.5-1ba16/x86_64-el9-gcc11-opt/lib/native"
os.environ["PATH"]            ="/data/cmssst/packages/hadoop/3.3.5-1ba16/x86_64-el9-gcc11-opt/bin:" + os.environ["PATH"]
import pydoop.hdfs
# ########################################################################### #



CORR_HDFS_PATH = "/project/monitoring/archive/cmssst/raw/ssbmetric/"
CORR_METRIC_NAMES = [ "vofeed15min",
                      "down15min",
                      "sam15min", "sam1hour", "sam6hour", "sam1day",
                      "hc15min",  "hc1hour",  "hc6hour",  "hc1day",
                      "fts15min", "fts1hour", "fts6hour", "fts1day",
                      "sr15min",  "sr1hour",  "sr6hour",  "sr1day",
                      "sts15min",
                      "scap15min" ]
#CORR_MONIT_URL = "http://monit-metrics.cern.ch:12001/"
# ########################################################################### #



corr_glbl_types = { 'CE': "CE",
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
                    'webdav': "WEBDAV",
                    'wlcg.webdav.tape': "WEBDAV",
                    'WebDAV': "WEBDAV",
                    'WebDAV.tape': "WEBDAV",
                    'WEBDAV': "WEBDAV",
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



def corr_kerberos_check(corr_cfg):
    """function to check we have a valid kerberos ticket"""
    # #################################################################### #
    # check lifetime of krbtgt and email in case less than an hour remains #
    # #################################################################### #
    CORR_KRBCCFILE = "/tmp/krb5cc_%d" % os.getuid()


    # check/set Kerberos credential cache:
    # ====================================
    if 'KRB5CCNAME' not in os.environ:
        os.environ['KRB5CCNAME'] = "FILE:" + CORR_KRBCCFILE
        logging.info("Kerberos credential cache set to %s" % CORR_KRBCCFILE)


    # check lifetime of ticket granting ticket:
    # =========================================
    try:
        cmplProc = subprocess.run(["/usr/bin/klist", "-c"],
                                  stdout=subprocess.PIPE,
                                  stderr=subprocess.DEVNULL, timeout=3)
        cmplProc.check_returncode()
        #
        for myLine in cmplProc.stdout.decode("utf-8").split("\n"):
            if ( myLine[:18] == "Default principal:" ):
                krbPrincipal = myLine[19:].split(" ")[0]
            #
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
                    raise TimeoutError("expiring in %d sec" % secLeft)
                #
                if 'author' not in corr_cfg:
                    loginAcnt = os.getlogin()
                    loginName = pwd.getpwnam(loginAcnt).pw_gecos.split(",")[0]
                    loginName = loginName.replace("\"", "").replace("'", "")
                    loginHost = socket.gethostname()
                    corr_cfg['author'] = "%s as %s from %s" % \
                        (loginName, krbPrincipal, loginHost)
                return True
        raise LookupError("Kerberos klist parsing")
    except Exception as excptn:
        logging.error("Kerberos TGT lifetime check failed, %s" % str(excptn))

    return False
# ########################################################################### #



def corr_monit_fetch(corr_cfg):
    """function to fetch relevant documents from MonIT/HDFS"""
    # #################################################################### #
    # return dictionary with timebin list of relevant documents from MonIT #
    # #################################################################### #
    docDict = {}


    # prepare HDFS subdirectory list:
    # ===============================
    logging.info("Retrieving %s documents from MonIT/HDFS" % corr_cfg['metric'])
    #
    tisDay = 24*60*60
    ts = time.gmtime( corr_cfg['start'] )
    startMidnight = calendar.timegm( ts[:3] + (0, 0, 0) + ts[6:] )
    now = int( time.time() )
    startTmpArea = max( calendar.timegm( time.gmtime( now - (6 * tisDay) ) ),
                        corr_cfg['start'] - tisDay)
    limitLocalTmpArea = calendar.timegm( time.localtime( now ) ) + tisDay
    #
    dirList = []
    for dirDay in range(startMidnight, corr_cfg['limit'], tisDay):
        dirList.append( time.strftime(corr_cfg['metric'] + "/%Y/%m/%d",
                                                       time.gmtime( dirDay )) )
    for dirDay in range(startTmpArea, limitLocalTmpArea, tisDay):
        dirList.append( time.strftime(corr_cfg['metric'] + "/%Y/%m/%d.tmp",
                                                       time.gmtime( dirDay )) )
    del(dirDay)


    # scan HDFS subdirectories and retrieve relevant documents:
    # =========================================================
    tmpDict = {}
    try:
        with pydoop.hdfs.hdfs() as myHDFS:
            fileHndl = None
            fileObj = None
            fileName = None
            fileNames = None
            for subDir in dirList:
                logging.debug("   checking HDFS subdirectory %s" % subDir)
                if not myHDFS.exists( CORR_HDFS_PATH + subDir ):
                    continue
                # get list of files in directory:
                myList = myHDFS.list_directory( CORR_HDFS_PATH + subDir )
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
                            if ( "monit_hdfs_path" not in myJson['metadata'] ):
                                if ( "path" in myJson['metadata'] ):
                                    myJson['metadata']['monit_hdfs_path'] = \
                                                     myJson['metadata']['path']
                                else:
                                    continue
                            if (( 'kafka_timestamp' not in myJson['metadata'] )
                                       or ( '_id' not in myJson['metadata'] )):
                                continue
                            if ( corr_cfg['family'] == "vofeed" ):
                                # check document has required vofeed keys:
                                if (( 'timestamp' not in myJson['metadata'] ) or
                                    ( 'gridsite' not in myJson['data'] ) or
                                    ( 'services' not in myJson['data'] ) or
                                    ( 'site' not in myJson['data'] ) or
                                    ( 'tier' not in myJson['data'] ) or
                                    ( 'update' not in myJson['data'] ) or
                                    ( 'vo' not in myJson['data'] )):
                                    continue
                                if ( myJson['metadata']['monit_hdfs_path'] !=
                                                          corr_cfg['metric'] ):
                                    continue
                                tis = int(myJson['metadata']['timestamp']/1000)
                                if ( tis < corr_cfg['start'] ):
                                    continue
                                if ( tis >= corr_cfg['limit'] ):
                                    continue
                                myName = myJson['data']['site']
                                if 'nameFilter' in corr_cfg:
                                    if ( corr_cfg['nameFilter'] != myName ):
                                        continue
                                myGrid = myJson['data']['gridsite']
                                #
                                version = myJson['metadata']['kafka_timestamp']
                                tbin = int( tis / corr_cfg['period'] )
                                #
                                key = ( tbin, myName, myGrid )
                                val = { 'v': version,
                                        'd': myJson['data'] }
                                if key in tmpDict:
                                    if ( version <= tmpDict[key]['v'] ):
                                        continue
                                tmpDict[key] = val
                            elif ( corr_cfg['family'] == "down" ):
                                # check document has required downtime keys:
                                if (( 'timestamp' not in myJson['metadata'] ) or
                                    ( 'name' not in myJson['data'] ) or
                                    ( 'type' not in myJson['data'] ) or
                                    ( 'status' not in myJson['data'] ) or
                                    ( 'duration' not in myJson['data'] )):
                                    continue
                                if ( myJson['metadata']['monit_hdfs_path'] !=
                                                          corr_cfg['metric'] ):
                                    continue
                                tis = int(myJson['metadata']['timestamp']/1000)
                                if ( tis < corr_cfg['start'] ):
                                    continue
                                if ( tis >= corr_cfg['limit'] ):
                                    continue
                                #
                                version = myJson['metadata']['kafka_timestamp']
                                tbin = int( tis / corr_cfg['period'] )
                                #
                                val = { 'v': version,
                                        'd': myJson['data'] }
                                if tbin not in tmpDict:
                                    tmpDict[ tbin ] = []
                                tmpDict[ tbin ].append( val )
                            elif ( corr_cfg['family'] == "sam" ):
                                # check document has required CMS-SAM keys:
                                if (( 'timestamp' not in myJson['metadata'] ) or
                                    ( 'name' not in myJson['data'] ) or
                                    ( 'type' not in myJson['data'] ) or
                                    ( 'status' not in myJson['data'] )):
                                    continue
                                if ( myJson['metadata']['monit_hdfs_path'] !=
                                                          corr_cfg['metric'] ):
                                    continue
                                tis = int(myJson['metadata']['timestamp']/1000)
                                if ( tis < corr_cfg['start'] ):
                                    continue
                                if ( tis >= corr_cfg['limit'] ):
                                    continue
                                myName = myJson['data']['name']
                                if 'nameFilter' in corr_cfg:
                                    if ( corr_cfg['nameFilter'] != myName ):
                                        continue
                                myType = myJson['data']['type']
                                if 'typeFilter' in corr_cfg:
                                    if myType in corr_glbl_types:
                                        myCtgry = corr_glbl_types[ myType ]
                                    else:
                                        myCtgry = ""
                                    if (( corr_cfg['typeFilter'] != myType ) and
                                        ( corr_cfg['typeFilter'] != myCtgry )):
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
                                tbin = int( tis / corr_cfg['period'] )
                                #
                                key = ( tbin, myName, myType )
                                val = { 'v': version,
                                        'd': myJson['data'] }
                                if key in tmpDict:
                                    if ( version <= tmpDict[key]['v'] ):
                                        continue
                                tmpDict[key] = val
                            elif ( corr_cfg['family'] == "hc" ):
                                # check document has required CMS-HC keys:
                                if (( 'timestamp' not in myJson['metadata'] ) or
                                    (( 'name' not in myJson['data'] ) and
                                     ( 'site' not in myJson['data'] )) or
                                    ( 'status' not in myJson['data'] )):
                                    continue
                                if ( myJson['metadata']['monit_hdfs_path'] !=
                                                          corr_cfg['metric'] ):
                                    continue
                                tis = int(myJson['metadata']['timestamp']/1000)
                                if ( tis < corr_cfg['start'] ):
                                    continue
                                if ( tis >= corr_cfg['limit'] ):
                                    continue
                                if 'name' not in myJson['data']:
                                    myJson['data']['name'] = myJson['data']['site']
                                myName = myJson['data']['name']
                                if 'nameFilter' in corr_cfg:
                                    if ( corr_cfg['nameFilter'] != myName ):
                                        continue
                                #
                                if 'value' not in myJson['data']:
                                    myJson['data']['value'] = None
                                if 'detail' not in myJson['data']:
                                    myJson['data']['detail'] = None
                                #
                                version = myJson['metadata']['kafka_timestamp']
                                tbin = int( tis / corr_cfg['period'] )
                                #
                                key = ( tbin, myName )
                                val = { 'v': version,
                                        'd': myJson['data'] }
                                if key in tmpDict:
                                    if ( version <= tmpDict[key]['v'] ):
                                        continue
                                tmpDict[key] = val
                            elif ( corr_cfg['family'] == "fts" ):
                                # check document has required CMS-FTS keys:
                                if (( 'timestamp' not in myJson['metadata'] ) or
                                    ( 'name' not in myJson['data'] ) or
                                    ( 'type' not in myJson['data'] ) or
                                    ( 'status' not in myJson['data'] )):
                                    continue
                                if ( myJson['metadata']['monit_hdfs_path'] !=
                                                          corr_cfg['metric'] ):
                                    continue
                                tis = int(myJson['metadata']['timestamp']/1000)
                                if ( tis < corr_cfg['start'] ):
                                    continue
                                if ( tis >= corr_cfg['limit'] ):
                                    continue
                                myName = myJson['data']['name']
                                if 'nameFilter' in corr_cfg:
                                    if ( corr_cfg['nameFilter'] != myName ):
                                        continue
                                myType = myJson['data']['type']
                                if 'typeFilter' in corr_cfg:
                                    if ( corr_cfg['typeFilter'] != myType ):
                                        continue
                                #
                                if 'quality' not in myJson['data']:
                                    myJson['data']['quality'] = None
                                if 'detail' not in myJson['data']:
                                    myJson['data']['detail'] = None
                                #
                                version = myJson['metadata']['kafka_timestamp']
                                tbin = int( tis / corr_cfg['period'] )
                                #
                                key = ( tbin, myName, myType )
                                val = { 'v': version,
                                        'd': myJson['data'] }
                                if key in tmpDict:
                                    if ( version <= tmpDict[key]['v'] ):
                                        continue
                                tmpDict[key] = val
                            elif ( corr_cfg['family'] == "sr" ):
                                # check document has required CMS-SR keys:
                                if (( 'timestamp' not in myJson['metadata'] ) or
                                    ( 'name' not in myJson['data'] ) or
                                    ( 'status' not in myJson['data'] )):
                                    continue
                                if ( myJson['metadata']['monit_hdfs_path'] !=
                                                          corr_cfg['metric'] ):
                                    continue
                                tis = int(myJson['metadata']['timestamp']/1000)
                                if ( tis < corr_cfg['start'] ):
                                    continue
                                if ( tis >= corr_cfg['limit'] ):
                                    continue
                                myName = myJson['data']['name']
                                if 'nameFilter' in corr_cfg:
                                    if ( corr_cfg['nameFilter'] != myName ):
                                        continue
                                #
                                if 'value' not in myJson['data']:
                                    myJson['data']['value'] = None
                                if 'detail' not in myJson['data']:
                                    myJson['data']['detail'] = None
                                #
                                version = myJson['metadata']['kafka_timestamp']
                                tbin = int( tis / corr_cfg['period'] )
                                #
                                key = ( tbin, myName )
                                val = { 'v': version,
                                        'd': myJson['data'] }
                                if key in tmpDict:
                                    if ( version <= tmpDict[key]['v'] ):
                                        continue
                                tmpDict[key] = val
                            elif ( corr_cfg['family'] == "sts" ):
                                # check document has required CMS-STS keys:
                                if (( 'timestamp' not in myJson['metadata'] ) or
                                    ( 'name' not in myJson['data'] ) or
                                    ( 'status' not in myJson['data'] ) or
                                    ( 'prod_status' not in myJson['data'] ) or
                                    ( 'crab_status' not in myJson['data'] )):
                                    continue
                                if ( myJson['metadata']['monit_hdfs_path'] !=
                                                          corr_cfg['metric'] ):
                                    continue
                                tis = int(myJson['metadata']['timestamp']/1000)
                                if ( tis < corr_cfg['start'] ):
                                    continue
                                if ( tis >= corr_cfg['limit'] ):
                                    continue
                                myName = myJson['data']['name']
                                if 'nameFilter' in corr_cfg:
                                    if ( corr_cfg['nameFilter'] != myName ):
                                        continue
                                #
                                if 'rucio_status' not in myJson['data']:
                                    myJson['data']['rucio_status'] = None
                                if 'manual_life' not in myJson['data']:
                                    myJson['data']['manual_life'] = None
                                if 'manual_prod' not in myJson['data']:
                                    myJson['data']['manual_prod'] = None
                                if 'manual_crab' not in myJson['data']:
                                    myJson['data']['manual_crab'] = None
                                if 'manual_rucio' not in myJson['data']:
                                    myJson['data']['manual_rucio'] = None
                                if 'detail' not in myJson['data']:
                                    myJson['data']['detail'] = None
                                #
                                version = myJson['metadata']['kafka_timestamp']
                                tbin = int( tis / corr_cfg['period'] )
                                #
                                key = ( tbin, myName )
                                val = { 'v': version,
                                        'd': myJson['data'] }
                                if key in tmpDict:
                                    if ( version <= tmpDict[key]['v'] ):
                                        continue
                                tmpDict[key] = val
                            elif ( corr_cfg['family'] == "scap" ):
                                # check document has required CMS-SCAP keys:
                                if (( 'timestamp' not in myJson['metadata'] ) or
                                    ( 'name' not in myJson['data'] ) or
                                    ( 'hs06_pledge' not in myJson['data'] ) or
                                    ( 'hs06_per_core' not in myJson['data'] ) or
                                    ( 'core_usable' not in myJson['data'] ) or
                                    ( 'core_max_used' not in myJson['data'] ) or
                                    ( 'core_production' not in
                                                            myJson['data'] ) or
                                    ( 'core_cpu_intensive' not in
                                                            myJson['data'] ) or
                                    ( 'core_io_intensive' not in
                                                            myJson['data'] ) or
                                    ( 'disk_pledge' not in myJson['data'] ) or
                                    ( 'disk_usable' not in myJson['data'] ) or
                                    ( 'disk_experiment_use' not in
                                                             myJson['data'] )):
                                    continue
                                if ( myJson['metadata']['monit_hdfs_path'] !=
                                                          corr_cfg['metric'] ):
                                    continue
                                tis = int(myJson['metadata']['timestamp']/1000)
                                if ( tis < corr_cfg['start'] ):
                                    continue
                                if ( tis >= corr_cfg['limit'] ):
                                    continue
                                myName = myJson['data']['name']
                                if 'nameFilter' in corr_cfg:
                                    if ( corr_cfg['nameFilter'] != myName ):
                                        continue
                                #
                                if 'wlcg_federation_name' not in myJson['data']:
                                    myJson['data']['wlcg_federation_name'] \
                                                                         = None
                                if 'wlcg_federation_fraction' not in \
                                                                myJson['data']:
                                    myJson['data']['wlcg_federation_fraction'] \
                                                                         = None
                                if 'tape_pledge' not in myJson['data']:
                                    myJson['data']['tape_pledge'] = 0.0
                                if 'tape_usable' not in myJson['data']:
                                    myJson['data']['tape_usable'] = 0.0
                                if 'when' not in myJson['data']:
                                    myJson['data']['when'] = None
                                if 'who' not in myJson['data']:
                                    myJson['data']['who'] = None
                                #
                                version = myJson['metadata']['kafka_timestamp']
                                tbin = int( tis / corr_cfg['period'] )
                                #
                                key = ( tbin, myName )
                                val = { 'v': version,
                                        'd': myJson['data'] }
                                if key in tmpDict:
                                    if ( version <= tmpDict[key]['v'] ):
                                        continue
                                tmpDict[key] = val
                            else:
                                continue

                    except json.decoder.JSONDecodeError as excptn:
                        logging.error("JSON decoding failure, %s, %s" %
                                                       (fileName, str(excptn)))
                    except FileNotFoundError as excptn:
                        logging.error("HDFS file not found, %s, %s" %
                                                       (fileName, str(excptn)))
                    except IOError as excptn:
                        logging.error("HDFS access failure, %s, %s" %
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
        logging.error("Failed to fetch %s metric docs from MonIT HDFS" %
                                                            corr_cfg['metric'])


    if ( corr_cfg['family'] == "down" ):
        # filter out superseded versions and fill global dictionary:
        cnt = 0
        for tbin in tmpDict:
            # loop over all docs of a timebin and find latest version:
            latest = 0
            for entry in tmpDict[ tbin ]:
                if ( entry['v'] > latest ):
                    latest = entry['v']
            #
            docDict[ tbin ] = []
            #
            # fill documents of the latest version into global dictionary:
            for entry in tmpDict[ tbin ]:
                # allow 5 min for MonIT importer processing
                if ( (latest - entry['v']) <= 300000 ):
                    docDict[ tbin ].append( entry['d'] )
                    cnt += 1
                    logging.log(9, "      adding %s (%d) of %s" %
                                (corr_cfg['metric'], tbin, entry['d']['name']))
        #
        logging.info("   found %d relevant %s metric docs in MonIT" %
                                                     (cnt, corr_cfg['metric']))
    else:
        # fill highest version name/type doc into global dictionary:
        for myKey in tmpDict:
            tbin = myKey[0]
            if tbin not in docDict:
                docDict[ tbin ] = []
            docDict[ tbin ].append( tmpDict[myKey]['d'] )
            logging.log(9, "      adding %s (%d) of %s" %
                                          (corr_cfg['metric'], tbin, myKey[1]))
        #
        logging.info("   found %d relevant %s metric docs in MonIT" %
                                            (len(tmpDict), corr_cfg['metric']))
    del tmpDict
    #
    return docDict
# ########################################################################### #



def corr_compose_vofeed_json(timestamp, topology):
    """function to convert a VO-feed to a JSON list of dictionaries"""
    # ################################################################# #
    # write JSON string with VO-feed list that can be uploaded to MonIT #
    # ################################################################# #

    jsonString = "["
    hdrString = ((",\n {\n   \"producer\": \"cmssst\",\n" +
                         "   \"type\": \"ssbmetric\",\n" +
                         "   \"monit_hdfs_path\": \"vofeed15min\",\n" +
                         "   \"timestamp\": %d000,\n" +
                         "   \"type_prefix\": \"raw\",\n" +
                         "   \"data\": {\n") % timestamp)

    comma1Flag = False
    for doc in sorted(topology, key=lambda k: [k['tier'], k['site'],
                                                          k['gridsite']]):
        if comma1Flag:
            jsonString += hdrString
        else:
            jsonString += hdrString[1:]
        #
        jsonString += (("      \"vo\": \"CMS\",\n" +
                        "      \"update\": \"%s\",\n" +
                        "      \"site\": \"%s\",\n" +
                        "      \"tier\": \"%s\",\n" +
                        "      \"gridsite\": \"%s\",\n" +
                        "      \"services\": [\n") %
                       (doc['update'], doc['site'], doc['tier'],
                        doc['gridsite']))
        comma2Flag = False
        for srvc in doc['services']:
            if comma2Flag:
                jsonString += ", {\n"
            else:
                jsonString += "       {\n"
            jsonString += ("         \"hostname\": \"%s\",\n" +
                           "         \"flavour\": \"%s\"") % \
                           (srvc['hostname'], srvc['flavour'])
            if 'endpoint' in srvc:
                jsonString += ",\n         \"endpoint\": \"%s\"" % \
                              srvc['endpoint']
            if 'queue' in srvc:
                jsonString += ",\n         \"queue\": \"%s\"" % \
                              srvc['queue']
            if 'batch' in srvc:
                jsonString += ",\n         \"batch\": \"%s\"" % \
                              srvc['batch']
            if 'production' in srvc:
                if not srvc['production']:
                    jsonString += ",\n         \"production\": false"
            jsonString += "\n       }"
            comma2Flag = True
        jsonString += "\n     ]"
        if 'author' in doc:
            if doc['author'] is not None:
                jsonString += ",\n      \"author\": \"%s\"" % doc['author']
        jsonString += "\n   }\n }"
        comma1Flag = True
    jsonString += "\n]\n"

    return jsonString



def corr_compose_down_json(timestamp, downtimes):
    """function to convert downtime list to a JSON list of dictionaries"""
    # ################################################################## #
    # write JSON string with downtime list that can be uploaded to MonIT #
    # ################################################################## #

    jsonString = "["
    hdrString = ((",\n {\n   \"producer\": \"cmssst\",\n" +
                         "   \"type\": \"ssbmetric\",\n" +
                         "   \"monit_hdfs_path\": \"down15min\",\n" +
                         "   \"timestamp\": %d000,\n" +
                         "   \"type_prefix\": \"raw\",\n" +
                         "   \"data\": {\n") % timestamp)

    commaFlag = False
    for doc in sorted(downtimes, key=lambda k: [k['name'], k['type'],
                                          k['duration'][0], k['duration'][1]]):
        if commaFlag:
            jsonString += hdrString
        else:
            jsonString += hdrString[1:]
        #
        jsonString += (("      \"name\": \"%s\",\n" +
                        "      \"type\": \"%s\",\n" +
                        "      \"status\": \"%s\",\n" +
                        "      \"duration\": [%d, %d],\n") %
                       (doc['name'], doc['type'], doc['status'],
                        doc['duration'][0], doc['duration'][1]))
        if doc['detail'] is not None:
            jsonString += ("      \"detail\": \"%s\"" %
                                             doc['detail'].replace('\n','\\n'))
        else:
            jsonString += ("      \"detail\": null")
        if 'author' in doc:
            if doc['author'] is not None:
                jsonString += (",\n      \"author\": \"%s\"" %
                                                                 doc['author'])
        jsonString += "\n   }\n }"
        commaFlag = True
    jsonString += "\n]\n"

    return jsonString



def corr_compose_sam_json(metric, timestamp, results):
    """function to convert SAM result list to a JSON list of dictionaries"""
    # #################################################################### #
    # write JSON string with SAM result list that can be uploaded to MonIT #
    # #################################################################### #

    jsonString = "["
    hdrString = ((",\n {\n   \"producer\": \"cmssst\",\n" +
                         "   \"type\": \"ssbmetric\",\n" +
                         "   \"monit_hdfs_path\": \"%s\",\n" +
                         "   \"timestamp\": %d000,\n" +
                         "   \"type_prefix\": \"raw\",\n" +
                         "   \"data\": {\n") % (metric, timestamp))

    commaFlag = False
    for doc in sorted(results, key=lambda k: [k['name'], k['type'],
                                                                 k['status']]):
        if commaFlag:
            jsonString += hdrString
        else:
            jsonString += hdrString[1:]
        #
        jsonString += (("      \"name\": \"%s\",\n" +
                        "      \"type\": \"%s\",\n" +
                        "      \"status\": \"%s\",\n") %
                       (doc['name'], doc['type'], doc['status']))
        if doc['availability'] is not None:
            jsonString += ("      \"availability\": %.3f,\n" %
                           doc['availability'])
        elif ( doc['type'] == "site" ):
            jsonString += ("      \"availability\": null,\n")
        if doc['reliability'] is not None:
            jsonString += ("      \"reliability\": %.3f,\n" %
                           doc['reliability'])
        elif ( doc['type'] == "site" ):
            jsonString += ("      \"reliability\": null,\n")
        if doc['detail'] is not None:
            jsonString += ("      \"detail\": \"%s\"" %
                                             doc['detail'].replace('\n','\\n'))
        else:
            jsonString += ("      \"detail\": null")
        if 'author' in doc:
            if doc['author'] is not None:
                jsonString += (",\n      \"author\": \"%s\"" %
                                                                 doc['author'])
        jsonString += "\n   }\n }"
        commaFlag = True
    jsonString += "\n]\n"

    return jsonString



def corr_compose_hc_json(metric, timestamp, results):
    """function to convert HC result list to a JSON list of dictionaries"""
    # ##################################################################### #
    # write JSON string with HammerCloud list that can be uploaded to MonIT #
    # ##################################################################### #

    jsonString = "["
    hdrString = ((",\n {\n   \"producer\": \"cmssst\",\n" +
                         "   \"type\": \"ssbmetric\",\n" +
                         "   \"monit_hdfs_path\": \"%s\",\n" +
                         "   \"timestamp\": %d000,\n" +
                         "   \"type_prefix\": \"raw\",\n" +
                         "   \"data\": {\n") % (metric, timestamp))

    commaFlag = False
    for doc in sorted(results, key=lambda k: [k['name'], k['status']]):
        if commaFlag:
            jsonString += hdrString
        else:
            jsonString += hdrString[1:]
        #
        jsonString += (("      \"name\": \"%s\",\n" +
                        "      \"status\": \"%s\",\n") %
                       (doc['name'], doc['status']))
        if doc['value'] is not None:
            jsonString += ("      \"value\": %.3f,\n" %
                           doc['value'])
        else:
            jsonString += "      \"value\": null,\n"
        if doc['detail'] is not None:
            jsonString += ("      \"detail\": \"%s\"" %
                                             doc['detail'].replace('\n','\\n'))
        else:
            jsonString += ("      \"detail\": null")
        if 'author' in doc:
            if doc['author'] is not None:
                jsonString += (",\n      \"author\": \"%s\"" %
                                                                 doc['author'])
        jsonString += "\n   }\n }"
        commaFlag = True
    jsonString += "\n]\n"

    return jsonString



def corr_compose_fts_json(metric, timestamp, results):
    """function to convert FTS result list to a JSON list of dictionaries"""
    # #################################################################### #
    # write JSON string with FTS result list that can be uploaded to MonIT #
    # #################################################################### #
    SORT_ORDER = {"link": 1, "GSIFTP-link": 2, "WEBDAV-link": 3,
                  "XROOTD-link": 4, "source": 5, "destination": 6,
                  "GSIFTP-source": 7, "GSIFTP-destination": 8,
                  "WEBDAV-source": 9, "WEBDAV-destination": 10,
                  "XROOTD-source": 11, "XROOTD-destination": 12,
                  "rse": 13, "site": 14}

    jsonString = "["
    hdrString = ((",\n {\n   \"producer\": \"cmssst\",\n" +
                         "   \"type\": \"ssbmetric\",\n" +
                         "   \"monit_hdfs_path\": \"%s\",\n" +
                         "   \"timestamp\": %d000,\n" +
                         "   \"type_prefix\": \"raw\",\n" +
                         "   \"data\": {\n") % (metric, timestamp))

    commaFlag = False
    for doc in sorted(results, key=lambda k: [SORT_ORDER[k['type']],k['name']]):
        if commaFlag:
            jsonString += hdrString
        else:
            jsonString += hdrString[1:]
        #
        jsonString += (("      \"name\": \"%s\",\n" +
                        "      \"type\": \"%s\",\n" +
                        "      \"status\": \"%s\",\n") %
                       (doc['name'], doc['type'], doc['status']))
        if doc['quality'] is not None:
            jsonString += ("      \"quality\": %.3f,\n" % doc['quality'])
        else:
            jsonString += ("      \"quality\": null,\n")
        if doc['detail'] is not None:
            jsonString += ("      \"detail\": \"%s\"" %
                                             doc['detail'].replace('\n','\\n'))
        else:
            jsonString += ("      \"detail\": null")
        if 'author' in doc:
            if doc['author'] is not None:
                jsonString += (",\n      \"author\": \"%s\"" %
                                                                 doc['author'])
        jsonString += "\n   }\n }"
        commaFlag = True
    jsonString += "\n]\n"

    return jsonString



def corr_compose_sr_json(metric, timestamp, results):
    """function to convert SR result list to a JSON list of dictionaries"""
    # ################################################################### #
    # write JSON string with SR result list that can be uploaded to MonIT #
    # ################################################################### #

    jsonString = "["
    hdrString = ((",\n {\n   \"producer\": \"cmssst\",\n" +
                         "   \"type\": \"ssbmetric\",\n" +
                         "   \"monit_hdfs_path\": \"%s\",\n" +
                         "   \"timestamp\": %d000,\n" +
                         "   \"type_prefix\": \"raw\",\n" +
                         "   \"data\": {\n") % (metric, timestamp))

    commaFlag = False
    for doc in sorted(results, key=lambda k: k['name']):
        if commaFlag:
            jsonString += hdrString
        else:
            jsonString += hdrString[1:]
        #
        jsonString += (("      \"name\": \"%s\",\n" +
                        "      \"status\": \"%s\",\n") %
                       (doc['name'], doc['status']))
        if doc['value'] is not None:
            jsonString += ("      \"value\": %.3f,\n" % doc['value'])
        else:
            jsonString += ("      \"value\": null,\n")
        if doc['detail'] is not None:
            jsonString += ("      \"detail\": \"%s\"" %
                                             doc['detail'].replace('\n','\\n'))
        else:
            jsonString += ("      \"detail\": null")
        if 'author' in doc:
            if doc['author'] is not None:
                jsonString += (",\n      \"author\": \"%s\"" %
                                                                 doc['author'])
        jsonString += "\n   }\n }"
        commaFlag = True
    jsonString += "\n]\n"

    return jsonString



def corr_compose_sts_json(timestamp, results):
    """function to convert STS result list to a JSON list of dictionaries"""
    # #################################################################### #
    # write JSON string with STS result list that can be uploaded to MonIT #
    # #################################################################### #

    jsonString = "["
    hdrString = ((",\n {\n   \"producer\": \"cmssst\",\n" +
                         "   \"type\": \"ssbmetric\",\n" +
                         "   \"monit_hdfs_path\": \"sts15min\",\n" +
                         "   \"timestamp\": %d000,\n" +
                         "   \"type_prefix\": \"raw\",\n" +
                         "   \"data\": {\n") % timestamp)

    commaFlag = False
    for doc in sorted(results, key=lambda k: k['name']):
        if commaFlag:
            jsonString += hdrString
        else:
            jsonString += hdrString[1:]
        #
        jsonString += (("      \"name\": \"%s\",\n" +
                        "      \"status\": \"%s\",\n" +
                        "      \"prod_status\": \"%s\",\n" +
                        "      \"crab_status\": \"%s\",\n") %
                       (doc['name'], doc['status'], doc['prod_status'],
                                                           doc['crab_status']))
        if doc['rucio_status'] is not None:
            jsonString += ("      \"rucio_status\": \"%s\",\n" %
                                                           doc['rucio_status'])
        if doc['manual_life'] is not None:
            jsonString += ("      \"manual_life\": \"%s\",\n" %
                                                            doc['manual_life'])
        if doc['manual_prod'] is not None:
            jsonString += ("      \"manual_prod\": \"%s\",\n" %
                                                            doc['manual_prod'])
        if doc['manual_crab'] is not None:
            jsonString += ("      \"manual_crab\": \"%s\",\n" %
                                                            doc['manual_crab'])
        if doc['manual_rucio'] is not None:
            jsonString += ("      \"manual_rucio\": \"%s\",\n" %
                                                           doc['manual_rucio'])
        if doc['detail'] is not None:
            jsonString += ("      \"detail\": \"%s\"" %
                                             doc['detail'].replace('\n','\\n'))
        else:
            jsonString += ("      \"detail\": null")
        if 'author' in doc:
            if doc['author'] is not None:
                jsonString += (",\n      \"author\": \"%s\"" %
                                                                 doc['author'])
        jsonString += "\n   }\n }"
        commaFlag = True
    jsonString += "\n]\n"

    return jsonString



def corr_compose_scap_json(timestamp, results):
    """function to convert capacity list to a JSON list of dictionaries"""
    # ################################################################## #
    # write JSON string with capacity list that can be uploaded to MonIT #
    # ################################################################## #

    jsonString = "["
    hdrString = ((",\n {\n   \"producer\": \"cmssst\",\n" +
                         "   \"type\": \"ssbmetric\",\n" +
                         "   \"monit_hdfs_path\": \"scap15min\",\n" +
                         "   \"timestamp\": %d000,\n" +
                         "   \"type_prefix\": \"raw\",\n" +
                         "   \"data\": {\n") % timestamp)

    commaFlag = False
    for doc in sorted(results, key=lambda k: k['name']):
        if commaFlag:
            jsonString += hdrString
        else:
            jsonString += hdrString[1:]
        #
        jsonString += ("      \"name\": \"%s\",\n" % doc['name'])
        if (( 'wlcg_federation_name' in doc ) and
            ( doc['wlcg_federation_name'] is not None )):
            jsonString += ("      \"wlcg_federation_name\": \"%s\",\n" %
                                                   doc['wlcg_federation_name'])
        else:
            jsonString += ("      \"wlcg_federation_name\": null,\n")
        if (( 'wlcg_federation_fraction' in doc ) and
            ( doc['wlcg_federation_fraction'] is not None )):
            jsonString += ("      \"wlcg_federation_fraction\": %.3f,\n" %
                                               doc['wlcg_federation_fraction'])
        else:
            jsonString += ("      \"wlcg_federation_fraction\": 1.000,\n")
        if (( 'hs06_pledge' in doc ) and ( doc['hs06_pledge'] is not None )):
            jsonString += ("      \"hs06_pledge\": %d,\n" % doc['hs06_pledge'])
        else:
            jsonString += ("      \"hs06_pledge\": 0,\n")
        if (( 'hs06_per_core' in doc ) and
            ( doc['hs06_per_core'] is not None )):
            jsonString += ("      \"hs06_per_core\": %.3f,\n" %
                                                          doc['hs06_per_core'])
        else:
           jsonString += ("      \"hs06_per_core\": 10.000,\n")
        for myKey in ['core_usable', 'core_max_used', 'core_production', \
                      'core_cpu_intensive', 'core_io_intensive' ]:
            if (( myKey in doc ) and ( doc[myKey] is not None )):
                jsonString += ("      \"%s\": %d,\n" % (myKey, doc[myKey]))
            else:
                jsonString += ("      \"%s\": 0,\n" % myKey)
        for myKey in ['disk_pledge', 'disk_usable', 'disk_experiment_use', \
                      'tape_pledge', 'tape_usable' ]:
            if (( myKey in doc ) and ( doc[myKey] is not None )):
                jsonString += ("      \"%s\": %.1f,\n" % (myKey, doc[myKey]))
            else:
                jsonString += ("      \"%s\": 0.0,\n" % myKey)
        if (( 'when' in doc ) and ( doc['when'] is not None )):
            jsonString += ("      \"when\": \"%s\",\n" % doc['when'])
        else:
            jsonString += ("      \"when\": null,\n")
        if (( 'who' in doc ) and ( doc['who'] is not None )):
            jsonString += ("      \"who\": \"%s\"\n" % doc['who'])
        else:
            jsonString += ("      \"who\": null")
        if 'author' in doc:
            if doc['author'] is not None:
                jsonString += (",\n      \"author\": \"%s\"" %
                                                                 doc['author'])
        jsonString += "\n   }\n }"
        commaFlag = True
    jsonString += "\n]\n"

    return jsonString



def corr_write_files(cfg, docDict):
    """function to write MonIT documents to file for editing/correction"""
    # ############################################################### #
    # write docs in global dictionary to one file or file per timebin #
    # ############################################################### #
    CORR_FILE_PATH = "/tmp/corr_%d_%%d.json" % os.getpid()
    halfBin = int( cfg['period'] / 2 )


    if ( not cfg['by_tbin'] ):
        filename = CORR_FILE_PATH % 0
        cfg['files'].append(filename)
        myFile = open(filename, "wt")
        myFile.write("[")

    commaFlag = False
    #
    for tbin in docDict:
        startTIS = int( tbin * cfg['period'] )
        centerTIS = ( startTIS + halfBin )
        #
        if ( cfg['family'] == "vofeed" ):
            jsonString = corr_compose_vofeed_json(centerTIS, docDict[tbin] )
        elif ( cfg['family'] == "down" ):
            jsonString = corr_compose_down_json(centerTIS, docDict[tbin] )
        elif ( cfg['family'] == "sam" ):
            jsonString = corr_compose_sam_json(cfg['metric'], centerTIS,
                                                                docDict[tbin] )
        elif ( cfg['family'] == "hc" ):
            jsonString = corr_compose_hc_json(cfg['metric'], centerTIS,
                                                                docDict[tbin] )
        elif ( cfg['family'] == "fts" ):
            jsonString = corr_compose_fts_json(cfg['metric'], centerTIS,
                                                                docDict[tbin] )
        elif ( cfg['family'] == "sr" ):
            jsonString = corr_compose_sr_json(cfg['metric'], centerTIS,
                                                                docDict[tbin] )
        elif ( cfg['family'] == "sts" ):
            jsonString = corr_compose_sts_json(centerTIS, docDict[tbin] )
        elif ( cfg['family'] == "scap" ):
            jsonString = corr_compose_scap_json(centerTIS, docDict[tbin] )
        #
        if ( cfg['by_tbin'] ):
            filename = CORR_FILE_PATH % tbin
            cfg['files'].append(filename)
            with open(filename, "wt") as myFile:
                myFile.write(("[\n\n# time-bin %s\n\n") %
                        time.strftime("%Y-%b-%d %H:%M", time.gmtime(startTIS)))
                myFile.write( jsonString[2:] )
            logging.info("document(s) written to %s for editing" % filename)
        else:
            if commaFlag:
                myFile.write((",\n\n\n# start of time-bin %s:\n") %
                        time.strftime("%Y-%b-%d %H:%M", time.gmtime(startTIS)))
                myFile.write( jsonString[2:-3] )
            else:
                myFile.write(("\n\n\n# start of time-bin %s:\n") %
                        time.strftime("%Y-%b-%d %H:%M", time.gmtime(startTIS)))
                myFile.write( jsonString[2:-3] )
        commaFlag = True

    if ( not cfg['by_tbin'] ):
        myFile.write("\n]\n")
        #
        logging.info("file %s with document(s) written for editing" % filename)
        myFile.close()

    return
# ########################################################################### #



def corr_advise_edit(cfg):
    """function to print correction editing advice, prompt, and edit"""
    # ########################################################## #
    # print correction editing advice, prompt, and launch editor #
    # ########################################################## #

    print("")
    print(("Documents fetched from MonIT/HDFS will be presented in vi for co" +
          "rrection.\n   To exit vi without saving, use the \":q!\" key-sque" +
          "nce. The file(s) are \n   /tmp/corr_%s_<timebin>.json (in case yo" +
          "u are unaccustomed with vi\n   and need to use another editor).") %
          corr_cfg['files'][0].split("_")[1])
    print("Documents of a timebin can be changed individually for SAM and HC" +
          " but not\n   for downtime. Downtime documents in the file(s) shou" +
          "d not be deleted\n   (except to remove a downtime entry but setti" +
          "ng status to \"ok\" would be\n   better). For both, SAM and HC, d" +
          "ocuments in the file that don't need\n   correction can be delete" +
          "d. Downtime entries stay valid until the next\n   timebin with do" +
          "cuments. To insert a new timebin, copy the documents of\n   the [" +
          "revious timebin to start. (Any documents that don't need to be \n" +
          "   loaded will be filtered out automatically to avoid unnecessary" +
          "\n   duplication.)\n   PLEASE make sure you know what you are doi" +
          "ng!!!")
    myAbort = input("\nPress <Enter> to begin the editing (or A[bort] to qui" +
                    "t). You get a chance\n   to discard any changes.) ")
    if (( myAbort.lower() == "a" ) or ( myAbort.lower() == "abort" )):
        for filename in corr_cfg['files']:
            os.unlink(filename)
            logging.info("deleting file %s written for editing" % filename)
        return False

    subprocess.run(["/usr/bin/vi"] + corr_cfg['files'])

    myAbort = input("\nDiscard? Y[es] (or <Enter> to keep and continue ")
    if (( myAbort.lower() == "y" ) or ( myAbort.lower() == "yes" ) or
        ( myAbort.lower() == "d" ) or ( myAbort.lower() == "discard" )):
        for filename in corr_cfg['files']:
            os.unlink(filename)
            logging.info("discarding file %s written for editing" % filename)
        return False

    return True
# ########################################################################### #



def corr_parse_files(corr_cfg):
    """function to read corrected JSON documents from the edited files"""
    # #################################################################### #
    # read JSON docs from files and return a dictionary with timebin lists #
    # #################################################################### #
    filedocs = {}

    # loop over files and read JSON docs:
    for filename in corr_cfg['files']:
        logging.debug("   file %s" % os.path.basename(filename))
        try:
            myData = ""
            with open(filename, "rt") as myFile:
                # read documents and add relevant lines to data string:
                for myLine in myFile:
                    if (( myLine != "\n" ) and ( myLine[0] != "#" )):
                        myData += myLine
            jsonArray = json.loads(myData)
            #
            for myJson in jsonArray:
                if (( 'timestamp' not in myJson ) or ( 'data' not in myJson )):
                    continue
                if ( corr_cfg['family'] == "vofeed" ):
                    # check document has required vofeed keys:
                    if (( 'gridsite' not in myJson['data'] ) or
                        ( 'services' not in myJson['data'] ) or
                        ( 'site' not in myJson['data'] ) or
                        ( 'tier' not in myJson['data'] ) or
                        ( 'update' not in myJson['data'] ) or
                        ( 'vo' not in myJson['data'] )):
                        continue
                elif ( corr_cfg['family'] == "down" ):
                    # check document has required downtime keys:
                    if (( 'name' not in myJson['data'] ) or
                        ( 'type' not in myJson['data'] ) or
                        ( 'status' not in myJson['data'] ) or
                        ( 'duration' not in myJson['data'] )):
                        continue
                elif ( corr_cfg['family'] == "sam" ):
                    # check document has required CMS-SAM keys:
                    if (( 'name' not in myJson['data'] ) or
                        ( 'type' not in myJson['data'] ) or
                        ( 'status' not in myJson['data'] )):
                        continue
                    #
                    if 'availability' not in myJson['data']:
                        myJson['data']['availability'] = None
                    if 'reliability' not in myJson['data']:
                        myJson['data']['reliability'] = None
                    if 'detail' not in myJson['data']:
                        myJson['data']['detail'] = None
                elif ( corr_cfg['family'] == "hc" ):
                    # check document has required CMS-HC keys:
                    if (( 'name' not in myJson['data'] ) or
                        ( 'status' not in myJson['data'] )):
                        continue
                    #
                    if 'value' not in myJson['data']:
                        myJson['data']['value'] = None
                    if 'detail' not in myJson['data']:
                        myJson['data']['detail'] = None
                elif ( corr_cfg['family'] == "fts" ):
                    # check document has required CMS-FTS keys:
                    if (( 'name' not in myJson['data'] ) or
                        ( 'type' not in myJson['data'] ) or
                        ( 'status' not in myJson['data'] )):
                        continue
                    #
                    if 'quality' not in myJson['data']:
                        myJson['data']['quality'] = None
                    if 'detail' not in myJson['data']:
                        myJson['data']['detail'] = None
                elif ( corr_cfg['family'] == "sr" ):
                    # check document has required CMS-Site Readiness keys:
                    if (( 'name' not in myJson['data'] ) or
                        ( 'status' not in myJson['data'] )):
                        continue
                    #
                    if 'value' not in myJson['data']:
                        myJson['data']['value'] = None
                    if 'detail' not in myJson['data']:
                        myJson['data']['detail'] = None
                elif ( corr_cfg['family'] == "sts" ):
                    # check document has required CMS-Status keys:
                    if (( 'name' not in myJson['data'] ) or
                        ( 'status' not in myJson['data'] ) or
                        ( 'prod_status' not in myJson['data'] ) or
                        ( 'crab_status' not in myJson['data'] ) or
                        ( 'rucio_status' not in myJson['data'] )):
                        continue
                    #
                    if 'manual_life' not in myJson['data']:
                        myJson['data']['manual_life'] = None
                    if 'manual_prod' not in myJson['data']:
                        myJson['data']['manual_prod'] = None
                    if 'manual_crab' not in myJson['data']:
                        myJson['data']['manual_crab'] = None
                    if 'manual_rucio' not in myJson['data']:
                        myJson['data']['manual_rucio'] = None
                    if 'detail' not in myJson['data']:
                        myJson['data']['detail'] = None
                elif ( corr_cfg['family'] == "scap" ):
                    # check document has required CMS-Status keys:
                    if (( 'name' not in myJson['data'] ) or
                        ( 'hs06_pledge' not in myJson['data'] ) or
                        ( 'hs06_per_core' not in myJson['data'] ) or
                        ( 'core_usable' not in myJson['data'] ) or
                        ( 'core_max_used' not in myJson['data'] ) or
                        ( 'core_production' not in myJson['data'] ) or
                        ( 'core_cpu_intensive' not in myJson['data'] ) or
                        ( 'core_io_intensive' not in myJson['data'] ) or
                        ( 'disk_pledge' not in myJson['data'] ) or
                        ( 'disk_usable' not in myJson['data'] ) or
                        ( 'disk_experiment_use' not in myJson['data'] )):
                        continue
                    #
                    if 'wlcg_federation_name' not in myJson['data']:
                        myJson['data']['wlcg_federation_name'] = None
                    if 'wlcg_federation_fraction' not in myJson['data']:
                        myJson['data']['wlcg_federation_fraction'] = None
                    if 'tape_pledge' not in myJson['data']:
                        myJson['data']['tape_pledge'] = 0.0
                    if 'tape_usable' not in myJson['data']:
                        myJson['data']['tape_usable'] = 0.0
                    if 'when' not in myJson['data']:
                        myJson['data']['when'] = None
                    if 'who' not in myJson['data']:
                        myJson['data']['who'] = None
                else:
                    continue
                #
                tbin = int( myJson['timestamp'] / (1000 * corr_cfg['period']) )
                if tbin not in filedocs:
                    filedocs[ tbin ] = []
                filedocs[ tbin ].append( myJson['data'] )

        except json.decoder.JSONDecodeError as excptn:
            logging.error("JSON decoding failure, %s, %s" %
                                                       (filename, str(excptn)))
        except FileNotFoundError as excptn:
            logging.error("File not found, %s, %s" % (filename, str(excptn)))
        except IOError as excptn:
            logging.error("File access failure, %s, %s" %
                                                       (filename, str(excptn)))


    return filedocs
# ########################################################################### #



def corr_monit_upload(cfg, docDict):
    """function to upload corrected documents to MonIT/HDFS"""
    # ####################################################################### #
    # upload documents provided in dictionary of lists as JSON array to MonIT #
    # ####################################################################### #
    CORR_MONIT_HDR = {'Content-Type': "application/json; charset=UTF-8"}
    halfBin = int(cfg['period'] / 2)
    #
    logging.info("Composing JSON array and uploading to MonIT")


    # compose JSON array string:
    # ==========================
    jsonString = "["
    commaFlag = False
    #
    for tbin in docDict:
        centerTIS = int( (tbin * cfg['period']) + halfBin )
        #
        if ( cfg['family'] == "vofeed" ):
            jsonSegmnt = corr_compose_vofeed_json(centerTIS, docDict[tbin] )
        elif ( cfg['family'] == "down" ):
            jsonSegmnt = corr_compose_down_json(centerTIS, docDict[tbin] )
        elif ( cfg['family'] == "sam" ):
            jsonSegmnt = corr_compose_sam_json(cfg['metric'], centerTIS,
                                                                docDict[tbin] )
        elif ( cfg['family'] == "hc" ):
            jsonSegmnt = corr_compose_hc_json(cfg['metric'], centerTIS,
                                                                docDict[tbin] )
        elif ( cfg['family'] == "fts" ):
            jsonSegmnt = corr_compose_fts_json(cfg['metric'], centerTIS,
                                                                docDict[tbin] )
        elif ( cfg['family'] == "sr" ):
            jsonSegmnt = corr_compose_sr_json(cfg['metric'], centerTIS,
                                                                docDict[tbin] )
        elif ( cfg['family'] == "sts" ):
            jsonSegmnt = corr_compose_sts_json(centerTIS, docDict[tbin] )
        elif ( cfg['family'] == "scap" ):
            jsonSegmnt = corr_compose_scap_json(centerTIS, docDict[tbin] )
        #
        if commaFlag:
            jsonString += "," + jsonSegmnt[2:-3]
        else:
            jsonString += jsonSegmnt[2:-3]
        commaFlag = True
    jsonString += "\n]\n"
    #
    if ( jsonString == "[\n]\n" ):
        logging.warning("skipping upload of document-devoid JSON string")
        return False
    #
    jsonString = jsonString.replace("ssbmetric", "metrictest")


    # upload string with JSON document array to MonIT/HDFS:
    # =====================================================
    docs = json.loads(jsonString)
    ndocs = len(docs)
    successFlag = True
    for myOffset in range(0, ndocs, 1024):
        if ( myOffset > 0 ):
            # give importer time to process documents
            time.sleep(2.500)
        # MonIT upload channel can handle at most 10,000 docs at once
        dataString = json.dumps( docs[myOffset:min(ndocs,myOffset+1024)] )
        #
        try:
            # MonIT needs a document array and without newline characters:
            requestObj = urllib.request.Request(CORR_MONIT_URL,
                         data=dataString.encode("utf-8"),
                         headers=CORR_MONIT_HDR, method="POST")
            responseObj = urllib.request.urlopen( requestObj, timeout=90 )
            if ( responseObj.status != http.HTTPStatus.OK ):
                logging.error(("Failed to upload JSON [%d:%d] string to MonI" +
                               "T, %d \"%s\"") %
                              (myOffset, min(ndocs,myOffset+1024),
                               responseObj.status, responseObj.reason))
                successFlag = False
            responseObj.close()
        except urllib.error.URLError as excptn:
            logging.error("Failed to upload JSON [%d:%d], %s" %
                             (myOffset, min(ndocs,myOffset+1024), str(excptn)))
            successFlag = False
    del docs

    if ( successFlag ):
        logging.log(25, "JSON string with %d docs of %s uploaded to MonIT" %
                                                        (ndocs, cfg['metric']))
    return successFlag
# ########################################################################### #



if __name__ == '__main__':
    corr_cfg = {}
    #
    parserObj = argparse.ArgumentParser(description="Script to correct VO-fe" +
        "ed, downtime, SAM, HC, SR, STS, or SCAP metrics. Documents for one " +
        "or more timebin and selected sites/hosts/types can be fetched, edit" +
        "ed, and uploaded.")
    parserObj.add_argument("-n", dest="fname", action="store",
                                 metavar="site/host-name",
                                 help=("select only documents with matching " +
                                       "SAM-site/HC-site/SAM-hostname/..."))
    parserObj.add_argument("-t", dest="ftype", action="store",
                                 metavar="resource-type",
                                 help=("select only documents with matching " +
                                       "SAM/HC resource-type"))
    parserObj.add_argument("-T", dest="bytbin", default=False,
                                 action="store_true",
                                 help=("provide documents for correction one" +
                                       " timebin at a time"))
    parserObj.add_argument("-A", dest="author", action="store",
                                 metavar="author-identification",
                                 help=argparse.SUPPRESS)
    parserObj.add_argument("-U", dest="upload", default=True,
                                 action="store_false",
                                 help=("do not upload to MonIT but print new" +
                                       "document(s) instead"))
    parserObj.add_argument("-v", action="count", default=0,
                                 help="increase verbosity")
    parserObj.add_argument("metric",
                                 metavar="metric-name",
                                 help=("name of the metric to be corrected, " +
                                       "i.e. down15min, sam15min, sam1hour, " +
                                       "sam6hour, sam1day, hc15min, ..."))
    parserObj.add_argument("timeSpec",
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
        logging.basicConfig(datefmt="%H:%M:%S",
                            format="%(asctime)s [%(levelname).1s] %(message)s",
                            level=logging.INFO)
    elif ( argStruct.v == 1 ):
        logging.basicConfig(format="[%(levelname).1s] %(message)s",
                            level=25)
    else:
        logging.basicConfig(format="[%(levelname).1s] %(message)s",
                            level=logging.WARNING)


    # check/handle arguments:
    # =======================
    if argStruct.fname is not None:
        corr_cfg['nameFilter'] = argStruct.fname
    if argStruct.ftype is not None:
        corr_cfg['typeFilter'] = argStruct.ftype
    #
    corr_cfg['by_tbin'] = argStruct.bytbin
    #
    if argStruct.author is not None:
        if ( argStruct.author == "" ):
            corr_cfg['author'] = None
        else:
            corr_cfg['author'] = argStruct.author
    #
    corr_cfg['upload'] = argStruct.upload
    #
    # check correction of metric is supported:
    if argStruct.metric not in CORR_METRIC_NAMES:
        raise SystemExit("Correction of metric %s not supported" %
                                                              argStruct.metric)
    corr_cfg['metric'] = argStruct.metric
    if ( argStruct.metric.find("15min") > 0 ):
        corr_cfg['family'] = argStruct.metric[:-5]
        corr_cfg['period'] = 900
    elif ( argStruct.metric.find("1hour") > 0 ):
        corr_cfg['family'] = argStruct.metric[:-5]
        corr_cfg['period'] = 3600
    elif ( argStruct.metric.find("6hour") > 0 ):
        corr_cfg['family'] = argStruct.metric[:-5]
        corr_cfg['period'] = 21600
    else:
        corr_cfg['family'] = argStruct.metric[:-4]
        corr_cfg['period'] = 86400
    #
    #
    # first time bin for which we need to fetch metric docs:
    if ( argStruct.timeSpec.isdigit() ):
        # argument should be time in seconds of first time bin
        tis = int( argStruct.timeSpec )
    else:
        # argument should be the time in "YYYY-Mmm-dd HH:MM" format
        tis = int( calendar.timegm( time.strptime("%s UTC" %
                   argStruct.timeSpec, "%Y-%b-%d %H:%M %Z") ) )
    corr_cfg['first'] = int( tis / corr_cfg['period'] )
    corr_cfg['start'] = corr_cfg['first'] * corr_cfg['period']
    #
    # last timebin for which we need to fetch metric docs:
    if argStruct.lastSpec is None:
        corr_cfg['last'] = corr_cfg['first']
        corr_cfg['limit'] = corr_cfg['start'] + corr_cfg['period']
        logging.log(25, "Fetching %s docs for time bin %s" %
                     (corr_cfg['metric'], time.strftime("%Y-%b-%d %H:%M",
                                              time.gmtime(corr_cfg['start']))))
    else:
        if ( argStruct.lastSpec.isdigit() ):
            # argument should be time in seconds of last 15 min time bin
            tis = int( argStruct.lastSpec )
        else:
            # argument should be the time in "YYYY-Mmm-dd HH:MM" format
            tis = int( calendar.timegm( time.strptime("%s UTC" %
                       argStruct.lastSpec, "%Y-%b-%d %H:%M %Z") ) )
        corr_cfg['last'] = int( tis / corr_cfg['period'] )
        corr_cfg['limit'] = ( corr_cfg['last'] + 1 ) * corr_cfg['period']
        logging.log(25, "Fetching %s docs for time bins %s to %s" %
                     (corr_cfg['metric'],
                      time.strftime("%Y-%b-%d %H:%M",
                                    time.gmtime(corr_cfg['start'])),
                      time.strftime("%Y-%b-%d %H:%M",
                                    time.gmtime(corr_cfg['limit']))))
    #
    corr_cfg['files'] = []


    # check we have a valid Kerberos ticket available:
    # ================================================
    if not corr_kerberos_check(corr_cfg):
        sys.exit(1)


    # fetch documents for requested timebins from MonIT:
    # ==================================================
    monitDocs = corr_monit_fetch(corr_cfg)


    # write documents of timebins to temporary file(s):
    # =================================================
    corr_write_files(corr_cfg, monitDocs)


    # print correction advice and present docs in editor:
    # ===================================================
    if not corr_advise_edit(corr_cfg):
        sys.exit(1)


    # read in corrected docs:
    # =======================
    correctDocs = corr_parse_files(corr_cfg)


    # filter out docs with identical entries in MonIT:
    # ================================================
    if ( corr_cfg['family'] == "down" ):
        # filter out identical timebins:
        cnt_docs = 0
        for tbin in sorted(correctDocs.keys()):
            if tbin in monitDocs:
                if ( len(correctDocs[tbin]) == len(monitDocs[tbin]) ):
                    identicalFlag = True
                    for doc in correctDocs[tbin]:
                        if doc not in monitDocs[tbin]:
                            identicalFlag = False
                    if ( identicalFlag ):
                        logging.debug(("filtering out (%d) with %d entries a" +
                                      "s timebin has identical entries in Mo" +
                                      "nIT") % (tbin, len(correctDocs[tbin])))
                        del correctDocs[tbin]
                    else:
                        cnt_docs += len( correctDocs[tbin] )
                else:
                    cnt_docs += len( correctDocs[tbin] )
            else:
                cnt_docs += len( correctDocs[tbin] )
    else:
        # filter out identical docs in each timebin:
        cnt_docs = 0
        for tbin in sorted(correctDocs.keys()):
            if tbin in monitDocs:
                for index in range(len(correctDocs[tbin])-1,-1,-1):
                    doc = correctDocs[tbin][index]
                    if doc in monitDocs[tbin]:
                        if (( corr_cfg['family'] == "hc" ) or
                            ( corr_cfg['family'] == "sr" ) or
                            ( corr_cfg['family'] == "sts" ) or
                            ( corr_cfg['family'] == "scap" )):
                            myResID = doc['name']
                        else:
                            myResID = doc['name'] + " / " + doc['type']
                        if ( corr_cfg['family'] == "scap" ):
                            myResST = ("%d/%.1f/%.1f" % (doc['core_usable'],
                                       doc['disk_usable'], doc['tape_usable']))
                        else:
                            myResST = doc['status']
                        logging.debug(("filtering out (%d) %s: %s as identic" +
                                       "al entry exists in MonIT") % (tbin,
                                                             myResID, myResST))
                        del correctDocs[tbin][index]
                    else:
                        cnt_docs += 1
                if ( len(correctDocs[tbin]) == 0 ):
                    # no documents left in timebin:
                    del correctDocs[tbin]
            else:
                cnt_docs += len( correctDocs[tbin] )


    # upload corrected document(s) to MonIT:
    # ======================================
    if ( cnt_docs > 0 ):
        if ( argStruct.upload ):
            successFlag = corr_monit_upload(corr_cfg, correctDocs)
        else:
            successFlag = False
        #
        if ( successFlag ):
            for filename in corr_cfg['files']:
                os.unlink(filename)
        else:
            filestrng = ""
            for filename in corr_cfg['files']:
                filestrng += filename + " "
            logging.log(25, "Keeping edited correction file(s) %s" %
                                                                filestrng[:-1])
    else:
        logging.warning("No corrected/revised documents")
        for filename in corr_cfg['files']:
            os.unlink(filename)

    #import pdb; pdb.set_trace()
