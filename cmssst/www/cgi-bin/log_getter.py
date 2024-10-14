#!/eos/user/c/cmssst/el9packages/bin/python3.9
# /eos/user/c/cmssst/packages/bin/python3.7
# ########################################################################### #
# python script to retrieve CMS SSB metric documents from CERN MonIT
#    ElasticSearch via Grafana. The cmssst log retrieval Bourne shell script
#    will use this script to retrieve, format as HTML table, and write to
#    standard output the document(s).
#
# 2020-Feb-11   Stephan Lammel
# ########################################################################### #
#
# PATH_INFO supported:
# ====================
#   /down15min / 1550923650     / T0_CH_CERN  / site           / 0+0
#    sam15min  / 201902231200   / ce07.pic.es / CE             /
#    sam1hour  / 20190223120730 / all         / SE-xrootd-read /
#    sam6hour                                                  /
#    sam1day                                                   /
#    hc15min     "HammerCloud"                                 / debug
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
import io
import time, calendar
import logging
import argparse
import urllib.request, urllib.error
import http
import re
import json
import gzip
# ########################################################################### #



LGET_SERVICE_ORDER = [ "site", "CE", "SRM", "WEBDAV", "XROOTD", "perfSONAR" ]
LGET_TRANSFER_ORDER = [ "site", "rse", "GSIFTP-destination", "GSIFTP-source",
                         "WEBDAV-destination", "WEBDAV-source", "destination",
                         "source", "GSIFTP-link", "WEBDAV-link", "link" ]
LGET_SUPERSEDED = 1000
LGET_METRICS_DEFINED = {
    'down15min': {
        'title': "Downtime(s)",
        'period': 900,
        'query': "down15min",
        'dfltwin': "day+0" },
    'sam15min': {
        'title': "SAM 15 min",
        'period': 900,
        'query': "sam15min",
        'dfltwin': "1+1" },
    'sam1hour': {
        'title': "SAM 1 hour", 
        'period': 3600,
        'query': "sam1hour",
        'dfltwin': "0+0" },
    'sam6hour': { 
        'title': "SAM 6 hours", 
        'period': 21600,
        'query': "sam6hour",
        'dfltwin': "0+0" },
    'sam1day': { 
        'title': "SAM 1 day",
        'period': 86400,
        'query': "sam1day",
        'dfltwin': "0+0" },
    'hc15min': { 
        'title': "HC 15 min", 
        'period': 900,
        'query': "hc15min",
        'dfltwin': "1+1" },
    'hc1hour': { 
        'title': "HC 1 hour", 
        'period': 3600,
        'query': "hc1hour",
        'dfltwin': "0+0" },
    'hc6hour': { 
        'title': "HC 6 hours", 
        'period': 21600,
        'query': "hc6hour",
        'dfltwin': "0+0" },
    'hc1day': { 
        'title': "HC 1 day", 
        'period': 86400,
        'query': "hc1day",
        'dfltwin': "0+0" },
    'fts15min': {
        'title': "FTS 15 min",
        'period': 900,
        'query': "fts15min",
        'dfltwin': "1+1" },
    'fts1hour': {
        'title': "FTS 1 hour",
        'period': 3600,
        'query': "fts1hour",
        'dfltwin': "0+0" },
    'fts6hour': {
        'title': "FTS 6 hours",
        'period': 21600,
        'query': "fts6hour",
        'dfltwin': "0+0" },
    'fts1day': {
        'title': "FTS 1 day",
        'period': 86400,
        'query': "fts1day",
        'dfltwin': "0+0" },
    'sr15min': {
        'title': "SiteReadiness 15 min",
        'period': 900,
        'query': "sr15min",
        'dfltwin': "1+1" },
    'sr1hour': {
        'title': "SiteReadiness 1 hour",
        'period': 3600,
        'query': "sr1hour",
        'dfltwin': "0+0" },
    'sr6hour': {
        'title': "SiteReadiness 6 hours",
        'period': 21600,
        'query': "sr6hour",
        'dfltwin': "0+0" },
    'sr1day': {
        'title': "SiteReadiness 1 day",
        'period': 86400,
        'query': "sr1day",
        'dfltwin': "0+0" },
    'sts15min': { 
        'title': "SiteStatus 15 min", 
        'period': 900,
        'query': "sts15min",
        'dfltwin': "day+0" },
    'links15min': {
        'title': "Links 15 min",
        'period': 900,
        'query': "fts15min",
        'dfltwin': "1+1" },
    'links1hour': {
        'title': "Links 1 hour",
        'period': 3600,
        'query': "fts1hour",
        'dfltwin': "0+0" },
    'links6hour': {
        'title': "Links 6 hours",
        'period': 21600,
        'query': "fts6hour",
        'dfltwin': "0+0" },
    'links1day': {
        'title': "Links 1 day",
        'period': 86400,
        'query': "fts1day",
        'dfltwin': "0+0" }
    }
LGET_SERVICE_TYPES = { 'CE': "CE",
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



def lget_grafana_fetch(cfg):
    """function to get relevant documents from MonIT/ElasticSearch"""
    # ####################################################################### #
    # return dictionary with list of documents from MonIT/ES for each timebin #
    # ####################################################################### #
    URL_GRAFANA = "https://monit-grafana.cern.ch/api/datasources/proxy/9475/_msearch"
    HDR_GRAFANA = {'Authorization': "Bearer eyJrIjxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxjoxMX0=", 'Content-Type': "application/json; charset=UTF-8"}
    #
    siteRegex = re.compile(r"T\d_[A-Z]{2,2}_\w+")
    #
    if ( cfg['metric'][:5] == "links" ):
        # restrict link view to one timebin:
        startTIS = cfg['time']
        limitTIS = cfg['time'] + cfg['period']
    else:
        startTIS = cfg['time'] - ( cfg['period'] * cfg['before'] )
        limitTIS = cfg['time'] + ( cfg['period'] * ( cfg['after'] + 1 ) )
    #
    logging.info("Retrieving %s docs from MonIT/ES via Grafana" % cfg['title'])
    logging.log(15, "   time range %s to %s" %
                    (time.strftime("%Y-%b-%d %H:%M", time.gmtime(startTIS)),
                     time.strftime("%Y-%b-%d %H:%M", time.gmtime(limitTIS))))


    # prepare Lucene ElasticSearch query:
    # ===================================
    queryString = ("{\"search_type\":\"query_then_fetch\",\"index\":[\"monit" +
                   "_prod_cmssst_*\"]}\n{\"query\":{\"bool\":{\"must\":[{\"m" +
                   "atch_phrase\":{\"metadata.type\":\"ssbmetric\"}},{\"matc" +
                   "h_phrase\":{\"metadata.type_prefix\":\"raw\"}},{\"match_" +
                   "phrase\":{\"metadata.monit_hdfs_path\":\"%s\"}}],\"filte" +
                   "r\":{\"range\":{\"metadata.timestamp\":{\"gte\":%d,\"lt" +
                   "\":%d,\"format\":\"epoch_second\"}}}}},\"_source\":{\"in" +
                   "cludes\":[\"metadata.timestamp\",\"metadata.kafka_timest" +
                   "amp\",\"metadata._id\",\"data.*\"]},\"size\":8192,\"sear" +
                   "ch_after\":[\"%%s\"],\"sort\":[{\"metadata._id\":\"asc\"" +
                   "}]}\n") % (cfg['query'], startTIS, limitTIS)


    # loop and fetch 8k docs at a time to get around ElasticSearch limit:
    # ===================================================================
    lget_monitdocs = {}
    nDocsHdr = None
    nDocsCnt = 0
    previousID = ""
    while ( nDocsCnt != nDocsHdr ):
        #
        # fetch a chunk of documents from ElasticSearch:
        # ==============================================
        try:
            requestObj = urllib.request.Request(URL_GRAFANA,
                         data=(queryString % previousID).encode("utf-8"),
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
        logging.log(15, "   ES chunk starting after _id=\"%s\" retrieved" %
                                                                    previousID)

        # unpack query result JSON data:
        # ==============================
        myResult = json.loads( myData )
        del myData

        # fill job records into global HTCondor list:
        # ===========================================
        nDocsChnk = 0
        for myResponse in myResult['responses']:
            try:
                if nDocsHdr is None:
                    nDocsHdr = myResponse['hits']['total']['value']
                elif ( nDocsHdr != myResponse['hits']['total']['value'] ):
                    logging.warning("Changed job record count, %d versus %d" %
                              (nDocsHdr, myResponse['hits']['total']['value']))
                #
                nDocsChnk += len( myResponse['hits']['hits'] )
                #
                for myHit in myResponse['hits']['hits']:
                    nDocsCnt += 1
                    try:
                        myJson = myHit['_source']
                        previousID = myJson['metadata']['_id']
                        logging.log(9, "   document %s" % \
                                                     myJson['metadata']['_id'])
                        #
                        tis = int( myJson['metadata']['timestamp'] / 1000 )
                        if (( tis < startTIS ) or ( tis >= limitTIS )):
                            continue
                        if ( cfg['metric'][:4] == "down" ):
                            if (( 'name' not in myJson['data'] ) or
                                ( 'type' not in myJson['data'] ) or
                                ( 'status' not in myJson['data'] ) or
                                ( 'duration' not in myJson['data'] )):
                                continue
                            myName = myJson['data']['name']
                            if (( siteRegex.match(cfg['name']) is not None ) and
                                ( cfg['type'] == "*" )):
                                if (( myName != cfg['name'] ) and
                                    ( myName.count(".") < 2 )):
                                    continue
                            elif ( cfg['name'] != "*" ):
                                if ( myName != cfg['name'] ):
                                    continue
                            myType = myJson['data']['type']
                            if ( cfg['type'] != "*" ):
                                if myType not in LGET_SERVICE_TYPES:
                                    ctgry = ""
                                else:
                                    ctgry = LGET_SERVICE_TYPES[ myType ]
                                if (( myType != cfg['type'] ) and
                                    ( ctgry != cfg['type'] )):
                                    continue
                            myStatus = myJson['data']['status']
                        elif ( cfg['metric'][:3] == "sam" ):
                            if (( 'name' not in myJson['data'] ) or
                                ( 'type' not in myJson['data'] ) or
                                ( 'status' not in myJson['data'] )):
                                continue
                            myName = myJson['data']['name']
                            if (( siteRegex.match(cfg['name']) is not None ) and
                                ( cfg['type'] == "*" )):
                                if (( myName != cfg['name'] ) and
                                    ( myName.count(".") < 2 )):
                                    continue
                            elif ( cfg['name'] != "*" ):
                                if ( myName != cfg['name'] ):
                                    continue
                            myType = myJson['data']['type']
                            if ( cfg['type'] != "*" ):
                                if ( myType != cfg['type'] ):
                                    continue
                            myStatus = myJson['data']['status']
                        elif ( cfg['metric'][:2] == "hc" ):
                            if 'name' not in myJson['data']:
                                myJson['data']['name'] = myJson['data']['site']
                            if (( 'name' not in myJson['data'] ) or
                                ( 'status' not in myJson['data'] )):
                                continue
                            myName = myJson['data']['name']
                            if ( cfg['name'] != "*" ):
                                if ( myName != cfg['name'] ):
                                    continue
                            myType = "site"
                            myStatus = myJson['data']['status']
                        elif ( cfg['metric'][:3] == "fts" ):
                            if (( 'name' not in myJson['data'] ) or
                                ( 'type' not in myJson['data'] ) or
                                ( 'status' not in myJson['data'] )):
                                continue
                            myName = myJson['data']['name']
                            if (( siteRegex.match(cfg['name']) is not None ) and
                                ( cfg['type'] == "*" )):
                                myLength = len(cfg['name'])
                                if (( myName[:myLength] != cfg['name'] ) and
                                    ( myName.count(".") < 2 )):
                                    continue
                            elif ( cfg['name'] != "*" ):
                                if ( myName != cfg['name'] ):
                                    continue
                            myType = myJson['data']['type']
                            if ( cfg['type'] != "*" ):
                                if ( myType != cfg['type'] ):
                                    continue
                            myStatus = myJson['data']['status']
                        elif ( cfg['metric'][:2] == "sr" ):
                            if (( 'name' not in myJson['data'] ) or
                                ( 'status' not in myJson['data'] )):
                                continue
                            myName = myJson['data']['name']
                            if ( cfg['name'] != "*" ):
                                if ( myName != cfg['name'] ):
                                    continue
                            myType = "site"
                            myStatus = myJson['data']['status']
                        elif ( cfg['metric'][:3] == "sts" ):
                            if (( 'name' not in myJson['data'] ) or
                                ( 'status' not in myJson['data'] ) or
                                ( 'prod_status' not in myJson['data'] ) or
                                ( 'crab_status' not in myJson['data'] )):
                                continue
                            if ( 'rucio_status' not in myJson['data'] ):
                                myJson['data']['rucio_status'] = "unknown"
                            myName = myJson['data']['name']
                            if ( cfg['name'] != "*" ):
                                if ( myName != cfg['name'] ):
                                    continue
                            myType = "site"
                            myStatus = myJson['data']['status']
                        elif ( cfg['metric'][:5] == "links" ):
                            if (( 'name' not in myJson['data'] ) or
                                ( 'type' not in myJson['data'] ) or
                                ( 'status' not in myJson['data'] )):
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
                        if tbin not in lget_monitdocs:
                            lget_monitdocs[ tbin ] = []
                        lget_monitdocs[tbin].append( myJson['data'] )
                        #
                        logging.log(15, "   adding [%d] %s / %s : %s" %
                                              (tbin, myName, myType, myStatus))
                    except KeyError:
                        logging.error("No or incomplete metric in hits docum" +
                                      "ent %d" % nDocsCnt)
            except KeyError:
                logging.error("No query hits keys in ElasticSearch response")

        # get next chunk:
        # ===============
        if ( nDocsChnk == 0 ):
            break

    # double check we have all job records:
    # =====================================
    if ( nDocsCnt != nDocsHdr ):
        logging.error("Incomplete metric docs, %d Header versus %d Hit Count" %
                      (nDocsHdr, nDocsCnt))


    if ( logging.getLogger().level <= 20 ):
        no_docs = 0
        for tbin in lget_monitdocs:
            no_docs += len( lget_monitdocs[tbin] )
        logging.info("got %d relevant metric docs in %d timebins in MonIT/ES" %
                                                (no_docs, len(lget_monitdocs)))

    return lget_monitdocs
# ########################################################################### #



def lget_compose_down(cfg, docs):
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
                ctgry = LGET_SERVICE_TYPES[ myDoc['type'] ]
                myOrder = LGET_SERVICE_ORDER.index( ctgry )
            except (KeyError, ValueError):
                myOrder = len( LGET_SERVICE_ORDER )
           # allow 5 min for MonIT importer processing
            if ( (highestVersion - myDoc['***VERSION***']) > 300000 ):
                myOrder += LGET_SUPERSEDED + \
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



def lget_compose_sam(cfg, docs):
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
                myOrder = LGET_SERVICE_ORDER.index( myDoc['type'] )
            except ValueError:
                myOrder = len( LGET_SERVICE_ORDER )
            if ( myDoc['***VERSION***'] < highestVersions[key] ):
                myOrder += LGET_SUPERSEDED + \
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



def lget_compose_hc(cfg, docs):
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



def lget_compose_fts(cfg, docs):
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
                myOrder = LGET_TRANSFER_ORDER.index( myDoc['type'] )
            except ValueError:
                myOrder = len( LGET_TRANSFER_ORDER )
            if ( myDoc['***VERSION***'] < highestVersions[key] ):
                myOrder += LGET_SUPERSEDED + \
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



def lget_compose_sr(cfg, docs):
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



def lget_compose_sts(cfg, docs):
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
                            "      \"crab_status\": \"%s\",\n" +
                            "      \"rucio_status\": \"%s\",\n") %
                           (myDoc['name'], myDoc['status'],
                            myDoc['prod_status'], myDoc['crab_status'],
                            myDoc['rucio_status']))
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



def lget_write_json(cfg, docs):
    """function to write documents as easy readable JSON to a file"""
    # ###################################################### #
    # write the documents as annotated JSON according to cfg #
    # ###################################################### #

    if ( cfg['metric'][:4] == "down" ):
        jsonString = lget_compose_down(cfg, docs)
    elif ( cfg['metric'][:3] == "sam" ):
        jsonString = lget_compose_sam(cfg, docs)
    elif ( cfg['metric'][:2] == "hc" ):
        jsonString = lget_compose_hc(cfg, docs)
    elif ( cfg['metric'][:3] == "fts" ):
        jsonString = lget_compose_fts(cfg, docs)
    elif ( cfg['metric'][:2] == "sr" ):
        jsonString = lget_compose_sr(cfg, docs)
    elif ( cfg['metric'][:3] == "sts" ):
        jsonString = lget_compose_sts(cfg, docs)
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



def lget_print_json(cfg, docs):
    """function to print documents as easy readable JSON to stdout"""
    # ###################################################### #
    # print the documents as annotated JSON according to cfg #
    # ###################################################### #

    if ( cfg['type'][1:] == "rgroup" ):
        logging.error("Writing of JSON for ranking group not implemented")
        return 1

    if ( cfg['metric'][:4] == "down" ):
        jsonString = lget_compose_down(cfg, docs)
    elif ( cfg['metric'][:3] == "sam" ):
        jsonString = lget_compose_sam(cfg, docs)
    elif ( cfg['metric'][:2] == "hc" ):
        jsonString = lget_compose_hc(cfg, docs)
    elif ( cfg['metric'][:3] == "fts" ):
        jsonString = lget_compose_fts(cfg, docs)
    elif ( cfg['metric'][:2] == "sr" ):
        jsonString = lget_compose_sr(cfg, docs)
    elif ( cfg['metric'][:3] == "sts" ):
        jsonString = lget_compose_sts(cfg, docs)
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



def lget_html_header(cfg):
    """function to write top of HTML page written by log for log_getter.py"""
    # ###################################################################### #

    if ( cfg['name'] != "*" ):
        myName = cfg['name']
    else:
        myName = "all"
    if ( cfg['type'] != "*" ):
        myType = cfg['type']
    else:
        myType = "any"
    if (( cfg['before'] == 0 ) and ( cfg['after'] == 0 )):
        myTitle = "%s of %s / %s for %s UTC" % (cfg['title'], myName, myType,
                  time.strftime("%Y-%b-%d %H:%M:%S", time.gmtime(cfg['time'])))
    else:
        tis = cfg['time'] - ( cfg['period'] * cfg['before'] )
        frstStrng = time.strftime("%Y-%b-%d %H:%M:%S", time.gmtime(tis))
        tis = cfg['time'] + ( cfg['period'] * ( cfg['after'] + 1 ) ) - 1
        lastStrng = time.strftime("%Y-%b-%d %H:%M:%S", time.gmtime(tis))
        myTitle = "%s of %s / %s for %s to %s UTC" % (cfg['title'],
                                          myName, myType, frstStrng, lastStrng)
    #
    #
    print(("<HTML lang=en>\n<HEAD>\n   <META charset=\"UTF-8\">\n   <TITLE>C" +
           "MS Log Retrieval</TITLE>\n   <STYLE TYPE=\"text/css\">\n      BO" +
           "DY {\n         background-color: white\n      }\n      A, A:LINK" +
           ", A:VISITED {\n         color:black; text-decoration:none\n     " +
           " }\n      TD A, TD A:LINK, TD A:VISITED {\n         color:black;" +
           " text-decoration:none\n      }\n   </STYLE>\n</HEAD>\n\n<BODY>\n" +
           "<H1>\n   <CENTER>CMS Log Retrieval\n      <SPAN STYLE=\"white-sp" +
           "ace:nowrap; font-size:75%%;\">%s</SPAN>\n   </CENTER>\n</H1>\n") %
          myTitle)
    #
    #
    sys.stdout.flush()

    return



def lget_maindvi_down(cfg, docs):
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
                ctgry = LGET_SERVICE_TYPES[ myDoc['type'] ]
                myOrder = LGET_SERVICE_ORDER.index( ctgry )
            except (KeyError, ValueError):
                myOrder = len( LGET_SERVICE_ORDER )
            # allow 5 min for MonIT importer processing
            if ( (highestVersion - myDoc['***VERSION***']) > 300000 ):
                myOrder += LGET_SUPERSEDED + \
                        int( (highestVersion - myDoc['***VERSION***'])/300000 )
            myDoc['***ORDER***'] = myOrder
        myDocs[tbin] = sorted(docs[tbin],
                 key=lambda k: [k['***ORDER***'], k['name'], k['duration'][0]])


    # write mainDVI downtime HTML section:
    # ====================================
    try:
        myFile = sys.stdout
        if ( True ):
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
                        if ( myDoc['***ORDER***'] > LGET_SUPERSEDED ):
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

    except (IOError, OSError) as excptn:
        logging.critical("Writing of downtime mainDVI section failed, %s" %
                                                                   str(excptn))
        return 1

    logging.log(25, "Downtime docs as HTML table written to stdout")
    return 0



def lget_url4sam(inputString, cfg, tbin, name, clss):
    """function to enhance SAM 15 min results with hyperlinks"""
    # ############################################################### #
    # enhance SAM 15 min results with hyperlink to the evaluation log #
    # ############################################################### #
    LGET_LOG_URL = "https://cmssst.web.cern.ch/cgi-bin/log"
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
                          (LGET_LOG_URL, t15bin, name, myType, n15bin, myLine))
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
                                  (LGET_LOG_URL, tbin, myName, myType, myLine))
            else:
                myHTML += myLine
        else:
            myHTML += myLine
        newlineFlag = True

    return myHTML



def lget_maindvi_sam(cfg, docs):
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
                myOrder = LGET_SERVICE_ORDER.index( myDoc['type'] )
            except ValueError:
                myOrder = len( LGET_SERVICE_ORDER )
            if ( myDoc['***VERSION***'] < highestVersions[key] ):
                myOrder += LGET_SUPERSEDED + \
                    int( (highestVersions[key]-myDoc['***VERSION***'])/300000 )
            myDoc['***ORDER***'] = myOrder
        myDocs[tbin] = sorted(docs[tbin],
                                   key=lambda k: [k['***ORDER***'], k['name']])


    # write mainDVI SAM HTML section:
    # ===============================
    try:
        myFile = sys.stdout
        if ( True ):
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
                        if ( myDoc['***ORDER***'] > LGET_SUPERSEDED ):
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
                                myStrng = lget_url4sam(myDoc['detail'],
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

    except (IOError, OSError) as excptn:
        logging.critical("Writing of CMS SAM mainDVI section failed, %s" %
                                                                   str(excptn))
        return 1

    logging.log(25, "CMS SAM docs as HTML table written to stdout")
    return 0



def lget_url4hc(inputString):
    """function to substitute job references with hyperlinks in a string"""
    # ####################################################################### #
    # replace brackets with a job job reference with hyperlink to the job log #
    # ####################################################################### #
    LGET_HCJOB_URL = ("https://cmsweb.cern.ch/scheddmon/%s/" +
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
                myURL = LGET_HCJOB_URL % (matchObj.group(1),
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



def lget_maindvi_hc(cfg, docs):
    """function to write CMS HC documents as HTML table to a file"""
    # ############################################################### #
    # prepare mainDVI section with CMS HC evaluation according to cfg #
    # ############################################################### #
    LGET_TASKGLBL = "https://monit-grafana.cern.ch/d/cmsTMGlobal/cms-tasks-monitoring-globalview?orgId=11&from=%d000&to=%d000&var-user=sciaba&var-site=All&var-task=All&var-Filters=data.CRAB_Workflow|=~|.*-%s-.*"


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
    try:
        myFile = sys.stdout
        if ( True ):
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
                                myStrng = lget_url4hc( myDoc['detail'] )
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
                                         (LGET_TASKGLBL % (sTIS, eTIS,
                                                               myDoc['name'])))
                        myFile.write("      </TABLE>\n      <BR>\n")
                    else:
                        myFile.write("   <TD>&nbsp;\n")
            myFile.write("</TABLE>\n")

    except (IOError, OSError) as excptn:
        logging.critical("Writing of CMS HC mainDVI section failed, %s" %
                                                                   str(excptn))
        return 1

    logging.log(25, "CMS HC docs as HTML table written to stdout")
    return 0



def lget_url4fts(inputString):
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



def lget_maindvi_fts(cfg, docs):
    """function to write CMS FTS documents as HTML table to a file"""
    # ################################################################ #
    # prepare mainDVI section with CMS FTS evaluation according to cfg #
    # ################################################################ #
    LGET_FTSDASHB = "https://monit-grafana.cern.ch/d/CIjJHKdGk/fts-transfers?orgId=20&from=%d000&to=%d000&var-group_by=endpnt&var-bin=1h&var-vo=cms&var-src_country=All&var-dst_country=All&var-src_site=All&var-dst_site=All&var-fts_server=All&var-protocol=All&var-staging=All"
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
                myOrder = LGET_TRANSFER_ORDER.index( myDoc['type'] )
            except ValueError:
                myOrder = len( LGET_TRANSFER_ORDER )
            if ( myDoc['***VERSION***'] < highestVersions[key] ):
                myOrder += LGET_SUPERSEDED + \
                    int( (highestVersions[key]-myDoc['***VERSION***'])/300000 )
            myDoc['***ORDER***'] = myOrder
        myDocs[tbin] = sorted(docs[tbin],
                                   key=lambda k: [k['***ORDER***'], k['name']])


    # write mainDVI SAM HTML section:
    # ===============================
    try:
        myFile = sys.stdout
        if ( True ):
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
                        if ( myDoc['***ORDER***'] > LGET_SUPERSEDED ):
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
                                myStrng = lget_url4fts( myDoc['detail'] )
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
                                         ((LGET_FTSDASHB % (sTIS, eTIS)),
                                                                myDoc['name']))
                        elif ( myDoc['type'][-11:] == "destination" ):
                            myFile.write(("      <TR>\n         <TD COLSPAN=" +
                                          "\"2\"><A HREF=\"%s&var-filters=da" +
                                          "ta.dst_hostname|=|%s\"><I>Link to" +
                                          " transfers in Grafana FTS dashboa" +
                                          "rd</I></A>\n") % ((LGET_FTSDASHB %
                                                 (sTIS, eTIS)), myDoc['name']))
                        elif ( myDoc['type'][-6:] == "source" ):
                            myFile.write(("      <TR>\n         <TD COLSPAN=" +
                                          "\"2\"><A HREF=\"%s&var-filters=da" +
                                          "ta.src_hostname|=|%s\"><I>Link to" +
                                          " transfers in Grafana FTS dashboa" +
                                          "rd</I></A>\n") % ((LGET_FTSDASHB %
                                                 (sTIS, eTIS)), myDoc['name']))
                        myFile.write("      </TABLE>\n      <BR>\n")
                    else:
                        myFile.write("   <TD>&nbsp;\n")
            myFile.write("</TABLE>\n")

    except (IOError, OSError) as excptn:
        logging.critical("Writing of CMS FTS mainDVI section failed, %s" %
                                                                   str(excptn))
        return 1

    logging.log(25, "CMS FTS docs as HTML table written to stdout")
    return 0



def lget_url4sr(inputString, cfg, tbin, site):
    """function to substitute SiteReadiness SAM,HC,FTS refs with hyperlinks"""
    # ##################################################################### #
    # replace SR SAM,HC,FTS references with hyperlink to the evaluation log #
    # ##################################################################### #
    LGET_LOG_URL = "https://cmssst.web.cern.ch/cgi-bin/log"
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
                       (LGET_LOG_URL, "down15min", t15bin, myLine))
        elif ( myLine[0:10] == "downtime: " ):
            t15bin = tbin * cfg['period'] / 900
            myHTML += ("<A HREF=\"%s/%s/%d/%s/*/day+0\">%s</A>" %
                       (LGET_LOG_URL, "down15min", t15bin, site, myLine))
        elif ( myLine[0:5] == "SAM: " ):
            if ( cfg['period'] == 900 ):
                myHTML += ("<A HREF=\"%s/sam%s/%d/%s/*/0+0\">%s</A>" % 
                         (LGET_LOG_URL, cfg['metric'][2:], tbin, site, myLine))
            else:
                myHTML += ("<A HREF=\"%s/sam%s/%d/%s/site/0+0\">%s</A>" % 
                         (LGET_LOG_URL, cfg['metric'][2:], tbin, site, myLine))
        elif ( myLine[0:4] == "HC: " ):
            myHTML += ("<A HREF=\"%s/hc%s/%d/%s/site/0+0\">%s</A>" %
                       (LGET_LOG_URL, cfg['metric'][2:], tbin, site, myLine))
        elif ( myLine[0:5] == "FTS: " ):
            myHTML += ("<A HREF=\"%s/links%s/%d/%s/*/0+0\">%s</A>" %
                       (LGET_LOG_URL, cfg['metric'][2:], tbin, site, myLine))
        else:
            myHTML += myLine
        newlineFlag = True

    return myHTML



def lget_maindvi_sr(cfg, docs):
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
    try:
        myFile = sys.stdout
        if ( True ):
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
                                myStrng = lget_url4sr( myDoc['detail'], 
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

    except (IOError, OSError) as excptn:
        logging.critical("Writing of CMS SR mainDVI section failed, %s" %
                                                                   str(excptn))
        return 1

    logging.log(25, "CMS SR docs as HTML table written to stdout")
    return 0



def lget_maindvi_sts(cfg, docs):
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
    try:
        myFile = sys.stdout
        if ( True ):
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
                        if ( myDoc['***ORDER***'] > 0 ):
                            myColor = "#DCDCDC"
                        elif ( myDoc['rucio_status'] == "dependable" ):
                            myColor = "#CDFFD4"
                        elif ( myDoc['rucio_status'] == "enabled" ):
                            myColor = "#CDFFD4"
                        elif ( myDoc['rucio_status'] == "new_data_stop" ):
                            myColor = "#FFFFCC"
                        elif ( myDoc['rucio_status'] == "downtime_stop" ):
                            myColor = "#FFFFCC"
                        elif ( myDoc['rucio_status'] == "parked" ):
                            myColor = "#FFFFCC"
                        elif ( myDoc['rucio_status'] == "disabled" ):
                            myColor = "#FFCCCC"
                        else:
                            myColor = "#FFFFFF"
                        myFile.write(("      <TR>\n         <TD NOWRAP>Rucio" +
                                      " Status\n         <TD BGCOLOR=\"%s\" " +
                                      "NOWRAP>%s\n") %
                                     (myColor, myDoc['rucio_status']))
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

    except (IOError, OSError) as excptn:
        logging.critical("Writing of CMS STS mainDVI section failed, %s" %
                                                                   str(excptn))
        return 1

    logging.log(25, "CMS STS docs as HTML table written to stdout")
    return 0



def lget_maindvi_links(cfg, docs):
    """function to write CMS FTS documents as HTML table to a file"""
    # ################################################################## #
    # prepare mainDVI section with CMS Link evaluations according to cfg #
    # ################################################################## #
    LGET_FTSDASHB = "https://monit-grafana.cern.ch/d/CIjJHKdGk/fts-transfers?orgId=20&from=%d000&to=%d000&var-group_by=endpnt&var-bin=1h&var-vo=cms&var-src_country=All&var-dst_country=All&var-src_site=All&var-dst_site=All&var-fts_server=All&var-protocol=All&var-staging=All"
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
        elif (( myDoc['type'] == "destination" ) or
              ( myDoc['type'] == "GSIFTP-destination" )):
            dstDocs[ myDoc['name'] ] = myDoc
        elif ( myDoc['type'] == "WEBDAV-destination" ):
            w_dDocs[ myDoc['name'] ] = myDoc
        elif ( myDoc['type'] == "XROOTD-destination" ):
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
    try:
        myFile = sys.stdout
        if ( True ):
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
                myFile.write(("<TR>\n   <TD COLSPAN=" + "\"2\"><A HREF=\"%s&" +
                              "var-include=%s\"><I>Link to transfers in Graf" +
                              "ana FTS dashboard</I></A>\n") %
                             ((LGET_FTSDASHB % (sTIS, eTIS)),
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
            # write GSIftp source host evaluation tables:
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
                myFile.write(("<TR>\n   <TD COLSPAN=" + "\"2\"><A HREF=\"%s&" +
                              "var-filters=data.src_hostname|=|%s\"><I>Link " +
                              "to transfers in Grafana FTS dashboard</I></A>" +
                              "\n") % ((LGET_FTSDASHB % (sTIS, eTIS)),
                                                      srcDocs[source]['name']))
                myFile.write("</TABLE>\n\n")
            myFile.write("<P>\n<HR>\n\n")
            #
            # write GSIftp destination host evaluation tables:
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
                myFile.write(("<TR>\n   <TD COLSPAN=" + "\"2\"><A HREF=\"%s&" +
                              "var-filters=data.dst_hostname|=|%s\"><I>Link " +
                              "to transfers in Grafana FTS dashboard</I></A>" +
                              "\n") % ((LGET_FTSDASHB % (sTIS, eTIS)),
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
            # write GSIftp link evaluation tables:
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
                    d_strng = lget_url4fts( lnkDocs[link]['detail'] )
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

    except (IOError, OSError) as excptn:
        logging.critical("Writing of CMS links mainDVI section failed, %s" %
                                                                   str(excptn))
        return 1

    logging.log(25, "CMS links doc as HTML table written to stdout")
    return 0



def lget_html_trailer(msgLog):
    """function to write the trailer of the HTML page"""
    # ###################################################################### #

    if ( len( msgLog ) > 0 ):
        msgStrng = msgLog.replace("\n", "<BR>\n")
        if ( msgStrng[-5:] == "<BR>\n" ):
            msgStrng = msgStrng[:-5]
        print("\n<HR>\n\n%s\n" % msgStrng)

    print("\n<HR>\n\n<SMALL>\n   <A HREF=\"http://cern.ch/copyright\">&copy;" +
          " Copyright author, CMS, Fermilab, and others 2019</A>\n</SMALL>\n" +
          "\n</BODY>\n</HTML>")
    #
    sys.stdout.flush()

    return
# ########################################################################### #



if __name__ == '__main__':
    # immediately print new line to keep CGI connection alive:
    print("", flush=True)
    #
    lget_cfg = {}
    rc = 0
    #
    os.umask(0o022)
    #
    parserObj = argparse.ArgumentParser(description="Script to retrieve CMS-" +
        "SSB metric documents from MonIT HDFS and format and write the infor" +
        "mation as HTML table or JSON file. HTTP log retrieval path or metri" +
        "c/name/type/time-stamps can be used to select the documents of inte" +
        "rest.")
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
    parserObj.add_argument("-H", dest="html", default=False,
                                 action="store_true",
                                 help="write document(s) information as HTML" +
                                      " table to stdout")
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
    if ( argStruct.html ):
        logStream = io.StringIO()
        #
        logging.basicConfig(datefmt="%Y-%b-%d %H:%M:%S",
                            format=logFormat, level=logLevel, stream=logStream)
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
        if compList[1] not in LGET_METRICS_DEFINED:
            logging.critical("Unknown metric \"%s\"" % compList[1])
            sys.exit(1)
        else:
            lget_cfg.update( LGET_METRICS_DEFINED[ compList[1] ] )
            lget_cfg['metric'] = compList[1]
        if( compList[2].isdigit() ):
            if ( len(compList[2]) <= 8 ):
                lget_cfg['time'] = int( compList[2] ) * lget_cfg['period']
            elif ( len(compList[2]) == 10 ):
                lget_cfg['time'] = int( compList[2] )
            elif ( len(compList[2]) == 12 ):
                lget_cfg['time'] = calendar.timegm(
                                     time.strptime(compList[2], "%Y%m%d%H%M") )
            elif ( len(compList[2]) == 14 ):
                lget_cfg['time'] = calendar.timegm(
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
            lget_cfg['name'] = "*"
        else:
            if (( siteRegex.match( compList[3] ) is None ) and
                ( compList[3].count(".") < 2 )):
                logging.critical(("Bad site/node specification \"%s\" in URL" +
                                                        "-path") % compList[3])
                sys.exit(1)
            lget_cfg['name'] = compList[3]
        if (( compList[4].lower() == "any" ) or ( compList[4] == "*" ) or
            ( compList[4] == "" )):
            lget_cfg['type'] = "*"
        elif ( compList[4].upper() == "CE" ):
            lget_cfg['type'] = "CE"
        elif (( compList[4].upper() == "SRM" ) or
              ( compList[4].upper() == "SE" )):
            lget_cfg['type'] = "SRM"
        elif ( compList[4].upper() == "XROOTD" ):
            lget_cfg['type'] = "XROOTD"
        elif ( compList[4].lower() == "site" ):
            lget_cfg['type'] = "site"
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
            bBin,aBin = lget_cfg['dfltwin'].split("+")[0:2]
        if ( len(compList) == 7 ):
            if ( compList[6] != "" ):
                logging.critical("URL-path with non-empty sixth field")
                sys.exit(1)
    #
    if argStruct.metric is not None:
        if argStruct.metric not in LGET_METRICS_DEFINED:
            logging.critical("Unknown metric \"%s\"" % argStruct.metric)
            sys.exit(1)
        else:
            lget_cfg.update( LGET_METRICS_DEFINED[ argStruct.metric ] )
            lget_cfg['metric'] = argStruct.metric
    elif argStruct.path is None:
        logging.critical("No document metric specified")
        sys.exit(1)
    #
    if argStruct.timebin is not None:
        if( argStruct.timebin.isdigit() ):
            if ( len(argStruct.timebin) <= 8 ):
                lget_cfg['time'] = int( argStruct.timebin ) * \
                                                             lget_cfg['period']
            elif ( len(argStruct.timebin) == 10 ):
                lget_cfg['time'] = int( argStruct.timebin )
            elif ( len(argStruct.timebin) == 12 ):
                lget_cfg['time'] = calendar.timegm(
                               time.strptime(argStruct.timebin, "%Y%m%d%H%M") )
            elif ( len(argStruct.timebin) == 14 ):
                lget_cfg['time'] = calendar.timegm(
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
            lget_cfg['name'] = "*"
        else:
            if (( siteRegex.match( argStruct.name ) is None ) and
                ( argStruct.name.count(".") < 2 )):
                logging.critical("Bad site/node specification \"%s\"" %
                                                                   compList[3])
                sys.exit(1)
            lget_cfg['name'] = argStruct.name
    elif argStruct.path is None:
        lget_cfg['name'] = "*"
    #
    if argStruct.type is not None:
        if (( argStruct.type.lower() == "any" ) or ( argStruct.type == "*" )):
            lget_cfg['type'] = "*"
        elif ( argStruct.type.upper() == "CE" ):
            lget_cfg['type'] = "CE"
        elif (( argStruct.type.upper() == "SRM" ) or
              ( argStruct.type.upper() == "SE" )):
            lget_cfg['type'] = "SRM"
        elif ( argStruct.type.upper() == "XROOTD" ):
            lget_cfg['type'] = "XROOTD"
        elif ( argStruct.type.lower() == "site" ):
            lget_cfg['type'] = "site"
        else:
            logging.critical("Unknown service type \"%s\"" % argStruct.type)
            sys.exit(1)
    elif argStruct.path is None:
        lget_cfg['type'] = "*"
    #
    if argStruct.window is not None:
        if ( argStruct.window.find("+") > 0 ):
            bBin,aBin = compList[5].split("+")[0:2]
        else:
            logging.critical("Bad timebin window parameter \"%s\"" %
                                                              argStruct.window)
            sys.exit(1)
    elif argStruct.path is None:
        bBin,aBin = lget_cfg['dfltwin'].split("+")[0:2]
    #
    if ( bBin == "day" ):
        lget_cfg['before'] = int( (lget_cfg['time'] % 86400) /
                                                           lget_cfg['period'] )
    elif ( bBin.isdigit() ):
        lget_cfg['before'] = int(bBin)
    elif (( bBin is None ) or ( bBin == "" )):
        lget_cfg['before'] = 0
    else:
        logging.critical("Bad before-timebin window parameter \"%s\"" % bBin)
        sys.exit(1)
    if ( aBin == "day" ):
        lget_cfg['after'] = int( ( 86400 - (lget_cfg['time'] % 86400) ) /
                                                       lget_cfg['period'] ) - 1
    elif ( aBin.isdigit() ):
        lget_cfg['after'] = int(aBin)
    elif (( aBin is None ) or ( aBin == "" )):
        lget_cfg['after'] = 0
    else:
        logging.critical("Bad after-timebin window parameter \"%s\"" % aBin)
        sys.exit(1)
    #
    if argStruct.json is not None:
        lget_cfg['json'] = allowedCharRegex.sub("", argStruct.json )



    # fetch relevant MonIT documents:
    # ===============================
    lget_monitdocs = lget_grafana_fetch(lget_cfg)



    # write docs in annotated JSON format to file:
    # ============================================
    if 'json' in lget_cfg:
        rc += lget_write_json(lget_cfg, lget_monitdocs)



    # write docs in HTML table format as mainDVI section to file:
    # ===========================================================
    if ( argStruct.html ):
        lget_html_header(lget_cfg)
        #
        if ( lget_cfg['metric'][:4] == "down" ):
            rc += lget_maindvi_down(lget_cfg, lget_monitdocs)
        elif ( lget_cfg['metric'][:3] == "sam" ):
            rc += lget_maindvi_sam(lget_cfg, lget_monitdocs)
        elif ( lget_cfg['metric'][:2] == "hc" ):
            rc += lget_maindvi_hc(lget_cfg, lget_monitdocs)
        elif ( lget_cfg['metric'][:3] == "fts" ):
            rc += lget_maindvi_fts(lget_cfg, lget_monitdocs)
        elif ( lget_cfg['metric'][:2] == "sr" ):
            rc += lget_maindvi_sr(lget_cfg, lget_monitdocs)
        elif ( lget_cfg['metric'][:3] == "sts" ):
            rc += lget_maindvi_sts(lget_cfg, lget_monitdocs)
        elif ( lget_cfg['metric'][:5] == "links" ):
            rc += lget_maindvi_links(lget_cfg, lget_monitdocs)
        #
        logging.shutdown()
        lget_html_trailer( logStream.getvalue() )



    # print docs in annotated JSON format to stdout:
    # ==============================================
    if (( 'json' not in lget_cfg ) and ( argStruct.html == False )):
        rc += lget_print_json(lget_cfg, lget_monitdocs)



    #import pdb; pdb.set_trace()
    if ( rc != 0 ):
        sys.exit(1)
    sys.exit(0)
