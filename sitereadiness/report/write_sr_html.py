#!/data/cmssst/packages/bin/python3.7
# ########################################################################### #
# python script to write the Site Readiness HTML report for the past 17 days  #
#                                                                             #
# 2019-Nov-16   v0.001   Stephan Lammel                                       #
# ########################################################################### #



import os, sys
import logging
import time, calendar
import ssl
import http.client
import urllib.request
import gzip
import json
import xml.etree.ElementTree
import re
#
# setup the Java/HDFS/PATH environment for pydoop to work properly:
os.environ["HADOOP_CONF_DIR"] = "/opt/hadoop/conf/etc/analytix/hadoop.analytix"
os.environ["JAVA_HOME"]       = "/etc/alternatives/jre"
os.environ["HADOOP_PREFIX"]   = "/usr/hdp/hadoop"
import pydoop.hdfs
# ########################################################################### #



#SRHR_HTML_DIR = "./junk"
#SRHR_CACHE_DIR = "./cache"
SRHR_HTML_DIR = "/eos/home-c/cmssst/www/sitereadiness"
SRHR_CACHE_DIR = "/data/cmssst/MonitoringScripts/sitereadiness/report/cache"

#SRHR_CERTIFICATE_CRT = '/afs/cern.ch/user/l/lammel/.globus/usercert.pem'
#SRHR_CERTIFICATE_KEY = '/afs/cern.ch/user/l/lammel/.globus/userkey.pem'
SRHR_CERTIFICATE_CRT = '/tmp/x509up_u79522'
SRHR_CERTIFICATE_KEY = '/tmp/x509up_u79522'
# ########################################################################### #



class HTTPSClientCertHandler(urllib.request.HTTPSHandler):
    'urllib.request.HTTPSHandler class with certificate access'

    def __init__(self):
        sslContext = ssl.create_default_context(purpose=ssl.Purpose.CLIENT_AUTH)
        sslContext.load_cert_chain(SRHR_CERTIFICATE_CRT, SRHR_CERTIFICATE_KEY)
        urllib.request.HTTPSHandler.__init__(self, context=sslContext)
# ########################################################################### #



def srhr_vofeed(timestamp):
    # ###################################### #
    # get list of CMS sites from the VO-feed #
    # ###################################### #
    FILE_VOFEED = "/afs/cern.ch/user/c/cmssst/www/vofeed/vofeed.xml"
    URL_VOFEED = "http://dashb-cms-vo-feed.cern.ch/dashboard/request.py/cmssitemapbdii"
    #
    now = int( time.time() )
    #
    first1d = int( timestamp / 86400 )
    last1d  = int( now / 86400 )


    # read VO-feed file and fallback to URL in case of failure:
    # =========================================================
    logging.info("Querying VO-feed for CMS site information")
    try:
        with open(FILE_VOFEED, 'r') as myFile:
            myData = myFile.read()
    except Exception as excptn:
        logging.error("Failed to read VO-feed file, %s" % str(excptn))

        try:
            with urllib.request.urlopen(URL_VOFEED) as urlHndl:
                myCharset = urlHndl.headers.get_content_charset()
                if myCharset is None:
                    myCharset = "utf-8"
                myData = urlHndl.read().decode( myCharset )
                del myCharset
        except Exception as excptn:
            logging.critical("Failed to read VO-feed URL, %s" % str(excptn))
            siteDict = {}
            nbin = last1d - first1d + 1
            for cmssite in [ "T0_CH_CERN", "T1_DE_KIT", "T1_ES_PIC", \
                             "T1_FR_CCIN2P3", "T1_IT_CNAF", "T1_RU_JINR",
                             "T1_UK_RAL", "T1_US_FNAL", "T2_CH_CERN" ]:
                siteDict[ cmssite ] = {}
                for metric in [ "sam1day", "hc1day", "fts1day", "sr1day" ]:
                    siteDict[cmssite][metric] = [ ("unknown",
                                                   "",
                                                   "No inforrmation available")
                                                  for i in range(nbin) ]
                    siteDict[cmssite][metric][nbin-1] = ("none", "", "")
            return siteDict


    # unpack XML data of the VO-feed:
    # ===============================
    vofeed = xml.etree.ElementTree.fromstring( myData )
    del myData


    # loop over site elements and fill CMS sites into global list:
    # ============================================================
    siteDict = {}
    nbin = last1d - first1d + 1
    for atpsite in vofeed.findall('atp_site'):
        samFlag = hcFlag = ftsFlag = False
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
                continue
            if 'flavour' not in service.attrib:
                continue
            flavour = service.attrib['flavour']
            if 'production_status' in service.attrib:
                if ( service.attrib['production_status'].lower() == "false" ):
                    continue
            if flavour in [ "CE", "CREAM-CE", "ARC-CE", "HTCONDOR-CE" ]:
                samFlag = True
                hcFlag = True
            elif ( flavour  == "SRM" ):
                samFlag = True
                ftsFlag = True
        #
        if cmssite not in siteDict:
            siteDict[ cmssite ] = {}
        if (( samFlag ) and ( 'sam1day' not in siteDict[ cmssite ] )):
            siteDict[cmssite][ 'sam1day' ] = [ ("unknown",
                                                "",
                                                "No inforrmation available")
                                               for i in range(nbin) ]
            siteDict[cmssite][ 'sam1day' ][nbin-1] = ("none", "", "")
        if (( hcFlag ) and ( 'hc1day' not in siteDict[ cmssite ] )):
            siteDict[cmssite][ 'hc1day' ] = [ ("unknown",
                                               "",
                                               "No inforrmation available")
                                              for i in range(nbin) ]
            siteDict[cmssite][ 'hc1day' ][nbin-1] = ("none", "", "")
        if (( ftsFlag ) and ( 'fts1day' not in siteDict[ cmssite ] )):
            siteDict[cmssite][ 'fts1day' ] = [ ("unknown",
                                                "",
                                                "No inforrmation available")
                                               for i in range(nbin) ]
            siteDict[cmssite][ 'fts1day' ][nbin-1] = ("none", "", "")


    # sort and sanity check:
    # ======================
    noSites = len( siteDict )
    if ( noSites <= 8 ):
        logging.critical("Too few sites, %d, in VO-feed" % noSites)
        siteDict = {}
        nbin = last1d - first1d + 1
        for cmssite in [ "T0_CH_CERN", "T1_DE_KIT", "T1_ES_PIC", \
                         "T1_FR_CCIN2P3", "T1_IT_CNAF", "T1_RU_JINR",
                         "T1_UK_RAL", "T1_US_FNAL", "T2_CH_CERN" ]:
            siteDict[ cmssite ] = {}
            for metric in [ "sam1day", "hc1day", "fts1day", "sr1day" ]:
                siteDict[cmssite][metric] = [ ("unknown",
                                               "",
                                               "No inforrmation available")
                                              for i in range(nbin) ]
                siteDict[cmssite][metric][nbin-1] = ("none", "", "")
        return siteDict


    logging.info("   CMS site list read from VO-feed, %d entries" % noSites)
    return siteDict



def srhr_ggus(siteDict):
    # ################################# #
    # get list of tickets for CMS sites #
    # ################################# #
    URL_GGUS_TICKET = 'https://ggus.eu/?mode=ticket_search&show_columns_check%5B%5D=CMS_SITE&show_columns_check%5B%5D=DATE_OF_CREATION&ticket_id=&su_hierarchy=0&vo=cms&cms_site=&specattrib=none&status=open&typeofproblem=all&ticket_category=all&date_type=creation+date&tf_radio=1&timeframe=any&orderticketsby=REQUEST_ID&orderhow=desc&search_submit=GO!&writeFormat=XML'

    # get list of all tickets for VO CMS from GGUS:
    # =============================================
    logging.info("Querying GGUS for Ticket information")
    urlOpener = None
    urlHndl = None
    try:
        request = urllib.request.Request(URL_GGUS_TICKET,
                                         headers={'Accept':'application/xml'})
        urlOpener = urllib.request.build_opener( HTTPSClientCertHandler() )
        urlHndl = urlOpener.open( request )
        myCharset = urlHndl.headers.get_content_charset()
        if myCharset is None:
            myCharset = "utf-8"
        myData = urlHndl.read().decode( myCharset )
        del(myCharset)
        #
        # update cache:
        try:
            myFile = open(SRHR_CACHE_DIR + "/cache_ggus.xml_new", 'w')
            try:
                myFile.write(myData)
                renameFlag = True
            except:
                renameFlag = False
            finally:
                myFile.close()
                del myFile
            if renameFlag:
                os.rename(SRHR_CACHE_DIR + "/cache_ggus.xml_new",
                          SRHR_CACHE_DIR + "/cache_ggus.xml")
                logging.info("   cache of GGUS updated")
            del renameFlag
        except:
            pass
    except:
        logging.warning("   failed to fetch GGUS ticket data")
        try:
            myFile = open(SRHR_CACHE_DIR + "/cache_ggus.xml", 'r')
            try:
                myData = myFile.read()
                logging.info("   using cached GGUS ticket data")
            except:
                logging.error("   failed to access cached GGUS ticket data")
                return
            finally:
                myFile.close()
                del myFile
        except:
            logging.error("   no GGUS ticket cache available")
            return
    finally:
        if urlHndl is not None:
            urlHndl.close()
    del urlHndl
    del urlOpener


    # unpack XML data of GGUS:
    # ========================
    tickets = xml.etree.ElementTree.fromstring( myData )
    del myData


    # loop over ticket elements and fill into CMS site dictionary:
    # ============================================================
    for ticket in tickets.findall('ticket'):
        ticketid = ticket.find('Ticket-ID').text
        cmssite = ticket.find('CMS_Site').text
        if not cmssite:
           continue
        created  = ticket.findtext('Creation_Date', '')
        ts = time.strptime(created + ' UTC', "%Y-%m-%d %H:%M:%S %Z")
        bin1d = int( calendar.timegm(ts) / 86400 )
        if cmssite not in siteDict:
            continue
        if 'ggus' not in siteDict[ cmssite ]:
            siteDict[ cmssite ][ 'ggus' ] = []
        siteDict[ cmssite ][ 'ggus' ].append( (ticketid, bin1d) )

    # count and sort tickets:
    # =======================
    noTickets = 0
    for cmssite in siteDict:
        try:
            noTickets += len( siteDict[cmssite]['ggus'] )
        except KeyError:
            pass


    logging.info("   ticket info fetched from GGUS, %d entries" % noTickets)
    return siteDict



def srhr_monit_SAM_HC_FTS_SR(timestamp, siteDict):
    # ############################################################## #
    # get SAM,HC,FTS,SR data from MonIT/HDFS and fill metric vectors #
    # ############################################################## #
    HDFS_PREFIX = "/project/monitoring/archive/cmssst/raw/ssbmetric"
    #
    oneDay = 86400
    now = int( time.time() )
    #
    first1d = int( timestamp / 86400 )
    last1d  = int( now / 86400 )
    #
    firstTIS = first1d * 86400
    limitTIS  = ( last1d * 86400 ) + 86400
    #
    sixDaysAgo = calendar.timegm( time.gmtime(now - (6 * oneDay)) )
    startLclTmpArea = calendar.timegm( time.localtime( sixDaysAgo ) )
    limitLclTmpArea = calendar.timegm( time.localtime( limitTIS ) )


    # prepare HDFS subdirectory list:
    # ===============================
    logging.info("Retrieving SAM,HC,FTS,SR docs from MonIT HDFS")
    #
    dirList = set()
    # fetch SAm, HammerCloud, FTS, and SiteReadiness of the last 17 days:
    for dirDay in range(firstTIS, limitTIS, oneDay):
        dirList.add( time.strftime("/sam1day/%Y/%m/%d", time.gmtime(dirDay)) )
        dirList.add( time.strftime("/hc1day/%Y/%m/%d", time.gmtime(dirDay)) )
        dirList.add( time.strftime("/fts1day/%Y/%m/%d", time.gmtime(dirDay)) )
        dirList.add( time.strftime("/sr1day/%Y/%m/%d", time.gmtime(dirDay)) )
    for dirDay in range(startLclTmpArea, limitLclTmpArea, oneDay):
        dirList.add( time.strftime("/sam1day/%Y/%m/%d.tmp",
                                                         time.gmtime(dirDay)) )
        dirList.add( time.strftime("/hc1day/%Y/%m/%d.tmp",
                                                         time.gmtime(dirDay)) )
        dirList.add( time.strftime("/fts1day/%Y/%m/%d.tmp",
                                                         time.gmtime(dirDay)) )
        dirList.add( time.strftime("/sr1day/%Y/%m/%d.tmp",
                                                         time.gmtime(dirDay)) )
    dirList = sorted( dirList )


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
                          if (( d['kind'] == "file" ) and ( d['size'] != 0 )) ]
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
                        # read documents and add relevant records to list:
                        for myLine in fileObj:
                            myJson = json.loads(myLine.decode('utf-8'))
                            try:
                                metric = myJson['metadata']['path']
                                status = myJson['data']['status']
                                if ( metric == "sam1day" ):
                                    if ( myJson['data']['type'] != "site" ):
                                        continue
                                    site = myJson['data']['name']
                                    if 'reliability' not in myJson['data']:
                                        if ( status == "unknown" ):
                                            label = "?"
                                        else:
                                           label = "n/a"
                                    elif myJson['data']['reliability'] is None:
                                        if ( status == "unknown" ):
                                            label = "?"
                                        else:
                                           label = "n/a"
                                    else:
                                        label = "%d%%" % \
                                      int(100 * myJson['data']['reliability'])
                                elif ( metric == "hc1day" ):
                                    if 'name' not in myJson['data']:
                                        myJson['data']['name'] = myJson['data']['site']
                                    site = myJson['data']['name']
                                    if 'value' not in myJson['data']:
                                        if ( status == "unknown" ):
                                            label = "?"
                                        else:
                                           label = "n/a"
                                    elif myJson['data']['value'] is None:
                                        if ( status == "unknown" ):
                                            label = "?"
                                        else:
                                           label = "n/a"
                                    else:
                                        label = "%d%%" % \
                                             int(100 * myJson['data']['value'])
                                elif ( metric == "fts1day" ):
                                    if ( myJson['data']['type'] != "site" ):
                                        continue
                                    site = myJson['data']['name']
                                    if 'quality' not in myJson['data']:
                                        if ( status == "unknown" ):
                                            label = "?"
                                        else:
                                           label = "n/a"
                                    elif myJson['data']['quality'] is None:
                                        if ( status == "unknown" ):
                                            label = "?"
                                        else:
                                           label = "n/a"
                                    else:
                                        label = "%d%%" % \
                                           int(100 * myJson['data']['quality'])
                                elif ( metric == "sr1day" ):
                                    site = myJson['data']['name']
                                    if 'value' not in myJson['data']:
                                        if ( status == "unknown" ):
                                            label = "?"
                                        else:
                                           label = "n/a"
                                    elif myJson['data']['value'] is None:
                                        if ( status == "unknown" ):
                                            label = "?"
                                        else:
                                           label = "n/a"
                                    else:
                                        label = "%d%%" % \
                                             int(100 * myJson['data']['value'])
                                else:
                                    continue
                                tis = int( myJson['metadata']['timestamp']
                                                                       / 1000 )
                                if (( tis < firstTIS ) or ( tis >= limitTIS )):
                                    continue
                                tbin = int( tis / 86400 )
                                #
                                if 'detail' not in myJson['data']:
                                    detail = ""
                                elif myJson['data']['detail'] is None:
                                    detail = ""
                                else:
                                    detail = myJson['data']['detail']
                                vrsn = myJson['metadata']['kafka_timestamp']
                                #
                                key = (metric, tbin, site)
                                value = (vrsn, status, label, detail)
                                #
                                if key in tmpDict:
                                    if ( vrsn <= tmpDict[key][0] ):
                                        continue
                                tmpDict[key] = value
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
        logging.error("Failed to fetch SAM,HC,FTS,SR docs from MonIT HDFS: %s"
                      % str(excptn))


    nbin = last1d - first1d + 1
    for key in tmpDict:
        metric = key[0]
        tbin = key[1]
        site = key[2]
        ibin = tbin - first1d
        if site not in siteDict:
            continue
        if metric not in siteDict[site]:
            siteDict[site][metric] = [ ("unknown",
                                        "",
                                        "No inforrmation available")
                                       for i in range(nbin) ]
            siteDict[site][metric][nbin-1] = ("none", "", "")
        siteDict[site][metric][ibin] = ( tmpDict[key][1], tmpDict[key][2],
                                         tmpDict[key][3].replace("\n","<BR>") )
    del tmpDict
    #
    return siteDict



def srhr_monit_down_STS(timestamp, siteDict):
    # ################################################################### #
    # get down15min,sts15min data from MonIT/HDFS and fill metric vectors #
    # ################################################################### #
    HDFS_PREFIX = "/project/monitoring/archive/cmssst/raw/ssbmetric"
    #
    oneDay = 86400
    now = int( time.time() )
    #
    first1d = int( timestamp / 86400 )
    last1d  = int( now / 86400 )
    #
    firstTIS = ( first1d - 1 ) * 86400
    limitTIS  = ( last1d * 86400 ) + 86400
    #
    sixDaysAgo = calendar.timegm( time.gmtime(now - (6 * oneDay)) )
    startLclTmpArea = calendar.timegm( time.localtime( sixDaysAgo ) )
    limitLclTmpArea = calendar.timegm( time.localtime( limitTIS ) )


    # prepare HDFS subdirectory list:
    # ===============================
    logging.info("Retrieving down,sts15min docs from MonIT HDFS")
    #
    dirList = set()
    for dirDay in range(firstTIS, limitTIS, oneDay):
        dirList.add( time.strftime("/down15min/%Y/%m/%d",
                                                       time.gmtime( dirDay )) )
    for dirDay in range(startLclTmpArea, limitLclTmpArea, oneDay):
        dirList.add( time.strftime("/down15min/%Y/%m/%d.tmp",
                                                       time.gmtime( dirDay )) )
    #
    for dirDay in range(firstTIS, limitTIS, oneDay):
        dirList.add( time.strftime("/sts15min/%Y/%m/%d",
                                                       time.gmtime( dirDay )) )
    for dirDay in range(startLclTmpArea, limitLclTmpArea, oneDay):
        dirList.add( time.strftime("/sts15min/%Y/%m/%d.tmp",
                                                       time.gmtime( dirDay )) )
    dirList = sorted( dirList )


    downDict = {}
    stsDict = {}
    try:
        with pydoop.hdfs.hdfs() as myHDFS:
            for subDir in dirList:
                logging.debug("   checking HDFS subdirectory %s" % subDir)
                if not myHDFS.exists( HDFS_PREFIX + subDir ):
                    continue
                # get list of files in directory:
                myList = myHDFS.list_directory( HDFS_PREFIX + subDir )
                fileNames = [ d['name'] for d in myList
                          if (( d['kind'] == "file" ) and ( d['size'] != 0 )) ]
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
                        # read documents and add relevant records to list:
                        for myLine in fileObj:
                            myJson = json.loads(myLine.decode('utf-8'))
                            try:
                                tis = int( myJson['metadata']['timestamp']
                                                                       / 1000 )
                                if (( tis < firstTIS ) or ( tis >= limitTIS )):
                                    continue
                                tbin = int( tis / 900 )
                                metric = myJson['metadata']['path']
                                if ( metric == "down15min" ):
                                    if ( myJson['data']['type'] != "site" ):
                                        continue
                                    site = myJson['data']['name']
                                    # convert duration back to integer:
                                    strt = int( myJson['data']['duration'][0] )
                                    end  = int( myJson['data']['duration'][1] )
                                    myJson['data']['duration'] = ( strt, end )
                                    if 'detail' not in myJson['data']:
                                        myJson['data']['detail'] = None
                                    vrsn = myJson['metadata']['kafka_timestamp']
                                    #
                                    mKey = (metric, tbin)
                                    dKey  = (site, strt, end)
                                    value = (vrsn, myJson['data'])
                                    #
                                    if mKey not in downDict:
                                        downDict[mKey] = {}
                                    if dKey in downDict[mKey]:
                                        if ( vrsn <= downDict[mKey][dKey][0] ):
                                            continue
                                    downDict[mKey][dKey] = value
                                elif ( metric == "sts15min" ):
                                    site = myJson['data']['name']
                                    if 'detail' not in myJson['data']:
                                        myJson['data']['detail'] = None
                                    vrsn = myJson['metadata']['kafka_timestamp']
                                    #
                                    mKey = (metric, tbin)
                                    value = (vrsn, myJson['data'])
                                    #
                                    if mKey not in stsDict:
                                        stsDict[mKey] = {}
                                    if site in stsDict[mKey]:
                                        if ( vrsn <= stsDict[mKey][site][0] ):
                                            continue
                                    stsDict[mKey][site] = value
                                else:
                                    continue
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
        logging.error("Failed to fetch down,sts15min docs from MonIT HDFS: %s"
                      % str(excptn))


    nbin = last1d - first1d + 1

    # need first time-bin before midnight of timestamp:
    myList = sorted( downDict.keys(), reverse=True )
    keepFlag = True
    for mKey in myList:
        if ( keepFlag ):
            if ( mKey[1] <= (first1d * 96) ):
                keepFlag = False
            #
            # documents in a metric time-bin are uploaded together but are
            # imported with a couple seconds time jitter, allow 90 seconds
            vrsn_thrshld = 0
            # find highest version number:
            for dKey in downDict[mKey]:
                if ( downDict[mKey][dKey][0] > vrsn_thrshld ):
                    vrsn_thrshld = downDict[mKey][dKey][0]
            vrsn_thrshld -= 90000
            #
            dKeyList = list( downDict[mKey] )
            for dKey in dKeyList:
                # filter out docs not from the last upload (cancelled downtimes)
                if ( downDict[mKey][dKey][0] < vrsn_thrshld ):
                    del downDict[mKey][dKey]
                # filter out downtime overrides via "ok" state:
                elif ( downDict[mKey][dKey][1]['status'] == "ok" ):
                    del downDict[mKey][dKey]
        else:
            del downDict[mKey]
    #
    # fill site dictionary with downtime information:
    end15m = ( last1d * 96 ) + 95
    for mKey in sorted( downDict.keys(), reverse=True ):
        metric = "down1day"
        for dKey in downDict[mKey]:
            site = dKey[0]
            status = downDict[mKey][dKey][1]['status']
            if downDict[mKey][dKey][1]['detail'] is not None:
                detail = downDict[mKey][dKey][1]['detail'].replace("\n","<BR>")
            else:
                detail = ""
            if site not in siteDict:
                continue
            if metric not in siteDict[site]:
                siteDict[site][metric] = [ ("none",
                                            "",
                                            "No inforrmation available")
                                           for i in range(nbin) ]
            start1d = max( int(mKey[1] / 96), int(dKey[1] / 86400) ) - first1d
            end1d = min( int(end15m / 96), int(dKey[2] / 86400) ) - first1d
            for ibin in range(start1d, end1d + 1):
                oldStatus = siteDict[site][metric][ibin][0]
                if ( status == "downtime" ):
                    myTuple = ( status, "D", detail )
                    siteDict[site][metric][ibin] = myTuple
                elif (( status == "partial" ) and ( oldStatus != "downtime" )):
                    myTuple = ( status, "P", detail )
                    siteDict[site][metric][ibin] = myTuple
                elif (( status == "adhoc" ) and ( oldStatus == "none" )):
                    myTuple = ( status, "U", detail )
                    siteDict[site][metric][ibin] = myTuple
        end15m = mKey[1]
    del downDict


    # need first time-bin before midnight of timestamp:
    myList = sorted( stsDict.keys(), reverse=True )
    keepFlag = True
    for mKey in myList:
        if ( keepFlag ):
            if ( mKey[1] <= (first1d * 96) ):
                keepFlag = False
        else:
            del stsDict[mKey]
    #
    # fill status dictionary with Life,Prod,Crab Status information:
    end15m = ( last1d * 96 ) + 95
    b15mDict = {}
    for mKey in sorted( stsDict.keys(), reverse=True ):
        for site in stsDict[mKey]:
            lifeStatus = stsDict[mKey][site][1]['status']
            prodStatus = stsDict[mKey][site][1]['prod_status']
            crabStatus = stsDict[mKey][site][1]['crab_status']
            if stsDict[mKey][site][1]['detail'] is not None:
                detail = stsDict[mKey][site][1]['detail'].replace("\n","<BR>")
            else:
                detail = ""
            if site not in b15mDict:
                b15mDict[site] = [ [ 0, 0, 0, 0, 0, 0, 0, 0 ]
                                   for i in range(nbin) ]
            start1d = int(mKey[1] / 96) - first1d
            end1d = int(end15m / 96) - first1d
            for ibin in range(start1d, end1d + 1):
                s15m = max( (ibin + first1d ) * 96, mKey[1] )
                e15m = min( (ibin + 1 + first1d ) * 96, end15m )
                d15m = e15m - s15m
                if ( lifeStatus == "enabled" ):
                    b15mDict[site][ibin][0] += d15m
                elif ( lifeStatus == "waiting_room" ):
                    b15mDict[site][ibin][1] += d15m
                elif ( lifeStatus == "morgue" ):
                    b15mDict[site][ibin][2] += d15m
                if ( prodStatus == "enabled" ):
                    b15mDict[site][ibin][3] += d15m
                elif (( prodStatus == "drain" ) or ( prodStatus == "test" )):
                    b15mDict[site][ibin][4] += d15m
                elif ( prodStatus == "disabled" ):
                    b15mDict[site][ibin][5] += d15m
                if ( crabStatus == "enabled" ):
                    b15mDict[site][ibin][6] += d15m
                elif ( crabStatus == "disabled" ):
                    b15mDict[site][ibin][7] += d15m
        end15m = mKey[1]
    del stsDict
    #
    for site in b15mDict:
        if site not in siteDict:
            continue
        if 'life1day' not in siteDict[site]:
            siteDict[site]['life1day'] = [ ("none",
                                            "",
                                            "No inforrmation available")
                                           for i in range(nbin) ]
        if 'prod1day' not in siteDict[site]:
            siteDict[site]['prod1day'] = [ ("none",
                                            "",
                                            "No inforrmation available")
                                           for i in range(nbin) ]
        if 'crab1day' not in siteDict[site]:
            siteDict[site]['crab1day'] = [ ("none",
                                            "",
                                            "No inforrmation available")
                                           for i in range(nbin) ]
        for ibin in range(nbin):
            counts = b15mDict[site][ibin]
            mxCnt = max( counts[0], counts[1], counts[2] )
            if ( counts[0] == mxCnt ):
                siteDict[site]['life1day'][ibin] = ("enabled", "", "")
            elif ( counts[1] == mxCnt ):
                siteDict[site]['life1day'][ibin] = ("waiting_room", "WR", "")
            elif ( counts[2] == mxCnt ):
                siteDict[site]['life1day'][ibin] = ("morgue", "M", "")
            mxCnt = max( counts[3], counts[4], counts[5] )
            if ( counts[3] == mxCnt ):
                siteDict[site]['prod1day'][ibin] = ("enabled", "", "")
            elif ( counts[4] == mxCnt ):
                siteDict[site]['prod1day'][ibin] = ("drain", "", "")
            elif ( counts[5] == mxCnt ):
                siteDict[site]['prod1day'][ibin] = ("disabled", "", "")
            mxCnt = max( counts[6], counts[7] )
            if ( counts[6] == mxCnt ):
                siteDict[site]['crab1day'][ibin] = ("enabled", "", "")
            elif ( counts[7] == mxCnt ):
                siteDict[site]['crab1day'][ibin] = ("disabled", "", "")
    del b15mDict
    #
    return siteDict



def srhr_write_html(timestamp, statusDict):
    # ################################################################# #
    # write Site Readiness HTML report with relevant metric information #
    # ################################################################# #
    GGUS_URL = "https://ggus.eu/?mode=ticket_info&ticket_id=%s"
    LOG_URL = "https://cmssst.web.cern.ch/cgi-bin/log/%s/%d/%s/%s/%s"
    # tickets:   0  1  2  3  4  5  6   7   8   9  10  11  12
    dbinSpace = [0, 2, 3, 5, 6, 7, 9, 10, 12, 13, 15, 16, 17]
    #
    now = int( time.time() )
    #
    first1d = int( timestamp / 86400 )
    last1d  = int( now / 86400 )
    total1d = last1d - first1d + 1

    timeStrng = time.strftime("%A", time.gmtime(now))[:2] + ", " + \
                       time.strftime("%Y-%b-%d %H:%M:%S UTC", time.gmtime(now))

    try:
        with open(SRHR_HTML_DIR + "/report.html_new", 'w') as myFile:
            myFile.write(("<!DOCTYPE html>\n<HTML>\n\n<HEAD>\n   <TITLE> CMS" +
                          " Site Readiness Report of %s</TITLE>\n\n") % \
                         timeStrng[:15])
            myFile.write("   <STYLE TYPE=\"text/css\">\n      BODY {\n      " +
                         "   background-color: white;\n      }\n      TD A, " +
                         "TD A:LINK, TD A:VISITED {\n         color: black; " +
                         "text-decoration: none\n      }\n      .tdHea" +
                         "der {\n         line-height: 1.5; padding: 2px;\n " +
                         "        background-color: #6A6A7D; color: white;\n" +
                         "         text-decoration: none;\n         font-siz" +
                         "e: x-large; font-weight: bold;\n         white-spa" +
                         "ce: nowrap; text-align: center;\n      }\n      .t" +
                         "dLabel1 {\n         padding: 1px;\n         color:" +
                         " black; text-decoration: none;\n         font-size" +
                         ": 18px; font-weight: bold;\n         white-space: " +
                         "nowrap; text-align: right;\n      }\n      .tdLabe" +
                         "l2 {\n         padding: 1px;\n         color: blac" +
                         "k; text-decoration: none;\n         font-size: 22p" +
                         "x; font-weight: bold;\n         white-space: nowra" +
                         "p; text-align: right;\n      }\n      .tdCell0 {\n" +
                         "         min-width: 48px; padding: 2px;\n         " +
                         "color: black; text-decoration: none;\n         fon" +
                         "t-size: 16px; font-weight: bold;\n         white-s" +
                         "pace: nowrap; text-align: center;\n      }\n      " +
                         ".tdCell1 {\n         min-width: 48px; padding: 2px" +
                         ";\n         color: black; text-decoration: none;\n" +
                         "         font-size: 14px; font-weight: bold;\n    " +
                         "     white-space: nowrap; text-align: center;\n   " +
                         "   }\n      .tdCell2 {\n         min-width: 48px; " +
                         "padding: 2px;\n         color: black; text-decorat" +
                         "ion: none;\n         font-size: 14px; font-weight:" +
                         " normal;\n         white-space: nowrap; text-align" +
                         ": center;\n      }\n      .tdDate {\n         min-" +
                         "width: 48px; padding: 2px;\n         color: black;" +
                         "\n         font-size: 14px; font-weight: bold;\n  " +
                         "       white-space: nowrap; text-align: center;\n " +
                         "     }\n      .tdLegend {\n         min-width: 42p" +
                         "x;\n         color: black; text-decoration: none;" +
                         "\n         font-size: 14px; font-weight: bold;\n  " +
                         "       white-space: nowrap; text-align: left;\n   " +
                         "   }\n      .toolTip1 {\n         text-decoration:" +
                         " none; position: relative;\n      }\n" +
                         "      .toolTip1 span {\n         display: none;\n " +
                         "        border-radius: 4px;\n         color: black" +
                         "; background: white;\n      }\n      .toolTip1:hov" +
                         "er span {\n         font-weight: bold;\n         w" +
                         "hite-space: normal;\n         display: block;\n   " +
                         "      position: absolute;\n         top: 90%; left" +
                         ": 90%;\n         z-index: 1000;\n         width: a" +
                         "uto; max-width: 480px; min-height: 16px;\n        " +
                         " border: 1px solid black; padding: 4px;\n      }\n" +
                         "      .toolTip2 {\n         text-decoration: none;" +
                         " position: relative;\n      }\n      .toolTip2 spa" +
                         "n {\n         display: none;\n         border-radi" +
                         "us: 4px;\n         color: black; background: white" +
                         ";\n      }\n      .toolTip2:hover span {\n        " +
                         " font-weight: bold;\n         white-space: normal;" +
                         "\n         display: block;\n         position: abs" +
                         "olute;\n         top: 98%; left: 50%;\n         tr" +
                         "ansform: translateX(-50%);\n         z-index: 1000" +
                         ";\n         width: auto; max-width: 480px; min-hei" +
                         "ght: 16px;\n         border: 1px solid black; padd" +
                         "ing: 4px;\n      }\n      .toolTip3 {\n         te" +
                         "xt-decoration: none; position: relative;\n      }" +
                         "\n      .toolTip3 span {\n         display: none;" +
                         "\n         border-radius: 4px;\n         color: bl" +
                         "ack; background: white;\n      }\n      .toolTip3:" +
                         "hover span {\n         font-weight: bold;\n       " +
                         "  white-space: normal;\n         display: block;\n" +
                         "         position: absolute;\n         top: 90%; r" +
                         "ight: 90%;\n         z-index: 1000;\n         widt" +
                         "h: auto; max-width: 480px; min-height: 16px;\n    " +
                         "     border: 1px solid black; padding: 4px;\n     " +
                         " }\n   </STYLE>\n")
            myFile.write(("</HEAD>\n\n<BODY>\n<H1>\n   <CENTER>      CMS Sit" +
                          "e Readiness Report of %s</CENTER>\n   </H1>\n<P>" +
                          "\n&nbsp;\n<P>\n&nbsp;\n<P>\n\n") % timeStrng[:15])
            for site in sorted( statusDict.keys() ):
                logging.debug("    site %s:" % site)
                myFile.write(("<TABLE BORDER=\"0\" CELLPADDING=\"0\" CELLSPA" +
                              "CING=\"1\">\n<TR>\n   <TD>\n   <TD COLSPAN=\"" +
                              "%d\" CLASS=\"tdHeader\"><A NAME=\"%s\">%s</A>" +
                              "\n") % (total1d, site, site))
                #
                # GGUS Tickets:
                if 'ggus' in statusDict[site]:
                    #
                    # sort tickets from old to recent:
                    statusDict[site]['ggus'].sort( key=lambda t: t[1] )
                    #
                    # count tickets belonging to each day-bin:
                    tcktDbin = [ 0 for i in range(total1d) ]
                    for tckt in statusDict[site]['ggus']:
                        dbin = min( max(0, tckt[1] - first1d), total1d - 1)
                        tcktDbin[ dbin ] += 1
                    #
                    logging.debug("      tcktDbin: %s" % str(tcktDbin))
                    # assign day-bins to TD blocks:
                    blckDbin = [ 0 for i in range(total1d) ]
                    emrgnt_blck = 1
                    emrgnt_dbin = 0
                    remain_tckt = len( statusDict[site]['ggus'] )
                    tckt_in_blck = 0
                    dbin_in_blck = 0
                    while ( emrgnt_dbin < total1d ):
                        if ( blckDbin[emrgnt_dbin] != 0 ):
                            # day-bin advanced assigned, skip
                            emrgnt_dbin += 1
                            continue
                        if (( tcktDbin[emrgnt_dbin] == 0 ) and
                            ( tckt_in_blck == 0 )):
                            # day-bin without ticket, keep in block 0 for now
                            emrgnt_dbin += 1
                            continue
                        #
                        # try to center a single day-bin with tickets
                        if ( tckt_in_blck == 0 ):
                            # try to steal previous day-bin
                            if (( emrgnt_dbin >= 1 ) and
                                ( blckDbin[emrgnt_dbin - 1] == 0 )):
                                blckDbin[emrgnt_dbin - 1] = emrgnt_blck
                                dbin_in_blck += 1
                                if (( emrgnt_dbin >= 2 ) and
                                    ( blckDbin[emrgnt_dbin - 2] == 0 ) and
                                    ( tcktDbin[emrgnt_dbin] >= 3 )):
                                    blckDbin[emrgnt_dbin - 2] = emrgnt_blck
                                    dbin_in_blck += 1
                            # try to take next day-bins
                            if (( emrgnt_dbin < total1d - 1 ) and
                                ( tcktDbin[emrgnt_dbin + 1] == 0 ) and
                                ( dbinSpace[
                                  min(remain_tckt - tcktDbin[emrgnt_dbin],12) ]
                                               <= total1d - emrgnt_dbin - 2 )):
                                blckDbin[emrgnt_dbin + 1] = emrgnt_blck
                                dbin_in_blck += 1
                                if (( emrgnt_dbin < total1d - 2 ) and
                                    ( tcktDbin[emrgnt_dbin] >= 3 ) and
                                    ( tcktDbin[emrgnt_dbin + 2] == 0 ) and
                                    ( dbinSpace[
                                  min(remain_tckt - tcktDbin[emrgnt_dbin],12) ]
                                               <= total1d - emrgnt_dbin - 3 )):
                                    blckDbin[emrgnt_dbin + 2] = emrgnt_blck
                                    dbin_in_blck += 1
                        #
                        # tag day-bin as block
                        blckDbin[emrgnt_dbin] = emrgnt_blck
                        dbin_in_blck += 1
                        tckt_in_blck += tcktDbin[emrgnt_dbin]
                        remain_tckt -= tcktDbin[emrgnt_dbin]
                        #
                        # check on completing/starting new block
                        if (( dbinSpace[min(tckt_in_blck,12)] <= dbin_in_blck )
                        and ( emrgnt_dbin < total1d - 1 ) and
                            ( tcktDbin[emrgnt_dbin + 1] == 0 ) and
                            ( dbinSpace[min(remain_tckt,12)] <
                                                  total1d - emrgnt_dbin - 1 )):
                            emrgnt_blck += 1
                            tckt_in_blck = 0
                            dbin_in_blck = 0
                            if ( remain_tckt == 0 ):
                                break
                        #
                        # advance to next day-bin
                        emrgnt_dbin += 1
                    logging.debug("      blckDbin: %s" % str(blckDbin))
                    #
                    # write table row
                    myFile.write("<TR>\n   <TD CLASS=\"tdLabel1\">GGUS Ticke" +
                                 "ts:\n")
                    i_dbin = 0
                    i_tckt = 0
                    while ( i_dbin < total1d ):
                        blck_id = blckDbin[i_dbin]
                        f_dbin = i_dbin
                        c_span = 1
                        while (( i_dbin < total1d - 1 ) and
                               ( blckDbin[i_dbin + 1] == blck_id )):
                            c_span += 1
                            i_dbin += 1
                        if ( blck_id == 0 ):
                            myFile.write(("   <TD COLSPAN=\"%d\" CLASS=\"tdC" +
                                          "ell0\">\n") % c_span)
                        else:
                            j_tckt = i_tckt + sum( tcktDbin[f_dbin:i_dbin+1] )
                            tckt_strng = ""
                            for tckt in statusDict[site]['ggus'][i_tckt:j_tckt]:
                                tckt_strng += (", <A HREF=\"%s\">%s</A>" %
                                                 (GGUS_URL % tckt[0], tckt[0]))
                            if (( f_dbin == 0 ) and ( tcktDbin[0] != 0 )):
                                myFile.write(("   <TD COLSPAN=\"%d\" CLASS=" +
                                              "\"tdCell0\" STYLE=\"text-alig" +
                                              "n: left\">%s\n") %
                                                      (c_span, tckt_strng[2:]))
                            elif (( i_dbin == total1d - 1 ) and
                                  ( tcktDbin[total1d-1] != 0 )):
                                myFile.write(("   <TD COLSPAN=\"%d\" CLASS=" +
                                              "\"tdCell0\" STYLE=\"text-alig" +
                                              "n: right\">%s\n") %
                                                      (c_span, tckt_strng[2:]))
                            else:
                                myFile.write(("   <TD COLSPAN=\"%d\" CLASS=" +
                                              "\"tdCell0\">%s\n") %
                                                      (c_span, tckt_strng[2:]))
                            i_tckt = j_tckt
                        #
                        i_dbin += 1
                    myFile.write(("<TR HEIGHT=\"2\">\n   <TD>\n   <TD COLSPA" +
                                  "N=\"%d\" STYLE=\"background-color: black" +
                                  "\">\n") % total1d)
                else:
                    myFile.write(("<TR>\n   <TD CLASS=\"tdLabel1\">GGUS Tick" +
                                  "ets:\n   <TD COLSPAN=\"%d\" CLASS=\"tdCel" +
                                  "l0\">\n<TR HEIGHT=\"2\">\n   <TD>\n   <TD" +
                                  " COLSPAN=\"%d\" STYLE=\"background-color:" +
                                  " black\">\n") % (total1d, total1d))
                #
                # Downtime Information:
                if 'down1day' in statusDict[site]:
                    myFile.write("<TR>\n   <TD CLASS=\"tdLabel1\">Downtimes:" +
                                  "\n")
                    for dbin in range( len( statusDict[site]['down1day'] ) ):
                        entry = statusDict[site]['down1day'][dbin]
                        if ( dbin <= 4 ):
                            ttip_strng = "toolTip1"
                        elif ( dbin > 10 ):
                            ttip_strng = "toolTip3"
                        else:
                            ttip_strng = "toolTip2"
                        strt_15m = ( first1d + dbin ) * 96
                        url_strng = LOG_URL % ("down15min", \
                                               strt_15m, "all", "any", "0+day")
                        if ( entry[0] != "none" ):
                            myFile.write(("   <TD CLASS=\"tdCell1\" STYLE=\"" +
                                          "background-color: #6080FF\"><A CL" +
                                          "ASS=\"%s\" HREF=\"%s\">%s<SPAN>%s" +
                                          "</SPAN></A>\n") % (ttip_strng,
                                                url_strng, entry[1], entry[2]))
                        else:
                            myFile.write("   <TD CLASS=\"tdCell1\">\n")
                else:
                    myFile.write(("<TR>\n   <TD CLASS=\"tdLabel1\">Downtimes" +
                                  ":\n   <TD COLSPAN=\"%d\" CLASS=\"tdCell1" +
                                  "\">\n") % total1d)
                #
                # SAM Status Information:
                if 'sam1day' in statusDict[site]:
                    myFile.write("<TR>\n   <TD CLASS=\"tdLabel1\">SAM Status" +
                                  ":\n")
                    for dbin in range( len( statusDict[site]['sam1day'] ) ):
                        entry = statusDict[site]['sam1day'][dbin]
                        if ( dbin <= 4 ):
                            ttip_strng = "toolTip1"
                        elif ( dbin > 10 ):
                            ttip_strng = "toolTip3"
                        else:
                            ttip_strng = "toolTip2"
                        if ( entry[0] == "ok" ):
                            rgb_strng = "#80FF80"
                        elif ( entry[0] == "warning" ):
                            rgb_strng = "#FFFF00"
                        elif ( entry[0] == "error" ):
                            rgb_strng = "#FF0000"
                        elif ( entry[0] == "downtime" ):
                            rgb_strng = "#6080FF"
                        else:
                            rgb_strng = "#F4F4F4"
                        strt_1d = first1d + dbin
                        url_strng = LOG_URL % ("sam1day", strt_1d, site,
                                                                    "*", "0+0")
                        if ( entry[0] != "none" ):
                            myFile.write(("   <TD CLASS=\"tdCell1\" STYLE=\"" +
                                          "background-color: %s\"><A CLASS=" +
                                          "\"%s\" HREF=\"%s\">%s<SPAN>%s</SP" +
                                          "AN></A>\n") % (rgb_strng,
                                    ttip_strng, url_strng, entry[1], entry[2]))
                        else:
                            myFile.write("   <TD CLASS=\"tdCell1\">\n")
                #
                # Hammer Cloud Information:
                if 'hc1day' in statusDict[site]:
                    myFile.write("<TR>\n   <TD CLASS=\"tdLabel1\">Hammer Clo" +
                                  "ud:\n")
                    for dbin in range( len( statusDict[site]['hc1day'] ) ):
                        entry = statusDict[site]['hc1day'][dbin]
                        if ( dbin <= 4 ):
                            ttip_strng = "toolTip1"
                        elif ( dbin > 10 ):
                            ttip_strng = "toolTip3"
                        else:
                            ttip_strng = "toolTip2"
                        if ( entry[0] == "ok" ):
                            rgb_strng = "#80FF80"
                        elif ( entry[0] == "warning" ):
                            rgb_strng = "#FFFF00"
                        elif ( entry[0] == "error" ):
                            rgb_strng = "#FF0000"
                        else:
                            rgb_strng = "#F4F4F4"
                        strt_1d = first1d + dbin
                        url_strng = LOG_URL % ("hc1day", strt_1d, site,
                                                                 "site", "0+0")
                        if (( entry[0] != "none" ) and ( entry[2] != "" )):
                            myFile.write(("   <TD CLASS=\"tdCell1\" STYLE=\"" +
                                          "background-color: %s\"><A CLASS=" +
                                          "\"%s\" HREF=\"%s\">%s<SPAN>%s</SP" +
                                          "AN></A>\n") % (rgb_strng,
                                    ttip_strng, url_strng, entry[1], entry[2]))
                        elif (( entry[0] != "none" ) and ( entry[2] == "" )):
                            myFile.write(("   <TD CLASS=\"tdCell1\" STYLE=\"" +
                                          "background-color: %s\"><A HREF=\"" +
                                          "%s\">%s</A>\n") % (rgb_strng,
                                                          url_strng, entry[1]))
                        else:
                            myFile.write("   <TD CLASS=\"tdCell1\">\n")
                #
                # FTS Status Information:
                if 'fts1day' in statusDict[site]:
                    myFile.write("<TR>\n   <TD CLASS=\"tdLabel1\">FTS Status" +
                                  ":\n")
                    for dbin in range( len( statusDict[site]['fts1day'] ) ):
                        entry = statusDict[site]['fts1day'][dbin]
                        if ( dbin <= 4 ):
                            ttip_strng = "toolTip1"
                        elif ( dbin > 10 ):
                            ttip_strng = "toolTip3"
                        else:
                            ttip_strng = "toolTip2"
                        if ( entry[0] == "ok" ):
                            rgb_strng = "#80FF80"
                        elif ( entry[0] == "warning" ):
                            rgb_strng = "#FFFF00"
                        elif ( entry[0] == "error" ):
                            rgb_strng = "#FF0000"
                        else:
                            rgb_strng = "#F4F4F4"
                        strt_1d = first1d + dbin
                        url_strng = LOG_URL % ("links1day", strt_1d, site,
                                                                    "*", "0+0")
                        if ( entry[0] != "none" ):
                            myFile.write(("   <TD CLASS=\"tdCell1\" STYLE=\"" +
                                          "background-color: %s\"><A CLASS=" +
                                          "\"%s\" HREF=\"%s\">%s<SPAN>%s</SP" +
                                          "AN></A>\n") % (rgb_strng,
                                    ttip_strng, url_strng, entry[1], entry[2]))
                        else:
                            myFile.write("   <TD CLASS=\"tdCell1\">\n")
                #
                # SiteReadiness Information:
                if 'sr1day' in statusDict[site]:
                    myFile.write(("<TR HEIGHT=\"12\">\n   <TD>\n   <TD COLSP" +
                                  "AN=\"%d\" STYLE=\"border-top: 4px solid b" +
                                  "lack; border-bottom: 4px solid black;\">" +
                                  "\n<TR>\n   <TD CLASS=\"tdLabel2\">Site Re" +
                                  "adiness:\n") % total1d)
                    for dbin in range( len( statusDict[site]['sr1day'] ) ):
                        entry = statusDict[site]['sr1day'][dbin]
                        if ( dbin <= 4 ):
                            ttip_strng = "toolTip1"
                        elif ( dbin > 10 ):
                            ttip_strng = "toolTip3"
                        else:
                            ttip_strng = "toolTip2"
                        if ( entry[0] == "ok" ):
                            rgb_strng = "#80FF80"
                        elif ( entry[0] == "warning" ):
                            rgb_strng = "#FFFF00"
                        elif ( entry[0] == "error" ):
                            rgb_strng = "#FF0000"
                        elif ( entry[0] == "downtime" ):
                            rgb_strng = "#6080FF"
                        else:
                            rgb_strng = "#F4F4F4"
                        if ( entry[0] != "none" ):
                            myFile.write(("   <TD CLASS=\"tdCell2\" STYLE=\"" +
                                          "background-color: %s\"><DIV CLASS" +
                                          "=\"%s\">%s<SPAN>%s</SPAN></DIV>\n")
                                         % (rgb_strng, ttip_strng, entry[1],
                                                                     entry[2]))
                        else:
                            myFile.write("   <TD CLASS=\"tdCell2\">\n")
                    myFile.write(("<TR HEIGHT=\"12\">\n   <TD>\n   <TD COLSP" +
                                  "AN=\"%d\" STYLE=\"border-top: 4px solid b" +
                                  "lack; border-bottom: 4px solid black;\">" +
                                  "\n") % total1d)
                else:
                    myFile.write(("<TR HEIGHT=\"12\">\n   <TD>\n   <TD COLSP" +
                                  "AN=\"%d\" STYLE=\"border-top: 4px solid b" +
                                  "lack; border-bottom: 4px solid black;\">" +
                                  "\n<TR>\n   <TD CLASS=\"tdLabel2\">Site Re" +
                                  "adiness:\n   <TD COLSPAN=\"%d\" CLASS=\"t" +
                                  "dCell0\">\n<TR HEIGHT=\"12\">\n   <TD>\n " +
                                  "  <TD COLSPAN=\"%d\" STYLE=\"border-top: " +
                                  "4px solid black; border-bottom: 4px solid" +
                                  " black;\">\n") % (total1d, total1d, total1d))
                #
                # Life Status Information:
                if 'life1day' in statusDict[site]:
                    myFile.write("<TR>\n   <TD CLASS=\"tdLabel1\">Life Statu" +
                                  "s:\n")
                    for dbin in range( len( statusDict[site]['life1day'] ) ):
                        entry = statusDict[site]['life1day'][dbin]
                        if ( dbin <= 4 ):
                            ttip_strng = "toolTip1"
                        elif ( dbin > 10 ):
                            ttip_strng = "toolTip3"
                        else:
                            ttip_strng = "toolTip2"
                        if ( entry[0] == "enabled" ):
                            rgb_strng = "#80FF80"
                        elif ( entry[0] == "waiting_room" ):
                            rgb_strng = "#A000A0"
                        elif ( entry[0] == "morgue" ):
                            rgb_strng = "#663300"
                        else:
                            rgb_strng = "#F4F4F4"
                        if (( entry[0] != "none" ) and ( entry[2] != "" )):
                            myFile.write(("   <TD CLASS=\"tdCell1\" STYLE=\"" +
                                          "background-color: %s\"><DIV CLASS" +
                                          "=\"%s\">%s<SPAN>%s</SPAN></DIV>\n")
                                         % (rgb_strng, ttip_strng,
                                                           entry[1], entry[2]))
                        elif (( entry[0] != "none" ) and ( entry[2] == "" )):
                            myFile.write(("   <TD CLASS=\"tdCell1\" STYLE=\"" +
                                          "background-color: %s\">%s\n") %
                                                         (rgb_strng, entry[1]))
                        else:
                            myFile.write("   <TD CLASS=\"tdCell1\">\n")
                else:
                    myFile.write(("<TR>\n   <TD CLASS=\"tdLabel1\">Life Stat" +
                                  "us:\n   <TD COLSPAN=\"%d\" CLASS=\"tdCell" +
                                  "1\">\n") % total1d)
                #
                # Prod Status Information:
                if 'prod1day' in statusDict[site]:
                    myFile.write("<TR>\n   <TD CLASS=\"tdLabel1\">Prod Statu" +
                                  "s:\n")
                    for dbin in range( len( statusDict[site]['prod1day'] ) ):
                        entry = statusDict[site]['prod1day'][dbin]
                        if ( dbin <= 4 ):
                            ttip_strng = "toolTip1"
                        elif ( dbin > 10 ):
                            ttip_strng = "toolTip3"
                        else:
                            ttip_strng = "toolTip2"
                        if ( entry[0] == "enabled" ):
                            rgb_strng = "#80FF80"
                        elif ( entry[0] == "drain" ):
                            rgb_strng = "#FFFF00"
                        elif ( entry[0] == "disabled" ):
                            rgb_strng = "#FF0000"
                        else:
                            rgb_strng = "#F4F4F4"
                        if (( entry[0] != "none" ) and ( entry[2] != "" )):
                            myFile.write(("   <TD CLASS=\"tdCell1\" STYLE=\"" +
                                          "background-color: %s\"><DIV CLASS" +
                                          "=\"%s\">%s<SPAN>%s</SPAN></DIV>\n")
                                         % (rgb_strng, ttip_strng,
                                                           entry[1], entry[2]))
                        elif (( entry[0] != "none" ) and ( entry[2] == "" )):
                            myFile.write(("   <TD CLASS=\"tdCell1\" STYLE=\"" +
                                          "background-color: %s\">%s\n") %
                                                         (rgb_strng, entry[1]))
                        else:
                            myFile.write("   <TD CLASS=\"tdCell1\">\n")
                else:
                    myFile.write(("<TR>\n   <TD CLASS=\"tdLabel1\">Prod Stat" +
                                  "us:\n   <TD COLSPAN=\"%d\" CLASS=\"tdCell" +
                                  "1\">\n") % total1d)
                #
                # CRAB Status Information:
                if 'crab1day' in statusDict[site]:
                    myFile.write("<TR>\n   <TD CLASS=\"tdLabel1\">CRAB Statu" +
                                  "s:\n")
                    for dbin in range( len( statusDict[site]['crab1day'] ) ):
                        entry = statusDict[site]['crab1day'][dbin]
                        if ( dbin <= 4 ):
                            ttip_strng = "toolTip1"
                        elif ( dbin > 10 ):
                            ttip_strng = "toolTip3"
                        else:
                            ttip_strng = "toolTip2"
                        if ( entry[0] == "enabled" ):
                            rgb_strng = "#80FF80"
                        elif ( entry[0] == "disabled" ):
                            rgb_strng = "#FF0000"
                        else:
                            rgb_strng = "#F4F4F4"
                        if (( entry[0] != "none" ) and ( entry[2] != "" )):
                            myFile.write(("   <TD CLASS=\"tdCell1\" STYLE=\"" +
                                          "background-color: %s\"><DIV CLASS" +
                                          "=\"%s\">%s<SPAN>%s</SPAN></DIV>\n")
                                         % (rgb_strng, ttip_strng,
                                                           entry[1], entry[2]))
                        elif (( entry[0] != "none" ) and ( entry[2] == "" )):
                            myFile.write(("   <TD CLASS=\"tdCell1\" STYLE=\"" +
                                          "background-color: %s\">%s\n") %
                                                         (rgb_strng, entry[1]))
                        else:
                            myFile.write("   <TD CLASS=\"tdCell1\">\n")
                else:
                    myFile.write(("<TR>\n   <TD CLASS=\"tdLabel1\">CRAB Stat" +
                                  "us:\n   <TD COLSPAN=\"%d\" CLASS=\"tdCell" +
                                  "1\">\n") % total1d)
                #
                # Date Information:
                myFile.write(("<TR HEIGHT=\"4\">\n   <TD>\n   <TD COLSPAN=\"" +
                              "%d\" STYLE=\"background-color: black\">\n<TR>" +
                              "\n   <TD CLASS=\"tdLabel1\">\n") % total1d)
                month_frst = time.strftime("%b", time.gmtime(first1d * 86400))
                month_cnt = 0
                for dbin in range(total1d):
                    tis = ( first1d + dbin ) * 86400
                    day_in_month = int( time.strftime("%d", time.gmtime(tis)) )
                    day_in_week = ( int( tis / 86400 ) + 4 ) % 7
                    if (( day_in_week == 0 ) or ( day_in_week == 6 )):
                        myFile.write(("   <TD CLASS=\"tdDate\" STYLE=\"backg" +
                                      "round-color: #D3D3D3\">%d\n") %
                                                                  day_in_month)
                    else:
                        myFile.write("   <TD CLASS=\"tdDate\">%d\n" %
                                                                  day_in_month)
                    #
                    month_strng = time.strftime("%b", time.gmtime(tis))
                    if ( month_strng == month_frst ):
                        month_cnt += 1
                month_last = time.strftime("%b", time.gmtime(last1d * 86400))
                myFile.write("<TR>\n   <TD CLASS=\"tdLabel1\">\n")
                if ( month_frst == month_last ):
                    myFile.write(("   <TD COLSPAN=\"%d\" CLASS=\"tdDate\" ST" +
                                  "YLE=\"border-top: 2px solid black;\">%s\n")
                                 % (total1d, month_frst))
                else:
                    myFile.write(("   <TD COLSPAN=\"%d\" CLASS=\"tdDate\" ST" +
                                  "YLE=\"border-right: 2px solid black; bord" +
                                  "er-top: 2px solid black;\">%s\n   <TD COL" +
                                  "SPAN=\"%d\" CLASS=\"tdDate\" STYLE=\"bord" +
                                  "er-left: 2px solid black; border-top: 2px" +
                                  " solid black;\">%s\n") %
                                 (month_cnt, month_frst,
                                            (total1d - month_cnt), month_last))
                myFile.write(("<TR HEIGHT=\"4\">\n   <TD>\n   <TD COLSPAN=\"" +
                              "%d\" STYLE=\"background-color: black\">\n</TA" +
                              "BLE>\n<BR>\n\n") % total1d)
                #
                # write legend:
                myFile.write(("<TABLE BORDER=\"0\" CELLPADDING=\"1\" CELLSPA" +
                              "CING=\"3\" WIDTH=\"100%%\">\n<TR>\n   <TD CLA" +
                              "SS=\"tdLegend\" STYLE=\"background-color: #80" +
                              "FF80;\">   <TD CLASS=\"tdLegend\"> = ok / ena" +
                              "bled\n   <TD CLASS=\"tdLegend\">&nbsp;\n   <T" +
                              "D CLASS=\"tdLegend\" STYLE=\"background-color" +
                              ": #F4F4F4; text-align: center;\">?\n   <TD CL" +
                              "ASS=\"tdLegend\"> = unknown / not set\n   <TD" +
                              " CLASS=\"tdLegend\">&nbsp;\n   <TD CLASS=\"td" +
                              "Legend\" STYLE=\"background-color: #6080FF; t" +
                              "ext-align: center;\">D\n   <TD CLASS=\"tdLege" +
                              "nd\"> = Scheduled Downtime\n" +
                              "<TR>\n   <TD CLASS=\"tdLegend\" STYLE=\"backg" +
                              "round-color: #FFFF00;\">\n   <TD CLASS=\"tdLe" +
                              "gend\"> = warning / drain, test\n   <TD CLASS" +
                              "=\"tdLegend\">&nbsp;\n   <TD CLASS=\"tdLegend" +
                              "\" STYLE=\"background-color: #A000A0; text-al" +
                              "ign: center;\">WR\n   <TD CLASS=\"tdLegend\">" +
                              " = Waiting Room state\n   <TD CLASS=\"tdLegen" +
                              "d\">&nbsp;\n   <TD CLASS=\"tdLegend\" STYLE=" +
                              "\"background-color: #6080FF; text-align: cent" +
                              "er;\">P\n   <TD CLASS=\"tdLegend\"> = Partial" +
                              " Downtime\n   <TD CLASS=\"tdLegend\">&nbsp;\n" +
                              "   <TD CLASS=\"tdLegend\" STYLE=\"text-align:" +
                              " right;\">information as of\n" +
                              "<TR>\n   <TD CLASS=\"tdLegend\" STYLE=\"backg" +
                              "round-color: #FF0000;\">\n   <TD CLASS=\"tdLe" +
                              "gend\"> = error / disabled\n   <TD CLASS=\"td" +
                              "Legend\">&nbsp;\n   <TD CLASS=\"tdLegend\" ST" +
                              "YLE=\"background-color: #663300; text-align: " +
                              "center;\">M\n   <TD CLASS=\"tdLegend\"> = Mor" +
                              "gue state\n   <TD CLASS=\"tdLegend\">&nbsp;\n" +
                              "   <TD CLASS=\"tdLegend\" STYLE=\"background-" +
                              "color: #6080FF; text-align: center;\">U\n   <" +
                              "TD CLASS=\"tdLegend\"> = Ad Hoc Downtime\n   " +
                              "<TD CLASS=\"tdLegend\">&nbsp;\n   <TD CLASS=" +
                              "\"tdLegend\" STYLE=\"text-align: right;\">%s" +
                              "\n</TABLE>\n<P>\n&nbsp;\n<P>\n&nbsp;\n<P>\n\n" +
                              "\n") % timeStrng[4:])
            #
            # write page trailer:
            myFile.write("\n<HR>\n<TABLE BORDER=\"0\" CELLPADDING=\"2\" CELL" +
                         "SPACING=\"0\" WIDTH=\"100%\">\n<TR>\n   <TD STYLE=" +
                         "\"text-align: right; font-size: smaller; white-spa" +
                         "ce: nowrap;\">\n      <A HREF=\"http://cern.ch/cop" +
                         "yright\">&copy; Copyright author, CMS, Fermilab, a" +
                         "nd others 2019</A>\n</TABLE>\n\n</BODY>\n\n</HTML>\n")
        #
        #
        # report file written, move into place
        os.rename(SRHR_HTML_DIR + "/report.html_new",
                  SRHR_HTML_DIR + "/report.html")
        #
        logging.info("   Site Readiness report written, %s" %
                                                SRHR_HTML_DIR + "/report.html")

    except Exception as excptn:
        logging.error("Failed to write report.html file, %s" % str(excptn))

    return



def srhr_write_summary(timestamp, statusDict):
    # ################################################################## #
    # write Site Readiness HTML summary report with relevant information #
    # ################################################################## #
    #
    now = int( time.time() )
    #
    first1d = int( timestamp / 86400 )
    last1d  = int( now / 86400 )
    total1d = last1d - first1d + 1

    timeStrng = time.strftime("%A", time.gmtime(now))[:2] + ", " + \
                          time.strftime("%Y-%b-%d %H:%M UTC", time.gmtime(now))

    try:
        with open(SRHR_HTML_DIR + "/sum_report.html_new", 'w') as myFile:
            myFile.write(("<!DOCTYPE html>\n<HTML>\n\n<HEAD>\n   <TITLE> CMS" +
                          " Site Readiness Summary Report %s</TITLE>\n\n") % \
                         timeStrng[:15])
            myFile.write("   <STYLE TYPE=\"text/css\">\n      BODY {\n      " +
                         "   background-color: white;\n      }\n      TD A, " +
                         "TD A:LINK, TD A:VISITED {\n         color: black; " +
                         "text-decoration: none\n      }\n" +
                         "      .tdLabel1 {\n         padding: 1px;\n       " +
                         "  color: black; text-decoration: none;\n         f" +
                         "ont-size: 18px; font-weight: bold;\n         white" +
                         "-space: nowrap; text-align: right;\n      }\n" +
                         "      .tdCell1 {\n         min-width: 48px; paddin" +
                         "g: 2px;\n         color: black; text-decoration: n" +
                         "one;\n         font-size: 14px; font-weight: bold;" +
                         "\n         white-space: nowrap; text-align: center" +
                         ";\n      }\n" +
                         "      .tdDate {\n         min-width: 48px; padding" +
                         ": 2px;\n         color: black;\n         font-size" +
                         ": 14px; font-weight: bold;\n         white-space: " +
                         "nowrap; text-align: center;\n      }\n" +
                         "      .tdLegend {\n         min-width: 42px;\n    " +
                         "     color: black; text-decoration: none;\n       " +
                         "  font-size: 14px; font-weight: bold;\n         wh" +
                         "ite-space: nowrap; text-align: left;\n      }\n" +
                         "      .toolTip1 {\n         text-decoration: none;" +
                         " position: relative;\n      }\n      .toolTip1 spa" +
                         "n {\n         display: none;\n         border-radi" +
                         "us: 4px;\n         color: black; background: white" +
                         ";\n      }\n      .toolTip1:hover span {\n        " +
                         " white-space: nowrap;\n         display: block;\n " +
                         "        text-align: left;\n         position: abso" +
                         "lute;\n         top: 90%; left: 90%;\n         z-i" +
                         "ndex: 1000;\n         width: auto; min-height: 16p" +
                         "x;\n         border: 1px solid black; padding: 4px" +
                         ";\n      }\n" +
                         "      .toolTip2 {\n         text-decoration: none;" +
                         " position: relative;\n      }\n      .toolTip2 spa" +
                         "n {\n         display: none;\n         border-radi" +
                         "us: 4px;\n         color: black; background: white" +
                         ";\n      }\n      .toolTip2:hover span {\n        " +
                         " white-space: nowrap;\n         display: block;\n " +
                         "        text-align: left;\n         position: abso" +
                         "lute;\n         top: 98%; left: 50%;\n         tra" +
                         "nsform: translateX(-50%);\n         z-index: 1000;" +
                         "\n         width: auto; min-height: 16px;\n       " +
                         "  border: 1px solid black; padding: 4px;\n      }" +
                         "\n" +
                         "      .toolTip3 {\n         text-decoration: none;" +
                         " position: relative;\n      }\n      .toolTip3 spa" +
                         "n {\n         display: none;\n         border-radi" +
                         "us: 4px;\n         color: black; background: white" +
                         ";\n      }\n      .toolTip3:hover span {\n        " +
                         " white-space: nowrap;\n         display: block;\n " +
                         "        text-align: left;\n         position: abso" +
                         "lute;\n         top: 90%; right: 90%;\n         z-" +
                         "index: 1000;\n         width: auto; min-height: 16" +
                         "px;\n         border: 1px solid black; padding: 4p" +
                         "x;\n      }\n   </STYLE>\n")
            myFile.write(("</HEAD>\n\n<BODY>\n<H1>\n   <CENTER>      CMS Sit" +
                          "e Readiness Summary Report %s</CENTER>\n   </H1>" +
                          "\n<P>\n&nbsp;\n<P>\n&nbsp;\n<P>\n\n<TABLE BORDER=" +
                          "\"0\" CELLPADDING=\"0\" CELLSPACING=\"1\">\n") % \
                         timeStrng[:15])
            #
            myFile.write(("<TR HEIGHT=\"4\">\n   <TD>\n   <TD COLSPAN=\"%d\"" +
                          " STYLE=\"background-color: black\">\n") % total1d)
            myTier = "T0_"
            for site in sorted( statusDict.keys() ):
                logging.debug("    site %s:" % site)
                #
                #
                if (( site[:3] != myTier ) and ( myTier == "T0_" )):
                    myFile.write(("<TR HEIGHT=\"4\">\n   <TD>\n   <TD COLSPA" +
                                  "N=\"%d\" STYLE=\"background-color: black" +
                                  "\">\n<TR>\n   <TD>\n") % total1d)
                    myTier = site[:3]
                if ( site[:3] != myTier ):
                    # write a date entry to separate new tier block a bit:
                    myFile.write(("<TR HEIGHT=\"4\">\n   <TD>\n   <TD COLSPA" +
                                  "N=\"%d\" STYLE=\"background-color: black" +
                                  "\">\n<TR>\n   <TD>\n") % total1d)
                    month_frst = time.strftime("%b", time.gmtime(first1d*86400))
                    month_cnt = 0
                    for ibin in range(total1d):
                        tis = ( first1d + ibin ) * 86400
                        day_in_month = int(time.strftime("%d",time.gmtime(tis)))
                        day_in_week = ( int( tis / 86400 ) + 4 ) % 7
                        if (( day_in_week == 0 ) or ( day_in_week == 6 )):
                            myFile.write(("   <TD CLASS=\"tdDate\" STYLE=\"b" +
                                          "ackground-color: #D3D3D3\">%d\n") %
                                                                  day_in_month)
                        else:
                            myFile.write("   <TD CLASS=\"tdDate\">%d\n" %
                                                                  day_in_month)
                        #
                        month_strng = time.strftime("%b", time.gmtime(tis))
                        if ( month_strng == month_frst ):
                            month_cnt += 1
                    month_last = time.strftime("%b", time.gmtime(last1d*86400))
                    if ( month_frst == month_last ):
                        myFile.write(("<TR>\n   <TD>\n   <TD COLSPAN=\"%d\" " +
                                      "CLASS=\"tdDate\" STYLE=\"border-top: " +
                                      "2px solid black;\">%s\n") %
                                                         (total1d, month_frst))
                    else:
                        myFile.write(("<TR>\n   <TD>\n   <TD COLSPAN=\"%d\" " +
                                      "CLASS=\"tdDate\" STYLE=\"border-right" +
                                      ": 2px solid black; border-top: 2px so" +
                                      "lid black;\">%s\n   <TD COLSPAN=\"%d" +
                                      "\" CLASS=\"tdDate\" STYLE=\"border-le" +
                                      "ft: 2px solid black; border-top: 2px " +
                                      "solid black;\">%s\n") % (month_cnt,
                                month_frst, (total1d - month_cnt), month_last))
                    myFile.write(("<TR HEIGHT=\"4\">\n   <TD>\n   <TD COLSPA" +
                                  "N=\"%d\" STYLE=\"background-color: black" +
                                  "\">\n") % total1d)
                    #
                    myTier = site[:3]
                #
                #
                # GGUS Tickets:
                if 'ggus' in statusDict[site]:
                    #
                    if 'ggus1day' not in siteDict[site]:
                        siteDict[site]['ggus1day'] = [ ("none", "0", "")
                                                      for i in range(total1d) ]
                    #
                    # sort tickets from old to recent:
                    statusDict[site]['ggus'].sort( key=lambda t: t[1] )
                    #
                    # assign tickets to day-bins:
                    for tckt in statusDict[site]['ggus']:
                        ibin = min( max(0, tckt[1] - first1d), total1d - 1)
                        shrt = int( siteDict[site]['ggus1day'][ ibin ][1] ) + 1
                        if ( siteDict[site]['ggus1day'][ ibin ][2] == "" ):
                            cmnt = "%s" % tckt[0]
                        else:
                            cmnt = siteDict[site]['ggus1day'][ ibin ][2] + \
                                                               ", %s" % tckt[0]
                        siteDict[site]['ggus1day'][ ibin ] = ("ticket(s)",
                                                             "%d" % shrt, cmnt)
                    #
                    logging.debug("      ggus1day: %s" %
                                               str(siteDict[site]['ggus1day']))
                #
                #
                myFile.write("<TR>\n   <TD CLASS=\"tdLabel1\">%s\n" % site)
                #
                for ibin in range( total1d ):
                    detail = ""
                    #
                    if 'ggus1day' in siteDict[site]:
                        myTuple = siteDict[site]['ggus1day'][ibin]
                        if ( myTuple[0] != "none" ):
                            detail += "GGUS Tickets: %s" % myTuple[2]
                    #
                    if 'down1day' in statusDict[site]:
                        myTuple = siteDict[site]['down1day'][ibin]
                        if ( myTuple[0] != "none" ):
                            if ( detail != "" ):
                                detail += "<BR>"
                            if ( myTuple[0] == "downtime" ):
                                detail += "Scheduled Downtime"
                            elif ( myTuple[0] == "partial" ):
                                detail += "Partial Downtime"
                            elif ( myTuple[0] == "adhoc" ):
                                detail += "Ad Hoc Downtime"
                            else:
                                detail += "Unknown Downtime"
                    #
                    if 'sam1day' in statusDict[site]:
                        myTuple = statusDict[site]['sam1day'][ibin]
                        if ( myTuple[0] != "none" ):
                            if ( detail != "" ):
                                detail += "<BR>"
                            if ( myTuple[0] == "ok" ):
                                detail += "SAM: ok, %s" % myTuple[1]
                            elif ( myTuple[0] == "warning" ):
                                detail += "SAM: warning, %s" % myTuple[1]
                            elif ( myTuple[0] == "error" ):
                                detail += "SAM: error, %s" % myTuple[1]
                            elif ( myTuple[0] == "downtime" ):
                                detail += "SAM: downtime, %s" % myTuple[1]
                            else:
                                detail += "SAM: unknown"
                    #
                    if 'hc1day' in statusDict[site]:
                        myTuple = statusDict[site]['hc1day'][ibin]
                        if ( myTuple[0] != "none" ):
                            if ( detail != "" ):
                                detail += "<BR>"
                            if ( myTuple[0] == "ok" ):
                                detail += "HC: ok, %s" % myTuple[1]
                            elif ( myTuple[0] == "warning" ):
                                detail += "HC: warning, %s" % myTuple[1]
                            elif ( myTuple[0] == "error" ):
                                detail += "HC: error, %s" % myTuple[1]
                            else:
                                detail += "HC: unknown"
                    if 'fts1day' in statusDict[site]:
                        myTuple = statusDict[site]['fts1day'][ibin]
                        if ( myTuple[0] != "none" ):
                            if ( detail != "" ):
                                detail += "<BR>"
                            if ( myTuple[0] == "ok" ):
                                detail += "FTS: ok, %s" % myTuple[1]
                            elif ( myTuple[0] == "warning" ):
                                detail += "FTS: warning, %s" % myTuple[1]
                            elif ( myTuple[0] == "error" ):
                                detail += "FTS: error, %s" % myTuple[1]
                            else:
                                detail += "FTS: unknown"
                    label = ""
                    if 'life1day' in statusDict[site]:
                        label = statusDict[site]['life1day'][ibin][1]
                    if ( label == "" ):
                        label = "&nbsp"
                    #
                    if ( ibin <= 4 ):
                        ttip_strng = "toolTip1"
                    elif ( ibin > 10 ):
                        ttip_strng = "toolTip3"
                    else:
                        ttip_strng = "toolTip2"
                    #
                    if 'sr1day' in statusDict[site]:
                        myTuple = statusDict[site]['sr1day'][ibin]
                        if ( myTuple[0] == "ok" ):
                            rgb_strng = "#80FF80"
                        elif ( myTuple[0] == "warning" ):
                            rgb_strng = "#FFFF00"
                        elif ( myTuple[0] == "error" ):
                            rgb_strng = "#FF0000"
                        elif ( myTuple[0] == "downtime" ):
                            rgb_strng = "#6080FF"
                        else:
                            rgb_strng = "#F4F4F4"
                        if ( myTuple[0] != "none" ):
                            myFile.write(("   <TD CLASS=\"tdCell1\" STYLE=\"" +
                                          "background-color: %s\"><DIV CLASS" +
                                          "=\"%s\">%s<SPAN>%s</SPAN></DIV>\n")
                                         % (rgb_strng, ttip_strng, label,
                                                                       detail))
                        else:
                            myFile.write(("   <TD CLASS=\"tdCell1\"><DIV CLA" +
                                          "SS=\"%s\">%s<SPAN>%s</SPAN></DIV>" +
                                          "\n") % (ttip_strng, label, detail))
                    else:
                        myFile.write(("   <TD CLASS=\"tdCell1\"><DIV CLASS=" +
                                      "\"%s\">%s<SPAN>%s</SPAN></DIV>\n") %
                                     (ttip_strng, label, detail))
            #
            # Date Information:
            myFile.write(("<TR HEIGHT=\"4\">\n   <TD>\n   <TD COLSPAN=\"%d\"" +
                          " STYLE=\"background-color: black\">\n<TR>\n   <TD" +
                          " CLASS=\"tdLabel1\">\n") % total1d)
            month_frst = time.strftime("%b", time.gmtime(first1d * 86400))
            month_cnt = 0
            for ibin in range(total1d):
                tis = ( first1d + ibin ) * 86400
                day_in_month = int( time.strftime("%d", time.gmtime(tis)) )
                day_in_week = ( int( tis / 86400 ) + 4 ) % 7
                if (( day_in_week == 0 ) or ( day_in_week == 6 )):
                    myFile.write(("   <TD CLASS=\"tdDate\" STYLE=\"backgroun" +
                                  "d-color: #D3D3D3\">%d\n") % day_in_month)
                else:
                    myFile.write("   <TD CLASS=\"tdDate\">%d\n" % day_in_month)
                #
                month_strng = time.strftime("%b", time.gmtime(tis))
                if ( month_strng == month_frst ):
                    month_cnt += 1
            month_last = time.strftime("%b", time.gmtime(last1d * 86400))
            myFile.write("<TR>\n   <TD CLASS=\"tdLabel1\">\n")
            if ( month_frst == month_last ):
                myFile.write(("   <TD COLSPAN=\"%d\" CLASS=\"tdDate\" STYLE=" +
                              "\"border-top: 2px solid black;\">%s\n") %
                                                         (total1d, month_frst))
            else:
                myFile.write(("   <TD COLSPAN=\"%d\" CLASS=\"tdDate\" STYLE=" +
                              "\"border-right: 2px solid black; border-top: " +
                              "2px solid black;\">%s\n   <TD COLSPAN=\"%d\" " +
                              "CLASS=\"tdDate\" STYLE=\"border-left: 2px sol" +
                              "id black; border-top: 2px solid black;\">%s\n")
                  % (month_cnt, month_frst, (total1d - month_cnt), month_last))
            myFile.write(("<TR HEIGHT=\"4\">\n   <TD>\n   <TD COLSPAN=\"%d\"" +
                          " STYLE=\"background-color: black\">\n</TABLE>\n<B" +
                          "R>\n\n") % total1d)
            #
            # write legend:
            myFile.write("<SPAN STYLE=\"font-size: 16px; font-weight: bold;" +
                         "\">Page shows Site Readiness of sites for the past" +
                         " 16 days (colour) and LifeStatus is not enabled (t" +
                         "ext).</SPAN>\n<BR>\n")
            myFile.write(("<TABLE BORDER=\"0\" CELLPADDING=\"1\" CELLSPACING" +
                          "=\"3\" WIDTH=\"100%%\">\n<TR>\n   <TD CLASS=\"tdL" +
                          "egend\" STYLE=\"background-color: #80FF80;\">   <" +
                          "TD CLASS=\"tdLegend\"> = ok\n   <TD CLASS=\"tdLeg" +
                          "end\">&nbsp;\n   <TD CLASS=\"tdLegend\" STYLE=\"b" +
                          "ackground-color: #FFFF00;\">\n   <TD CLASS=\"tdLe" +
                          "gend\"> = warning\n   <TD CLASS=\"tdLegend\">&nbs" +
                          "p;\n   <TD CLASS=\"tdLegend\" STYLE=\"text-align:" +
                          " center;\">WR\n   <TD CLASS=\"tdLegend\"> = Waiti" +
                          "ng Room\n   <TD CLASS=\"tdLegend\">&nbsp;\n   <TD" +
                          " CLASS=\"tdLegend\" STYLE=\"background-color: #F4" +
                          "F4F4;\">\n   <TD CLASS=\"tdLegend\"> = unknown / " +
                          "not set\n   <TD CLASS=\"tdLegend\">&nbsp;\n   <TD" +
                          " CLASS=\"tdLegend\" STYLE=\"text-align: right;\">" +
                          "information as of\n" +
                          "<TR>\n   <TD CLASS=\"tdLegend\" STYLE=\"backgroun" +
                          "d-color: #FF0000;\">\n   <TD CLASS=\"tdLegend\"> " +
                          "= error\n   <TD CLASS=\"tdLegend\">&nbsp;\n   <TD" +
                          " CLASS=\"tdLegend\" STYLE=\"background-color: #60" +
                          "80FF;\">\n   <TD CLASS=\"tdLegend\"> = downtime\n" +
                          "   <TD CLASS=\"tdLegend\">&nbsp;\n   <TD CLASS=" +
                          "\"tdLegend\" STYLE=\"text-align: center;\">M\n   " +
                          "<TD CLASS=\"tdLegend\"> = Morgue state\n   <TD CL" +
                          "ASS=\"tdLegend\">&nbsp;\n   <TD CLASS=\"tdLegend\"" +
                          ">\n   <TD CLASS=\"tdLegend\">" +
                          "\n   <TD CLASS=\"tdLegend\">&nbsp;\n   <TD CLASS=" +
                          "\"tdLegend\" STYLE=\"text-align: right;\">%s\n</T" +
                          "ABLE>\n<P>\n&nbsp;\n<P>\n&nbsp;\n<P>\n\n\n") %
                                                                 timeStrng[4:])
            #
            # write page trailer:
            myFile.write("\n<HR>\n<TABLE BORDER=\"0\" CELLPADDING=\"2\" CELL" +
                         "SPACING=\"0\" WIDTH=\"100%\">\n<TR>\n   <TD STYLE=" +
                         "\"text-align: right; font-size: smaller; white-spa" +
                         "ce: nowrap;\">\n      <A HREF=\"http://cern.ch/cop" +
                         "yright\">&copy; Copyright author, CMS, Fermilab, a" +
                         "nd others 2019</A>\n</TABLE>\n\n</BODY>\n\n</HTML>\n")
        #
        #
        # report file written, move into place
        os.rename(SRHR_HTML_DIR + "/sum_report.html_new",
                  SRHR_HTML_DIR + "/sum_report.html")
        #
        logging.info("   Site Readiness summary report written, %s" %
                                            SRHR_HTML_DIR + "/sum_report.html")

    except Exception as excptn:
        logging.error("Failed to write sum_report.html file, %s" % str(excptn))

    return
# ########################################################################### #



if __name__ == '__main__':

    # configure the message logger:
    # =============================
    logging.basicConfig(datefmt="%Y-%b-%d %H:%M:%S",
                        format="%(asctime)s [%(levelname).1s] %(message)s",
                        level=logging.INFO)


    # include today and previous 16 days (two weeks plus weekends):
    # =============================================================
    timestamp = ( int( time.time() / 86400 ) - 16 ) * 86400

    siteDict = srhr_vofeed( timestamp )
    srhr_ggus( siteDict )

    srhr_monit_SAM_HC_FTS_SR( timestamp, siteDict )
    srhr_monit_down_STS( timestamp, siteDict )

    srhr_write_html( timestamp, siteDict )

    srhr_write_summary( timestamp, siteDict )

    #import pdb; pdb.set_trace()
