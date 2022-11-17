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
import logging
import time, calendar
import ssl
import urllib.request, urllib.error
import xml.etree.ElementTree
import json
import gzip
import re
#
# setup the Java/HDFS/PATH environment for pydoop to work properly:
os.environ["HADOOP_CONF_DIR"] = "/opt/hadoop/conf/etc/analytix/hadoop.analytix"
os.environ["JAVA_HOME"]       = "/etc/alternatives/jre"
os.environ["HADOOP_PREFIX"]   = "/usr/hdp/hadoop"
import pydoop.hdfs
#
import vofeed
# ########################################################################### #



#EVDT_BACKUP_DIR = "./junk"
EVDT_BACKUP_DIR = "/data/cmssst/MonitoringScripts/downtime/failed"
# ########################################################################### #



class DowntimeMetric:
    """CMS Site Support Team downtime metric class"""

    def __init__(self):
        self.mtrc = {}
        return


    @staticmethod
    def status_names():
        return [ "downtime", "partial", "adhoc", "atrisk" ]


    @staticmethod
    def entry_order(entry):
        """function to determine the sort order of downtime entries"""
        SORT_ORDER = {'': 0,
                      'CE': 1, 'SE': 2, 'XRD': 3, 'perfSONAR': 4,
                      'site': 9}

        ctgry   = vofeed.vofeed.type2category( entry['type'] )
        try:
            return [ SORT_ORDER[ctgry],
                     entry['name'],
                     entry['duration'][0], entry['duration'][1] ]
        except KeyError:
            return [ 0,
                     entry['name'],
                     entry['duration'][0], entry['duration'][1] ]


    def fetch(self, timestamp):
        """function to fetch downtime information documents from MonIT/HDFS"""
        # ################################################################### #
        # In case timestamp is an integer retrieve the downtime document(s)   #
        # covering the time. In case timestamp is a tuple, retrieve the       #
        # downtime document(s) covering the time period spanned by the tuple. #
        # ################################################################### #
        HDFS_PREFIX = "/project/monitoring/archive/cmssst/raw/ssbmetric/"
        #
        if ( type(timestamp) == type( 0 ) ):
            timeFrst = int( timestamp / 86400 ) * 86400
            timeLast = ( int( timestamp / 900 ) * 900 ) + 899
        elif ( type(timestamp) == type( (0,0) ) ):
            timeFrst = int( timestamp[0] / 86400 ) * 86400
            timeLast = ( int( timestamp[1] / 900 ) * 900 ) + 899
        #
        oneDay = 86400
        now = int( time.time() )
        sixDaysAgo = calendar.timegm( time.gmtime(now - (6 * oneDay)) )


        # prepare HDFS subdirectory list:
        # ===============================
        logging.info("Retrieving downtime docs from MonIT HDFS")
        logging.log(15, "   from %s to %s" %
                       (time.strftime("%Y-%m-%d %H:%M", time.gmtime(timeFrst)),
                    time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime(timeLast))))
        #
        dirList = set()
        for dirDay in range(timeFrst, timeLast + 1, oneDay):
            dirList.add( time.strftime("down15min/%Y/%m/%d",
                                                         time.gmtime(dirDay)) )
        #
        startLclTmpArea = max( calendar.timegm( time.localtime( sixDaysAgo ) ),
                               calendar.timegm( time.localtime( timeFrst ) ) )
        midnight = ( int( now / 86400 ) * 86400 )
        limitLclTmpArea = calendar.timegm( time.localtime( midnight + 86399 ) )
        for dirDay in range( startLclTmpArea, limitLclTmpArea, oneDay):
            dirList.add( time.strftime("down15min/%Y/%m/%d.tmp",
                                                         time.gmtime(dirDay)) )
        #
        dirList = sorted( dirList )

        # connect to HDFS, loop over directories and read downtime docs:
        # ==============================================================
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
                    del(myList)
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
                            # read documents and add relevant records to list:
                            for myLine in fileObj:
                                myJson = json.loads(myLine.decode('utf-8'))
                                try:
                                    metric = myJson['metadata']['path']
                                    if ( metric != "down15min" ):
                                        continue
                                    tis = int( myJson['metadata']['timestamp']
                                                                       / 1000 )
                                    if (( tis < timeFrst ) or
                                        ( tis > timeLast )):
                                        continue
                                    # convert duration back to integer:
                                    strt = int( myJson['data']['duration'][0] )
                                    end  = int( myJson['data']['duration'][1] )
                                    myJson['data']['duration'] = ( strt, end )
                                    if 'detail' not in myJson['data']:
                                        myJson['data']['detail'] = None
                                    tbin = int( tis / 900 )
                                    name = myJson['data']['name']
                                    clss = myJson['data']['type']
                                    vrsn = myJson['metadata']['kafka_timestamp']
                                    #
                                    mKey = (metric, tbin)
                                    dKey  = (name, clss, strt, end)
                                    value = (vrsn, myJson['data'])
                                    #
                                    if mKey not in tmpDict:
                                        tmpDict[mKey] = {}
                                    if dKey in tmpDict[mKey]:
                                        if ( vrsn <= tmpDict[mKey][dKey][0] ):
                                            continue
                                    tmpDict[mKey][dKey] = value
                                except KeyError:
                                    logging.error(("Incomplete downtime reco" +
                                                   "rd, file %s: %s") %
                                                       (fileName, str(excptn)))
                                    continue
                        except json.decoder.JSONDecodeError as excptn:
                            logging.error("JSON decoding failure, file %s: %s"
                                                     % (fileName, str(excptn)))
                        except FileNotFoundError as excptn:
                            logging.error("HDFS file not found, %s: %s" %
                                                       (fileName, str(excptn)))
                        except IOError as excptn:
                            logging.error(("I/O error accessing HDFS file %s" +
                                           ": %s") % (fileName, str(excptn)))
                        finally:
                            if fileObj is not None:
                                fileObj.close()
                            if fileHndl is not None:
                                fileHndl.close()
        except Exception as excptn:
            logging.error("Failed to fetch downtime documents from MonIT: %s" %
                          str(excptn))


        # load downtime information into object:
        # ======================================
        cnt_docs = 0
        cnt_mtrc = len(tmpDict)
        for mtrcKey in tmpDict:
            # documents in a metric time-bin are uploaded together but are
            # imported with a couple seconds time jitter, allow 90 seconds
            vrsn_thrshld = 0
            # find highest version number:
            for evalKey in tmpDict[mtrcKey]:
                if ( tmpDict[mtrcKey][evalKey][0] > vrsn_thrshld ):
                    vrsn_thrshld = tmpDict[mtrcKey][evalKey][0]
            vrsn_thrshld -= 90000
            #
            self.add1metric(mtrcKey)
            for evalKey in tmpDict[mtrcKey]:
                # filter out docs not from the last upload (cancelled downtimes)
                if ( tmpDict[mtrcKey][evalKey][0] < vrsn_thrshld ):
                    continue
                downDict = tmpDict[mtrcKey][evalKey][1]
                # filter out downtime overrides via "ok" state:
                if ( downDict['status'] == "ok" ):
                    continue
                downDict['category'] = \
                                vofeed.vofeed.type2category( downDict['type'] )
                cnt_docs += 1
                self.add1entry(mtrcKey, downDict)
        del tmpDict

        if (( cnt_docs == 0 ) or ( cnt_mtrc == 0 )):
            logging.warning("No relevant downtime documents found in MonIT")
        else:
            logging.info("   found %d relevant docs for %d time-bins"
                                                        % (cnt_docs, cnt_mtrc))
        #
        return


    def metrics(self):
        """return list of downtime metrics in the object inventory"""
        # ################################################################ #
        # metric names are all "down15min" and returned sorted by time-bin #
        # ################################################################ #
        return sorted( self.mtrc.keys(), key=lambda m: m[1] )


    def downtimes(self, metric=None):
        """function to return a list of the downtimes for a metric tuple"""
        # ################################################################### #
        # metric is a tuple of metric-name and time-bin: ("down15min", 16954) #
        # downtimes are returned sorted by type, name, and duration-start and #
        # duration-end time                                                   #
        # ################################################################### #
        if (( metric is None ) and ( len(self.mtrc) == 1 )):
            metric = next(iter( self.mtrc.keys() ))
        #
        return sorted( self.mtrc[metric],
                                  key=lambda e: DowntimeMetric.entry_order(e) )


    def sites(self, metric=None):
        """return a list of sites with downtimes in the metric of the object"""
        # ################################################################### #
        # metric is a tuple of metric-name and time-bin: ("down15min", 16954) #
        # ################################################################### #
        if (( metric is None ) and ( len(self.mtrc) == 1 )):
            metric = next(iter( self.mtrc.keys() ))
        #
        return [ e['name'] for e in self.mtrc[metric] \
                                                   if ( e['type'] == "site" ) ]


    def add1metric(self, metric, data=None):
        """function to add an additional downtime metric to the obj inventory"""
        if ( metric[0] != "down15min" ):
            raise ValueError("metric %s is not a valid downtime metric name" %
                             str(metric[0]))
        #
        if metric not in self.mtrc:
            if data is not None:
                self.mtrc[metric] = data
            else:
                self.mtrc[metric] = []
        elif data is not None:
            self.mtrc[metric].extend( data )
        return


    @staticmethod
    def mk_entry(name, clss, status, start, stop, detail):
        """check values and create a downtime dictionary"""
        # ######################################################### #
        # check arguments and create a downtime dictionary, i.e.    #
        #    {'name':, 'type':, 'status':, 'duration':, 'detail': } #
        # ######################################################### #
        hostRegex = re.compile(r"^(([a-z0-9\-]+)\.)+[a-z0-9\-]+$")
        siteRegex = re.compile(r"T\d_[A-Z]{2,2}_\w+")
        #
        if (( name is None ) or ( name == "" ) or
            ( clss is None ) or ( clss == "" ) or
            ( status not in DowntimeMetric.status_names() ) or
            ( start is None ) or ( stop is None ) or
            ( start > stop )):
            logging.error("Bad entry values %s/%s/%s/%s/%s/%s" %
                          (str(name),str(clss),str(status),
                           str(start),str(stop),str(detail)))
            return {}

        ctgry = vofeed.vofeed.type2category( clss )

        return {'name': name, 'type': clss, 'status': status,
                'duration': (start, stop), 'detail': detail, 'category': ctgry}


    def add1entry(self, metric, entry):
        """function to add an additional downtime entry to a metric"""
        hostRegex = re.compile(r"^(([a-z0-9\-]+)\.)+[a-z0-9\-]+$")
        siteRegex = re.compile(r"T\d_[A-Z]{2,2}_\w+")
        #
        # check entry has mandatory keys:
        if (( 'name' not in entry ) or ( 'type' not in entry ) or
            ( 'status' not in entry ) or ( 'duration' not in entry )):
            raise ValueError("Mandatory keys missing in entry %s" %
                             str(entry))
        #
        entry = entry.copy()
        if ( entry['type'] == "site" ):
            if ( siteRegex.match( entry['name'] ) is None ):
                raise ValueError("Illegal site name %s" % entry['name'])
        else:
            if ( hostRegex.match( entry['name'] ) is None ):
                raise ValueError("Illegal host name %s" % entry['name'])
            entry['name'] = entry['name'].lower()
        #
        if 'detail' not in entry:
            entry['detail'] = None
        elif ( entry['detail'] == "" ):
            entry['detail'] = None
        #
        self.mtrc[metric].append( entry )
        #
        return


    def del1metric(self, metric):
        """function to remove a downtime metric from the object inventory"""
        # ################################################################### #
        del self.mtrc[metric]
        return


    def del1entry(self, metric, entry):
        """function to remove a downtime entry from a metric in the obj inv"""
        # ################################################################### #
        self.mtrc[metric].remove( entry )
        return


    @staticmethod
    def no_downtime_entry(timebin):
        strt = timebin * 900
        end  = strt + 899
        return { 'name': "*", 'type': "*", 'status': "ok",
                 'duration': ( strt, end ), 'detail': None }


    def compare2list(self, metric, downtimeList):
        """compare downtime entries in a metric with a provided list"""
        # ################################################################### #
        # check if the downtime entries in the metric ("down15min", time-bin) #
        # of the object match the provided list of downtimes                  #
        # ################################################################### #

        try:
            if ( len(self.mtrc[metric]) != len(downtimeList) ):
                logging.log(25, ("Different number of downtimes %d (%s,%d) a" +
                                 "nd %d list") % (len(self.mtrc[metric]),
                                      metric[0], metric[1], len(downtimeList)))
                return False
        except KeyError:
            logging.log(25, "No metric (%s,%d) in inventory" % (metric[0],
                                                                    metric[1]))
            return False
        #
        flag = True
        for entry in self.mtrc[metric]:
            if entry not in downtimeList:
                flag = False
                logging.log(25, "Downtime not in list: %s" % str(entry))
                if ( logging.getLogger().level > 15 ):
                    return False
        for entry in downtimeList:
            if entry not in self.mtrc[metric]:
                logging.log(15, "Downtime not in metric: %s" % str(entry))
        #
        return flag


    def compose_json(self):
        """function to extract downtimes in the obj inv into a JSON string"""
        # ############################################################ #
        # compose a JSON string from downtimes in the object inventory #
        # ############################################################ #

        jsonString = "["
        commaFlag = False
        #
        for metric in sorted( self.mtrc.keys() ):
            #
            timestamp = ( 900 * metric[1] ) + 450
            hdrString = (",\n {\n   \"producer\": \"cmssst\",\n" +
                                "   \"type\": \"ssbmetric\",\n" +
                                "   \"path\": \"%s\",\n" +
                                "   \"monit_hdfs_path\": \"%s\",\n" +
                                "   \"timestamp\": %d000,\n" +
                                "   \"type_prefix\": \"raw\",\n" +
                                "   \"data\": {\n") % (metric[0], metric[0],
                                                                     timestamp)
            #
            for entry in self.downtimes( metric ):
                if commaFlag:
                    jsonString += hdrString
                else:
                    jsonString += hdrString[1:]
                jsonString += (("      \"name\": \"%s\",\n" +
                                "      \"type\": \"%s\",\n" +
                                "      \"status\": \"%s\",\n" +
                                "      \"duration\": [%d, %d],\n") %
                               (entry['name'], entry['type'], entry['status'],
                                entry['duration'][0], entry['duration'][1]))
                if entry['detail'] is not None:
                    jsonString += ("      \"detail\": \"%s\"\n   }\n }" %
                                           entry['detail'].replace('\n','\\n'))
                else:
                    jsonString += ("      \"detail\": null\n   }\n }")
                commaFlag = True
        jsonString += "\n]\n"
        #
        return jsonString


    def dump(self, file=sys.stdout):
        """dump the contents of a downtime metric object"""
        # ################################################################### #

        for metric in sorted( self.mtrc.keys() ):
            #
            timestamp = 900 * metric[1]
            file.write("\nMetric \"%s\", %d (%s):\n" % (metric[0], metric[1],
                   time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime(timestamp))))
            file.write("---------------------------------------------------\n")
            #
            for entry in self.downtimes( metric ):
                #
                if entry['detail'] is not None:
                    detail = entry['detail'].replace('\n','\n           ')
                else:
                    detail = "null"
                fm_strng = time.strftime("%Y-%m-%d %H:%M:%S",
                                             time.gmtime(entry['duration'][0]))
                to_strng = time.strftime("%Y-%m-%d %H:%M:%S",
                                             time.gmtime(entry['duration'][1]))
                file.write("%s (%s): %s\n   from: %s to %s\n   detail: %s\n" %
                           (entry['name'], entry['type'], entry['status'],
                            fm_strng, to_strng, detail))
        file.write("=======================================================\n")
        file.write("\n")
        file.flush()
        return
# ########################################################################### #



if __name__ == '__main__':
    #
    import argparse
    import http.client
    import ssl

    #EVDT_CACHE_DIR = "./cache"
    EVDT_CACHE_DIR = "/data/cmssst/MonitoringScripts/downtime/cache"

    #EVDT_CERTIFICATE_CRT = "/afs/cern.ch/user/l/lammel/.globus/usercert.pem"
    #EVDT_CERTIFICATE_KEY = "/afs/cern.ch/user/l/lammel/.globus/userkey.pem"
    EVDT_CERTIFICATE_CRT = "/tmp/x509up_u79522"
    EVDT_CERTIFICATE_KEY = "/tmp/x509up_u79522"
    # ####################################################################### #



    class HTTPSClientAuthHandler(urllib.request.HTTPSHandler):
        """Urllib.request.HTTPSHandler class with certificate access"""

        def __init__(self):
            urllib.request.HTTPSHandler.__init__(self)

        def https_open(self, req):
            return self.do_open(self.getConnection, req)

        def getConnection(self, host, timeout=90):
            return http.client.HTTPSConnection(host,
                                               key_file=EVDT_CERTIFICATE_KEY,
                                               cert_file=EVDT_CERTIFICATE_CRT)
    # ####################################################################### #



    class HTTPSNoCertCheckHandler(urllib.request.HTTPSHandler):
        """Urllib.request.HTTPSHandler class with no certificate check"""

        def __init__(self):
            sslContext = ssl._create_unverified_context()
            urllib.request.HTTPSHandler.__init__(self, context=sslContext)
    # ####################################################################### #



    def evdt_osg_downtime(cmsHosts, start15m, limit15m):
        """fetch service downtime information relevant to CMS from OSG"""
        # ################################################################# #
        # fetch downtimes falling into the start15m to limit15m time-bin    #
        # interval, select downtimes relavant to CMS, and apply WLCG policy #
        # to classify downtimes into scheduled and ad-hoc ones;             #
        # return list of downtime dictionaries, i.e.                        #
        #   [ {'name':, 'type':, 'status':, 'duration':, 'detail': },       #
        #     {...}, ... ]                                                  #
        # ################################################################# #
        startTIS = start15m * 900
        limitTIS = limit15m * 900
        noDays = max(0, int( ( time.time() - startTIS ) / 86400 ) ) + 1
        OSG_DOWNTIME_URL = "http://my.opensciencegrid.org/rgdowntime/xml?downtime_attrs_showpast=%d&gridtype=on&gridtype_1=on&active=on&active_value=1" % noDays
        #
        downtimeList = []


        # get list of all CMS impacting downtimes from OSG:
        # =================================================
        logging.info("Querying OSG for downtime information")
        logging.log(15, "   between %s and %s" %
                       (time.strftime("%Y-%m-%d %H:%M", time.gmtime(startTIS)),
                    time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime(limitTIS))))
        urlHndl = None
        try:
            urlHndl = urllib.request.urlopen(OSG_DOWNTIME_URL)
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
                    logging.error(("Bad StartTime format \"%s\", OSG downtim" +
                                   "e %s") % (timeStr, id))
                    continue
                ts = time.strptime(timeStr, "%b %d, %Y %H:%M %p %Z")
                start = calendar.timegm(ts)
                if ( start >= limitTIS ):
                    continue
                #
                timeStr = downtime.findtext('EndTime', default="")
                if (( len(timeStr) != 25 ) or ( timeStr[6:10] != ", 20" )):
                    logging.error(("Bad EndTime format \"%s\", OSG downtime " +
                                   "%s") % (timeStr, id))
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
                            logging.warning(("No/bad CreatedTime format \"%s" +
                                             "\", OSG downtime %s") %
                                            (timeStr, id))
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
                    clss = service.findtext('Name', default="")
                    ctgry = vofeed.vofeed.type2category( clss )
                    if (host, ctgry) not in cmsHosts:
                        continue
                    detail = "OSG:" + id
                    if flip is None:
                        entry = DowntimeMetric.mk_entry(host,clss,status,
                                                        start,end,detail)
                        if ( len(entry) != 0 ):
                            downtimeList.append( entry )
                    else:
                        entry = DowntimeMetric.mk_entry(host,clss,status,
                                                        start,flip,detail)
                        if ( len(entry) != 0 ):
                            downtimeList.append( entry )
                        #
                        entry = DowntimeMetric.mk_entry(host,clss,"downtime",
                                                        flip,end,detail)
                        if ( len(entry) != 0 ):
                            downtimeList.append( entry )

        logging.info("   found %d relevant OSG downtimes" % len(downtimeList))
        #
        return downtimeList



    def evdt_egi_downtime(cmsHosts, start15m, limit15m):
        """function to fetch service downtime information from EGI"""
        # ################################################################ #
        # fill sswp_sites site element arrays with EGI downtime informaton #
        # ################################################################ #
        startTIS = start15m * 900
        limitTIS = limit15m * 900
        ts1 = time.gmtime( startTIS - 86400 )
        ts2 = time.gmtime( limitTIS + 86400 )
        EGI_DOWNTIME_URL = "https://goc.egi.eu/gocdbpi/public/?method=get_downtime&windowstart=%d-%02d-%02d&windowend=%d-%02d-%02d&scope=" % (ts1[0], ts1[1], ts1[2], ts2[0], ts2[1], ts2[2])
        #
        downtimeList = []


        # get list of all downtimes that could impact CMS from EGI:
        # =========================================================
        logging.info("Querying EGI for downtime information")
        logging.log(15, "   between %s and %s" %
                       (time.strftime("%Y-%m-%d %H:%M", time.gmtime(startTIS)),
                    time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime(limitTIS))))
        urlHndl = None
        try:
            myContext = ssl._create_unverified_context()
            urlHndl = urllib.request.urlopen(EGI_DOWNTIME_URL,
                                             context=myContext)
            myCharset = urlHndl.headers.get_content_charset()
            if myCharset is None:
                myCharset = "utf-8"
            myData = urlHndl.read().decode( myCharset )
            del(myCharset)
            del(myContext)
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
            clss = downtime.findtext('SERVICE_TYPE', default="")
            ctgry = vofeed.vofeed.type2category( clss )
            if (host, ctgry) not in cmsHosts:
                continue
            detail = "EGI:" + id
            if flip is None:
                entry = DowntimeMetric.mk_entry(host,clss,status,
                                                start,end,detail)
                if ( len(entry) != 0 ):
                    downtimeList.append( entry )
            else:
                entry = DowntimeMetric.mk_entry(host,clss,status,
                                                start,flip,detail)
                if ( len(entry) != 0 ):
                    downtimeList.append( entry )
                #
                entry = DowntimeMetric.mk_entry(host,clss,"downtime",
                                                flip,end,detail)
                if ( len(entry) != 0 ):
                    downtimeList.append( entry )

        logging.info("   found %d relevant EGI downtimes" % len(downtimeList))
        #
        return downtimeList
    # ####################################################################### #



    def evdt_site_status(sitename, downtimes, startTIS, limitTIS, noCE, noXRD):
        """evaluate site downtime status for one site and one interval"""
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
            if ((( status != "downtime") and
                 ( downtime['status'] == status )) or
                (( status == "partial" ) and
                 ( downtime['status'] == "downtime" ))):
                detail += ", " + downtime['name'] + "/" + downtime['category']
            if (( downtime['status'] == "atrisk" ) and ( status == "ok" )):
                status = "atrisk"
                detail =  downtime['name'] + "/" + downtime['category']
            elif (( downtime['status'] == "adhoc" ) and
                  (( status == "ok" ) or ( status == "atrisk" ))):
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
                elif ( downtime['category'] == "SE" ):
                    if ( status != "downtime" ):
                        status = "downtime"
                        detail =  downtime['name'] + "/" + downtime['category']
                    else:
                        detail += ", " + downtime['name'] + "/" + \
                                  downtime['category']
                elif ( downtime['category'] == "XRD" ):
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

        # assemble dictionary in case of a downtime:
        # ==========================================
        if ( status != "ok" ):
            entry = DowntimeMetric.mk_entry(sitename, "site", status,
                                            startTIS, limitTIS, detail)
        else:
            entry = {}
        #
        return entry



    def evdt_site_downtime(vofeedObj, downtimeList, start15m, limit15m):
        """evaluate site downtime status for all sites and intervals"""
        # ############################################################## #
        # evaluate site downtime status for sites from bin15m bin onward #
        # ############################################################## #
        startTIS = start15m * 900
        limitTIS = limit15m * 900
        #
        siteDowntimes = []

        logging.info("Evaluating site downtime status")
        logging.log(15, "   between %s and %s" %
                       (time.strftime("%Y-%m-%d %H:%M", time.gmtime(startTIS)),
                    time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime(limitTIS))))

        # use latest available site topology right now:
        timestamp = sorted( vofd.times() )[-1]
        logging.log(9, "Using VO-feed time-bin %d (%s)" % (timestamp,
                      time.strftime("%Y-%m-%d %H:%M", time.gmtime(timestamp))))

        # evaluate site downtime status:
        # ==============================
        for site in vofeedObj.sites(timestamp):
            srvcList = []
            for service in vofeedObj.services(timestamp, site):
                if ( service['production'] != True ):
                    continue
                srvcList.append( (service['hostname'], service['category']) )
            logging.log(9, "Site %s with %d production services" % (site,
                                                                len(srvcList)))

            # select downtimes of site and make list of status boundaries:
            # ============================================================
            relevant = []
            boundary = set()
            for downtime in downtimeList:
                if ( downtime['type'] == "site" ):
                    continue
                if (downtime['name'], downtime['category']) in srvcList:
                    relevant.append( downtime )
                    boundary.add( downtime['duration'][0] )
                    boundary.add( downtime['duration'][1] )
                    logging.log(9, "   %s / %s: %d to %d %s" %
                                   (downtime['name'], downtime['category'],
                                    downtime['duration'][0],
                                  downtime['duration'][1], downtime['status']))

            logging.debug(("Site %s has %d relevant downtimes with %d bounda" +
                           "ries") % (site, len(relevant), len(boundary)))
            if ( len(relevant) == 0 ):
                # no relevant downtime(s) for the site
                continue

            # count number of CE and XROOTD services at site:
            # ===============================================
            noCE = 0
            noXRD = 0
            for tuple in srvcList:
                if ( tuple[1] == "CE" ):
                    noCE += 1
                elif ( tuple[1] == "XRD" ):
                    noXRD += 1

            # evaluate site status for downtime periods:
            # ==========================================
            boundary = sorted( boundary )
            for period in range(1, len(boundary)):
                if ( boundary[period] < startTIS ):
                    continue
                if ( boundary[period-1] >= limitTIS ):
                    break
                entry = evdt_site_status(site, relevant, boundary[period-1],
                                                 boundary[period], noCE, noXRD)
                if ( len(entry) != 0 ):
                    siteDowntimes.append( entry )

        logging.info("   compiled %d relevant site downtimes" %
                                                            len(siteDowntimes))
        #
        return siteDowntimes
    # ####################################################################### #



    def evdt_bins15m_monitdocs(monitDocs, after15m, last15m):
        """list of time-bins for which we have/should have MonIT docs"""
        # ################################################################## #
        # return a list of time-bins within the interval for which we either #
        # already a metric already in MonIT or need to upload a metric       #
        # ################################################################## #
        bin15mList = set()

        for bin15m in [ e[1] for e in monitDocs.metrics() ]:
            if (( bin15m > after15m ) and ( bin15m <= last15m )):
                bin15mList.add( bin15m )

        nextMidnight = int( (after15m + 96) / 96 ) * 96
        for bin15m in range( nextMidnight, last15m + 1, 96):
            bin15mList.add( bin15m )

        return list( bin15mList )
    # ####################################################################### #



    def evdt_bins15m_downtimes(downtimeList, after15m, last15m):
        """list of time-bins with potential downtime change"""
        # ################################################################## #
        # return a list of time-bins within the interval for which we have a #
        # downtime boundary, i.e. a potential downtime status change         #
        # ################################################################## #
        bin15mList = set()

        for downtime in downtimeList:
            bin15m = int( downtime['duration'][0] / 900 )
            if (( bin15m > after15m ) and ( bin15m <= last15m )):
                bin15mList.add( bin15m )
            bin15m = int( (downtime['duration'][1] - 1) / 900 ) + 1
            if (( bin15m > after15m ) and ( bin15m <= last15m )):
                bin15mList.add( bin15m )

        return list( bin15mList )
    # ####################################################################### #



    def evdt_select_downtimes(downtimeList, bin15m):
        """function to select downtimes for time-bin and following two weeks"""
        # ######################################################## #
        # return a list of downtimes relevant for a given time-bin #
        # ######################################################## #
        startTIS = bin15m * 900
        limitTIS = int( (startTIS + (15 * 86400)) / 86400 ) * 86400

        selected = []
        for downtime in downtimeList:
            if ( downtime['duration'][0] >= limitTIS ):
                continue
            if ( downtime['duration'][1] <= startTIS ):
                continue
            selected.append( downtime )

        return selected
    # ####################################################################### #



    def evdt_print_difference(firstDowntimes, secondDowntimes):
        """print difference in two downtimes lists in compact format"""
        # ################################################ #
        # print just the differences in two downtime lists #
        # ################################################ #

        for downtime in sorted(firstDowntimes, key=lambda k: [k['name'],
                               k['type'], k['duration'][0], k['duration'][1]]):
            if downtime not in secondDowntimes:
                print("   - %s (%s) %s to %s" %
                      (downtime['name'], downtime['status'],
                       time.strftime("%Y-%m-%d %H:%M",
                                     time.gmtime(downtime['duration'][0])),
                       time.strftime("%Y-%m-%d %H:%M",
                                     time.gmtime(downtime['duration'][1]))))

        for downtime in sorted(secondDowntimes, key=lambda k: [k['name'],
                               k['type'], k['duration'][0], k['duration'][1]]):
            if downtime not in firstDowntimes:
                print("   + %s (%s) %s to %s" %
                      (downtime['name'], downtime['status'],
                       time.strftime("%Y-%m-%d %H:%M",
                                     time.gmtime(downtime['duration'][0])),
                       time.strftime("%Y-%m-%d %H:%M",
                                     time.gmtime(downtime['duration'][1]))))
        return
    # ####################################################################### #



    def monit_upload(mtrcObj):
        """function to upload CMS downtime evaluations to MonIT"""
        # ################################################################## #
        # upload downtime evaluations as JSON metric documents to MonIT/HDFS #
        # ################################################################## #
        #MONIT_URL = "http://monit-metrics.cern.ch:10012/"
        MONIT_URL = "http://fail.cern.ch:10012/"
        MONIT_HDR = {'Content-Type': "application/json; charset=UTF-8"}
        #
        logging.info("Composing JSON array and uploading to MonIT")


        # compose JSON array string:
        # ==========================
        jsonString = mtrcObj.compose_json()
        if ( jsonString == "[\n]\n" ):
            logging.warning("skipping upload of document-devoid JSON string")
            return False
        cnt_15min = jsonString.count("\"path\": \"down15min\"")
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
                requestObj = urllib.request.Request(MONIT_URL,
                             data=dataString.encode("utf-8"),
                             headers=MONIT_HDR, method="POST")
                responseObj = urllib.request.urlopen( requestObj, timeout=90 )
                #
                #openerDir = urllib.request.build_opener( HTTPSClientAuthHandler() )
                #responseObj = openerDir.open( requestObj )
                #
                if ( responseObj.status != http.HTTPStatus.OK ):
                    logging.error(("Failed to upload JSON [%d:%d] string to " +
                                   "MonIT, %d \"%s\"") %
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
            logging.log(25, "JSON string with %d docs uploaded to MonIT" %
                            cnt_15min)
        return successFlag
    # ####################################################################### #



    def write_evals(mtrcObj, filename=None):
        """function to write CMS downtime evaluation JSON to a file"""
        # ############################################################# #
        # write downtime evaluations as JSON metric documents to a file #
        # ############################################################# #

        if filename is None:
            filename = "%s/eval_down_%s.json" % (EVDT_BACKUP_DIR,
                                    time.strftime("%Y%m%d%H%M", time.gmtime()))
        logging.info("Writing JSON array to file %s" % filename)

        # compose JSON array string:
        # ==========================
        jsonString = mtrcObj.compose_json()

        if ( jsonString == "[\n]\n" ):
            logging.warning("skipping writing of document-devoid JSON string")
            return False
        cnt_docs = jsonString.count("\"producer\": \"cmssst\"")


        # write string to file:
        # =====================
        try:
            with open(filename, 'w') as myFile:
                myFile.write( jsonString )
            logging.log(25, "JSON array with %d docs written to file" %
                                                                      cnt_docs)
        except OSError as excptn:
            logging.error("Failed to write JSON array, %s" % str(excptn))

        return
    # ####################################################################### #



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


    # time period for which we need to get/compile downtime information:
    # ==================================================================
    if argStruct.timeSpec is None:
        # current 15 minute time-bin:
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
            # argument should be time in seconds of last 15 min time-bin
            last15m = int( argStruct.lastSpec / 900 )
        else:
            # argument should be the time in "YYYY-Mmm-dd HH:MM" format
            last15m = int( calendar.timegm( time.strptime("%s UTC" %
                           argStruct.lastSpec, "%Y-%b-%d %H:%M %Z") ) / 900 )
        logging.info(("Compiling downtimes covering 15 min time-bins %d (%s)" +
                      " to %d (%s)") %
                     (frst15m, time.strftime("%Y-%m-%d %H:%M",
                                             time.gmtime(frst15m * 900)),
                      last15m, time.strftime("%Y-%m-%d %H:%M",
                                             time.gmtime(last15m * 900))))
    else:
        last15m = frst15m
        logging.info("Compiling downtimes covering 15 min time-bin %d (%s)" %
                     (frst15m, time.strftime("%Y-%m-%d %H:%M",
                                             time.gmtime(frst15m * 900))))


    # fetch relevant MonIT downtime documents:
    # ========================================
    if argStruct.timeSpec is None:
        # check for missing MonIT documents (up to midnight 7 days ago):
        startTIS = int( (frst15m - (7 * 96)) / 96 ) * 86400
    else:
        # document covering time bin could be at midnight, fetch 1 extra day:
        startTIS = int( (frst15m - 96) / 96 ) * 86400
    #
    monitDocs = DowntimeMetric()
    monitDocs.fetch( (startTIS, last15m * 900) )


    # fetch site and service information:
    # ===================================
    vofd = vofeed.vofeed()
    if argStruct.timeSpec is None:
        # load latest/fetch previous VO-feed information:
        vofd.load()
    else:
        # fetch VO-feed information for time range:
        vofd.fetch( (startTIS, last15m * 900) )


    # fetch downtime information:
    # ===========================
    start15m = frst15m
    # locate document prior to time period we need to compile downtime for:
    invList = [ m[1] for m in monitDocs.metrics() ]
    for t15m in invList:
        if ( t15m > frst15m ):
            break
        start15m = t15m
    # downtime document includes upcoming downtimes of the next two weeks:
    limit15m = int( (last15m + (15 * 96)) / 96 ) * 96
    #
    # generate (host, category) tuple hash for lowest timestamp:
    timestamp = sorted( vofd.times() )[0]
    cmsHosts = []
    for site in vofd.topo[timestamp].keys():
        for service in vofd.topo[timestamp][ site ]:
            cmsHosts.append( (service['hostname'], service['category']) )
    #
    osgList = evdt_osg_downtime(cmsHosts, start15m, limit15m)
    egiList = evdt_egi_downtime(cmsHosts, start15m, limit15m)
    if ( len(osgList) + len(egiList) == 0 ):
        logging.warning("No relevant EGI or OSG downtimes found")
    else:
        logging.info("Downtimes found: %d OSG, %d EGI" %
                     (len(osgList), len(egiList)))
    #
    downtimeList = osgList + egiList
    del osgList
    del egiList


    # compile site downtime information:
    # ==================================
    siteList = evdt_site_downtime(vofd, downtimeList, start15m, limit15m)
    downtimeList += siteList
    del siteList


    # prepare a list of time bins we need to check and potentially upload:
    # ====================================================================
    list1 = evdt_bins15m_downtimes(downtimeList, start15m, last15m)
    list1.append( start15m )
    list2 = evdt_bins15m_monitdocs(monitDocs, start15m, last15m)
    if ( len(list2) == 0 ):
        # check previous metric entry in MonIT
        list2.append( start15m )
    bin15mList = sorted( set( list1 + list2 ) )
    logging.log(15, "Boundary list from downtimes %s" % str(list1))
    logging.log(15, "Boundary list from MonIT docs %s" % str(list2))
    logging.info("Checking downtimes between %d boundaries" % len(bin15mList))
    del(list1)


    # check if downtime information changes and if exists in MonIT:
    # =============================================================
    uploadDocs = DowntimeMetric()
    priorDowntimes = evdt_select_downtimes(downtimeList, start15m)
    for bin15m in bin15mList:
        logging.info("Interval starting %d (%s)" % (bin15m,
                     time.strftime("%Y-%m-%d %H:%M", time.gmtime(bin15m*900))))
        selectDowntimes = evdt_select_downtimes(downtimeList, bin15m)
        metric = ("down15min", bin15m)
        if ((( selectDowntimes != priorDowntimes ) or
             ( (bin15m % 96) == 0 ) or
             ( bin15m in list2 )) and
            ( monitDocs.compare2list(metric, selectDowntimes) == False )):
            #
            # add metric with downtime information for upload to MonIT:
            if ( len(selectDowntimes) == 0 ):
                uploadDocs.add1metric(metric,
                                  [ DowntimeMetric.no_downtime_entry(bin15m) ])
            else:
                uploadDocs.add1metric(metric, selectDowntimes)
            #
            if ( argStruct.v >= 4 ):
                if ( selectDowntimes != priorDowntimes ):
                    logging.debug("   downtime information change")
                    evdt_print_difference(priorDowntimes, selectDowntimes)
                if ( (bin15m % 96) == 0 ):
                    logging.debug("   midnight entry")
                if ( bin15m in list2 ):
                    logging.debug("   new or superseded MonIT document")
            logging.info("   update, time-bin %d (%s), %d downtimes" %
                         (bin15m, time.strftime("%Y-%m-%d %H:%M",
                             time.gmtime(bin15m * 900)), len(selectDowntimes)))
        priorDowntimes = selectDowntimes
    del(list2)


    # upload downtime metric documents to MonIT:
    # ==========================================
    if ( len( uploadDocs.metrics() ) > 0 ):
        if ( argStruct.upload ):
            successFlag = monit_upload( uploadDocs )
        else:
            successFlag = False
        #
        if ( not successFlag ):
            write_evals( uploadDocs )

    #import pdb; pdb.set_trace()
