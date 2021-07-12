#!/eos/user/c/cmssst/packages/bin/python3.7
# ########################################################################### #
# python CGI script to fetch and update Rebus pledge information, glide-in    #
#    WMS monitor core usage information, to fetch, and to upload SiteCapacity #
#    information from/into CERN MonIT.                                        #
#                                                                             #
# 2020-Jan-30   Stephan Lammel                                                #
# ########################################################################### #
#
# [
#  {
#   "name": "T0_CH_CERN",
#    "wlcg_federation_name": "CH-CERN",      # by site admin/exec
#    "wlcg_federation_fraction": 1.000,      # by site admin/exec
#    "hs06_pledge": 423000,                  # by Rebus
#    "hs06_per_core": 10.000,                # default or site admin/exec
#    "core_usable": 31700,
#    "core_max_used": 12100,                 # by gwmsmon, SSB#136/Real [cores]
#    "core_production": 12100,               # auto or site admin/exec
#    "core_cpu_intensive": 22467,            # by site admin/exec, SSB#160
#    "core_io_intensive": 1350,              # by site admin/exec, SSB#161
#    "disk_pledge": 26100.0,                 # by Rebus
#    "disk_usable": 26100.0,
#    "disk_experiment_use": 0.0,
#    "disk_local_use": 0.0,
#    "tape_pledge": 99000.0,
#    "tape_usable": 99000.0,
#    "when": "2019-Jan-17 22:12:00",
#    "who": "lammel"
#  }, ...
# ]



import os, sys
import fcntl
import argparse
import logging
import time, calendar
import math
import socket
import urllib.request, urllib.error
import http
import json
import re
import gzip
#
# setup the Java/HDFS/PATH environment for pydoop to work properly:
os.environ["HADOOP_CONF_DIR"] = "/opt/hadoop/conf/etc/analytix/hadoop.analytix"
os.environ["JAVA_HOME"]       = "/etc/alternatives/jre"
os.environ["HADOOP_PREFIX"]   = "/usr/hdp/hadoop"
import pydoop.hdfs
# ########################################################################### #



CAPA_LOCK_PATH = "/eos/home-c/cmssst/www/capacity/update.lock"
CAPA_FILE_PATH = "/eos/home-c/cmssst/www/capacity/SiteCapacity.json"
CAPA_CACHE_DIR = "/data/cmssst/MonitoringScripts/capacity/cache"
CAPA_BCKUP_DIR = "/data/cmssst/MonitoringScripts/capacity/failed"
# ########################################################################### #



def capa_cric_cmssites():
    # ##################################### #
    # return list with valid CMS site names #
    # ##################################### #
    URL_CRIC_SITES = "https://cms-cric.cern.ch/api/cms/site/query/?json"
    #
    siteRegex = re.compile(r"T\d_[A-Z]{2,2}_\w+")

    logging.info("Fetching CMS site list from CRIC")
    try:
        with urllib.request.urlopen(URL_CRIC_SITES) as urlHandle:
            urlCharset = urlHandle.headers.get_content_charset()
            if urlCharset is None:
                urlCharset = "utf-8"
            myData = urlHandle.read().decode( urlCharset )
        #
        # sanity check:
        if ( len(myData) < 65536 ):
            raise ValueError("CRIC site query result failed sanity check")
        #
        # decode JSON:
        myDict = json.loads( myData )
        del myData
        #
        # loop over entries and add site with facility name:
        siteList = set()
        for myKey in myDict:
            site = myDict[myKey]['name']
            if ( siteRegex.match( site ) is None ):
                continue
            #
            if (( site[-5:] == "_Disk" ) or ( site[-7:] == "_Buffer" ) or
                ( site[-7:] == "_Export" ) or ( site[-4:] == "_MSS" )):
                continue
            #
            siteList.add( site )
        del myDict
        siteList = sorted( siteList )
        #
        #
        # compose JSON string:
        jsonString = "["
        commaFlag = False
        for site in siteList:
            if commaFlag:
                jsonString += ",\n   \"%s\"" % site
            else:
                jsonString += "\n   \"%s\"" % site
            commaFlag = True
        jsonString += "\n]\n"
        #
        # update cache:
        cacheFile = CAPA_CACHE_DIR + "/cric_cmssites.json"
        try:
            with open(cacheFile + "_new", 'w') as myFile:
                myFile.write( jsonString )
            os.rename(cacheFile + "_new", cacheFile)
        except:
            pass
        del jsonString
        #
        logging.log(25, "CMS site list cache updated")
    except Exception as excptn:
        logging.error("Failed to fetch CMS site list from CRIC: %s" %
                                                                   str(excptn))
        #
        cacheFile = CAPA_CACHE_DIR + "/cric_cmssites.json"
        try:
            with open(cacheFile, 'rt') as myFile:
                myData = myFile.read()
            #
            # decode JSON:
            siteList = json.loads( myData )
            del myData
        except:
            logging.critical("Failed to read CMS site list cache")
            return []
        #
    return siteList
# ########################################################################### #



def capa_cric_pledges():
    # ####################################### #
    # return dictionary of federation pledges #
    # ####################################### #
    URL_CRIC_PLDG = "https://wlcg-cric.cern.ch/api/core/federation/query/?json&start_year=%d"
    #
    now = int( time.time() )
    # a WLCG pledge year starts April 1st, so quarters are shifted by one
    month = time.gmtime(now)[1]
    if (( month >= 1 ) and ( month <= 3 )):
        monthStrng = "Q4"
        yearStrng = "%d" % (time.gmtime(now)[0] - 1)
        prevYear = time.gmtime(now)[0] - 2
    elif (( month >= 4 ) and ( month <= 6 )):
        monthStrng = "Q1"
        yearStrng = "%d" % time.gmtime(now)[0]
        prevYear = time.gmtime(now)[0] - 1
    elif (( month >= 7 ) and ( month <= 9 )):
        monthStrng = "Q2"
        yearStrng = "%d" % time.gmtime(now)[0]
        prevYear = time.gmtime(now)[0] - 1
    else:
        monthStrng = "Q3"
        yearStrng = "%d" % time.gmtime(now)[0]
        prevYear = time.gmtime(now)[0] - 1
    del month

    logging.info("Fetching WLCG federation pledges from CRIC")
    try:
        with urllib.request.urlopen(URL_CRIC_PLDG % prevYear) as urlHandle:
            urlCharset = urlHandle.headers.get_content_charset()
            if urlCharset is None:
                urlCharset = "utf-8"
            myData = urlHandle.read().decode( urlCharset )
        #
        # sanity check:
        if ( len(myData) < 16384 ):
            raise ValueError("WLCG federation pledges data failed sanity check")
        #
        # decode JSON:
        myDict = json.loads( myData )
        del myData
        #
        # loop over entries and add WLCG federation pledges to dictionary:
        pledgesDict = {}
        for myKey in myDict:
            try:
                federation = myDict[ myKey ]['name']
                pledges = myDict[ myKey ]['pledges'][yearStrng][monthStrng]
                if 'CPU' in pledges['cms']:
                    pldg_hs06 = round( float( pledges['cms']['CPU'] ), 3)
                else:
                    pldg_hs06 = 0
                if 'Disk' in pledges['cms']:
                    pldg_disk = round( float( pledges['cms']['Disk'] ), 3)
                else:
                    pldg_disk = 0.0
                if 'Tape' in pledges['cms']:
                    pldg_tape = round( float( pledges['cms']['Tape'] ), 3)
                else:
                    pldg_tape = 0.0
            except KeyError:
                continue
            if (( federation is None ) or ( federation == "" )):
                continue
            logging.debug("Pledge for \"%s\": %.1f / %.1f / %.1f" %
                                 (federation, pldg_hs06, pldg_disk, pldg_tape))
            pledgesDict[federation] = { 'hs06': pldg_hs06, 'disk': pldg_disk,
                                                           'tape': pldg_tape }
        del myDict
    except Exception as excptn:
        logging.error("Failed to fetch WLCG federation pledges from CRIC: %s" %
                                                                   str(excptn))
        return {}
    #
    return pledgesDict
# ########################################################################### #



def capa_gwmsmon_usage():
    # ##################################################### #
    # return dictionary of max cores used during last month #
    # ##################################################### #
    URL_GWMS_USAGE = "http://cms-gwmsmon.cern.ch/totalview/json/maxused"
    #
    siteRegex = re.compile(r"T\d_[A-Z]{2,2}_\w+")

    logging.info("Fetching max core usage information from gWMSmon")
    try:
        with urllib.request.urlopen(URL_GWMS_USAGE) as urlHandle:
            urlCharset = urlHandle.headers.get_content_charset()
            if urlCharset is None:
                urlCharset = "utf-8"
            myData = urlHandle.read().decode( urlCharset )
        #
        # sanity check:
        if ( len(myData) < 32768 ):
            raise ValueError("gWMSmon max core usage data failed sanity check")
        #
        # decode JSON:
        myDict = json.loads( myData )
        del myData
        #
        # loop over entries and add max one month usage to dictionary:
        usageDict = {}
        for mySite in myDict:
            if ( siteRegex.match( mySite ) is None ):
                continue
            try:
                usage = int( myDict[mySite]['onemonth'] )
            except KeyError:
                continue
            logging.debug("Core Usage for \"%s\": %d" % (mySite, usage))
            usageDict[ mySite ] = usage
        del myDict
    except Exception as excptn:
        logging.error("Failed to fetch max core usage from gWMSmon: %s" %
                                                                   str(excptn))
        return {}
    #
    return usageDict
# ########################################################################### #



def capa_startd_usage():
    # ##################################################### #
    # return dictionary of max cores used during last month #
    # ##################################################### #
    URL_GRAFANA = "https://monit-grafana.cern.ch/api/datasources/proxy/9668/_msearch?filter_path=responses.aggregations.cpus_per_site.buckets.key,responses.aggregations.cpus_per_site.buckets.max_cpus_a.value,responses.aggregations.cpus_per_site.buckets.max_cpus_b.value"
    HDR_GRAFANA = {'Authorization': "Bearer eyJrIjoiZWRnWXc1bUZWS0kwbWExN011TGNTN2I2S1JpZFFtTWYiLCJuIjoiY21zLXNzYiIsImlkIjoxMX0=", 'Content-Type': "application/json; charset=UTF-8"}
    #
    siteRegex = re.compile(r"T\d_[A-Z]{2,2}_\w+")
    #
    logging.info("Fetching max core usage count of startds via Grafana")

    # prepare Lucene ElasticSearch query:
    # ===================================
    today = int( time.time() / 86400 )
    startTIS = ( today - 30 ) * 86400
    limitTIS = today * 86400
    queryString = ("{\"search_type\":\"query_then_fetch\",\"index\":[\"monit" +
                   "_prod_cms_raw_si_condor_*\"],\"ignore_unavailable\":true" +
                   "}\n{\"query\":{\"bool\":{\"must\":[{\"match_phrase\":{\"" +
                   "metadata.topic\":\"cms_raw_si_condor_startd\"}}],\"must_" +
                   "not\":[{\"match_phrase\":{\"data.payload.SlotType\":\"Dy" +
                   "namic\"}}],\"filter\":{\"range\":{\"metadata.timestamp\"" +
                   ":{\"gte\":%d,\"lt\":%d,\"format\":\"epoch_second\"}}}}}," +
                   "\"size\":0,\"aggs\":{\"cpus_per_site\":{\"terms\":{\"fie" +
                   "ld\":\"data.payload.GLIDEIN_CMSSite\",\"size\":512},\"ag" +
                   "gs\":{\"cpus_per_report_a\":{\"date_histogram\":{\"field" +
                   "\":\"metadata.timestamp\",\"interval\":\"360s\",\"offset" +
                   "\":\"0s\"},\"aggs\":{\"cpus\":{\"sum\":{\"field\":\"data" +
                   ".payload.TotalSlotCpus\"}}}},\"cpus_per_report_b\":{\"da" +
                   "te_histogram\":{\"field\":\"metadata.timestamp\",\"inter" +
                   "val\":\"360s\",\"offset\":\"180s\"},\"aggs\":{\"cpus\":{" +
                   "\"sum\":{\"field\":\"data.payload.TotalSlotCpus\"}}}},\"" +
                   "max_cpus_a\":{\"max_bucket\":{\"buckets_path\":\"cpus_pe" +
                   "r_report_a>cpus\"}},\"max_cpus_b\":{\"max_bucket\":{\"bu" +
                   "ckets_path\":\"cpus_per_report_b>cpus\"}}}}}}\n") % \
                                                           (startTIS, limitTIS)

    # fetch startd max core usage count from ElasticSearch:
    # =====================================================
    try:
        requestObj = urllib.request.Request(URL_GRAFANA,
                                            data=queryString.encode("utf-8"),
                                            headers=HDR_GRAFANA, method="POST")
        with urllib.request.urlopen( requestObj, timeout=90 ) as responseObj:
            urlCharset = responseObj.headers.get_content_charset()
            if urlCharset is None:
                urlCharset = "utf-8"
            myData = responseObj.read().decode( urlCharset )
            del urlCharset
        #
        # sanity check:
        if ( len(myData) < 2048 ):
            raise ValueError("Startd max core usage data failed sanity check")
        #
        # decode JSON:
        myJson = json.loads( myData )
        del myData
        #
        # loop over entries and add max one month usage to dictionary:
        usageDict = {}
        for myRspns in myJson['responses']:
            for myBuckt in myRspns['aggregations']['cpus_per_site']['buckets']:
                try:
                    mySite = myBuckt['key']
                    if ( siteRegex.match( mySite ) is None ):
                        continue
                    myUsage = int( max( myBuckt['max_cpus_a']['value'],
                                        myBuckt['max_cpus_b']['value'] ) )
                except KeyError:
                    logging.warning("Missing key in ES bucket, skipping, %s" %
                                                                   str(excptn))
                    continue
                logging.debug("Core Usage for \"%s\": %d" % (mySite, myUsage))
                usageDict[ mySite ] = myUsage
        del myJson
    except urllib.error.URLError as excptn:
        logging.error("Failed to query ElasticSearch via Grafana, %s" %
                                                                   str(excptn))
        return {}
    #
    return usageDict
# ########################################################################### #



def capa_dynamo_quota():
    # ##################################################################### #
    # return dictionary of current experiment disk quota settings in Dynamo #
    # ##################################################################### #
    URL_DDM_QUOTA = "http://t3serv001.mit.edu/~cmsprod/IntelROCCS/Detox/SitesInfo.csv"
    #
    siteRegex = re.compile(r"T\d_[A-Z]{2,2}_\w+")

    logging.info("Fetching experiment disk quota settings from Dynamo")
    try:
        with urllib.request.urlopen(URL_DDM_QUOTA) as urlHandle:
            urlCharset = urlHandle.headers.get_content_charset()
            if urlCharset is None:
                urlCharset = "utf-8"
            myData = urlHandle.read().decode( urlCharset )
        #
        # sanity check:
        if ( len(myData) < 256 ):
            raise ValueError("Dynamo experiment disk quota failed sanity check")
        #
        # loop over lines and add experiment disk quota to dictionary:
        quotaDict = {}
        for myLine in myData.splitlines():
            myEntries = myLine.split(",")
            mySite = myEntries[-1]
            if ( siteRegex.match( mySite ) is None ):
                continue
            try:
                myQuota = int( 2.0 * float(myEntries[2]) ) / 2.0
            except KeyError:
                continue
            logging.debug("Experiment quota for \"%s\": %d" % (mySite, myQuota))
            quotaDict[ mySite ] = myQuota
    except Exception as excptn:
        logging.error("Failed to fetch experiment disk quota from Dynamo: %s" %
                                                                   str(excptn))
        return {}
    #
    return quotaDict
# ########################################################################### #



def capa_rucio_quotas():
    # ##################################################################### #
    # return dictionary of current experiment and local disk quota settings #
    # in Rucio                                                              #
    # ##################################################################### #
    os.environ["RUCIO_HOME"] = "/eos/user/c/cmssst/packages"
    #
    import getpass
    import rucio.client.client
    import rucio.common.exception
    #
    siteRegex = re.compile(r"T\d_[A-Z]{2,2}_\w+")

    logging.info("Fetching experiment/local disk quota settings from Rucio")
    quotaDict = {}
    #
    try:
        # initialize Rucio client for current username:
        myUser = getpass.getuser()
        rcoClient=rucio.client.client.Client(account=myUser)

        # loop over Rucio Storage Elements:
        for rseName in [ d['rse'] for d in rcoClient.list_rses()
                                  if ( d['rse_type'] == "DISK" ) ]:
            # filter out all but "real" "production" RSEs:
            try:
                rseAttributes = rcoClient.list_rse_attributes(rseName)
                if ( rseAttributes['cms_type'] != "real" ):
                    continue
                if ( rseAttributes['sitestatus_ignore'] == True ):
                    continue
            except (KeyError, rucio.common.exception.RucioException):
                pass

            # get total space, "static" RSE usage:
            rseUsages = rcoClient.get_rse_usage(rseName, {'source': "static"})
            try:
                myValue = next(iter(rseUsages))['total']
                if ( myValue is not None ):
                    # convert to TeraBytes with 100 GB precision
                    totalSpc = int( myValue / 100000000000 ) / 10.0
                else:
                    totalSpc = 0.0
            except (TypeError, KeyError, StopIteration, \
                    rucio.common.exception.RucioException):
                totalSpc = 0.0

            # derive sitename from RSE name:
            if (( rseName.endswith('_Disk') ) or
                ( rseName.endswith('_Ceph') )):
                mySite = rseName[:-5]
            else:
                mySite = rseName

            # get local space, limit of lowercase(sitename)_local_users account:
            rseAccount = mySite.lower() + "_local_users"
            if ( len(rseAccount) > 25 ):
               rseAccount = mySite.lower() + "_local"
               if ( len(rseAccount) > 25 ):
                   rseAccount = mySite[:19].lower() + "_local"
            try:
                myValue = next(iter(rcoClient.get_account_limits(rseAccount,
                                                   rseName, "local").values()))
                if ( myValue is not None ):
                    # convert to TeraBytes with 100 GB precision
                    lclQuota = int( myValue / 100000000000 ) / 10.0
                else:
                    lclQuota = 0.0
            except (TypeError, StopIteration, \
                    rucio.common.exception.RucioException):
                lclQuota = 0.0

            expQuota = max(0.0, totalSpc - lclQuota)

            # check site naming convention
            if ( siteRegex.match( mySite ) is None ):
                logging.warning(("RSE %s (real/production) with %.1f/%.1f qu" \
                                 "ota") % (rseName, expQuota, lclQuota))
                continue
            logging.debug("RSE %s experiment %.1f / local %.1f quotas" % \
                                                 (rseName, expQuota, lclQuota))
            try:
                if ( quotaDict[ mySite ] == (0.0, 0.0) ):
                    quotaDict[ mySite ] = (expQuota, lclQuota)
                elif (( expQuota != 0.0 ) or ( lclQuota != 0.0 )):
                    logging.warning(("Multiple disk quotas for site %s (%.1f" \
                                     "/%.1f) and (%.1f/%.1f)") % (mySite,
                                     quotaDict[ mySite ][0],
                                     quotaDict[ mySite ][1],
                                     expQuota, lclQuota))
                    # choose RSE with larger quota for experiment use:
                    if ( expQuota > quotaDict[ mySite ][0] ):
                        quotaDict[ mySite ] = (expQuota, lclQuota)
            except KeyError:
                # first RSE for site:
                quotaDict[ mySite ] = (expQuota, lclQuota)
    except Exception as excptn:
        logging.error(("Failed to fetch experiment/local disk quota from Ruc" \
                       "io: %s") % str(excptn))
    #
    return quotaDict
# ########################################################################### #



def capa_read_jsonfile():
    """read SiteCapacity and return contents as dictionary of dictionaries"""
    # ####################################################################### #

    logging.info("Reading SiteCapacity file, %s" % CAPA_FILE_PATH)
    # acquire lock to read JSON file:
    remainWait = 5.0
    while ( remainWait > 0.0 ):
        with open(CAPA_LOCK_PATH, 'w') as lckFile:
            try:
                fcntl.lockf(lckFile, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError:
                logging.log(25, "Lock busy, retry in 250 msec")
                sleep(0.250)
                remainWait -= 0.250
                continue
            #
            with open(CAPA_FILE_PATH, 'rt') as myFile:
                jsonString = myFile.read()
            #
            fcntl.lockf(lckFile, fcntl.LOCK_UN)
            break
    if ( remainWait <= 0.0 ):
        raise TimeoutError("Failed to acquire lock, %s" % CAPA_LOCK_PATH)
    #
    # decode JSON:
    capacityList = json.loads( jsonString )
    del jsonString
    #
    # check SiteCapacity entries:
    for myEntry in capacityList:
        if ( 'name' not in myEntry ):
            logging.error("Missing key(s) in capacity entry \"%s\" of %s" %
                                                (str(myEntry), CAPA_FILE_PATH))
            continue
        if 'wlcg_federation_name' not in myEntry:
            myEntry['wlcg_federation_name'] = None
        if 'wlcg_federation_fraction' not in myEntry:
            myEntry['wlcg_federation_fraction'] = 1.000
        if 'hs06_pledge' not in myEntry:
            myEntry['hs06_pledge'] = 0
        if 'hs06_per_core' not in myEntry:
            myEntry['hs06_per_core'] = 10.000
        if 'core_usable' not in myEntry:
            myEntry['core_usable'] = 0
        if 'core_max_used' not in myEntry:
            myEntry['core_max_used'] = 0
        if 'core_production' not in myEntry:
            myEntry['core_production'] = 0
        if 'core_cpu_intensive' not in myEntry:
            myEntry['core_cpu_intensive'] = 0
        if 'core_io_intensive' not in myEntry:
            myEntry['core_io_intensive'] = 0
        if 'disk_pledge' not in myEntry:
            myEntry['disk_pledge'] = 0.0
        if 'disk_usable' not in myEntry:
            myEntry['disk_usable'] = 0.0
        if 'disk_experiment_use' not in myEntry:
            myEntry['disk_experiment_use'] = 0.0
        if 'disk_local_use' not in myEntry:
            myEntry['disk_local_use'] = 0.0
        if 'tape_pledge' not in myEntry:
            myEntry['tape_pledge'] = 0.0
        if 'tape_usable' not in myEntry:
            myEntry['tape_usable'] = 0.0
        if 'when' not in myEntry:
            myEntry['when'] = None
        if 'who' not in myEntry:
            myEntry['who'] = None

    return capacityList
# ########################################################################### #



def capa_compose_json(capacityList, time15bin, noWho):
    """function to compose a JSON string from the list of site capacities"""
    # ##################################################################### #
    # compose a JSON string from the list of capacity dictionaries provided #
    # ##################################################################### #

    jsonString = "["
    commaFlag = False
    #
    if  time15bin is not None:
        timestamp = ( time15bin * 900 ) + 450
        hdrString = ((",\n {\n   \"producer\": \"cmssst\",\n" +
                             "   \"type\": \"ssbmetric\",\n" +
                             "   \"path\": \"scap15min\",\n" +
                             "   \"timestamp\": %d000,\n" +
                             "   \"type_prefix\": \"raw\",\n" +
                             "   \"data\": {\n") % timestamp)
        spcStrng = "      "
    else:
        spcStrng = "   "
    tmpDict = { e['name']:e for e in capacityList }
    #
    for myName in sorted( tmpDict.keys() ):
        if (( time15bin is not None ) and commaFlag ):
            jsonString += hdrString
        elif time15bin is not None:
            jsonString += hdrString[1:]
        elif ( commaFlag ):
            jsonString += ",\n {\n"
        else:
            jsonString += "\n {\n"
        #
        jsonString += ("%s\"name\": \"%s\",\n" % (spcStrng,
                                                      tmpDict[myName]['name']))
        if (( 'wlcg_federation_name' in tmpDict[myName] ) and
            ( tmpDict[myName]['wlcg_federation_name'] is not None )):
            jsonString += ("%s\"wlcg_federation_name\": \"%s\",\n" %
                           (spcStrng, tmpDict[myName]['wlcg_federation_name']))
        else:
            jsonString += "%s\"wlcg_federation_name\": null,\n" % spcStrng
        if (( 'wlcg_federation_fraction' in tmpDict[myName] ) and
            ( tmpDict[myName]['wlcg_federation_fraction'] is not None )):
            jsonString += ("%s\"wlcg_federation_fraction\": %.3f,\n" %
                       (spcStrng, tmpDict[myName]['wlcg_federation_fraction']))
        else:
            jsonString += "%s\"wlcg_federation_fraction\": 1.000,\n" % spcStrng
        if (( 'hs06_pledge' in tmpDict[myName] ) and
            ( tmpDict[myName]['hs06_pledge'] is not None )):
            jsonString += ("%s\"hs06_pledge\": %d,\n" %
                                    (spcStrng, tmpDict[myName]['hs06_pledge']))
        else:
            jsonString += "%s\"hs06_pledge\": 0,\n" % spcStrng
        if (( 'hs06_per_core' in tmpDict[myName] ) and
            ( tmpDict[myName]['hs06_per_core'] is not None )):
            jsonString += ("%s\"hs06_per_core\": %.3f,\n" %
                                  (spcStrng, tmpDict[myName]['hs06_per_core']))
        else:
           jsonString += "%s\"hs06_per_core\": 10.000,\n" % spcStrng
        for cpctyKey in ['core_usable', 'core_max_used', 'core_production', \
                         'core_cpu_intensive', 'core_io_intensive' ]:
            if (( cpctyKey in tmpDict[myName] ) and
                ( tmpDict[myName][cpctyKey] is not None )):
                jsonString += ("%s\"%s\": %d,\n" %
                               (spcStrng, cpctyKey, tmpDict[myName][cpctyKey]))
            else:
                jsonString += "%s\"%s\": 0,\n" % (spcStrng, cpctyKey)
        for cpctyKey in ['disk_pledge', 'disk_usable', 'disk_experiment_use', \
                         'disk_local_use', 'tape_pledge', 'tape_usable' ]:
            if (( cpctyKey in tmpDict[myName] ) and
                ( tmpDict[myName][cpctyKey] is not None )):
                jsonString += ("%s\"%s\": %.1f,\n" %
                               (spcStrng, cpctyKey, tmpDict[myName][cpctyKey]))
            else:
                jsonString += "%s\"%s\": 0.0,\n" % (spcStrng, cpctyKey)
        
        if (( 'when' in tmpDict[myName] ) and
            ( tmpDict[myName]['when'] is not None )):
            jsonString += ("%s\"when\": \"%s\",\n" %
                                           (spcStrng, tmpDict[myName]['when']))
        else:
            jsonString += "%s\"when\": null,\n" % spcStrng
        if ( noWho == True ):
            jsonString += "%s\"who\": null\n" % spcStrng
        elif (( 'who' in tmpDict[myName] ) and
            ( tmpDict[myName]['who'] is not None )):
            jsonString += ("%s\"who\": \"%s\"\n" %
                                            (spcStrng, tmpDict[myName]['who']))
        else:
            jsonString += "%s\"who\": null\n" % spcStrng
        if time15bin is not None:
            jsonString += "   }\n }"
        else:
            jsonString += " }"
        commaFlag = True
    jsonString += "\n]\n"
    #
    return jsonString
# ########################################################################### #



def capa_update_jsonfile(siteList, pledgesDict, quotaDict, usageDict):
    """update the site capacity file with pledges and/or usage"""
    # ##################################################################### #
    # read the SiteCapacity JSON file, update the information for valid CMS #
    # sites with pledge and/or usage data, write out the new/updated site   #
    # site capacity information, and return in a site capacity dictionary.  #
    # ##################################################################### #

    if (( pledgesDict is not None ) or ( quotaDict is not None ) or
                                       ( usageDict is not None )):
        logging.info("Updating pledge/quota/usage in SiteCapacity file, %s" %
                                                                CAPA_FILE_PATH)
    else:
        return capa_read_jsonfile()
    if ((( usageDict is not None ) or ( quotaDict is not None )) and
                                             ( siteList is None)):
        logging.warning("Core usage/Experiment quota update limited to exist" +
                        "ing site entries!")
    if pledgesDict is None:
        pledgesDict = {}
    if quotaDict is None:
        quotaDict = {}
    if usageDict is None:
        usageDict = {}
    #
    # acquire lock and read capacity file:
    remainWait = 5.0
    while ( remainWait > 0.0 ):
        with open(CAPA_LOCK_PATH, 'w') as lckFile:
            try:
                fcntl.lockf(lckFile, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError:
                logging.log(25, "Lock busy, retry in 250 msec")
                sleep(0.250)
                remainWait -= 0.250
                continue
            #
            #
            try:
                with open(CAPA_FILE_PATH, 'r+t') as myFile:
                    #
                    jsonString = myFile.read()
                    #
                    capacityList = json.loads( jsonString )
                    #
                    #
                    tmpSet = set( e['wlcg_federation_name']
                                  for e in capacityList
                                  if (('wlcg_federation_name' in e) and
                                      (e['wlcg_federation_name'] is not None)) )
                    for myKey in pledgesDict:
                        if myKey in tmpSet:
                            for myEntry in capacityList:
                                if (( 'wlcg_federation_name' in myEntry ) and
                                    ( myEntry['wlcg_federation_name'] ==
                                                                      myKey )):
                                    try:
                                       fractn = \
                                            myEntry['wlcg_federation_fraction']
                                    except KeyError:
                                       fractn = 1.000
                                    myEntry['hs06_pledge'] = int( (fractn *
                                            pledgesDict[myKey]['hs06']) + 0.5 )
                                    myEntry['disk_pledge'] = int(2.0 * (fractn
                                           * pledgesDict[myKey]['disk'])) / 2.0
                                    myEntry['tape_pledge'] = int(2.0 * (fractn
                                           * pledgesDict[myKey]['tape'])) / 2.0
                                    logging.log(15, ("Pledge for %s updated:" +
                                                     " %.1f, %.1f, %.1f") %
                                                              (myEntry['name'],
                                                        myEntry['hs06_pledge'],
                                                        myEntry['disk_pledge'],
                                                       myEntry['tape_pledge']))
                    del tmpSet
                    #
                    #
                    if siteList is None:
                        siteList = [ e['name'] for e in capacityList ]
                    tmpDict = { e['name']:e for e in capacityList }
                    for myKey in quotaDict:
                        if myKey not in siteList:
                            continue
                        if myKey in tmpDict:
                            if (( type( quotaDict[myKey] ) is tuple ) or
                                ( type( quotaDict[myKey] ) is list )):
                                # experiment and local quota in Rucio:
                                tmpDict[myKey]['disk_experiment_use'] = \
                                                            quotaDict[myKey][0]
                                tmpDict[myKey]['disk_local_use'] = \
                                                            quotaDict[myKey][1]
                                logging.log(15, ("Experiment/local disk quot" \
                                                "a for %s updated to: %.1f/" \
                                                "%.1f") % (myKey,
                                     quotaDict[myKey][0], quotaDict[myKey][1]))
                            else:
                                # experiment quota in DDM:
                                tmpDict[myKey]['disk_experiment_use'] = \
                                                               quotaDict[myKey]
                                logging.log(15, ("Experiment disk quota for " \
                                                 "%s updated to %.1f") % (myKey,
                                                             quotaDict[myKey]))
                        elif (( type( quotaDict[myKey] ) is tuple ) or
                              ( type( quotaDict[myKey] ) is list )):
                            if (( quotaDict[myKey][0] > 0.0 ) or
                                ( quotaDict[myKey][1] > 0.0 )):
                                # experiment and local quota in Rucio:
                                capacityList.append( {
                                    'name':                     myKey,
                                    'wlcg_federation_name':     None,
                                    'wlcg_federation_fraction': 1.000,
                                    'hs06_pledge':              0,
                                    'hs06_per_core':            10.000,
                                    'core_usable':              0,
                                    'core_max_used':            0,
                                    'core_production':          0,
                                    'core_cpu_intensive':       0,
                                    'core_io_intensive':        0,
                                    'disk_pledge':              0.0,
                                    'disk_usable':              0.0,
                                    'disk_experiment_use': quotaDict[myKey][0],
                                    'disk_local_use':      quotaDict[myKey][1],
                                    'tape_pledge':              0.0,
                                    'tape_usable':              0.0,
                                    'when':                     None,
                                    'who':                      None } )
                                logging.log(15, ("Experiment/local disk quot" \
                                                "a for %s set to: %.1f/%.1f") %
                                                (myKey, quotaDict[myKey][0],
                                                          quotaDict[myKey][1]))
                        elif ( quotaDict[myKey] > 0.0 ):
                            # experiment quota in DDM:
                            capacityList.append( {
                                'name':                     myKey,
                                'wlcg_federation_name':     None,
                                'wlcg_federation_fraction': 1.000,
                                'hs06_pledge':              0,
                                'hs06_per_core':            10.000,
                                'core_usable':              0,
                                'core_max_used':            0,
                                'core_production':          0,
                                'core_cpu_intensive':       0,
                                'core_io_intensive':        0,
                                'disk_pledge':              0.0,
                                'disk_usable':              0.0,
                                'disk_experiment_use':    quotaDict[myKey],
                                'disk_local_use':           0.0,
                                'tape_pledge':              0.0,
                                'tape_usable':              0.0,
                                'when':                     None,
                                'who':                      None } )
                            logging.log(15, ("Experiment disk quota for %s s" +
                                             "et to: %.1f") % (myKey,
                                                             quotaDict[myKey]))
                    del tmpDict
                    #
                    #
                    if siteList is None:
                        siteList = [ e['name'] for e in capacityList ]
                    tmpDict = { e['name']:e for e in capacityList }
                    for myKey in usageDict:
                        if myKey not in siteList:
                            continue
                        if ( myKey == "T0_CH_CERN" ):
                            continue
                        if myKey in tmpDict:
                            tmpDict[myKey]['core_max_used'] = usageDict[myKey]
                            logging.log(15, "Core usage for %s updated to %d" %
                                                     (myKey, usageDict[myKey]))
                        elif ( usageDict[myKey] != 0 ):
                            capacityList.append( {
                                'name':                     myKey,
                                'wlcg_federation_name':     None,
                                'wlcg_federation_fraction': 1.000,
                                'hs06_pledge':              0,
                                'hs06_per_core':            10.000,
                                'core_usable':              0,
                                'core_max_used':            usageDict[myKey],
                                'core_production':          0,
                                'core_cpu_intensive':       0,
                                'core_io_intensive':        0,
                                'disk_pledge':              0.0,
                                'disk_usable':              0.0,
                                'disk_experiment_use':      0.0,
                                'disk_local_use':           0.0,
                                'tape_pledge':              0.0,
                                'tape_usable':              0.0,
                                'when':                     None,
                                'who':                      None } )
                            logging.log(15, "Core usage for %s set to: %d" %
                                                     (myKey, usageDict[myKey]))
                    del tmpDict
                    #
                    #
                    jsonString = capa_compose_json(capacityList, None, False)
                    #
                    myFile.seek(0)
                    myFile.write(jsonString)
                    myFile.truncate()
                    #
                logging.info("Successfully updated SiteCapacity file, %s" %
                                                                CAPA_FILE_PATH)
            except Exception as excptn:
                logging.error("Failed to update SiteCapacity file %s, %s" %
                                                 (CAPA_FILE_PATH, str(excptn)))
                return
            #
            fcntl.lockf(lckFile, fcntl.LOCK_UN)
            break
    if ( remainWait <= 0.0 ):
        logging.error("Timeout acquiring lock %s" % CAPA_LOCK_PATH)

    return capacityList
# ########################################################################### #



def capa__monit_fetch(time15bin=None):
    """function to fetch SiteCapacity docs from MonIT/HDFS"""
    # ################################################################## #
    # fetch SiteCapacity document from MonIT covering bin15min or latest #
    # ################################################################## #
    HDFS_PREFIX = "/project/monitoring/archive/cmssst/raw/ssbmetric/"
    #
    now = int( time.time() )
    sixDaysAgo = calendar.timegm( time.gmtime(now - (6 * 86400)) )
    #
    # metric covering 15min timesbin could be at midnight, fetch 1 extra day:
    if time15bin is None:
        time15bin = int( now / 900 ) + 1
    timeFrst = ( int( time15bin / 96 ) - 1) * 86400
    timeLast = ( time15bin * 900 ) + 899


    # prepare HDFS subdirectory list:
    # ===============================
    logging.info("Retrieving SiteCapacity docs from MonIT HDFS")
    logging.log(15, "   from %s to %s" %
                       (time.strftime("%Y-%m-%d %H:%M", time.gmtime(timeFrst)),
                    time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime(timeLast))))
    #
    dirList = set()
    for dirDay in range(timeFrst, timeLast + 1, 86400):
        dirList.add( time.strftime("scap15min/%Y/%m/%d", time.gmtime(dirDay)) )
    #
    startLclTmpArea = max( calendar.timegm( time.localtime( sixDaysAgo ) ),
                           calendar.timegm( time.localtime( timeFrst ) ) )
    midnight = ( int( now / 86400 ) * 86400 )
    limitLclTmpArea = calendar.timegm( time.localtime( midnight + 86399 ) )
    for dirDay in range( startLclTmpArea, limitLclTmpArea, 86400):
        dirList.add( time.strftime("scap15min/%Y/%m/%d.tmp",
                                                         time.gmtime(dirDay)) )
    #
    dirList = sorted( dirList )


    # connect to HDFS, loop over directories and read status docs:
    # ============================================================
    tmpDict = {}
    try:
        with pydoop.hdfs.hdfs() as myHDFS:
            for subDir in dirList:
                logging.debug("   checking HDFS subdirectory %s" % subDir)
                if not myHDFS.exists( HDFS_PREFIX + subDir ):
                    continue
                # get list of files in directory:
                myList = myHDFS.list_directory( HDFS_PREFIX + subDir )
                fileNames = [ d['name'] for d in myList
                              if (( d['kind'] == "file" ) and
                                  ( d['size'] != 0 )) ]
                del myList
                for fileName in fileNames:
                    logging.debug("   reading file %s" %
                                  os.path.basename(fileName))
                    fileHndl = fileObj = None
                    try:
                        if ( os.path.splitext(fileName)[-1] == ".gz" ):
                            fileHndl = myHDFS.open_file(fileName)
                            fileObj = gzip.GzipFile(fileobj=fileHndl)
                        else:
                            fileObj = myHDFS.open_file(fileName)
                        # read SiteCapacity documents in file:
                        for myLine in fileObj:
                            myJson = json.loads(myLine.decode('utf-8'))
                            try:
                                if ( myJson['metadata']['path'] !=
                                                                 "scap15min" ):
                                    continue
                                tis = int( myJson['metadata']['timestamp']
                                                                       / 1000 )
                                if (( tis < timeFrst ) or ( tis > timeLast )):
                                    continue
                                myData = myJson['data']
                                if (( 'hs06_pledge' not in myData ) or
                                    ( 'hs06_per_core' not in myData ) or
                                    ( 'core_usable' not in myData ) or
                                    ( 'core_max_used' not in myData ) or
                                    ( 'core_production' not in myData ) or
                                    ( 'core_cpu_intensive' not in myData ) or
                                    ( 'core_io_intensive' not in myData ) or
                                    ( 'disk_pledge' not in myData ) or
                                    ( 'disk_usable' not in myData ) or
                                    ( 'disk_experiment_use' not in myData )):
                                    continue
                                if 'wlcg_federation_name' not in myData:
                                    myData['wlcg_federation_name'] = None
                                if 'wlcg_federation_fraction' not in myData:
                                    myData['wlcg_federation_fraction'] = None
                                if 'disk_local_use' not in myData:
                                    myData['disk_local_use'] = 0.0
                                if 'tape_pledge' not in myData:
                                    myData['tape_pledge'] = 0.0
                                if 'tape_usable' not in myData:
                                    myData['tape_usable'] = 0.0
                                if 'when' not in myData:
                                    myData['when'] = None
                                if 'who' not in myData:
                                    myData['who'] = None
                                #
                                tbin = int( tis / 900 )
                                name = myData['name']
                                vrsn = myJson['metadata']['kafka_timestamp']
                                #
                                value = (vrsn, myData)
                                #
                                if tbin not in tmpDict:
                                    tmpDict[tbin] = {}
                                if name in tmpDict[tbin]:
                                    if ( vrsn <= tmpDict[tbin][name][0] ):
                                        continue
                                tmpDict[tbin][name] = value
                            except KeyError:
                                continue
                    except json.decoder.JSONDecodeError as excptn:
                        logging.error("JSON decoding failure, file %s: %s"
                                                     % (fileName, str(excptn)))
                    except FileNotFoundError as excptn:
                        logging.error("HDFS file not found, %s: %s" %
                                                       (fileName, str(excptn)))
                    except IOError as excptn:
                        logging.error("IOError accessing HDFS file %s: %s"
                                                     % (fileName, str(excptn)))
                    finally:
                        if fileObj is not None:
                            fileObj.close()
                        if fileHndl is not None:
                            fileHndl.close()
    except Exception as excptn:
        logging.error("Failed to fetch SiteCapacity docs from MonIT HDFS: %s" %
                                                                   str(excptn))


    # select proper timebin and load SiteCapacity into a metric dictionary:
    # =====================================================================
    if ( len(tmpDict) == 0 ):
        logging.error("No SiteCapacity documents found in MonIT")
        return { 0: [] }
    myList = sorted( tmpDict.keys(), reverse=True )
    for tbin in myList:
        if ( tbin <= time15bin ):
            break
    if ( tbin > time15bin ):
        logging.error("No SiteCapacity documents covering timebin %d found" %
                                                                     time15bin)
        return { 0: [] }
    #
    metricDict = {}
    metricDict[ tbin ] = []
    for myName in sorted( tmpDict[ tbin ] ):
        metricDict[ tbin ].append( tmpDict[ tbin ][myName][1] )
    del tmpDict

    logging.info("   found %d relevant SiteCapacity docs in timebin %d" %
                                               (len(metricDict[ tbin ]), tbin))
    #
    return metricDict
# ########################################################################### #



def capa_monit_upload(metricDict):
    """function to upload SiteCapacity metric(s) to MonIT/HDFS"""
    # ################################################################# #
    # upload SiteCapacity information as JSON metric documents to MonIT #
    # ################################################################# #
    #MONIT_URL = "http://monit-metrics.cern.ch:10012/"
    MONIT_URL = "http://fail.cern.ch:10001/"
    MONIT_HDR = {'Content-Type': "application/json; charset=UTF-8"}
    #
    logging.info("Composing SiteCapacity JSON array and uploading to MonIT")


    # compose JSON array string:
    # ==========================
    jsonString = "["
    commaFlag = False
    for t15bin in sorted( metricDict.keys() ):
        mtrcString = capa_compose_json(metricDict[t15bin], t15bin, True)
        if ( commaFlag ):
            jsonString = ","
        jsonString += mtrcString[1:-3]
        commaFlag = True
    jsonString += "\n]\n"
    #
    if ( jsonString == "[\n]\n" ):
        logging.warning("skipping upload of document-devoid JSON string")
        return False
    cnt_docs = jsonString.count("\"producer\": \"cmssst\"")
    #
    jsonString = jsonString.replace("ssbmetric", "metrictest")


    # upload string with JSON document array to MonIT/HDFS:
    # =====================================================
    docs = json.loads(jsonString)
    ndocs = len(docs)
    successFlag = True
    for myOffset in range(0, ndocs, 2048):
        if ( myOffset > 0 ):
            # give importer time to process documents
            time.sleep(1.500)
        # MonIT upload channel can handle at most 10,000 docs at once
        dataString = json.dumps( docs[myOffset:min(ndocs,myOffset+2048)] )
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
                              (myOffset, min(ndocs,myOffset+2048),
                               responseObj.status, responseObj.reason))
                successFlag = False
            responseObj.close()
        except urllib.error.URLError as excptn:
            logging.error("Failed to upload JSON [%d:%d], %s" %
                             (myOffset, min(ndocs,myOffset+2048), str(excptn)))
            successFlag = False
    del docs

    if ( successFlag ):
        logging.log(25, "JSON array with %d docs uploaded to MonIT" % cnt_docs)
    return successFlag
# ########################################################################### #



def capa_monit_write(metricDict, filename=None):
    """function to write SiteCapacity metric(s) to a file"""
    # ################################################################# #
    # write SiteCapacity information as JSON metric documents to a file #
    # ################################################################# #

    if filename is None:
        filename = "%s/eval_scap_%s.json" % (CAPA_BCKUP_DIR,
                                    time.strftime("%Y%m%d%H%M", time.gmtime()))
    logging.info("Writing SiteCapacity JSON array to file %s" % filename)


    # compose JSON array string:
    # ==========================
    jsonString = "["
    commaFlag = False
    for t15bin in sorted( metricDict.keys() ):
        #mtrcString = capa_compose_json(metricDict[t15bin], None, True)
        mtrcString = capa_compose_json(metricDict[t15bin], t15bin, True)
        if ( commaFlag ):
            jsonString = ","
        jsonString += mtrcString[1:-3]
        commaFlag = True
    jsonString += "\n]\n"
    #
    if ( jsonString == "[\n]\n" ):
        logging.warning("skipping upload of document-devoid JSON string")
        return False
    #cnt_docs = jsonString.count("   \"name\": \"T")
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



def capa_compare_metrics(metricDict, capacityList):
    """compare a SiteCapacity dictionary with last list in a metrics dict"""
    # #################################################################### #
    # check if the SiteCapacity entries in the capacityList match with the #
    # last SiteCapacity list in the provided metric dictionary             #
    # #################################################################### #

    if (( len(metricDict) == 0 ) and ( len(capacityList) == 0 )):
        logging.warning("Empty metric and capacity list compared")
        return True
    #
    # get latest timebin in metricDict:
    t15bin = sorted( metricDict.keys(), reverse=True )[0]
    #
    # convert SiteCapacity list to dictionary:
    tmp1Dict = { e['name']:e for e in capacityList }
    #
    # convert SiteCapacity list in metric to dictionary:
    tmp2Dict = { e['name']:e for e in metricDict[t15bin] }
    #
    # compare the two dictionaries:
    compFlag = ( tmp1Dict == tmp2Dict )

    return compFlag
# ########################################################################### #



if __name__ == '__main__':
    #
    os.umask(0o022)
    #
    parserObj = argparse.ArgumentParser(description="Script to update/fetch/" +
        "upload site capacity information in the JSON file/CERN MonIT.")
    parserObj.add_argument("-p", dest="pledge", default=False,
                                 action="store_true",
                                 help="fetch/update pledges from ReBus/CRIC")
    parserObj.add_argument("-q", dest="quota", default=False,
                                 action="store_true",
                                 help="fetch/update experiment disk quota fr" +
                                 "om Rucio")
    parserObj.add_argument("-u", dest="usage", default=False,
                                 action="store_true",
                                 help="fetch/update max core usage from Elas" +
                                 "ticSearch/startd data")
    parserObj.add_argument("-f", dest="file", default=None, const="",
                                 action="store", nargs="?",
                                 metavar="filepath",
                                 help="write SiteCapacity data to file")
    parserObj.add_argument("-U", dest="upload", default=True,
                                 action="store_false",
                                 help="do not upload SiteCapacity to MonIT")
    parserObj.add_argument("-v", action="count", default=0,
                                 help="increase logging verbosity")
    argStruct = parserObj.parse_args()
    #
    # configure message logging:
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
    logging.basicConfig(datefmt="%Y-%b-%d %H:%M:%S", format=logFormat,
                                                                level=logLevel)


    now15m = int( time.time() / 900 )
    #
    # fetch list of valid CMS site names as needed:
    siteList = None
    if ( argStruct.pledge or argStruct.usage ):
        siteList = capa_cric_cmssites()
    #
    #
    # fetch federation pledge information from ReBUS/CRIC if requested:
    pledgeDict = None
    if ( argStruct.pledge ):
        pledgeDict = capa_cric_pledges()
    #
    #
    # fetch experiment disk quota setting from Rucio if requested:
    quotaDict = None
    if ( argStruct.quota ):
        quotaDict = capa_rucio_quotas()
    #
    #
    # fetch maximum number of cores provided by sites if requested:
    usageDict = None
    if ( argStruct.usage ):
        usageDict = capa_startd_usage()



    # update SiteCapacity JSON file as needed:
    if ( argStruct.pledge or argStruct.quota or argStruct.usage ):
        capacityList = capa_update_jsonfile(siteList,
                                            pledgeDict, quotaDict, usageDict)
    else:
        capacityList = capa_read_jsonfile()



    # upload SiteCapacity data to MonIT HDFS as needed/requested:
    if ( argStruct.upload ):
        #
        # fetch latest SiteCapacity docs from MonIT
        metricDict = capa__monit_fetch()
        #
        hourLatest = int( (sorted( metricDict.keys(), reverse=True )[0]) / 4 )
        hourCurrent = int( now15m / 4 )
        if ( hourLatest == hourCurrent ):
            skipFlag = capa_compare_metrics(metricDict, capacityList)
        else:
            skipFlag = False
        #
        # upload SiteCapacity data as needed:
        if ( skipFlag == False ):
            capa_monit_upload( { now15m: capacityList } )
    #
    #
    # write SiteCapacity data to file as requested:
    if argStruct.file is not None:
        if ( argStruct.file == "" ):
            capa_monit_write( { now15m: capacityList } )
        else:
            capa_monit_write( { now15m: capacityList }, argStruct.file )


    #import pdb; pdb.set_trace()
