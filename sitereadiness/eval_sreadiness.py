#!/data/cmssst/packages/bin/python3.7
# ########################################################################### #
# python script to query the VO-feed, downtime, SAM, HammerCloud, and FTS
#    metrics and derive a Site Readiness evaluation for sites. The script
#    checks/updates 15 min, 1 hour, 6 hour, and 1 day results, depending on
#    the execution time.
#
# 2019-Sep-26   Stephan Lammel
# ########################################################################### #
# 'metadata': {
#     'monit_hdfs_path': "sr15min",
#     'timestamp':       1464871600000
# },
# "data": {
#      "name":    "T1_DE_KIT",
#      "status":  "ok" | "warning" | "error" | "downtime" | "unknown"
#      "value":   0.750,
#      "detail":  "VO-feed: 6 CE(s), 1 SE(s), 1 XRD(s) in production,
#                  downtime: none,
#                  SAM: ok,
#                  HC: error (69 Success, 8 Failedm ExitCode 137),
#                  FTS: warning (Links (from/to): ... ok/ok)
# }



import os, sys
import logging
import time, calendar
import math
import socket
import urllib.request, urllib.error
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



#EVSR_BACKUP_DIR = "./junk"
EVSR_BACKUP_DIR = "/data/cmssst/MonitoringScripts/sitereadiness/failed"
# ########################################################################### #



class SReadinessMetric:
    'CMS Site Support Team Site Readiness metric class'

    def __init__(self):
        self.mtrc = {}
        return


    @staticmethod
    def interval(metric_name=None):
        SR_METRICS = {'sr15min':   900, 'sr1hour':  3600,
                                        'sr6hour': 21600, 'sr1day':  86400 }
        #
        if metric_name is None:
            return SR_METRICS
        #
        try:
            return SR_METRICS[ metric_name ]
        except KeyError:
            return 0


    @staticmethod
    def metric_order(metric):
        """function to determine the sort order of Site Readiness metrics"""
        SORT_ORDER = {'sr15min': 1, 'sr1hour': 2, 'sr6hour': 3, 'sr1day': 4}

        try:
            return [ SORT_ORDER[ metric[0] ], metric[1] ]
        except KeyError:
            return [ 0, metric[1] ]


    def fetch(self, metricList):
        """function to retrieve Site Readiness evaluation from MonIT"""
        # ################################################################ #
        # Retrieve all Site Readiness evaluations for the (metric-name,    #
        # time-bin) tuples in the provided metricList from MonIT/HDFS.     #
        # If a time-bin is "0", the latest entries for the metric-name are #
        # retrieved, with increasing range up to 5 days.                   #
        # ################################################################ #
        HDFS_PREFIX = "/project/monitoring/archive/cmssst/raw/ssbmetric/"

        now = int( time.time() )
        #
        if (( ("sr15min", 0) in metricList ) or
            ( ("sr1hour", 0) in metricList ) or
            ( ("sr6hour", 0) in metricList ) or
            ( ("sr1day", 0) in metricList )):
            metricSet = set( [ e for e in metricList if ( e[1] != 0 ) ] )
            #
            if ( ("sr15min", 0) in metricList ):
                # fetch data of last six hours:
                frst = int( (now - 21600) / 900 )
                for tbin in range( frst, int(now/900) ):
                    metricSet.add( ("sr15min", tbin) )
                latestTIS = int( (now - 86400) / 900 ) * 900
            if ( ("sr1hour", 0) in metricList ):
                # fetch data of last half day:
                frst = int( (now - 43200) / 3600 )
                for tbin in range( frst, int(now/3600) ):
                    metricSet.add( ("sr1hour", tbin) )
                latestTIS = int( (now - 172800) / 3600 ) * 3600
            if ( ("sr6hour", 0) in metricList ):
                # fetch data of last two days:
                frst = int( (now - 172800) / 21600 )
                for tbin in range( frst, int(now/21600) ):
                    metricSet.add( ("sr6hour", tbin) )
                latestTIS = int( (now - 432000) / 21600 ) * 21600
            if ( ("sr1day", 0) in metricList ):
                # fetch data of last five days:
                frst = int( (now - 432000) / 86400 )
                for tbin in range( frst, int(now/86400) ):
                    metricSet.add( ("sr1day", tbin) )
                latestTIS = int( (now - 604800) / 86400 ) * 86400
            #
            self.fetch(metricSet)
            #
            refetch = [False, False, False, False]
            inventoryList = self.metrics()
            if ( ("sr1day", 0) in metricList ):
                invList = [ e for e in inventoryList if ( e[0] == "sr1day" ) ]
                if ( len( invList ) == 0 ):
                    refetch[3] = True
                else:
                    latestTIS = min( latestTIS,
                                     max( [ e[1] for e in invList ] ) * 86400 )
            if ( ("sr6hour", 0) in metricList ):
                invList = [ e for e in inventoryList if ( e[0] == "sr6hour" ) ]
                if ( len( invList ) == 0 ):
                    refetch[2] = True
                else:
                    latestTIS = min( latestTIS,
                                     max( [ e[1] for e in invList ] ) * 21600 )
            if ( ("sr1hour", 0) in metricList ):
                invList = [ e for e in inventoryList if ( e[0] == "sr1hour" ) ]
                if ( len( invList ) == 0 ):
                    refetch[1] = True
                else:
                    latestTIS = min( latestTIS,
                                     max( [ e[1] for e in invList ] ) * 3600 )
            if ( ("sr15min", 0) in metricList ):
                invList = [ e for e in inventoryList if ( e[0] == "sr15min" ) ]
                if ( len( invList ) == 0 ):
                    refetch[0] = True
                else:
                    latestTIS = min( latestTIS,
                                     max( [ e[1] for e in invList ] ) * 900 )
            #
            if ( any(refetch) == True ):
                if ( refetch[0] == True ):
                    frst = int( latestTIS / 900 )
                    for tbin in range( frst, int(now/900) ):
                        metricSet.add( ("sr15min", tbin) )
                if ( refetch[1] == True ):
                    frst = int( latestTIS / 3600 ) - 1
                    for tbin in range( frst, int(now/3600) ):
                        metricSet.add( ("sr1hour", tbin) )
                if ( refetch[2] == True ):
                    frst = int( latestTIS / 21600 ) - 1
                    for tbin in range( frst, int(now/21600) ):
                        metricSet.add( ("sr6hour", tbin) )
                if ( refetch[3] == True ):
                    frst = int( latestTIS / 86400 ) - 1
                    for tbin in range( frst, int(now/86400) ):
                        metricSet.add( ("sr1day", tbin) )
                latestTIS = int( (now - 604800) / 86400 ) * 86400
                #
                self.fetch(metricSet)
                #
                inventoryList = self.metrics()
                if ( refetch[0] == True ):
                    invList = [ e[1] for e in inventoryList \
                                                     if ( e[0] == "sr15min" ) ]
                    if ( len( invList ) > 0 ):
                        refetch[0] = False
                    else:
                        frst = int( latestTIS / 900 )
                        if frst in invList:
                            refetch[0] = False
                        else:
                            for tbin in range( frst, int(now/900) ):
                                metricSet.add( ("sr15min", tbin) )
                if ( refetch[1] == True ):
                    invList = [ e[1] for e in inventoryList \
                                                     if ( e[0] == "sr1hour" ) ]
                    if ( len( invList ) > 0 ):
                        refetch[1] = False
                    else:
                        frst = int( latestTIS / 3600 )
                        if frst in invList:
                            refetch[1] = False
                        else:
                            for tbin in range( frst, int(now/3600) ):
                                metricSet.add( ("sr1hour", tbin) )
                if ( refetch[2] == True ):
                    invList = [ e[1] for e in inventoryList \
                                                     if ( e[0] == "sr6hour" ) ]
                    if ( len( invList ) > 0 ):
                        refetch[2] = False
                    else:
                        frst = int( latestTIS / 21600 )
                        if frst in invList:
                            refetch[2] = False
                        else: 
                            for tbin in range( frst, int(now/21600) ):
                                metricSet.add( ("sr6hour", tbin) )
                if ( refetch[3] == True ):
                    invList = [ e[1] for e in inventoryList \
                                                      if ( e[0] == "sr1day" ) ]
                    if ( len( invList ) > 0 ):
                        refetch[3] = False
                    else:
                        frst = int( latestTIS / 86400 )
                        if frst in invList:
                            refetch[3] = False
                        else:
                            for tbin in range( frst, int(now/86400) ):
                                metricSet.add( ("sr1day", tbin) )
                #
                if ( any(refetch) == True ):
                    # make final 7 day attempt:
                    self.fetch(metricSet)
            return



        # retrieve specific Site Readiness documents from MonIT/HDFS:
        # ===========================================================
        t15mFrst = min( [ e[1] for e in metricList \
                                     if ( e[0] == "sr15min" ) ], default=None )
        t1hFrst = min( [ e[1] for e in metricList \
                                     if ( e[0] == "sr1hour" ) ], default=None )
        t6hFrst = min( [ e[1] for e in metricList \
                                     if ( e[0] == "sr6hour" ) ], default=None )
        t1dFrst = min( [ e[1] for e in metricList \
                                      if ( e[0] == "sr1day" ) ], default=None )
        timeFrst = min( [ ( e[1] * SReadinessMetric.interval( e[0] ) ) \
                                                        for e in metricList ] )
        timeLast = max( [ ( (e[1] + 1) * SReadinessMetric.interval( e[0] ) ) \
                                                    for e in metricList ] ) - 1
        #
        logging.info("Retrieving Site Readiness evaluation docs from MonIT")
        logging.log(15, "   between %s and %s" %
                       (time.strftime("%Y-%m-%d %H:%M", time.gmtime(timeFrst)),
                    time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime(timeLast))))


        # prepare HDFS subdirectory list:
        # ===============================
        dirList = set()
        for mtrc in metricList:
            dirDay = mtrc[1] * SReadinessMetric.interval( mtrc[0] )
            dirList.add( mtrc[0] + time.strftime("/%Y/%m/%d",
                                              time.gmtime( dirDay )) )
        #
        oneDay = 86400
        sixDaysAgo = calendar.timegm( time.gmtime(now - (6 * oneDay)) )
        midnight = ( int( now / 86400 ) * 86400 )
        limitLclTmpArea = calendar.timegm( time.localtime( midnight + 86399 ) )
        if t15mFrst is not None:
            startLclTmpArea = max( calendar.timegm(time.localtime(sixDaysAgo)),
                                   calendar.timegm(time.localtime(t15mFrst)) )
            for dirDay in range(startLclTmpArea, limitLclTmpArea, oneDay):
                dirList.add( time.strftime("sr15min/%Y/%m/%d.tmp",
                                           time.gmtime( dirDay )) )
        if t1hFrst is not None:
            startLclTmpArea = max( calendar.timegm(time.localtime(sixDaysAgo)),
                                   calendar.timegm(time.localtime(t1hFrst)) )
            for dirDay in range(startLclTmpArea, limitLclTmpArea, oneDay):
                dirList.add( time.strftime("sr1hour/%Y/%m/%d.tmp",
                                            time.gmtime( dirDay )) )
        if t6hFrst is not None:
            startLclTmpArea = max( calendar.timegm(time.localtime(sixDaysAgo)),
                                   calendar.timegm(time.localtime(t6hFrst)) )
            for dirDay in range(startLclTmpArea, limitLclTmpArea, oneDay):
                dirList.add( time.strftime("sr6hour/%Y/%m/%d.tmp",
                                           time.gmtime( dirDay )) )
        if t1dFrst is not None:
            startLclTmpArea = max( calendar.timegm(time.localtime(sixDaysAgo)),
                                   calendar.timegm(time.localtime(t1dFrst)) )
            for dirDay in range(startLclTmpArea, limitLclTmpArea, oneDay):
                dirList.add( time.strftime("sr1day/%Y/%m/%d.tmp",
                                           time.gmtime( dirDay )) )
        del dirDay
        dirList = sorted(dirList)


        # connect to HDFS, loop over directories and read Site Readiness docs:
        # ====================================================================
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
                            # read Site Readiness evaluation documents in file:
                            for myLine in fileObj:
                                myJson = json.loads(myLine.decode('utf-8'))
                                try:
                                    if ( "monit_hdfs_path" not
                                                       in myJson['metadata'] ):
                                        myJson['metadata']['monit_hdfs_path'] \
                                                   = myJson['metadata']['path']
                                    metric = myJson['metadata']['monit_hdfs_path']
                                    if metric not in SReadinessMetric.interval():
                                        continue
                                    tbin = int( myJson['metadata']['timestamp']
                                 / (SReadinessMetric.interval(metric) * 1000) )
                                    mKey = (metric, tbin)
                                    if mKey not in metricList:
                                        continue
                                    if 'value' not in myJson['data']:
                                        myJson['data']['value'] = None
                                    if 'detail' not in myJson['data']:
                                        myJson['data']['detail'] = None
                                    name = myJson['data']['name']
                                    vrsn = myJson['metadata']['kafka_timestamp']
                                    #
                                    value = (vrsn, myJson['data'])
                                    #
                                    if mKey not in tmpDict:
                                        tmpDict[mKey] = {}
                                    if name in tmpDict[mKey]:
                                        if ( vrsn <= tmpDict[mKey][name][0] ):
                                            continue
                                    tmpDict[mKey][name] = value
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
            logging.error("Failed to fetch documents from MonIT HDFS: %s" %
                          str(excptn))


        # load Site Readiness evaluation information into object:
        # =======================================================
        cnt_docs = 0
        cnt_mtrc = len(tmpDict)
        for mtrcKey in tmpDict:
            self.add1metric(mtrcKey)
            for evalKey in tmpDict[mtrcKey]:
                cnt_docs += 1
                self.add1entry(mtrcKey, tmpDict[mtrcKey][evalKey][1])
        del tmpDict

        logging.info("   found %d relevant docs for %d metric-tuples" %
                                                          (cnt_docs, cnt_mtrc))
        #
        return


    def metrics(self):
        """function to return list of SR metrics in the object inventory"""
        # ############################################################# #
        # metrics are returned sorted by metric name (15m/1h/6h/1d) and #
        # time-bin                                                      #
        # ############################################################# #
        return sorted( self.mtrc.keys(),
                               key=lambda m: SReadinessMetric.metric_order(m) )


    def evaluations(self, metric=None):
        """function to return a list of the evaluations for a metric tuple"""
        # ################################################################## #
        # metric is a tuple of metric-name and time-bin: ("sr1hour", 406896) #
        # evaluations are returned sorted by site name                       #
        # ################################################################## #
        if (( metric is None ) and ( len(self.mtrc) == 1 )):
            metric = next(iter( self.mtrc.keys() ))
        #
        return sorted( self.mtrc[metric], key=lambda e: e['name'] )


    def sites(self, metric=None):
        """function to return a list of sites in the metric of the object"""
        # ################################################################# #
        # metric is a tuple of metric-name and time-bin: ("sr6hour", 67816) #
        # ################################################################# #
        if (( metric is None ) and ( len(self.mtrc) == 1 )):
            metric = next(iter( self.mtrc.keys() ))
        #
        return sorted( [ e['name'] for e in self.mtrc[metric] ] )


    def status(self, metric, name):
        """function to return the Site Readiness status of a site"""
        # ################################################################# #
        # metric is a tuple of metric-name and time-bin: ("sr6hour", 67816) #
        # and name is a CMS site name: Tn_CC_*                              #
        # return value is the status: "ok|warning|error|downtime|unknown"   #
        # ###################################################################
        if (( metric is None ) and ( len(self.mtrc) == 1 )):
            metric = next(iter( self.mtrc.keys() ))
        #
        for entry in self.mtrc[metric]:
            if ( entry['name'] == name ):
                return entry['status']
        #
        return "unknown"


    def add1metric(self, metric, data=None):
        """function to add an additional SR metric to the object inventory"""
        if metric[0] not in SReadinessMetric.interval():
            raise ValueError("metric %s is not a valid Site Readiness name" %
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


    def add1entry(self, metric, entry):
        """function to add an additional Site Readiness entry to a metric"""
        siteRegex = re.compile(r"T\d_[A-Z]{2,2}_\w+")
        #
        # check entry has mandatory keys:
        if (( 'name' not in entry ) or ( 'status' not in entry )):
            raise ValueError("Mandatory keys missing in entry %s" %
                             str(entry))
        #
        if ( siteRegex.match( entry['name'] ) is None ):
             raise ValueError("Illegal site name %s" % entry['name'])
        #
        entry = entry.copy()
        if 'value' not in entry:
            entry['value'] = None
        if 'detail' not in entry:
            entry['detail'] = None
        elif ( entry['detail'] == "" ):
            entry['detail'] = None
        #
        self.mtrc[metric].append( entry )
        #
        return


    def del1metric(self, metric):
        """function to remove an evaluation metric from the object inventory"""
        # ################################################################### #
        del self.mtrc[metric]


    def del1entry(self, metric, entry):
        """function to remove a site evaluation entry from a metric"""
        # ################################################################### #
        self.mtrc[metric].remove( entry )


    def compose_json(self):
        """extract a Site Readiness evaluations into a JSON string"""
        # ################################################################# #
        # compose a JSON string from the Site Readiness evaluations metrics #
        #in the object                                                      #
        # ################################################################# #

        jsonString = "["
        commaFlag = False
        #
        for metric in self.metrics():
            #
            interval = SReadinessMetric.interval( metric[0] )
            timestamp = ( interval * metric[1] ) + int( interval / 2 )
            hdrString = (",\n {\n   \"producer\": \"cmssst\",\n" +
                                "   \"type\": \"ssbmetric\",\n" +
                                "   \"monit_hdfs_path\": \"%s\",\n" +
                                "   \"timestamp\": %d000,\n" +
                                "   \"type_prefix\": \"raw\",\n" +
                                "   \"data\": {\n") % (metric[0], timestamp)
            #
            for entry in self.evaluations( metric ):
            #
                if commaFlag:
                    jsonString += hdrString
                else:
                    jsonString += hdrString[1:]
                jsonString += (("      \"name\": \"%s\",\n" +
                                "      \"status\": \"%s\",\n") %
                                              (entry['name'], entry['status']))
                if entry['value'] is not None:
                    jsonString += ("      \"value\": %.3f,\n" % entry['value'])
                else:
                    jsonString += ("      \"value\": null,\n")
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
        """dump the contents of a Site Readiness evaluation object"""
        # ################################################################### #

        for metric in self.metrics():
            #
            interval = SReadinessMetric.interval( metric[0] )
            timestamp = ( interval * metric[1] ) + int( interval / 2 )
            file.write("\nMetric \"%s\", %d (%s):\n" % (metric[0], metric[1],
                   time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime(timestamp))))
            file.write("---------------------------------------------------\n")
            #
            for entry in self.evaluations( metric ):
                #
                if entry['value'] is not None:
                    value = "%.3f" % entry['value']
                else:
                    value = "null"
                if entry['detail'] is not None:
                    detail = entry['detail'].replace('\n','\n           ')
                else:
                    detail = "null"
                file.write("%s: %s %s\n   detail: %s\n" %
                               (entry['name'], entry['status'], value, detail))
        file.write("=======================================================\n")
        file.write("\n")
        file.flush()
        return
# ########################################################################### #



if __name__ == '__main__':
    #
    import argparse
    import getpass
    import shutil
    import http
    #
    import vofeed
    import eval_downtime
    import eval_fts



    def sammtrc_interval(metric_name=None):
        SAM_METRICS = {'sam15min': 900, 'sam1hour':  3600,
                                        'sam6hour': 21600, 'sam1day':  86400 }
        #
        if metric_name is None:
            return SAM_METRICS
        #
        try:
            return SAM_METRICS[ metric_name ]
        except KeyError:
            return 0


    def fetch_sam(metricList):
        """function to fetch SAM evaluation documents from MonIT/HDFS"""
        # ############################################################### #
        # Retrieve all SAM CE/SRM/XROOTD/site evaluations for the metric  #
        # tuples (metric-name, time-bin) in the metricList from MonIT. If #
        # a time-bin is "0", the latest entries for the metric-name are   #
        # retrieved, with increasing range up to 5 days.                  #
        # return a dictionary of lists of SAM evaluation results, i.e.    #
        # { ('sam15min', 16954): [ {'name':, 'type':, 'status':, ...},    #
        #                          {...}, ... ],                          #
        #   ('sam1hour', 1695):  [ {'name':, 'type':, 'status':, ...},    #
        #                          {...}, ... ] }                         #
        # ############################################################### #
        HDFS_PREFIX = "/project/monitoring/archive/cmssst/raw/ssbmetric/"

        now = int( time.time() )
        #
        if (( ("sam15min", 0) in metricList ) or
            ( ("sam1hour", 0) in metricList ) or
            ( ("sam6hour", 0) in metricList ) or
            ( ("sam1day", 0) in metricList )):
            metricSet = set( [ e for e in metricList if ( e[1] != 0 ) ] )
            #
            if ( ("sam15min", 0) in metricList ):
                # fetch data of last six hours:
                frst = int( (now - 21600) / 900 )
                for tbin in range( frst, int(now/900) ):
                    metricSet.add( ("sam15min", tbin) )
                latestTIS = int( (now - 86400) / 900 ) * 900
            if ( ("sam1hour", 0) in metricList ):
                # fetch data of last half day:
                frst = int( (now - 43200) / 3600 )
                for tbin in range( frst, int(now/3600) ):
                    metricSet.add( ("sam1hour", tbin) )
                latestTIS = int( (now - 172800) / 3600 ) * 3600
            if ( ("sam6hour", 0) in metricList ):
                # fetch data of last two days:
                frst = int( (now - 172800) / 21600 )
                for tbin in range( frst, int(now/21600) ):
                    metricSet.add( ("sam6hour", tbin) )
                latestTIS = int( (now - 432000) / 21600 ) * 21600
            if ( ("sam1day", 0) in metricList ):
                # fetch data of last five days:
                frst = int( (now - 432000) / 86400 )
                for tbin in range( frst, int(now/86400) ):
                    metricSet.add( ("sam1day", tbin) )
                latestTIS = int( (now - 604800) / 86400 ) * 86400
            #
            self.fetch(metricSet)
            #
            refetch = [False, False, False, False]
            inventoryList = self.metrics()
            if ( ("sam1day", 0) in metricList ):
                invList = [ e for e in inventoryList if ( e[0] == "sam1day" ) ]
                if ( len( invList ) == 0 ):
                    refetch[3] = True
                else:
                    latestTIS = min( latestTIS,
                                     max( [ e[1] for e in invList ] ) * 86400 )
            if ( ("sam6hour", 0) in metricList ):
                invList = [ e for e in inventoryList if ( e[0] == "sam6hour" ) ]
                if ( len( invList ) == 0 ):
                    refetch[2] = True
                else:
                    latestTIS = min( latestTIS,
                                     max( [ e[1] for e in invList ] ) * 21600 )
            if ( ("sam1hour", 0) in metricList ):
                invList = [ e for e in inventoryList if ( e[0] == "sam1hour" ) ]
                if ( len( invList ) == 0 ):
                    refetch[1] = True
                else:
                    latestTIS = min( latestTIS,
                                     max( [ e[1] for e in invList ] ) * 3600 )
            if ( ("sam15min", 0) in metricList ):
                invList = [ e for e in inventoryList if ( e[0] == "sam15min" ) ]
                if ( len( invList ) == 0 ):
                    refetch[0] = True
                else:
                    latestTIS = min( latestTIS,
                                     max( [ e[1] for e in invList ] ) * 900 )
            #
            if ( any(refetch) == True ):
                if ( refetch[0] == True ):
                    frst = int( latestTIS / 900 )
                    for tbin in range( frst, int(now/900) ):
                        metricSet.add( ("sam15min", tbin) )
                if ( refetch[1] == True ):
                    frst = int( latestTIS / 3600 ) - 1
                    for tbin in range( frst, int(now/3600) ):
                        metricSet.add( ("sam1hour", tbin) )
                if ( refetch[2] == True ):
                    frst = int( latestTIS / 21600 ) - 1
                    for tbin in range( frst, int(now/21600) ):
                        metricSet.add( ("sam6hour", tbin) )
                if ( refetch[3] == True ):
                    frst = int( latestTIS / 86400 ) - 1
                    for tbin in range( frst, int(now/86400) ):
                        metricSet.add( ("sam1day", tbin) )
                latestTIS = int( (now - 604800) / 86400 ) * 86400
                #
                self.fetch(metricSet)
                #
                inventoryList = self.metrics()
                if ( refetch[0] == True ):
                    invList = [ e[1] for e in inventoryList \
                                                    if ( e[0] == "sam15min" ) ]
                    if ( len( invList ) > 0 ):
                        refetch[0] = False
                    else:
                        frst = int( latestTIS / 900 )
                        if frst in invList:
                            refetch[0] = False
                        else:
                            for tbin in range( frst, int(now/900) ):
                                metricSet.add( ("sam15min", tbin) )
                if ( refetch[1] == True ):
                    invList = [ e[1] for e in inventoryList \
                                                    if ( e[0] == "sam1hour" ) ]
                    if ( len( invList ) > 0 ):
                        refetch[1] = False
                    else:
                        frst = int( latestTIS / 3600 )
                        if frst in invList:
                            refetch[1] = False
                        else:
                            for tbin in range( frst, int(now/3600) ):
                                metricSet.add( ("sam1hour", tbin) )
                if ( refetch[2] == True ):
                    invList = [ e[1] for e in inventoryList \
                                                    if ( e[0] == "sam6hour" ) ]
                    if ( len( invList ) > 0 ):
                        refetch[2] = False
                    else:
                        frst = int( latestTIS / 21600 )
                        if frst in invList:
                            refetch[2] = False
                        else:
                            for tbin in range( frst, int(now/21600) ):
                                metricSet.add( ("sam6hour", tbin) )
                if ( refetch[3] == True ):
                    invList = [ e[1] for e in inventoryList \
                                                     if ( e[0] == "sam1day" ) ]
                    if ( len( invList ) > 0 ):
                        refetch[3] = False
                    else:
                        frst = int( latestTIS / 86400 )
                        if frst in invList:
                            refetch[3] = False
                        else:
                            for tbin in range( frst, int(now/86400) ):
                                metricSet.add( ("sam1day", tbin) )
                #
                if ( any(refetch) == True ):
                    # make final 7 day attempt:
                    self.fetch(metricSet)
            return



        # retrieve specific SAM evaluation documents from MonIT/HDFS:
        # ===========================================================
        t15mFrst = min( [ e[1] for e in metricList \
                                    if ( e[0] == "sam15min" ) ], default=None )
        t1hFrst = min( [ e[1] for e in metricList \
                                    if ( e[0] == "sam1hour" ) ], default=None )
        t6hFrst = min( [ e[1] for e in metricList \
                                    if ( e[0] == "sam6hour" ) ], default=None )
        t1dFrst = min( [ e[1] for e in metricList \
                                     if ( e[0] == "sam1day" ) ], default=None )
        timeFrst = min( [ ( e[1] * sammtrc_interval( e[0] ) ) \
                                                        for e in metricList ] )
        timeLast = max( [ ( (e[1] + 1) * sammtrc_interval( e[0] ) ) \
                                                    for e in metricList ] ) - 1
        #
        logging.info("Retrieving SAM evaluation docs from MonIT")
        logging.log(15, "   between %s and %s" %
                       (time.strftime("%Y-%m-%d %H:%M", time.gmtime(timeFrst)),
                    time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime(timeLast))))


        # prepare HDFS subdirectory list:
        # ===============================
        dirList = set()
        for mtrc in metricList:
            dirDay = mtrc[1] * sammtrc_interval( mtrc[0] )
            dirList.add( mtrc[0] + time.strftime("/%Y/%m/%d",
                                              time.gmtime( dirDay )) )
        #
        oneDay = 86400
        sixDaysAgo = calendar.timegm( time.gmtime(now - (6 * oneDay)) )
        midnight = ( int( now / 86400 ) * 86400 )
        limitLclTmpArea = calendar.timegm( time.localtime( midnight + 86399 ) )
        if t15mFrst is not None:
            startLclTmpArea = max( calendar.timegm(time.localtime(sixDaysAgo)),
                                   calendar.timegm(time.localtime(t15mFrst)) )
            for dirDay in range(startLclTmpArea, limitLclTmpArea, oneDay):
                dirList.add( time.strftime("sam15min/%Y/%m/%d.tmp",
                                           time.gmtime( dirDay )) )
        if t1hFrst is not None:
            startLclTmpArea = max( calendar.timegm(time.localtime(sixDaysAgo)),
                                   calendar.timegm(time.localtime(t1hFrst)) )
            for dirDay in range(startLclTmpArea, limitLclTmpArea, oneDay):
                dirList.add( time.strftime("sam1hour/%Y/%m/%d.tmp",
                                            time.gmtime( dirDay )) )
        if t6hFrst is not None:
            startLclTmpArea = max( calendar.timegm(time.localtime(sixDaysAgo)),
                                   calendar.timegm(time.localtime(t6hFrst)) )
            for dirDay in range(startLclTmpArea, limitLclTmpArea, oneDay):
                dirList.add( time.strftime("sam6hour/%Y/%m/%d.tmp",
                                           time.gmtime( dirDay )) )
        if t1dFrst is not None:
            startLclTmpArea = max( calendar.timegm(time.localtime(sixDaysAgo)),
                                   calendar.timegm(time.localtime(t1dFrst)) )
            for dirDay in range(startLclTmpArea, limitLclTmpArea, oneDay):
                dirList.add( time.strftime("sam1day/%Y/%m/%d.tmp",
                                           time.gmtime( dirDay )) )
        del dirDay
        dirList = sorted(dirList)


        # connect to HDFS, loop over directories and read SAM evaluation docs:
        # ====================================================================
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
                            # read SAM evaluation documents in file:
                            for myLine in fileObj:
                                myJson = json.loads(myLine.decode('utf-8'))
                                try:
                                    if ( "monit_hdfs_path" not
                                                       in myJson['metadata'] ):
                                        myJson['metadata']['monit_hdfs_path'] \
                                                   = myJson['metadata']['path']
                                    metric = myJson['metadata']['monit_hdfs_path']
                                    if metric not in sammtrc_interval():
                                        continue
                                    tbin = int( myJson['metadata']['timestamp']
                                          / (sammtrc_interval(metric) * 1000) )
                                    mKey = (metric, tbin)
                                    if mKey not in metricList:
                                        continue
                                    if 'availability' not in myJson['data']:
                                        myJson['data']['availability'] = None
                                    if 'reliability' not in myJson['data']:
                                        myJson['data']['reliability'] = None
                                    if 'detail' not in myJson['data']:
                                        myJson['data']['detail'] = None
                                    name = myJson['data']['name']
                                    type = myJson['data']['type']
                                    vrsn = myJson['metadata']['kafka_timestamp']
                                    #
                                    eKey  = (name, type)
                                    value = (vrsn, myJson['data'])
                                    #
                                    if mKey not in tmpDict:
                                        tmpDict[mKey] = {}
                                    if eKey in tmpDict[mKey]:
                                        if ( vrsn <= tmpDict[mKey][eKey][0] ):
                                            continue
                                    tmpDict[mKey][eKey] = value
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
            logging.error("Failed to fetch documents from MonIT HDFS: %s" %
                          str(excptn))


        # load SAM evaluation information into object:
        # ============================================
        MTRC = {}
        cnt_docs = 0
        cnt_mtrc = len(tmpDict)
        for mtrcKey in tmpDict:
            #self.add1metric(mtrcKey)
            if mtrcKey not in MTRC:
                MTRC[mtrcKey] = []
            #-end
            for evalKey in tmpDict[mtrcKey]:
                cnt_docs += 1
                #self.add1entry(mtrcKey, tmpDict[mtrcKey][evalKey][1])
                if ( tmpDict[mtrcKey][evalKey][1]['detail'] == "" ):
                    tmpDict[mtrcKey][evalKey][1]['detail'] = None
                elif ( tmpDict[mtrcKey][evalKey][1]['detail'][-1:] == "\n" ):
                    # fix up eval_sam bug...
                    tmpDict[mtrcKey][evalKey][1]['detail'] = \
                                    tmpDict[mtrcKey][evalKey][1]['detail'][:-1]
                MTRC[mtrcKey].append( tmpDict[mtrcKey][evalKey][1] )
                #-end
        del tmpDict

        logging.info("   found %d relevant docs for %d metric-tuples" %
                                                          (cnt_docs, cnt_mtrc))
        #
        return MTRC


    def get1entry_sam(metricDict, metric, name, clss):
        if (( metric is None ) and ( len(metricDict) == 1 )):
            metric = next(iter( metricDict.keys() ))
        #
        for entry in metricDict[metric]:
            if (( entry['name'] == name ) and ( entry['type'] == clss )):
                return entry
        #
        raise KeyError("No such entry %s / %s in (%s,%d)" % (name, clss,
                                                         metric[0], metric[1]))
    # ####################################################################### #



    def hcmtrc_interval(metric_name=None):
        HC_METRICS = {'hc15min': 900, 'hc1hour':  3600,
                                      'hc6hour': 21600, 'hc1day':  86400 }
        #
        if metric_name is None:
            return HC_METRICS
        #
        try:
            return HC_METRICS[ metric_name ]
        except KeyError:
            return 0


    def fetch_hc(metricList):
        """function to fetch HammerCloud evaluation documents from MonIT"""
        # ############################################################### #
        # Retrieve all HammerCloud site evaluations for the metric tuples #
        # (metric-name, time-bin) in the metricList from MonIT/HDFS. If a #
        # time-bin is "0", the latest entries for the metric-name are     #
        # retrieved, with increasing range up to 5 days.                  #
        # return a dictionary of lists of HC evaluation results, i.e.     #
        # { ('hc15min', 16954): [ {'name':, 'status':, 'value':, ...},    #
        #                         {...}, ... ],                           #
        #   ('hc1hour', 1695):  [ {'name':, 'status':, 'value':, ...},    #
        #                         {...}, ... ] }                          #
        # ############################################################### #
        HDFS_PREFIX = "/project/monitoring/archive/cmssst/raw/ssbmetric/"

        now = int( time.time() )
        #
        if (( ("hc15min", 0) in metricList ) or
            ( ("hc1hour", 0) in metricList ) or
            ( ("hc6hour", 0) in metricList ) or
            ( ("hc1day", 0) in metricList )):
            metricSet = set( [ e for e in metricList if ( e[1] != 0 ) ] )
            #
            if ( ("hc15min", 0) in metricList ):
                # fetch data of last half day:
                frst = int( (now - 43200) / 900 )
                for tbin in range( frst, int(now/900) ):
                    metricSet.add( ("hc15min", tbin) )
                latestTIS = int( (now - 86400) / 900 ) * 900
            if ( ("hc1hour", 0) in metricList ):
                # fetch data of last day:
                frst = int( (now - 86400) / 3600 )
                for tbin in range( frst, int(now/3600) ):
                    metricSet.add( ("hc1hour", tbin) )
                latestTIS = int( (now - 172800) / 3600 ) * 3600
            if ( ("hc6hour", 0) in metricList ):
                # fetch data of last two days:
                frst = int( (now - 172800) / 21600 )
                for tbin in range( frst, int(now/21600) ):
                    metricSet.add( ("hc6hour", tbin) )
                latestTIS = int( (now - 432000) / 21600 ) * 21600
            if ( ("hc1day", 0) in metricList ):
                # fetch data of last five days:
                frst = int( (now - 432000) / 86400 )
                for tbin in range( frst, int(now/86400) ):
                    metricSet.add( ("hc1day", tbin) )
                latestTIS = int( (now - 604800) / 86400 ) * 86400
            #
            self.fetch(metricSet)
            #
            refetch = [False, False, False, False]
            inventoryList = self.metrics()
            if ( ("hc1day", 0) in metricList ):
                invList = [ e for e in inventoryList if ( e[0] == "hc1day" ) ]
                if ( len( invList ) == 0 ):
                    refetch[3] = True
                else:
                    latestTIS = min( latestTIS,
                                     max( [ e[1] for e in invList ] ) * 86400 )
            if ( ("hc6hour", 0) in metricList ):
                invList = [ e for e in inventoryList if ( e[0] == "hc6hour" ) ]
                if ( len( invList ) == 0 ):
                    refetch[2] = True
                else:
                    latestTIS = min( latestTIS,
                                     max( [ e[1] for e in invList ] ) * 21600 )
            if ( ("hc1hour", 0) in metricList ):
                invList = [ e for e in inventoryList if ( e[0] == "hc1hour" ) ]
                if ( len( invList ) == 0 ):
                    refetch[1] = True
                else:
                    latestTIS = min( latestTIS,
                                     max( [ e[1] for e in invList ] ) * 3600 )
            if ( ("hc15min", 0) in metricList ):
                invList = [ e for e in inventoryList if ( e[0] == "hc15min" ) ]
                if ( len( invList ) == 0 ):
                    refetch[0] = True
                else:
                    latestTIS = min( latestTIS,
                                     max( [ e[1] for e in invList ] ) * 900 )
            #
            if ( any(refetch) == True ):
                if ( refetch[0] == True ):
                    frst = int( latestTIS / 900 )
                    for tbin in range( frst, int(now/900) ):
                        metricSet.add( ("hc15min", tbin) )
                if ( refetch[1] == True ):
                    frst = int( latestTIS / 3600 ) - 1
                    for tbin in range( frst, int(now/3600) ):
                        metricSet.add( ("hc1hour", tbin) )
                if ( refetch[2] == True ):
                    frst = int( latestTIS / 21600 ) - 1
                    for tbin in range( frst, int(now/21600) ):
                        metricSet.add( ("hc6hour", tbin) )
                if ( refetch[3] == True ):
                    frst = int( latestTIS / 86400 ) - 1
                    for tbin in range( frst, int(now/86400) ):
                        metricSet.add( ("hc1day", tbin) )
                latestTIS = int( (now - 604800) / 86400 ) * 86400
                #
                self.fetch(metricSet)
                #
                inventoryList = self.metrics()
                if ( refetch[0] == True ):
                    invList = [ e[1] for e in inventoryList \
                                                     if ( e[0] == "hc15min" ) ]
                    if ( len( invList ) > 0 ):
                        refetch[0] = False
                    else:
                        frst = int( latestTIS / 900 )
                        if frst in invList:
                            refetch[0] = False
                        else:
                            for tbin in range( frst, int(now/900) ):
                                metricSet.add( ("hc15min", tbin) )
                if ( refetch[1] == True ):
                    invList = [ e[1] for e in inventoryList \
                                                     if ( e[0] == "hc1hour" ) ]
                    if ( len( invList ) > 0 ):
                        refetch[1] = False
                    else:
                        frst = int( latestTIS / 3600 )
                        if frst in invList:
                            refetch[1] = False
                        else:
                            for tbin in range( frst, int(now/3600) ):
                                metricSet.add( ("hc1hour", tbin) )
                if ( refetch[2] == True ):
                    invList = [ e[1] for e in inventoryList \
                                                     if ( e[0] == "hc6hour" ) ]
                    if ( len( invList ) > 0 ):
                        refetch[2] = False
                    else:
                        frst = int( latestTIS / 21600 )
                        if frst in invList:
                            refetch[2] = False
                        else:
                            for tbin in range( frst, int(now/21600) ):
                                metricSet.add( ("hc6hour", tbin) )
                if ( refetch[3] == True ):
                    invList = [ e[1] for e in inventoryList \
                                                      if ( e[0] == "hc1day" ) ]
                    if ( len( invList ) > 0 ):
                        refetch[3] = False
                    else:
                        frst = int( latestTIS / 86400 )
                        if frst in invList:
                            refetch[3] = False
                        else:
                            for tbin in range( frst, int(now/86400) ):
                                metricSet.add( ("hc1day", tbin) )
                #
                if ( any(refetch) == True ):
                    # make final 7 day attempt:
                    self.fetch(metricSet)
            return



        # retrieve specific HammerCloud evaluation documents from MonIT/HDFS:
        # ===================================================================
        t15mFrst = min( [ e[1] for e in metricList \
                                     if ( e[0] == "hc15min" ) ], default=None )
        t1hFrst = min( [ e[1] for e in metricList \
                                     if ( e[0] == "hc1hour" ) ], default=None )
        t6hFrst = min( [ e[1] for e in metricList \
                                     if ( e[0] == "hc6hour" ) ], default=None )
        t1dFrst = min( [ e[1] for e in metricList \
                                      if ( e[0] == "hc1day" ) ], default=None )
        timeFrst = min( [ ( e[1] * hcmtrc_interval( e[0] ) ) \
                                                        for e in metricList ] )
        timeLast = max( [ ( (e[1] + 1) * hcmtrc_interval( e[0] ) ) \
                                                    for e in metricList ] ) - 1
        #
        logging.info("Retrieving HammerCloud evaluation docs from MonIT")
        logging.log(15, "   between %s and %s" %
                       (time.strftime("%Y-%m-%d %H:%M", time.gmtime(timeFrst)),
                    time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime(timeLast))))


        # prepare HDFS subdirectory list:
        # ===============================
        dirList = set()
        for mtrc in metricList:
            dirDay = mtrc[1] * hcmtrc_interval( mtrc[0] )
            dirList.add( mtrc[0] + time.strftime("/%Y/%m/%d",
                                              time.gmtime( dirDay )) )
        #
        oneDay = 86400
        sixDaysAgo = calendar.timegm( time.gmtime(now - (6 * oneDay)) )
        midnight = ( int( now / 86400 ) * 86400 )
        limitLclTmpArea = calendar.timegm( time.localtime( midnight + 86399 ) )
        if t15mFrst is not None:
            startLclTmpArea = max( calendar.timegm(time.localtime(sixDaysAgo)),
                                   calendar.timegm(time.localtime(t15mFrst)) )
            for dirDay in range(startLclTmpArea, limitLclTmpArea, oneDay):
                dirList.add( time.strftime("hc15min/%Y/%m/%d.tmp",
                                           time.gmtime( dirDay )) )
        if t1hFrst is not None:
            startLclTmpArea = max( calendar.timegm(time.localtime(sixDaysAgo)),
                                   calendar.timegm(time.localtime(t1hFrst)) )
            for dirDay in range(startLclTmpArea, limitLclTmpArea, oneDay):
                dirList.add( time.strftime("hc1hour/%Y/%m/%d.tmp",
                                            time.gmtime( dirDay )) )
        if t6hFrst is not None:
            startLclTmpArea = max( calendar.timegm(time.localtime(sixDaysAgo)),
                                   calendar.timegm(time.localtime(t6hFrst)) )
            for dirDay in range(startLclTmpArea, limitLclTmpArea, oneDay):
                dirList.add( time.strftime("hc6hour/%Y/%m/%d.tmp",
                                           time.gmtime( dirDay )) )
        if t1dFrst is not None:
            startLclTmpArea = max( calendar.timegm(time.localtime(sixDaysAgo)),
                                   calendar.timegm(time.localtime(t1dFrst)) )
            for dirDay in range(startLclTmpArea, limitLclTmpArea, oneDay):
                dirList.add( time.strftime("hc1day/%Y/%m/%d.tmp",
                                           time.gmtime( dirDay )) )
        del dirDay
        dirList = sorted(dirList)


        # connect to HDFS, loop over directories and read HC evaluation docs:
        # ===================================================================
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
                            # read HammerCloud evaluation documents in file:
                            for myLine in fileObj:
                                myJson = json.loads(myLine.decode('utf-8'))
                                try:
                                    if ( "monit_hdfs_path" not
                                                       in myJson['metadata'] ):
                                        myJson['metadata']['monit_hdfs_path'] \
                                                   = myJson['metadata']['path']
                                    metric = myJson['metadata']['monit_hdfs_path']
                                    if metric not in hcmtrc_interval():
                                        continue
                                    tbin = int( myJson['metadata']['timestamp']
                                          / (hcmtrc_interval(metric) * 1000) )
                                    mKey = (metric, tbin)
                                    if mKey not in metricList:
                                        continue
                                    if 'value' not in myJson['data']:
                                        myJson['data']['value'] = None
                                    if 'detail' not in myJson['data']:
                                        myJson['data']['detail'] = None
                                    if 'name' in myJson['data']:
                                        site = myJson['data']['name']
                                    else:
                                        site = myJson['data']['site']
                                        myJson['data']['name'] = site
                                    vrsn = myJson['metadata']['kafka_timestamp']
                                    #
                                    value = (vrsn, myJson['data'])
                                    #
                                    if mKey not in tmpDict:
                                        tmpDict[mKey] = {}
                                    if site in tmpDict[mKey]:
                                        if ( vrsn <= tmpDict[mKey][site][0] ):
                                            continue
                                    tmpDict[mKey][site] = value
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
            logging.error("Failed to fetch documents from MonIT HDFS: %s" %
                          str(excptn))


        # load HC evaluation information into object:
        # ===========================================
        MTRC = {}
        cnt_docs = 0
        cnt_mtrc = len(tmpDict)
        for mtrcKey in tmpDict:
            #self.add1metric(mtrcKey)
            if mtrcKey not in MTRC:
                MTRC[mtrcKey] = []
            #-end
            for evalKey in tmpDict[mtrcKey]:
                cnt_docs += 1
                #self.add1entry(mtrcKey, tmpDict[mtrcKey][evalKey][1])
                if ( tmpDict[mtrcKey][evalKey][1]['detail'] == "" ):
                    tmpDict[mtrcKey][evalKey][1]['detail'] = None
                MTRC[mtrcKey].append( tmpDict[mtrcKey][evalKey][1] )
                #-end
        del tmpDict

        logging.info("   found %d relevant docs for %d metric-tuples" %
                                                          (cnt_docs, cnt_mtrc))
        #
        return MTRC


    def get1entry_hc(metricDict, metric, site):
        if (( metric is None ) and ( len(metricDict) == 1 )):
            metric = next(iter( metricDict.keys() ))
        #
        for entry in metricDict[metric]:
            if ( entry['name'] == site ):
                return entry
        #
        raise KeyError("No such entry %s in (%s,%d)" % (site,
                                                         metric[0], metric[1]))
    # ####################################################################### #



    def site_in_downtime(downObj, site_name, metric):
        """evaluate if site was half or more of the time-bin in downtime"""
        # ################################################################# #
        # downObj is a filled downtime metric object, site_name is the name #
        # of the CMS site to check, and metric a tuple of metric-name and   #
        # time-bin                                                          #
        # function returns a tuple (True/False, string with downtime status #
        # found if any, otherwise "none")                                   #
        # evaluation is based only on the duration of scheduled downtimes   #
        # ################################################################# #
        if ( metric[0][-5:] == "15min" ):
            interval = 900
        elif ( metric[0][-5:] == "1hour" ):
            interval = 3600
        elif ( metric[0][-5:] == "6hour" ):
            interval = 21600
        elif ( metric[0][-4:] == "1day" ):
            interval = 86400
        else:
            raise ValueError("metric %s is not a valid cmssst metric name" %
                             str(metric[0]))
        first15b = int( metric[1] * interval / 900 )
        limit15b = int( ( (metric[1] + 1) * interval ) / 900 )
        #
        down15Inv = sorted( [ m[1] for m in downObj.metrics() ], reverse=True )

        # loop over metrics in the downtime object in reverse time:
        cnt_seconds = 0
        prev15bin = limit15b
        for t15bin in down15Inv:
            if ( t15bin < limit15b ):
                # check if site in scheduled downtime:
                for entry in downObj.downtimes( ("down15min", t15bin) ):
                    if (( entry['name'] == site_name ) and
                        ( entry['type'] == "site" ) and 
                        ( entry['status'] == "downtime" )):
                        duration_s = max(first15b * 900, t15bin * 900,
                                                          entry['duration'][0])
                        duration_e = min(limit15b * 900, prev15bin * 900,
                                                          entry['duration'][1])
                        # downtime metric has no overlapping site downtimes
                        cnt_seconds += max(0, duration_e - duration_s)
                if ( t15bin <= first15b ):
                    break
            prev15bin = t15bin
        #
        if ( (cnt_seconds / interval) >= 0.5 ):
            status_flag = True
            strng = "yes"
        else:
            status_flag = False
            strng = "no"
        #
        if ( cnt_seconds == 0 ):
           status_strng = "%s scheduled downtime" % strng
        elif ( cnt_seconds >= 5400 ):
           status_strng = "%s (%dh %dmin scheduled)" % (strng,
                             int(cnt_seconds/3600), int((cnt_seconds%3600)/60))
        elif ( cnt_seconds >= 90 ):
           status_strng = "%s (%dmin %dsec scheduled)" % (strng,
                                           int(cnt_seconds/60), cnt_seconds%60)
        else:
           status_strng = "%s (%d sec scheduled)" % (strng, cnt_seconds)
        #
        logging.log(9, "      %s: %s" % (site_name, status_strng))

        return status_flag, status_strng
    # ####################################################################### #



    def count_good_15min(srObj, evalObj, start15m, limit15m):
        """number of good 15m Site Readiness evaluations of site in interval"""
        # ################################################################### #
        cnt_good = {}
        #
        mtrcList = set( [ m for m in srObj.metrics() if (m[0]=="sr15min") ] + 
                        [ m for m in evalObj.metrics() if (m[0]=="sr15min") ] )
        #
        cnt_15min = 0
        for mtrc in mtrcList:
            if (( mtrc[1] < start15m ) or ( mtrc[1] >= limit15m )):
                continue
            try:
                evalList = evalObj.evaluations(mtrc)
            except KeyError:
                evalList = srObj.evaluations(mtrc)
            logging.log(9, "   (%s,%d) has %d entries" % (mtrc[0], mtrc[1],
                                                                len(evalList)))
            for entry in evalList:
                if entry['name'] not in cnt_good:
                    cnt_good[ entry['name'] ] = 0
                if (( entry['status'] == "ok" ) or
                    ( entry['status'] == "warning" )):
                    cnt_good[ entry['name'] ] += 1
            cnt_15min += 1
        #
        for site in cnt_good:
            cnt_good[site] = round( cnt_good[site] / cnt_15min, 3)
        #
        return cnt_good
    # ####################################################################### #



    def eval_status(evalObj, vofdObj, samObj, hcObj, ftsObj, downObj, srObj):
        """function to evaluate Site Readiness status of sites"""
        # ################################################################### #
        # for each metric-tuple in evalObj evaluate Site Readiness for all    #
        # sites in the VO-feed a the start of the time-bin and store the      #
        # evaluations in evalObj                                              #
        # Site Readiness status is the most faulty status of SAM, HC, and FTS #
        # Site Readiness value is the number of 15 min ok or warning states   #
        # divided by the number of 15 min bins in the time-bin interval       #
        # metric-tuples with only unknown evaluations are deleted             #
        # ################################################################### #
        hcRegex = re.compile(r"\[.*\]|\s\.{3}")

        logging.info("Evaluating Site Readiness status for %d metric-tuples"
                                                    % len( evalObj.metrics() ))


        # prepare VO-feed time inventory list:
        # ====================================
        vofdTimeList = sorted( vofdObj.times(), reverse=True )


        # prepare a list of sites with downtimes for quick no-downtime check:
        # ===================================================================
        site_with_downtime = set()
        for mtrc in downObj.metrics():
            for dntm in downObj.downtimes( mtrc ):
                if (( dntm['type'] == "site" ) and
                    ( dntm['status'] == "downtime" )):
                    site_with_downtime.add( dntm['name'] )


        # loop over metric-tuple to-do list:
        # ==================================
        for mtrc in evalObj.metrics():
            interval = SReadinessMetric.interval( mtrc[0] )
            startTIS = mtrc[1] * interval
            mtrcTail = mtrc[0][2:]
            logging.log(15, "   metric (%s,%d), starting %s" % (mtrc[0],
                                                                mtrc[1],
                       time.strftime("%Y-%m-%d %H:%M", time.gmtime(startTIS))))
            #
            # find appropriate VO-feed (first time entry before metric starts):
            # -----------------------------------------------------------------
            for vofdTime in vofdTimeList:
                if ( vofdTime <= startTIS ):
                    break
            #
            # get list of active sites:
            # -------------------------
            siteList = vofdObj.sites(vofdTime)
            #
            #
            # get good 15min Site Readiness count inside time-bin:
            # ----------------------------------------------------
            if ( mtrcTail != "15min" ):
                start15m = startTIS / 900
                limit15m = (startTIS + interval) / 900
                #
                cntDict = count_good_15min(srObj, evalObj, start15m, limit15m)
            #
            #
            # loop over sites and evaluate Site Readiness:
            # ============================================
            samMtrc = ("sam"+mtrcTail, mtrc[1])
            hcMtrc = ("hc"+mtrcTail, mtrc[1])
            ftsMtrc = ("fts"+mtrcTail, mtrc[1])
            for site in siteList:
                detail = ""
                #
                # get SAM status:
                # ---------------
                try:
                    entry = get1entry_sam(samObj, samMtrc, site, "site")
                    sam_status = entry['status']
                    if entry['detail'] is not None:
                        if ( detail != "" ):
                            detail += ",\n"
                        detail += "SAM: %s (%s)" % (sam_status,
                                            entry['detail'].replace('\n','; '))
                    else:
                        if ( detail != "" ):
                            detail += ",\n"
                        detail += "SAM: %s" % sam_status
                except KeyError:
                    serviceList = vofdObj.services(vofdTime, site)
                    if ( len(serviceList) == 0 ):
                        sam_status = None
                    else:
                        sam_status = "unknown"
                #
                # get HammerCloud status:
                # -----------------------
                try:
                    entry = get1entry_hc(hcObj, hcMtrc, site)
                    hc_status = entry['status']
                    if entry['detail'] is not None:
                        if ( detail != "" ):
                            detail += ",\n"
                        # remove refid entries and convert to single line:
                        hc_detail = re.sub(hcRegex, "", entry['detail'])
                        hc_detail = hc_detail.replace(' \n','; ')
                        hc_detail = hc_detail.replace('\n','; ')
                        detail += "HC: %s (%s)" % (hc_status, hc_detail)
                    else:
                        if ( detail != "" ):
                            detail += ",\n"
                        detail += "HC: %s" % hc_status
                except KeyError:
                    serviceList = vofdObj.services(vofdTime, site, "CE")
                    if ( len(serviceList) == 0 ):
                        hc_status = None
                    else:
                        hc_status = "unknown"
                #
                # get FTS status:
                # ---------------
                try:
                    entry = ftsObj.get1entry(ftsMtrc, site, "site")
                    fts_status = entry['status']
                    if entry['detail'] is not None:
                        if ( detail != "" ):
                            detail += ",\n"
                        # keep link/endpoint info and convert to single line:
                        indx = entry['detail'].find("\nLinks: ") + 1
                        fts_detail = entry['detail'][indx:].replace('\n','; ')
                        detail += "FTS: %s (%s)" % (fts_status, fts_detail)
                    else:
                        if ( detail != "" ):
                            detail += ",\n"
                        detail += "FTS: %s" % fts_status
                except KeyError:
                    serviceList = vofdObj.services(vofdTime, site, "SE")
                    if ( len(serviceList) == 0 ):
                        fts_status = None
                    else:
                        fts_status = "unknown"
                logging.debug("      %s: SAM: %s, HC: %s, FTS: %s" % (site,
                                            sam_status, hc_status, fts_status))
                #
                #
                # evaluate Site Readiness status:
                # -------------------------------
                if (( sam_status == None ) and ( hc_status == None ) and
                    ( fts_status == None )):
                    continue
                for status in [ "downtime","error","unknown","warning","ok" ]:
                    if status in [ sam_status, hc_status, fts_status ]:
                        break
                if ((( status == "error" ) or ( status == "unknown" )) and
                    ( site in site_with_downtime )):
                    dt_flag, dt_strng = site_in_downtime(downObj, site, mtrc)
                    if ( dt_flag == True ):
                        status = "downtime"
                    if ( detail != "" ):
                           detail += ",\n"
                    detail += "downtime: %s" % dt_strng
                #
                #
                # calculate Site Readiness value:
                # -------------------------------
                if ( mtrcTail == "15min" ):
                    if (( status == "ok" ) or ( status == "warning" )):
                        value = 1.000
                    else:
                        value = 0.000
                else:
                    try:
                        value = cntDict[site]
                    except KeyError:
                        value = None
                #
                #
                # add site evaluation to Site Readiness metric of object:
                # =======================================================
                evalObj.add1entry(mtrc, { 'name': site, 'status': status,
                                          'value': value, 'detail': detail } )
                #
                try:
                    logging.log(15, "      %s: %s %.3f" % (site, status, value))
                except TypeError:
                    logging.log(15, "      %s: %s null" % (site, status))
            #
            #
            # check for all unknowns and remove metric in this case:
            # ======================================================
            rm_flag = True
            for entry in evalObj.evaluations(mtrc):
                if ( entry['status'] != "unknown" ):
                    rm_flag = False
                    break
            if ( rm_flag == True ):
                logging.log(25, ("Deleting Site Readiness metric (%s,%d) wit" +
                                 "h all, %d, unknown") % (mtrc[0], mtrc[1],
                                               len(evalObj.evaluations(mtrc))))
                evalObj.del1metric( mtrc )

        return
    # ####################################################################### #



    def monit_upload(mtrcObj):
        """function to upload Site Readiness evaluations to MonIT"""
        # ################################################################### #
        # upload Site Readiness evaluations as JSON metric documents to MonIT #
        # ################################################################### #
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
        cnt_15min = jsonString.count("\"monit_hdfs_path\": \"sr15min\"")
        cnt_1hour = jsonString.count("\"monit_hdfs_path\": \"sr1hour\"")
        cnt_6hour = jsonString.count("\"monit_hdfs_path\": \"sr6hour\"")
        cnt_1day  = jsonString.count("\"monit_hdfs_path\": \"sr1day\"")
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
            logging.log(25, ("JSON string with %d(15m)/%d(1h)/%d(6h)/%d(1d) " +
                             "docs uploaded to MonIT") %
                            (cnt_15min, cnt_1hour, cnt_6hour, cnt_1day))
        return successFlag
    # ####################################################################### #



    def write_evals(mtrcObj, filename=None):
        """function to write Site Readiness evaluations JSON to a file"""
        # ################################################################### #
        # write Site Readiness evaluations as JSON metric documents to a file #
        # ################################################################### #

        if filename is None:
            filename = "%s/eval_sr_%s.json" % (EVSR_BACKUP_DIR,
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



    parserObj = argparse.ArgumentParser(description="Script to evaluate Site" +
        " Readiness status for the 15 minute (1 hour, 6 hours, and 1 day) bi" +
        "n that started 60 minutes ago. SiteReadiness for a specific time bi" +
        "n or time interval are evaluated in case of of one or two arguments.")
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
                                 help="do not upload to MonIT but print FTS " +
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


    # find what we need to do:
    # ========================
    eval15min = set()
    eval1hour = set()
    eval6hour = set()
    eval1day  = set()

    now15m = int( time.time() / 900 )
    if argStruct.timeSpec is None:
        if ( argStruct.qhour ):
            # no time specified, evaluate/check recent time-bins:
            eval15min.add( now15m - 3 )
            eval15min.add( now15m - 6 )
            eval15min.add( now15m - 10 )
            eval15min.add( now15m - 15 )
        #
        # evaluate the time bin as requested/needed (3.5 hours after):
        if (( argStruct.hour ) and ( now15m % 4 == 2 )):
            bin15m = now15m - 18
            eval1hour.add( int(bin15m / 4) )
        if (( argStruct.qday ) and ( now15m % 24 == 14 )):
            bin15m = now15m - 38
            eval6hour.add( int(bin15m / 24) )
        if (( argStruct.day ) and ( now15m % 96 == 14 )):
            bin15m = now15m - 110
            eval1day.add( int(bin15m / 96) )
        #
        logging.log(15, "No time specified: 15 min bin starting %s" %
                    time.strftime("%Y-%b-%d %H:%M", time.gmtime(now15m * 900)))
    elif argStruct.lastSpec is None:
        # single time specification:
        if ( argStruct.timeSpec.isdigit() ):
            # argument should be time in seconds of 15 min time bin
            bin15m = int( argStruct.timeSpec / 900 )
        else:
            # argument should be the time in "YYYY-Mmm-dd HH:MM" format
            bin15m = int( calendar.timegm( time.strptime("%s UTC" %
                             argStruct.timeSpec, "%Y-%b-%d %H:%M %Z") ) / 900 )
        #
        # evaluate the time bins as requested:
        if ( argStruct.qhour ):
            eval15min.add( bin15m )
        if ( argStruct.hour ):
            eval1hour.add( int(bin15m / 4) )
        if ( argStruct.qday ):
            eval6hour.add( int(bin15m / 24) )
        if ( argStruct.day ):
            eval1day.add( int(bin15m / 96) )
        #
        logging.log(15, "Time specified: 15 min bin starting %s" %
                    time.strftime("%Y-%b-%d %H:%M", time.gmtime(bin15m * 900)))
    else:
        # start and end time specification:
        if ( argStruct.timeSpec.isdigit() ):
            # argument should be time in seconds of 15 min time bin
            frst15m = int( argStruct.timeSpec / 900 )
        else:
            # argument should be the time in "YYYY-Mmm-dd HH:MM" format
            frst15m = int( calendar.timegm( time.strptime("%s UTC" %
                             argStruct.timeSpec, "%Y-%b-%d %H:%M %Z") ) / 900 )
        #
        if ( argStruct.lastSpec.isdigit() ):
            # argument should be time in seconds of 15 min time bin
            last15m = int( argStruct.lastSpec / 900 )
        else:
            # argument should be the time in "YYYY-Mmm-dd HH:MM" format
            last15m = int( calendar.timegm( time.strptime("%s UTC" %
                             argStruct.lastSpec, "%Y-%b-%d %H:%M %Z") ) / 900 )
        #
        # evaluate time bins as requested:
        if ( argStruct.qhour ):
            for tbin in range(frst15m, last15m + 1):
                eval15min.add( tbin )
        if ( argStruct.hour ):
            for tbin in range( int(frst15m / 4), int(last15m / 4) + 1):
                eval1hour.add( tbin )
        if ( argStruct.qday ):
            for tbin in range( int(frst15m / 24), int(last15m / 24) + 1):
                eval6hour.add( tbin )
        if ( argStruct.day ):
            for tbin in range( int(frst15m / 96), int(last15m / 96) + 1):
                eval1day.add( tbin )
        #
        logging.log(15, "Time range specified: %s to %s" %
                  (time.strftime("%Y-%b-%d %H:%M", time.gmtime(frst15m * 900)),
            time.strftime("%Y-%b-%d %H:%M", time.gmtime((last15m * 900)+899))))
    logging.debug("   15 min  evaluations for %s" % str( sorted(eval15min) ))
    logging.debug("   1 hour  evaluations for %s" % str( sorted(eval1hour) ))
    logging.debug("   6 hours evaluations for %s" % str( sorted(eval6hour) ))
    logging.debug("   1 day   evaluations for %s" % str( sorted(eval1day) ))
    if (( len(eval15min) == 0 ) and ( len(eval1hour) == 0 ) and
        ( len(eval6hour) == 0 ) and ( len(eval1day) == 0 )):
        logging.log(25, "Nothing to do")
        sys.exit(0)


    # fetch list of sites:
    # ====================
    vofd = vofeed.vofeed()
    if argStruct.timeSpec is None:
        # load latest/fetch previous VO-feed information:
        vofd.load()
    elif argStruct.lastSpec is None:
        # fetch VO-feed information for time bin:
        vofd.fetch( bin15m * 900 )
    else:
        # fetch VO-feed information for time range:
        vofd.fetch( (frst15m * 900, last15m * 900) )
    if ( len( vofd.times() ) == 0 ):
        raise RuntimeError("VO-feed inventory is empty")


    # fetch site downtime information:
    # ================================
    minTIS = min( min( eval15min, default=now15m ) * 900,
                  min( eval1hour, default=int(now15m/4)+1 ) * 3600,
                  min( eval6hour, default=int(now15m/24)+1 ) * 21600,
                  min( eval1day,  default=int(now15m/96)+1 ) * 86400)
    maxTIS = max( ( max( eval15min, default=0 ) * 900 ) + 899,
                  ( max( eval1hour, default=0 ) * 3600 ) + 3599,
                  ( max( eval6hour, default=0 ) * 21600 ) + 21599,
                  ( max( eval1day,  default=0 ) * 86400 ) + 86399 )
    downDocs = eval_downtime.DowntimeMetric()
    downDocs.fetch( (minTIS, maxTIS) )
    #
    # trim downtime information to scheduled downtimes of sites
    cnt_docs = 0
    for mtrc in downDocs.metrics():
        for dntm in downDocs.downtimes( mtrc ):
            if (( dntm['type'] != "site" ) or
                ( dntm['status'] != "downtime" )):
                downDocs.del1entry(mtrc, dntm)
        cnt_docs += len( downDocs.downtimes(mtrc) )
    logging.info("   %d site scheduled downtime entries" % cnt_docs)


    # fetch necessary metrics:
    # ========================
    mtrcList = [ ("sam15min", e) for e in eval15min ] + \
               [ ("sam1hour", e) for e in eval1hour ] + \
               [ ("sam6hour", e) for e in eval6hour ] + \
               [ ("sam1day", e)  for e in eval1day  ]
    samMtrc = fetch_sam( mtrcList )
    #
    mtrcList = [ ("fts15min", e) for e in eval15min ] + \
               [ ("fts1hour", e) for e in eval1hour ] + \
               [ ("fts6hour", e) for e in eval6hour ] + \
               [ ("fts1day", e)  for e in eval1day  ]
    ftsDocs = eval_fts.FTSmetric()
    ftsDocs.fetch( mtrcList )
    #
    mtrcList = [ ("hc15min", e) for e in eval15min ] + \
               [ ("hc1hour", e) for e in eval1hour ] + \
               [ ("hc6hour", e) for e in eval6hour ] + \
               [ ("hc1day", e)  for e in eval1day  ]
    hcMtrc = fetch_hc( mtrcList )


    # fetch existing Site Readiness documents from MonIT:
    # ===================================================
    mtrcList = set()
    for tbin in eval1hour:
        for t15bin in range( tbin * 4, (tbin + 1) * 4):
            mtrcList.add( ("sr15min", t15bin) )
    for tbin in eval6hour:
        for t15bin in range( tbin * 24, (tbin + 1) * 24):
            mtrcList.add( ("sr15min", t15bin) )
    for tbin in eval1day:
        for t15bin in range( tbin * 96, (tbin + 1) * 96):
            mtrcList.add( ("sr15min", t15bin) )
    mtrcList.update( [ ("sr15min", e) for e in eval15min ] )
    mtrcList.update( [ ("sr1hour", e) for e in eval1hour ] )
    mtrcList.update( [ ("sr6hour", e) for e in eval6hour ] )
    mtrcList.update( [ ("sr1day", e)  for e in eval1day  ] )
    #
    monitDocs = SReadinessMetric()
    monitDocs.fetch( mtrcList )


    # evaluate Site Readiness status:
    # ===============================
    evalDocs = SReadinessMetric()
    for mtrc in [ ("sr15min", e) for e in eval15min ] + \
                [ ("sr1hour", e) for e in eval1hour ] + \
                [ ("sr6hour", e) for e in eval6hour ] + \
                [ ("sr1day", e)  for e in eval1day  ]:
        evalDocs.add1metric( mtrc )
    eval_status(evalDocs, vofd, samMtrc, hcMtrc, ftsDocs, downDocs, monitDocs)


    # filter out metric/time bin entries with identical docs in MonIT:
    # ================================================================
    cnt_docs = 0
    for tuple in sorted( evalDocs.metrics() ):
        if tuple in monitDocs.metrics():
            monitEvals = monitDocs.evaluations(tuple)
            for eval in evalDocs.evaluations(tuple):
                if eval in monitEvals:
                    logging.debug(("filtering out (%s, %d) %s as identical e" +
                                   "ntry exists in MonIT") %
                                            (tuple[0], tuple[1], eval['name']))
                    evalDocs.del1entry( tuple, eval )
                else:
                    cnt_docs += 1
            if ( len( evalDocs.evaluations(tuple) ) == 0 ):
                # no result left in metric/time-bin:
                evalDocs.del1metric( tuple )
        else:
            cnt_docs += len( evalDocs.evaluations(tuple) )


    # upload Site Readiness metric docs to MonIT:
    # ===========================================
    if ( cnt_docs > 0 ):
        if ( argStruct.upload ):
            successFlag = monit_upload( evalDocs )
        else:
            successFlag = False
        #
        if ( not successFlag ):
            write_evals( evalDocs )

    #import pdb; pdb.set_trace()
