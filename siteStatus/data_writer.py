#!/data/cmssst/packages/bin/python3.7
# ########################################################################### #
# python script to write the data summary JSON for the site status web pages. #
#                                                                             #
# 2016-Aug-09   v0.001   Stephan Lammel                                       #
# ########################################################################### #



import os, sys
import logging
import threading
import time, calendar
import ssl
import http.client
import urllib.request
import gzip
import json
import xml.etree.ElementTree as ET
import re
#
# setup the Java/HDFS/PATH environment for pydoop to work properly:
os.environ["HADOOP_CONF_DIR"] = "/opt/hadoop/conf/etc/analytix/hadoop.analytix"
os.environ["JAVA_HOME"]       = "/etc/alternatives/jre"
os.environ["HADOOP_PREFIX"]   = "/usr/hdp/hadoop"
import pydoop.hdfs
# ########################################################################### #



#SSWP_DATA_DIR = "./data"
#SSWP_CACHE_DIR = "./cache"
SSWP_DATA_DIR = "/eos/home-c/cmssst/www/siteStatus/data"
SSWP_CACHE_DIR = "/data/cmssst/MonitoringScripts/siteStatus/cache"

#SSWP_CERTIFICATE_CRT = '/afs/cern.ch/user/l/lammel/.globus/usercert.pem'
#SSWP_CERTIFICATE_KEY = '/afs/cern.ch/user/l/lammel/.globus/userkey.pem'
SSWP_CERTIFICATE_CRT = '/tmp/x509up_u79522'
SSWP_CERTIFICATE_KEY = '/tmp/x509up_u79522'
# ########################################################################### #



sswp_times = {}    # timestamp dictionary, contains the now timestamp and the #
                   #                       start times of the six information #
                   #                       periods (month, pweek, ...)        #
sswp_sites = {}    # site dictionary, contains the site status information of #
                   #                  each site {ggus, month, pweek,          #
                   #                             yesterday, today, fweek}     #
sswp_other = {}    # non-data item dictionary, url, msg, alert, ...           #
# ########################################################################### #



class HTTPSClientCertHandler(urllib.request.HTTPSHandler):
    'urllib.request.HTTPSHandler class with certificate access'

    def __init__(self):
        sslContext = ssl.create_default_context(purpose=ssl.Purpose.CLIENT_AUTH)
        sslContext.load_cert_chain(SSWP_CERTIFICATE_CRT, SSWP_CERTIFICATE_KEY)
        urllib.request.HTTPSHandler.__init__(self, context=sslContext)
# ########################################################################### #



class sswpTopology:
    'Site Topology class of the CMSSST site status display'

    @staticmethod
    def TypeGroup(type):
        if ( type in glbFlavours ):
           return glbFlavours[type]
        else:
            return None

    def __init__(self):
        self.map = {}

    def addSite(self, cmssite):
        if cmssite not in self.map:
            self.map[cmssite] = {'elements': []}

    def addElement(self, cmssite, gridsite, host, type, prod=True):
        if ( type not in glbFlavours ):
            return
        host = host.lower()
        #
        if cmssite not in self.map:
            self.map[cmssite] = {'elements': []}
        for element in self.map[cmssite]['elements']:
            if (( element['host'] == host ) and
                ( element['type'] == type )):
                return
        #
        if not isinstance(prod, bool):
            return

        self.map[cmssite]['elements'].append({'site': gridsite,
                                              'host': host,
                                              'type': type,
                                              'prod': prod})

    def sites(self):
        return sorted(self.map.keys())

    def verifyType(self, host, type):
        if ( type not in glbFlavours ):
            return None
        host = host.lower()
        # pass one, exact match:
        for cmssite in self.sites():
            for element in self.map[cmssite]['elements']:
                if ( element['host'] == host ):
                    if ( element['type'] == type ):
                        return element['type']
        # pass two, group match:
        for cmssite in self.sites():
            for element in self.map[cmssite]['elements']:
                if ( element['host'] == host ):
                    if ( glbFlavours[ element['type'] ] == glbFlavours[type] ):
                        return element['type']
        return None

    def countProdCEs(self, cmssite):
        count = 0
        for element in self.map[cmssite]['elements']:
            if ( glbFlavours[ element['type'] ] == "CE" ):
                if ( element['prod'] == True ):
                    count += 1
        return count

    def getElements(self, cmssite):
        eList = []
        for element in self.map[cmssite]['elements']:
            eList.append( element['host'] + "/" + element['type'] )
        return eList

    def getProdElements(self, cmssite):
        eList = []
        for element in self.map[cmssite]['elements']:
            if ( element['prod'] == True ):
                eList.append( element['host'] + "/" + element['type'] )
        return eList

    def write(self, file=sys.stdout, offset=0):
        off = "".ljust(offset)
        #
        for cmssite in self.sites():
            file.write("%s%s\n" % (off, cmssite))
            for element in self.map[cmssite]['elements']:
                file.write("%s   %s   (%s) at %s\n" % (off, element['host'],
                    element['type'], element['site']))
# ########################################################################### #



class sswpVector:
    'Data vector class for site metrics of the CMSSST site status display'
    tis_month = 0
    tis_pweek = 0
    tis_yrday = 0
    tis_today = 0
    tis_fweek = 0

    @staticmethod
    def SetTimestamps( timestamp ):
        # calculate start time of first bin in each section:
        # ==================================================
        #
        # month, first six-hour bin starts 00:00 a month+week+day earlier:
        ts = time.gmtime( timestamp - (30+7+1) * 24*60*60 )
        sswpVector.tis_month = calendar.timegm( ts[:3] + (0, 0, 0) + ts[6:] )
        #
        # pweek, first one-hour bin starts 00:00 a week+day earlier:
        ts = time.gmtime( timestamp - (7+1) * 24*60*60 )
        sswpVector.tis_pweek = calendar.timegm( ts[:3] + (0, 0, 0) + ts[6:] )
        #
        # yrday, first 15-min bin starts 00:00 yesterday:
        ts = time.gmtime( timestamp - 24*60*60 )
        sswpVector.tis_yrday = calendar.timegm( ts[:3] + (0, 0, 0) + ts[6:] )
        #
        # today, first 15-min bin starts 00:00 today:
        ts = time.gmtime( timestamp )
        sswpVector.tis_today = calendar.timegm( ts[:3] + (0, 0, 0) + ts[6:] )
        # 
        # fweek, first one-hour bin starts 00:00 tomorrow:
        ts = time.gmtime( timestamp + 24*60*60 )
        sswpVector.tis_fweek = calendar.timegm( ts[:3] + (0, 0, 0) + ts[6:] )
        # 
        # final, starts 00:00 a week+day after:
        ts = time.gmtime( timestamp + (7+1) * 24*60*60 )
        sswpVector.tis_final = calendar.timegm( ts[:3] + (0, 0, 0) + ts[6:] )

    @staticmethod
    def GetTimestamps():
        return { 'month': sswpVector.tis_month,
                 'pweek': sswpVector.tis_pweek,
                 'yrday': sswpVector.tis_yrday,
                 'today': sswpVector.tis_today,
                 'fweek': sswpVector.tis_fweek,
                 'final': sswpVector.tis_final }

    @staticmethod
    def WriteTimestamps(file=sys.stdout, offset=0):
        off = "".ljust(offset)
        #
        file.write("%sPrevious Month starts at %d (%s)\n" %
                   (off, sswpVector.tis_month,
                    time.strftime("%Y-%m-%d %H:%M:%S",
                                  time.gmtime(sswpVector.tis_month))))
        file.write("%sPrevious Week  starts at %d (%s)\n" %
                   (off, sswpVector.tis_pweek,
                    time.strftime("%Y-%m-%d %H:%M:%S",
                                  time.gmtime(sswpVector.tis_pweek))))
        file.write("%sYesterday      starts at %d (%s)\n" %
                   (off, sswpVector.tis_yrday,
                    time.strftime("%Y-%m-%d %H:%M:%S",
                                  time.gmtime(sswpVector.tis_yrday))))
        file.write("%sToday          starts at %d (%s)\n" %
                   (off, sswpVector.tis_today,
                    time.strftime("%Y-%m-%d %H:%M:%S",
                                  time.gmtime(sswpVector.tis_today))))
        file.write("%sFollowing Week starts at %d (%s)\n" %
                   (off, sswpVector.tis_fweek,
                    time.strftime("%Y-%m-%d %H:%M:%S",
                                  time.gmtime(sswpVector.tis_fweek))))
        file.write("%sFollowing Week ends   at %d (%s)\n" %
                   (off, sswpVector.tis_final,
                    time.strftime("%Y-%m-%d %H:%M:%S",
                                  time.gmtime(sswpVector.tis_final))))

    @staticmethod
    def FallsIntoBins(binType, binTime):
        if ( binType == "6hour" ):
            if (( binTime >= sswpVector.tis_month ) and
                ( binTime <= sswpVector.tis_pweek )):
                return True
        elif ( binType == "1hour" ):
            if (( binTime >= sswpVector.tis_pweek ) and
                ( binTime <= sswpVector.tis_yrday )):
                return True
            if (( binTime >= sswpVector.tis_fweek ) and
                ( binTime <= sswpVector.tis_final )):
                return True
        elif ( binType == "15min" ):
            if (( binTime >= sswpVector.tis_yrday ) and
                ( binTime <= sswpVector.tis_fweek )):
                return True
        return False

    @staticmethod
    def Bin2times(bin):
        if ( bin < (30 * 4) ):
            tis = sswpVector.tis_month + (bin * 21600)
            return (tis, tis + 21599)
        else:
            bin -= (30 * 4)
            if ( bin < (7 * 24) ):
                tis = sswpVector.tis_pweek + (bin * 3600)
                return (tis, tis + 3599)
            else:
                bin -= (7 * 24)
                if ( bin < (24 * 4) ):
                    tis = sswpVector.tis_yrday + (bin * 900)
                    return (tis, tis + 899)
                else:
                    bin -= (24 * 4)
                    if ( bin < (24 * 4) ):
                        tis = sswpVector.tis_today + (bin * 900)
                        return (tis, tis + 899)
                    else:
                        bin -= (24 * 4)
                        if ( bin < (7 * 24) ):
                            tis = sswpVector.tis_fweek + (bin * 3600)
                            return (tis, tis + 3599)
                        else:
                            raise IndexError("Bin number out-of-range")

    @staticmethod
    def Time2bin(tis):
        if ( tis < sswpVector.tis_month ):
            bin = None
        elif ( tis < sswpVector.tis_pweek ):
            bin = int( (tis - sswpVector.tis_month) / 21600 )
        elif ( tis < sswpVector.tis_yrday ):
            bin = (30 * 4) + int( (tis - sswpVector.tis_pweek) / 3600 )
        elif ( tis < sswpVector.tis_today ):
            bin = 120 + (7 * 24) + int( (tis - sswpVector.tis_yrday) / 900 )
        elif ( tis < sswpVector.tis_fweek ):
            bin = 288 + (24 * 4) + int( (tis - sswpVector.tis_today) / 900 )
        elif ( tis < sswpVector.tis_final ):
            bin = 384 + (24 * 4) + int( (tis - sswpVector.tis_fweek) / 3600 )
        else:
            # 480 + (7 * 12) = 648 bins total
            bin = None
        return bin

    @staticmethod
    def getDefaultBins():
        return 30*4+7*24+24*4+24*4+7*24

    @staticmethod
    def getDefaultBins15m():
        return 30*4+7*24+24*4+24*4+7*24+7*24*4

    @staticmethod
    def getYesterdayTodayBinRange():
        return range(30*4+7*24, 30*4+7*24+24*4+24*4)

    @staticmethod
    def writeEmpty_js(file=sys.stdout, offset=0):
        off = "".ljust(offset)
        #
        file.write("%spmonth: \"%s\" +\n%s        \"%s\",\n" %
            (off, ('u'*60), off, ('u'*60)))
        file.write(("%spweek: \"%s\" + \"%s\" +\n%s       \"%s\" + \"%s\" " + \
                    "+\n%s       \"%s\" + \"%s\" +\n%s       \"%s\",\n") %
            (off, ('u'*24), ('u'*24), off, ('u'*24), ('u'*24),
             off, ('u'*24), ('u'*24), off, ('u'*24)))
        file.write("%syesterday: \"%s\" +\n%s           \"%s\",\n" %
            (off, ('u'*48), off, ('u'*48)))
        file.write("%stoday: \"%s\" +\n%s       \"%s\",\n" %
            (off, ('u'*48), off, ('u'*48)))
        file.write(("%sfweek: \"%s\" + \"%s\" +\n%s       \"%s\" + \"%s\" " + \
                    "+\n%s       \"%s\" + \"%s\" +\n%s       \"%s\"") %
            (off, ('u'*24), ('u'*24), off, ('u'*24), ('u'*24),
             off, ('u'*24), ('u'*24), off, ('u'*24)))

    @staticmethod
    def writeEmty_json(file=sys.stdout, offset=0):
        off = "".ljust(offset)
        #
        file.write("%s\"pmonth\": [\"%s\",\n%s           \"%s\"],\n" %
            (off, ('u'*60), off, ('u'*60)))
        file.write(("%s\"pweek\": [\"%s\", \"%s\",\n" + \
                    "%s          \"%s\", \"%s\",\n" + \
                    "%s          \"%s\", \"%s\",\n%s          \"%s\"],\n") %
            (off, ('u'*24), ('u'*24), off, ('u'*24), ('u'*24),
             off, ('u'*24), ('u'*24), off, ('u'*24)))
        file.write("%s\"yesterday\": [\"%s\",\n%s              \"%s\"],\n" %
            (off, ('u'*48), off, ('u'*48)))
        file.write("%s\"today\": [\"%s\",\n%s          \"%s\"],\n" %
            (off, ('u'*48), off, ('u'*48)))
        file.write(("%s\"fweek\": [\"%s\", \"%s\",\n" + \
                    "%s          \"%s\", \"%s\",\n" + \
                    "%s          \"%s\", \"%s\",\n%s          \"%s\"]") %
            (off, ('u'*24), ('u'*24), off, ('u'*24), ('u'*24),
             off, ('u'*24), ('u'*24), off, ('u'*24)))
        # no newline at the end so newline or comma/newline should be added

    def __init__(self):
        self.month = 30*4*['u']
        self.pweek = 7*24*['u']
        self.yrday = 24*4*['u']
        self.today = 24*4*['u']
        self.fweek = 7*24*['u']

    def add15min(self):
        self.p15week = 7*24*4*['u']

    def del15min(self):
         if hasattr(self, 'p15week'):
             del self.p15week

    def addCounters(self):
        self.cnt_month = [{} for i in range(0, 30*4)]
        self.cnt_pweek = [{} for i in range(0, 7*24)]
        self.cnt_fweek = [{} for i in range(0, 7*24)]

    def delCounters(self):
        if hasattr(self, 'cnt_month'):
             del self.cnt_month
        if hasattr(self, 'cnt_pweek'):
             del self.cnt_pweek
        if hasattr(self, 'cnt_fweek'):
             del self.cnt_fweek

    def addVersions(self):
        self.ver_month = [-1 for i in range(0, 30*4)]
        self.ver_pweek = [-1 for i in range(0, 7*24)]
        self.ver_yrday = [-1 for i in range(0, 24*4)]
        self.ver_today = [-1 for i in range(0, 24*4)]
        self.ver_fweek = [-1 for i in range(0, 7*24)]

    def delVersions(self):
        if hasattr(self, 'ver_month'):
             del self.ver_month
        if hasattr(self, 'ver_pweek'):
             del self.ver_pweek
        if hasattr(self, 'ver_yrday'):
             del self.ver_yrday
        if hasattr(self, 'ver_today'):
             del self.ver_today
        if hasattr(self, 'ver_fweek'):
             del self.ver_fweek

    def getTotalBins(self):
        total = len(self.month) + len(self.pweek) + len(self.yrday) + \
                len(self.today) + len(self.fweek)
        if hasattr(self, 'p15week'):
            total += len(self.p15week)
        return total

    def fill(self, start, end, code):
        #
        # fill Previous Month six-hour list:
        sIndx = max(0, int( (start - sswpVector.tis_month) / 21600 ))
        eIndx = min(30*4, int( (end - sswpVector.tis_month + 21600) / 21600 ))
        #logging.debug("filling %s into month %d to %d", code, sIndx, eIndx)
        for indx in range(sIndx, eIndx):
            self.month[indx] = code
        #
        # fill Previous Week one-hour list:
        sIndx = max(0, int( (start - sswpVector.tis_pweek) / 3600 ))
        eIndx = min(7*24, int( (end - sswpVector.tis_pweek + 3600) / 3600 ))
        #logging.debug("filling %s into pweek %d to %d", code, sIndx, eIndx)
        for indx in range(sIndx, eIndx):
            self.pweek[indx] = code
        #
        # fill Yesterday 15-min list:
        sIndx = max(0, int( (start - sswpVector.tis_yrday) / 900 ))
        eIndx = min(24*4, int( (end - sswpVector.tis_yrday + 900) / 900 ))
        #logging.debug("filling %s into yrday %d to %d", code, sIndx, eIndx)
        for indx in range(sIndx, eIndx):
            self.yrday[indx] = code
        #
        # fill Today 15-min list:
        sIndx = max(0, int( (start - sswpVector.tis_today) / 900 ))
        eIndx = min(24*4, int( (end - sswpVector.tis_today + 900) / 900 ))
        #logging.debug("filling %s into today %d to %d", code, sIndx, eIndx)
        for indx in range(sIndx, eIndx):
            self.today[indx] = code
        #
        # fill Following Week one-hour list:
        sIndx = max(0, int( (start - sswpVector.tis_fweek) / 3600 ))
        eIndx = min(7*24, int( (end - sswpVector.tis_fweek + 3600) / 3600 ))
        #logging.debug("filling %s into fweek %d to %d", code, sIndx, eIndx)
        for indx in range(sIndx, eIndx):
            self.fweek[indx] = code
        #
        if hasattr(self, 'p15week'):
            # fill Previous Week 15-min list:
            sIndx = max(0, int( (start - sswpVector.tis_pweek) / 900 ))
            eIndx = min(7*24*4, int( (end - sswpVector.tis_pweek + 900) / 900 ))
            #logging.debug("filling %s into p15week %d to %d",
            #              code, sIndx, eIndx)
            for indx in range(sIndx, eIndx):
                self.p15week[indx] = code

    def fillCounters(self, start, end, code):
        #
        # fill counters Previous Month six-hour list:
        sIndx = max(0, int( (start - sswpVector.tis_month) / 21600 ))
        eIndx = min(30*4, int( (end - sswpVector.tis_month + 21600) / 21600 ))
        for indx in range(sIndx, eIndx):
            # calculate number of seconds inside bin:
            binStart = sswpVector.tis_month + indx * 21600
            binEnd = binStart + 21600
            nSec = min(end, binEnd) - max(start, binStart)
            if ( nSec <= 0 ):
                continue
            #logging.debug("filling %d sec of %s into month counter bin %d",
            #              nSec, code, indx)
            if code in self.cnt_month[indx]:
                self.cnt_month[indx][code] += nSec
            else:
                self.cnt_month[indx][code] = nSec
        #
        # fill counter Previous Week one-hour list:
        sIndx = max(0, int( (start - sswpVector.tis_pweek) / 3600 ))
        eIndx = min(7*24, int( (end - sswpVector.tis_pweek + 3600) / 3600 ))
        for indx in range(sIndx, eIndx):
            # calculate number of seconds inside bin:
            binStart = sswpVector.tis_pweek + indx * 3600
            binEnd = binStart + 3600
            nSec = min(end, binEnd) - max(start, binStart)
            if ( nSec <= 0 ):
                continue
            #logging.debug("filling %d sec of %s into pweek counter bin %d",
            #              nSec, code, indx)
            if code in self.cnt_pweek[indx]:
                self.cnt_pweek[indx][code] += nSec
            else:
                self.cnt_pweek[indx][code] = nSec
        #
        # fill Yesterday 15-min list:
        sIndx = max(0, int( (start - sswpVector.tis_yrday + 300) / 900 ))
        eIndx = min(24*4, int( (end - sswpVector.tis_yrday + 600) / 900 ))
        #logging.debug("filling %s into yrday %d to %d", code, sIndx, eIndx)
        for indx in range(sIndx, eIndx):
            self.yrday[indx] = code
        #
        # fill Today 15-min list:
        sIndx = max(0, int( (start - sswpVector.tis_today + 300) / 900 ))
        eIndx = min(24*4, int( (end - sswpVector.tis_today + 600) / 900 ))
        #logging.debug("filling %s into today %d to %d", code, sIndx, eIndx)
        for indx in range(sIndx, eIndx):
            self.today[indx] = code
        #
        # fill counter Following Week one-hour list:
        sIndx = max(0, int( (start - sswpVector.tis_fweek) / 3600 ))
        eIndx = min(7*24, int( (end - sswpVector.tis_fweek + 3600) / 3600 ))
        for indx in range(sIndx, eIndx):
            # calculate number of seconds inside bin:
            binStart = sswpVector.tis_fweek + indx * 3600
            binEnd = binStart + 3600
            nSec = min(end, binEnd) - max(start, binStart)
            if ( nSec <= 0 ):
                continue
            #logging.debug("filling %d sec of %s into fweek counter bin %d",
            #              nSec, code, indx)
            if code in self.cnt_fweek[indx]:
                self.cnt_fweek[indx][code] += nSec
            else:
                self.cnt_fweek[indx][code] = nSec

    def fillCenter(self, start, end, code):
        #
        # fill Previous Month six-hour list:
        sIndx = max(0, int( (start + 10799 - sswpVector.tis_month) / 21600 ))
        eIndx = min(30*4, int( (end - sswpVector.tis_month + 10800) / 21600 ))
        #logging.debug("filling %s into month %d to %d", code, sIndx, eIndx)
        for indx in range(sIndx, eIndx):
            self.month[indx] = code
        #
        # fill Previous Week one-hour list:
        sIndx = max(0, int( (start + 1799 - sswpVector.tis_pweek) / 3600 ))
        eIndx = min(7*24, int( (end - sswpVector.tis_pweek + 1800) / 3600 ))
        #logging.info("filling %s into pweek %d to %d", code, sIndx, eIndx)
        for indx in range(sIndx, eIndx):
            self.pweek[indx] = code
        #
        # fill Yesterday 15-min list:
        sIndx = max(0, int( (start + 449 - sswpVector.tis_yrday) / 900 ))
        eIndx = min(24*4, int( (end - sswpVector.tis_yrday + 450) / 900 ))
        #logging.debug("filling %s into yrday %d to %d", code, sIndx, eIndx)
        for indx in range(sIndx, eIndx):
            self.yrday[indx] = code
        #
        # fill Today 15-min list:
        sIndx = max(0, int( (start + 449 - sswpVector.tis_today) / 900 ))
        eIndx = min(24*4, int( (end - sswpVector.tis_today + 450) / 900 ))
        #logging.info("filling %s into today %d to %d", code, sIndx, eIndx)
        for indx in range(sIndx, eIndx):
            self.today[indx] = code
        #
        # fill Following Week one-hour list:
        sIndx = max(0, int( (start + 1799 - sswpVector.tis_fweek) / 3600 ))
        eIndx = min(7*24, int( (end - sswpVector.tis_fweek + 1800) / 3600 ))
        #logging.info("filling %s into fweek %d to %d", code, sIndx, eIndx)
        for indx in range(sIndx, eIndx):
            self.fweek[indx] = code
        #
        if hasattr(self, 'p15week'):
            # fill Previous Week 15-min list:
            sIndx = max(0, int( (start + 449 - sswpVector.tis_pweek) / 900 ))
            eIndx = min(7*24*4, int( (end - sswpVector.tis_pweek + 450) / 900 ))
            #logging.info("filling %s into p15week %d to %d",
            #             code, sIndx, eIndx)
            for indx in range(sIndx, eIndx):
                self.p15week[indx] = code

    def fillCenterErrorWarningOk(self, start, end, code):
        #
        # fill Previous Month six-hour list:
        sIndx = max(0, int( (start + 10799 - sswpVector.tis_month) / 21600 ))
        eIndx = min(30*4, int( (end - sswpVector.tis_month + 10800) / 21600 ))
        #logging.debug("filling %s into month %d to %d", code, sIndx, eIndx)
        for indx in range(sIndx, eIndx):
            if ( self.month[indx] == 'u' ):
                self.month[indx] = code
            elif ( self.month[indx] == 'o' ):
                self.month[indx] = code
            elif (( self.month[indx] == 'w' ) and ( code == 'e' )):
                self.month[indx] = 'e'
        #
        # fill Previous Week one-hour list:
        sIndx = max(0, int( (start + 1799 - sswpVector.tis_pweek) / 3600 ))
        eIndx = min(7*24, int( (end - sswpVector.tis_pweek + 1800) / 3600 ))
        #logging.debug("filling %s into pweek %d to %d", code, sIndx, eIndx)
        for indx in range(sIndx, eIndx):
            if ( self.pweek[indx] == 'u' ):
                self.pweek[indx] = code
            elif ( self.pweek[indx] == 'o' ):
                self.pweek[indx] = code
            elif (( self.pweek[indx] == 'w' ) and ( code == 'e' )):
                self.pweek[indx] = 'e'
        #
        # fill Yesterday 15-min list:
        sIndx = max(0, int( (start + 449 - sswpVector.tis_yrday) / 900 ))
        eIndx = min(24*4, int( (end - sswpVector.tis_yrday + 450) / 900 ))
        #logging.debug("filling %s into yrday %d to %d", code, sIndx, eIndx)
        for indx in range(sIndx, eIndx):
            if ( self.yrday[indx] == 'u' ):
                self.yrday[indx] = code
            elif ( self.yrday[indx] == 'o' ):
                self.yrday[indx] = code
            elif (( self.yrday[indx] == 'w' ) and ( code == 'e' )):
                self.yrday[indx] = 'e'
        #
        # fill Today 15-min list:
        sIndx = max(0, int( (start + 449 - sswpVector.tis_today) / 900 ))
        eIndx = min(24*4, int( (end - sswpVector.tis_today + 450) / 900 ))
        #logging.debug("filling %s into today %d to %d", code, sIndx, eIndx)
        for indx in range(sIndx, eIndx):
            if ( self.today[indx] == 'u' ):
                self.today[indx] = code
            elif ( self.today[indx] == 'o' ):
                self.today[indx] = code
            elif (( self.today[indx] == 'w' ) and ( code == 'e' )):
                self.today[indx] = 'e'
        #
        # fill Following Week one-hour list:
        sIndx = max(0, int( (start + 1799 - sswpVector.tis_fweek) / 3600 ))
        eIndx = min(7*24, int( (end - sswpVector.tis_fweek + 1800) / 3600 ))
        #logging.debug("filling %s into fweek %d to %d", code, sIndx, eIndx)
        for indx in range(sIndx, eIndx):
            if ( self.fweek[indx] == 'u' ):
                self.fweek[indx] = code
            elif ( self.fweek[indx] == 'o' ):
                self.fweek[indx] = code
            elif (( self.fweek[indx] == 'w' ) and ( code == 'e' )):
                self.fweek[indx] = 'e'
        #
        if hasattr(self, 'p15week'):
            # fill Previous Week 15-min list:
            sIndx = max(0, int( (start + 449 - sswpVector.tis_pweek) / 900 ))
            eIndx = min(7*24*4, int( (end - sswpVector.tis_pweek + 450) / 900 ))
            #logging.debug("filling %s into p15week %d to %d",
            #              code, sIndx, eIndx)
            for indx in range(sIndx, eIndx):
                if ( self.p15week[indx] == 'u' ):
                    self.p15week[indx] = code
                elif ( self.p15week[indx] == 'o' ):
                    self.p15week[indx] = code
                elif (( self.p15week[indx] == 'w' ) and ( code == 'e' )):
                    self.p15week[indx] = 'e'

    def fillCenterNoOverride(self, start, end, code):
        #
        # fill Previous Month six-hour list:
        sIndx = max(0, int( (start + 10799 - sswpVector.tis_month) / 21600 ))
        eIndx = min(30*4, int( (end - sswpVector.tis_month + 10800) / 21600 ))
        #logging.debug("filling %s into month %d to %d", code, sIndx, eIndx)
        for indx in range(sIndx, eIndx):
            if ( self.month[indx] == 'u' ):
                self.month[indx] = code
        #
        # fill Previous Week one-hour list:
        sIndx = max(0, int( (start + 1799 - sswpVector.tis_pweek) / 3600 ))
        eIndx = min(7*24, int( (end - sswpVector.tis_pweek + 1800) / 3600 ))
        #logging.debug("filling %s into pweek %d to %d", code, sIndx, eIndx)
        for indx in range(sIndx, eIndx):
            if ( self.pweek[indx] == 'u' ):
                self.pweek[indx] = code
        #
        # fill Yesterday 15-min list:
        sIndx = max(0, int( (start + 449 - sswpVector.tis_yrday) / 900 ))
        eIndx = min(24*4, int( (end - sswpVector.tis_yrday + 450) / 900 ))
        #logging.debug("filling %s into yrday %d to %d", code, sIndx, eIndx)
        for indx in range(sIndx, eIndx):
            if ( self.yrday[indx] == 'u' ):
                self.yrday[indx] = code
        #
        # fill Today 15-min list:
        sIndx = max(0, int( (start + 449 - sswpVector.tis_today) / 900 ))
        eIndx = min(24*4, int( (end - sswpVector.tis_today + 450) / 900 ))
        #logging.debug("filling %s into today %d to %d", code, sIndx, eIndx)
        for indx in range(sIndx, eIndx):
            if ( self.today[indx] == 'u' ):
                self.today[indx] = code
        #
        # fill Following Week one-hour list:
        sIndx = max(0, int( (start + 1799 - sswpVector.tis_fweek) / 3600 ))
        eIndx = min(7*24, int( (end - sswpVector.tis_fweek + 1800) / 3600 ))
        #logging.debug("filling %s into fweek %d to %d", code, sIndx, eIndx)
        for indx in range(sIndx, eIndx):
            if ( self.fweek[indx] == 'u' ):
                self.fweek[indx] = code
        #
        if hasattr(self, 'p15week'):
            # fill Previous Week 15-min list:
            sIndx = max(0, int( (start + 449 - sswpVector.tis_pweek) / 900 ))
            eIndx = min(7*24*4, int( (end - sswpVector.tis_pweek + 450) / 900 ))
            #logging.debug("filling %s into p15week %d to %d",
            #              code, sIndx, eIndx)
            for indx in range(sIndx, eIndx):
                if ( self.p15week[indx] == 'u' ):
                    self.p15week[indx] = code

    def fillWithVersion(self, center, code, version):
        #
        # check if timebin center falls into Previous Month six-hour bins:
        indx = round( (center - (sswpVector.tis_month + 10800)) / 21600 )
        if (( indx >= 0 ) and ( indx < 30*4 )):
            if ( version > self.ver_month[indx] ):
                self.month[indx] = code
                self.ver_month[indx] = version
        else:
            indx = round( (center - (sswpVector.tis_pweek + 1800)) / 3600 )
            if (( indx >= 0 ) and ( indx < 7*24 )):
                if ( version > self.ver_pweek[indx] ):
                    self.pweek[indx] = code
                    self.ver_pweek[indx] = version
            else:
                indx = round( (center - (sswpVector.tis_yrday + 450)) / 900 )
                if (( indx >= 0 ) and ( indx < 24*4 )):
                    if ( version > self.ver_yrday[indx] ):
                        self.yrday[indx] = code
                        self.ver_yrday[indx] = version
                else:
                    indx = round( (center - (sswpVector.tis_today + 450)) /
                                                                          900 )
                    if (( indx >= 0 ) and ( indx < 24*4 )):
                        if ( version > self.ver_today[indx] ):
                            self.today[indx] = code
                            self.ver_today[indx] = version
                    else:
                        indx = round( (center - (sswpVector.tis_fweek + 1800))
                                                                       / 3600 )
                        if (( indx >= 0 ) and ( indx < 7*24 )):
                            if ( version > self.ver_fweek[indx] ):
                                self.fweek[indx] = code
                                self.ver_fweek[indx] = version

    def setBin(self, bin, code):
        if ( bin < len(self.month) ):
            self.month[bin] = code
        else:
            bin -= len(self.month)
            if ( bin < len(self.pweek) ):
                self.pweek[bin] = code
            else:
                bin -= len(self.pweek)
                if ( bin < len(self.yrday) ):
                    self.yrday[bin] = code
                else:
                    bin -= len(self.yrday)
                    if ( bin < len(self.today) ):
                        self.today[bin] = code
                    else:
                        bin -= len(self.today)
                        if ( bin < len(self.fweek) ):
                            self.fweek[bin] = code
                        else:
                            bin -= len(self.fweek)
                            if not hasattr(self, 'p15week'):
                                raise IndexError("No p15min vector")
                            if ( bin < len(self.p15week) ):
                                self.p15week[bin] = code
                            else:
                                raise IndexError("Bin number out-of-range")

    def setBinNoOverride(self, bin, code):
        if ( bin < len(self.month) ):
            if (( self.month[bin] == 'u' ) or ( self.month[bin] == 'p' )):
                self.month[bin] = code
            elif (( self.month[bin] == 'd' ) or ( self.month[bin] == 'a' )):
                if ( code == 'o'):
                    self.month[bin] = 'o'
        else:
            bin -= len(self.month)
            if ( bin < len(self.pweek) ):
                if (( self.pweek[bin] == 'u' ) or ( self.pweek[bin] == 'p' )):
                    self.pweek[bin] = code
                elif (( self.pweek[bin] == 'd' ) or ( self.pweek[bin] == 'a' )):
                    if ( code == 'o'):
                       self.pweek[bin] = 'o'
            else:
                bin -= len(self.pweek)
                if ( bin < len(self.yrday) ):
                    if (( self.yrday[bin] == 'u' ) or
                        ( self.yrday[bin] == 'p' )):
                        self.yrday[bin] = code
                    elif (( self.yrday[bin] == 'd' ) or
                          ( self.yrday[bin] == 'a' )):
                        if ( code == 'o'):
                           self.yrday[bin] = 'o'
                else:
                    bin -= len(self.yrday)
                    if ( bin < len(self.today) ):
                        if (( self.today[bin] == 'u' ) or
                            ( self.today[bin] == 'p' )):
                            self.today[bin] = code
                        elif (( self.today[bin] == 'd' ) or
                              ( self.today[bin] == 'a' )):
                            if ( code == 'o'):
                               self.today[bin] = 'o'
                    else:
                        bin -= len(self.today)
                        if ( bin < len(self.fweek) ):
                            if (( self.fweek[bin] == 'u' ) or
                                ( self.fweek[bin] == 'p' )):
                                self.fweek[bin] = code
                            elif (( self.fweek[bin] == 'd' ) or
                                  ( self.fweek[bin] == 'a' )):
                                if ( code == 'o'):
                                   self.fweek[bin] = 'o'
                        else:
                            bin -= len(self.fweek)
                            if not hasattr(self, 'p15week'):
                                raise IndexError("No p15min vector")
                            if ( bin < len(self.p15week) ):
                                if (( self.p15week[bin] == 'u' ) or
                                    ( self.p15week[bin] == 'p' )):
                                    self.p15week[bin] = code
                                elif (( self.p15week[bin] == 'd' ) or
                                      ( self.p15week[bin] == 'a' )):
                                    if ( code == 'o'):
                                       self.p15week[bin] = 'o'
                            else:
                                raise IndexError("Bin number out-of-range")

    def getBin(self, bin):
        if ( bin < len(self.month) ):
            return self.month[bin]
        else:
            bin -= len(self.month)
            if ( bin < len(self.pweek) ):
                return self.pweek[bin]
            else:
                bin -= len(self.pweek)
                if ( bin < len(self.yrday) ):
                    return self.yrday[bin]
                else:
                    bin -= len(self.yrday)
                    if ( bin < len(self.today) ):
                        return self.today[bin]
                    else:
                        bin -= len(self.today)
                        if ( bin < len(self.fweek) ):
                            return self.fweek[bin]
                        else:
                            bin -= len(self.fweek)
                            if not hasattr(self, 'p15week'):
                                raise IndexError("No p15min vector")
                            if ( bin < len(self.p15week) ):
                                return self.p15week[bin]
                            else:
                                raise IndexError("Bin number out-of-range")

    def write_js(self, file=sys.stdout, offset=0):
        off = "".ljust(offset)
        #
        file.write("%spmonth: \"%s\" +\n%s        \"%s\",\n" %
            (off, ''.join(self.month[0:60]), off, ''.join(self.month[60:120])))
        file.write(("%spweek: \"%s\" + \"%s\" +\n%s       \"%s\" + \"%s\" " + \
                    "+\n%s       \"%s\" + \"%s\" +\n%s       \"%s\",\n") %
            (off, ''.join(self.pweek[0:24]), ''.join(self.pweek[24:48]),
             off, ''.join(self.pweek[48:72]), ''.join(self.pweek[72:96]),
             off, ''.join(self.pweek[96:120]), ''.join(self.pweek[120:144]),
             off, ''.join(self.pweek[144:168])))
        file.write("%syesterday: \"%s\" +\n%s           \"%s\",\n" %
            (off, ''.join(self.yrday[0:48]),
             off, ''.join(self.yrday[48:96])))
        file.write("%stoday: \"%s\" +\n%s       \"%s\",\n" %
            (off, ''.join(self.today[0:48]), off, ''.join(self.today[48:96])))
        file.write(("%sfweek: \"%s\" + \"%s\" +\n%s       \"%s\" + \"%s\" " + \
                    "+\n%s       \"%s\" + \"%s\" +\n%s       \"%s\"") %
            (off, ''.join(self.fweek[0:24]), ''.join(self.fweek[24:48]),
             off, ''.join(self.fweek[48:72]), ''.join(self.fweek[72:96]),
             off, ''.join(self.fweek[96:120]), ''.join(self.fweek[120:144]),
             off, ''.join(self.fweek[144:168])))
        # no newline at the end so newline or comma/newline should be added

    def write_json(self, file=sys.stdout, offset=0):
        off = "".ljust(offset)
        #
        file.write("%s\"pmonth\": [\"%s\",\n%s           \"%s\"],\n" %
            (off, ''.join(self.month[0:60]), off, ''.join(self.month[60:120])))
        file.write(("%s\"pweek\": [\"%s\", \"%s\",\n" + \
                    "%s          \"%s\", \"%s\",\n" + \
                    "%s          \"%s\", \"%s\",\n%s          \"%s\"],\n") %
            (off, ''.join(self.pweek[0:24]), ''.join(self.pweek[24:48]),
             off, ''.join(self.pweek[48:72]), ''.join(self.pweek[72:96]),
             off, ''.join(self.pweek[96:120]), ''.join(self.pweek[120:144]),
             off, ''.join(self.pweek[144:168])))
        file.write("%s\"yesterday\": [\"%s\",\n%s              \"%s\"],\n" %
            (off, ''.join(self.yrday[0:48]),
             off, ''.join(self.yrday[48:96])))
        file.write("%s\"today\": [\"%s\",\n%s          \"%s\"],\n" %
            (off, ''.join(self.today[0:48]), off, ''.join(self.today[48:96])))
        file.write(("%s\"fweek\": [\"%s\", \"%s\",\n" + \
                    "%s          \"%s\", \"%s\",\n" + \
                    "%s          \"%s\", \"%s\",\n%s          \"%s\"]") %
            (off, ''.join(self.fweek[0:24]), ''.join(self.fweek[24:48]),
             off, ''.join(self.fweek[48:72]), ''.join(self.fweek[72:96]),
             off, ''.join(self.fweek[96:120]), ''.join(self.fweek[120:144]),
             off, ''.join(self.fweek[144:168])))
        # no newline at the end so newline or comma/newline should be added

    def merge15min(self):
        cnt = {}
        #
        # previous week (15 min --> 1 hour bins):
        for bin in range(0, 7*24):
            # loop over the 168 one-hour bins and combine the 4 15-min bins:
            for code in ('u', 'p', 'd', 'a', 'o', 'w', 'e', 'W', 'M'):
                cnt[code] = 0
            cnt_pda = 0
            cnt_owe = 0
            cnt_wgt = 0
            for bin15m in range(bin*4, bin*4+4):
                code = self.p15week[bin15m]
                cnt[ code ] += 1
                if ( code in ('p', 'd', 'a')):
                    cnt_pda += 1
                elif ( code == 'o' ):
                    cnt_owe += 1
                elif ( code == 'w' ):
                    cnt_owe += 1
                    cnt_wgt += 1
                elif ( code == 'e' ):
                    cnt_owe += 1
                    cnt_wgt += 2
            codes = sorted(cnt, key=cnt.__getitem__, reverse=True)
            indx = 0
            if ( codes[indx] == 'u' ):
                indx += 1
            if ( cnt[ codes[indx] ] == 0 ):
                scode = 'u'
            elif ( cnt[ codes[indx] ] > (4-cnt['u']) / 2 ):
                scode = codes[indx]
            elif ( cnt_owe >= (4-cnt['u']) / 2 ):
                cnt_wgt = cnt_wgt / (cnt['o'] + cnt['w'] + cnt['e'])
                if ( cnt_wgt <= 2/3 ):
                    scode = 'o'
                elif ( cnt_wgt <= 4/3 ):
                    scode = 'w'
                else:
                    scode = 'e'
            elif ( cnt_pda >= (4-cnt['u']) / 2 ):
                if (( cnt['d'] >= cnt['p'] ) and ( cnt['d'] >= cnt['a'] )):
                    scode = 'd'
                elif ( cnt['p'] >= cnt['a'] ):
                    scode = 'p'
                else:
                    scode = 'a'
            elif ( cnt['W'] >= cnt['M'] ):
                scode = 'W'
            else:
                scode = 'M'
            self.pweek[bin] = scode
        #
        del self.p15week

    def resolveCounters(self):
        # previous month, 30*4 six-hour bins:
        for bin in range(0, 30*4):
            # count seconds for which we have information:
            if 'u' in self.cnt_month[bin]:
               del self.cnt_month[bin]['u']
            tSec = 0
            for code in self.cnt_month[bin].keys():
                tSec += self.cnt_month[bin][code]
            if ( tSec <= 2160 ):
                # counter covers less than 10% of time bin
                continue
            #logging.debug(("resolving month[%d] counter, total=%d, down=%d," +
            #               " ok=%d, warn=%d, err=%d", bin, tSec,
            #              self.cnt_month[bin].get('d', 0),
            #              self.cnt_month[bin].get('o', 0),
            #              self.cnt_month[bin].get('w', 0),
            #              self.cnt_month[bin].get('e', 0))
            sKey = sorted(self.cnt_month[bin],
                          key=self.cnt_month[bin].__getitem__, reverse=True)
            if ( self.cnt_month[bin][ sKey[0] ] > 0.5*tSec ):
                # code covers more than half the time bin
                self.month[bin] = sKey[0]
            elif (( sKey[0] != 'd' ) and
                  ( self.cnt_month[bin][ sKey[0] ] >
                    0.5*(tSec - self.cnt_month[bin].get('d', 0)))):
                # code covers more than half the time bin not in downtime
                self.month[bin] = sKey[0]
            elif ( self.cnt_month[bin].get('o', 0) +
                   self.cnt_month[bin].get('w', 0) +
                   self.cnt_month[bin].get('d', 0) > 0.5*tSec ):
                # 'o', 'w', and 'd' cover more than have the time bin
                if ( self.cnt_month[bin].get('o', 0) >=
                     self.cnt_month[bin].get('w', 0) ):
                    self.month[bin] = 'o'
                else:
                    self.month[bin] = 'w'
            elif ( self.cnt_month[bin].get('o', 0) +
                   self.cnt_month[bin].get('w', 0) +
                   self.cnt_month[bin].get('e', 0) >= 0.5*tSec ):
                # 'o', 'w', 'e' status codes cover more than have the time bin
                wgt = ( self.cnt_month[bin].get('w', 0) +
                         2.0 * self.cnt_month[bin].get('e', 0) ) / \
                      ( self.cnt_month[bin].get('o', 0) +
                        self.cnt_month[bin].get('w', 0) +
                        self.cnt_month[bin].get('e', 0) )
                if ( wgt < 0.6667 ):
                    self.month[bin] = 'o'
                elif ( wgt < 1.3333 ):
                    self.month[bin] = 'w'
                else:
                    self.month[bin] = 'e'
            elif ( self.cnt_month[bin].get('p', 0) +
                   self.cnt_month[bin].get('a', 0) +
                   self.cnt_month[bin].get('d', 0) >= 0.5*tSec ):
                # 'p', 'a', 'd' status codes cover more than have the time bin
                if (( self.cnt_month[bin].get('d', 0) >=
                      self.cnt_month[bin].get('p', 0) ) and
                    ( self.cnt_month[bin].get('d', 0) >=
                      self.cnt_month[bin].get('a', 0) )):
                    self.month[bin] = 'd'
                elif ( self.cnt_month[bin].get('p', 0) >=
                       self.cnt_month[bin].get('a', 0) ):
                    self.month[bin] = 'p'
                else:
                    self.month[bin] = 'a'
            elif ( self.cnt_month[bin].get('W', 0) +
                   self.cnt_month[bin].get('M', 0) >= 0.5*tSec ):
                # 'W', 'M' status codes cover more than have the time bin
                if ( self.cnt_month[bin].get('W', 0) >=
                     self.cnt_month[bin].get('M', 0) ):
                    self.month[bin] = 'W'
                else:
                    self.month[bin] = 'M'
        # previous week, 7*24 one-hour bins:
        for bin in range(0, 7*24):
            # count seconds for which we have information:
            if 'u' in self.cnt_pweek[bin]:
               del self.cnt_pweek[bin]['u']
            tSec = 0
            for code in self.cnt_pweek[bin].keys():
                tSec += self.cnt_pweek[bin][code]
            if ( tSec <= 360 ):
                # counter covers less than 10% of time bin
                continue
            #logging.debug(("resolving pweek[%d] counter, total=%d, down=%d," +
            #               " ok=%d, warn=%d, err=%d"), bin, tSec,
            #              self.cnt_pweek[bin].get('d', 0),
            #              self.cnt_pweek[bin].get('o', 0),
            #              self.cnt_pweek[bin].get('w', 0),
            #              self.cnt_pweek[bin].get('e', 0))
            sKey = sorted(self.cnt_pweek[bin],
                          key=self.cnt_pweek[bin].__getitem__, reverse=True)
            if ( self.cnt_pweek[bin][ sKey[0] ] > 0.5*tSec ):
                # code covers more than half the time bin
                self.pweek[bin] = sKey[0]
            elif (( sKey[0] != 'd' ) and
                  ( self.cnt_pweek[bin][ sKey[0] ] >
                    0.5*(tSec - self.cnt_pweek[bin].get('d', 0)))):
                # code covers more than half the time bin not in downtime
                self.pweek[bin] = sKey[0]
            elif ( self.cnt_pweek[bin].get('o', 0) +
                   self.cnt_pweek[bin].get('w', 0) +
                   self.cnt_pweek[bin].get('d', 0) > 0.5*tSec ):
                # 'o', 'w', and 'd' cover more than have the time bin
                if ( self.cnt_pweek[bin].get('o', 0) >=
                     self.cnt_pweek[bin].get('w', 0) ):
                    self.pweek[bin] = 'o'
                else:
                    self.pweek[bin] = 'w'
            elif ( self.cnt_pweek[bin].get('o', 0) +
                   self.cnt_pweek[bin].get('w', 0) +
                   self.cnt_pweek[bin].get('e', 0) >= 0.5*tSec ):
                # 'o', 'w', 'e' status codes cover more than have the time bin
                wgt = ( self.cnt_pweek[bin].get('w', 0) +
                        2.0 * self.cnt_pweek[bin].get('e', 0) ) / \
                      ( self.cnt_pweek[bin].get('o', 0) +
                        self.cnt_pweek[bin].get('w', 0) +
                        self.cnt_pweek[bin].get('e', 0) )
                if ( wgt < 0.6667 ):
                    self.pweek[bin] = 'o'
                elif ( wgt < 1.3333 ):
                    self.pweek[bin] = 'w'
                else:
                    self.pweek[bin] = 'e'
            elif ( self.cnt_pweek[bin].get('p', 0) +
                   self.cnt_pweek[bin].get('a', 0) +
                   self.cnt_pweek[bin].get('d', 0) >= 0.5*tSec ):
                # 'p', 'a', 'd' status codes cover more than have the time bin
                if (( self.cnt_pweek[bin].get('d', 0) >=
                      self.cnt_pweek[bin].get('p', 0) ) and
                    ( self.cnt_pweek[bin].get('d', 0) >=
                      self.cnt_pweek[bin].get('a', 0) )):
                    self.pweek[bin] = 'd'
                elif ( self.cnt_pweek[bin].get('p', 0) >=
                       self.cnt_pweek[bin].get('a', 0) ):
                    self.pweek[bin] = 'p'
                else:
                    self.pweek[bin] = 'a'
            elif ( self.cnt_pweek[bin].get('W', 0) +
                   self.cnt_pweek[bin].get('M', 0) >= 0.5*tSec ):
                # 'W', 'M' status codes cover more than have the time bin
                if ( self.cnt_pweek[bin].get('W', 0) >=
                     self.cnt_pweek[bin].get('M', 0) ):
                    self.pweek[bin] = 'W'
                else:
                    self.pweek[bin] = 'M'
        # following week, 7*24 one-hour bins:
        for bin in range(0, 7*24):
            # count seconds for which we have information:
            if 'u' in self.cnt_fweek[bin]:
               del self.cnt_fweek[bin]['u']
            tSec = 0
            for code in self.cnt_fweek[bin].keys():
                tSec += self.cnt_fweek[bin][code]
            if ( tSec <= 360 ):
                # counter covers less than 10% of time bin
                continue
            #logging.debug(("resolving fweek[%d] counter, total=%d, down=%d," +
            #               " ok=%d, warn=%d, err=%d"), bin, tSec,
            #              self.cnt_fweek[bin].get('d', 0),
            #              self.cnt_fweek[bin].get('o', 0),
            #              self.cnt_fweek[bin].get('w', 0),
            #              self.cnt_fweek[bin].get('e', 0)))
            sKey = sorted(self.cnt_fweek[bin],
                          key=self.cnt_fweek[bin].__getitem__, reverse=True)
            if ( self.cnt_fweek[bin][ sKey[0] ] > 0.5*tSec ):
                # code covers more than half the time bin
                self.fweek[bin] = sKey[0]
            elif (( sKey[0] != 'd' ) and
                  ( self.cnt_fweek[bin][ sKey[0] ] >
                    0.5*(tSec - self.cnt_fweek[bin].get('d', 0)))):
                # code covers more than half the time bin not in downtime
                self.fweek[bin] = sKey[0]
            elif ( self.cnt_fweek[bin].get('o', 0) +
                   self.cnt_fweek[bin].get('w', 0) +
                   self.cnt_fweek[bin].get('d', 0) > 0.5*tSec ):
                # 'o', 'w', and 'd' cover more than have the time bin
                if ( self.cnt_fweek[bin].get('o', 0) >=
                     self.cnt_fweek[bin].get('w', 0) ):
                    self.fweek[bin] = 'o'
                else:
                    self.fweek[bin] = 'w'
            elif ( self.cnt_fweek[bin].get('o', 0) +
                   self.cnt_fweek[bin].get('w', 0) +
                   self.cnt_fweek[bin].get('e', 0) >= 0.5*tSec ):
                # 'o', 'w', 'e' status codes cover more than have the time bin
                wgt = ( self.cnt_fweek[bin].get('w', 0) +
                        2.0 * self.cnt_fweek[bin].get('e', 0) ) / \
                      ( self.cnt_fweek[bin].get('o', 0) +
                        self.cnt_fweek[bin].get('w', 0) +
                        self.cnt_fweek[bin].get('e', 0) )
                if ( wgt < 0.6667 ):
                    self.fweek[bin] = 'o'
                elif ( wgt < 1.3333 ):
                    self.fweek[bin] = 'w'
                else:
                    self.fweek[bin] = 'e'
            elif ( self.cnt_fweek[bin].get('p', 0) +
                   self.cnt_fweek[bin].get('a', 0) +
                   self.cnt_fweek[bin].get('d', 0) >= 0.5*tSec ):
                # 'p', 'a', 'd' status codes cover more than have the time bin
                if (( self.cnt_fweek[bin].get('d', 0) >=
                      self.cnt_fweek[bin].get('p', 0) ) and
                    ( self.cnt_fweek[bin].get('d', 0) >=
                      self.cnt_fweek[bin].get('a', 0) )):
                    self.fweek[bin] = 'd'
                elif ( self.cnt_fweek[bin].get('p', 0) >=
                       self.cnt_fweek[bin].get('a', 0) ):
                    self.fweek[bin] = 'p'
                else:
                    self.fweek[bin] = 'a'
            elif ( self.cnt_fweek[bin].get('W', 0) +
                   self.cnt_fweek[bin].get('M', 0) >= 0.5*tSec ):
                # 'W', 'M' status codes cover more than have the time bin
                if ( self.cnt_fweek[bin].get('W', 0) >=
                     self.cnt_fweek[bin].get('M', 0) ):
                    self.fweek[bin] = 'W'
                else:
                    self.fweek[bin] = 'M'

    def resolveCountersDownOkWarnErr(self, errorThreshold):
        # previous month, 30*4 six-hour bins:
        for bin in range(0, 30*4):
            if (( len( self.cnt_month[bin] ) == 1 ) and
                ( list(self.cnt_month[bin].values())[0] > 2160 )):
               # only one entry covering more than 10% of the time interval
               self.month[bin] = list(self.cnt_month[bin].keys())[0]
               continue
            # count seconds for which we have information:
            tSec = 0
            for code in self.cnt_month[bin].keys():
               tSec += self.cnt_month[bin][code]
            if ( tSec <= 2160 ):
               continue
            #logging.debug(("resolving month[%d] counter, total=%d, ok=%d, e" +
            #               "rr=%d"), bin, tSec,
            #              self.cnt_month[bin].get('o', 0),
            #              self.cnt_month[bin].get('e', 0))
            if ( self.cnt_month[bin].get('d', 0) > tSec / 2 ):
               # downtime for more than half of the time interval
               self.month[bin] = 'd'
               continue
            tSec = float( tSec - self.cnt_month[bin].get('d', 0) )
            if ( (self.cnt_month[bin].get('o', 0) / tSec) >= 0.90 ):
               self.month[bin] = 'o'
            elif ( (self.cnt_month[bin].get('e', 0) / tSec) >
                   (1.00-errorThreshold) ):
               self.month[bin] = 'e'
            else:
               self.month[bin] = 'w'
        # previous week, 7*24 one-hour bins:
        for bin in range(0, 7*24):
            # count seconds for which we have information:
            tSec = 0
            for code in self.cnt_pweek[bin].keys():
               tSec += self.cnt_pweek[bin][code]
            if ( tSec <= 360 ):
               continue
            #logging.debug(("resolving pweek[%d] counter, total=%d, down=%d," +
            #               " ok=%d, warn=%d, err=%d"), bin, tSec,
            #              self.cnt_pweek[bin].get('d', 0),
            #              self.cnt_pweek[bin].get('o', 0),
            #              self.cnt_pweek[bin].get('w', 0),
            #              self.cnt_pweek[bin].get('e', 0))
            if ( self.cnt_pweek[bin].get('d', 0) > tSec / 2 ):
               self.pweek[bin] = 'd'
               continue
            tSec = float( tSec - self.cnt_pweek[bin].get('d', 0) )
            if ( (self.cnt_pweek[bin].get('o',0) / tSec) >= 0.90 ):
               self.pweek[bin] = 'o'
            elif ( (self.cnt_pweek[bin].get('e', 0) / tSec) >
                   (1.00-errorThreshold) ):
               self.pweek[bin] = 'e'
            else:
               self.pweek[bin] = 'w'
        # following week, 7*24 one-hour bins:
        for bin in range(0, 7*24):
            # count seconds for which we have information:
            tSec = 0
            for code in self.cnt_fweek[bin].keys():
               tSec += self.cnt_fweek[bin][code]
            if ( tSec <= 360 ):
               continue
            #logging.debug(("resolving fweek[%d] counter, total=%d, ok=%d, e" +
            #               "rr=%d"), bin, tSec,
            #              self.cnt_fweek[bin].get('o', 0),
            #              self.cnt_fweek[bin].get('e', 0))
            if ( self.cnt_fweek[bin].get('d', 0) > tSec / 2 ):
               self.fweek[bin] = 'd'
               continue
            tSec = float( tSec - self.cnt_fweek[bin].get('d', 0) )
            if ( (self.cnt_fweek[bin].get('o', 0) / tSec) >= 0.90 ):
               self.fweek[bin] = 'o'
            elif ( (self.cnt_fweek[bin].get('e', 0) / tSec) >
                   (1.00-errorThreshold) ):
               self.fweek[bin] = 'e'
            else:
               self.fweek[bin] = 'w'
# ########################################################################### #



class sswpArray:
    'Vector array class for site metrics of the CMSSST site status display'

    def __init__(self):
        self.array = {}

    def fill(self, metric, site, start, end, code):
        if site not in self.array:
            self.array[site] = {metric: sswpVector()}
        else:
            if metric not in self.array[site]:
                self.array[site][metric] = sswpVector()
        #
        self.array[site][metric].fill(start, end, code)

    def fill15m(self, metric, site, start, end, code):
        if site not in self.array:
            self.array[site] = {metric: sswpVector()}
            self.array[site][metric].add15min()
        else:
            if metric not in self.array[site]:
                self.array[site][metric] = sswpVector()
                self.array[site][metric].add15min()
        #
        self.array[site][metric].fill(start, end, code)

    def fillCenter(self, metric, site, start, end, code):
        if site not in self.array:
            self.array[site] = {metric: sswpVector()}
        else:
            if metric not in self.array[site]:
                self.array[site][metric] = sswpVector()
        #
        self.array[site][metric].fillCenter(start, end, code)

    def fillCenter15m(self, metric, site, start, end, code):
        if site not in self.array:
            self.array[site] = {metric: sswpVector()}
            self.array[site][metric].add15min()
        else:
            if metric not in self.array[site]:
                self.array[site][metric] = sswpVector()
                self.array[site][metric].add15min()
        #
        self.array[site][metric].fillCenter(start, end, code)

    def fillCenterErrorWarningOk(self, metric, site, start, end, code):
        if site not in self.array:
            self.array[site] = {metric: sswpVector()}
        else:
            if metric not in self.array[site]:
                self.array[site][metric] = sswpVector()
        #
        self.array[site][metric].fillCenterErrorWarningOk(start, end, code)

    def fillCenterNoOverride(self, metric, site, start, end, code):
        if site not in self.array:
            self.array[site] = {metric: sswpVector()}
        else:
            if metric not in self.array[site]:
                self.array[site][metric] = sswpVector()
        #
        self.array[site][metric].fillCenterNoOverride(start, end, code)

    def fillCounters(self, metric, site, start, end, code):
        if site not in self.array:
            self.array[site] = {metric: sswpVector()}
            self.array[site][metric].addCounters()
        else:
            if metric not in self.array[site]:
                self.array[site][metric] = sswpVector()
                self.array[site][metric].addCounters()
        #
        self.array[site][metric].fillCounters(start, end, code)

    def fillWithVersion(self, metric, site, center, code, version):
        if site not in self.array:
            self.array[site] = {metric: sswpVector()}
            self.array[site][metric].addVersions()
        else:
            if metric not in self.array[site]:
                self.array[site][metric] = sswpVector()
                self.array[site][metric].addVersions()
        #
        self.array[site][metric].fillWithVersion(center, code, version)

    def getTotalBins(self, metric, site):
        if site not in self.array:
            return sswpVector.getDefaultBins()
        else:
            if metric not in self.array[site]:
                return sswpVector.getDefaultBins()
        #
        return self.array[site][metric].getTotalBins()

    def setBin(self, metric, site, bin, code):
        if ( code == 'u' ):
            return
        #
        if site not in self.array:
            self.array[site] = {metric: sswpVector()}
        else:
            if metric not in self.array[site]:
                self.array[site][metric] = sswpVector()
        #
        self.array[site][metric].setBin(bin, code)

    def setBin15m(self, metric, site, bin, code):
        if ( code == 'u' ):
            return
        #
        if site not in self.array:
            self.array[site] = {metric: sswpVector()}
            self.array[site][metric].add15min()
        else:
            if metric not in self.array[site]:
                self.array[site][metric] = sswpVector()
                self.array[site][metric].add15min()
        #
        self.array[site][metric].setBin(bin, code)

    def setBinNoOverride(self, metric, site, bin, code):
        if ( code == 'u' ):
            return
        #
        if site not in self.array:
            self.array[site] = {metric: sswpVector()}
        else:
            if metric not in self.array[site]:
                self.array[site][metric] = sswpVector()
        #
        self.array[site][metric].setBinNoOverride(bin, code)

    def getBin(self, metric, site, bin):
        if site not in self.array:
            return 'u'
        else:
            if metric not in self.array[site]:
                return 'u'
        #
        return self.array[site][metric].getBin(bin)

    def getMetricList(self):
        tuple = ()
        for site in self.array.keys():
            for metric in self.array[site].keys():
                if metric not in tuple:
                    tuple += (metric, )
        return tuple

    def getVector(self, metric, site):
        if site not in self.array:
            return None
        if metric not in self.array[site]:
            return None
        return self.array[site][metric]

    def deleteVector(self, metric, site):
        if site in self.array:
            if metric in self.array[site]:
                del self.array[site][metric]

    def writeSite(self, file, offset, site):
        first = True
        #
        for metric in sorted(self.array[site].keys()):
            if ( not first ):
                file.write(",\n")
            self.array[site][metric].write(file, offset)
            first = False
        # no newline at the end so newline or comma/newline should be added

    def writeMetric(self, file, offset, metric):
        first = True
        #
        for site in sorted(self.array.keys()):
            if metric in self.array[site]:
                if ( not first ):
                    file.write(",\n")
                self.array[site][metric].write(file, offset)
                first = False
        # no newline at the end so newline or comma/newline should be added

    def write(self, file=sys.stdout, offset=0):
        off = "".ljust(offset)
        #
        for site in sorted(self.array.keys()):
            file.write("%s%s:\n" % (off, site))
            for metric in sorted(self.array[site].keys()):
                file.write("%s   %s:\n" % (off, metric))
                self.array[site][metric].write(file, offset + 6)
                file.write("\n")

    def resolveCounters(self, metric):
        for site in self.array.keys():
            if metric in self.array[site]:
                self.array[site][metric].resolveCounters()
                self.array[site][metric].delCounters()

    def resolveCountersDownOkWarnErr(self, metric):
        for site in self.array.keys():
            if metric in self.array[site]:
                if (( site[1:2] == '0' ) or ( site[1:2] == '1' )):
                   self.array[site][metric].resolveCountersDownOkWarnErr(0.90)
                else:
                   self.array[site][metric].resolveCountersDownOkWarnErr(0.80)
                self.array[site][metric].delCounters()

    def dropVersions(self, metric):
        for site in self.array.keys():
            if metric in self.array[site]:
                self.array[site][metric].delVersions()
# ########################################################################### #



class sswpTickets:
    'Ticket class for site metrics of the CMSSST site status display'

    def __init__(self):
        self.store = {}

    def add(self, site, ticketid, opentime):
        if site not in self.store:
            self.store[site] = []
        self.store[site].append( {'id': ticketid, 'date': opentime} )

    def getSummary(self, site, referenceTime):
        if site not in self.store:
            return [0, 0, 0]
        count = 0
        youngest = None
        oldest = None
        for ticket in self.store[site]:
            count += 1
            age = max(0, referenceTime - ticket['date'] )
            if (( youngest is None ) or ( age < youngest )):
                youngest = age
            if (( oldest is None ) or ( age > oldest )):
                oldest = age
        return [count, youngest, oldest]

    def getTickets(self, site):
        if site not in self.store:
            return []
        tList = []
        for ticket in self.store[site]:
            tList.append( [ticket['id'], ticket['date']] )
        return tList

    def write(self, file=sys.stdout, offset=0):
        off = "".ljust(offset)
        #
        for site in sorted(self.store.keys()):
            file.write("%s%s has GGUS ticket(s):\n" % (off, site))
            for ticket in self.store[site]:
                file.write("%s   %s with data %d = %s\n" % (off, ticket['id'],
                    ticket['date'], time.strftime("%Y-%m-%d %H:%M:%S",
                    time.gmtime(ticket['date']))))
# ########################################################################### #



glbLock = None
glbInfo = {}
glbTopology = None
glbTickets = None
glbSites = None
glbElements = None
glbFlavours = {'CE': "CE",
               'GLOBUS': "CE",
               'gLite-CE': "CE",
               'ARC-CE': "CE",
               'CREAM-CE': "CE",
               'org.opensciencegrid.htcondorce': "CE",
               'HTCONDOR-CE': "CE",
               'SE': "SE",
               'SRM': "SE",
               'SRMv2': "SE",
               'SRMv1': "SE",
               'globus-GRIDFTP': "SE",
               'GridFtp': "SE",
               'XRD': "XRD",
               'XROOTD': "XRD",
               'XRootD': "XRD",
               'XRootD.Redirector': "XRD",
               'XRootD origin server': "XRD",
               'XRootD component': "XRD",
               'perfSONAR': "perfSONAR",
               'net.perfSONAR.Bandwidth': "perfSONAR",
               'net.perfSONAR.Latency': "perfSONAR"}
# ########################################################################### #



def sswp_init():
    global glbLock
    glbLock = threading.Lock()

    global glbTopology
    global glbTickets
    global glbSites
    global glbElements
    URL_SSWB_BASE = 'http://cmssst.web.cern.ch/siteStatus/'
    FILENAME_MSG = './message.txt'

    # configure the message logger:
    # =============================
    logging.basicConfig(format='%(threadName)-10s %(message)s',
                        level=logging.INFO)

    # fill timestamp dictionary:
    # ==========================
    glbInfo['timestamp'] = int( time.time() )

    # base URL of site status web page location:
    # ==========================================
    glbInfo['url'] = URL_SSWB_BASE

    # check for message.txt file:
    # ===========================
    if ( os.path.isfile(FILENAME_MSG) ):
        if ( os.path.getsize(FILENAME_MSG) > 0 ):
           with open(FILENAME_MSG, 'r') as myfile:
              glbInfo['msg'] = myfile.read(256).replace('\n', '')

    # initialize global objects:
    # ==========================
    sswpVector.SetTimestamps( glbInfo['timestamp'] )
    glbTopology = sswpTopology()
    glbTickets = sswpTickets()
    glbSites = sswpArray()
    glbElements = sswpArray()



def sswp_vofeed():
    # ############################################################### #
    # fill sswp_sites site element array with grid element dictionary #
    # ############################################################### #
    URL_VOFEED = "http://dashb-cms-vo-feed.cern.ch/dashboard/request.py/cmssitemapbdii"

    # get list of grid elements and grid sites from the VO-feed:
    # ==========================================================
    logging.info("Querying VO-feed for site information")
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
            myFile = open("%s/cache_vofeed.xml_new" % SSWP_CACHE_DIR, 'w')
            try:
                myFile.write(myData)
                renameFlag = True
            except:
                renameFlag = False
            finally:
                myFile.close()
                del myFile
            if renameFlag:
                os.rename("%s/cache_vofeed.xml_new" % SSWP_CACHE_DIR,
                          "%s/cache_vofeed.xml" % SSWP_CACHE_DIR)
                logging.info("   cache of VO-feed updated")
            del renameFlag
        except:
            pass
    except:
        if 'stale' not in glbInfo:
            glbInfo['stale'] = "No/stale information (VO-feed"
        else:
            glbInfo['stale'] += ", VO-feed"
        logging.warning("   failed to fetch VO-feed data")
        try:
            myFile = open("%s/cache_vofeed.xml" % SSWP_CACHE_DIR, 'r')
            try:
                myData = myFile.read()
                logging.info("   using cached VO-feed data")
            except:
                logging.error("   failed to access cached VO-feed data")
                return
            finally:
                myFile.close()
                del myFile
        except:
            logging.error("   no VO-feed cache available")
            return
    finally:
        if urlHndl is not None:
            urlHndl.close()
    del urlHndl
    #
    # unpack XML data of the VO-feed:
    vofeed = ET.fromstring( myData )
    del myData
    #
    # loop over site elements (multiple entries per grid and CMS site possible):
    for atpsite in vofeed.findall('atp_site'):
        gridsite = atpsite.attrib['name']
        cmssite = None
        for group in atpsite.findall('group'):
            if 'type' in group.attrib:
                if ( group.attrib['type'] == "CMS_Site" ):
                    cmssite = group.attrib['name']
                    break
        if cmssite is not None:
            #logging.debug("CMS site %s associates grid site %s",
            #              cmssite, gridsite)
            # add CMS site to topology map:
            glbTopology.addSite(cmssite)
            # 
            for service in atpsite.findall('service'):
                if 'flavour' in service.attrib:
                    host = service.attrib['hostname'].lower()
                    type = service.attrib['flavour']
                    if 'production_status' in service.attrib:
                        prod = service.attrib['production_status'].lower()
                        if ( prod == "false" ):
                            glbTopology.addElement(cmssite, gridsite, host,
                                                   type, False)
                    glbTopology.addElement(cmssite, gridsite, host, type)
                    #logging.debug("   Element \"%s\" (%s)", host, type)



def sswp_ggus():
    # ########################################################### #
    # fill sswp_sites site ggus array with GGUS ticket informaton #
    # ########################################################### #
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
            myFile = open("%s/cache_ggus.xml_new" % SSWP_CACHE_DIR, 'w')
            try:
                myFile.write(myData)
                renameFlag = True
            except:
                renameFlag = False
            finally:
                myFile.close()
                del myFile
            if renameFlag:
                os.rename("%s/cache_ggus.xml_new" % SSWP_CACHE_DIR,
                          "%s/cache_ggus.xml" % SSWP_CACHE_DIR)
                logging.info("   cache of GGUS updated")
            del renameFlag
        except:
            pass
    except:
        if 'stale' not in glbInfo:
            glbInfo['stale'] = "No/stale information (GGUS"
        else:
            glbInfo['stale'] += ", GGUS"
        logging.warning("   failed to fetch GGUS ticket data")
        try:
            myFile = open("%s/cache_ggus.xml" % SSWP_CACHE_DIR, 'r')
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

    glbLock.acquire()

    # unpack XML data of GGUS:
    tickets = ET.fromstring( myData )
    del myData
    #
    # loop over ticket elements:
    for ticket in tickets.findall('ticket'):
        ticketid = ticket.find('Ticket-ID').text
        try:
            cmssite = ticket.find('CMS_Site').text
        except (KeyError, AttributeError):
            cmssite = None
        if not cmssite:
           continue
        created  = ticket.findtext('Creation_Date', '')     # time is in UTC
        ts = time.strptime(created + ' UTC', "%Y-%m-%d %H:%M:%S %Z")
        tis = calendar.timegm(ts)
        #logging.debug("CMS site %s has ticket %s (%d)", cmssite, ticketid, tis)
        glbTickets.add(cmssite, ticketid, tis)

    glbLock.release()



def sswp_osg_downtime():
    # ################################################################ #
    # fill sswp_sites site element arrays with OSG downtime informaton #
    # ################################################################ #
    URL_OSG_DOWNTIME = "http://my.opensciencegrid.org/rgdowntime/xml?summary_attrs_showrsvstatus=on&downtime_attrs_showpast=39&summary_attrs_showfqdn=on&all_resources=on&gridtype=on&gridtype_1=on&active=on&active_value=1&has_wlcg=on"

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
            myFile = open("%s/cache_osgdowntime.xml_new" % SSWP_CACHE_DIR, 'w')
            try:
                myFile.write(myData)
                renameFlag = True
            except:
                renameFlag = False
            finally:
                myFile.close()
                del myFile
            if renameFlag:
                os.rename("%s/cache_osgdowntime.xml_new" % SSWP_CACHE_DIR,
                          "%s/cache_osgdowntime.xml" % SSWP_CACHE_DIR)
                logging.info("   cache of OSG downtime updated")
            del renameFlag
        except:
            pass
    except:
        if 'stale' not in glbInfo:
            glbInfo['stale'] = "No/stale information (OSG downtime"
        else:
            glbInfo['stale'] += ", OSG downtime"
        logging.warning("   failed to fetch OSG downtime data")
        try:
            myFile = open("%s/cache_osgdowntime.xml" % SSWP_CACHE_DIR, 'r')
            try:
                myData = myFile.read()
                logging.info("   using cached OSG downtime data")
            except:
                logging.error("   failed to access cached OSG downtime data")
                return
            finally:
                myFile.close()
                del myFile
        except:
            logging.error("   no OSG downtime cache available")
            return
    finally:
        if urlHndl is not None:
            urlHndl.close()
    del urlHndl

    glbLock.acquire()

    # unpack XML data of the OSG downtime information:
    downtimes = ET.fromstring( myData )
    del myData
    #
    # loop over downtime-type (Past, Current, Future) elements:
    for downtypes in downtimes:
        # loop over downtime elements:
        for downtime in downtypes.findall('Downtime'):
            resourcegroup = downtime.find('ResourceGroup')
            if not resourcegroup:
                continue
            gridsite = resourcegroup.find('GroupName').text
            host = downtime.find('ResourceFQDN').text
            s_str = downtime.find('StartTime').text
            ts = time.strptime(s_str, "%b %d, %Y %H:%M %p %Z")
            start = calendar.timegm(ts)
            e_str = downtime.find('EndTime').text
            ts = time.strptime(e_str, "%b %d, %Y %H:%M %p %Z")
            end = calendar.timegm(ts)
            adhoc = downtime.find('Class').text
            severity = downtime.find('Severity').text
            if ( severity.lower() != 'outage' ):
                continue
            c_str = downtime.findtext('CreatedTime', default='Not Available')
            if ( c_str != 'Not Available' ):
                ts = time.strptime(c_str, "%b %d, %Y %H:%M %p %Z")
                create = calendar.timegm(ts)
                if ( create > start - 86400 ):
                    # 24 hour advanced notice required for scheduled downtimes
                    adhoc = 'Adhoc'
            if ( adhoc.lower() == 'scheduled' ):
                code = "d"
            else:
                code = "a"
            services = downtime.find('Services')
            if not services:
                continue
            for service in services.findall('Service'):
                type = service.find('Name').text
                host = host.lower()
                # check element belongs to a CMS site:
                type = glbTopology.verifyType(host, type)
                if type is None:
                    continue
                element = host + "/" + type
                #logging.debug(("   downtime %s (%s) at %s (%s,%s)\n" + \
                #          "            from %s = %d\n            to %s = %d"),
                #              host, type, gridsite, adhoc, severity,
                #              s_str, start, e_str, end)
                glbElements.fill15m('downtime', element, start, end, code)

    glbLock.release()



def sswp_egi_downtime():
    # ################################################################ #
    # fill sswp_sites site element arrays with EGI downtime informaton #
    # ################################################################ #
    ts1 = time.gmtime( glbInfo['timestamp'] - 39*24*60*60)
    ts2 = time.gmtime( glbInfo['timestamp'] + 8*24*60*60)
    URL_EGI_DOWNTIME = "https://goc.egi.eu/gocdbpi/public/?method=get_downtime&windowstart=%d-%02d-%02d&windowend=%d-%02d-%02d&scope=cms" % (ts1[0], ts1[1], ts1[2], ts2[0], ts2[1], ts2[2])

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
            myFile = open("%s/cache_egidowntime.xml_new" % SSWP_CACHE_DIR, 'w')
            try:
                myFile.write(myData)
                renameFlag = True
            except:
                renameFlag = False
            finally:
                myFile.close()
                del myFile
            if renameFlag:
                os.rename("%s/cache_egidowntime.xml_new" % SSWP_CACHE_DIR,
                          "%s/cache_egidowntime.xml" % SSWP_CACHE_DIR)
                logging.info("   cache of EGI downtime updated")
            del renameFlag
        except:
            pass
    except:
        if 'stale' not in glbInfo:
            glbInfo['stale'] = "No/stale information (EGI downtime"
        else:
            glbInfo['stale'] += ", EGI downtime"
        logging.warning("   failed to fetch EGI downtime data")
        try:
            myFile = open("%s/cache_egidowntime.xml" % SSWP_CACHE_DIR, 'r')
            try:
                myData = myFile.read()
                logging.info("   using cached EGI downtime data")
            except:
                logging.error("   failed to access cached EGI downtime data")
                return
            finally:
                myFile.close()
                del myFile
        except:
            logging.error("   no EGI downtime cache available")
            return
    finally:
        if urlHndl is not None:
            urlHndl.close()
    del urlHndl

    glbLock.acquire()

    # unpack XML data of the OSG downtime information:
    downtimes = ET.fromstring( myData )
    del myData
    #
    # loop over downtime elements:
    for downtime in downtimes.findall('DOWNTIME'):
        adhoc = downtime.attrib.get('CLASSIFICATION')
        host = downtime.find('HOSTNAME').text
        type = downtime.find('SERVICE_TYPE').text
        gridsite = downtime.find('HOSTED_BY').text
        severity = downtime.find('SEVERITY').text
        if ( severity.upper() != 'OUTAGE' ):
            continue
        start = int( downtime.find('START_DATE').text )
        end = int( downtime.find('END_DATE').text )
        s_str = downtime.find('FORMATED_START_DATE').text
        e_str = downtime.find('FORMATED_END_DATE').text
        host = host.lower()
        # check element belongs to a CMS site:
        type = glbTopology.verifyType(host, type)
        if type is None:
            continue
        element = host + "/" + type
        # set time period code:
        if ( adhoc.lower() == 'scheduled' ):
            code = "d"
        else:
            code = "a"
        #logging.debug(("   downtime %s (%s) at %s (%s,%s)\n" + \
        #               "            from %s = %d\n            to %s = %d"),
        #              host, type, gridsite, adhoc, severity,
        #              s_str, start, e_str, end)
        glbElements.fill15m('downtime', element, start, end, code)

    glbLock.release()



def sswp_site_downtime():
    # #################################################################### #
    # fill downtime vector of a site based on element downtime information #
    # #################################################################### #

    glbLock.acquire()

    logging.info("Composing site downtime information")
    for cmssite in sorted(glbTopology.sites()):
        # locate relevant downtime vectors:
        ceTuple = ()
        seTuple = ()
        xrdTuple = ()
        for element in glbTopology.getProdElements(cmssite):
            vector = glbElements.getVector('downtime', element)
            if vector is not None:
                host, type = element.split("/",1)
                type = sswpTopology.TypeGroup(type)
                if ( type == "CE" ):
                    ceTuple += (vector, )
                elif ( type == "SE" ):
                    seTuple += (vector, )
                elif ( type == "XROOTD" ):
                    xrdTuple += (vector, )
        #
        # evaluate site downtime status based on element downtime states:
        for bin in range( sswpVector.getDefaultBins15m() ):
            code = 'u'
            for vector in seTuple:
                binCode = vector.getBin(bin)
                if ( binCode == 'd' ):
                    # any SE in scheduled downtime is a scheduled site downtime
                    code = 'd'
                    break
                elif ( binCode == 'a' ):
                    code = 'a'
            if ( code != 'd' ):
                # count number of CEs belonging to site:
                ceTotal = glbTopology.countProdCEs(cmssite)
                if ( ceTotal > 0 ):
                    dCount = 0
                    aCount = 0
                    for vector in ceTuple:
                        binCode = vector.getBin(bin)
                        if ( binCode == 'd' ):
                            dCount += 1
                        elif ( binCode == 'a' ):
                            aCount += 1
                    if ( dCount == ceTotal ):
                        code = 'd'
                    elif ( dCount > 0 ):
                        code = 'p'
                    elif ( aCount == ceTotal ):
                        code = 'a'
            if (( code == 'u' ) or ( code == 'a' )):
                for vector in xrdTuple:
                    binCode = vector.getBin(bin)
                    if ( binCode == 'd' ):
                        code = 'p'
                        break
                    elif ( binCode == 'a' ):
                        code = 'a'
            if ( bin < sswpVector.getDefaultBins() ):
                glbSites.setBin('downtime', cmssite, bin, code)

            glbSites.setBin15m('summary', cmssite, bin, code)

    glbLock.release()



def sswp_ssb_SiteReadiness():
    # ################################################################### #
    # get metric data from the SSB-Dashboard and fill site/metric vectors #
    # ################################################################### #
    ts1 = time.gmtime( glbInfo['timestamp'] - 39*24*60*60)
    ts2 = time.gmtime( glbInfo['timestamp'] + 24*60*60)
    #
    URL_SSB_SITEREADINESS = "http://dashb-ssb.cern.ch/dashboard/request.py/getplotdata?columnid=234&time=custom&sites=all&clouds=all&batch=1&dateFrom=%s&dateTo=%s" % (time.strftime("%Y-%m-%d", ts1), time.strftime("%Y-%m-%d", ts2))

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
        #
        # update cache:
        try:
            myFile = open("%s/cache_ssbSiteReadiness.json_new" %
                          SSWP_CACHE_DIR, 'w')
            try:
                myFile.write(myData)
                renameFlag = True
            except:
                renameFlag = False
            finally:
                myFile.close()
                del myFile
            if renameFlag:
                os.rename("%s/cache_ssbSiteReadiness.json_new" % SSWP_CACHE_DIR,
                          "%s/cache_ssbSiteReadiness.json" % SSWP_CACHE_DIR)
                logging.info("   cache of SSB SiteReadiness updated")
            del renameFlag
        except:
            pass
    except:
        if 'stale' not in glbInfo:
            glbInfo['stale'] = "No/stale information (SSB SiteReadiness"
        else:
            glbInfo['stale'] += ", SSB SiteReadiness"
        logging.warning("   failed to fetch SSB SiteReadiness data")
        try:
            myFile = open("%s/cache_ssbSiteReadiness.json" % SSWP_CACHE_DIR,
                          'r')
            try:
                myData = myFile.read()
                logging.info("   using cached SSB SiteReadiness data")
            except:
                logging.error(("   failed to access cached SSB SiteReadiness" +
                               " data"))
                return
            finally:
                myFile.close()
                del myFile
        except:
            logging.error("   no SSB SiteReadiness cache available")
            return
    finally:
        if urlHndl is not None:
            urlHndl.close()
    del urlHndl

    glbLock.acquire()

    # unpack JSON data of SSB SiteReadiness information:
    sitereadiness = json.loads( myData )

    # truncate SiteReadiness at the end of yesterday
    ts = time.gmtime( glbInfo['timestamp'] )
    cutoff = calendar.timegm( ts[:3] + (0, 0, 0) + ts[6:] ) - 1

    for entry in sitereadiness['csvdata']:
        cmssite = entry['VOName']
        status = entry['Status']                 # Ok, Warning, Error, Downtime
        status = status.lower()
        if ( status == "ok" ):
            code = 'o'
        elif ( status == "warning" ):
            code = 'w'
        elif ( status == "error" ):
            code = 'e'
        elif ( status == "downtime" ):
            code = 'd'
        else:
            continue
        tstrng = entry['Time']
        ts = time.strptime(tstrng + ' UTC', "%Y-%m-%dT%H:%M:%S %Z")
        start = calendar.timegm(ts)
        tstrng = entry['EndTime']
        ts = time.strptime(tstrng + ' UTC', "%Y-%m-%dT%H:%M:%S %Z")
        end = min(cutoff, calendar.timegm(ts))
        #logging.debug("SR(%s) %s to %s = %s",
        #              cmssite, entry['Time'], tstrng, code)
        
        glbSites.fillCenter('SiteReadiness', cmssite, start, end, code)

        glbSites.fillCenter15m('summary', cmssite, start, end, code)

    glbLock.release()



def sswp_ssb_LifeStatus():
    # ####################################################################### #
    # get LifeStatus data from the SSB-Dashboard and fill site/metric vectors #
    # ####################################################################### #
    ts1 = time.gmtime( glbInfo['timestamp'] - 39*24*60*60)
    ts2 = time.gmtime( glbInfo['timestamp'] + 24*60*60)
    #
    URL_SSB_LIFESTATUS = "http://dashb-ssb.cern.ch/dashboard/request.py/getplotdata?columnid=235&time=custom&sites=all&clouds=all&batch=1&dateFrom=%s&dateTo=%s" % (time.strftime("%Y-%m-%d", ts1), time.strftime("%Y-%m-%d", ts2))

    # get LifeStatus data from the SSB dashboard:
    # ===========================================
    logging.info("Querying SSB for LifeStatus information")
    urlHndl = None
    try:
        request = urllib.request.Request(URL_SSB_LIFESTATUS,
                                         headers={'Accept':'application/json'})
        urlHndl = urllib.request.urlopen( request )
        myCharset = urlHndl.headers.get_content_charset()
        if myCharset is None:
            myCharset = "utf-8"
        myData = urlHndl.read().decode( myCharset )
        del(myCharset)
        #
        # update cache:
        try:
            myFile = open("%s/cache_ssbLifeStatus.json_new" % SSWP_CACHE_DIR,
                          'w')
            try:
                myFile.write(myData)
                renameFlag = True
            except:
                renameFlag = False
            finally:
                myFile.close()
                del myFile
            if renameFlag:
                os.rename("%s/cache_ssbLifeStatus.json_new" % SSWP_CACHE_DIR,
                          "%s/cache_ssbLifeStatus.json" % SSWP_CACHE_DIR)
                logging.info("   cache of SSB LifeStatus updated")
            del renameFlag
        except:
            pass
    except:
        if 'stale' not in glbInfo:
            glbInfo['stale'] = "No/stale information (SSB LifeStatus"
        else:
            glbInfo['stale'] += ", SSB LifeStatus"
        logging.warning("   failed to fetch SSB LifeStatus data")
        try:
            myFile = open("%s/cache_ssbLifeStatus.json" % SSWP_CACHE_DIR, 'r')
            try:
                myData = myFile.read()
                logging.info("   using cached SSB LifeStatus data")
            except:
                logging.warning(("   failed to access cached SSB LifeStatus " +
                                 "data"))
                return
            finally:
                myFile.close()
                del myFile
        except:
            logging.warning("   no SSB LifeStatus cache available")
            return
    finally:
        if urlHndl is not None:
            urlHndl.close()
    del urlHndl

    glbLock.acquire()

    # unpack JSON data of SSB LifeStatus information:
    lifestatus = json.loads( myData )

    # truncate LifeStatus at the end of today
    ts = time.gmtime( glbInfo['timestamp'] )
    cutoff = calendar.timegm( ts[:3] + (23, 59, 59) + ts[6:] )

    for entry in lifestatus['csvdata']:
        cmssite = entry['VOName']
        status = entry['Status']                # enabled, waiting_room, morgue
        status = status.lower()
        if ( status == "enabled" ):
            code = 'o'
        elif (( status == "waiting_room" ) or ( status == "waitingroom" )):
            code = 'W'
        elif ( status == "morgue" ):
            code = 'M'
        else:
            continue
        tstrng = entry['Time']
        ts = time.strptime(tstrng + ' UTC', "%Y-%m-%dT%H:%M:%S %Z")
        start = calendar.timegm(ts)
        tstrng = entry['EndTime']
        ts = time.strptime(tstrng + ' UTC', "%Y-%m-%dT%H:%M:%S %Z")
        end = min( cutoff, calendar.timegm(ts))
        #logging.debug("LS(%s) %s to %s = %s",
        #              cmssite, entry['Time'], tstrng, code)

        glbSites.fillCenter('LifeStatus', cmssite, start, end, code)

        if (( code == 'W' ) or ( code == 'M' )):
            glbSites.fillCenter15m('summary', cmssite, start, end, code)

    glbLock.release()



def sswp_old_site_summary():
    # ##################################################################### #
    # evaluate summary vectors based on downtime, SiteReadiness, LifeStatus #
    # ##################################################################### #

    glbLock.acquire()

    logging.info("Compiling site summary information")
    for cmssite in sorted(glbTopology.sites()):
        vector = glbSites.getVector('summary', cmssite)
        if vector is not None:
            vector.merge15min()

        # drop 15 min entries from downtime vector of site elements
        for element in glbTopology.getElements(cmssite):
            vector = glbElements.getVector('downtime', element)
            if vector is not None:
                vector.del15min()

    glbLock.release()



def sswp_ssb_manLifeStatus():
    # ################################################################## #
    # get manual LifeStatus data from the SSB-Dashboard and fill vectors #
    # ################################################################## #
    ts1 = time.gmtime( glbInfo['timestamp'] - 39*24*60*60 )
    ts2 = time.gmtime( glbInfo['timestamp'] + 8*24*60*60 )
    #
    URL_SSB_MANLIFESTATUS = "http://dashb-ssb.cern.ch/dashboard/request.py/getplotdata?columnid=232&time=custom&sites=all&clouds=all&batch=1&dateFrom=%s&dateTo=%s" % (time.strftime("%Y-%m-%d", ts1), time.strftime("%Y-%m-%d", ts2))

    # get manual LifeStatus data from the SSB dashboard:
    # ==================================================
    logging.info("Querying SSB for manual LifeStatus information")
    urlHndl = None
    try:
        request = urllib.request.Request(URL_SSB_MANLIFESTATUS,
                                         headers={'Accept':'application/json'})
        urlHndl = urllib.request.urlopen( request )
        myCharset = urlHndl.headers.get_content_charset()
        if myCharset is None:
            myCharset = "utf-8"
        myData = urlHndl.read().decode( myCharset )
        del(myCharset)
        #
        # update cache:
        try:
            myFile = open("%s/cache_ssbmanLifeStatus.json_new" % SSWP_CACHE_DIR,
                          'w')
            try:
                myFile.write(myData)
                renameFlag = True
            except:
                renameFlag = False
            finally:
                myFile.close()
                del myFile
            if renameFlag:
                os.rename("%s/cache_ssbmanLifeStatus.json_new" % SSWP_CACHE_DIR,
                          "%s/cache_ssbmanLifeStatus.json" % SSWP_CACHE_DIR)
                logging.info("   cache of SSB manual LifeStatus updated")
            del renameFlag
        except:
            pass
    except:
        if 'stale' not in glbInfo:
            glbInfo['stale'] = "No/stale information (SSB manual LifeStatus"
        else:
            glbInfo['stale'] += ", SSB manual LifeStatus"
        logging.warning("   failed to fetch SSB manual LifeStatus data")
        try:
            myFile = open("%s/cache_ssbmanLifeStatus.json" % SSWP_CACHE_DIR,
                          'r')
            try:
                myData = myFile.read()
                logging.info("   using cached SSB manual LifeStatus data")
            except:
                logging.error(("   failed to access cached SSB manual LifeSt" +
                               "atus data"))
                return
            finally:
                myFile.close()
                del myFile
        except:
            logging.error("   no SSB manual LifeStatus cache available")
            return
    finally:
        if urlHndl is not None:
            urlHndl.close()
    del urlHndl

    glbLock.acquire()

    # unpack JSON data of SSB manual LifeStatus information:
    manlifestatus = json.loads( myData )

    for entry in manlifestatus['csvdata']:
        cmssite = entry['VOName']
        status = entry['Status']                # enabled, waiting_room, morgue
        status = status.lower()
        if ( status == "enabled" ):
            code = 'o'
        elif (( status == "waiting_room" ) or ( status == "waitingroom" )):
            code = 'W'
        elif ( status == "morgue" ):
            code = 'M'
        else:
            continue
        tstrng = entry['Time']
        ts = time.strptime(tstrng + ' UTC', "%Y-%m-%dT%H:%M:%S %Z")
        start = calendar.timegm(ts)
        tstrng = entry['EndTime']
        ts = time.strptime(tstrng + ' UTC', "%Y-%m-%dT%H:%M:%S %Z")
        end = calendar.timegm(ts)
        #logging.info("mLS(%s) %s to %s = %s",
        #             cmssite, entry['Time'], tstrng, code))
        
        glbSites.fill('manualLifeStatus', cmssite, start, end, code)

    glbLock.release()



def sswp_ssb_ProdStatus():
    # ####################################################################### #
    # get ProdStatus data from the SSB-Dashboard and fill site/metric vectors #
    # ####################################################################### #
    ts1 = time.gmtime( glbInfo['timestamp'] - 39*24*60*60 )
    ts2 = time.gmtime( glbInfo['timestamp'] + 24*60*60 )
    #
    URL_SSB_PRODSTATUS = "http://dashb-ssb.cern.ch/dashboard/request.py/getplotdata?columnid=237&time=custom&sites=all&clouds=all&batch=1&dateFrom=%s&dateTo=%s" % (time.strftime("%Y-%m-%d", ts1), time.strftime("%Y-%m-%d", ts2))

    # get ProdStatus data from the SSB dashboard:
    # ===========================================
    logging.info("Querying SSB for ProdStatus information")
    urlHndl = None
    try:
        request = urllib.request.Request(URL_SSB_PRODSTATUS,
                                         headers={'Accept':'application/json'})
        urlHndl = urllib.request.urlopen( request )
        myCharset = urlHndl.headers.get_content_charset()
        if myCharset is None:
            myCharset = "utf-8"
        myData = urlHndl.read().decode( myCharset )
        del(myCharset)
        #
        # update cache:
        try:
            myFile = open("%s/cache_ssbProdStatus.json_new" % SSWP_CACHE_DIR,
                          'w')
            try:
                myFile.write(myData)
                renameFlag = True
            except:
                renameFlag = False
            finally:
                myFile.close()
                del myFile
            if renameFlag:
                os.rename("%s/cache_ssbProdStatus.json_new" % SSWP_CACHE_DIR,
                          "%s/cache_ssbProdStatus.json" % SSWP_CACHE_DIR)
                logging.info("   cache of SSB ProdStatus updated")
            del renameFlag
        except:
            pass
    except:
        if 'stale' not in glbInfo:
            glbInfo['stale'] = "No/stale information (SSB ProdStatus"
        else:
            glbInfo['stale'] += ", SSB ProdStatus"
        logging.warning("   failed to fetch SSB ProdStatus data")
        try:
            myFile = open("%s/cache_ssbProdStatus.json" % SSWP_CACHE_DIR, 'r')
            try:
                myData = myFile.read()
                logging.info("   using cached SSB ProdStatus data")
            except:
                logging.error("   failed to access cached SSB ProdStatus data")
                return
            finally:
                myFile.close()
                del myFile
        except:
            logging.error("   no SSB ProdStatus cache available")
            return
    finally:
        if urlHndl is not None:
            urlHndl.close()
    del urlHndl

    glbLock.acquire()

    # unpack JSON data of SSB ProdStatus information:
    prodstatus = json.loads( myData )

    # truncate ProdStatus at the end of today
    ts = time.gmtime( glbInfo['timestamp'] )
    cutoff = calendar.timegm( ts[:3] + (23, 59, 59) + ts[6:] )

    for entry in prodstatus['csvdata']:
        cmssite = entry['VOName']
        status = entry['Status']               # enabled, drain, test, disabled
        status = status.lower()
        if ( status == "enabled" ):
            code = 'o'
        elif (( status == "drain" ) or ( status == "test" )):
            code = 'w'
        elif ( status == "disabled" ):
            code = 'e'
        else:
            continue
        tstrng = entry['Time']
        ts = time.strptime(tstrng + ' UTC', "%Y-%m-%dT%H:%M:%S %Z")
        start = calendar.timegm(ts)
        tstrng = entry['EndTime']
        ts = time.strptime(tstrng + ' UTC', "%Y-%m-%dT%H:%M:%S %Z")
        end = min( cutoff, calendar.timegm(ts))
        #logging.debug("LS(%s) %s to %s = %s",
        #              cmssite, entry['Time'], tstrng, code)
        
        glbSites.fillCenter('ProdStatus', cmssite, start, end, code)

    glbLock.release()



def sswp_ssb_CrabStatus():
    # ####################################################################### #
    # get CrabStatus data from the SSB-Dashboard and fill site/metric vectors #
    # ####################################################################### #
    ts1 = time.gmtime( glbInfo['timestamp'] - 39*24*60*60 )
    ts2 = time.gmtime( glbInfo['timestamp'] + 24*60*60 )
    #
    URL_SSB_CRABSTATUS = "http://dashb-ssb.cern.ch/dashboard/request.py/getplotdata?columnid=242&time=custom&sites=all&clouds=all&batch=1&dateFrom=%s&dateTo=%s" % (time.strftime("%Y-%m-%d", ts1), time.strftime("%Y-%m-%d", ts2))

    # get CrabStatus data from the SSB dashboard:
    # ===========================================
    logging.info("Querying SSB for CrabStatus information")
    urlHndl = None
    try:
        request = urllib.request.Request(URL_SSB_CRABSTATUS,
                                         headers={'Accept':'application/json'})
        urlHndl = urllib.request.urlopen( request )
        myCharset = urlHndl.headers.get_content_charset()
        if myCharset is None:
            myCharset = "utf-8"
        myData = urlHndl.read().decode( myCharset )
        del(myCharset)
        #
        # update cache:
        try:
            myFile = open("%s/cache_ssbCrabStatus.json_new" % SSWP_CACHE_DIR,
                          'w')
            try:
                myFile.write(myData)
                renameFlag = True
            except:
                renameFlag = False
            finally:
                myFile.close()
                del myFile
            if renameFlag:
                os.rename("%s/cache_ssbCrabStatus.json_new" % SSWP_CACHE_DIR,
                          "%s/cache_ssbCrabStatus.json" % SSWP_CACHE_DIR)
                logging.info("   cache of SSB CrabStatus updated")
            del renameFlag
        except:
            pass
    except:
        if 'stale' not in glbInfo:
            glbInfo['stale'] = "No/stale information (SSB CrabStatus"
        else:
            glbInfo['stale'] += ", SSB CrabStatus"
        logging.warning("   failed to fetch SSB CrabStatus data")
        try:
            myFile = open("%s/cache_ssbCrabStatus.json" % SSWP_CACHE_DIR, 'r')
            try:
                myData = myFile.read()
                logging.info("   using cached SSB CrabStatus data")
            except:
                logging.error("   failed to access cached SSB CrabStatus data")
                return
            finally:
                myFile.close()
                del myFile
        except:
            logging.error("   no SSB CrabStatus cache available")
            return
    finally:
        if urlHndl is not None:
            urlHndl.close()
    del urlHndl

    glbLock.acquire()

    # unpack JSON data of SSB CrabStatus information:
    crabstatus = json.loads( myData )

    # truncate CrabStatus at the end of today
    ts = time.gmtime( glbInfo['timestamp'] )
    cutoff = calendar.timegm( ts[:3] + (23, 59, 59) + ts[6:] )

    for entry in crabstatus['csvdata']:
        cmssite = entry['VOName']
        status = entry['Status']                            # enabled, disabled
        status = status.lower()
        if ( status == "enabled" ):
            code = 'o'
        elif ( status == "disabled" ):
            code = 'e'
        else:
            continue
        tstrng = entry['Time']
        ts = time.strptime(tstrng + ' UTC', "%Y-%m-%dT%H:%M:%S %Z")
        start = calendar.timegm(ts)
        tstrng = entry['EndTime']
        ts = time.strptime(tstrng + ' UTC', "%Y-%m-%dT%H:%M:%S %Z")
        end = min(cutoff, calendar.timegm(ts))
        #logging.info("CS(%s) %s to %s = %s",
        #             cmssite, entry['Time'], tstrng, code)
        
        glbSites.fillCenter('CrabStatus', cmssite, start, end, code)

    glbLock.release()



def sswp_ssb_manProdStatus():
    # ################################################################## #
    # get manual ProdStatus data from the SSB-Dashboard and fill vectors #
    # ################################################################## #
    ts1 = time.gmtime( glbInfo['timestamp'] - 39*24*60*60 )
    ts2 = time.gmtime( glbInfo['timestamp'] + 8*24*60*60 )
    #
    URL_SSB_MANPRODSTATUS = "http://dashb-ssb.cern.ch/dashboard/request.py/getplotdata?columnid=238&time=custom&sites=all&clouds=all&batch=1&dateFrom=%s&dateTo=%s" % (time.strftime("%Y-%m-%d", ts1), time.strftime("%Y-%m-%d", ts2))

    # get manual ProdStatus data from the SSB dashboard:
    # ==================================================
    logging.info("Querying SSB for manual ProdStatus information")
    urlHndl = None
    try:
        request = urllib.request.Request(URL_SSB_MANPRODSTATUS,
                                         headers={'Accept':'application/json'})
        urlHndl = urllib.request.urlopen( request )
        myCharset = urlHndl.headers.get_content_charset()
        if myCharset is None:
            myCharset = "utf-8"
        myData = urlHndl.read().decode( myCharset )
        del(myCharset)
        #
        # update cache:
        try:
            myFile = open("%s/cache_ssbmanProdStatus.json_new" %
                          SSWP_CACHE_DIR, 'w')
            try:
                myFile.write(myData)
                renameFlag = True
            except:
                renameFlag = False
            finally:
                myFile.close()
                del myFile
            if renameFlag:
                os.rename("%s/cache_ssbmanProdStatus.json_new" % SSWP_CACHE_DIR,
                          "%s/cache_ssbmanProdStatus.json" % SSWP_CACHE_DIR)
                logging.info("   cache of SSB manual ProdStatus updated")
            del renameFlag
        except:
            pass
    except:
        if 'stale' not in glbInfo:
            glbInfo['stale'] = "No/stale information (SSB manual ProdStatus"
        else:
            glbInfo['stale'] += ", SSB manual ProdStatus"
        logging.warning("   failed to fetch SSB manual ProdStatus data")
        try:
            myFile = open("%s/cache_ssbmanProdStatus.json" % SSWP_CACHE_DIR,
                          'r')
            try:
                myData = myFile.read()
                logging.info("   using cached SSB manual ProdStatus data")
            except:
                logging.error(("   failed to access cached SSB manual ProdSt" +
                               "atus data"))
                return
            finally:
                myFile.close()
                del myFile
        except:
            logging.error("   no SSB manual ProdStatus cache available")
            return
    finally:
        if urlHndl is not None:
            urlHndl.close()
    del urlHndl

    glbLock.acquire()

    # unpack JSON data of SSB manual ProdStatus information:
    manprodstatus = json.loads( myData )

    for entry in manprodstatus['csvdata']:
        cmssite = entry['VOName']
        status = entry['Status']                # enabled, waiting_room, morgue
        status = status.lower()
        if ( status == "enabled" ):
            code = 'o'
        elif (( status == "drain" ) or ( status == "test" )):
            code = 'w'
        elif ( status == "disabled" ):
            code = 'e'
        else:
            continue
        tstrng = entry['Time']
        ts = time.strptime(tstrng + ' UTC', "%Y-%m-%dT%H:%M:%S %Z")
        start = calendar.timegm(ts)
        tstrng = entry['EndTime']
        ts = time.strptime(tstrng + ' UTC', "%Y-%m-%dT%H:%M:%S %Z")
        end = calendar.timegm(ts)
        #logging.debug("mPS(%s) %s to %s = %s",
        #              cmssite, entry['Time'], tstrng, code)

        glbSites.fill('manualProdStatus', cmssite, start, end, code)

    glbLock.release()



def sswp_ssb_manCrabStatus():
    # ################################################################## #
    # get manual CrabStatus data from the SSB-Dashboard and fill vectors #
    # ################################################################## #
    ts1 = time.gmtime( glbInfo['timestamp'] - 39*24*60*60 )
    ts2 = time.gmtime( glbInfo['timestamp'] + 8*24*60*60 )
    #
    URL_SSB_MANCRABSTATUS = "http://dashb-ssb.cern.ch/dashboard/request.py/getplotdata?columnid=239&time=custom&sites=all&clouds=all&batch=1&dateFrom=%s&dateTo=%s" % (time.strftime("%Y-%m-%d", ts1), time.strftime("%Y-%m-%d", ts2))

    # get manual CrabStatus data from the SSB dashboard:
    # ==================================================
    logging.info("Querying SSB for manual CrabStatus information")
    urlHndl = None
    try:
        request = urllib.request.Request(URL_SSB_MANCRABSTATUS,
                                         headers={'Accept':'application/json'})
        urlHndl = urllib.request.urlopen( request )
        myCharset = urlHndl.headers.get_content_charset()
        if myCharset is None:
            myCharset = "utf-8"
        myData = urlHndl.read().decode( myCharset )
        del(myCharset)
        #
        # update cache:
        try:
            myFile = open("%s/cache_ssbmanCrabStatus.json_new" %
                          SSWP_CACHE_DIR, 'w')
            try:
                myFile.write(myData)
                renameFlag = True
            except:
                renameFlag = False
            finally:
                myFile.close()
                del myFile
            if renameFlag:
                os.rename("%s/cache_ssbmanCrabStatus.json_new" % SSWP_CACHE_DIR,
                          "%/scache_ssbmanCrabStatus.json" % SSWP_CACHE_DIR)
                logging.info("   cache of SSB manual CrabStatus updated")
            del renameFlag
        except:
            pass
    except:
        if 'stale' not in glbInfo:
            glbInfo['stale'] = "No/stale information (SSB manual CrabStatus"
        else:
            glbInfo['stale'] += ", SSB manual CrabStatus"
        logging.warning("   failed to fetch SSB manual CrabStatus data")
        try:
            myFile = open("%s/cache_ssbmanCrabStatus.json" % SSWP_CACHE_DIR,
                          'r')
            try:
                myData = myFile.read()
                logging.info("   using cached SSB manual CrabStatus data")
            except:
                logging.error(("   failed to access cached SSB manual CrabSt" +
                               "atus data"))
                return
            finally:
                myFile.close()
                del myFile
        except:
            logging.error("   no SSB manual crabStatus cache available")
            return
    finally:
        if urlHndl is not None:
            urlHndl.close()
    del urlHndl

    glbLock.acquire()

    # unpack JSON data of SSB manual CrabStatus information:
    mancrabstatus = json.loads( myData )

    for entry in mancrabstatus['csvdata']:
        cmssite = entry['VOName']
        status = entry['Status']                # enabled, waiting_room, morgue
        status = status.lower()
        if ( status == "enabled" ):
            code = 'o'
        elif ( status == "disabled" ):
            code = 'e'
        else:
            continue
        tstrng = entry['Time']
        ts = time.strptime(tstrng + ' UTC', "%Y-%m-%dT%H:%M:%S %Z")
        start = calendar.timegm(ts)
        tstrng = entry['EndTime']
        ts = time.strptime(tstrng + ' UTC', "%Y-%m-%dT%H:%M:%S %Z")
        end = calendar.timegm(ts)
        #logging.debug("mPS(%s) %s to %s = %s",
        #              cmssite, entry['Time'], tstrng, code)

        glbSites.fill('manualCrabStatus', cmssite, start, end, code)

    glbLock.release()



def sswp_wlcg_sam_downtime():
    # ##################################################################### #
    # get SAM service status information from the WLCG monitoring dashboard #
    # ##################################################################### #
    ts1 = time.gmtime( glbInfo['timestamp'] - 39*24*60*60)
    ts2 = time.gmtime( glbInfo['timestamp'] + 8*24*60*60)
    #
    URL_WLCG_SAM_DOWNTIME = "http://wlcg-mon.cern.ch/dashboard/request.py/getplotdata?columnid=487&time=custom&sites=all&clouds=all&batch=1&dateFrom=%s&dateTo=%s" % (time.strftime("%Y-%m-%d", ts1), time.strftime("%Y-%m-%d", ts2))

    # get SAM downtime information from the WLCG monitorng dashboard:
    # ===============================================================
    logging.info("Querying WLCG for SAM downtime information")
    urlHndl = None
    try:
        request = urllib.request.Request(URL_WLCG_SAM_DOWNTIME,
                                         headers={'Accept':'application/json'})
        urlHndl = urllib.request.urlopen( request )
        myCharset = urlHndl.headers.get_content_charset()
        if myCharset is None:
            myCharset = "utf-8"
        myData = urlHndl.read().decode( myCharset )
        del(myCharset)
        #
        # update cache:
        try:
            myFile = open("%s/cache_wlcgSAMdowntime.json_new" % SSWP_CACHE_DIR,
                          'w')
            try:
                myFile.write(myData)
                renameFlag = True
            except:
                renameFlag = False
            finally:
                myFile.close()
                del myFile
            if renameFlag:
                os.rename("%s/cache_wlcgSAMdowntime.json_new" % SSWP_CACHE_DIR,
                          "%s/cache_wlcgSAMdowntime.json" % SSWP_CACHE_DIR)
                logging.info("   cache of WLCG SAM downtime updated")
            del renameFlag
        except:
            pass
    except:
        if 'stale' not in glbInfo:
            glbInfo['stale'] = "No/stale information (WLCG SAM downtime"
        else:
            glbInfo['stale'] += ", WLCG SAM downtime"
        logging.warning("   failed to fetch WLCG SAM downtime data")
        try:
            myFile = open("%s/cache_wlcgSAMdowntime.json" % SSWP_CACHE_DIR, 'r')
            try:
                myData = myFile.read()
                logging.info("   using cached WLCG SAM downtime data")
            except:
                logging.error("   failed to access cached WLCG SAM downtime")
                return
            finally:
                myFile.close()
                del myFile
        except:
            logging.error("   no WLCG SAM downtime cache available")
            return
    finally:
        if urlHndl is not None:
            urlHndl.close()
    del urlHndl

    glbLock.acquire()

    # parse JSON string:
    indx_s = myData.find('"csvdata":')
    indx_e = indx_s + 9
    while True:
        indx_s = myData.find('{', indx_e + 1)
        if ( indx_s < 0 ):
            break
        indx_e = myData.find('}', indx_s + 1)
        #
        indx_1 = myData.find('"VOName":', indx_s + 1, indx_e)
        indx_2 = myData.find('"Status":', indx_s + 1, indx_e)
        indx_3 = myData.find('"Time":', indx_s + 1, indx_e)
        indx_4 = myData.find('"EndTime":', indx_s + 1, indx_e)
        if (( indx_1 < 0 ) or ( indx_2 < 0 ) or
            ( indx_3 < 0 ) or ( indx_4 < 0 )):
            continue
        indx_1 += 9
        indx_2 += 9
        indx_3 += 7
        indx_4 += 10
        #
        indx_a = indx_1
        indx_o = myData.find(',', indx_1, indx_e) - 1
        if ( indx_o > 0 ):
            while (( myData[indx_a] == ' ' ) or ( myData[indx_a] == '"' )):
                indx_a += 1
            while (( myData[indx_o] == ' ' ) or ( myData[indx_o] == '"' )):
                indx_o -= 1
            if ( indx_a > indx_o ):
                continue
            service = myData[indx_a:indx_o+1]
            if ( service.find(" ") == -1 ):
                continue
            type, host = service.split(" ",1)
            host = host.lower()
            type = glbTopology.verifyType(host, type)
            if type is None:
                continue
            element = host + "/" + type
        #
        indx_a = indx_2
        indx_o = myData.find(',', indx_2, indx_e) - 1
        if ( indx_o > 0 ):
            while (( myData[indx_a] == ' ' ) or ( myData[indx_a] == '"' )):
                indx_a += 1
            while (( myData[indx_o] == ' ' ) or ( myData[indx_o] == '"' )):
                indx_o -= 1
            if ( indx_a > indx_o ):
                continue
            status = myData[indx_a:indx_o+1]         # null, OUTAGE UNSCHEDULED
            status = status.lower()                        # scheduled downtime
            if ( status == 'outage unscheduled' ):
                code = 'a'
            elif ( status == 'scheduled downtime' ):
                code = 'd'
            else:
                continue
        #
        indx_a = indx_3
        indx_o = myData.find(',', indx_3, indx_e) - 1
        if ( indx_o > 0 ):
            while (( myData[indx_a] == ' ' ) or ( myData[indx_a] == '"' )):
                indx_a += 1
            while (( myData[indx_o] == ' ' ) or ( myData[indx_o] == '"' )):
                indx_o -= 1
            if ( indx_a > indx_o ):
                continue
            tstrng1 = myData[indx_a:indx_o+1]
            ts = time.strptime(tstrng1 + ' UTC', "%Y-%m-%dT%H:%M:%S %Z")
            start = calendar.timegm(ts)
        #
        indx_a = indx_4
        indx_o = myData.find(',', indx_4, indx_e) - 1
        if ( indx_o > 0 ):
            while (( myData[indx_a] == ' ' ) or ( myData[indx_a] == '"' )):
                indx_a += 1
            while (( myData[indx_o] == ' ' ) or ( myData[indx_o] == '"' )):
                indx_o -= 1
            if ( indx_a > indx_o ):
                continue
            tstrng2 = myData[indx_a:indx_o+1]
            ts = time.strptime(tstrng2 + ' UTC', "%Y-%m-%dT%H:%M:%S %Z")
            end = calendar.timegm(ts)
        #logging.debug("WLCG SAM downtime(%s) %s to %s = %s",
        #              element, tstrng1, tstrng2, code)

        glbElements.fill('wlcgSAMdowntime', element, start, end, code)

    glbLock.release()



def sswp_wlcg_sam_services():
    # #################################################################### #
    # get SAM service status information from the WLCG monitorng dashboard #
    # #################################################################### #
    ELEMENT_METRICES = [{'no': 547, 'desc': "CREAM-CEs"},
                        {'no': 550, 'desc': "ARC-CEs"},
                        {'no': 1382, 'desc': "HTCONDOR-CEs"},
                        {'no': 1438, 'desc': "GLOBUS-CEs"},
                        {'no': 1442, 'desc': "SRM"},
                        {'no': 1494, 'desc': "XROOTD"}]
    #
    ts1 = time.gmtime( glbInfo['timestamp'] - 39*24*60*60)
    ts2 = time.gmtime( glbInfo['timestamp'] + 24*60*60)
    #
    for metric in ELEMENT_METRICES:
        URL_WLCG_SAM_SRV = "http://wlcg-mon.cern.ch/dashboard/request.py/getplotdata?columnid=%u&time=custom&sites=all&clouds=all&batch=1&dateFrom=%s&dateTo=%s" % (metric['no'], time.strftime("%Y-%m-%d", ts1), time.strftime("%Y-%m-%d", ts2))
        fid = "srv" + metric['desc'].split("-",1)[0]
    
        # get SAM service status information from the WLCG monitorng dashboard:
        # =====================================================================
        logging.info("Querying WLCG for service %s SAM status information",
                     metric['desc'])
        urlHndl = None
        try:
            request = urllib.request.Request(URL_WLCG_SAM_SRV,
                                         headers={'Accept':'application/json'})
            urlHndl = urllib.request.urlopen( request )
            myCharset = urlHndl.headers.get_content_charset()
            if myCharset is None:
                myCharset = "utf-8"
            myData = urlHndl.read().decode( myCharset )
            del(myCharset)
            #
            # update cache:
            try:
                myFile = open("%s/cache_wlcgSAM%s.json_new" %
                              (SSWP_CACHE_DIR, fid), 'w')
                try:
                    myFile.write(myData)
                    renameFlag = True
                except:
                    renameFlag = False
                finally:
                    myFile.close()
                    del myFile
                if renameFlag:
                    os.rename("%s/cache_wlcgSAM%s.json_new" %
                              (SSWP_CACHE_DIR, fid),
                              "%s/cache_wlcgSAM%s.json" %
                              (SSWP_CACHE_DIR, fid))
                    logging.info(("   cache of WLCG service %s SAM status up" +
                                  "dated"), metric['desc'])
                del renameFlag
            except:
                pass
        except:
            if 'stale' not in glbInfo:
                glbInfo['stale'] = ("No/stale information (WLCG service %s" + \
                    " SAM status") % metric['desc']
            else:
                glbInfo['stale'] += (", WLCG service %s SAM status" %
                    metric['desc'])
            logging.warning(("   failed to fetch WLCG service %s SAM status " +
                             "data"), metric['desc'])
            try:
                myFile = open("%s/cache_wlcgSAM%s.json" % (SSWP_CACHE_DIR, fid),
                              'r')
                try:
                    myData = myFile.read()
                    logging.info(("   using cached WLCG service %s SAM statu" +
                                  "s data"), metric['desc'])
                except:
                    logging.error(("   failed to access cached WLCG service " +
                                   "%s SAM status data"), metric['desc'])
                    return
                finally:
                    myFile.close()
                    del myFile
            except:
                logging.error(("   no WLCG service %s SAM status cache avail" +
                               "able"), metric['desc'])
                return
        finally:
            if urlHndl is not None:
                urlHndl.close()
        del urlHndl

        glbLock.acquire()

        # parse JSON string:
        indx_s = myData.find('"csvdata":')
        indx_e = indx_s + 9
        while True:
            indx_s = myData.find('{', indx_e + 1)
            if ( indx_s < 0 ):
                break
            indx_e = myData.find('}', indx_s + 1)
            #
            indx_1 = myData.find('"VOName":', indx_s + 1, indx_e)
            indx_2 = myData.find('"Status":', indx_s + 1, indx_e)
            indx_3 = myData.find('"Time":', indx_s + 1, indx_e)
            indx_4 = myData.find('"EndTime":', indx_s + 1, indx_e)
            if (( indx_1 < 0 ) or ( indx_2 < 0 ) or
                ( indx_3 < 0 ) or ( indx_4 < 0 )):
                continue
            indx_1 += 9
            indx_2 += 9
            indx_3 += 7
            indx_4 += 10
            #
            indx_a = indx_1
            indx_o = myData.find(',', indx_1, indx_e) - 1
            if ( indx_o > 0 ):
                while (( myData[indx_a] == ' ' ) or ( myData[indx_a] == '"' )):
                    indx_a += 1
                while (( myData[indx_o] == ' ' ) or ( myData[indx_o] == '"' )):
                    indx_o -= 1
                if ( indx_a > indx_o ):
                    continue
                service = myData[indx_a:indx_o+1]
                if ( service.find(" ") == -1 ):
                    continue
                type, host = service.split(" ",1)
                host = host.lower()
                type = glbTopology.verifyType(host, type)
                if type is None:
                    continue
                element = host + "/" + type
            #
            indx_a = indx_2
            indx_o = myData.find(',', indx_2, indx_e) - 1
            if ( indx_o > 0 ):
                while (( myData[indx_a] == ' ' ) or ( myData[indx_a] == '"' )):
                    indx_a += 1
                while (( myData[indx_o] == ' ' ) or ( myData[indx_o] == '"' )):
                    indx_o -= 1
                if ( indx_a > indx_o ):
                    continue
                status = myData[indx_a:indx_o+1]        # OK, WARNING, CRITICAL
                if ( status == 'OK' ):                                # UNKNOWN
                    code = 'o'
                elif ( status == 'WARNING' ):
                    code = 'w'
                elif ( status == 'CRITICAL' ):
                    code = 'e'
                else:
                    continue
            #
            indx_a = indx_3
            indx_o = myData.find(',', indx_3, indx_e) - 1
            if ( indx_o > 0 ):
                while (( myData[indx_a] == ' ' ) or ( myData[indx_a] == '"' )):
                    indx_a += 1
                while (( myData[indx_o] == ' ' ) or ( myData[indx_o] == '"' )):
                    indx_o -= 1
                if ( indx_a > indx_o ):
                    continue
                tstrng1 = myData[indx_a:indx_o+1]
                ts = time.strptime(tstrng1 + ' UTC', "%Y-%m-%dT%H:%M:%S %Z")
                start = calendar.timegm(ts)
            #
            indx_a = indx_4
            indx_o = myData.find(',', indx_4, indx_e) - 1
            if ( indx_o > 0 ):
                while (( myData[indx_a] == ' ' ) or ( myData[indx_a] == '"' )):
                    indx_a += 1
                while (( myData[indx_o] == ' ' ) or ( myData[indx_o] == '"' )):
                    indx_o -= 1
                if ( indx_a > indx_o ):
                    continue
                tstrng2 = myData[indx_a:indx_o+1]
                ts = time.strptime(tstrng2 + ' UTC', "%Y-%m-%dT%H:%M:%S %Z")
                end = calendar.timegm(ts)
            #logging.debug("WLCG service SAM(%s) %s to %s = %s",
            #              element, tstrng1, tstrng2, code)

            glbElements.fillCounters('wlcgSAMservice', element,
                start, min(glbInfo['timestamp'], end), code)

        glbLock.release()

    glbLock.acquire()
    glbElements.resolveCounters('wlcgSAMservice')
    glbLock.release()



def sswp_wlcg_sam_site():
    # ################################################################# #
    # get site SAM status information from the WLCG monitorng dashboard #
    # ################################################################# #
    ts1 = time.gmtime( glbInfo['timestamp'] - 39*24*60*60)
    ts2 = time.gmtime( glbInfo['timestamp'] + 24*60*60)
    #
    URL_WLCG_SAM_SITE = "http://wlcg-mon.cern.ch/dashboard/request.py/getplotdata?columnid=745&time=custom&sites=all&clouds=all&batch=1&dateFrom=%s&dateTo=%s" % (time.strftime("%Y-%m-%d", ts1), time.strftime("%Y-%m-%d", ts2))

    # get site SAM status information from the WLCG monitorng dashboard:
    # ==================================================================
    logging.info("Querying WLCG for site SAM status information")
    urlHndl = None
    try:
        request = urllib.request.Request(URL_WLCG_SAM_SITE,
                                         headers={'Accept':'application/json'})
        urlHndl = urllib.request.urlopen( request )
        myCharset = urlHndl.headers.get_content_charset()
        if myCharset is None:
            myCharset = "utf-8"
        myData = urlHndl.read().decode( myCharset )
        del(myCharset)
        #
        # update cache:
        try:
            myFile = open("%s/cache_wlcgSAMsite.json_new" % SSWP_CACHE_DIR, 'w')
            try:
                myFile.write(myData)
                renameFlag = True
            except:
                renameFlag = False
            finally:
                myFile.close()
                del myFile
            if renameFlag:
                os.rename("%s/cache_wlcgSAMsite.json_new" % SSWP_CACHE_DIR,
                          "%s/cache_wlcgSAMsite.json" % SSWP_CACHE_DIR)
                logging.info("   cache of WLCG site SAM status updated")
            del renameFlag
        except:
            pass
    except:
        if 'stale' not in glbInfo:
            glbInfo['stale'] = "No/stale information (WLCG site SAM status"
        else:
            glbInfo['stale'] += ", WLCG site SAM status"
        logging.warning("   failed to fetch WLCG site SAM status data")
        try:
            myFile = open("%s/cache_wlcgSAMsite.json" % SSWP_CACHE_DIR, 'r')
            try:
                myData = myFile.read()
                logging.info("   using cached WLCG site SAM status data")
            except:
                logging.error(("   failed to access cached WLCG site SAM sta" +
                               "tus data"))
                return
            finally:
                myFile.close()
                del myFile
        except:
            logging.error("   no WLCG site SAM status cache available")
            return
    finally:
        if urlHndl is not None:
            urlHndl.close()
    del urlHndl

    glbLock.acquire()

    # parse JSON string:
    indx_s = myData.find('"csvdata":')
    indx_e = indx_s + 9
    while True:
        indx_s = myData.find('{', indx_e + 1)
        if ( indx_s < 0 ):
            break
        indx_e = myData.find('}', indx_s + 1)
        #
        indx_1 = myData.find('"VOName":', indx_s + 1, indx_e)
        indx_2 = myData.find('"Status":', indx_s + 1, indx_e)
        indx_3 = myData.find('"Time":', indx_s + 1, indx_e)
        indx_4 = myData.find('"EndTime":', indx_s + 1, indx_e)
        if (( indx_1 < 0 ) or ( indx_2 < 0 ) or
            ( indx_3 < 0 ) or ( indx_4 < 0 )):
            continue
        indx_1 += 9
        indx_2 += 9
        indx_3 += 7
        indx_4 += 10
        #
        indx_a = indx_1
        indx_o = myData.find(',', indx_1, indx_e) - 1
        if ( indx_o > 0 ):
            while (( myData[indx_a] == ' ' ) or ( myData[indx_a] == '"' )):
                indx_a += 1
            while (( myData[indx_o] == ' ' ) or ( myData[indx_o] == '"' )):
                indx_o -= 1
            if ( indx_a > indx_o ):
                continue
            cmssite = myData[indx_a:indx_o+1]
            if (( cmssite[0:1] != "T") or (not (cmssite[1:2]).isdigit()) or
                ( cmssite[2:3] != "_" ) or ( cmssite[5:6] != "_" )):
                continue
        #
        indx_a = indx_2
        indx_o = myData.find(',', indx_2, indx_e) - 1
        if ( indx_o > 0 ):
            while (( myData[indx_a] == ' ' ) or ( myData[indx_a] == '"' )):
                indx_a += 1
            while (( myData[indx_o] == ' ' ) or ( myData[indx_o] == '"' )):
                indx_o -= 1
            if ( indx_a > indx_o ):
                continue
            status = myData[indx_a:indx_o+1]            # OK, WARNING, CRITICAL
            if ( status == 'OK' ):                          # DOWNTIME, UNKNOWN
                code = 'o'
            elif ( status == 'WARNING' ):
                code = 'w'
            elif ( status == 'CRITICAL' ):
                code = 'e'
            elif ( status == 'DOWNTIME' ):
                code = 'd'
            else:
                continue
        #
        indx_a = indx_3
        indx_o = myData.find(',', indx_3, indx_e) - 1
        if ( indx_o > 0 ):
            while (( myData[indx_a] == ' ' ) or ( myData[indx_a] == '"' )):
                indx_a += 1
            while (( myData[indx_o] == ' ' ) or ( myData[indx_o] == '"' )):
                indx_o -= 1
            if ( indx_a > indx_o ):
                continue
            tstrng1 = myData[indx_a:indx_o+1]
            ts = time.strptime(tstrng1 + ' UTC', "%Y-%m-%dT%H:%M:%S %Z")
            start = calendar.timegm(ts)
        #
        indx_a = indx_4
        indx_o = myData.find(',', indx_4, indx_e) - 1
        if ( indx_o > 0 ):
            while (( myData[indx_a] == ' ' ) or ( myData[indx_a] == '"' )):
                indx_a += 1
            while (( myData[indx_o] == ' ' ) or ( myData[indx_o] == '"' )):
                indx_o -= 1
            if ( indx_a > indx_o ):
                continue
            tstrng2 = myData[indx_a:indx_o+1]
            ts = time.strptime(tstrng2 + ' UTC', "%Y-%m-%dT%H:%M:%S %Z")
            end = calendar.timegm(ts)
        #logging.debug("WLCG site SAM(%s) %s to %s = %s",
        #              cmssite, tstrng1, tstrng2, code)

        glbSites.fillCounters('wlcgSAMsite', cmssite,
            start, min(glbInfo['timestamp'], end), code)

    glbSites.resolveCountersDownOkWarnErr('wlcgSAMsite')

    glbLock.release()



def sswp_ssb_HammerCloud15min():
    # #################################################################### #
    # get Hammer Cloud 15 min data from the SSB-Dashboard and fill vectors #
    # #################################################################### #
    ts1 = time.gmtime( glbInfo['timestamp'] - 39*24*60*60)
    ts2 = time.gmtime( glbInfo['timestamp'] + 24*60*60)
    #
    URL_SSB_HAMMERCLOUD15M = "http://dashb-ssb.cern.ch/dashboard/request.py/getplotdata?columnid=217&time=custom&sites=all&clouds=all&batch=1&dateFrom=%s&dateTo=%s" % (time.strftime("%Y-%m-%d", ts1), time.strftime("%Y-%m-%d", ts2))

    # get HammerCloud 15 min data from the SSB dashboard:
    # ===================================================
    logging.info("Querying SSB for HammerCloud 15 min information")
    urlHndl = None
    try:
        request = urllib.request.Request(URL_SSB_HAMMERCLOUD15M,
                                         headers={'Accept':'application/json'})
        urlHndl = urllib.request.urlopen( request )
        myCharset = urlHndl.headers.get_content_charset()
        if myCharset is None:
            myCharset = "utf-8"
        myData = urlHndl.read().decode( myCharset )
        del myCharset
        #
        # update cache:
        try:
            myFile = open("%s/cache_ssbHammerCloud15m.json_new" %
                          SSWP_CACHE_DIR, 'w')
            try:
                myFile.write(myData)
                renameFlag = True
            except:
                renameFlag = False
            finally:
                myFile.close()
                del myFile
            if renameFlag:
                os.rename("%s/cache_ssbHammerCloud15m.json_new" %
                          SSWP_CACHE_DIR,
                          "%s/cache_ssbHammerCloud15m.json" % SSWP_CACHE_DIR)
                logging.info("   cache of SSB HammerCloud 15 min updated")
            del renameFlag
        except:
            pass
    except BaseException as excptn:
        if 'stale' not in glbInfo:
            glbInfo['stale'] = "No/stale information (SSB HammerCloud 15 min"
        else:
            glbInfo['stale'] += ", SSB HammerCloud 15 min"
        logging.warning("   failed to fetch SSB HammerCloud 15 min data")
        logging.exception(excptn)
        try:
            myFile = open("%s/cache_ssbHammerCloud15m.json" % SSWP_CACHE_DIR,
                          'r')
            try:
                myData = myFile.read()
                logging.info("   using cached SSB HammerCloud 15 min data")
            except:
                logging.error(("   failed to access cached SSB HammerCloud 1" +
                               "5 min data"))
                return
            finally:
                myFile.close()
                del myFile
        except:
            logging.error("   no SSB HammerCloud 15 min cache available")
            return
    finally:
        if urlHndl is not None:
            urlHndl.close()
    del urlHndl

    glbLock.acquire()

    # parse JSON string:
    indx_s = myData.find('"csvdata":')
    indx_e = indx_s + 9
    while True:
        indx_s = myData.find('{', indx_e + 1)
        if ( indx_s < 0 ):
            break
        indx_e = myData.find('}', indx_s + 1)
        #
        indx_1 = myData.find('"VOName":', indx_s + 1, indx_e)
        indx_2 = myData.find('"COLORNAME":', indx_s + 1, indx_e)
        indx_3 = myData.find('"Time":', indx_s + 1, indx_e)
        indx_4 = myData.find('"EndTime":', indx_s + 1, indx_e)
        if (( indx_1 < 0 ) or ( indx_2 < 0 ) or
            ( indx_3 < 0 ) or ( indx_4 < 0 )):
            continue
        indx_1 += 9
        indx_2 += 12
        indx_3 += 7
        indx_4 += 10
        #
        indx_a = indx_1
        indx_o = myData.find(',', indx_1, indx_e) - 1
        if ( indx_o > 0 ):
            while (( myData[indx_a] == ' ' ) or ( myData[indx_a] == '"' )): 
                indx_a += 1
            while (( myData[indx_o] == ' ' ) or ( myData[indx_o] == '"' )):
                indx_o -= 1
            if ( indx_a > indx_o ):
                continue
            cmssite = myData[indx_a:indx_o+1]
        #
        indx_a = indx_2
        indx_o = myData.find(',', indx_2, indx_e) - 1
        if ( indx_o > 0 ):
            while (( myData[indx_a] == ' ' ) or ( myData[indx_a] == '"' )):
                indx_a += 1
            while (( myData[indx_o] == ' ' ) or ( myData[indx_o] == '"' )):
                indx_o -= 1
            if ( indx_a > indx_o ):
                continue
            status = myData[indx_a:indx_o+1]        # green, yellow, red, white
            if (( status == 'green' ) or ( status == 'cOk' )):
                code = 'o'
            elif ( status == 'yellow,' ):
                code = 'w'
            elif (( status == 'red' ) or ( status == 'cNotOk' )):
                code = 'e'
            else:
                continue
        #
        indx_a = indx_3
        indx_o = myData.find(',', indx_3, indx_e) - 1
        if ( indx_o > 0 ):
            while (( myData[indx_a] == ' ' ) or ( myData[indx_a] == '"' )):
                indx_a += 1
            while (( myData[indx_o] == ' ' ) or ( myData[indx_o] == '"' )):
                indx_o -= 1
            if ( indx_a > indx_o ):
                continue
            tstrng1 = myData[indx_a:indx_o+1]
            ts = time.strptime(tstrng1 + ' UTC', "%Y-%m-%dT%H:%M:%S %Z")
            start = calendar.timegm(ts)
        #
        indx_a = indx_4
        indx_o = myData.find(',', indx_4, indx_e) - 1
        if ( indx_o > 0 ):
            while (( myData[indx_a] == ' ' ) or ( myData[indx_a] == '"' )):
                indx_a += 1
            while (( myData[indx_o] == ' ' ) or ( myData[indx_o] == '"' )):
                indx_o -= 1
            if ( indx_a > indx_o ):
                continue
            tstrng2 = myData[indx_a:indx_o+1]
            ts = time.strptime(tstrng2 + ' UTC', "%Y-%m-%dT%H:%M:%S %Z")
            end = calendar.timegm(ts)
        #logging.debug("HC15min(%s) %s to %s = %s",
        #              cmssite, tstrng1, tstrng2, code)

        glbSites.fillCounters('HC15min', cmssite,
            start, min(glbInfo['timestamp'], end), code)

    glbSites.resolveCountersDownOkWarnErr('HC15min')

    glbLock.release()



def ssdw_monit_SAM_HC_FTS_SR():
    # ############################################################## #
    # get SAM,HC,FTS,SR data from MonIT/HDFS and fill metric vectors #
    # ############################################################## #
    HDFS_PREFIX = "/project/monitoring/archive/cmssst/raw/ssbmetric"
    #
    tis_start = sswpVector.GetTimestamps()
    #
    oneDay = 86400
    now = int( time.time() )
    sixDaysAgo = calendar.timegm( time.gmtime(now - (6 * oneDay)) )
    startLclTmpArea = calendar.timegm( time.localtime( sixDaysAgo ) )
    #
    midnight = ( int( now / 86400 ) * 86400 )
    limitLclTmpArea = calendar.timegm( time.localtime( midnight + 86399 ) )


    # prepare HDFS subdirectory list:
    # ===============================
    logging.info("Retrieving SAM,HC,FTS,SR docs from MonIT HDFS")
    #
    dirList = set()
    # 1 day directories of metrics that go into SiteReadiness:
    for dirDay in range(tis_start['month'], tis_start['fweek'], oneDay):
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
    # 6 hour bin directories of previous month:
    for dirDay in range(tis_start['month'], tis_start['pweek'], oneDay):
        dirList.add( time.strftime("/sam6hour/%Y/%m/%d",
                                                       time.gmtime( dirDay )) )
        dirList.add( time.strftime("/hc6hour/%Y/%m/%d",
                                                       time.gmtime( dirDay )) )
        dirList.add( time.strftime("/fts6hour/%Y/%m/%d",
                                                       time.gmtime( dirDay )) )
        dirList.add( time.strftime("/sr6hour/%Y/%m/%d",
                                                       time.gmtime( dirDay )) )
    for dirDay in range(startLclTmpArea, limitLclTmpArea, oneDay):
        dirList.add( time.strftime("/sam6hour/%Y/%m/%d.tmp",
                                                       time.gmtime( dirDay )) )
        dirList.add( time.strftime("/hc6hour/%Y/%m/%d.tmp",
                                                       time.gmtime( dirDay )) )
        dirList.add( time.strftime("/fts6hour/%Y/%m/%d.tmp",
                                                       time.gmtime( dirDay )) )
        dirList.add( time.strftime("/sr6hour/%Y/%m/%d.tmp",
                                                       time.gmtime( dirDay )) )
    #
    # 1 hour bin directories of previous week:
    for dirDay in range(tis_start['pweek'], tis_start['yrday'], oneDay):
        dirList.add( time.strftime("/sam1hour/%Y/%m/%d",
                                                       time.gmtime( dirDay )) )
        dirList.add( time.strftime("/hc1hour/%Y/%m/%d",
                                                       time.gmtime( dirDay )) )
        dirList.add( time.strftime("/fts1hour/%Y/%m/%d",
                                                       time.gmtime( dirDay )) )
        dirList.add( time.strftime("/sr1hour/%Y/%m/%d",
                                                       time.gmtime( dirDay )) )
    for dirDay in range(startLclTmpArea, limitLclTmpArea, oneDay):
        dirList.add( time.strftime("/sam1hour/%Y/%m/%d.tmp",
                                                       time.gmtime( dirDay )) )
        dirList.add( time.strftime("/hc1hour/%Y/%m/%d.tmp",
                                                       time.gmtime( dirDay )) )
        dirList.add( time.strftime("/fts1hour/%Y/%m/%d.tmp",
                                                       time.gmtime( dirDay )) )
        dirList.add( time.strftime("/sr1hour/%Y/%m/%d.tmp",
                                                       time.gmtime( dirDay )) )
    #
    # 15 min bin directory of yesterday and today:
    dirList.add( time.strftime("/sam15min/%Y/%m/%d",
                                           time.gmtime( tis_start['yrday'] )) )
    dirList.add( time.strftime("/sam15min/%Y/%m/%d",
                                           time.gmtime( tis_start['today'] )) )
    dirList.add( time.strftime("/hc15min/%Y/%m/%d",
                                           time.gmtime( tis_start['yrday'] )) )
    dirList.add( time.strftime("/hc15min/%Y/%m/%d",
                                           time.gmtime( tis_start['today'] )) )
    dirList.add( time.strftime("/fts15min/%Y/%m/%d",
                                           time.gmtime( tis_start['yrday'] )) )
    dirList.add( time.strftime("/fts15min/%Y/%m/%d",
                                           time.gmtime( tis_start['today'] )) )
    dirList.add( time.strftime("/sr15min/%Y/%m/%d",
                                           time.gmtime( tis_start['yrday'] )) )
    dirList.add( time.strftime("/sr15min/%Y/%m/%d",
                                           time.gmtime( tis_start['today'] )) )
    for dirDay in range(startLclTmpArea, limitLclTmpArea, oneDay):
        dirList.add( time.strftime("/sam15min/%Y/%m/%d.tmp",
                                                       time.gmtime( dirDay )) )
        dirList.add( time.strftime("/hc15min/%Y/%m/%d.tmp",
                                                       time.gmtime( dirDay )) )
        dirList.add( time.strftime("/fts15min/%Y/%m/%d.tmp",
                                                       time.gmtime( dirDay )) )
        dirList.add( time.strftime("/sr15min/%Y/%m/%d.tmp",
                                                       time.gmtime( dirDay )) )
    #
    dirList = sorted( dirList )


    vrsnDict = {}
    jsonList = []
    updateCache = True
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
                                if ( metric[-4:] == "1day" ):
                                    if (( metric[:3] == "sam" ) and
                                        ( myJson['data']['type'] == "site" )):
                                        label = "SAM1day"
                                        site = myJson['data']['name']
                                    elif ( metric[:2] == "hc" ):
                                        label = "HC1day"
                                        if 'name' not in myJson['data']:
                                            myJson['data']['name'] = myJson['data']['site']
                                        site = myJson['data']['name']
                                    elif (( metric[:3] == "fts" ) and
                                          ( myJson['data']['type'] == "site" )):
                                        label = "FTS1day"
                                        site = myJson['data']['name']
                                    elif ( metric[:2] == "sr" ):
                                        label = "SR1day"
                                        site = myJson['data']['name']
                                    else:
                                        continue
                                    period = "1day"
                                elif ( metric[:3] == "sam" ):
                                    if ( myJson['data']['type'] == "site" ):
                                        label = "SAMsite"
                                        site = myJson['data']['name']
                                    else:
                                        label = "SAMservice"
                                        host = myJson['data']['name']
                                        flavour = glbTopology.verifyType(host,
                                                        myJson['data']['type'])
                                        if flavour is None:
                                            continue
                                        site = host + "/" + flavour
                                    period = metric[3:]
                                elif ( metric[:2] == "hc" ):
                                    label = "HammerCloud"
                                    if 'name' not in myJson['data']:
                                        myJson['data']['name'] = myJson['data']['site']
                                    site = myJson['data']['name']
                                    period = metric[2:]
                                elif ( metric[:3] == "fts" ):
                                    if ( myJson['data']['type'] == "site" ):
                                        label = "FTSsite"
                                        site = myJson['data']['name']
                                    elif ( myJson['data']['type'] == "source" ):
                                        label = "FTSsource"
                                        site = myJson['data']['name'] + "/SRM"
                                    elif ( myJson['data']['type'] ==
                                                               "destination" ):
                                        label = "FTSdestination"
                                        site = myJson['data']['name'] + "/SRM"
                                    else:
                                        continue
                                    period = metric[3:]
                                elif ( metric[:2] == "sr" ):
                                    label = "SiteReadiness"
                                    site = myJson['data']['name']
                                    period = metric[2:]
                                else:
                                    continue
                                tis = int( myJson['metadata']['timestamp']
                                                                       / 1000 )
                                # need center of time-bin for filling:
                                if ( period == "1day" ):
                                    tis = int( tis / 86400 )
                                elif ( period == "6hour" ):
                                    tis = (int( tis / 21600 ) * 21600 ) + 10800
                                    if ( sswpVector.FallsIntoBins(period, tis)
                                                                    == False ):
                                        continue
                                elif ( period == "1hour" ):
                                    tis = (int( tis / 3600 ) * 3600 ) + 1800
                                    if ( sswpVector.FallsIntoBins(period, tis)
                                                                    == False ):
                                        continue
                                elif ( period == "15min" ):
                                    tis = (int( tis / 900 ) * 900 ) + 450
                                    if ( sswpVector.FallsIntoBins(period, tis)
                                                                    == False ):
                                        continue
                                if ( myJson['data']['status'] == "ok" ):
                                    code = "o"
                                elif ( myJson['data']['status'] == "warning" ):
                                    code = "w"
                                elif ( myJson['data']['status'] == "error" ):
                                    code = "e"
                                elif ( myJson['data']['status'] == "downtime" ):
                                    code = "d"
                                else:
                                    code = "u"
                                version = myJson['metadata']['kafka_timestamp']
                                if ( label[-4:] == "1day" ):
                                    myKey = (label, tis, site)
                                    if ( myKey not in vrsnDict ):
                                        vrsnDict[myKey] = (version, code)
                                    elif ( version > vrsnDict[myKey][0] ):
                                        vrsnDict[myKey] = (version, code)
                                else:
                                    jsonList.append( {'l': label,
                                                      't': tis,
                                                      's': site,
                                                      'c': code,
                                                      'v': version } )
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
        updateCache = False

    for myKey in vrsnDict:
        jsonList.append( {'l': myKey[0], 't': myKey[1], 's': myKey[2],
                          'c': vrsnDict[myKey][1], 'v': vrsnDict[myKey][0] } )
    del vrsnDict


    if updateCache:
        try:
            myFile = open("%s/monit_samhcftssr.json_new" % SSWP_CACHE_DIR, "w")
            try:
                for myJson in jsonList:
                    json.dump(myJson, myFile, separators=(",", ":"), indent=None)
                    myFile.write("\n")
                renameFlag = True
            except:
                logging.warning("   failed to write MonIT SAM,HC,FTS,SR cache")
                renameFlag = False
            finally:
                myFile.close()

            if renameFlag:
                os.rename("%s/monit_samhcftssr.json_new" % SSWP_CACHE_DIR,
                          "%s/monit_samhcftssr.json" % SSWP_CACHE_DIR)
                logging.info("   cache of MonIT SAM,HC,FTS,SR updated")
            del renameFlag
        except:
            logging.warning("   failed to update MonIT SAM,HC,FTS,SR cache")
    else:
        if 'stale' not in glbInfo:
            glbInfo['stale'] = "No/stale information (MonIT SAM,HC,FTS,SR"
        else:
            glbInfo['stale'] += ", MonIT SAM,HC,FTS,SR"
        try:
            with open("%s/monit_samhcftssr.json" % SSWP_CACHE_DIR, "r") as myFile:
                for myLine in myFile:
                    myJson = json.loads(myLine.decode('utf-8'))
                    if ( myJson['l'][-4:] == "1day" ):
                        jsonList.append( myJson )
                    elif sswpVector.FallsIntoBins(myJson['p'],  myJson['t']):
                        jsonList.append( myJson )
        except:
            logging.warning("   failed to access MonIT SAM,HC,FTS,SR cache")
    del updateCache


    glbLock.acquire()

    for myJson in jsonList:
        if ( myJson['l'][-4:] == "1day" ):
            start = myJson['t'] * 86400
            end = start + 86399
            glbSites.fill(myJson['l'], myJson['s'], start, end, myJson['c'] )
        else:
            if "/" in myJson['s']:
                glbElements.fillWithVersion(myJson['l'], myJson['s'],
                                         myJson['t'], myJson['c'], myJson['v'])
            else:
                glbSites.fillWithVersion(myJson['l'], myJson['s'], myJson['t'],
                                                      myJson['c'], myJson['v'])
    glbSites.dropVersions("SAMsite")
    glbElements.dropVersions("SAMservice")
    glbSites.dropVersions("HammerCloud")
    glbSites.dropVersions("FTSsite")
    glbElements.dropVersions("FTSsource")
    glbElements.dropVersions("FTSdestination")
    glbSites.dropVersions("SiteReadiness")

    glbLock.release()
    del jsonList
    #
    return



def ssdw_monit_down_STS():
    # ################################################################### #
    # get down15min,sts15min data from MonIT/HDFS and fill metric vectors #
    # ################################################################### #
    HDFS_PREFIX = "/project/monitoring/archive/cmssst/raw/ssbmetric"
    #
    oneDay = 86400
    tis_start = sswpVector.GetTimestamps()
    timeFrst = tis_start['month'] - oneDay
    timeLast = tis_start['fweek'] - 1
    #
    now = int( time.time() )
    sixDaysAgo = calendar.timegm( time.gmtime(now - (6 * oneDay)) )
    startLclTmpArea = calendar.timegm( time.localtime( sixDaysAgo ) )
    #
    midnight = ( int( now / 86400 ) * 86400 )
    limitLclTmpArea = calendar.timegm( time.localtime( midnight + 86399 ) )


    # prepare HDFS subdirectory list:
    # ===============================
    logging.info("Retrieving down,sts15min docs from MonIT HDFS")
    #
    dirList = set()
    #
    for dirDay in range(timeFrst, timeLast + 1, oneDay):
        dirList.add( time.strftime("/down15min/%Y/%m/%d",
                                                       time.gmtime( dirDay )) )
    for dirDay in range(startLclTmpArea, limitLclTmpArea, oneDay):
        dirList.add( time.strftime("/down15min/%Y/%m/%d.tmp",
                                                       time.gmtime( dirDay )) )
    #
    for dirDay in range(timeFrst, timeLast + 1, oneDay):
        dirList.add( time.strftime("/sts15min/%Y/%m/%d",
                                                       time.gmtime( dirDay )) )
    for dirDay in range(startLclTmpArea, limitLclTmpArea, oneDay):
        dirList.add( time.strftime("/sts15min/%Y/%m/%d.tmp",
                                                       time.gmtime( dirDay )) )
    #
    dirList = sorted( dirList )


    jsonList = []
    tmpDict = {}
    updateCache = True
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
                                if (( tis < timeFrst ) or ( tis > timeLast )):
                                    continue
                                metric = myJson['metadata']['path']
                                if ( metric == "down15min" ):
                                    name = myJson['data']['name']
                                    clss = myJson['data']['type']
                                    # convert duration back to integer:
                                    strt = int( myJson['data']['duration'][0] )
                                    end  = int( myJson['data']['duration'][1] )
                                    eKey = (name, clss, strt, end)
                                    #
                                    status = myJson['data']['status']
                                    if ( status == "ok" ):
                                        code = "o"
                                    elif ( status == "downtime" ):
                                        code = "d"
                                    elif ( status == "partial" ):
                                        code = "p"
                                    elif ( status == "adhoc" ):
                                        code = "a"
                                    elif ( status == "atrisk" ):
                                        code = "r"
                                    else:
                                        continue
                                    vrsn = myJson['metadata']['kafka_timestamp']
                                    value = ( vrsn, code, strt, end )
                                elif ( metric == "sts15min" ):
                                    eKey = (myJson['data']['name'], "site")
                                    status = myJson['data']['status']
                                    if ( status == "enabled" ):
                                        life = "o"
                                    elif ( status == "waiting_room" ):
                                        life = "W"
                                    elif ( status == "morgue" ):
                                        life = "M"
                                    else:
                                        life = "u"
                                    status = myJson['data']['prod_status']
                                    if ( status == "enabled" ):
                                        prod = "o"
                                    elif (( status == "drain" ) or
                                          ( status == "test" )):
                                        prod = "w"
                                    elif ( status == "disabled" ):
                                        prod = "e"
                                    else:
                                        prod = "u"
                                    status = myJson['data']['crab_status']
                                    if ( status == "enabled" ):
                                        crab = "o"
                                    elif ( status == "disabled" ):
                                        crab = "e"
                                    else:
                                        crab = "u"
                                    if "manual_life" not in myJson['data']:
                                        myJson['data']['manual_life'] = None
                                    if myJson['data']['manual_life'] is None:
                                        mLife = "u"
                                    else:
                                        status = myJson['data']['manual_life']
                                        if ( status == "enabled" ):
                                            mLife = "o"
                                        elif ( status == "waiting_room" ):
                                            mLife = "W"
                                        elif ( status == "morgue" ):
                                            mLife = "M"
                                        else:
                                            mLife = "u"
                                    if "manual_prod" not in myJson['data']:
                                        myJson['data']['manual_prod'] = None
                                    if myJson['data']['manual_prod'] is None:
                                        mProd = "u"
                                    else:
                                        status = myJson['data']['manual_prod']
                                        if ( status == "enabled" ):
                                            mProd = "o"
                                        elif (( status == "drain" ) or
                                              ( status == "test" )):
                                            mProd = "w"
                                        elif ( status == "disabled" ):
                                            mProd = "e"
                                        else:
                                            mProd = "u"
                                    if "manual_crab" not in myJson['data']:
                                        myJson['data']['manual_crab'] = None
                                    if myJson['data']['manual_crab'] is None:
                                        mCrab = "u"
                                    else:
                                        status = myJson['data']['manual_crab']
                                        if ( status == "enabled" ):
                                            mCrab = "o"
                                        elif ( status == "disabled" ):
                                            mCrab = "e"
                                        else:
                                            mCrab = "u"
                                    vrsn = myJson['metadata']['kafka_timestamp']
                                    value = ( vrsn, life, prod, crab,
                                                    mLife, mProd, mCrab )
                                else:
                                    continue
                                tbin = int( tis / 900 )
                                #
                                mKey = (metric, tbin)
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
        logging.error("Failed to fetch down,sts15min docs from MonIT HDFS: %s"
                      % str(excptn))
        updateCache = False


    if updateCache:
        try:
            myFile = open("%s/monit_downsts15m.json_new" % SSWP_CACHE_DIR, "w")
            try:
                for mtrcKey in tmpDict:
                    for evalKey in tmpDict[mtrcKey]:
                        myJson = {'m': mtrcKey,
                                  'e': evalKey,
                                  'v': tmpDict[mtrcKey][evalKey] }
                        json.dump(myJson, myFile, separators=(",", ":"),
                                                                   indent=None)
                        myFile.write("\n")
                renameFlag = True
            except:
                logging.warning("   failed to write MonIT down,sts15min cache")
                renameFlag = False
            finally:
                myFile.close()

            if renameFlag:
                os.rename("%s/monit_downsts15m.json_new" % SSWP_CACHE_DIR,
                          "%s/monit_downsts15m.json" % SSWP_CACHE_DIR)
                logging.info("   cache of MonIT down,sts15min updated")
            del renameFlag
        except:
            logging.warning("   failed to update MonIT down,sts15min cache")
    else:
        if 'stale' not in glbInfo:
            glbInfo['stale'] = "No/stale information (MonIT down,sts15min"
        else:
            glbInfo['stale'] += ", MonIT down,sts15min"
        try:
            with open("%s/monit_downsts15m.json" % SSWP_CACHE_DIR, "r") as myFile:
                for myLine in myFile:
                    myJson = json.loads(myLine.decode('utf-8'))
                    try:
                        tis = ( myJson['t'] * 900 ) + 450
                        if (( tis < timeFrst ) or ( tis > timeLast )):
                            continue
                        mKey = tuple( myJson['m'] )
                        eKey = tuple( myJson['e'] )
                        #
                        if mKey not in tmpDict:
                            tmpDict[mKey] = {}
                        if eKey in tmpDict[mKey]:
                            if ( myJson['v'][0] <= tmpDict[mKey][eKey][0] ):
                                continue
                        tmpDict[mKey][eKey] = tuple( myJson['v'] )
                    except KeyError:
                        continue
        except:
            logging.warning("   failed to access MonIT down,sts15min cache")
    del updateCache


    glbLock.acquire()

    # need first time-bin before previous month:
    myList = sorted( [ m[1] for m in tmpDict.keys()
                       if ( m[0] == "down15min" ) ], reverse=True )
    keepFlag = True
    for tbin in myList:
        if ( keepFlag ):
            if ( (tbin * 900) <= tis_start['month'] ):
                keepFlag = False
        else:
            del tmpDict[("down15min", tbin)]
    #
    downDict = {}
    endBIN = tis_start['final']
    for mtrcKey in sorted( [ m for m in tmpDict.keys()
                             if ( m[0] == "down15min" ) ], reverse=True ):
        # documents in a metric time-bin are uploaded together but are
        # imported with a couple seconds time jitter, allow 90 seconds
        vrsn_thrshld = 0
        # find highest version number:
        for evalKey in tmpDict[mtrcKey]:
            if ( tmpDict[mtrcKey][evalKey][0] > vrsn_thrshld ):
                vrsn_thrshld = tmpDict[mtrcKey][evalKey][0]
        vrsn_thrshld -= 90000
        #
        startBIN = mtrcKey[1] * 900
        for evalKey in tmpDict[mtrcKey]:
            # filter out docs not from the last upload (cancelled downtimes)
            if ( tmpDict[mtrcKey][evalKey][0] < vrsn_thrshld ):
                continue
            # filter out downtime overrides via "ok" state:
            if ( tmpDict[mtrcKey][evalKey][1] == "o" ):
                continue
            startTIS = max( startBIN, tmpDict[mtrcKey][evalKey][2] )
            endTIS   = min( endBIN,   tmpDict[mtrcKey][evalKey][3] )
            if ( endTIS <= startTIS ):
                continue
            name = evalKey[0]
            clss = evalKey[1]
            if ( clss != "site" ):
                name = name.lower()
                flavour = glbTopology.verifyType(name, clss)
                if flavour is None:
                    continue
                name = name + "/" + flavour
            if name not in downDict:
                downDict[name] = (30+7+1+1+7)*24*4*['u']
            sIndx = max(0, int( (startTIS - tis_start['month']) / 900 ))
            eIndx = min(4416, int( (endTIS - tis_start['month'] + 900) / 900 ))
            for indx in range(sIndx, eIndx):
                downDict[name][indx] = tmpDict[mtrcKey][evalKey][1]
        endBIN = startBIN
    #
    for name in downDict:
        for bin in range( sswpVector.getDefaultBins() ):
            startTIS, endTIS = sswpVector.Bin2times(bin)
            counters = [0, 0, 0, 0, 0]
            for bTIS in range(startTIS, endTIS, 900):
                indx = int( (bTIS - tis_start['month']) / 900)
                code = downDict[name][indx]
                if ( code == "d" ):
                   counters[1] += 1
                elif ( code == "p" ):
                   counters[2] += 1
                elif ( code == "a" ):
                   counters[3] += 1
                elif ( code == "r" ):
                   counters[4] += 1
                else:
                   counters[0] += 1
            mx = max(counters)
            if ( counters[1] == mx ):
               code = "d"
            elif ( counters[2] == mx ):
               code = "p"
            elif ( counters[3] == mx ):
               code = "a"
            elif ( counters[4] == mx ):
               code = "r"
            else:
               code = "u"
            if "/" in name:
                glbElements.setBin("Downtime", name, bin, code)
            else:
                glbSites.setBin("Downtime", name, bin, code)
    del downDict


    myList = sorted( [ m[1] for m in tmpDict.keys()
                       if ( m[0] == "sts15min" ) ], reverse=True )
    keepFlag = True
    for tbin in myList:
        if ( keepFlag ):
            if ( (tbin * 900) <= tis_start['month'] ):
                keepFlag = False
        else:
            del tmpDict[("sts15min", tbin)]
    #
    lifeDict = {}
    prodDict = {}
    crabDict = {}
    manLifeDict = {}
    manProdDict = {}
    manCrabDict = {}
    endTIS = tis_start['fweek']
    for mtrcKey in sorted( [ m for m in tmpDict.keys()
                             if ( m[0] == "sts15min" ) ], reverse=True ):
        startTIS = mtrcKey[1] * 900
        for evalKey in tmpDict[mtrcKey]:
            name = evalKey[0]
            if name not in lifeDict:
                lifeDict[name] = (30+7+1+1+7)*24*4*['u']
                prodDict[name] = (30+7+1+1+7)*24*4*['u']
                crabDict[name] = (30+7+1+1+7)*24*4*['u']
                manLifeDict[name] = (30+7+1+1+7)*24*4*['u']
                manProdDict[name] = (30+7+1+1+7)*24*4*['u']
                manCrabDict[name] = (30+7+1+1+7)*24*4*['u']
            sIndx = max(0, int( (startTIS - tis_start['month']) / 900 ))
            eIndx = min(4416, int( (endTIS - tis_start['month'] + 900) / 900 ))
            for indx in range(sIndx, eIndx):
                lifeDict[name][indx] = tmpDict[mtrcKey][evalKey][1]
                prodDict[name][indx] = tmpDict[mtrcKey][evalKey][2]
                crabDict[name][indx] = tmpDict[mtrcKey][evalKey][3]
                manLifeDict[name][indx] = tmpDict[mtrcKey][evalKey][4]
                manProdDict[name][indx] = tmpDict[mtrcKey][evalKey][5]
                manCrabDict[name][indx] = tmpDict[mtrcKey][evalKey][6]
        endTIS = startTIS
    #
    for name in lifeDict:
        for bin in range( sswpVector.getDefaultBins() ):
            startTIS, endTIS = sswpVector.Bin2times(bin)
            life_cnt = [0, 0, 0, 0]
            prod_cnt = [0, 0, 0, 0]
            crab_cnt = [0, 0, 0, 0]
            manLife_cnt = [0, 0, 0]
            manProd_cnt = [0, 0, 0]
            manCrab_cnt = [0, 0, 0]
            for bTIS in range(startTIS, endTIS, 900):
                indx = int( (bTIS - tis_start['month']) / 900)
                code = lifeDict[name][indx]
                if ( code == "o" ):
                   life_cnt[1] += 1
                elif ( code == "W" ):
                   life_cnt[2] += 1
                elif ( code == "M" ):
                   life_cnt[3] += 1
                else:
                   life_cnt[0] += 1
                #
                code = prodDict[name][indx]
                if ( code == "o" ):
                   prod_cnt[1] += 1
                elif ( code == "w" ):
                   prod_cnt[2] += 1
                elif ( code == "e" ):
                   prod_cnt[3] += 1
                else:
                   prod_cnt[0] += 1
                #
                code = crabDict[name][indx]
                if ( code == "o" ):
                   crab_cnt[1] += 1
                elif ( code == "w" ):
                   crab_cnt[2] += 1
                elif ( code == "e" ):
                   crab_cnt[3] += 1
                else:
                   crab_cnt[0] += 1
                #
                code = manLifeDict[name][indx]
                if ( code == "o" ):
                   manLife_cnt[0] += 1
                elif ( code == "W" ):
                   manLife_cnt[1] += 1
                elif ( code == "M" ):
                   manLife_cnt[2] += 1
                #
                code = manProdDict[name][indx]
                if ( code == "o" ):
                   manProd_cnt[0] += 1
                elif ( code == "w" ):
                   manProd_cnt[1] += 1
                elif ( code == "e" ):
                   manProd_cnt[2] += 1
                #
                code = manCrabDict[name][indx]
                if ( code == "o" ):
                   manCrab_cnt[0] += 1
                elif ( code == "w" ):
                   manCrab_cnt[1] += 1
                elif ( code == "e" ):
                   manCrab_cnt[2] += 1
            mx = max(life_cnt)
            if ( life_cnt[3] == mx ):
               code = "M"
            elif ( life_cnt[2] == mx ):
               code = "W"
            elif ( life_cnt[1] == mx ):
               code = "o"
            else:
               code = "u"
            glbSites.setBin("LifeStatus", name, bin, code)
            #
            mx = max(prod_cnt)
            if ( prod_cnt[3] == mx ):
               code = "e"
            elif ( prod_cnt[2] == mx ):
               code = "w"
            elif ( prod_cnt[1] == mx ):
               code = "o"
            else:
               code = "u"
            glbSites.setBin("ProdStatus", name, bin, code)
            #
            mx = max(crab_cnt)
            if ( crab_cnt[3] == mx ):
               code = "e"
            elif ( crab_cnt[2] == mx ):
               code = "w"
            elif ( crab_cnt[1] == mx ):
               code = "o"
            else:
               code = "u"
            glbSites.setBin("CrabStatus", name, bin, code)
            #
            mx = max(manLife_cnt)
            if ( mx == 0 ):
               code = "u"
            elif ( manLife_cnt[2] == mx ):
               code = "M"
            elif ( manLife_cnt[1] == mx ):
               code = "W"
            else:
               code = "o"
            glbSites.setBin("manLifeStatus", name, bin, code)
            #
            mx = max(manProd_cnt)
            if ( mx == 0 ):
               code = "u"
            elif ( manProd_cnt[2] == mx ):
               code = "e"
            elif ( manProd_cnt[1] == mx ):
               code = "w"
            else:
               code = "o"
            glbSites.setBin("manProdStatus", name, bin, code)
            #
            mx = max(manCrab_cnt)
            if ( mx == 0 ):
               code = "u"
            elif ( manCrab_cnt[2] == mx ):
               code = "e"
            elif ( manCrab_cnt[1] == mx ):
               code = "w"
            else:
               code = "o"
            glbSites.setBin("manCrabStatus", name, bin, code)
    del manCrabDict
    del manProdDict
    del manLifeDict
    del crabDict
    del prodDict
    del lifeDict

    del tmpDict

    glbLock.release()
    #
    return



def ssdw_monit_etf():
    # ########################################################### #
    # get SAM ETF results from MonIT/HDFS and fill metric vectors #
    # ########################################################### #
    HDFS_PREFIX = "/project/monitoring/archive/sam3/raw/metric/"
    #
    oneDay = 86400
    tis_start = sswpVector.GetTimestamps()
    # limit retrieval/display, for the time being:
    #timeFrst = tis_start['month'] - oneDay
    timeFrst = tis_start['pweek']
    timeLast = tis_start['fweek'] - 1
    #
    now = int( time.time() )
    sixDaysAgo = calendar.timegm( time.gmtime(now - (6 * oneDay)) )
    startLclTmpArea = calendar.timegm( time.localtime( sixDaysAgo ) )
    #
    midnight = ( int( now / 86400 ) * 86400 )
    limitLclTmpArea = calendar.timegm( time.localtime( midnight + 86399 ) )


    # prepare service host/flavour list/set:
    # ======================================
    hostflavourSet = set()
    for cmssite in glbTopology.sites():
        for service in glbTopology.getElements(cmssite):
            hostflavourSet.add( service )


    # prepare HDFS subdirectory list:
    # ===============================
    logging.info("Retrieving SAM ETF result docs from MonIT HDFS")
    #
    dirList = set()
    #
    for dirDay in range(timeFrst, timeLast + 1, oneDay):
        dirList.add( time.strftime("%Y/%m/%d", time.gmtime( dirDay )) )
    for dirDay in range(startLclTmpArea, limitLclTmpArea, oneDay):
        dirList.add( time.strftime("%Y/%m/%d.tmp", time.gmtime( dirDay )) )
    #
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
                                if ( myJson['metadata']['topic'] !=
                                                           "sam3_raw_metric" ):
                                    continue
                                if ( myJson['data']['vo'] != "cms" ):
                                    continue
                                tis = int( myJson['data']['timestamp'] / 1000 )
                                if (( tis < timeFrst ) or ( tis > timeLast )):
                                    continue
                                hostname = myJson['data']['dst_hostname']
                                flavour = myJson['data']['service_flavour']
                                service = hostname + "/" + flavour
                                if service not in hostflavourSet:
                                    continue
                                probe = myJson['data']['metric_name'][8:].split("-/cms/Role=",1)[0]
                                status = myJson['data']['status']
                                if ( status == "OK" ):
                                    code = "o"
                                elif ( status == "WARNING" ):
                                    code = "w"
                                elif ( status == "CRITICAL" ):
                                    code = "e"
                                else:
                                    continue
                                tbin = sswpVector.Time2bin( tis )
                                if tbin is None:
                                    continue
                                #
                                if service not in tmpDict:
                                    tmpDict[service] = {}
                                if probe not in tmpDict[service]:
                                    tmpDict[service][probe] = {}
                                if tbin not in tmpDict[service][probe]:
                                    tmpDict[service][probe][tbin] = []
                                tmpDict[service][probe][tbin].append( code )
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
        if 'stale' not in glbInfo:
            glbInfo['stale'] = "No/incomplete information (MonIT SAM-ETF"
        else:
            glbInfo['stale'] += ", SAM-ETF"


    glbLock.acquire()

    for service in tmpDict:
        for probe in tmpDict[service]:
            for tbin in tmpDict[service][probe]:
                counters = [0, 0, 0]
                for code in tmpDict[service][probe][tbin]:
                    if ( code == "o" ):
                        counters[0] += 1
                    elif ( code == "w" ):
                        counters[1] += 1
                    elif ( code == "e" ):
                        counters[2] += 1
                mx = max(counters)
                if ( counters[2] == mx ):
                   code = "e"
                elif ( counters[1] == mx ):
                   code = "w"
                else:
                    code = "o"
                glbElements.setBin("ETF_" + probe, service, tbin, code)


    del tmpDict

    glbLock.release()
    #
    return



def ssdw_site_summary():
    # ############################################################## #
    # fill site Summary vector based on LifeStatus and SiteReadiness #
    # ############################################################## #

    glbLock.acquire()

    logging.info("Composing site summary information")
    for cmssite in sorted(glbTopology.sites()):
        # locate SiteReadiness:
        SRvector = glbSites.getVector("SiteReadiness", cmssite)

        # locate LifeStatus:
        LSvector = glbSites.getVector("LifeStatus", cmssite)

        # locate Downtime:
        DTvector = glbSites.getVector("Downtime", cmssite)

        # evaluate site summary based on LifeStatus and Site Readiness:
        for bin in range( sswpVector.getDefaultBins() ):
            SRcode = "u"
            if SRvector is not None:
                SRcode = SRvector.getBin(bin)
            #
            LScode = "u"
            if LSvector is not None:
                LScode = LSvector.getBin(bin)
            #
            if ( LScode == "o" ):
                code = SRcode
            elif ( LScode == "W" ):
                if ( SRcode == "o" ):
                    code = "R"
                elif ( SRcode == "w" ):
                    code = "S"
                elif ( SRcode == "e" ):
                    code = "T"
                elif ( SRcode == "d" ):
                    code = "U"
                else:
                    code = "V"
            elif ( LScode == "M" ):
                if ( SRcode == "o" ):
                    code = "H"
                elif ( SRcode == "w" ):
                    code = "I"
                elif ( SRcode == "e" ):
                    code = "J"
                elif ( SRcode == "d" ):
                    code = "K"
                else:
                    code = "L"
            elif ( SRcode != "u" ):
                code = SRcode
            else:
                code = "u"
            #
            DTcode = "u"
            if DTvector is not None:
                DTcode = DTvector.getBin(bin)
            if ( code == "u" ):
                code = DTcode
            elif (( code == "e" ) and ( DTcode == "d" )):
                code = DTcode

            glbSites.setBin('Summary', cmssite, bin, code)

    glbLock.release()



def sswp_ssb_PhEDExLinks():
    # ################################################################### #
    # get PhEDEx Link data from the SSB-Dashboard and fill metric vectors #
    # ################################################################### #
    ts1 = time.gmtime( glbInfo['timestamp'] - 39*24*60*60)
    ts2 = time.gmtime( glbInfo['timestamp'] + 24*60*60)
    #
    URL_SSB_PHEDEXLINKS = "http://dashb-ssb.cern.ch/dashboard/request.py/getplotdata?columnid=63&time=custom&sites=all&clouds=all&batch=1&dateFrom=%s&dateTo=%s" % (time.strftime("%Y-%m-%d", ts1), time.strftime("%Y-%m-%d", ts2))

    # get PhEDEx Links data from the SSB dashboard:
    # =============================================
    logging.info("Querying SSB for PhEDEx Links information")
    urlHndl = None
    try:
        request = urllib.request.Request(URL_SSB_PHEDEXLINKS,
                                         headers={'Accept':'application/json'})
        urlHndl = urllib.request.urlopen( request )
        myCharset = urlHndl.headers.get_content_charset()
        if myCharset is None:
            myCharset = "utf-8"
        myData = urlHndl.read().decode( myCharset )
        del(myCharset)
        #
        # update cache:
        try:
            myFile = open("%s/cache_ssbPhEDExLinks.json_new" % SSWP_CACHE_DIR,
                          'w')
            try:
                myFile.write(myData)
                renameFlag = True
            except:
                renameFlag = False
            finally:
                myFile.close()
                del myFile
            if renameFlag:
                os.rename("%s/cache_ssbPhEDExLinks.json_new" % SSWP_CACHE_DIR,
                          "%s/cache_ssbPhEDExLinks.json" % SSWP_CACHE_DIR)
                logging.info("   cache of SSB PhEDEx Links updated")
            del renameFlag
        except:
            pass
    except:
        if 'stale' not in glbInfo:
            glbInfo['stale'] = "No/stale information (SSB PhEDEx Links"
        else:
            glbInfo['stale'] += ", SSB PhEDEx Links"
        logging.warning("   failed to fetch SSB PhEDEx Links data")
        try:
            myFile = open("%s/cache_ssbPhEDExLinks.json" % SSWP_CACHE_DIR, 'r')
            try:
                myData = myFile.read()
                logging.info("   using cached SSB PhEDEx Links data")
            except:
                logging.warning(("   failed to access cached SSB PhEDEx Link" +
                                 "s data"))
                return
            finally:
                myFile.close()
                del myFile
        except:
            logging.warning("   no SSB PhEDEx Links cache available")
            return
    finally:
        if urlHndl is not None:
            urlHndl.close()
    del urlHndl

    glbLock.acquire()

    # unpack JSON data of SSB PhEDEx Links 2 hours information:
    phedexlinks = json.loads( myData )

    for entry in phedexlinks['csvdata']:
        cmssite = entry['VOName']
        status = entry['COLORNAME']                                # red, green
        status = status.lower()
        if ( status == "green" ):
            code = 'o'
        elif ( status == "red" ):
            code = 'e'
        else:
            continue
        tstrng = entry['Time']
        ts = time.strptime(tstrng + ' UTC', "%Y-%m-%dT%H:%M:%S %Z")
        # PhEDEx Links metric is shifter by 24 hours, correct time:
        start = calendar.timegm(ts) - 86400
        tstrng = entry['EndTime']
        ts = time.strptime(tstrng + ' UTC', "%Y-%m-%dT%H:%M:%S %Z")
        # PhEDEx Links metric is shifter by 24 hours, correct time:
        end = calendar.timegm(ts) - 86400
        #logging.debug("LS(%s) %s to %s = %s",
        #              cmssite, entry['Time'], tstrng, code)

        glbSites.fillCenter('PhEDExLinks', cmssite, start,
            min(glbInfo['timestamp'], end), code)

    glbLock.release()



def sswp_ssb_Links2hours():
    # ################################################################### #
    # get PhEDEx Link data from the SSB-Dashboard and fill metric vectors #
    # ################################################################### #
    ts1 = time.gmtime( glbInfo['timestamp'] - 39*24*60*60)
    ts2 = time.gmtime( glbInfo['timestamp'] + 24*60*60)
    #
    URL_SSB_LINKS2HOURS = "http://dashb-ssb.cern.ch/dashboard/request.py/getplotdata?columnid=16101&time=custom&sites=all&clouds=all&batch=1&dateFrom=%s&dateTo=%s" % (time.strftime("%Y-%m-%d", ts1), time.strftime("%Y-%m-%d", ts2))

    # get PhEDEx Links 2 hours data from the SSB dashboard:
    # =====================================================
    logging.info("Querying SSB for PhEDEx Links 2 hours information")
    urlHndl = None
    try:
        request = urllib.request.Request(URL_SSB_LINKS2HOURS,
                                         headers={'Accept':'application/json'})
        urlHndl = urllib.request.urlopen( request )
        myCharset = urlHndl.headers.get_content_charset()
        if myCharset is None:
            myCharset = "utf-8"
        myData = urlHndl.read().decode( myCharset )
        del(myCharset)
        #
        # update cache:
        try:
            myFile = open("%s/cache_ssbPhEDExLinks2h.json_new" % SSWP_CACHE_DIR,
                          'w')
            try:
                myFile.write(myData)
                renameFlag = True
            except:
                renameFlag = False
            finally:
                myFile.close()
                del myFile
            if renameFlag:
                os.rename("%s/cache_ssbPhEDExLinks2h.json_new" % SSWP_CACHE_DIR,
                          "%s/cache_ssbPhEDExLinks2h.json" % SSWP_CACHE_DIR)
                logging.info("   cache of SSB PhEDEx Links 2 hours updated")
            del renameFlag
        except:
            pass
    except:
        if 'stale' not in glbInfo:
            glbInfo['stale'] = "No/stale information (SSB PhEDEx Links 2 hours"
        else:
            glbInfo['stale'] += ", SSB PhEDEx Links 2 hours"
        logging.warning("   failed to fetch SSB PhEDEx Links 2 hours data")
        try:
            myFile = open("%s/cache_ssbPhEDExLinks2h.json" % SSWP_CACHE_DIR,
                          'r')
            try:
                myData = myFile.read()
                logging.info("   using cached SSB PhEDEx Links 2 hours data")
            except:
                logging.warning(("   failed to access cached SSB PhEDEx Link" +
                                 "s 2 hours data"))
                return
            finally:
                myFile.close()
                del myFile
        except:
            logging.warning("   no SSB PhEDEx Links 2 hours cache available")
            return
    finally:
        if urlHndl is not None:
            urlHndl.close()
    del urlHndl

    glbLock.acquire()

    # unpack JSON data of SSB PhEDEx Links 2 hours information:
    links2hours = json.loads( myData )

    for entry in links2hours['csvdata']:
        cmssite = entry['VOName']
        # filter out fake "*_Disk", "*_Buffer", and "*_MSS" sites
        if ( cmssite.find('_Disk', 5) > 0 ): continue
        if ( cmssite.find('_Buffer', 5) > 0 ): continue
        if ( cmssite.find('_MSS', 5) > 0 ): continue
        status = entry['COLORNAME']                       # red, green, yellow
        status = status.lower()
        if ( status == "green" ):
            code = 'o'
        elif ( status == "yellow" ):
            code = 'w'
        elif ( status == "red" ):
            code = 'e'
        else:
            continue
        tstrng = entry['Time']
        ts = time.strptime(tstrng + ' UTC', "%Y-%m-%dT%H:%M:%S %Z")
        start = calendar.timegm(ts)
        tstrng = entry['EndTime']
        ts = time.strptime(tstrng + ' UTC', "%Y-%m-%dT%H:%M:%S %Z")
        end = calendar.timegm(ts)
        #logging.debug("LS(%s) %s to %s = %s",
        #              cmssite, entry['Time'], tstrng, code)

        glbSites.fillCounters('PhEDEx2hours', cmssite, start,
            min(glbInfo['timestamp'], end), code)

    glbSites.resolveCountersDownOkWarnErr('PhEDEx2hours')

    glbLock.release()



def sswp_site_readiness():
    # ############################################################# #
    # fill SAM site and HC 15 min results into site summary vectors #
    # ############################################################# #

    vectorUNKNOWN = sswpVector()

    logging.info("Filling WLCG site SAM/HC 15 min results into site summary")
    for cmssite in sorted(glbTopology.sites()):
        vector1 = glbSites.getVector('wlcgSAMsite', cmssite)
        vector2 = glbSites.getVector('HC15min', cmssite)
        if vector2 is None:
            vector2 = vectorUNKNOWN
        if vector1 is not None:
            for bin in sswpVector.getYesterdayTodayBinRange():
                code = vector1.getBin(bin)
                code2 = vector2.getBin(bin)
                if ( code == 'u' ):
                   code = code2
                elif (( code == 'o' ) and ( code2 != 'u' )):
                    code = code2
                elif (( code == 'w' ) and ( code2 == 'e' )):
                    code = 'e'
                #
                glbSites.setBinNoOverride('summary', cmssite, bin, code)



def sswp_write_summary_js():
    # ####################################################################### #

    myfile = open("%s/summary.js_new" % SSWP_DATA_DIR, 'w')
    try:
        myfile.write("/* JavaScript */\n\"use strict\";\n\n\n")
        myfile.write("var siteStatusInfo = {\n   time: %d,   // %s\n" %
            (glbInfo['timestamp'], time.strftime("%Y-%m-%d %H:%M:%S",
                                 time.gmtime(glbInfo['timestamp']))))
        if 'stale' in glbInfo:
            myfile.write("   alert: \"%s)\",\n" % glbInfo['stale'])
        else:
            myfile.write("   alert: \"\",\n")
        if 'msg' in glbInfo:
            myfile.write("   msg: \"%s\",\n" % glbInfo['msg'])
        else:
            myfile.write("   msg: \"\",\n")
        myfile.write("   url: \"%s\",\n" % glbInfo['url'])
        myfile.write("   reload: 900\n};\n\n")

        myfile.write("var siteStatusData = [")
        mypreceding = False
        for cmssite in sorted(glbTopology.sites()):
            vector = glbSites.getVector('Summary', cmssite)
            ticket = glbTickets.getSummary(cmssite, glbInfo['timestamp'])
            if (( vector is None ) and ( ticket[0] == 0 )):
                continue

            if mypreceding:
                myfile.write(",\n   { site: \"%s\",\n" % cmssite)
            else:
                myfile.write("\n   { site: \"%s\",\n" % cmssite)
            # GGUS ticket summary:
            myfile.write("     ggus: [%d, %d, %d],\n" % (
                ticket[0], ticket[1], ticket[2]))
            # summary vector:
            if ( vector is None ):
                sswpVector.writeEmpty_js(myfile, 5)
            else:
                vector.write_js(myfile, 5)
            myfile.write("\n   }")
            mypreceding = True
        myfile.write("\n]")
        renameFlag = True
    except:
        renameFlag = False
    finally:
        myfile.close()

    if renameFlag:
        os.rename("%s/summary.js_new" % SSWP_DATA_DIR,
                  "%s/summary.js" % SSWP_DATA_DIR)



def sswp_write_downtime_js():
    # ####################################################################### #

    myfile = open("%s/downtime.js_new" % SSWP_DATA_DIR, 'w')
    try:
        myfile.write("/* JavaScript */\n\"use strict\";\n\n\n")
        myfile.write("var siteStatusInfo = {\n   time: %d,   // %s\n" %
            (glbInfo['timestamp'], time.strftime("%Y-%m-%d %H:%M:%S",
                                 time.gmtime(glbInfo['timestamp']))))
        if 'stale' in glbInfo:
            myfile.write("   alert: \"%s)\",\n" % glbInfo['stale'])
        else:
            myfile.write("   alert: \"\",\n")
        if 'msg' in glbInfo:
            myfile.write("   msg: \"%s\",\n" % glbInfo['msg'])
        else:
            myfile.write("   msg: \"\",\n")
        myfile.write("   url: \"%s\",\n" % glbInfo['url'])
        myfile.write("   reload: 3600\n};\n\n")

        myfile.write("var siteStatusData = [")
        mypreceding = False
        for cmssite in sorted(glbTopology.sites()):
            vector = glbSites.getVector('Summary', cmssite)
            ticket = glbTickets.getSummary(cmssite, glbInfo['timestamp'])
            if (( vector is None ) and ( ticket[0] == 0 )):
                continue

            vector = glbSites.getVector('Downtime', cmssite)

            if mypreceding:
                myfile.write(",\n   { site: \"%s\",\n" % cmssite)
            else:
                myfile.write("\n   { site: \"%s\",\n" % cmssite)
            # GGUS ticket summary:
            myfile.write("     ggus: [%d, %d, %d],\n" % (
                ticket[0], ticket[1], ticket[2]))
            # downtime vector:
            if ( vector is None ):
                sswpVector.writeEmpty_js(myfile, 5)
            else:
                vector.write_js(myfile, 5)
            myfile.write("\n   }")
            mypreceding = True
        myfile.write("\n]")
        renameFlag = True
    except:
        renameFlag = False
    finally:
        myfile.close()

    if renameFlag:
        os.rename("%s/downtime.js_new" % SSWP_DATA_DIR,
                  "%s/downtime.js" % SSWP_DATA_DIR)



def sswp_write_detail_json():
    # ####################################################################### #

    sMetrics = glbSites.getMetricList()
    eMetrics = glbElements.getMetricList()

    for cmssite in sorted(glbTopology.sites()):
        myfile = open("%s/%s.json_new" % (SSWP_DATA_DIR, cmssite), 'w')
        try:
            myfile.write("{\n \"time\": %d,\n" % glbInfo['timestamp'])
            if 'stale' in glbInfo:
                myfile.write(" \"alert\": \"%s)\",\n" % glbInfo['stale'])
            else:
                myfile.write(" \"alert\": \"\",\n")
            if 'msg' in glbInfo:
                myfile.write(" \"msg\": \"%s\",\n" % glbInfo['msg'])
            else:
                myfile.write(" \"msg\": \"\",\n")
            myfile.write(" \"url\": \"%s\",\n" % glbInfo['url'])
            myfile.write(" \"reload\": 900,\n")
            myfile.write(" \"site\": \"%s\",\n" % cmssite)
            # GGUS ticket information:
            myfile.write(" \"ggus\": [")
            mycnt = 0
            for ticket in glbTickets.getTickets(cmssite):
                if ( mycnt == 0 ):
                    myfile.write("[%s, %d]" % (ticket[0], ticket[1]))
                elif ( mycnt % 3 == 0 ):
                    myfile.write(",\n          [%s, %d]" % (ticket[0],
                        ticket[1]))
                else:
                    myfile.write(", [%s, %d]" % (ticket[0], ticket[1]))
                mycnt += 1
            myfile.write("],\n")

            myfile.write(" \"metrics\": {")
            mypreceding = False
            for metric in sMetrics:
                vector = glbSites.getVector(metric, cmssite)
                #
                if (( vector is None ) and ( metric[0:7] == "manual ") and
                    ( metric[-6:] == "Status" )):
                    # skip empty manual override status metrics
                    continue
                #
                if mypreceding:
                    myfile.write(",\n   \"%s\": {\n" % metric)
                else:
                    myfile.write("\n   \"%s\": {\n" % metric)
                if ( vector is None ):
                    sswpVector.writeEmty_json(myfile, 5)
                else:
                    vector.write_json(myfile, 5)
                #
                myfile.write("\n   }")
                mypreceding = True
            myfile.write("\n },\n")

            myfile.write(" \"elements\": [\n")
            mypreceding = False
            for element in sorted(glbTopology.getElements(cmssite)):
                host, type = element.split("/",1)
                if mypreceding:
                    myfile.write(", {\n   \"host\": \"%s\",\n" % host)
                else:
                    myfile.write("  {\n   \"host\": \"%s\",\n" % host)
                myfile.write("   \"type\": \"%s\",\n" % type)

                myfile.write("   \"metrics\": {")
                my2preceding = False
                for metric in eMetrics:
                    vector = glbElements.getVector(metric, element)
                    if (( vector is None ) and
                        (( metric != "downtime" ) and
                         ( metric != "Downtime" ))):
                        continue
                    #
                    if my2preceding:
                        myfile.write(",\n    \"%s\": {\n" %
                            metric)
                    else:
                        myfile.write("\n    \"%s\": {\n" %
                            metric)
                    if ( vector is None ):
                        sswpVector.writeEmty_json(myfile, 5)
                    else:
                        vector.write_json(myfile, 5)
                    myfile.write("\n    }")
                    my2preceding = True
                myfile.write("\n   }\n  }")
                mypreceding = True
            myfile.write("\n ]\n}")
            renameFlag = True
        except:
            renameFlag = False
        finally:
            myfile.close()

        if renameFlag:
            os.rename("%s/%s.json_new" % (SSWP_DATA_DIR, cmssite),
                      "%s/%s.json" % (SSWP_DATA_DIR, cmssite))



def oswp_time_print(seconds):

    if (seconds < 120):
        tstring = "%d sec" % seconds
    elif (seconds < 7200):
        tstring = "%d min" % int(seconds / 60)
    elif (seconds < 172800):
        tstring = "%d hours" % int(seconds / 3600)
    elif (seconds < 1209600):
        tstring = "%d days" % int(seconds / 86400)
    elif (seconds < 5270400):
        tstring = "%d weeks" % int(seconds / 604800)
    elif (seconds < 63072000):
        tstring = "%d months" % int(seconds / 2628000)
    else:
        tstring = "%d years" % int(seconds / 31536000)

    return tstring



def sswp_dump():

    print("\nStatus Time = %d   %s" % (sswp_times['timestamp'],
                   time.strftime("%Y-%m-%d %H:%M:%S",
                                 time.gmtime(sswp_times['timestamp']))))

    for site in sorted(sswp_sites.keys()):
        if ((( not sswp_sites[site]['ggus'] ) or
             ( sswp_sites[site]['ggus'][0] == 0 )) and
            ( ''.join(sswp_sites[site]['month']) == 120*'u' ) and
            ( ''.join(sswp_sites[site]['pweek']) == 168*'u') and
            ( ''.join(sswp_sites[site]['yesterday']) == 96*'u') and
            ( ''.join(sswp_sites[site]['today']) == 96*'u') and
            ( ''.join(sswp_sites[site]['tomorrow']) == 24*'u') and
            ( ''.join(sswp_sites[site]['nweek']) == 28*'u' ) and
            ( not sswp_sites[site]['elements'] )): continue

        if ( not sswp_sites[site]['ggus'] ):
            print("%-24s: GGUS unknown" % site)
        elif ( sswp_sites[site]['ggus'][0] == 0 ):
            print("%-24s: GGUS none" % site)
        else:
            print("%-24s: GGUS %d (youngest %s / oldest %s)" % (site,
                sswp_sites[site]['ggus'][0],
                oswp_time_print( sswp_sites[site]['ggus'][1] ),
                oswp_time_print( sswp_sites[site]['ggus'][2] )))
        if ( ''.join(sswp_sites[site]['month']) != 120*'u' ):
            print("%-24s  Prev.Month = %s\n %37s %s\n %37s %s" %
                  ('', ''.join(sswp_sites[site]['month'][0:40]),
                   '', ''.join(sswp_sites[site]['month'][40:80]),
                   '', ''.join(sswp_sites[site]['month'][80:120])))
        if ( ''.join(sswp_sites[site]['pweek']) != 168*'u' ):
            print(("%-24s  Prev.Week  = %s\n %37s %s\n %37s %s\n %37s %s\n" + \
                   " %37s %s\n %37s %s\n %37s %s") %
                  ('', ''.join(sswp_sites[site]['pweek'][0:24]),
                   '', ''.join(sswp_sites[site]['pweek'][24:48]),
                   '', ''.join(sswp_sites[site]['pweek'][48:72]),
                   '', ''.join(sswp_sites[site]['pweek'][72:96]),
                   '', ''.join(sswp_sites[site]['pweek'][96:120]),
                   '', ''.join(sswp_sites[site]['pweek'][120:144]),
                   '', ''.join(sswp_sites[site]['pweek'][144:168])))
        if ( ''.join(sswp_sites[site]['yesterday']) != 96*'u' ):
            print("%-24s  Yesterday  = %s\n %37s %s\n %37s %s" %
                  ('', ''.join(sswp_sites[site]['yesterday'][0:32]),
                   '', ''.join(sswp_sites[site]['yesterday'][32:64]),
                   '', ''.join(sswp_sites[site]['yesterday'][64:96])))
        if ( ''.join(sswp_sites[site]['today']) != 96*'u' ):
            print("%-24s  Today      = %s\n %37s %s\n %37s %s" %
                  ('', ''.join(sswp_sites[site]['today'][0:32]),
                   '', ''.join(sswp_sites[site]['today'][32:64]),
                   '', ''.join(sswp_sites[site]['today'][64:96])))
        if ( ''.join(sswp_sites[site]['fweek']) != 168*'u' ):
            print(("%-24s  Foll.Week  = %s\n %37s %s\n %37s %s\n %37s %s\n" + \
                   " %37s %s\n %37s %s\n %37s %s") %
                  ('', ''.join(sswp_sites[site]['fweek'][0:24]),
                   '', ''.join(sswp_sites[site]['fweek'][24:48]),
                   '', ''.join(sswp_sites[site]['fweek'][48:72]),
                   '', ''.join(sswp_sites[site]['fweek'][72:96]),
                   '', ''.join(sswp_sites[site]['fweek'][96:120]),
                   '', ''.join(sswp_sites[site]['fweek'][120:144]),
                   '', ''.join(sswp_sites[site]['fweek'][144:168])))
        for element in sswp_sites[site]['elements']:
            print("%-24s  %s service %s of %s" %
                  ('', element['type'], element['host'], element['site']))
            if ( ''.join(element['down2d']) != 192*'u' ):
                print(("%-24s     down2d = %s\n %36s %s\n %36s %s\n %36s " + \
                       "%s\n %36s %s\n %36s %s\n") %
                      ('', ''.join(element['down2d'][0:32]),
                       '', ''.join(element['down2d'][32:64]),
                       '', ''.join(element['down2d'][64:96]),
                       '', ''.join(element['down2d'][96:128]),
                       '', ''.join(element['down2d'][128:160]),
                       '', ''.join(element['down2d'][160:192])))
            if ( ''.join(element['down1w']) != 168*'u' ):
                print(("%-24s     down1w = %s\n %36s %s\n %36s %s\n %36s " + \
                       "%s\n %36s %s\n %36s %s\n %36s %s") %
                      ('', ''.join(element['down1w'][0:24]),
                       '', ''.join(element['down1w'][24:48]),
                       '', ''.join(element['down1w'][48:72]),
                       '', ''.join(element['down1w'][72:96]),
                       '', ''.join(element['down1w'][96:120]),
                       '', ''.join(element['down1w'][120:144]),
                       '', ''.join(element['down1w'][144:168])))
# ########################################################################### #



def sswp_work1():
    tis = time.time()
    cpt = time.process_time()
    sswp_osg_downtime()
    sswp_egi_downtime()
    sswp_site_downtime()                               # updates summary metric
    sswp_ssb_SiteReadiness()                           # updates summary metric
    sswp_ssb_LifeStatus()                              # updates summary metric
    sswp_old_site_summary()                             # drops 15 min downtime
    ncpu = time.process_time() - cpt
    nsec = time.time() - tis
    logging.info("sswp_work1 took %8.3f / %d seconds", ncpu, nsec)
    # 3.880 / 6 seconds
    return



def sswp_work2():
    tis = time.time()
    cpt = time.process_time()
    sswp_ssb_HammerCloud15min()
    ncpu = time.process_time() - cpt
    nsec = time.time() - tis
    logging.info("sswp_work2 took %8.3f / %d seconds", ncpu, nsec)
    # 17.040 / 25 seconds
    return



def sswp_work3():
    tis = time.time()
    cpt = time.process_time()
    sswp_ssb_ProdStatus()
    sswp_ssb_CrabStatus()
    sswp_ssb_manLifeStatus()
    sswp_ssb_manProdStatus()
    sswp_ssb_manCrabStatus()
    sswp_ssb_PhEDExLinks()
    sswp_ssb_Links2hours()
    ncpu = time.process_time() - cpt
    nsec = time.time() - tis
    logging.info("sswp_work3 took %8.3f / %d seconds", ncpu, nsec)
    # 3.810 / 6 seconds
    return



def sswp_work4():
    tis = time.time()
    cpt = time.process_time()
    sswp_wlcg_sam_site()
    sswp_wlcg_sam_downtime()
    sswp_wlcg_sam_services()
    ncpu = time.process_time() - cpt
    nsec = time.time() - tis
    logging.info("sswp_work4 took %8.3f / %d seconds", ncpu, nsec)
    # 20.510 / 30 seconds
    return



if __name__ == '__main__':
    sswp_init()

    sswp_vofeed()
    sswp_ggus()

    #t1 = threading.Thread(name='Wrk1Thread', target=sswp_work1)
    #t1.start()
    #t2 = threading.Thread(name='Wrk2Thread', target=sswp_work2)
    #t2.start()
    #t3 = threading.Thread(name='Wrk3Thread', target=sswp_work3)
    #t3.start()
    #t4 = threading.Thread(name='Wrk4Thread', target=sswp_work4)
    #t4.start()
    #
    #t1.join()
    #t3.join()
    #t4.join()
    #t2.join()
    #
    #sswp_site_readiness()                              # updates summary metric

    tis = time.time()
    cpt = time.process_time()
    ssdw_monit_SAM_HC_FTS_SR()                 # pydoop/OpenJDK not thread safe
    ssdw_monit_down_STS()
    ssdw_site_summary()
    #
    ssdw_monit_etf()
    ncpu = time.process_time() - cpt
    nsec = time.time() - tis
    logging.info("MonIT fetching took %8.3f / %d seconds", ncpu, nsec)

    sswp_write_summary_js()
    sswp_write_downtime_js()
    sswp_write_detail_json()
    #
    #glbTopology.write()
    #glbTickets.write()
    #glbSites.write()


#   sswp_dump()
    #import pdb; pdb.set_trace()
