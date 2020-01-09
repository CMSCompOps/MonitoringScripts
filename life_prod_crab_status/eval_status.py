#!/data/cmssst/packages/bin/python3.7
# ########################################################################### #
# python script to read the current VO-feed and manual override states, to    #
#    query downtime, HammerCloud, and Site Readiness metrics of the previous  #
#    days, and derive a LifeStatus, ProdStatus, and CrabStatus for sites.     #
#    The script checks and writes a new 15min metric in case of a change or   #
#    after midnight                                                           #
#                                                                             #
# 2019-Oct-08   Stephan Lammel                                                #
# ########################################################################### #
# 'metadata': {
#     'path':      "sts15min"
#     'timestamp': 1464871600000
# },
# "data": {
#      "name":        "T1_DE_KIT",
#      "status":      "enabled | waiting_room | morgue"
#      "prod_status": "enabled | drain | disabled | test"
#      "crab_status": "enabled | disabled"
#      "manual_life": "enabled | waiting_room | morgue"
#      "manual_prod": "enabled | drain | disabled | test"
#      "manual_crab": "enabled | disabled"
#      "detail":      "Life: approaching downtime\n
#                     "Prod: LifeStatus change to Waiting Room\n
#                     "CRAB: manual override"
#                     "Life: 5th Site Readiness error"
#                     "Life: 30 days in Waiting Room"
#                     "CRAB: no HammerCloud ok in last 3 days"
# }
# manual override: [ { 'name': "T1_DE_KIT",
#                      'status': "enabled | waiting_room | morgue",
#                      'mode':   "latched | toggle",
#                      'when':   "2019-Sep-28 12:45:12",
#                      'who':    "lammel",
#                      'why':    "issue resolved, returning site to service" },
#                    {...}, ... ]



import os, sys
import logging
import time, calendar
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



EVSTS_BACKUP_DIR = "./junk"
#EVSTS_BACKUP_DIR = "/data/cmssst/MonitoringScripts/site_status/failed"
# ########################################################################### #



class StatusMetric:
    'CMS Site Support Team Life/Prod/Crab Status metric class'

    def __init__(self):
        self.mtrc = {}
        return


    def fetch(self, timestamp):
        """function to retrieve Site Status evaluation docs from MonIT"""
        # ################################################################# #
        # In case timestamp is an integer retrieve the status document(s)   #
        # covering the time. In case timestamp is a tuple, retrieve the     #
        # status document(s) covering the time period spanned by the tuple. #
        # ################################################################# #
        HDFS_PREFIX = "/project/monitoring/archive/cmssst/raw/ssbmetric/"
        #
        # metric covering timestamp could be at midnight, fetch 1 extra day:
        if ( type(timestamp) == type( 0 ) ):
            timeFrst = (int( timestamp / 86400 ) - 1) * 86400
            timeLast = ( int( timestamp / 900 ) * 900 ) + 899
        elif ( type(timestamp) == type( (0,0) ) ):
            timeFrst = (int( timestamp[0] / 86400 ) - 1) * 86400
            timeLast = ( int( timestamp[1] / 900 ) * 900 ) + 899
        #
        oneDay = 86400
        now = int( time.time() )
        sixDaysAgo = calendar.timegm( time.gmtime(now - (6 * oneDay)) )


        # prepare HDFS subdirectory list:
        # ===============================
        logging.info("Retrieving site status docs from MonIT HDFS")
        logging.log(15, "   from %s to %s" %
                       (time.strftime("%Y-%m-%d %H:%M", time.gmtime(timeFrst)),
                    time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime(timeLast))))
        #
        dirList = set()
        for dirDay in range(timeFrst, timeLast + 1, oneDay):
            dirList.add( time.strftime("sts15min/%Y/%m/%d",
                                                         time.gmtime(dirDay)) )
        #
        startLclTmpArea = max( calendar.timegm( time.localtime( sixDaysAgo ) ),
                               calendar.timegm( time.localtime( timeFrst ) ) )
        midnight = ( int( now / 86400 ) * 86400 )
        limitLclTmpArea = calendar.timegm( time.localtime( midnight + 86399 ) )
        for dirDay in range( startLclTmpArea, limitLclTmpArea, oneDay):
            dirList.add( time.strftime("sts15min/%Y/%m/%d.tmp",
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
                            # read Site Status evaluation documents in file:
                            for myLine in fileObj:
                                myJson = json.loads(myLine.decode('utf-8'))
                                try:
                                    metric = myJson['metadata']['path']
                                    if ( metric != "sts15min" ):
                                        continue
                                    tis = int( myJson['metadata']['timestamp']
                                                                       / 1000 )
                                    if (( tis < timeFrst ) or
                                        ( tis > timeLast )):
                                        continue
                                    if 'manual_life' not in myJson['data']:
                                        myJson['data']['manual_life'] = None
                                    if 'manual_prod' not in myJson['data']:
                                        myJson['data']['manual_prod'] = None
                                    if 'manual_crab' not in myJson['data']:
                                        myJson['data']['manual_crab'] = None
                                    if 'detail' not in myJson['data']:
                                        myJson['data']['detail'] = None
                                    tbin = int( tis / 900 )
                                    name = myJson['data']['name']
                                    vrsn = myJson['metadata']['kafka_timestamp']
                                    #
                                    mKey = (metric, tbin)
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
                        except IOError as err:
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


        # load Site Status evaluation information into object:
        # ====================================================
        cnt_docs = 0
        cnt_mtrc = len(tmpDict)
        for mtrcKey in tmpDict:
            self.add1metric(mtrcKey)
            for evalKey in tmpDict[mtrcKey]:
                cnt_docs += 1
                self.add1entry(mtrcKey, tmpDict[mtrcKey][evalKey][1])
        del tmpDict

        logging.info("   found %d relevant status docs for %d metric-tuples" %
                                                          (cnt_docs, cnt_mtrc))
        #
        return


    def metrics(self):
        """function to return list of status metrics in the object inventory"""
        # ############################################################### #
        # metric names are all "sts15min" and returned sorted by time-bin #
        # ############################################################### #
        return sorted( self.mtrc.keys(), key=lambda m: m[1] )


    def evaluations(self, metric=None):
        """function to return a list of the evaluations for a metric tuple"""
        # ################################################################## #
        # metric is a tuple of metric-name and time-bin: ("sts15min", 40896) #
        # evaluations are returned sorted by site name                       #
        # ################################################################## #
        if (( metric is None ) and ( len(self.mtrc) == 1 )):
            metric = next(iter( self.mtrc.keys() ))
        #
        return sorted( self.mtrc[metric], key=lambda e: e['name'] )


    def sites(self, metric=None):
        """function to return a list of sites in the metric of the object"""
        # ################################################################## #
        # metric is a tuple of metric-name and time-bin: ("sts15min", 67816) #
        # ################################################################## #
        if (( metric is None ) and ( len(self.mtrc) == 1 )):
            metric = next(iter( self.mtrc.keys() ))
        #
        return sorted( [ e['name'] for e in self.mtrc[metric] ] )


    def status(self, metric, name):
        """function to return the Site Status triple of a site"""
        # ################################################################### #
        # metric is a tuple of metric-name and time-bin: ("sts15min", 67816)  #
        # and name is a CMS site name: Tn_CC_*                                #
        # return value is a tuple with LifeStatus, ProdStatus, and CrabStatus #
        # ################################################################### #
        if (( metric is None ) and ( len(self.mtrc) == 1 )):
            metric = next(iter( self.mtrc.keys() ))
        #
        for entry in self.mtrc[metric]:
            if ( entry['name'] == name ):
                if entry['manual_life'] is not None:
                    mLife = entry['manual_life']
                else:
                    mLife = "unknown"
                if entry['manual_prod'] is not None:
                    mProd = entry['manual_prod']
                else:
                    mProd = "unknown"
                if entry['manual_crab'] is not None:
                    mCrab = entry['manual_crab']
                else:
                    mCrab = "unknown"
                return ( entry['status'], \
                         entry['prod_status'], entry['crab_status'], \
                         mLife, mProd, mCrab )
        #
        return ( "unknown", "unknown", "unknown", \
                 "unknown", "unknown", "unknown" )


    def get1entry(self, metric, name):
        """return the entry of a Life/Prod/Crab Status Evaluation"""
        # ################################################################### #
        # metric is a tuple of metric-name and time-bin: ("sts15min", 169854) #
        # name is a site name of the form Tn_CC_*                             #
        # returned is an evaluation dictionary {'name':, 'status', ... }      #
        # ################################################################### #
        if (( metric is None ) and ( len(self.mtrc) == 1 )):
            metric = next(iter( self.mtrc.keys() ))
        #
        for entry in self.mtrc[metric]:
            if ( entry['name'] == name ):
                return entry
        #
        raise KeyError("No such entry %s in (%s,%d)" % (name,
                                                         metric[0], metric[1]))


    def add1metric(self, metric, data=None):
        """add an additional Site Status metric to the object inventory"""
        if ( metric[0] != "sts15min" ):
            raise ValueError("metric %s is not a valid Site Status name" %
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
        """function to add an additional Site Status entry to a metric"""
        siteRegex = re.compile(r"T\d_[A-Z]{2,2}_\w+")
        #
        # check entry has mandatory keys:
        if (( 'name' not in entry ) or ( 'status' not in entry ) or
            ( 'prod_status' not in entry ) or ( 'crab_status' not in entry )):
            raise ValueError("Mandatory keys missing in entry %s" %
                             str(entry))
        #
        if ( siteRegex.match( entry['name'] ) is None ):
             raise ValueError("Illegal site name %s" % entry['name'])
        #
        entry = entry.copy()
        if 'manual_life' not in entry:
            entry['manual_life'] = None
        if 'manual_prod' not in entry:
            entry['manual_prod'] = None
        if 'manual_crab' not in entry:
            entry['manual_crab'] = None
        if 'detail' not in entry:
            entry['detail'] = None
        elif ( entry['detail'] == "" ):
            entry['detail'] = None
        #
        self.mtrc[metric].append( entry )
        #
        return


    def update1entry(self, metric, entry):
        """function to add an additional Site Status entry to a metric"""
        siteRegex = re.compile(r"T\d_[A-Z]{2,2}_\w+")
        #
        # check entry has mandatory keys:
        if (( 'name' not in entry ) or ( 'status' not in entry ) or
            ( 'prod_status' not in entry ) or ( 'crab_status' not in entry )):
            raise ValueError("Mandatory keys missing in entry %s" %
                             str(entry))
        #
        if ( siteRegex.match( entry['name'] ) is None ):
             raise ValueError("Illegal site name %s" % entry['name'])
        #
        # locate previous entry of site and delete:
        for oldEntry in list(self.mtrc[metric]):
            if ( oldEntry['name'] == entry['name'] ):
                self.mtrc[metric].remove( oldEntry )
        #
        entry = entry.copy()
        if 'manual_life' not in entry:
            entry['manual_life'] = None
        if 'manual_prod' not in entry:
            entry['manual_prod'] = None
        if 'manual_crab' not in entry:
            entry['manual_crab'] = None
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
        """function to remove a site status evaluation entry from a metric"""
        # ################################################################### #
        self.mtrc[metric].remove( entry )


    def compose_json(self):
        """extract Site Status evaluations into a JSON string"""
        # ############################################################## #
        # compose a JSON string from the Site Status evaluations metrics #
        # in the object                                                  #
        # ############################################################## #

        jsonString = "["
        commaFlag = False
        #
        for metric in self.metrics():
            #
            timestamp = ( 900 * metric[1] ) + 450
            hdrString = (",\n {\n   \"producer\": \"cmssst\",\n" +
                                "   \"type\": \"ssbmetric\",\n" +
                                "   \"path\": \"sts15min\",\n" +
                                "   \"timestamp\": %d000,\n" +
                                "   \"type_prefix\": \"raw\",\n" +
                                "   \"data\": {\n") % timestamp
            #
            for entry in self.evaluations( metric ):
            #
                if commaFlag:
                    jsonString += hdrString
                else:
                    jsonString += hdrString[1:]
                jsonString += (("      \"name\": \"%s\",\n" +
                                "      \"status\": \"%s\",\n" +
                                "      \"prod_status\": \"%s\",\n" +
                                "      \"crab_status\": \"%s\",\n") %
                               (entry['name'], entry['status'],
                                   entry['prod_status'], entry['crab_status']))
                if entry['manual_life'] is not None:
                    jsonString += ("      \"manual_life\": \"%s\",\n" %
                                                          entry['manual_life'])
                if entry['manual_prod'] is not None:
                    jsonString += ("      \"manual_prod\": \"%s\",\n" %
                                                          entry['manual_prod'])
                if entry['manual_crab'] is not None:
                    jsonString += ("      \"manual_crab\": \"%s\",\n" %
                                                          entry['manual_crab'])
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
        """dump the contents of a Site Status evaluation object"""
        # ################################################################### #

        for metric in self.metrics():
            #
            timestamp = ( 900 * metric[1] ) + 450
            file.write("\nMetric \"%s\", %d (%s):\n" % (metric[0], metric[1],
                   time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime(timestamp))))
            file.write("---------------------------------------------------\n")
            #
            for entry in self.evaluations( metric ):
                #
                if entry['manual_life'] is not None:
                    mLife = entry['manual_life']
                else:
                    mLife = "unknown"
                if entry['manual_prod'] is not None:
                    mProd = entry['manual_prod']
                else:
                    mProd = "unknown"
                if entry['manual_crab'] is not None:
                    mCrab = entry['manual_crab']
                else:
                    mCrab = "unknown"
                if entry['detail'] is not None:
                    detail = entry['detail'].replace('\n','\n           ')
                else:
                    detail = "null"
                file.write("%s: %s/%s/%s %s/%s/%s\n   detail: %s\n" %
                           (entry['name'], entry['status'],
                           entry['prod_status'], entry['crab_status'],
                           mLife, mProd, mCrab, detail))
        file.write("=======================================================\n")
        file.write("\n")
        file.flush()
        return
# ########################################################################### #



if __name__ == '__main__':
    #
    import argparse
    import getpass
    import socket
    import shutil
    import http
    import fcntl
    #
    import vofeed
    import eval_downtime
    import eval_sreadiness



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
        # { ('hc15min', 16954): [ {'site':, 'status':, 'value':, ...},    #
        #                         {...}, ... ],                           #
        #   ('hc1hour', 1695):  [ {'site':, 'status':, 'value':, ...},    #
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
                                    metric = myJson['metadata']['path']
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
                                    site = myJson['data']['site']
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
                        except IOError as err:
                            logging.error("IOError accessing HDFS file %s: %s"
                                                     % (fileName, str(excptn)))
                        finally:
                            if fileObj is not None:
                                fileObj.close()
                            if fileHndl is not None:
                                fileHndl.close()
        except Exception as excptn:
            logging.error("Failed to fetch HC documents from MonIT HDFS: %s" %
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

        logging.info("   found %d relevant HC docs for %d metric-tuples" %
                                                          (cnt_docs, cnt_mtrc))
        #
        return MTRC


    def get1entry_hc(metricDict, metric, site):
        if (( metric is None ) and ( len(metricDict) == 1 )):
            metric = next(iter( metricDict.keys() ))
        #
        for entry in metricDict[metric]:
            if ( entry['site'] == site ):
                return entry
        #
        raise KeyError("No such entry %s in (%s,%d)" % (site,
                                                         metric[0], metric[1]))
    # ####################################################################### #


    def emergent_downtimes(downObj, timestamp):
        """find next scheduled or unscheduled downtime of sites"""
        # ################################################################# #
        # downObj is a filled downtime metric object, timestamp is the time #
        # used to discriminate past from current/future downtimes           #
        # function returns a site: list-of-string dictionary of sites with  #
        # an upcoming downtime, scheduled or adhoc, of over 24 hours        #
        # ################################################################# #
        time15m = int( timestamp / 900 )

        # latest downtime metric:
        mtrc = downObj.metrics()[-1]

        # loop over entris in metric and build site dictionary:
        downDict = {}
        for entry in downObj.downtimes( mtrc ):
            if ( entry['type'] != "site" ):
                continue
            if (( entry['status'] != "downtime" ) and
                ( entry['status'] != "adhoc" )):
                continue
            if ( entry['duration'][1] <  timestamp ):
                continue
            site    = entry['name']
            frst15m = int( entry['duration'][0] / 900 )
            last15m = int( (entry['duration'][1] - 1) / 900 )
            if site not in downDict:
                downDict[ site ] = []
            downDict[ site ].append( [ frst15m, last15m ] )
        #
        # loop over sites and combine downtimes if possible:
        for site in downDict:
            downDict[site].sort()
            for indx in range(len(downDict[site])-1, 0, -1):
                if ( (downDict[site][indx-1][1] + 1) >=
                                                     downDict[site][indx][0] ):
                    downDict[site][indx-1][1] = downDict[site][indx][1]
                    del downDict[site][indx]
        #
        # filter out future downtimes of less than 24 hours:
        for site in list( downDict ):
            for indx in range(len(downDict[site])-1, -1, -1):
                if (( downDict[site][indx][0] > time15m ) and
                    ( downDict[site][indx][1] - downDict[site][indx][0] < 95 )):
                    del downDict[site][indx]
            if ( len( downDict[site] ) == 0 ):
                del downDict[site]
        #
        # filter out any site without current or downtime within 48 hours:
        for site in list( downDict ):
            for indx in range(len(downDict[site])-1, -1, -1):
                if ( downDict[site][indx][0] <= time15m ):
                    downDict[site][indx] = "current"
                elif ( downDict[site][indx][0] <= time15m + 192 ):
                    downDict[site][indx] = "future"
                else:
                    del downDict[site][indx]
            if ( len( downDict[site] ) == 0 ):
                del downDict[site]
            else:
                logging.debug("   %s: %s downtime(s)", (site,
                                                          str(downDict[site])))

        return downDict
    # ####################################################################### #



    def hammercloud_good3days(hcDict, timestamp):
        """count number of good HC evaluations during the last three days"""
        # ############################################################## #
        # hcObj is a filled HammerCloud object, timestamp is used to     #
        # determine the last three days of HammerCloud evaluations; a HC #
        # evaluation metric with only unknown states is ignored, so more #
        # than the last three calendar days may be considered;           #
        # function returns a site: count dictionary of sites with a HC   #
        # evaluation in the examined interval                            #
        # ############################################################## #
        time1d = int( timestamp / 86400 )
        #
        logging.info("Counting number of good HC evaluations in last 3 days")

        # reverse-sorted list of relevant HammerCloud metrics:
        hcList = sorted( [ m for m in hcDict.keys()
                           if (( m[0] == "hc1day" ) and ( m[1] < time1d )) ],
                         key=lambda m: m[1], reverse=True )

        # loop over entris in metrics and build site dictionary:
        goodDict = {}
        n_days = 0
        for mtrc in hcList:
            # check for all unknown evaluations:
            use_flag = False
            for entry in hcDict[mtrc]:
                if ( entry['status'] != "unknown" ):
                    use_flag = True
                    break
            if ( use_flag == False ):
                continue
            #
            for entry in hcDict[mtrc]:
                site = entry['site']
                if site not in goodDict:
                    goodDict[ site ] = 0
                if (( entry['status'] == "ok" ) or
                    ( entry['status'] == "warning" )):
                    goodDict[ site ] += 1
            #
            n_days += 1
            if ( n_days >= 3 ):
                break;
        #
        if ( logging.getLogger().level <= 10 ):
            for site in goodDict:
                logging.debug("   %s: %d good HC evals" % (site,goodDict[site]))

        return goodDict
    # ####################################################################### #



    def sreadiness_bad14days(srObj, timestamp):
        """number of bad SR evals during the last fourteen days if bad now"""
        # ################################################################### #
        # srObj is a filled Site Readiness object, timestamp is used to       #
        # determine the last fourteen days of Site Readinness evaluations;    #
        # only sites with current bad SR state are included (and for tier-2   #
        # sites with continuous bad state since Friday in case of weekend);   #
        # unknown SR states are counted as bad except if the SR metric has    #
        # only downtime, error, or unknown states, i.e. one of the SR input   #
        # metric was missing, could not be evaluated, or evaluated to all     #
        # downtime, error, or unknown;
        # function returns a site: count dictionary of sites with a SR        #
        # evaluation in the examined interval                                 #
        # ################################################################### #
        time1d = int( timestamp / 86400 ) 
        frst1d = time1d - 14
        #
        logging.info("Counting number of bad SR entries in the last 2 weeks")

        # reverse-sorted list of relevant Site Readiness metrics:
        srList = sorted( [ m for m in srObj.metrics()
                           if (( m[0] == "sr1day" ) and
                               ( m[1] >= frst1d ) and ( m[1] < time1d )) ],
                         key=lambda m: m[1], reverse=True )

        # loop over entris in metrics and build site dictionary:
        badDict = {}
        for mtrc in srList:
            indxday = srList[0][1] - mtrc[1]
            weekday = ( mtrc[1] + 4) % 7
            #
            # check for all downtime,error,unknown evaluations:
            unkn_flag = False
            for entry in srObj.evaluations(mtrc):
                if (( entry['status'] == "warning" ) or
                    ( entry['status'] == "ok" )):
                    unkn_flag = True
                    break
            #
            for entry in srObj.evaluations(mtrc):
                site = entry['name']
                tier = site[1:2]
                if (( tier == "0" ) or ( tier == "1" )):
                    if (( entry['status'] == "error" ) or
                        (( unkn_flag ) and ( entry['status'] == "unknown" ))):
                        if ( indxday == 0 ):
                            badDict[ site ] = 0
                        try:
                            badDict[ site ] += 1
                        except KeyError:
                            pass
                else:
                    if (( indxday == 0 ) and
                        (( entry['status'] == "error" ) or
                         (( unkn_flag ) and ( entry['status'] == "unknown" )))):
                        badDict[ site ] = 0
                    elif (( indxday == 1 ) and
                          (( weekday == 6 ) or ( weekday == 5 )) and
                          (( entry['status'] == "ok" ) or
                           ( entry['status'] == "warning" ))):
                        try:
                            del badDict[ site ]
                        except KeyError:
                            pass
                    elif (( indxday == 2 ) and
                          ( weekday == 5 ) and
                          (( entry['status'] == "ok" ) or
                           ( entry['status'] == "warning" ))):
                        try:
                            del badDict[ site ]
                        except KeyError:
                            pass
                    if (( weekday >= 1 ) and ( weekday <= 5 ) and
                        (( entry['status'] == "error" ) or
                         (( unkn_flag ) and ( entry['status'] == "unknown" )))):
                        try:
                            badDict[ site ] += 1
                        except KeyError:
                            pass
        #
        if ( logging.getLogger().level <= 10 ):
            for site in badDict:
                logging.debug("   %s: %d bad SR days" % (site, badDict[site]))

        return badDict



    def sreadiness_bad3days(srObj, timestamp):
        """number of bad SR evals during the last three days if bad now"""
        # ################################################################### #
        # srObj is a filled Site Readiness object, timestamp is used to       #
        # determine the last three days of Site Readinness evaluations;       #
        # only sites with current bad SR state are included (and for tier-2   #
        # sites with continuous bad state since Friday in case of weekend);   #
        # unknown SR states are counted as bad except if the SR metric has    #
        # only downtime, error, or unknown states, i.e. one of the SR input   #
        # metric was missing, could not be evaluated, or evaluated to all     #
        # downtime, error, or unknown;
        # function returns a site: count dictionary of sites with a SR        #
        # evaluation in the examined interval                                 #
        # ################################################################### #
        time1d = int( timestamp / 86400 ) 
        wday1d = ( time1d + 4) % 7
        if ( wday1d == 0 ):
            frst1d = time1d - 4
        elif (( wday1d >= 1 ) and ( wday1d <= 3 )):
            frst1d = time1d - 5
        else:
            frst1d = time1d - 3
        #
        logging.info("Counting number of bad SR entries in the last 3 days")

        # reverse-sorted list of relevant Site Readiness metrics:
        srList = sorted( [ m for m in srObj.metrics()
                           if (( m[0] == "sr1day" ) and
                               ( m[1] >= frst1d ) and ( m[1] < time1d )) ],
                         key=lambda m: m[1], reverse=True )

        # loop over entris in metrics and build site dictionary:
        cntDict = {}
        badDict = {}
        for mtrc in srList:
            indxday = srList[0][1] - mtrc[1]
            weekday = ( mtrc[1] + 4) % 7
            #
            # check for all downtime,error,unknown evaluations:
            unkn_flag = False
            for entry in srObj.evaluations(mtrc):
                if (( entry['status'] == "warning" ) or
                    ( entry['status'] == "ok" )):
                    unkn_flag = True
                    break
            #
            for entry in srObj.evaluations(mtrc):
                site = entry['name']
                tier = site[1:2]
                if site not in cntDict:
                    cntDict[ site ] = 0
                if ( cntDict[ site ] >= 3 ):
                    continue
                #
                if (( tier == "0" ) or ( tier == "1" )):
                    # count SR states independently of workday or weekend:
                    cntDict[ site ] += 1
                    if (( entry['status'] == "error" ) or
                        (( unkn_flag ) and ( entry['status'] == "unknown" ))):
                        if ( indxday == 0 ):
                            # include only sites with current bad SR state:
                            badDict[ site ] = 0
                        try:
                            badDict[ site ] += 1
                        except KeyError:
                            pass
                else:
                    if (( entry['status'] == "error" ) or
                        (( unkn_flag ) and ( entry['status'] == "unknown" ))):
                        if ( indxday == 0 ):
                            # include only sites with current bad SR state:
                            badDict[ site ] = 0
                        if (( weekday >= 1 ) and ( weekday <= 5 )):
                            # include bad SR states only only workdays:
                            cntDict[ site ] += 1
                            try:
                                badDict[ site ] += 1
                            except KeyError:
                                pass
                    else:
                        # include good SR state throughout the week
                        cntDict[ site ] += 1
        #
        if ( logging.getLogger().level <= 10 ):
            for site in badDict:
                logging.debug("   %s: %d bad SR days" % (site, badDict[site]))

        return badDict



    def sreadiness_good7days(srObj, timestamp):
        """count number of good SR evaluations in a row before timestamp"""
        # ################################################################### #
        # srObj is a filled Site Readiness object, timestamp is used to       #
        # determine the last 7 days of Site Readinness evaluations;           #
        # function returns a site: count dictionary of sites with a SR        #
        # evaluation in the examined interval                                 #
        # ################################################################### #
        time1d = int( timestamp / 86400 ) 
        frst1d = time1d - 7
        #
        logging.info("Counting number of continuous good SR entries")

        # reverse-sorted list of relevant Site Readiness metrics:
        srList = sorted( [ m for m in srObj.metrics()
                           if (( m[0] == "sr1day" ) and 
                               ( m[1] >= frst1d ) and ( m[1] < time1d )) ],
                         key=lambda m: m[1], reverse=True )

        # sites currently in good state:
        goodDict = {}
        for entry in srObj.evaluations( srList[0] ):
            if (( entry['status'] == "ok" ) or
                ( entry['status'] == "warning" )):
                goodDict[ entry['name'] ] = 1
        del srList[0]
        #
        # loop over metrics and count continuous good states:
        day = 1
        for mtrc in srList:
            for entry in srObj.evaluations( mtrc ):
                if entry['name'] not in goodDict:
                    continue
                if ( goodDict[ entry['name'] ] != day ):
                    continue
                if (( entry['status'] == "ok" ) or
                    ( entry['status'] == "warning" )):
                    goodDict[ entry['name'] ] += 1
            day += 1
        
        if ( logging.getLogger().level <= 10 ):
            for site in goodDict:
                logging.debug("   %s: %d good SR days" % (site,goodDict[site]))

        return goodDict
    # ####################################################################### #



    def lifestatus_wr45days(stsObj, timestamp):
        """list of sites in Waiting Room LifeStatus state since 45 days"""
        # ################################################################# #
        # lifeObj is a filled LifeStatus object, timestamp is used to       #
        # determine the last fourtyfive days of LifeStatus states;          #
        # function returns a list of sites in Waiting Room state all of the #
        # last 45 days                                                      #
        # ################################################################# #
        time15m = int( timestamp / 900 )
        frst15m = ( int( time15m / 96 ) - 45 ) * 96
        #
        logging.info("List sites in Waiting Room state all of last 45 days")

        # reverse-sorted list of relevant Site Status metrics:
        stsList = sorted( [ m for m in stsObj.metrics()
                            if (( m[1] >= frst15m ) and ( m[1] < time15m )) ],
                          key=lambda m: m[1], reverse=True )
        if ( len( stsList ) == 0 ):
            return []

        # sites currently in Waiting Room state:
        badList = set()
        for entry in stsObj.evaluations( stsList[0] ):
            if ( entry['status'] == "waiting_room" ):
                badList.add( entry['name'] )
        del stsList[0]
        #
        # loop over metrics and remove sites not in Waiting Room state:
        for mtrc in stsList:
            for entry in stsObj.evaluations( mtrc ):
                if ( entry['status'] != "waiting_room" ):
                    try:
                        badList.remove( entry['name'] )
                        if ( len(badList) == 0 ):
                            break
                    except KeyError:
                        pass
            if ( len(badList) == 0 ):
                break
        #
        badList = sorted( badList )
        #
        if ( logging.getLogger().level <= 10 ):
            logging.debug("   WR state last 45 days: %s" % str(badList))

        return badList
    # ####################################################################### #



    def read_override(filename):
        """read in override file and return contents in dictionary"""
        # ################################################################ #
        LOCK_FILE = "./cache/status.lock"
        #LOCK_FILE = "/eos/home-c/cmssst/www/override/data/status.lock"

        remainWait = 3.0
        while ( remainWait > 0.0 ):
            with open(LOCK_FILE, 'w') as lckFile:
                try:
                    fcntl.lockf(lckFile, fcntl.LOCK_EX | fcntl.LOCK_NB)
                except BlockingIOError:
                    sleep(0.250)
                    remainWait -= 0.250
                    continue
                #
                #
                try:
                    with open(filename, 'rt') as myFile:
                        #
                        jsonString = myFile.read()
                        #
                except Exception as excptn:
                    logging.error("Error reading override file %s: %s" %
                                                       (filename, str(excptn)))
                    sleep(1.000)
                    remainWait -= 1.000
                    continue
                #
                fcntl.lockf(lckFile, fcntl.LOCK_UN)
                break
        #
        if ( remainWait <= 0 ):
            logging.error("Failed to read override file %s" % filename)
            return {}

        # decode JSON:
        # ============
        try:
            overrideList = json.loads( jsonString )
            del jsonString
        except json.decoder.JSONDecodeError as excptn:
            logging.error("JSON decoding failed, file %s: %s"
                                                     % (filename, str(excptn)))
            return {}

        # convert to dictionary:
        # ======================
        overrideDict = {}
        for entry in overrideList:
            if (( 'name' not in entry ) or ( 'status' not in entry ) or
                ( 'mode' not in entry )):
                logging.error("Mandatory key(s) missing in override entry %s" %
                                                                    str(entry))
                continue
            if 'when' not in entry:
                entry['when'] = ""
            if 'who' not in entry:
                entry['who'] = ""
            if 'why' not in entry:
                entry['why'] = ""
            overrideDict[ entry['name'] ] = entry
        del overrideList

        logging.info("Override with %d entries read in" % len(overrideDict))

        return overrideDict



    def compose_override(overrideList):
        """compose JSON string from list of manual override entries"""
        # ################################################################### #
        jsonString = "["
        commaFlag = False
        #
        for entry in overrideList:
            if commaFlag:
                jsonString += ",\n {\n"
            else:
                jsonString += "\n {\n"
            jsonString += (("   \"name\": \"%s\",\n" +
                            "   \"status\": \"%s\",\n" +
                            "   \"mode\": \"%s\",\n") %
                           (entry['name'], entry['status'], entry['mode']))
            if entry['when'] is not None:
                jsonString += ("   \"when\": \"%s\",\n" % entry['when'])
            else:
                jsonString += ("   \"when\": null,\n")
            if entry['who'] is not None:
                jsonString += ("   \"who\": \"%s\",\n" % entry['who'])
            else:
                jsonString += ("   \"who\": null,\n")
            if entry['why'] is not None:
                jsonString += ("   \"why\": \"%s\"\n }" % entry['why'])
            else:
                jsonString += ("   \"why\": null\n }")
            commaFlag = True
        jsonString += "\n]\n"
        #
        return jsonString



    def update_override(filename, entry):
        """update a manual override file with an entry of a site"""
        # ################################################################# #
        # "name" is mandatory, if status is None the existing entry will be #
        # removed from the file                                             #
        # ################################################################# #
        LOCK_FILE = "./cache/status.lock"
        #LOCK_FILE = "/eos/home-c/cmssst/www/override/data/status.lock"
        siteRegex = re.compile(r"T\d_[A-Z]{2,2}_\w+")
        #
        if ( siteRegex.match( entry['name'] ) is None ):
            logging.error("Illegal site name %s" % entry['name'])
            return
        site = entry['name']
 
        remainWait = 3.0
        while ( remainWait > 0.0 ):
            with open(LOCK_FILE, 'w') as lckFile:
                try:
                    fcntl.lockf(lckFile, fcntl.LOCK_EX | fcntl.LOCK_NB)
                except BlockingIOError:
                    sleep(0.250)
                    remainWait -= 0.250
                    continue
                #
                #
                try:
                    with open(filename, 'r+t') as myFile:
                        #
                        jsonString = myFile.read()
                        #
                        entries = json.loads( jsonString )
                        #
                        entries = [ e for e in entries if ( e['name'] != site ) ]
                        if entry['status'] is not None:
                            entries.append(entry)
                        #
                        jsonString = compose_override(entries)
                        #
                        myFile.seek(0)
                        myFile.write(jsonString)
                        #
                    logging.info("Successfully updated override file %s" %
                                                                      filename)
                except Exception as excptn:
                    logging.warning("Error updating override file %s: %s" %
                                                       (filename, str(excptn)))
                    sleep(1.000)
                    remainWait -= 1.000
                    continue
                #
                fcntl.lockf(lckFile, fcntl.LOCK_UN)
                break

        if ( remainWait <= 0 ):
            logging.error("Failed to update override file %s" % filename)
        return
    # ####################################################################### #



    def eval_lifestatus(evalObj, stsObj, srObj):
        """function to evaluate Life Status of sites"""
        # ################################################################### #
        LIFE_FILE = "/eos/home-c/cmssst/www/override/data/LifeStatus.json"
        #
        metric = evalObj.metrics()[0]
        timestamp = metric[1] * 900
        #
        logging.info("Evaluating Life Status for %d (%s)" % (metric[1],
                      time.strftime("%Y-%b-%d %H:%M", time.gmtime(timestamp))))


        # get previous LifeStatus evaluations:
        # ====================================
        mtrc = stsObj.metrics()[-1]
        logging.debug("Previous LifeStatus metric from %d (%s)" % (mtrc[1],
                  time.strftime("%Y-%b-%d %H:%M", time.gmtime(mtrc[1] * 900))))
        prevDict = {}
        for entry in stsObj.evaluations( mtrc ):
            prevDict[ entry['name'] ] = entry


        # get a dictionary with bad SR states during last 14 days:
        # ========================================================
        sr14badDict = sreadiness_bad14days(srObj, timestamp)

        # get a dictionary with good SR states in a row:
        # ==============================================
        sr7goodDict = sreadiness_good7days(srObj, timestamp)


        # get a list of sites with LifeStatus Waiting Room state for 45 days:
        # ===================================================================
        ls45wrList = lifestatus_wr45days(stsObj, timestamp)


        # get manual override information:
        # ================================
        overrideDict = read_override(LIFE_FILE)


        # get list of sites for evaluation from latest Site Readiness metric:
        # ===================================================================
        mtrc = srObj.metrics()[-1]
        siteList = srObj.sites( mtrc )


        # loop over sites and evaluate LifeStatus:
        # ========================================
        nChange = 0
        for site in siteList:
            newOverride = None
            #
            # fetch existing entry in status metric:
            # ======================================
            try:
                entry = evalObj.get1entry(metric, site)
            except KeyError:
                entry = { 'name': site, 'detail': "",
                          'prod_status': "unknown", 'crab_status': "unknown" }
            #
            # get previous LifeStatus:
            # ========================
            try:
                pStatus = prevDict[site]['status']
            except KeyError:
                pStatus = "unknown"
            nStatus = pStatus
            oStatus = None
            detail = ""

            # process state changes:
            # ======================
            if (( pStatus == "enabled" ) or ( pStatus == "unknown" )):
                # check for 5th error states in 2 weeks:
                try:
                    cnt = sr14badDict[site]
                    if ( cnt >= 5 ):
                        nStatus = "waiting_room"
                        detail = "Life: 5th Site Readiness error in 2 weeks"
                except KeyError:
                    pass
            #
            if (( pStatus == "waiting_room" ) or ( pStatus == "unknown" )):
                # check for 3rd ok states in a row:
                try:
                    cnt = sr7goodDict[site]
                    if ( cnt >= 3 ):
                        nStatus = "enabled"
                        detail = "Life: 3rd Site Readiness ok in a row"
                except KeyError:
                    pass
            #
            if ( pStatus == "waiting_room" ):
                # check is 45 days in Waiting Room state:
                if site in ls45wrList:
                    nStatus = "morgue"
                    detail = "Life: 45 days in Waiting Room state"
            #
            if ( pStatus == "morgue" ):
                # check for 5th ok states in a row:
                try: 
                    cnt = sr7goodDict[site]
                    if ( cnt >= 5 ):
                        nStatus = "waiting_room"
                        detail = "Life: 5th Site Readiness ok in a row"
                        #
                        # prepare manual override entry:
                        timestrng = time.strftime("%Y-%b-%d %H:%M:%S",
                                                      time.gmtime(time.time()))
                        newOverride = { 'name': site,
                                        'status': nStatus, 'mode': "latched",
                                        'when': timestrng, 'who': "eval_status",
                                        'why': "holding for re-commissioning" }
                except KeyError:
                    pass
            #
            # apply any manual override:
            # ==========================
            try:
                manOverride = overrideDict[site]
                if manOverride['status'] is None:
                    raise KeyError("Cleared override")
                if ( manOverride['status'] == "" ):
                    raise KeyError("Cleared override")
                oStatus = manOverride['status']
                if ( manOverride['mode'] == "oneday" ):
                    theDay = int( calendar.timegm( time.strptime(
                          manOverride['when'], "%Y-%b-%d %H:%M:%S") ) / 86400 )
                    if ( theDay >= mtrc[1] ):
                        nStatus = manOverride['status']
                        detail = "Life: manual override by %s (%s)" % \
                                       (manOverride['who'], manOverride['why'])
                    else:
                        newOverride = { 'name': site, 'status': None }
                elif ( manOverride['mode'] == "toggle" ):
                    if ( nStatus != manOverride['status'] ):
                        nStatus = manOverride['status']
                        detail = "Life: manual override by %s (%s)" % \
                                       (manOverride['who'], manOverride['why'])
                    else:
                        newOverride = { 'name': site, 'status': None }
                else:
                    nStatus = manOverride['status']
                    detail = "Life: manual override by %s (%s)" % \
                                       (manOverride['who'], manOverride['why'])
                    newOverride = None
            except KeyError:
                pass
            #
            # update manual override file if needed:
            # ======================================
            if newOverride is not None:
                update_override(LIFE_FILE, newOverride)
            #
            #
            # update metric entry:
            # ====================
            entry['status'] = nStatus
            if oStatus is not None:
                entry['manual_life'] = oStatus
            if ( entry['detail'] != "" ):
                entry['detail'] += ",\n"
            entry['detail'] += detail
            evalObj.update1entry(metric, entry)
            #
            if ( pStatus != nStatus ):
                nChange += 1

        logging.info("LifeStatus evaluation led to %d state changes" % nChange)
        return
    # ####################################################################### #



    def eval_prodstatus(evalObj, stsObj, srObj, downObj):
        """function to evaluate Prod Status of sites"""
        # ################################################################### #
        PROD_FILE = "/eos/home-c/cmssst/www/override/data/ProdStatus.json"
        #
        metric = evalObj.metrics()[0]
        timestamp = metric[1] * 900
        #
        logging.info("Evaluating Prod Status for %d (%s)" % (metric[1],
                      time.strftime("%Y-%b-%d %H:%M", time.gmtime(timestamp))))


        # get previous ProdStatus evaluations:
        # ====================================
        mtrc = stsObj.metrics()[-1]
        logging.debug("Previous ProdStatus metric from %d (%s)" % (mtrc[1],
                  time.strftime("%Y-%b-%d %H:%M", time.gmtime(mtrc[1] * 900))))
        prevDict = {}
        for entry in stsObj.evaluations( mtrc ):
            prevDict[ entry['name'] ] = entry


        # get a dictionary with bad SR states during last 3 days:
        # =======================================================
        sr3badDict = sreadiness_bad3days(srObj, timestamp)

        # get a dictionary with good SR states in a row:
        # ==============================================
        sr7goodDict = sreadiness_good7days(srObj, timestamp)


        # get a dictionary of sites with emerging downtime:
        # =================================================
        down48hDict = emergent_downtimes(downObj, timestamp)


        # get manual override information:
        # ================================
        overrideDict = read_override(PROD_FILE)


        # get list of sites for evaluation from latest Site Readiness metric:
        # ===================================================================
        mtrc = srObj.metrics()[-1]
        siteList = srObj.sites( mtrc )


        # loop over sites and evaluate ProdStatus:
        # ========================================
        nChange = 0
        for site in siteList:
            newOverride = None
            #
            # fetch existing entry in status metric:
            # ======================================
            try:
                entry = evalObj.get1entry(metric, site)
                if entry['detail'] is None:
                    entry['detail'] = ""
            except KeyError:
                entry = { 'name': site, 'detail': "",
                          'status': "unknown", 'crab_status': "unknown" }
            #
            # get current LifeStatus:
            # ========================
            try:
                lStatus = entry['status']
            except KeyError:
                # take previous LifeStatus:
                try:
                    lStatus = prevDict[site]['status']
                except KeyError:
                    lStatus = "unknown"
            #
            # get previous ProdStatus:
            # ========================
            try:
                pStatus = prevDict[site]['prod_status']
            except KeyError:
                pStatus = "unknown"
            logging.log(15, "%s previous ProdStatus = %s" % (site, pStatus))
            nStatus = pStatus
            oStatus = None
            detail = ""

            # process state changes:
            # ======================
            if (( pStatus == "enabled" ) or ( pStatus == "unknown" )):
                # check for 2nd error states in 3 days:
                try:
                    cnt = sr3badDict[site]
                    logging.log(15, "   3-day bad SiteReadiness = %d" % cnt)
                    if ( cnt >= 2 ):
                        nStatus = "drain"
                        detail = "Prod: 2nd Site Readiness error in 3 days"
                except KeyError:
                    pass
            #
            if (( pStatus == "disabled" ) or ( pStatus == "drain" ) or
                                             ( pStatus == "unknown" )):
                # check for 2nd ok states in a row:
                try:
                    cnt = sr7goodDict[site]
                    logging.log(15, "   good SiteReadiness iaR = %d" % cnt)
                    if ( cnt >= 2 ):
                        nStatus = "enabled"
                        detail = "Prod: 2nd Site Readiness ok in a row"
                except KeyError:
                    pass
            #
            if ( pStatus != "test" ):
                # check for 24 hour downtime within next 48 hours:
                try:
                    downStrng = str(down48hDict[site]).replace("'","")
                    logging.log(15, "   emerging downtime = %s" % downStrng)
                    nStatus = "drain"
                    detail = "Prod: Emerging downtime, %s" % downStrng
                except KeyError:
                    pass
            #
            if (( pStatus != "test" ) and
                ( lStatus == "waiting_room" )):
                logging.log(15, "   Waiting Room state")
                nStatus = "drain"
                detail = "Prod: site in Waiting Room state"
            #
            if (( pStatus != "test" ) and
                ( lStatus == "morgue" )):
                logging.log(15, "   Morgue state")
                nStatus = "disabled"
                detail = "Prod: site in Morgue state"
            #
            # apply any manual override:
            # ==========================
            try:
                manOverride = overrideDict[site]
                if manOverride['status'] is None:
                    raise KeyError("Cleared override")
                if ( manOverride['status'] == "" ):
                    raise KeyError("Cleared override")
                logging.log(15, "   manual override = %s (%s)" % 
                                  (manOverride['status'], manOverride['mode']))
                oStatus = manOverride['status']
                if ( manOverride['mode'] == "oneday" ):
                    theDay = int( calendar.timegm( time.strptime(
                          manOverride['when'], "%Y-%b-%d %H:%M:%S") ) / 86400 )
                    if ( theDay >= mtrc[1] ):
                        nStatus = manOverride['status']
                        detail = "Prod: manual override by %s (%s)" % \
                                       (manOverride['who'], manOverride['why'])
                    else:
                        newOverride = { 'name': site, 'status': None }
                elif ( manOverride['mode'] == "toggle" ):
                    if ( nStatus != manOverride['status'] ):
                        nStatus = manOverride['status']
                        detail = "Prod: manual override by %s (%s)" % \
                                       (manOverride['who'], manOverride['why'])
                    else:
                        newOverride = { 'name': site, 'status': None }
                else:
                    nStatus = manOverride['status']
                    detail = "Prod: manual override by %s (%s)" % \
                                       (manOverride['who'], manOverride['why'])
                    newOverride = None
            except KeyError:
                pass
            #
            # update manual override file if needed:
            # ======================================
            if newOverride is not None:
                update_override(PROD_FILE, newOverride)
            #
            #
            # update metric entry:
            # ====================
            entry['prod_status'] = nStatus
            if oStatus is not None:
                entry['manual_prod'] = oStatus
            if ( entry['detail'] != "" ):
                entry['detail'] += ",\n"
            entry['detail'] += detail
            evalObj.update1entry(metric, entry)
            #
            if ( pStatus != nStatus ):
                nChange += 1

        logging.info("ProdStatus evaluation led to %d state changes" % nChange)
        return
    # ####################################################################### #



    def eval_crabstatus(evalObj, stsObj, srObj, hcDict):
        """function to evaluate Prod Status of sites"""
        # ################################################################### #
        CRAB_FILE = "/eos/home-c/cmssst/www/override/data/CrabStatus.json"
        #
        metric = evalObj.metrics()[0]
        timestamp = metric[1] * 900
        #
        logging.info("Evaluating Crab Status for %d (%s)" % (metric[1],
                      time.strftime("%Y-%b-%d %H:%M", time.gmtime(timestamp))))


        # get previous CrabStatus evaluations:
        # ====================================
        mtrc = stsObj.metrics()[-1]
        logging.debug("Previous CrabStatus metric from %d (%s)" % (mtrc[1],
                  time.strftime("%Y-%b-%d %H:%M", time.gmtime(mtrc[1] * 900))))
        prevDict = {}
        for entry in stsObj.evaluations( mtrc ):
            prevDict[ entry['name'] ] = entry


        # get a dictionary with good HammerCloud states during last 3 days:
        # =================================================================
        hc3goodDict = hammercloud_good3days(hcDict, timestamp)


        # get manual override information:
        # ================================
        overrideDict = read_override(CRAB_FILE)


        # get list of sites for evaluation from latest Site Readiness metric:
        # ===================================================================
        mtrc = srObj.metrics()[-1]
        siteList = srObj.sites( mtrc )


        # loop over sites and evaluate CrabStatus:
        # ========================================
        nChange = 0
        for site in siteList:
            newOverride = None
            #
            # fetch existing entry in status metric:
            # ======================================
            try:
                entry = evalObj.get1entry(metric, site)
                if entry['detail'] is None:
                    entry['detail'] = ""
            except KeyError:
                entry = { 'name': site, 'detail': "",
                          'status': "unknown", 'prod_status': "unknown" }
            #
            # get current LifeStatus:
            # ========================
            try:
                lStatus = entry['status']
            except KeyError:
                # take previous LifeStatus:
                try:
                    lStatus = prevDict[site]['status']
                except KeyError:
                    lStatus = "unknown"
            #
            # get previous CrabStatus:
            # ========================
            try:
                pStatus = prevDict[site]['crab_status']
            except KeyError:
                pStatus = "unknown"

            oStatus = None

            # check Hammer Cloud results:
            # ===========================
            try:
                cnt = hc3goodDict[site]
                if ( cnt >= 1 ):
                    nStatus = "enabled"
                    detail = "Crab: %d Hammer Cloud ok state(s) in 3 days" % cnt
                else:
                    nStatus = "disabled"
                    detail = "Crab: No Hammer Cloud ok state in 3 days"
            except KeyError:
                nStatus = "disabled"
                detail = "Crab: No Hammer Cloud entry in 3 days"
            #
            if (( lStatus == "waiting_room" ) or ( lStatus == "morgue" )):
                nStatus = "disabled"
                detail = "Crab: site in Waiting Room/Morgue state"
            #
            # apply any manual override:
            # ==========================
            try:
                manOverride = overrideDict[site]
                if manOverride['status'] is None:
                    raise KeyError("Cleared override")
                if ( manOverride['status'] == "" ):
                    raise KeyError("Cleared override")
                oStatus = manOverride['status']
                if ( manOverride['mode'] == "oneday" ):
                    theDay = int( calendar.timegm( time.strptime(
                          manOverride['when'], "%Y-%b-%d %H:%M:%S") ) / 86400 )
                    if ( theDay >= mtrc[1] ):
                        nStatus = manOverride['status']
                        detail = "Crab: manual override by %s (%s)" % \
                                       (manOverride['who'], manOverride['why'])
                    else:
                        newOverride = { 'name': site, 'status': None }
                elif ( manOverride['mode'] == "toggle" ):
                    if ( nStatus != manOverride['status'] ):
                        nStatus = manOverride['status']
                        detail = "Crab: manual override by %s (%s)" % \
                                       (manOverride['who'], manOverride['why'])
                    else:
                        newOverride = { 'name': site, 'status': None }
                else:
                    nStatus = manOverride['status']
                    detail = "Crab: manual override by %s (%s)" % \
                                       (manOverride['who'], manOverride['why'])
                    newOverride = None
            except KeyError:
                pass
            #
            # update manual override file if needed:
            # ======================================
            if newOverride is not None:
                update_override(CRAB_FILE, newOverride)
            #
            #
            # update metric entry:
            # ====================
            entry['crab_status'] = nStatus
            if oStatus is not None:
                entry['manual_crab'] = oStatus
            if ( entry['detail'] != "" ):
                entry['detail'] += ",\n"
            entry['detail'] += detail
            evalObj.update1entry(metric, entry)
            #
            if ( pStatus != nStatus ):
                nChange += 1

        logging.info("CrabStatus evaluation led to %d state changes" % nChange)
        return
    # ####################################################################### #



    def monit_upload(mtrcObj):
        """function to upload Site Status evaluations to MonIT"""
        # ################################################################ #
        # upload Site Status evaluations as JSON metric documents to MonIT #
        # ################################################################ #
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
        cnt_15min = jsonString.count("\"path\": \"sts15min\"")
        #
        jsonString = jsonString.replace("ssbmetric", "metrictest")


        # upload string with JSON document array to MonIT/HDFS:
        # =====================================================
        docs = json.loads(jsonString)
        ndocs = len(docs)
        successFlag = True
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
                    logging.error(("Failed to upload JSON [%d:%d] string to " +
                                   "MonIT, %d \"%s\"") %
                                  (myOffset, min(ndocs,myOffset+4096),
                                   responseObj.status, responseObj.reason))
                    successFlag = False
                responseObj.close()
            except urllib.error.URLError as excptn:
                logging.error("Failed to upload JSON [%d:%d], %s" %
                             (myOffset, min(ndocs,myOffset+4096), str(excptn)))
                successFlag = False
        del docs

        if ( successFlag ):
            logging.log(25, ("JSON string with %d docs uploaded to MonIT") %
                                                                     cnt_15min)
        return successFlag
    # ####################################################################### #



    def write_evals(mtrcObj, filename=None):
        """function to write Site Status evaluations JSON to a file"""
        # ################################################################ #
        # write Site Status evaluations as JSON metric documents to a file #
        # ################################################################ #

        if filename is None:
            filename = "%s/eval_sts_%s.json" % (EVSTS_BACKUP_DIR,
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



    def compose_prod_ssbmetric(evalObj):
        """compose production backward compatible SSB metric file string"""
        # ########################################################## #

        now = time.strftime("%Y-%b-%d %H:%M:%S UTC", time.gmtime())
        #
        ssbString = "#txt\n#\n# Site Support Team, Prod Status SSB-Metric\n"
        ssbString += (("#    written at %s by %s\n#    in account %s on node" +
                       " %s\n#    maintained by cms-comp-ops-site-support-te" +
                       "am@cern.ch\n#   https://twiki.cern.ch/twiki/bin/view" +
                       "/CMS/SiteSupportSiteStatusSiteReadiness\n# =========" +
                       "==============================================\n#\n") %
                      (now, sys.argv[0], getpass.getuser(), socket.getfqdn()))
        #
        mtrc = evalObj.metrics()[0]
        timeStrng = time.strftime("%Y-%m-%d %H:%M:%S",
                                  time.gmtime( 900 * mtrc[1] ))
        #
        for entry in evalObj.evaluations( mtrc ):
            if ( entry['prod_status'] == "enabled" ):
                my_colour = "green"
            elif ( entry['prod_status'] == "drain" ):
                my_colour = "yellow"
            elif ( entry['prod_status'] == "disabled" ):
                my_colour = "red"
            elif ( entry['prod_status'] == "test" ):
                my_colour = "yellow"
            else:
                continue
            ssbString += (("%s\t%s\t%s\t%s\thttps://twiki.cern.ch/twiki/bin/" +
                           "view/CMS/SiteSupportSiteStatusSiteReadiness\n" ) %
                          (timeStrng, entry['name'], entry['prod_status'],
                           my_colour))
        #
        return ssbString



    def compose_prod_ssbjson(evalObj):
        """compose production backward compatible SSB JSON file string"""
        # ########################################################## #

        jsonString = "{\"csvdata\": ["
        commaFlag = False
        #
        mtrc = evalObj.metrics()[0]
        strtStrng = time.strftime("%Y-%m-%dT%H:%M:%S",
                                  time.gmtime( 900 * mtrc[1] ))
        stopStrng = time.strftime("%Y-%m-%dT%H:%M:%S",
                                  time.gmtime( (900 * mtrc[1]) + 86400 ))
        #
        for entry in evalObj.evaluations( mtrc ):
            if ( entry['prod_status'] == "enabled" ):
                my_colour = "green"
            elif ( entry['prod_status'] == "drain" ):
                my_colour = "yellow"
            elif ( entry['prod_status'] == "disabled" ):
                my_colour = "red"
            elif ( entry['prod_status'] == "test" ):
                my_colour = "yellow"
            else:
                continue
            try:
                my_tier = int( entry['name'][1] )
            except ValueError:
                my_tier = 9
            if commaFlag:
                jsonString += ", "
            jsonString += (("{\"Status\": \"%s\", \"COLORNAME\": \"%s\", " +
                             "\"VOName\": \"%s\", \"Time\": \"%s\", " +
                             "\"Tier\": %d, \"EndTime\": \"%s\"}") %
                           (entry['prod_status'], my_colour, entry['name'],
                            strtStrng, my_tier, stopStrng))
            commaFlag = True
        jsonString += "]}"
        #
        return jsonString



    def write_prod_ssbmetric(evalObj):
        """function to write backward compatible SSB metric file for P&R"""
        # ############################################################## #
        # write ProdStatus information as SSB metric file for production #
        # ############################################################## #
        PRODSTS_FILE = "./junk/ProdStatus.txt"
        PRODSTS_COPY = None
        #PRODSTS_FILE = "/afs/cern.ch/user/c/cmssst/www/prodstatus/ProdStatus.txt"
        #PRODSTS_COPY = "/eos/home-c/cmssst/www/ssb_metric/ProdStatus.txt"

        logging.info("Writing ProdStatus SSB JSON file")

        # compose ProdStatus SSB JSON string:
        # ===================================
        jsonString = compose_prod_ssbmetric(evalObj)
        if ( jsonString == "{\"csvdata\": []}" ):
            logging.warning("skipping writing of site-devoid SSB JSON string")
            return False


        # write string to file:
        # =====================
        try:
            with open(PRODSTS_FILE + "_new", 'w') as myFile:
                myFile.write( jsonString )
            #
            # move file into place:
            os.rename(PRODSTS_FILE + "_new", PRODSTS_FILE)
            #
            # place copy as required:
            if PRODSTS_COPY is not None:
                shutil.copyfile(PRODSTS_FILE, PRODSTS_COPY)
        except Exception as excptn:
            logging.critical("Failed to write ProdStatus SSB JSON file, %s" %
                                                                   str(excptn))

        return
    # ####################################################################### #



    def compose_crab_usablesites(evalObj):
        """compose CRAB backward compatible usableSites.json string"""
        # ########################################################## #

        jsonString = "["
        commaFlag = False
        #
        mtrc = evalObj.metrics()[0]
        timestamp = ( 900 * mtrc[1] ) + 450
        #
        for entry in evalObj.evaluations( mtrc ):
            if commaFlag:
                jsonString += ","
            if ( entry['crab_status'] == "enabled" ):
                my_colour = "green"
                my_value  = "usable"
            else:
                my_colour = "red"
                my_value  = "not_usable"
            jsonString += (("\n  {\n" +
                            "    \"name\": \"%s\",\n" +
                            "    \"nvalue\": null,\n" +
                            "    \"color\": \"%s\",\n" +
                            "    \"value\": \"%s\",\n" +
                            "    \"url\": \"https://twiki.cern.ch/twiki/bin/" +
                           "view/CMS/SiteSupportSiteStatusSiteReadiness\",\n" +
                            "    \"date\": %d\n" +
                            "  }" ) % (entry['name'], my_colour, my_value,
                                       timestamp))
            commaFlag = True
        jsonString += "\n]\n"
        #
        return jsonString



    def write_crab_usablesites(evalObj):
        """function to write backward compatible usableSites.json for CRAB"""
        # ############################################################## #
        # write CrabStatus information as usableSites.json file for CRAB #
        # ############################################################## #
        USABLE_FILE = "./junk/usableSites.json"
        USABLE_COPY = None
        #USABLE_FILE = "/afs/cern.ch/user/c/cmssst/www/analysis/usableSites.json"
        #USABLE_COPY = "/eos/home-c/cmssst/www/ssb_metric/usableSites.json"

        logging.info("Writing CRAB usableSites JSON file")

        # compose usableSites JSON string:
        # ================================
        jsonString = compose_crab_usablesites(evalObj)
        if ( jsonString == "[\n]\n" ):
            logging.warning("skipping writing of site-devoid JSON string")
            return False


        # write string to file:
        # =====================
        try:
            with open(USABLE_FILE + "_new", 'w') as myFile:
                myFile.write( jsonString )
            #
            # move file into place:
            os.rename(USABLE_FILE + "_new", USABLE_FILE)
            #
            # place copy as required:
            if USABLE_COPY is not None:
                shutil.copyfile(USABLE_FILE, USABLE_COPY)
        except Exception as excptn:
            logging.critical("Failed to write CRAB usableSites JSON file, %s" %
                                                                   str(excptn))

        return
    # ####################################################################### #



    parserObj = argparse.ArgumentParser(description="Script to evaluate Site" +
        " Status, i.e. LifeStatus, ProdStatus, and CrabStatus, for the curre" +
        "nt 15 minute bin.")
    parserObj.add_argument("-U", dest="upload", default=True,
                                 action="store_false",
                                 help="do not upload to MonIT but print stat" +
                                 "us evaluations")
    parserObj.add_argument("-v", action="count", default=0,
                                 help="increase verbosity")
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


    # Site Status will always be evaluated for the current 15 min time-bin:
    # =====================================================================
    now15m = int( time.time() / 900 )


    # fetch Site Readiness metrics of previous 15 days:
    # =================================================
    ystr1d = int( now15m / 96 ) - 1
    mtrcList = [ ("sr1day", e) for e in range(ystr1d, ystr1d - 15, -1) ]
    srDocs = eval_sreadiness.SReadinessMetric()
    srDocs.fetch( mtrcList )


    # fetch current downtime information:
    # ===================================
    ystrTIS = ystr1d * 86400
    b15mTIS = ( now15m * 900 ) + 899
    downDocs = eval_downtime.DowntimeMetric()
    downDocs.fetch( (ystrTIS, b15mTIS) )
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


    # fetch HammerCloud metrics of previous 6 days:
    # =============================================
    mtrcList = [ ("hc1day", e) for e in range(ystr1d, ystr1d - 6, -1) ]
    hcMtrc = fetch_hc( mtrcList )


    # fetch Site Status metrics of previous 46 days:
    # ==============================================
    a45dTIS = ( ystr1d - 46 ) * 86400
    stsDocs = StatusMetric()
    stsDocs.fetch( (a45dTIS, b15mTIS) )
    if ( len( stsDocs.metrics() ) == 0 ):
        stsDocs.add1metric( ("sts15min", 0) )



    # evaluate Site Statuses (Life, Prod, Crab):
    # ==========================================
    evalDocs = StatusMetric()
    evalDocs.add1metric( ("sts15min", now15m) )
    #
    # evaluate LifeStatus:
    eval_lifestatus(evalDocs, stsDocs, srDocs)
    #
    # evaluate ProdStatus:
    eval_prodstatus(evalDocs, stsDocs, srDocs, downDocs)
    #
    # evaluate CrabStatus:
    eval_crabstatus(evalDocs, stsDocs, srDocs, hcMtrc)



    # filter out metric/time bin entries with identical docs in MonIT:
    # ================================================================
    mtrc = stsDocs.metrics()[-1]
    prvDict = {}
    for entry in stsDocs.evaluations( mtrc ):
        site = entry['name']
        prvDict[site] = entry
    #
    cnt_docs = 0
    for eval in evalDocs.evaluations( ("sts15min", now15m) ):
        site = eval['name']
        if site not in prvDict:
            cnt_docs += 1
        elif (( eval['status'] != prvDict[site]['status'] ) or
              ( eval['prod_status'] != prvDict[site]['prod_status'] ) or
              ( eval['crab_status'] != prvDict[site]['crab_status'] ) or
              ( eval['manual_life'] != prvDict[site]['manual_life'] ) or
              ( eval['manual_prod'] != prvDict[site]['manual_prod'] ) or
              ( eval['manual_crab'] != prvDict[site]['manual_crab'] )):
            cnt_docs += 1


    # upload Site Readiness metric docs to MonIT (status change or new day):
    # ======================================================================
    if (( cnt_docs > 0 ) or
        ( int( now15m / 96 ) != int( mtrc[1] / 96 ) )):
        if ( argStruct.upload ):
            successFlag = monit_upload( evalDocs )
        else:
            successFlag = False
        #
        if ( not successFlag ):
            write_evals( evalDocs )
        #
        write_prod_ssbmetric(evalDocs)
        write_crab_usablesites(evalDocs)

    #import pdb; pdb.set_trace()
