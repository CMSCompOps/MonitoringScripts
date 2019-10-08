#!/data/cmssst/packages/bin/python3.7
# ########################################################################### #
# python script to query the OSG and EGI downtime databases and upload a JSON
#    document to MonIT with the downtimes of hosts relevant to CMS operations
#    during the previous 45 days and future 15 days. The script creates a new
#    document for each day and in case of a downtime addition/change/removal.
#
# 2018-Nov-26   Stephan Lammel
# ########################################################################### #
# "data": {
#      "name":     "T1_US_FNAL" | "cmsdcadisk01.fnal.gov",
#      "type":     "site" | "XRootD origin server",
#      "status":   "downtime | partial | adhoc | atrisk",
#      "duration": [1510234650, 1510235550],
#      "detail":   "OSG:1005707" | "EGI:24466"
# }
# https://goc.egi.eu/portal/index.php?Page_Type=Downtime&id=24466
# https://my.opensciencegrid.org/rgdowntime/xml?downtime_attrs_showpast=all



import os, sys
import argparse
import logging
import time, calendar
import ssl
import http.client
import urllib.request, urllib.error
import xml.etree.ElementTree
import json
import gzip
#
# setup the Java/HDFS/PATH environment for pydoop to work properly:
os.environ["HADOOP_CONF_DIR"] = "/opt/hadoop/conf/etc/analytix/hadoop.analytix"
os.environ["JAVA_HOME"]       = "/etc/alternatives/jre"
os.environ["HADOOP_PREFIX"]   = "/usr/hdp/hadoop"
import pydoop.hdfs
# ########################################################################### #



#EVDT_CACHE_DIR = "./cache"
EVDT_CACHE_DIR = "/data/cmssst/MonitoringScripts/downtime/cache"
#EVHC_MONIT_URL = ""
#EVHC_MONIT_URL = "http://monit-metrics-dev.cern.ch:10012/"
EVHC_MONIT_URL = "http://monit-metrics.cern.ch:10012/"
# ########################################################################### #



evdt_glbl_topology = { '*hash*': [] }
evdt_glbl_types = { 'CE': "CE",
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
                    'gLExec': "",
                    'APEL': "", 'gLite-APEL': "",
                    'SRM.nearline': "", 'FTS': "",
                    'Local-LFC': "", 'Central-LFC': "", 'VO-box': "",
                    'UI': "", 'LB': "", 'VOMS': "", 'MyProxy': "", 'WMS': "",
                    'emi.ARGUS': "", 'ngi.ARGUS': "",
                    'eu.egi.storage.accounting': "",
                    'Top-BDII': "", 'Site-BDII': "", 'egi.GOCDB': "",
                    'ngi.SAM': "", 'MON': "" }
evdt_glbl_downtimes = []
evdt_glbl_monitdocs = []
evdt_glbl_status = [ "downtime", "partial", "adhoc", "atrisk" ]
# ########################################################################### #



class HTTPSClientAuthHandler(urllib.request.HTTPSHandler):
    """urllib.request.HTTPSHandler class with certificate access"""

    def __init__(self):
        urllib.request.HTTPSHandler.__init__(self)

    def https_open(self, req):
        return self.do_open(self.getConnection, req)

    def getConnection(self, host, timeout=15):
        return http.client.HTTPSConnection(host, key_file=EVDT_CERTIFICATE_KEY,
                                                 cert_file=EVDT_CERTIFICATE_CRT)
# ########################################################################### #



def evdt_add_service(site, host, type, prod):
    """low-level function to add a service to the global topology dictionary"""
    # ############################################################ #
    # add a site-service entry into the global topology dictionary #
    # ############################################################ #
    global evdt_glbl_topology

    if (( site == "" ) or ( host == "" )):
        return

    if type not in evdt_glbl_types:
        logging.warning("Service at %s on host %s of unknown type \"%s\"" %
                        (site, host, type))

    if site not in evdt_glbl_topology:
        evdt_glbl_topology[ site ] = []

    if type not in evdt_glbl_types:
        ctgry = ""
    else:
        ctgry = evdt_glbl_types[ type ]
    service = {'host': host, 'type': type, 'prod': prod, 'category': ctgry}
    if service not in evdt_glbl_topology[ site ]:
        evdt_glbl_topology[ site ].append( service )
        evdt_glbl_topology[ "*hash*" ].clear()
        logging.debug("Service at %s added: %s %s %r" %
                      (site, host, type, prod))

    return

def evdt_check_service(host, type):
    """low-level function to check if a service belongs to/is used by CMS"""
    # ########################################################### #
    # check if a service exists in the global topology dictionary #
    # ########################################################### #
    global evdt_glbl_topology

    if ( host == "" ):
        return False

    if ( len( evdt_glbl_topology[ "*hash*" ] ) == 0 ):
        # create (host, category) tuple hash
        for site in evdt_glbl_topology:
            if ( site[0] == "*" ):
                continue
            for service in evdt_glbl_topology[ site ]:
                evdt_glbl_topology[ "*hash*" ].append( (service['host'],
                                                        service['category']) )

    if  type not in evdt_glbl_types:
        logging.warning("Service on host %s of unknown type \"%s\"" %
                        (host, type))
        category = ""
    else:
        category = evdt_glbl_types[ type ]

    if (host, category) in evdt_glbl_topology[ "*hash*" ]:
        return True

    return False

def evdt_add_downtime(name, type, status, start, stop, detail):
    """low-level function to add a downtime to the global downtime list"""
    # ##################################################### #
    # add a downtime dictionary to the global downtime list #
    # ##################################################### #
    global evdt_glbl_downtimes

    if ( name == "" ):
        return
    if status not in evdt_glbl_status:
        return

    if type not in evdt_glbl_types:
        ctgry = ""
    else:
        ctgry = evdt_glbl_types[ type ]

    downtime = {'name': name, 'type': type, 'status': status,
                'duration': (start, stop), 'detail': detail,
                'category': ctgry}

    evdt_glbl_downtimes.append( downtime )
    logging.debug("Downtime for %s / %s added: %d to %d (%s)" %
                  (name, type, start, stop, status))

    return

def evdt_del_site_downtimes():
    """low-level function to remove site downtimes from the global list"""
    # ####################################################### #
    # delete all site downtimes from the global downtime list #
    # ####################################################### #
    global evdt_glbl_downtimes

    evdt_glbl_downtimes = [ d for d in evdt_glbl_downtimes
                            if ( d['type'] != "site" ) ]

    return

def evdt_get_site_downtimes(downtimes):
    """low-level function to extract site downtimes from the provided list"""
    # ###################################################### #
    # return all site downtimes from the input downtime list #
    # ###################################################### #

    return [ d for d in downtimes if ( d['type'] == "site" ) ]
# ########################################################################### #



def evdt_vofeed():
    """function to fetch site topology information of CMS"""
    # ################################################################# #
    # fill evdt_glbl_topology with service information of the CMS sites #
    # ################################################################# #
    URL_VOFEED = "http://dashb-cms-vo-feed.cern.ch/dashboard/request.py/cmssitemapbdii"

    # get list of host and flavours for CMS sites from the VO-feed:
    # =============================================================
    logging.info("Querying VO-feed for site service information")
    urlHndl = None
    try:
        urlHndl = urllib.request.urlopen(URL_VOFEED)
        myCharset = urlHndl.headers.get_content_charset()
        if myCharset is None:
            myCharset = "utf-8"
        myData = urlHndl.read().decode( myCharset )
        del(myCharset)
        #
        # update cache:
        try:
            myFile = open("%s/vofeed.xml_new" % EVDT_CACHE_DIR, 'w')
            try:
                myFile.write(myData)
                renameFlag = True
            except:
                renameFlag = False
            finally:
                myFile.close()
                del myFile
            if renameFlag:
                os.rename("%s/vofeed.xml_new" % EVDT_CACHE_DIR,
                          "%s/vofeed.xml" % EVDT_CACHE_DIR)
                logging.info("   cache of VO-feed updated")
            del renameFlag
        except:
            pass
    except:
        logging.warning("Failed to fetch VO-feed data")
        try:
            myFile = open("%s/vofeed.xml" % EVDT_CACHE_DIR, 'r')
            try:
                myData = myFile.read()
                logging.info("   using cached VO-feed data")
            except:
                logging.error("Failed to access cached VO-feed data")
                return
            finally:
                myFile.close()
                del myFile
        except:
            logging.error("No VO-feed cache available")
            return
    finally:
        if urlHndl is not None:
            urlHndl.close()
    del urlHndl
    #
    # unpack XML data of the VO-feed:
    vofeed = xml.etree.ElementTree.fromstring( myData )
    del myData
    #
    # loop over site elements (multiple entries per grid and CMS site possible):
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
        for service in atpsite.findall('service'):
            if 'hostname' not in service.attrib:
                continue;
            host = service.attrib['hostname'].lower()
            if 'flavour' not in service.attrib:
                continue;
            type = service.attrib['flavour']
            if 'production_status' not in service.attrib:
                prod = True
            elif ( service.attrib['production_status'].lower() == "false" ):
                prod = False
            else:
                prod = True
            evdt_add_service(cmssite, host, type, prod)



def evdt_osg_downtime(start15m, limit15m):
    """function to fetch service downtime information from OSG"""
    # ################################################################ #
    # fill sswp_sites site element arrays with OSG downtime informaton #
    # ################################################################ #
    startTIS = start15m * 900
    limitTIS = limit15m * 900
    noDays = min(0, int( ( time.time() - startTIS ) / 86400 ) ) + 1
    URL_OSG_DOWNTIME = "http://my.opensciencegrid.org/rgdowntime/xml?downtime_attrs_showpast=%d&gridtype=on&gridtype_1=on&active=on&active_value=1" % noDays

    # get list of all CMS impacting downtimes from OSG:
    # =================================================
    logging.info("Querying OSG for downtime information")
    urlHndl = None
    try:
        urlHndl = urllib.request.urlopen(URL_OSG_DOWNTIME)
        myCharset = urlHndl.headers.get_content_charset()
        if myCharset is None:
            myCharset = "utf-8"
        myData = urlHndl.read().decode( myCharset )
        del(myCharset)
        #
        # update cache:
        try:
            myFile = open("%s/osg_downtime.xml_new" % EVDT_CACHE_DIR, 'w')
            try:
                myFile.write(myData)
                renameFlag = True
            except:
                renameFlag = False
            finally:
                myFile.close()
                del myFile
            if renameFlag:
                os.rename("%s/osg_downtime.xml_new" % EVDT_CACHE_DIR,
                          "%s/osg_downtime.xml" % EVDT_CACHE_DIR)
                logging.info("   cache of OSG downtime updated")
            del renameFlag
        except:
            pass
    except:
        logging.warning("Failed to fetch OSG downtime data")
        try:
            myFile = open("%s/osg_downtime.xml" % EVDT_CACHE_DIR, 'r')
            try:
                myData = myFile.read()
                logging.info("   using cached OSG downtime data")
            except:
                logging.error("Failed to access cached OSG downtime data")
                return
            finally:
                myFile.close()
                del myFile
        except:
            logging.error("No OSG downtime cache available")
            return
    finally:
        if urlHndl is not None:
            urlHndl.close()
    del urlHndl


    # unpack XML data of the OSG downtime information:
    downtimes = xml.etree.ElementTree.fromstring( myData )
    del myData
    #
    # loop over downtime-type (Past, Current, Future) elements:
    for downtypes in downtimes:
        # loop over downtime elements:
        for downtime in downtypes.findall('Downtime'):
            id = downtime.findtext('ID', default="")
            if ( id == "" ):
                logging.warning("OSG downtime entry without id, skipping")
                continue
            host = downtime.findtext('ResourceFQDN', default="").lower()
            if ( host == "" ):
                logging.warning("OSG downtime entry without FQDN, skipping")
                continue
            #
            timeStr = downtime.findtext('StartTime', default="")
            if (( len(timeStr) != 25 ) or ( timeStr[6:10] != ", 20" )):
                logging.error("Bad StartTime format \"%s\", OSG downtime %s" %
                              (timeStr, id))
                continue
            ts = time.strptime(timeStr, "%b %d, %Y %H:%M %p %Z")
            start = calendar.timegm(ts)
            if ( start >= limitTIS ):
                continue
            #
            timeStr = downtime.findtext('EndTime', default="")
            if (( len(timeStr) != 25 ) or ( timeStr[6:10] != ", 20" )):
                logging.error("Bad EndTime format \"%s\", OSG downtime %s" %
                              (timeStr, id))
                continue
            ts = time.strptime(timeStr, "%b %d, %Y %H:%M %p %Z")
            end = calendar.timegm(ts)
            if ( end < startTIS ):
                continue
            #
            severity = downtime.findtext('Severity', default="").lower()
            if (( severity == 'outage' ) or ( severity == 'severe' )):
                schedld = downtime.findtext('Class', default="").upper()
                timeStr = downtime.findtext('CreatedTime', default="")
                if (( len(timeStr) != 25 ) or ( timeStr[6:10] != ", 20" )):
                    if ( timeStr != "Not Available" ):
                        logging.warning(("No/bad CreatedTime format \"%s\", " +
                                         "OSG downtime %s") % (timeStr, id))
                    flip = None
                else:
                    ts = time.strptime(timeStr, "%b %d, %Y %H:%M %p %Z")
                    flip = calendar.timegm(ts) + 86400
                if ( schedld == 'SCHEDULED' ):
                    status = "downtime"
                    if flip is None:
                        flip = 0
                    # scheduled downtime requires 24 hour advanced notice
                    if ( flip <= start ):
                        flip = None
                    elif (flip >= end ):
                        status = "adhoc"
                        flip = None
                    elif ( flip <= startTIS ):
                        start = flip
                        flip = None
                    else:
                        status = "adhoc"
                else:
                    status = "adhoc"
                    if flip is None:
                        flip = start + 86400
                    # auto-promote adhoc to scheduled after 24 hours
                    if (flip >= end ):
                        flip = None
                    elif ( flip <= start ):
                        status = "downtime"
                        flip = None
                    elif ( flip <= startTIS ):
                        start = flip
                        flip = None
                        status = "downtime"
            else:
                status = "atrisk"
                flip = None
            #
            services = downtime.find('Services')
            if not services:
                continue
            for service in services.findall('Service'):
                type = service.findtext('Name', default="")
                if not evdt_check_service(host, type):
                    continue
                detail = "OSG:" + id
                if flip is None:
                    evdt_add_downtime(host, type, status, start, end, detail)
                else:
                    evdt_add_downtime(host, type, status, start, flip, detail)
                    status = "downtime"
                    evdt_add_downtime(host, type, status, flip, end, detail)



def evdt_egi_downtime(start15m, limit15m):
    """function to fetch service downtime information from EGI"""
    # ################################################################ #
    # fill sswp_sites site element arrays with EGI downtime informaton #
    # ################################################################ #
    startTIS = start15m * 900
    limitTIS = limit15m * 900
    ts1 = time.gmtime( startTIS - 86400 )
    ts2 = time.gmtime( limitTIS + 86400 )
    URL_EGI_DOWNTIME = "https://goc.egi.eu/gocdbpi/public/?method=get_downtime&windowstart=%d-%02d-%02d&windowend=%d-%02d-%02d&scope=" % (ts1[0], ts1[1], ts1[2], ts2[0], ts2[1], ts2[2])

    # get list of all downtimes that could impact CMS from EGI:
    # =========================================================
    logging.info("Querying EGI for downtime information")
    urlHndl = None
    try:
        myContext = ssl._create_unverified_context()
        urlHndl = urllib.request.urlopen(URL_EGI_DOWNTIME, context=myContext)
        del(myContext)
        myCharset = urlHndl.headers.get_content_charset()
        if myCharset is None:
            myCharset = "utf-8"
        myData = urlHndl.read().decode( myCharset )
        del(myCharset)
        #
        # update cache:
        try:
            myFile = open("%s/egi_downtime.xml_new" % EVDT_CACHE_DIR, 'w')
            try:
                myFile.write(myData)
                renameFlag = True
            except:
                renameFlag = False
            finally:
                myFile.close()
                del myFile
            if renameFlag:
                os.rename("%s/egi_downtime.xml_new" % EVDT_CACHE_DIR,
                          "%s/egi_downtime.xml" % EVDT_CACHE_DIR)
                logging.info("   cache of EGI downtime updated")
            del renameFlag
        except:
            pass
    except:
        logging.warning("Failed to fetch EGI downtime data")
        try:
            myFile = open("%s/egi_downtime.xml" % EVDT_CACHE_DIR, 'r')
            try:
                myData = myFile.read()
                logging.info("   using cached EGI downtime data")
            except:
                logging.error("Failed to access cached EGI downtime data")
                return
            finally:
                myFile.close()
                del myFile
        except:
            logging.error("No EGI downtime cache available")
            return
    finally:
        if urlHndl is not None:
            urlHndl.close()
    del urlHndl


    # unpack XML data of the EGI downtime information:
    downtimes = xml.etree.ElementTree.fromstring( myData )
    del myData
    #
    # loop over downtime elements:
    for downtime in downtimes.findall('DOWNTIME'):
        id = downtime.attrib.get('ID')
        if id is None:
            logging.warning("EGI downtime entry without id, skipping")
            continue
        host = downtime.findtext('HOSTNAME', default="").lower()
        if ( host == "" ):
            logging.warning("EGI downtime entry without HOSTNAME, skipping")
            continue
        #
        timeStr = downtime.findtext('START_DATE', default="")
        if ( not timeStr.isdigit() ):
            logging.error("Bad StartDate format \"%s\", EGI downtime %s" %
                          (timeStr, id))
            continue
        start = int( timeStr )
        if ( start >= limitTIS ):
            continue
        #
        timeStr = downtime.findtext('END_DATE', default="")
        if ( not timeStr.isdigit() ):
            logging.error("Bad EndDate format \"%s\", EGI downtime %s" %
                          (timeStr, id))
            continue
        end = int( timeStr )
        if ( end < startTIS ):
            continue
        #
        severity = downtime.findtext('SEVERITY', default="").upper()
        if ( severity == 'OUTAGE' ):
            schedld = downtime.attrib.get('CLASSIFICATION', "")
            if ( schedld == 'SCHEDULED' ):
                status = "downtime"
                flip = None
            else:
                status = "adhoc"
                flip = start + 259200
                timeStr = downtime.findtext('INSERT_DATE', default="")
                if ( timeStr.isdigit() ):
                    iflip = int( timeStr ) + 86400
                    if ( iflip < flip ):
                        flip = iflip
                # auto-promote adhoc to scheduled after known 24 hours
                if (flip >= end ):
                    flip = None
                elif ( flip <= startTIS ):
                    start = flip
                    flip = None
                    status = "downtime"
        else:
            status = "atrisk"
            flip = None
        type = downtime.findtext('SERVICE_TYPE', default="")
        if not evdt_check_service(host, type):
            continue
        detail = "EGI:" + id
        if flip is None:
            evdt_add_downtime(host, type, status, start, end, detail)
        else:
            evdt_add_downtime(host, type, status, start, flip, detail)
            status = "downtime"
            evdt_add_downtime(host, type, status, flip, end, detail)
# ########################################################################### #



def evdt_site_status(sitename, downtimes, startTIS, limitTIS, noCE, noXRD):
    """function to evaluate site downtime status for one site and one period"""
    # ########################################################## #
    # evaluate site status for downtimes during start-end period #
    # ########################################################## #

    status = "ok"
    downCE = []
    downXRD = []
    detail = None
    ceDetail = None
    xrdDetail = None
    for downtime in downtimes:
        if ( downtime['duration'][0] >= limitTIS ):
            continue
        if ( downtime['duration'][1] <= startTIS ):
            continue
        #
        if ((( status != "downtime") and ( downtime['status'] == status )) or
            (( status == "partial" ) and ( downtime['status'] == "downtime" ))):
            detail += ", " + downtime['name'] + "/" + downtime['category']
        if (( downtime['status'] == "atrisk" ) and ( status == "ok" )):
            status = "atrisk"
            detail =  downtime['name'] + "/" + downtime['category']
        elif (( downtime['status'] == "adhoc" ) and (( status == "ok" ) or
                                                     ( status == "atrisk" ))):
            status = "adhoc"
            detail =  downtime['name'] + "/" + downtime['category']
        elif ( downtime['status'] == "downtime" ):
            if (( status != "partial" ) and ( status != "downtime" )):
                status = "partial"
                detail =  downtime['name'] + "/" + downtime['category']
            if ( downtime['category'] == "CE" ):
                if ( len(downCE) == 0 ):
                    downCE = [ downtime['name'] ]
                    ceDetail = downtime['name']
                elif downtime['name'] not in downCE:
                    downCE.append(downtime['name'])
                    ceDetail += ", " + downtime['name']
            elif ( downtime['category'] == "SRM" ):
                if ( status != "downtime" ):
                    status = "downtime"
                    detail =  downtime['name'] + "/" + downtime['category']
                else:
                    detail += ", " + downtime['name'] + "/" + \
                              downtime['category']
            elif ( downtime['category'] == "XROOTD" ):
                if ( len(downXRD) == 0 ):
                    downXRD = [ downtime['name'] ]
                    xrdDetail = downtime['name']
                elif downtime['name'] not in downXRD:
                    downXRD.append(downtime['name'])
                    xrdDetail += ", " + downtime['name']
    if (( noCE > 0 ) and ( len(downCE) == noCE )):
        if ( status != "downtime" ):
            status = "downtime"
            detail = "All CEs (" + ceDetail + ")"
        else:
            detail += ", all CEs (" + ceDetail + ")"
    if (( noXRD > 0 ) and ( len(downXRD) == noXRD )):
        if ( status != "downtime" ):
            status = "downtime"
            detail = "All XROOTDs (" + xrdDetail + ")"
        else:
            detail += ", all XROOTDs (" + xrdDetail + ")"

    # add downtime to evdt_glbl_downtimes:
    # ====================================
    if ( status != "ok" ):
        evdt_add_downtime(sitename, "site", status, startTIS, limitTIS, detail)

    return



def evdt_site_downtime(start15m, limit15m):
    """function to evaluate site downtime status for all sites and periods"""
    # ############################################################## #
    # evaluate site downtime status for sites from bin15m bin onward #
    # ############################################################## #
    startTIS = start15m * 900
    limitTIS = limit15m * 900

    # evaluate site downtime status:
    # ==============================
    for site in evdt_glbl_topology:
        if ( site[0] == "*" ):
            continue

        # select downtimes of site and make list of status boundaries:
        # ============================================================
        relevant = []
        boundary = []
        for downtime in evdt_glbl_downtimes:
            if ( downtime['type'] == "site" ):
                continue
            for service in evdt_glbl_topology[ site ]:
                if (( downtime['name'] == service['host'] ) and
                    ( downtime['category'] == service['category'] ) and
                    service['prod'] ):
                    relevant.append( downtime )
                    if downtime['duration'][0] not in boundary:
                        boundary.append( downtime['duration'][0] )
                    if downtime['duration'][1] not in boundary:
                        boundary.append( downtime['duration'][1] )
                    break

        logging.debug("Site %s has %d relevant downtimes with %d boundaries" %
                      (site, len(relevant), len(boundary)))
        if ( len(relevant) == 0 ):
            # no relevant downtime(s) for the site
            continue

        # count number of CE and XROOTD services at site:
        # ===============================================
        noCE = 0
        noXRD = 0
        for service in evdt_glbl_topology[ site ]:
            if not service['prod']:
                continue
            if ( service['category'] == "CE" ):
                noCE += 1
            elif ( service['category'] == "XROOTD" ):
                noXRD += 1

        # evaluate site status for downtime periods:
        # ==========================================
        boundary.sort()
        for period in range(1, len(boundary)):
            if ( boundary[period] < startTIS ):
                continue
            if ( boundary[period-1] >= limitTIS ):
                break
            evdt_site_status(site, relevant, boundary[period-1],
                                             boundary[period], noCE, noXRD)

    return
# ########################################################################### #



def evdt_json_arraystring(bin15m, downtimes):
    """function to convert downtime list to a JSON list of dictionaries"""
    # ################################################################## #
    # write JSON string with downtime list that can be uploaded to MonIT #
    # ################################################################## #

    if ( len(downtimes) == 0 ):
        downtimes = [ {'name': "*", 'type': "*", 'status': "ok",
                       'duration': [(bin15m*900),((bin15m*900)+899)],
                       'detail': None} ]

    jsonStr = "[\n "
    hdrStr = (("{\n   \"producer\": \"cmssst\",\n" +
               "   \"type\": \"ssbmetric\",\n" +
               "   \"path\": \"down15min\",\n" +
               "   \"timestamp\": %d,\n" +
               "   \"type_prefix\": \"raw\",\n" +
               "   \"data\": {\n") % (((bin15m * 900) + 450) * 1000))
 
    commaFlag = False
    for downtime in sorted(downtimes, key=lambda k: [k['name'], k['type'],
                                          k['duration'][0], k['duration'][1]]):
        if commaFlag:
            jsonStr += ",\n " + hdrStr
        else:
            jsonStr += hdrStr
        #
        jsonStr += (("      \"name\": \"%s\",\n" +
                     "      \"type\": \"%s\",\n" +
                     "      \"status\": \"%s\",\n" +
                     "      \"duration\": [%d, %d],\n") %
                    (downtime['name'], downtime['type'], downtime['status'],
                     downtime['duration'][0], downtime['duration'][1]))
        if downtime['detail'] is not None:
            jsonStr += ("      \"detail\": \"%s\"\n   }\n }" %
                        downtime['detail'])
        else:
            jsonStr += ("      \"detail\": null\n   }\n }")
        commaFlag = True
    jsonStr += "\n]"
    return jsonStr



def evdt_upload_jsonstring(jsonString):
    """function to post downtime information to MonIT"""
    # ############################################### #
    # upload JSON string with downtime array to MonIT #
    # ############################################### #

    try:
        # MonIT needs a document/array of documents without newline characters:
        jsonBytes = json.dumps(json.loads(jsonString)).encode("utf-8")
        #
        requestObj = urllib.request.Request(EVHC_MONIT_URL, data=jsonBytes,
            headers={'Content-Type': "application/json; charset=UTF-8"},
            method="POST")
        #
        #openerDir = urllib.request.build_opener( HTTPSClientAuthHandler() )
        #responseObj = openerDir.open( requestObj )
        #
        responseObj = urllib.request.urlopen( requestObj, timeout=15 )
    except ConnectionError:
        logging.error("Failed to upload downtime JSON, connection error")
    except TimeoutError:
        logging.error("Failed to upload downtime JSON, reached 15 sec timeout")
    except urllib.error.HTTPError as excptn:
        logging.error("Failed to upload downtime JSON, HTTP error %d \"%s\"" %
                      (excptn.status, excptn.reason))
    except Exception as excptn:
        logging.error("Failed to upload downtime JSON, %s" % str(excptn))
    else:
        logging.info("Downtime JSON string uploaded to MonIT")

    return
# ########################################################################### #



def evdt_monit_downtime(start15m, limit15m):
    """function to fetch downtime information documents from MonIT"""
    # ################################################################# #
    # fill global document list with downtime documents from MonIT/HDFS #
    # ################################################################# #
    global evdt_glbl_monitdocs
    startTIS = start15m * 900
    limitTIS = limit15m * 900
    #PATH_HDFS_PREFIX = "/project/monitoring/archive_qa/cmssst/raw/ssbmetric/"
    PATH_HDFS_PREFIX = "/project/monitoring/archive/cmssst/raw/ssbmetric/"

    # prepare HDFS subdirectory list:
    # ===============================
    logging.info("Retrieving downtime docs from MonIT HDFS")
    logging.debug("   starting time bin %d (%s), limit %d (%s)" %
                  (start15m, time.strftime("%Y-%m-%d %H:%M",
                                         time.gmtime(startTIS)),
                   limit15m, time.strftime("%Y-%m-%d %H:%M",
                                         time.gmtime(limitTIS))))
    #
    tisDay = 24*60*60
    ts = time.gmtime( startTIS )
    startMidnight = calendar.timegm( ts[:3] + (0, 0, 0) + ts[6:] )
    now = int( time.time() )
    startTmpArea = calendar.timegm( time.gmtime( now - (6 * tisDay) ) )
    limitLocalTmpArea = calendar.timegm( time.localtime( now ) ) + tisDay
    #
    dirList = []
    for dirDay in range(startMidnight, limitTIS, tisDay):
        dirList.append( time.strftime("down15min/%Y/%m/%d",
                                      time.gmtime( dirDay )) )
    for dirDay in range(startTmpArea, limitLocalTmpArea, tisDay):
        dirList.append( time.strftime("down15min/%Y/%m/%d.tmp",
                                      time.gmtime( dirDay )) )
    del(dirDay)

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
                del(myList)
                for fileName in fileNames:
                    logging.debug("   reading file %s" %
                                  os.path.basename(fileName))
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
                            if (( "metadata" not in myJson ) or
                                ( "data" not in myJson )):
                                continue
                            if (( "timestamp" not in myJson['metadata'] ) or
                                ( "kafka_timestamp" not in myJson['metadata'] ) or
                                ( "path" not in myJson['metadata'] ) or
                                ( "name" not in myJson['data'] ) or
                                ( "type" not in myJson['data'] ) or
                                ( "status" not in myJson['data'] ) or
                                ( "duration" not in myJson['data'] )):
                                continue
                            if ( myJson['metadata']['path'] != "down15min" ):
                                continue
                            bin15m = int(myJson['metadata']['timestamp']/900000)
                            if ( bin15m < start15m ):
                                continue
                            if ( bin15m >= limit15m ):
                                continue
                            if "partition" in myJson['metadata']:
                                del myJson['metadata']['partition']
                            if "type_prefix" in myJson['metadata']:
                                del myJson['metadata']['type_prefix']
                            if "topic" in myJson['metadata']:
                                del myJson['metadata']['topic']
                            if "producer" in myJson['metadata']:
                                del myJson['metadata']['_id']
                            if "type" in myJson['metadata']:
                                del myJson['metadata']['type']
                            # convert duration back to integer:
                            start = int( myJson['data']['duration'][0] )
                            end = int( myJson['data']['duration'][1] )
                            myJson['data']['duration'] = (start, end)
                            #
                            evdt_glbl_monitdocs.append( myJson )
                    except IOError as err:
                        logging.error("IOError accessing HDFS file %s: %s" %
                                                       (fileName, err.message))
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
        logging.error("Failed to fetch downtime information from MonIT HDFS")

    logging.info("   found %d relevant downtime docs in MonIT" %
                 len(evdt_glbl_monitdocs))
    return



def evdt_previous_monitdoc(before15m):
    """function to find the last downtime document before the time bin"""
    # ################################################################### #
    # get time bin of most-recent prior to time-bin downtime doc in MonIT #
    # ################################################################### #

    logging.info("Searching MonIT docs for downtime doc prior to %d (%s)" %
                 (before15m, time.strftime("%Y-%m-%d %H:%M",
                                           time.gmtime(before15m * 900))))

    prior15m = 0
    for monitdoc in evdt_glbl_monitdocs:
        doc15m = int( monitdoc['metadata']['timestamp'] / 900000 )
        if ( doc15m >= before15m ):
            continue
        if ( doc15m <= prior15m ):
            continue
        prior15m = doc15m

    logging.info("   previous downtime doc, time bin %d (%s)" %
                 (prior15m, time.strftime("%Y-%m-%d %H:%M",
                                          time.gmtime(prior15m * 900))))
    return prior15m



def evdt_check_monitdoc(bin15m, downtimes):
    """function to check if MonIT contains a specific downtime document"""
    # ####################################################################### #
    # check there is a doc in MonIT for time-bin and with identical downtimes #
    # ####################################################################### #

    logging.info("Checking MonIT docs for %d (%s) and its downtimes" %
                 (bin15m, time.strftime("%Y-%m-%d %H:%M",
                                        time.gmtime(bin15m * 900))))

    newestVer = 0
    jsonList = []
    for monitdoc in evdt_glbl_monitdocs:
        doc15m = int( monitdoc['metadata']['timestamp'] / 900000 )
        if ( doc15m != bin15m ):
            continue
        version = int( monitdoc['metadata']['kafka_timestamp'] / 1000 )
        # deal with MonIT importer processing, allow for up to 90 sec
        if ( version > (newestVer + 90) ):
            newestVer = version
            jsonList = [ monitdoc['data'] ]
        elif ( abs( version - newestVer ) <= 90 ):
            jsonList.append( monitdoc['data'] )

    if ( len(jsonList) == 0 ):
        logging.info("   no MonIT doc for time bin")
        return False

    if (( jsonList != downtimes ) and
        (( len(downtimes) != 0 ) or ( len(jsonList) != 1 ) or
         ( jsonList[0]['name'] != "*" ) or ( jsonList[0]['status'] != "ok" ))):
        logging.info("   no MonIT doc with identical downtimes")
        return False

    logging.info("   MonIT doc with identical %d downtimes" %
                 len(downtimes))
    return True



def evdt_bins15m_monitdocs(after15m, last15m):
    """function to list the time bins in the global MonIT document list"""
    # #################################################################### #
    # get time bins in the global MonIT document list matching time window #
    # #################################################################### #

    ts = time.gmtime( (after15m + 96) * 900 )
    tomorrow15m = int( calendar.timegm( ts[:3] + (0, 0, 0) + ts[6:] ) / 900 )

    bin15mList = []
    for midnight15m in range( tomorrow15m, last15m + 1, 96):
        bin15mList.append( midnight15m )

    for monitdoc in evdt_glbl_monitdocs:
        bin15m = int( monitdoc['metadata']['timestamp'] / 900000 )
        if (( bin15m > after15m ) and ( bin15m <= last15m )):
            if bin15m not in bin15mList:
                bin15mList.append( bin15m )

    logging.info("MonIT document list contains %d time bins" %
                 len(bin15mList))
    return bin15mList
# ########################################################################### #



def evdt_bins15m_downtimes(after15m, last15m):
    """function to list the downtime boundaries for a time period"""
    # #################################################################### #
    # get downtime boundaries in global downtime list matching time window #
    # #################################################################### #

    ts = time.gmtime( (after15m + 96) * 900 )
    tomorrow15m = int( calendar.timegm( ts[:3] + (0, 0, 0) + ts[6:] ) / 900 )

    bin15mList = []
    for midnight15m in range( tomorrow15m, last15m + 1, 96):
        bin15mList.append( midnight15m )

    for downtime in evdt_glbl_downtimes:
        bin15m = int( downtime['duration'][0] / 900 )
        if (( bin15m > after15m ) and ( bin15m <= last15m )):
            if bin15m not in bin15mList:
                bin15mList.append( bin15m )
        bin15m = int( (downtime['duration'][1] - 1) / 900 ) + 1
        if (( bin15m > after15m ) and ( bin15m <= last15m )):
            if bin15m not in bin15mList:
                bin15mList.append( bin15m )

    return bin15mList
# ########################################################################### #



def evdt_select_downtimes(bin15m):
    """function to select downtimes for time-bin and following two weeks"""
    # ###################################################### #
    # return a list of downtimes relevant for given time-bin #
    # ###################################################### #
    startTIS = bin15m * 900
    ts = time.gmtime( (bin15m * 900) + (15 * 24 * 60 * 60) )
    limitTIS = calendar.timegm( ts[:3] + (0, 0, 0) + ts[6:] )

    selected = []
    for downtime in evdt_glbl_downtimes:
        if ( downtime['duration'][0] >= limitTIS ):
            continue
        if ( downtime['duration'][1] <= startTIS ):
            continue
        selected.append( downtime )

    return selected
# ########################################################################### #



def evdt_print_difference(firstDowntimes, secondDowntimes):
    """function to print difference in two downtimes lists in compact format"""
    # ################################################ #
    # print just the differences in two downtime lists #
    # ################################################ #

    for downtime in sorted(firstDowntimes, key=lambda k: [k['name'], k['type'],
                                          k['duration'][0], k['duration'][1]]):
        if downtime not in secondDowntimes:
            print("   - %s (%s) %s to %s" %
                  (downtime['name'], downtime['status'],
                   time.strftime("%Y-%m-%d %H:%M",
                                 time.gmtime(downtime['duration'][0])),
                   time.strftime("%Y-%m-%d %H:%M",
                                 time.gmtime(downtime['duration'][1]))))

    for downtime in sorted(secondDowntimes, key=lambda k: [k['name'], k['type'],
                                          k['duration'][0], k['duration'][1]]):
        if downtime not in firstDowntimes:
            print("   + %s (%s) %s to %s" %
                  (downtime['name'], downtime['status'],
                   time.strftime("%Y-%m-%d %H:%M",
                                 time.gmtime(downtime['duration'][0])),
                   time.strftime("%Y-%m-%d %H:%M",
                                 time.gmtime(downtime['duration'][1]))))
    return



def evdt_print_downtimes(downtimes):
    """function to print downtimes in compact format"""
    # ########################################## #
    # print downtimes with one line per downtime #
    # ########################################## #

    for downtime in sorted(downtimes, key=lambda k: [k['name'], k['type'],
                                          k['duration'][0], k['duration'][1]]):
        print("   %s   %s  %s to %s" %
              (downtime['name'], downtime['status'],
               time.strftime("%Y-%m-%d %H:%M",
                             time.gmtime(downtime['duration'][0])),
               time.strftime("%Y-%m-%d %H:%M",
                             time.gmtime(downtime['duration'][1]))))
    return
# ########################################################################### #



if __name__ == '__main__':
    #
    parserObj = argparse.ArgumentParser(description="Script to compile Downt" +
        "ime information for the current 15 minute bin. Downtime information" +
        " since the last MonIT downtime document is checked and uploaded if " +
        "found missing. Downtime information covering a specified 15 minute " +
        "bin is compiled and checked/uploaded in case of one argument and fo" +
        "r downtimes covering the time range in case of two arguments.")
    parserObj.add_argument("-U", dest="upload", default=True,
                                 action="store_false",
                                 help="do not upload to MonIT")
    parserObj.add_argument("-v", action="count", default=0,
                                 help="increase verbosity")
    parserObj.add_argument("timeSpec", nargs="?",
                                 metavar="Time Specification in UTC",
                                 help=("time specification, either an intege" +
                                       "r with the time in seconds since the" +
                                       " epoch or time in the format \"YYYY-" +
                                       "Mmm-dd HH:MM\""))
    parserObj.add_argument("lastSpec", nargs="?",
                                 metavar="End Time Specification in UTC",
                                 help=("time specification, either an intege" +
                                       "r with the time in seconds since the" +
                                       " epoch or time in the format \"YYYY-" +
                                       "Mmm-dd HH:MM\""))
    argStruct = parserObj.parse_args()


    # configure the message logger:
    # =============================
    if ( argStruct.v >= 2 ):
        logging.basicConfig(datefmt="%Y-%b-%d %H:%M:%S",
                            format="%(asctime)s [%(levelname).1s] %(message)s",
                            level=logging.DEBUG)
    elif ( argStruct.v == 1 ):
        logging.basicConfig(datefmt="%Y-%b-%d %H:%M:%S",
                            format="%(asctime)s [%(levelname).1s] %(message)s",
                            level=logging.INFO)
    else:
        logging.basicConfig(datefmt="%Y-%b-%d %H:%M:%S",
                            format="%(asctime)s [%(levelname).1s] %(message)s",
                            level=logging.WARNING)


    # time period for which we need to get/compile downtime information:
    # ==================================================================
    if argStruct.timeSpec is None:
        # current 15 minute time bin:
        frst15m = int( time.time() / 900 )
    elif argStruct.timeSpec.isdigit():
        # argument should be time in seconds for which to compile downtimes
        frst15m = int( argStruct.timeSpec / 900 )
    else:
        # argument should be the time in "YYYY-Mmm-dd HH:MM" format
        frst15m = int( calendar.timegm( time.strptime("%s UTC" %
                       argStruct.timeSpec, "%Y-%b-%d %H:%M %Z") ) / 900 )


    # last timebin for which we should compile downtime information:
    # ==============================================================
    if argStruct.lastSpec is not None:
        if argStruct.lastSpec.isdigit():
            # argument should be time in seconds of last 15 min time bin
            last15m = int( argStruct.lastSpec / 900 )
        else:
            # argument should be the time in "YYYY-Mmm-dd HH:MM" format
            last15m = int( calendar.timegm( time.strptime("%s UTC" %
                           argStruct.lastSpec, "%Y-%b-%d %H:%M %Z") ) / 900 )
        logging.info(("Compiling downtimes covering 15 min time bins %d (%s)" +
                      " to %d (%s)") %
                     (frst15m, time.strftime("%Y-%m-%d %H:%M",
                                             time.gmtime(frst15m * 900)),
                      last15m, time.strftime("%Y-%m-%d %H:%M",
                                             time.gmtime(last15m * 900))))
    else:
        last15m = frst15m
        logging.info("Compiling downtimes covering 15 min time bin %d (%s)" %
                     (frst15m, time.strftime("%Y-%m-%d %H:%M",
                                             time.gmtime(frst15m * 900))))


    # fetch service information of sites:
    # ===================================
    evdt_vofeed()
    t0sites = 0
    t1sites = 0
    t2sites = 0
    t3sites = 0
    for site in evdt_glbl_topology:
        if ( site[0:3] == "T3_" ):
            t3sites += 1
        elif ( site[0:3] == "T2_" ):
            t2sites += 1
        elif ( site[0:3] == "T1_" ):
            t1sites += 1
        elif ( site[0:3] == "T0_" ):
            t0sites += 1
    # sanity check:
    if (( t0sites < 1 ) or ( t1sites < 5 ) or ( t2sites < 35 ) or 
                                              ( t3sites < 24 )):
        logging.critical("No/too few sites in topology dictionary, %d" %
                         len(evdt_glbl_topology))
        sys.exit(1)
    logging.info("Topology: %d Tier-0, %d Tier-1, %d Tier-2, %d Tier-3 sites" %
                 (t0sites, t1sites, t2sites, t3sites))


    # fetch relevant MonIT downtime documents:
    # ========================================
    if argStruct.timeSpec is None:
        # check previous seven days for missing MonIT documents:
        ts = time.gmtime( (frst15m * 900) - (7 * 24 * 60 * 60) )
    else:
        # document covering time bin must be after or at midnight:
        ts = time.gmtime( frst15m * 900 )
    start15m = int( calendar.timegm( ts[:3] + (0, 0, 0) + ts[6:] ) / 900 )
    ts = time.gmtime( (last15m * 900) + (15 * 24 * 60 * 60) )
    limit15m = int( calendar.timegm( ts[:3] + (0, 0, 0) + ts[6:] ) / 900 )
    #
    evdt_monit_downtime(start15m, limit15m)
    if ( len(evdt_glbl_monitdocs) == 0 ):
        logging.warning("No relevant downtime documents found in MonIT")
    else:
        # locate document prior to time period we need to compile downtime for:
        prior15m = evdt_previous_monitdoc(frst15m)
        if ( prior15m != 0 ):
            # adjust search time window:
            start15m = prior15m


    # fetch downtime information:
    # ===========================
    evdt_osg_downtime(start15m, limit15m)
    noOSG = len(evdt_glbl_downtimes)
    evdt_egi_downtime(start15m, limit15m)
    if ( len(evdt_glbl_downtimes) == 0 ):
        logging.warning("No relevant EGI or OSG downtimes found")
        sys.exit(0)
    logging.info("Downtimes found: %d OSG, %d EGI" %
                 (noOSG, len(evdt_glbl_downtimes) - noOSG))


    # compile site downtime information:
    # ==================================
    evdt_site_downtime(start15m, limit15m)


    # prepare a list of time bins we need to check and potentially upload:
    # ====================================================================
    list1 = evdt_bins15m_downtimes(start15m, last15m)
    list2 = evdt_bins15m_monitdocs(start15m, last15m)
    bin15mList = list( set(list1 + list2) )
    if start15m not in bin15mList:
        bin15mList.append( start15m )
    bin15mList.sort()
    del(list1)


    # check if downtime information changes and if exists in MonIT:
    # =============================================================
    priorDowntimes = evdt_select_downtimes(start15m)
    for bin15m in bin15mList:
        selectDowntimes = evdt_select_downtimes(bin15m)
        if ((( selectDowntimes != priorDowntimes ) or
             ( (bin15m % 96) == 0 ) or
             ( bin15m in list2 )) and
            ( evdt_check_monitdoc(bin15m, selectDowntimes) == False )):
            # assemble JSON array and upload to MonIT:
            if ( argStruct.v >= 1 ):
                if ( selectDowntimes != priorDowntimes ):
                    logging.debug("Downtime information change")
                    evdt_print_difference(priorDowntimes, selectDowntimes)
                if ( (bin15m % 96) == 0 ):
                    logging.debug("Midnight entry")
                if ( bin15m in list2 ):
                    logging.debug("Superseded MonIT document")
            logging.info("Downtime update, time bin %d (%s)" %
                         (bin15m, time.strftime("%Y-%m-%d %H:%M",
                                                time.gmtime(bin15m * 900))))
            if ( argStruct.upload ):
                jsonString = evdt_json_arraystring(bin15m, selectDowntimes)
                evdt_upload_jsonstring(jsonString)
            else:
                evdt_print_downtimes(selectDowntimes)
        priorDowntimes = selectDowntimes
    del(list2)


    #fileObj = open("test_downtime.json", "w")
    #fileObj.write( jsonString )
    #fileObj.close()

    #import pdb; pdb.set_trace()
