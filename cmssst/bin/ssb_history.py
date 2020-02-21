#!/data/cmssst/packages/bin/python3.7
# ########################################################################### #
# python script to fetch historic SAM and Site Readiness information from the
#    SSB dashboard and upload it into MonIT/HDFS (sam1day, sr1day).
#
# 2020-Feb-19 Stephan Lammel
# ########################################################################### #



import os
import argparse
import logging
import time, calendar
import http
import urllib.request, urllib.error
import json
import re
#
# setup the Java/HDFS/PATH environment for pydoop to work properly:
os.environ["HADOOP_CONF_DIR"] = "/opt/hadoop/conf/etc/analytix/hadoop.analytix"
os.environ["JAVA_HOME"]       = "/etc/alternatives/jre"
os.environ["HADOOP_PREFIX"]   = "/usr/hdp/hadoop"
import pydoop.hdfs
# ########################################################################### #



def sam3_sam_site( frstDAY, lastDAY ):
    # ################################################################## #
    # get SAM site availability information of sites from SAM3 dashboard #
    # ################################################################## #
    #
    URL_SAM3_SITE_STATS = "http://wlcg-sam-cms.cern.ch/dashboard/request.py/getstatsresultsmin?prettyprint&plot_type=quality&start_time=%s&profile_name=CMS_CRITICAL_FULL&end_time=%s&granularity=daily&view=siteavl" % (time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(frstDAY * 86400)), time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime((lastDAY * 86400) + 86399)))
    #
    siteRegex = re.compile(r"T\d_[A-Z]{2,2}_\w+")
    originStrng = "historic result from SAM3, wlcg-sam-cms.cern.ch, dashboard"


    # get SAM site availability information from the SAM3 dashboard:
    # ==============================================================
    logging.info("Querying SAM3 for SAM site availability information")
    urlHndl = None
    try:
        request = urllib.request.Request(URL_SAM3_SITE_STATS,
                                         headers={'Accept':'application/json'})
        urlHndl = urllib.request.urlopen( request )
        myCharset = urlHndl.headers.get_content_charset()
        if myCharset is None:
            myCharset = "utf-8"
        myData = urlHndl.read().decode( myCharset )
        del(myCharset)
    except Exception as excptn:
        logging.critical("Failed to fetch SAM3 SAM site data, %s" % str(excptn))
        raise
    finally:
        if urlHndl is not None:
            urlHndl.close()
    del urlHndl


    # parse JSON string:
    # ==================
    myJson = json.loads(myData)
    #
    resultDict = {}
    for myEntry in myJson['data']:
        mySite = myEntry['name']
        if ( siteRegex.match( mySite ) is None ):
            logging.warning("Unknown/bad SAM3 SAM site name \"%s\"" % mySite)
            continue
        for myItem in myEntry['data']:
            ts = time.strptime(myItem['date'] + 'T12 UTC', "%Y/%m/%dT%H %Z")
            myDay = int( calendar.timegm(ts) / 86400 )
            myBad = myItem['CRIT']
            myGood = myItem['OK']
            myDown = myItem['SCHED']
            #
            try:
                myAvailability = round( myGood / (myBad + myGood + myDown), 3)
                try:
                    myReliability  = round( myGood / (myBad + myGood), 3)
                except ZeroDivisionError:
                    myReliability = None
            except ZeroDivisionError:
                myAvailability = None
                myReliability  = None
            #
            if ( myAvailability is None ):
                myStatus = "unknown"
            elif ( myAvailability >= 0.900 ):
                myStatus = "ok"
            elif ( myAvailability < 0.800 ):
                myStatus = "error"
            elif (( mySite[1] == "0" ) or ( mySite[1] == "1" )):
                myStatus = "error"
            else:
                myStatus = "warning"
            if (( myDown > 0 ) and ( myDown >= (myBad + myGood) )):
                myStatus = "downtime"
            myKey = ( myDay, mySite )
            resultDict[ myKey ] = { 'name': mySite, 'type': "site",
                                    'status': myStatus,
                                    'availability': myAvailability,
                                    'reliability': myReliability,
                                    'detail': originStrng }

    if ( len(resultDict) == 0 ):
        logging.warning("No SAM site availability entries found!")
    else:
        logging.log(25, "%d SAM site availability entries found" %
                                                               len(resultDict))
    #
    return resultDict
# ########################################################################### #



def ssb_sitereadiness( frstDAY, lastDAY ):
    # ##################################################### #
    # get Site Readiness metric data from the SSB-Dashboard #
    # ##################################################### #
    URL_SSB_SITEREADINESS = "http://dashb-ssb.cern.ch/dashboard/request.py/getplotdata?columnid=234&time=custom&sites=all&clouds=all&batch=1&dateFrom=%s&dateTo=%s" % (time.strftime("%Y-%m-%d", time.gmtime(frstDAY * 86400)), time.strftime("%Y-%m-%d", time.gmtime((lastDAY + 1) * 86400)))
    #
    siteRegex = re.compile(r"T\d_[A-Z]{2,2}_\w+")
    noonList = [ ((day*86400) + 43200) for day in range(frstDAY, lastDAY + 1) ]
    originStrng = "historic result from SSB #234, dashb-ssb.cern.ch, dashboard"

    # get SiteReadiness data from the SSB dashboard:
    # ==============================================
    logging.info("Querying SSB for SiteReadiness information")
    urlHndl = None
    try:
        request = urllib.request.Request(URL_SSB_SITEREADINESS,
                                         headers={'Accept':'application/json'})
        urlHndl = urllib.request.urlopen( request )
        myCharset = urlHndl.headers.get_content_charset()
        if myCharset is None:
            myCharset = "utf-8"
        myData = urlHndl.read().decode( myCharset )
        del(myCharset)
    except Exception as excptn:
        logging.critical("Failed to fetch SSB SiteReadiness data, %s" %
                                                                   str(excptn))
        raise
    finally:
        if urlHndl is not None:
            urlHndl.close()
    del urlHndl


    # parse JSON data:
    sreadiness = json.loads( myData )
    #
    resultDict = {}
    for myEntry in sreadiness['csvdata']:
        try:
            mySite = myEntry['VOName']
            if ( siteRegex.match( mySite ) is None ):
                logging.warning("Unknown/bad SiteReadiness site name \"%s\"" %
                                                                        mySite)
                continue
            if (( mySite[-5:] == "_Disk" ) or ( mySite[-7:] == "_Buffer" ) or
                ( mySite[-7:] == "_Export" ) or ( mySite[-4:] == "_MSS" )):
                continue
            myStatus = myEntry['Status'].lower()
            if ( myStatus not in ["ok", "warning", "error", "downtime" ] ):
                logging.warning("Unknown/bad SiteReadiness status \"%s\"" %
                                                             myEntry['Status'])
                myStatus = "unknown"
            ts = time.strptime(myEntry['Time'] + ' UTC', "%Y-%m-%dT%H:%M:%S %Z")
            startTIS = calendar.timegm(ts)
            ts = time.strptime(myEntry['EndTime'] + ' UTC',
                                                        "%Y-%m-%dT%H:%M:%S %Z")
            finalTIS = calendar.timegm(ts)
            for tis in noonList:
                if (( tis >= startTIS ) and ( tis < finalTIS )):
                    myKey = ( int(tis / 86400), mySite )
                    resultDict[ myKey ] = { 'name': mySite,
                                            'status': myStatus,
                                            'value': None,
                                            'detail': originStrng }
        except KeyError:
            continue

    if ( len(resultDict) == 0 ):
        logging.warning("No SSB Site Readiness entries found!")
    else:
        logging.log(25, "%d SSB Site Readiness entries found" %
                                                               len(resultDict))
    #
    return resultDict
# ########################################################################### #



def compose_sam_json(timestamp, results):
    """function to convert SAM result list to a JSON string"""
    # #################################################################### #
    # write JSON string with SAM result list that can be uploaded to MonIT #
    # #################################################################### #

    jsonString = "["
    hdrString = ((",\n {\n   \"producer\": \"cmssst\",\n" +
                         "   \"type\": \"ssbmetric\",\n" +
                         "   \"path\": \"sam1day\",\n" +
                         "   \"timestamp\": %d000,\n" +
                         "   \"type_prefix\": \"raw\",\n" +
                         "   \"data\": {\n") % timestamp)

    commaFlag = False
    for doc in sorted(results, key=lambda k: k['name'] ):
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
        jsonString += "\n   }\n }"
        commaFlag = True
    jsonString += "\n]\n"

    return jsonString



def compose_sr_json(timestamp, results):
    """function to convert SR result dictionary to a JSON string"""
    # ################################################################### #
    # write JSON string with SR result list that can be uploaded to MonIT #
    # ################################################################### #

    jsonString = "["
    hdrString = ((",\n {\n   \"producer\": \"cmssst\",\n" +
                         "   \"type\": \"ssbmetric\",\n" +
                         "   \"path\": \"sr1day\",\n" +
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
        jsonString += "\n   }\n }"
        commaFlag = True
    jsonString += "\n]\n"

    return jsonString



def write_file(samDict, srDict):
    """function to write MonIT documents to file for editing/correction"""
    # ############################################################### #
    # write docs in global dictionary to one file or file per timebin #
    # ############################################################### #
    filename = "historic_%s.json" % time.strftime("%Y%m%d%H%M%S", time.gmtime())

    logging.info("Writing JSON array to file %s" % filename)


    # compose JSON array string:
    # ==========================
    jsonString = "["
    commaFlag = False
    #
    #
    dayList = set()
    for myKey in samDict:
        dayList.add( myKey[0] )
    dayList = sorted( dayList )
    for myDay in dayList:
        tis = ( myDay * 86400 ) + 43200
        docList = [ samDict[k] for k in samDict if (k[0] == myDay) ]
        #
        jsonSegmnt = compose_sam_json(tis, docList)
        #
        #
        if commaFlag:
            jsonString += "," + jsonSegmnt[1:-3]
        else:
            jsonString += jsonSegmnt[1:-3]
        commaFlag = True
    #
    #
    dayList = set()
    for myKey in srDict:
        dayList.add( myKey[0] )
    dayList = sorted( dayList )
    for myDay in dayList:
        tis = ( myDay * 86400 ) + 43200
        docList = [ srDict[k] for k in srDict if (k[0] == myDay) ]
        #
        jsonSegmnt = compose_sr_json(tis, docList)
        #
        #
        if commaFlag:
            jsonString += "," + jsonSegmnt[1:-3]
        else:
            jsonString += jsonSegmnt[1:-3]
        commaFlag = True
    #
    #
    jsonString += "\n]\n"
    #
    if ( jsonString == "[\n]\n" ):
        logging.warning("skipping upload of document-devoid JSON string")
        return
    cnt_docs = jsonString.count("\"producer\": \"cmssst\"")


    # write string to file:
    # =====================
    try:
        with open(filename, 'w') as myFile:
            myFile.write( jsonString )
        logging.log(25, "JSON array with %d docs written to file" % cnt_docs)
    except OSError as excptn:
        logging.error("Failed to write JSON array, %s" % str(excptn))
    #
    time.sleep(1.000)

    return
# ########################################################################### #



def monit_upload(samDict, srDict):
    """function to upload SAM and Site Readiness documents to MonIT"""
    # ####################################################################### #
    # upload documents provided in dictionary of lists as JSON array to MonIT #
    # ####################################################################### #
    #MONIT_URL = "http://monit-metrics.cern.ch:12021/"
    MONIT_HDR = {'Content-Type': "application/json; charset=UTF-8"}
    #
    logging.info("Composing JSON array and uploading to MonIT")


    # compose JSON array string:
    # ==========================
    jsonString = "["
    commaFlag = False
    #
    #
    dayList = set()
    for myKey in samDict:
        dayList.add( myKey[0] )
    dayList = sorted( dayList )
    for myDay in dayList:
        tis = ( myDay * 86400 ) + 43200
        docList = [ samDict[k] for k in samDict if (k[0] == myDay) ]
        #
        jsonSegmnt = compose_sam_json(tis, docList)
        #
        #
        if commaFlag:
            jsonString += "," + jsonSegmnt[1:-3]
        else:
            jsonString += jsonSegmnt[1:-3]
        commaFlag = True
    #
    #
    dayList = set()
    for myKey in srDict:
        dayList.add( myKey[0] )
    dayList = sorted( dayList )
    for myDay in dayList:
        tis = ( myDay * 86400 ) + 43200
        docList = [ srDict[k] for k in srDict if (k[0] == myDay) ]
        #
        jsonSegmnt = compose_sr_json(tis, docList)
        #
        #
        if commaFlag:
            jsonString += "," + jsonSegmnt[1:-3]
        else:
            jsonString += jsonSegmnt[1:-3]
        commaFlag = True
    #
    #
    jsonString += "\n]\n"
    #
    if ( jsonString == "[\n]\n" ):
        logging.warning("skipping upload of document-devoid JSON string")
        return
    #
    jsonString = jsonString.replace("ssbmetric", "metrictest")


    # upload string with JSON document array to MonIT/HDFS:
    # =====================================================
    docs = json.loads(jsonString)
    ndocs = len(docs)
    for myOffset in range(0, ndocs, 4096):
        if ( myOffset > 0 ):
            # give importer time to process documents
            time.sleep(1.500)
        # MonIT upload channel can handle at most 10,000 docs at once
        dataString = json.dumps( docs[myOffset:min(ndocs,myOffset+4096)] )
        #
        try:
            # MonIT needs a document array and without newline characters:
            requestObj = urllib.request.Request(MONIT_URL,
                         data=dataString.encode("utf-8"),
                         headers=MONIT_HDR, method="POST")
            responseObj = urllib.request.urlopen( requestObj, timeout=90 )
            if ( responseObj.status != http.HTTPStatus.OK ):
                myStatus = responseObj.status
                myReason = responseObj.reason
                responseObj.close()
                raise urllib.error.URLError("response status %d \"%s\"" %
                                                          (myStatus, myReason))
            responseObj.close()
        except urllib.error.URLError as excptn:
            logging.error("Failed to upload JSON [%d:%d], %s, retry in 90 sec"
                           % (myOffset, min(ndocs,myOffset+4096), str(excptn)))
            del requestObj
            time.sleep(90.500)
            dataString = json.dumps( docs[myOffset:min(ndocs,myOffset+4096)] )
            try:
                requestObj = urllib.request.Request(MONIT_URL,
                             data=dataString.encode("utf-8"),
                             headers=MONIT_HDR, method="POST")
                responseObj = urllib.request.urlopen( requestObj, timeout=90 )
                if ( responseObj.status != http.HTTPStatus.OK ):
                    raise urllib.error.URLError("response status %d \"%s\"" %
                                      (responseObj.status, responseObj.reason))
                responseObj.close()
            except urllib.error.URLError as excptn:
                raise urllib.error.URLError("Failed to upload JSON [%d:%d], %s"
                           % (myOffset, min(ndocs,myOffset+4096), str(excptn)))
    del docs

    logging.log(25, "JSON string with %d docs uploaded to MonIT" % ndocs)
    return
# ########################################################################### #



if __name__ == '__main__':
    corr_cfg = {}
    #
    parserObj = argparse.ArgumentParser(description="Script to fetch histori" +
        "c SAM and Site Readiness information from the SSB and upload to Mon" +
        "IT. Default time period is ( sites/hosts/types can be fetched, edit" +
        "ed, and uploaded.")
    parserObj.add_argument("-U", dest="upload", default=True,
                                 action="store_false",
                                 help=("do not upload to MonIT but print new" +
                                       "document(s) instead"))
    parserObj.add_argument("-v", action="count", default=1,
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
    if argStruct.timeSpec is None:
        # first SAM site status 2014-Aug-01
        startDAY = int( 1406894400 / 86400 )
    elif ( argStruct.timeSpec.isdigit() ):
        # argument should be time in seconds of first time bin
        startDAY = int( argStruct.timeSpec / 86400 )
    else:
        # argument should be the time in "YYYY-Mmm-dd HH:MM" format
        startDAY = int( calendar.timegm( time.strptime("%s UTC" %
                        argStruct.timeSpec, "%Y-%b-%d %H:%M %Z") ) / 86400 )
    #
    if argStruct.lastSpec is None:
        # SSB to MonIT switch 2020-Feb-17
        lastDAY = int( 1581854400 / 86400 )
    elif ( argStruct.lastSpec.isdigit() ):
        # argument should be time in seconds of last 15 min time bin
        lastDAY = int( argStruct.lastSpec / 86400 )
    else:
        # argument should be the time in "YYYY-Mmm-dd HH:MM" format
        lastDAY = int( calendar.timegm( time.strptime("%s UTC" %
                        argStruct.lastSpec, "%Y-%b-%d %H:%M %Z") ) / 86400 )
    #
    logging.log(25, "Uploading SAM/SR info of SSB into MonIT from %s to %s" %
                    (time.strftime("%Y-%b-%d", time.gmtime(startDAY*86400)),
                     time.strftime("%Y-%b-%d", time.gmtime(lastDAY*86400))))


    # loop over time period one week at a time:
    # =========================================
    for frstDAY in range(startDAY, lastDAY + 1, 10):
        finlDAY = min( frstDAY + 9, lastDAY)
        #
        logging.log(25, "period %s --- %s" %
                        (time.strftime("%Y-%b-%d", time.gmtime(frstDAY*86400)),
                         time.strftime("%Y-%b-%d", time.gmtime(finlDAY*86400))))
        #
        #
        # SSB #126 is uncorrected and WLCG #745 are timeseries
        samDict = sam3_sam_site( frstDAY, finlDAY )
        #
        #
        # first Site Readiness 2015-Jan-02:
        if ( finlDAY >= 16437 ):
            srDict = ssb_sitereadiness( max(frstDAY,16437), finlDAY )
        else:
            srDict = {}
        #
        #
        # upload corrected document(s) to MonIT:
        # ======================================
        if ( argStruct.upload ):
            monit_upload(samDict, srDict)
        else:
            write_file(samDict, srDict)


    #import pdb; pdb.set_trace()
