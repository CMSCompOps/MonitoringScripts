#!/data/cmssst/packages/bin/python3.7
# ########################################################################### #
# python script to write the CMS VO-feed XML and JSON files. The script is    #
#    based on earlier versions that run inside the SAM3 dashboard.            #
#                                                                             #
# 2016-Dec-28   Stephan Lammel                                                #
# ########################################################################### #
# 'metadata': {
#     'timestamp': 1464871600000,
# }
# 'data': {
#     'vo': "CMS",
#     'update': "2016-06-02T12:45:00Z",
#     'site': "T0_CH_CERN",
#     'tier': 0,
#     'gridsite': "CERN-PROD",
#     'services': [
#         {
#             'category':
#             'hostname':
#             'flavour':
#             'endpoint':
#             'queue':
#             'batch':
#             'production': true | false
#         }, {
#             ...
#         }
#     ]
# }


import os, sys
import logging
import time, calendar
import urllib.request, urllib.error
import json
import xml.etree.ElementTree
import re
import gzip
#
# setup the Java/HDFS/PATH environment for pydoop to work properly:
os.environ["HADOOP_CONF_DIR"] = "/opt/hadoop/conf/etc/analytix/hadoop.analytix"
os.environ["JAVA_HOME"]       = "/etc/alternatives/jre"
os.environ["HADOOP_PREFIX"]   = "/usr/hdp/hadoop"
import pydoop.hdfs
# ########################################################################### #



VOFEED_VERSION = "v2.00.04"
# ########################################################################### #



class vofeed:
    'CMS Site Support Team VO-feed topology class'

    def __init__(self):
        self.topo = {}
        return


    @staticmethod
    def type2flavour(type):
        """function to translate a grid service type into VO-feed flavour"""
        TYPE_FLAVOUR_DICT = {
            'CE':                             "CE",
            'GLOBUS':                         "CE",
            'gLite-CE':                       "CE",
            'ARC-CE':                         "ARC-CE",
            'CREAM-CE':                       "CREAM-CE",
            'org.opensciencegrid.htcondorce': "HTCONDOR-CE",
            'HTCONDOR-CE':                    "HTCONDOR-CE",
            'gLExec':                         "",
            'SE':                             "SRM",
            'SRM':                            "SRM",
            'SRMv2':                          "SRM",
            'SRMv1':                          "SRM",
            'globus-GRIDFTP':                 "SRM",
            'GridFtp':                        "SRM",
            'webdav':                         "",
            'XROOTD':                         "XROOTD",
            'XRootD':                         "XROOTD",
            'XRootD.Redirector':              "XROOTD",
            'XRootD origin server':           "XROOTD",
            'XRootD component':               "XROOTD",
            'org.squid-cache.Squid':          "",
            'perfSONAR':                      "perfSONAR",
            'net.perfSONAR.Bandwidth':        "perfSONAR",
            'net.perfSONAR.Latency':          "perfSONAR",
            'Squid':                          "",
            'site':                           "site"
        }
        try:
            return TYPE_FLAVOUR_DICT[type]
        except KeyError:
            return ""


    @staticmethod
    def flavour2category(flavour):
        """function to translate a VO-feed flavour into service category"""
        FLAVOUR_CATEGORY_DICT = {
            'CE':            "CE",
            'CREAM-CE':      "CE",
            'ARC-CE':        "CE",
            'HTCONDOR-CE':   "CE",
            'SRM':           "SE",
            'XROOTD':        "XRD",
            'perfSONAR':     "perfSONAR",
            'site':          "site"
        }
        try:
            return FLAVOUR_CATEGORY_DICT[flavour]
        except KeyError:
            return ""


    @staticmethod
    def type2category(type):
        """function to translate a grid service type into service category"""
        return vofeed.flavour2category( vofeed.type2flavour(type) )


    def load(self):
        """function to load the current VO-feed information from FILE/URL"""
        # ############################################################ #
        # load the current VO-feed information into the object, either #
        # directly reading the vofeed.xml file from AFS or via http    #
        # ############################################################ #
        VOFEED_FILE = "/afs/cern.ch/user/c/cmssst/www/vofeed/vofeed.xml"
        VOFEED_URL  = "http://cmssst.web.cern.ch/cmssst/vofeed/vofeed.xml"

        try:
            with open(VOFEED_FILE, 'r') as myFile:
                myData = myFile.read()
        except:
            with urllib.request.urlopen(VOFEED_URL) as urlHandle:
                urlCharset = urlHandle.headers.get_content_charset()
                if urlCharset is None:
                    urlCharset = "utf-8"
                myData = urlHandle.read().decode( urlCharset )

        # decode XML:
        vofd = xml.etree.ElementTree.fromstring( myData )
        del myData

        if 0 in self.topo:
            del self.topo[0]
        self.topo[0] = {}

        # loop over entries (multiple entries per grid and CMS site possible):
        for atpsite in vofd.findall('atp_site'):
            site = None
            for group in atpsite.findall('group'):
                if 'type' in group.attrib:
                    if ( group.attrib['type'] == "CMS_Site" ):
                        site = group.attrib['name']
                        break
            if site is None:
                continue
            self.add1site(0, site)
            #
            gridsite = atpsite.attrib['name']
            for service in atpsite.findall('service'):
                host = service.attrib['hostname'].lower()
                flavour = service.attrib['flavour']
                if 'production_status' not in service.attrib:
                    prod = True
                elif ( service.attrib['production_status'].lower() == "false" ):
                    prod = False
                else:
                    prod = True
                ctgry = vofeed.flavour2category(flavour)
                #
                srvc = { 'category': ctgry, 'hostname': host,
                         'flavour': flavour, 'production': prod }
                #
                if ( gridsite != "" ):
                    srvc['gridsite'] = gridsite
                if 'endpoint' in service.attrib:
                    srvc['endpoint'] = service.attrib['endpoint']
                if ( ctgry == 'CE' ):
                    resources = service.findall('ce_resource')
                else:
                    resources = []
                #
                if ( len(resources) <= 0 ):
                    self.add1service(0, site, srvc)
                else:
                    for resource in resources:
                        xsrvc = srvc.copy()
                        if 'batch_system' in resource.attrib:
                            xsrvc['batch'] = resource.attrib['batch_system']
                        if 'queue' in resource.attrib:
                            xsrvc['queue'] = resource.attrib['queue']
                        self.add1service(0, site, xsrvc)
                        del xsrvc
                #
                del srvc

        # link timestamp of the VO-feed to latest, 0 entry:
        timestamp = calendar.timegm( time.strptime("%s UTC" %
                       vofd.findtext('last_update'), "%Y-%m-%dT%H:%M:%SZ %Z") )
        if timestamp in self.topo:
            del self.topo[timestamp]
        self.topo[timestamp] = self.topo[0]
        #
        return


    def fetch(self, timestamp):
        """function to retrieve VO-feed information from MonIT"""
        # ################################################################ #
        # In case timestamp is an integer, retrieve the VO-feed time entry #
        # covering that time. In case timestamp is a tuple, retrieve the   #
        # VO-feed time entries covering the time period in the tuple       #
        # ################################################################ #
        HDFS_PREFIX = "/project/monitoring/archive/cmssst/raw/ssbmetric/"
        #
        if ( type(timestamp) == type(0) ):
            timeFrst = int( timestamp / 86400 ) * 86400
            timeLast = ( int( timestamp / 900 ) * 900 ) + 450
        elif ( type(timestamp) == type( (0,0) ) ):
            timeFrst = int( timestamp[0] / 86400 ) * 86400
            timeLast = ( int( timestamp[1] / 900 ) * 900 ) + 450
        #
        oneDay = 24*60*60
        now = int( time.time() )
        startTmpArea = max( calendar.timegm( time.gmtime(now - (6 * oneDay)) ),
                            timeFrst - oneDay)
        limitLocalTmpArea = calendar.timegm( time.localtime( now ) ) + oneDay
        #
        logging.info("Retrieving VO-feed docs from MonIT HDFS")
        logging.log(15, "   from %s to %s" %
                       (time.strftime("%Y-%m-%d %H:%M", time.gmtime(timeFrst)),
                    time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime(timeLast))))
        #
        dirList = []
        for dirDay in range(timeFrst, timeLast + 1, oneDay):
            dirList.append( time.strftime("vofeed15min/%Y/%m/%d",
                                          time.gmtime( dirDay )) )
        for dirDay in range(startTmpArea, limitLocalTmpArea, oneDay):
            dirList.append( time.strftime("vofeed15min/%Y/%m/%d.tmp",
                                          time.gmtime( dirDay )) )
        del dirDay

        # connect to HDFS, loop over directories and read VO-feed docs:
        # =============================================================
        siteRegex = re.compile(r"T\d_[A-Z]{2,2}_\w+")
        tmpVersion = {}
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
                            # read VO-feed documents in file:
                            for myLine in fileObj:
                                myJson = json.loads(myLine.decode('utf-8'))
                                try:
                                    if (( myJson['metadata']['path'] !=
                                                             "vofeed15min" ) or
                                        ( myJson['data']['vo'] != "CMS" )):
                                        continue
                                    tis = int(myJson['metadata']['timestamp']
                                                                         /1000)
                                    if (( tis < timeFrst ) or
                                        ( tis > timeLast )):
                                        continue
                                    site = myJson['data']['site']
                                    if ( siteRegex.match( site ) is None ):
                                        continue
                                    try:
                                        grid = myJson['data']['gridsite']
                                    except:
                                        grid = ""
                                    tuple = (site, grid)
                                    vrsn = myJson['metadata']['kafka_timestamp']
                                    srvcs = myJson['data']['services']
                                    #
                                    if tis not in tmpVersion:
                                        tmpVersion[tis] = {}
                                    if tuple in tmpVersion[tis]:
                                        if ( vrsn <= tmpVersion[tis][tuple][0] ):
                                            continue
                                    tmpVersion[tis][tuple] = (vrsn, srvcs)
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
                                fileObj  = None
                            if fileHndl is not None:
                                fileHndl.close()
                                fileHndl = None
        except Exception as excptn:
            logging.error("Failed to fetch documents from MonIT HDFS: %s" %
                          str(excptn))


        # load timebin, site, service information into VO-feed object:
        # ============================================================
        cnt_docs = 0
        cnt_time = len(tmpVersion)
        cnt_srvc = 0
        for timestamp in tmpVersion:
            self.add1time(timestamp)
            for entry in tmpVersion[timestamp]:
                cnt_docs += 1
                site = entry[0]
                grid = entry[1]
                self.add1site(timestamp, site)
                cnt_srvc += len( tmpVersion[timestamp][entry][1] )
                for service in tmpVersion[timestamp][entry][1]:
                    if (( 'hostname' not in service ) or
                        ( 'flavour' not in service )):
                        logging.error(("Mandatory hostname and/or flavour mi" +
                                       "ssing in service %s") % str(service))
                        cnt_srvc -= 1
                        continue
                    service['hostname'] = service['hostname'].lower()
                    if ( grid != "" ):
                        service['gridsite'] = grid
                    self.add1service(timestamp, site, service)
        del tmpVersion

        logging.info("   found %d relevant docs with %d timebins/%d services" %
                                                (cnt_docs, cnt_time, cnt_srvc))
        #
        return


    def times(self):
        """function to return list of VO-feed times in object inventory"""
        return sorted( self.topo.keys() )


    def sites(self, timestamp=None):
        """function to return list of CMS sites in the VO-feed for the time"""
        # ############################################################## #
        # timestamp=None selects the available VO-feed time entry or the #
        # latest is multiple are available                               #
        # timestamp=0 selects the latest VO-feed time entry              #
        # ############################################################## #
        if timestamp is not None:
            return sorted( self.topo[timestamp].keys() )
        elif ( len(self.topo) == 1 ):
            return sorted( next(iter( self.topo.values() )).keys() )
        else:
            return sorted( self.topo[0].keys() )


    def services(self, timestamp=None, site=None, category=None):
        """function to return list of services filtered by site/category"""
        # ############################################################## #
        # timestamp=None selects the available VO-feed time entry or the #
        # latest is multiple are available                               #
        # timestamp=0 selects the latest VO-feed time entry              #
        # ############################################################## #
        if timestamp is None:
            if ( len(self.topo) == 1 ):
                timestamp = next(iter( self.topo.keys() ))
            else:
                timestamp = 0
        #
        if site is None:
            siteList = list( self.topo[timestamp].keys() )
        else:
            siteList = [ site ]
        #
        myList = []
        for mySite in siteList:
            try:
                myDict = self.topo[timestamp][mySite]
            except KeyError:
                continue
            for myService in myDict:
                if ( myService['production'] != True ):
                    continue
                if category is not None:
                    if ( category != myService['category'] ):
                        continue
                myList.append( myService )
        #
        return myList


    def add1time(self, timestamp):
        """function to add an additional VO-feed time entry to the object"""
        if timestamp not in self.topo:
            self.topo[timestamp] = {}
        return


    def add1site(self, timestamp, site):
        """function to add an additional site to the VO-feed time entry"""
        siteRegex = re.compile(r"T\d_[A-Z]{2,2}_\w+")
        #
        if ( siteRegex.match( site ) is None ):
            raise ValueError("Site \"%s\" is not a valid CMS sitename" % site)
        #
        if site not in self.topo[timestamp]:
            self.topo[timestamp][site] = []
        #
        return


    def add1service(self, timestamp, site, service):
        """function to add an additional service to a site in the VO-feed"""
        service = service.copy()
        #
        if (( 'hostname' not in service ) or ( 'flavour' not in service )):
            raise ValueError(("Mandatory hostname and/or flavour missing in " +
                              "service %s") % str(service))
        #
        service['hostname'] = service['hostname'].lower()
        if 'production' not in service:
            service['production'] = True
        #
        # prefer first prod=True entry for host/flavour:
        for srv in self.topo[timestamp][site]:
            if (( srv['hostname'] == service['hostname'] ) and
                ( srv['flavour'] == service['flavour'] )):
                if ( srv['production'] == True ):
                    return
                elif ( service['production'] == False ):
                    return
                self.topo[timestamp][site].remove( srv )
                break
        #
        service['category'] = vofeed.flavour2category( service['flavour'] )
        #
        self.topo[timestamp][site].append( service )
        #
        return


    def trim0service(self, timestamp):
        """remove sites without services from a VO-feed time entry"""
        for site in sorted( self.topo[timestamp].keys() ):
            if ( len(self.topo[timestamp][site]) == 0 ):
                del self.topo[timestamp][site]
        return
            

    def delete(self, timestamp):
        """function to remove a VO-feed time entry from the object"""
        del self.topo[timestamp]
        #
        return


    def compare2times(self, timeone, timetwo):
        """function to compare two VO-feed time entries from the object"""
        #
        site1List = sorted( [k for k in self.topo[timeone]
                             if ( len(self.topo[timeone][k]) != 0) ] )
        site2List = sorted( [k for k in self.topo[timetwo]
                             if ( len(self.topo[timetwo][k]) != 0) ] )
        if ( site1List != site2List ):
            diffList = [e for e in site1List + site2List
                        if ((e not in site1List) or (e not in site2List)) ]
            logging.log(25, ("Site inventory in VO-feed time entries differ:" +
                             " %s") % str(diffList))
            return False
        #
        for site in site1List:
            if ( len(self.topo[timeone][site]) !=
                 len(self.topo[timetwo][site]) ):
                diffList = [e for e in self.topo[timeone][site] +
                                       self.topo[timetwo][site]
                            if ((e not in self.topo[timeone][site]) or
                                (e not in self.topo[timetwo][site])) ]
                logging.log(25, ("Service inventory of site %s in VO-feed ti" +
                                 "me entries differs : %s") % (site, diffList))
                return False
            for service in self.topo[timeone][site]:
                if service not in self.topo[timetwo][site]:
                    diffList = [e for e in self.topo[timeone][site] +
                                           self.topo[timetwo][site]
                                if ((e not in self.topo[timeone][site]) or
                                    (e not in self.topo[timetwo][site])) ]
                    logging.log(25, ("Service inventory of site %s in VO-fee" +
                                     "d time entries differs : %s") % (site,
                                                                     diffList))
                    return False
        #
        return True


    def convert2XML(self, timestamp, owner, site2email):
        """function to extract a VO-feed time entry into an XML string"""
        RECORD_FIRST = [ ("T0_CH_CERN",     "CERN-PROD"),
                         ("T2_CH_CSCS",     "CSCS-LCG2"),
                         ("T2_US_Nebraska", "Nebraska"),
                         ("T2_US_Purdue",   "Purdue-Hammer") ]
        SAM3_GROUPS = {
            '0': ['AllGroups', 'Tier1s + Tier0', 'Tier2s + Tier1s + Tier0'],
            '1': ['AllGroups', 'Tier1s + Tier0', 'Tier2s + Tier1s + Tier0',
                  'Tier3s + Tier2s + Tier1s'],
            '2': ['AllGroups', 'Tier2s', 'Tier3s + Tier2s',
                  'Tier2s + Tier1s + Tier0', 'Tier3s + Tier2s + Tier1s'],
            '3': ['AllGroups', 'Tier3s', 'Tier3s + Tier2s',
                  'Tier3s + Tier2s + Tier1s'],
            '9': ['AllGroups']
        }
        #
        if ( timestamp == 0 ):
            for entry in self.topo:
                if ( self.topo[entry] == self.topo[0] ):
                    timestamp = entry
                    break
        if ( timestamp == 0 ):
            raise ValueError("XML conversion must be for a specific timestamp")
        #
        xmlString = ("<root>\n   <title>CMS Topology Information</title>\n  " +
                     " <description>List of CMS grid sites and resources for" +
                     " SAM/WLCG monitoring</description>\n   <feed_responsib" +
                     "le>DN=\"%s\"</feed_responsible>\n   <last_update>%s</l" +
                     "ast_update>\n   <version>%s</version>\n   <vo>cms</vo>" +
                     "\n") % (owner, time.strftime("%Y-%m-%dT%H:%M:%SZ",
                                                   time.gmtime(timestamp)),
                              VOFEED_VERSION)
        #
        # write special, multi-CMS and multi-grid site, ahead of other sites:
        siteList = RECORD_FIRST.copy()
        for site in sorted( self.topo[timestamp].keys() ):
            gridSet = set()
            for srvc in self.topo[timestamp][site]:
                try:
                    gridSet.add( srvc['gridsite'] )
                except:
                    gridSet.add( "" )
            if "" in gridSet:
                gridSet.remove( "" )
                gridList = sorted( gridSet )
                gridList.append( "" )
            else:
                gridList = sorted( gridSet )
            del gridSet
            for gridsite in gridList:
                tuple = (site, gridsite)
                if tuple not in siteList:
                    siteList.append( tuple )
        #
        for tuple in siteList:
            site = tuple[0]
            grid = tuple[1]
            #
            tier = site[1:2]
            if tier not in ['0', '1', '2', '3']:
                tier = '9'
            #
            # for right now, map non-registered resources to first gridsite
            if ( grid == "" ):
                 try:
                     email = site2email[site]
                     if ( email is None ):
                         raise UnboundLocalError(("No email for site admin " +
                                                  "at \"%s\"") % site)
                     xmlString += ("   <atp_site name=\"%s\" contact=\"%s\">" +
                                   "\n") % (grid, email)
                 except:
                     xmlString += "   <atp_site name=\"%s\">\n" % grid
            else:
                xmlString += "   <atp_site name=\"%s\">\n" % grid
            for srvc in self.topo[timestamp][site]:
                try:
                    gridsite = srvc['gridsite']
                except:
                    gridsite = ""
                if ( gridsite != grid ):
                    continue
                #
                xmlString += "      <service hostname=\"%s\" flavour=\"%s\"" \
                             % (srvc['hostname'], srvc['flavour'])
                if 'endpoint' in srvc:
                    xmlString += " endpoint=\"%s\"" % srvc['endpoint']
                if ( not srvc['production'] ):
                    xmlString += " production_status=\"false\""
                if (( 'queue' in srvc ) and
                    ( srvc['flavour'] in ["GLOBUS", "CREAM-CE"] ) and
                    ( 'batch' in srvc )):
                    xmlString += (">\n         <ce_resource batch_system=\"" +
                                  "%s\" queue=\"%s\"/>\n      </service>\n") \
                                 % (srvc['batch'], srvc['queue'])
                elif ( 'queue' in srvc ):
                    xmlString += (">\n         <ce_resource queue=\"%s\"/>\n" +
                                  "      </service>\n") % srvc['queue']
                elif (( srvc['flavour'] in ["GLOBUS", "CREAM-CE"] ) and
                      ( 'batch' in srvc )):
                    xmlString += (">\n         <ce_resource batch_system=\"" +
                                  "%s\"/>\n      </service>\n") % srvc['batch']
                else:
                    xmlString += "/>\n"
            xmlString += ("      <group name=\"Tier-%s\" type=\"CMS_Tier\"/>" +
                          "\n      <group name=\"%s\" type=\"CMS_Site\"/>\n") \
                         % (tier, site)
            for group in SAM3_GROUPS[tier]:
                xmlString += "      <group name=\"%s\" type=\"%s\"/>\n" % \
                             (site, group)
            xmlString += "   </atp_site>\n"
        #
        xmlString += "</root>\n"
        #
        return xmlString


    def convert2JSON(self, timestamp):
        """function to extract a VO-feed time entry into an JSON string"""
        if ( timestamp == 0 ):
            for entry in self.topo:
                if ( self.topo[entry] == self.topo[0] ):
                    timestamp = entry
                    break
        if ( timestamp == 0 ):
            raise ValueError("JSON conversion must be for a specific timestamp")
        #
        jsonString = "["
        comma1Flag = False
        #
        hdrString = (",\n {\n   \"producer\": \"cmssst\",\n" +
                            "   \"type\": \"ssbmetric\",\n" +
                            "   \"path\": \"vofeed15min\",\n" +
                            "   \"timestamp\": %d000,\n" +
                            "   \"type_prefix\": \"raw\",\n" +
                            "   \"data\": {\n") % timestamp
        updateStr = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(timestamp))
        #
        for site in sorted( self.topo[timestamp].keys() ):
            gridSet = set()
            for srvc in self.topo[timestamp][site]:
                try:
                    gridSet.add( srvc['gridsite'] )
                except:
                    gridSet.add( "" )
            if "" in gridSet:
                gridSet.remove( "" )
                gridList = sorted( gridSet )
                gridList.append( "" )
            else:
                gridList = sorted( gridSet )
            del gridSet
            #
            tier = site[1:2]
            if tier not in ['0', '1', '2', '3']:
                tier = '9'
            #
            for gridsite in gridList:
                if comma1Flag:
                    jsonString += hdrString
                else:
                    jsonString += hdrString[1:]
                jsonString += ("     \"vo\": \"CMS\",\n" +
                               "     \"update\": \"%s\",\n" +
                               "     \"site\": \"%s\",\n" +
                               "     \"tier\": %s,\n" +
                               "     \"gridsite\": \"%s\",\n" +
                               "     \"services\": [\n") % (updateStr, site,
                               tier, gridsite)
                comma2Flag = False
                for srvc in self.topo[timestamp][site]:
                    try:
                        grid = srvc['gridsite']
                    except:
                        grid = ""
                    if ( grid != gridsite ):
                        continue
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
                    if not srvc['production']:
                        jsonString += ",\n         \"production\": false"
                    jsonString += "\n       }"
                    comma2Flag = True
                jsonString += "\n     ]\n   }\n }"
                comma1Flag = True
        jsonString += "\n]\n"
        #
        return jsonString


    def dump(self, file=sys.stdout):
        """function to dump the contents of a VO-feed object to stdout"""
        #
        for timestamp in sorted(self.topo.keys()):
            if ( timestamp == 0 ):
               file.write("timestamp %d (current):\n" % timestamp)
            else:
               file.write("timestamp %d (%s):\n" % (timestamp,
                   time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime(timestamp))))
            #
            for site in sorted(self.topo[timestamp].keys()):
                file.write("   site %s:\n" % site)
                #
                for service in self.topo[timestamp][site]:
                   try:
                       gridsite = service['gridsite']
                   except KeyError:
                       gridsite = "\"\""
                   file.write("      %s: %s / %s @ %s" % (service['category'],
                            service['hostname'], service['flavour'], gridsite))
                   try:
                       file.write(" %s" % service['endpoint'])
                   except KeyError:
                       pass
                   for key in service:
                       if key in ['category', 'hostname', 'flavour',
                                                       'gridsite', 'endpoint']:
                           continue
                       file.write(" %1.1s=%s" % (str(key), str(service[key])))
                   file.write("\n") 
        file.write("\n") 
        return


    def __del__(self):
        inventory = list( self.topo.keys() )
        for timestamp in inventory:
            self.delete(timestamp)
        del self.topo
        #
        return
# ########################################################################### #



if __name__ == '__main__':
    #
    import argparse
    import getpass
    import socket
    import shutil
    import http.client
    from OpenSSL import crypto
    import ssl
    import htcondor

    #VOFD_CACHE_DIR = "./cache"
    VOFD_CACHE_DIR = "/data/cmssst/MonitoringScripts/vofeed/cache"

    #VOFD_CERTIFICATE_CRT = "/afs/cern.ch/user/l/lammel/.globus/usercert.pem"
    #VOFD_CERTIFICATE_KEY = "/afs/cern.ch/user/l/lammel/.globus/userkey.pem"
    VOFD_CERTIFICATE_CRT = "/tmp/x509up_u79522"
    VOFD_CERTIFICATE_KEY = "/tmp/x509up_u79522"
    # ####################################################################### #



    class HTTPSClientAuthHandler(urllib.request.HTTPSHandler):
        """Urllib.request.HTTPSHandler class with certificate access"""

        def __init__(self):
            urllib.request.HTTPSHandler.__init__(self)

        def https_open(self, req):
            return self.do_open(self.getConnection, req)

        def getConnection(self, host, timeout=90):
            return http.client.HTTPSConnection(host,
                                               key_file=VOFD_CERTIFICATE_KEY,
                                               cert_file=VOFD_CERTIFICATE_CRT)



    class HTTPSNoCertCheckHandler(urllib.request.HTTPSHandler):
        """Urllib.request.HTTPSHandler class with no certificate check"""

        def __init__(self):
            sslContext = ssl._create_unverified_context()
            urllib.request.HTTPSHandler.__init__(self, context=sslContext)
    # ####################################################################### #



    def vofd_sites_email():
        # ###################################################### #
        # return dictionary with valid CMS sites: sysadmin-email #
        # ###################################################### #
        URL_CRIC_SITES = "https://cms-cric.cern.ch/api/cms/site/query/?json"
 
        logging.info("Fetching CMS site information from CRIC")
        try:
            with urllib.request.urlopen(URL_CRIC_SITES) as urlHandle:
                urlCharset = urlHandle.headers.get_content_charset()
                if urlCharset is None:
                    urlCharset = "utf-8"
                myData = urlHandle.read().decode( urlCharset )
            #
            # sanity check:
            if ( len(myData) < 65536 ):
                raise IOError("CRIC-sites data failed sanity check")
            #
            # update cache:
            try:
                myFile = open("%s/CRICsites.json_new" % VOFD_CACHE_DIR, 'w')
                try:
                    myFile.write(myData)
                    renameFlag = True
                except:
                    renameFlag = False
                finally:
                    myFile.close()
                    del myFile
                if renameFlag:
                    os.rename("%s/CRICsites.json_new" % VOFD_CACHE_DIR,
                              "%s/CRICsites.json" % VOFD_CACHE_DIR)
                    logging.info("   cache of CMS site information updated")
                del renameFlag
            except:
                pass
        except:
            logging.error("Failed to fetch CMS site information from CRIC")
            try:
                with open("%s/CRICsites.json" % VOFD_CACHE_DIR, 'r') as myFile:
                    myData = myFile.read()
                    logging.warning("Using cached CMS site information")
            except:
                logging.critical("Failed to read cached CMS site information")
                raise

        # decode JSON:
        siteDict = json.loads( myData )
        del myData

        # loop over entries and add site with facility-admin email list
        siteRegex = re.compile(r"T\d_[A-Z]{2,2}_\w+")
        facilityRegex = re.compile(r"[A-Z]{2,2}_\w+")
        emailDict = {}
        for entry in siteDict:
            site = siteDict[entry]['name']
            if ( siteRegex.match( site ) is None ):
                continue
            try:
                facility = siteDict[entry]['facility'].split(" ")[0]
                if ( facilityRegex.match( facility ) is not None ):
                    email = "cms-" + facility + "-admin@cern.ch"
                else:
                    email = None
            except KeyError:
                email = None
            emailDict[site] = email
        #
        return emailDict



    def vofd_hosts_gridsite():
        # ############################################################### #
        # return dictionary with (hostname,category) tuple: gridsite name #
        # ############################################################### #
        URL_OSG_RGSUM = "https://my.opensciencegrid.org/rgsummary/xml"

        logging.info("Fetching resource summary information from OSG")
        try:
            with urllib.request.urlopen(URL_OSG_RGSUM) as urlHandle:
                urlCharset = urlHandle.headers.get_content_charset()
                if urlCharset is None:
                    urlCharset = "utf-8"
                myData = urlHandle.read().decode( urlCharset )
                del urlCharset
            #
            # sanity check:
            if ( len(myData) < 65536 ):
                raise IOError("OSG-rgsummary data failed sanity check")
            #
            # update cache:
            try:
                myFile = open("%s/OSGrgsum.xml_new" % VOFD_CACHE_DIR, 'w')
                try:
                    myFile.write(myData)
                    renameFlag = True
                except:
                    renameFlag = False
                finally:
                    myFile.close()
                    del myFile
                if renameFlag:
                    os.rename("%s/OSGrgsum.xml_new" % VOFD_CACHE_DIR,
                              "%s/OSGrgsum.xml" % VOFD_CACHE_DIR)
                    logging.info("   cache of OSG-rgsummary data updated")
                del renameFlag
            except:
                pass
        except:
            logging.error("Failed to fetch OSG-rgsummary data")
            try:
                with open("%s/OSGrgsum.xml" % VOFD_CACHE_DIR, 'r') as myFile:
                    myData = myFile.read()
                    logging.warning("Using cached OSG-rgsummary data")
            except:
                logging.critical("Failed to read cached OSG-rgsummary data")
                raise

        # decode XML:
        rgsum = xml.etree.ElementTree.fromstring( myData )
        del myData

        hostDict = {}

        # loop over resource group elements:
        for rgroup in rgsum.findall('ResourceGroup'):
            gridsite = rgroup.find('GroupName').text
            resources = rgroup.find('Resources')
            for resource in resources.findall('Resource'):
                host = resource.find('FQDN').text.lower()
                services = resource.find('Services')
                for service in services.findall('Service'):
                    service_type = service.find('Name').text
                    category = vofeed.type2category( service_type )
                    if ( category == "" ):
                        continue
                    tuple = (host, category)
                    if tuple in hostDict:
                        if ( hostDict[tuple] != gridsite ):
                            if ( len( hostDict[tuple] ) <= len( gridsite ) ):
                                logging.warning(("Host %s (%s) belongs to mu" +
                                                 "tiple sites, keeping %s, i" +
                                                 "gnoring %s") % (host,
                                          category, hostDict[tuple], gridsite))
                            else:
                                logging.warning(("Host %s (%s) belongs to mu" +
                                                 "tiple sites, prefering %s," +
                                                 " ignoring %s") % (host,
                                          category, gridsite, hostDict[tuple]))
                                hostDict[tuple] = gridsite
                    else:
                        hostDict[tuple] = gridsite


        # ########################################################### #
        URL_EGI_ENDPNT = "https://goc.egi.eu/gocdbpi/public/?method=get_service_endpoint&scope="

        logging.info("Fetching service endpoint list from EGI")
        try:
            urlRequest = urllib.request.Request(URL_EGI_ENDPNT)
            urlOpener = urllib.request.build_opener( HTTPSNoCertCheckHandler() )
            with urlOpener.open ( urlRequest ) as urlHandle:
                urlCharset = urlHandle.headers.get_content_charset()
                if urlCharset is None:
                    urlCharset = "utf-8"
                myData = urlHandle.read().decode( urlCharset )
                del urlCharset
            #
            # sanity check:
            if ( len(myData) < 65536 ):
                raise IOError("EGI-endpoint data failed sanity check")
            #
            # update cache:
            try:
                myFile = open("%s/EGIendpnt.xml_new" % VOFD_CACHE_DIR, 'w')
                try:
                    myFile.write(myData)
                    renameFlag = True
                except:
                    renameFlag = False
                finally:
                    myFile.close()
                    del myFile
                if renameFlag:
                    os.rename("%s/EGIendpnt.xml_new" % VOFD_CACHE_DIR,
                              "%s/EGIendpnt.xml" % VOFD_CACHE_DIR)
                    logging.info("   cache of EGI-endpoint data updated")
                del renameFlag
            except:
                pass
        except:
            logging.error("Failed to fetch EGI-endpoint data")
            try:
                with open("%s/EGIendpnt.xml" % VOFD_CACHE_DIR, 'r') as myFile:
                    myData = myFile.read()
                    logging.warning("Using cached EGI-endpoint data")
            except:
                logging.critical("Failed to read cached EGI-endpoint data")
                raise

        # decode XML:
        endpoints = xml.etree.ElementTree.fromstring( myData )
        del myData

        # loop over service endpoint elements:
        for endpoint in endpoints.findall('SERVICE_ENDPOINT'):
            service_type = endpoint.find('SERVICE_TYPE').text
            category = vofeed.type2category( service_type )
            if ( category == "" ):
                continue
            host = endpoint.find('HOSTNAME').text.lower()
            gridsite = endpoint.find('SITENAME').text
            tuple = (host, category)
            if tuple in hostDict:
                if ( hostDict[tuple] != gridsite ):
                    if ( len( hostDict[tuple] ) <= len( gridsite ) ):
                        logging.warning(("Host %s (%s) belongs to mutiple si" +
                                         "tes, keeping %s, ignoring %s") %
                                   (host, category, hostDict[tuple], gridsite))
                    else:
                        logging.warning(("Host %s (%s) belongs to mutiple si" +
                                         "tes, prefering %s, ignoring %s") %
                                   (host, category, gridsite, hostDict[tuple]))
                        hostDict[tuple] = gridsite
            else:
                hostDict[tuple] = gridsite

        return hostDict



    def vofd_glideinWMSfactory(vofeedObj, timestamp, host2grid):
        # ############################################################## #
        # fill vofeedObj with CE information from glide-in WMS factories #
        # ############################################################## #
        DICT_GLIDEIN_FACTORIES = [
            {   'lbl': "UCSD",
                'uri': "gfactory-2.opensciencegrid.org",
                'prd': True
            },
            {   'lbl': "CERN",
                'uri': "vocms0206.cern.ch",
                'prd': True
            },
            {   'lbl': "CERNint",
                'uri': "vocms0204.cern.ch",
                'prd': False
            },
            {   'lbl': "FNAL",
                'uri': "cmssi-factory01.fnal.gov",
                'prd': True
            } ]

        # loop over factories and get list of CEs:
        # ========================================
        for factory in DICT_GLIDEIN_FACTORIES:
            logging.info("Fetching entries from %s factory" % factory['lbl'])
            try:
                collector = htcondor.Collector(factory['uri'])
                classAds = collector.query(htcondor.AdTypes.Any, "(MyType =?= \"glidefactory\") && (GLIDEIN_CMSSite isnt Undefined) && (GLIDEIN_Gatekeeper isnt Undefined) && (GLIDEIN_GridType isnt Undefined) && (GLIDEIN_Supported_VOs isnt Undefined)", ['GLIDEIN_CMSSite', 'GLIDEIN_Gatekeeper', 'GLIDEIN_GridType', 'GLIDEIN_GlobusRSL', 'GLIDEIN_In_Downtime', 'GLIDEIN_Supported_VOs'])
                # catch HT Condor's faulty error handling:
                if not classAds:
                    raise IOError("Empty Collector ClassAd List")
                if ( len(classAds) < 16 ):
                    raise IOError("Collector ClassAd list failed sanity check")
                # convert list of classAd objects into list of dictionaries:
                myData = []
                for classAd in classAds:
                    try:
                        globusRSL = classAd['GLIDEIN_GlobusRSL']
                    except KeyError:
                        globusRSL = ""
                    try:
                        inDowntime = classAd['GLIDEIN_In_Downtime']
                    except KeyError:
                        inDowntime = "False"
                    myData.append( {
                        'GLIDEIN_GridType': classAd['GLIDEIN_GridType'],
                        'GLIDEIN_Gatekeeper': classAd['GLIDEIN_Gatekeeper'],
                        'GLIDEIN_GlobusRSL': globusRSL,
                        'GLIDEIN_In_Downtime': inDowntime,
                        'GLIDEIN_Supported_VOs': classAd['GLIDEIN_Supported_VOs'],
                        'GLIDEIN_CMSSite': classAd['GLIDEIN_CMSSite']
                        } )
                #
                # update cache:
                try:
                    myFile = open("%s/factory_%s.json_new" %
                        (VOFD_CACHE_DIR, factory['lbl']), 'w')
                    try:
                        json.dump(myData, myFile)
                        renameFlag = True
                    except:
                        renameFlag = False
                    finally:
                        myFile.close()
                        del myFile
                    if renameFlag:
                        os.rename("%s/factory_%s.json_new" %
                                  (VOFD_CACHE_DIR, factory['lbl']),
                                  "%s/factory_%s.json" %
                                  (VOFD_CACHE_DIR, factory['lbl']))
                        logging.info("   cache of %s factory updated" %
                                     factory['lbl'])
                    del renameFlag
                except:
                    pass
            except:
                logging.error("Failed to fetch %s factory data" %
                              factory['lbl'])
                try:
                    with open("%s/factory_%s.json" %
                              (VOFD_CACHE_DIR, factory['lbl']), 'r') as myFile:
                        myData = json.load( myFile )
                        logging.warning("Using cached %s factory data" %
                                        factory['lbl'])
                except:
                    logging.critical("Failed to read cached %s factory data" %
                                     factory['lbl'])
                    raise
            #
            for classAd in myData:
                if ( classAd['GLIDEIN_In_Downtime'] == "True" ):
                    # exclude entries set to indefinite downtime
                    continue
                if 'CMS' not in classAd['GLIDEIN_Supported_VOs']:
                    continue
                #
                gkeeper = classAd['GLIDEIN_Gatekeeper'].split()[-1]
                gkeeper = gkeeper.split("://")[-1]
                host = gkeeper.split(":")[0].lower()
                if classAd['GLIDEIN_GridType'] == 'cream':
                    ceType = "CREAM-CE"
                elif classAd['GLIDEIN_GridType'] == 'nordugrid':
                    ceType = "ARC-CE"
                elif classAd['GLIDEIN_GridType'] == 'condor':
                    ceType = "HTCONDOR-CE"
                elif ( classAd['GLIDEIN_GridType'].find('gt') == 0 ):
                    ceType = "GLOBUS"
                else:
                    ceType = "CE"
                service = { 'category': "CE", 'hostname': host,
                            'flavour': ceType, 'production': factory['prd'] }
                #
                try:
                    service['gridsite'] = host2grid[ (host, "CE") ]
                except KeyError:
                    pass
                endpoint = gkeeper.split("/")[0]
                if ( endpoint != host ):
                    service['endpoint'] = endpoint
                if ( gkeeper.find("/") > 0 ):
                    batch = gkeeper.split("/")[1]
                    if ( batch.find("-") > 0 ):
                        if ( batch.find("-") != batch.rfind("-") ):
                            service['queue'] = batch.split("-")[2]
                        service['batch'] = batch.split("-")[1]
                if 'queue' not in service:
                    globusRSL = classAd['GLIDEIN_GlobusRSL']
                    indx1 = globusRSL.find("(queue=")
                    if ( indx1 >= 0 ):
                        indx1 += 7
                        indx2 = globusRSL.find(")", indx1)
                        service['queue'] = globusRSL[indx1:indx2]
                logging.debug("   site %s: host %s flavour %s" %
                              (classAd['GLIDEIN_CMSSite'], service['hostname'],
                               service['flavour']))
                logging.log(9, "      %s" % str(service))
                #
                try:
                    vofeedObj.add1service(timestamp, classAd['GLIDEIN_CMSSite'],
                                          service)
                except:
                    pass

                # add CERN Tier-2 production factory entries also under Tier-0
                if (( classAd['GLIDEIN_CMSSite'] == "T2_CH_CERN" ) and
                    ( factory['prd'] == True )):
                    try:
                        vofeedObj.add1service(timestamp, "T0_CH_CERN", service)
                    except:
                        pass

        return



    def vofd_phedex(vofeedObj, timestamp, host2grid):
        # #################################################### #
        # fill vofeedObj with SE/SRMv2 information from PhEDEx #
        # #################################################### #
        URL_PHEDEX_LFN2PFN = 'https://cmsweb.cern.ch:8443/phedex/datasvc/json/prod/lfn2pfn?node=T*&lfn=/store/data&lfn=/store/hidata&lfn=/store/mc&lfn=/store/himc&lfn=/store/relval&lfn=/store/hirelval&lfn=/store/user&lfn=/store/group&lfn=/store/results&lfn=/store/unmerged&lfn=/store/temp&lfn=/store/temp/user&lfn=/store/backfill/1&lfn=/store/backfill/2&lfn=/store/generator&lfn=/store/local&protocol=srmv2&custodial=n'

        logging.info("Fetching LFN-to-PFN translations from PhEDEx")
        try:
            urlRequest = urllib.request.Request(URL_PHEDEX_LFN2PFN,
                                             headers={'Accept':'application/json'})
            with urllib.request.urlopen( urlRequest ) as urlHandle:
                urlCharset = urlHandle.headers.get_content_charset()
                if urlCharset is None:
                    urlCharset = "utf-8"
                myData = urlHandle.read().decode( urlCharset )
                del urlCharset
            #
            # sanity check:
            if ( len(myData) < 1024 ):
                raise IOError("PhEDEx-lfn2pfn data failed sanity check")
            #
            # update cache:
            try:
                myFile = open("%s/PhEDEx.json_new" % VOFD_CACHE_DIR, 'w')
                try:
                    myFile.write(myData)
                    renameFlag = True
                except:
                    renameFlag = False
                finally:
                    myFile.close()
                    del myFile
                if renameFlag:
                    os.rename("%s/PhEDEx.json_new" % VOFD_CACHE_DIR,
                        "%s/PhEDEx.json" % VOFD_CACHE_DIR)
                    logging.info("   cache of PhEDEx-lfn2pfn data updated")
                del renameFlag
            except:
                pass
        except:
            logging.error("Failed to fetch PhEDEx-lfn2pfn data")
            try:
                with open("%s/PhEDEx.json" % VOFD_CACHE_DIR, 'r') as myFile:
                    myData = myFile.read()
                    logging.warning("Using cached PhEDEx-lfn2pfn data")
            except:
                logging.critical("Failed to read cached PhEDEx-lfn2pfn data")
                raise

        # unpack JSON:
        phedex = json.loads( myData )
        del myData

        # loop LFN-to-PFN mapping dictionaries:
        for entry in phedex['phedex']['mapping']:
            if (( entry['node'] is None ) or ( entry['pfn'] is None )):
                continue
            #
            phedex_noname = entry['node']
            # remove any "_Disk", "_Buffer", and "_MSS" from site names
            phedex_noname = phedex_noname.replace('_Disk','')
            phedex_noname = phedex_noname.replace('_Buffer','')
            phedex_noname = phedex_noname.replace('_Export','')
            phedex_noname = phedex_noname.replace('_MSS','')
            # KNU site kept T2* PhEDEx nodename when switching to Tier-3
            if ( phedex_noname == "T2_KR_KNU" ):
                phedex_noname = "T3_KR_KNU"
            #
            phedex_pfn = entry['pfn']
            phedex_prot = phedex_pfn.split("://")[0]
            if ( phedex_prot == phedex_pfn ):
                phedex_prot = "srm"
                endpoint = phedex_pfn.split("/")[0].lower()
            else:
                endpoint = phedex_pfn.split("://")[1].split("/")[0].lower()
            host = endpoint.split(":")[0]
            if ( host == "" ):
                continue
            service = { 'category': "SE", 'hostname': host, 'flavour': "SRM" }
            #
            try:
                service['gridsite'] = host2grid[ (host, "SE") ]
            except KeyError:
                pass
            #
            if ( endpoint == host ):
                if ( phedex_prot == "gsiftp" ):
                    service['endpoint'] = host + ":2811"
                elif ( phedex_prot == "gridftp" ):
                    service['endpoint'] = host + ":2812"
            else:
                service['endpoint'] = endpoint
            logging.debug("   site %s: hostname %s flavour %s" %
                          (phedex_noname, host, "SRM"))
            logging.log(9, "      %s" % str(service))
            #
            try:
                vofeedObj.add1service(timestamp, phedex_noname, service)
            except:
                pass

        return



    def vofd_extraCMSendpoints(vofeedObj, timestamp, host2grid):
        # ########################################################### #
        # get xrootd, perfSONAR, and test endpoints missing from CRIC #
        # ########################################################### #
        FILE_CMSSST_ENDPNT = "/afs/cern.ch/user/c/cmssst/www/site_info/site_endpoints.json"
        URL_CMSSST_ENDPNT = "http://cmssst.web.cern.ch/cmssst/site_info/site_endpoints.json"

        # read CMSSST-endpoint file and fallback to URL in case of failure:
        # =================================================================
        logging.info("Fetching endpoint information from CMSSST")
        try:
            with open(FILE_CMSSST_ENDPNT, 'r') as myFile:
                myData = myFile.read()
        except Exception as excptn:
            logging.error("Failed to read CMSSST-endpoint file %s, %s" %
                          (FILE_CMSSST_ENDPNT, str(excptn)))
            #
            try:
                urlRequest = urllib.request.Request(URL_CMSSST_ENDPNT,
                                         headers={'Accept':'application/json'})
                with urllib.request.urlopen( urlRequest ) as urlHandle:
                    urlCharset = urlHandle.headers.get_content_charset()
                    if urlCharset is None:
                        urlCharset = "utf-8"
                    myData = urlHandle.read().decode( urlCharset )
                    del urlCharset
                #
                # sanity check:
                if ( len(myData) < 1024 ):
                    raise IOError("CMSSST-endpoint data failed sanity check")
            except Exception as excptn:
                logging.critical("Failed to fetch CMSSST-endpoint URL %s, %s" %
                             (URL_CMSSST_ENDPNT, str(excptn)))
                raise


        # decode JSON into dictionary structure:
        # ======================================
        endpoints = json.loads( myData )


        # add service endpoints to CMS topology:
        # ======================================
        siteRegex = re.compile(r"T\d_[A-Z]{2,2}_\w+")
        for endpoint in endpoints['data']:
            if (( siteRegex.match( endpoint['site'] ) is None ) or
                ( endpoint['endpoint'].count(".") < 2 )):
                logging.error("Skipping bad endpoint entry, %s, %s (%s)" %
                    (endpoint['site'], endpoint['endpoint'], endpoint['type']))
            else:
                host = endpoint['endpoint'].split(":")[0].lower()
                flavour = vofeed.type2flavour( endpoint['type'] )
                ctgry = vofeed.flavour2category( flavour )
                service = { 'category': ctgry, 'hostname': host,
                            'flavour': flavour }
                try:
                    service['gridsite'] = host2grid[ (host, "SE") ]
                except KeyError:
                    pass
                if ( host != endpoint['endpoint'] ):
                    service['endpoint'] = endpoint['endpoint']
                if ( endpoint['usage'] == "test" ):
                    service['production'] = False
                logging.debug("   site %s: hostname %s flavour %s" %
                              (endpoint['site'], host, "SRM"))
                logging.log(9, "      %s" % str(service))
                #
                try:
                    vofeedObj.add1service(timestamp, endpoint['site'], service)
                except:
                    pass
        #
        return
    # ####################################################################### #



    def write_vofeed_xml(vofeedObj, timestamp, site2email):
        # ############################################################ #
        # write VO-feed XML file with CMS grid resources for SAM3/WLCG #
        # ############################################################ #
        #VOFEED_FILE = "vofeed.xml"
        #VOFEED_COPY = None
        VOFEED_FILE = "/afs/cern.ch/user/c/cmssst/www/vofeed/vofeed.xml"
        VOFEED_COPY = "/eos/home-c/cmssst/www/vofeed/vofeed.xml"

        logging.info("Writing VO-feed XML file(s)")

        # derive VO-feed owner string from certificate:
        cert = crypto.load_certificate(crypto.FILETYPE_PEM,
                                       open(VOFD_CERTIFICATE_CRT, 'r').read() )
        subject = str( cert.get_subject() ).split("'")[1]
        owner = re.sub("['\"<>]", "", subject)
        del subject
        del cert
        xmlString = vofeedObj.convert2XML(timestamp, owner, site2email)
        #
        # sanity check:
        if ( len(xmlString) < 4096 ):
            raise IOError("New VO-feed XML string failed sanity check")

        try:
            with open(VOFEED_FILE + "_new", 'w') as myFile:
                myFile.write( xmlString )
            #
            # move file into place:
            os.rename(VOFEED_FILE + "_new", VOFEED_FILE)
            #
            # place copy as required:
            if VOFEED_COPY is not None:
                shutil.copyfile(VOFEED_FILE, VOFEED_COPY)
        except Exception as excptn:
            logging.critical("Failed to write VO-feed file, %s" % str(excptn))

        return
    # ####################################################################### #



    def write_inuse_metric(vofeedObj, timestamp):
        # ############################################################### #
        # write metric file with grid resources in prod use for SAM3/WLCG #
        # ############################################################### #
        #INUSE_FILE = "in_use.txt"
        #INUSE_COPY = None
        INUSE_FILE = "/afs/cern.ch/user/c/cmssst/www/vofeed/in_use.txt"
        INUSE_COPY = "/eos/home-c/cmssst/www/vofeed/in_use.txt"
        REFERENCE_URL = "http://cmssst.web.cern.ch/cmssst/vofeed/vofeed.xml"

        logging.info("Writing in_use metric file(s)")
        try:
            rsrcList = []
            with open(INUSE_FILE + "_new", 'w') as myFile:
                #
                myFile.write(("#txt\n#\n# Site Support Team, Resources in Pr" +
                              "oduction Use Metric\n#    written at %s by %s" +
                              "\n#    in account %s on node %s\n#    maintai" +
                              "ned by cms-comp-ops-site-support-team@cern.ch" +
                              "\n#    https://twiki.cern.ch/twiki/bin/viewau" +
                              "th/CMS/SiteSupportSiteStatusSiteReadiness\n# " +
                              "=============================================" +
                              "===========================\n#\n") %
                             (time.strftime("%Y-%b-%d %H:%M:%S UTC",
                                            time.gmtime(timestamp)),
                              sys.argv[0], getpass.getuser(), socket.getfqdn()))
                #
                # write out resources in production use:
                for srvc in vofeedObj.services(timestamp, None, None):
                    if not srvc['production']:
                        continue
                    tuple = ( srvc['hostname'], srvc['flavour'] )
                    if tuple in rsrcList:
                        continue
                    myFile.write("%s\t%s %s\tproduction\tgreen\t%s\n" %
                                 (time.strftime("%Y-%m-%d %H:%M:%S",
                                                time.gmtime(timestamp)),
                             srvc['flavour'], srvc['hostname'], REFERENCE_URL))
                    rsrcList.append( tuple )
            #
            # sanity check:
            if ( len(rsrcList) < 64 ):
                raise IOError("New in-use file failed sanity check")
            #
            # move file into place:
            os.rename(INUSE_FILE + "_new", INUSE_FILE)
            #
            # place copy as required:
            if INUSE_COPY is not None:
                shutil.copyfile(INUSE_FILE, INUSE_COPY)
        except Exception as excptn:
            logging.critical("Failed to write in-use file, %s" % str(excptn))

        return
    # ####################################################################### #



    def monit_upload(vofeedObj, timestamp):
        # ################################################################# #
        # upload VO-feed for a time entry as JSON metric documents to MonIT #
        # ################################################################# #
        #MONIT_URL = "http://monit-metrics.cern.ch:10012/"
        MONIT_URL = "http://fail.cern.ch:10012/"
        MONIT_HDR = {'Content-Type': "application/json; charset=UTF-8"}
        #
        logging.info("Composing JSON array and uploading to MonIT")


        # compose JSON array string:
        # ==========================
        jsonString = vofeedObj.convert2JSON(timestamp)
        if ( jsonString == "[\n]\n" ):
            logging.warning("skipping upload of document-devoid JSON string")
            return False

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
        del docs

        if ( successFlag ):
            logging.log(25, "JSON string with %d docs uploaded to MonIT" %
                             ndocs)
        return successFlag
    # ####################################################################### #



    parserObj = argparse.ArgumentParser(description="Script to collect VO-f " +
        "eed information of a 15 minute bin, write the XML file and upload t" +
        "he JSON to MonIT is needed.")
    parserObj.add_argument("-U", dest="upload", default=True,
                                 action="store_false",
                                 help="do not upload to MonIT but print VO-f" +
                                 "eed information")
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


    # get timestamp of 15 min bin:
    # ============================
    timestamp = int( time.time() / 900 ) * 900


    # initialize vofeed object:
    # =========================
    vofd = vofeed()
    #
    # load latest/fetch previous VO-feed information:
    # ===============================================
    vofd.load()
    #
    timeList = vofd.times()
    timePrevious = sorted( timeList )[-1]
    #
    if ( (timestamp + 450) <= timePrevious ):
        raise ValueError("No new VO-feed version possible in this 15 minute " +
                         "time period")
    elif ( timestamp <= timePrevious ):
        timestamp = timePrevious + 1
    logging.log(25, "Assembling VO-feed for %d (%s)" %
                    (timestamp, time.strftime("%Y-%b-%d %H:%M:%S",
                                              time.gmtime(timestamp))))


    # add current time entry:
    # =======================
    vofd.add1time(timestamp)


    # get list of valid CMS sites and sysadmin email list:
    # ====================================================
    emailDict = vofd_sites_email()
    for site in emailDict:
        vofd.add1site(timestamp, site)


    # get host to gridsite association from OSG and EGI:
    # ==================================================
    hostDict = vofd_hosts_gridsite()


    # get CE information from glide-in WMS factories:
    # ===============================================
    vofd_glideinWMSfactory(vofd, timestamp, hostDict)


    # get SE information from PhEDEx:
    # ===============================
    vofd_phedex(vofd, timestamp, hostDict)


    # add extra xrootd/perfSONAR/test endpoints:
    # ==========================================
    vofd_extraCMSendpoints(vofd, timestamp, hostDict)


    # remove sites without services:
    # ==============================
    vofd.trim0service(timestamp)


    # write VO-feed XML file:
    # =======================
    write_vofeed_xml(vofd, timestamp, emailDict)


    # write metric with services in production use:
    # =============================================
    write_inuse_metric(vofd, timestamp)


    # check if new time entry is different from previous one:
    # =======================================================
    if (( not vofd.compare2times(timestamp, timePrevious) ) or
        ( int(timePrevious / 86400) != int(timestamp / 86400) )):
        # and upload metric docs to MonIT if requested:
        if ( argStruct.upload ):
            successFlag = monit_upload(vofd, timestamp)
        else:
            successFlag = False
        # or print:
        if ( not successFlag ):
            print( vofd.convert2JSON(timestamp) )

    #import pdb; pdb.set_trace()
