#!/usr/bin/python
# ########################################################################### #
# python script to query the CMS job dashboard on FTS job results,    #
#    calculate success rate and status, and write an SSB metric file and a    #
#    JSON document for MonIT. Script queries and updates for a specific       #
#    15 min time slot or, if no time specified, queries/uploads the 15 min    #
#    time slot that started 30 min ago and checks/updates the 15 min time     #
#    slot that started 75 min ago (to catch any very late arriving/processes  #
#    results. Script should be run several minutes into the 15 min time slot, #
#    i.e. hour plus 10, 25, 40, and 55 minutes.
#                                                                             #
#Last modification:2018-Jun-13  Maria P. Acosta 
#                               Based on the HC script by Stephan Lammel      #
# ########################################################################### #


from __future__ import division
import os, sys
import time, calendar
import fnmatch
import dateutil.parser
import traceback
import monitES
from decimal import *
from datetime import datetime, timedelta
from lib import dashboard,sites,url
import sys, os
import simplejson as json
import getpass, socket
import urllib2
import requests
import argparse
import logging
import smtplib
from email.mime.text import MIMEText
import pprint
# ########################################################################### #



#EVFTS_SSB_DIR = "."
EVFTS_SSB_DIR = "/afs/cern.ch/user/c/cmssst/www/fts_links"
EVFTS_JSON_DIR = "./cache"
EVFTS_MONIT_URL = "http://monit-metrics-dev.cern.ch:10012/"
# ########################################################################### #
class Site:

    def __init__(self, cms_name):
        self.site_name = cms_name
        self.endpoints = self.getEndpoints()
        self.tier = sites.getTier(self.site_name)
    #In progress -> secondary
        self.fts_server = "https://testurl.cern.ch/"

    #Statistical attributes
        self.totalrecords = 0
        self.successful = 0
        self.totalfailed = 0
        
    #Number of failed fts files categorized by type (undecided is not counted in the final rate)
        self.failed = dict()
        self.failed['undecided']=0
        self.failed['quota']=0
        self.failed['permissions']=0
        self.failed['unreachable']=0
        self.failed['file']=0
        self.failed['other']=0

    #Success rate before categorizing error messages
        self.status = ""
        self.quality = 0.0

    def calculate(self):
        for k in self.failed.iterkeys():
          self.totalfailed+=self.failed[k]

        fl_quality = 0.0

        if self.totalrecords > 0:
            self.quality = (1-(self.totalfailed/self.totalrecords))
        else:
            self.quality = -1
            self.color = "white"
        if self.quality >= 0.8:
            self.status = "ok"
        elif self.quality >= 0.4 and self.quality < 0.8:
            self.status = "warning"
        elif self.quality < 0.4:
            self.status = "error"
        else:
           self.quality = -1
           self.color = "white"

    def getEndpoints(self):
        try:
            return sites.getSRMEndpoints()[self.site_name]
        except:
            return None

# ########################################################################### #



class ssbMetric:
    'Site Status Board metric class of the CMS Site Support team'

    def __init__(self, metricName, timeBin, timeInterval):
        self.metric_name = metricName
        self.time_bin = timeBin
        self.time_interval = timeInterval
        self.data = {}
        self.active_sites=[]
        self.count=0

    def addEntry(self, name, status, value):
        if name not in self.data:
            self.data[name] = {'status': status, 'value': value}

    def addEntryFromSite(self, site):
        #if site.site_name not in self.data:
        self.data[site.site_name] = {'status': site.status, 'value': site.quality}
        #print "Appending " + site.site_name
        #pprint.pprint(self.data[site.site_name])

    def entries(self):
        return sorted(self.data.keys())

    def isEmpty(self):
        return (not bool(self.data))

    def writeSSBfile(self,dateFrom, file=sys.stdout):
        dateFormat="%Y-%m-%d %H:%M:%S"
        date_from_str = datetime.strftime(dateFrom, dateFormat)
        dateFr = dateFrom.strftime('%s.%f')
        d_in_ms = int(float(dateFr)*1000)
        d_in_ns = int(float(dateFr)*1000000000)
        #print d_in_ns
        d_in_ns_s=str(int(d_in_ns))
        dateTo = dateFrom + timedelta(minutes=15)
        date_to_str = datetime.strftime(dateTo, dateFormat)
        if ( self.metric_name == "fts15min" ):
            lbl = "15 Minutes"
        elif ( self.metric_name == "fts1day" ):
            lbl = "1 Day"
        elif ( self.metric_name == "fts1hour" ):
            lbl = "1 Hour"
        
        else:
            lbl = "\"%s\"" % self.metric_name
        now = time.strftime("%Y-%b-%d %H:%M:%S UTC", time.gmtime())
        file.write(("#txt\n#\n# Site Support Team, FTS %s Metric" +
            "\n#    written at %s by %s\n#    in account %s on node %s\n#   " +
            " maintained by cms-comp-ops-site-support-team@cern.ch\n#    htt" +
            "ps://twiki.cern.ch/twiki/bin/view/CMSPublic/...\n# ============" +
            "===========================================\n#\n") %
            (lbl, now, sys.argv[0], getpass.getuser(), socket.gethostname()))

        timeStamp = date_from_str
        for siteName in self.entries():
            if self.data[siteName]['value'] is not None:
                value = self.data[siteName]['value'] * 100.0
            else:
                value = -1.0
            if ( self.data[siteName]['status'] == "ok" ):
                colour = "green"
            elif ( self.data[siteName]['status'] == "warning" ):
                colour = "yellow"
            elif ( self.data[siteName]['status'] == "error" ):
                colour = "red"
            else:
                colour = "white"
            url = "testURL.cern.ch"
            #
            print lbl+" "+siteName+" value="+str(value)+",colour="+colour+" "+date_from_str
            if value >= 0:
                file.write("%s\t%s\t%.1f\t%s\t%s\n" %
                    (timeStamp, siteName, value, colour, url))
            else:
                file.write("%s\t%s\tN/A\twhite\t%s\n" %
                    (timeStamp, siteName, url))

        print "Total records = "+str(self.count)+" "+date_from_str

    def updateSSB(self,dateFrom):
        dateFormat="%Y-%m-%dT%H:%M:%S"
        date_from_str = datetime.strftime(dateFrom, dateFormat)
        filePath = os.path.join(EVFTS_SSB_DIR, self.metric_name +".txt")
        #
        try:
            fileObj = open(filePath + "_new", 'w')
            try:
                self.writeSSBfile(dateFrom,fileObj)
                myRename = True
            except:
                myRename = False
                logging.error("[E]: Failed to write new SSB file")
            finally:
                fileObj.close()
            #
            if myRename:
                os.chmod(filePath + "_new", 0644)
                os.rename(filePath + "_new", filePath)
                logging.info("[I]: SSB file updated")
        except:
            logging.error("[E]: Failed to open new SSB file")

    def compJSONstring(self):
        # time in milliseconds, middle of the timebin
        jsonString = ("{\n \"producer\": \"cmssst\",\n" +
                         " \"type\": \"ssbmetric\",\n" +
                         " \"path\": \"%s\",\n" +
                         " \"timestamp\": %d,\n" +
                         " \"type_prefix\": \"raw\",\n" +
                         " \"data\": [") % (self.metric_name, ((self.time_bin *
                            self.time_interval) + self.time_interval/2) * 1000)

        commaFlag = False
        for siteName in self.entries():
            if commaFlag:
                jsonString += ",\n    { \"name\": \"%s\",\n" % siteName
            else:
                jsonString += "\n    { \"name\": \"%s\",\n" % siteName
            jsonString += ("      \"status\": \"%s\",\n" %
                self.data[siteName]['status'])
            if self.data[siteName]['value'] is not None:
               jsonString += ("      \"value\": %.3f\n" %
                   self.data[siteName]['value'])
            else:
               jsonString += "      \"value\": null\n"
            jsonString += "    }"
            commaFlag = True
        jsonString += "\n ]\n}"
        return jsonString

    def compJSONcacheFileName(self):
        filePath = os.path.join(EVFTS_JSON_DIR,
                              "%s.json_%d" % (self.metric_name, self.time_bin))
        return filePath

    @classmethod
    def writeJSONfile(myClass, filePath, jsonString):
        successFlag = False
        #
        try:
            fileObj = open(filePath, 'w')
            try:
                fileObj.write( jsonString )
                successFlag = True
                #logging.info("JSON string written to file in cache area")
            except:
                fileName = os.path.basename(filePath)
                logging.error("[E]: Failed to write JSON file %s to cache area"
                              % fileName)
                os.unlink(filePath)
            finally:
                fileObj.close()
                os.chmod(filePath, 0644)
        except:
            fileName = os.path.basename(filePath)
            logging.error(("[E]: Failed to write-open JSON file %s in cache " +
                           "area") % fileName)
        #
        return successFlag

    @classmethod
    def readJSONfile(myClass, filePath):
        jsonString = "{}"
        try:
            fileObj = open(filePath, 'r')
            try:
                jsonString = fileObj.read()
            except:
                fileName = os.path.basename(filePath)
                logging.error(("[E]: Failed to read JSON file %s from cache " +
                               "area") % fileName)
            finally:
                fileObj.close()
        except:
            fileName = os.path.basename(filePath)
            logging.error("[W]FTSile %s in cache area" % fileName)
        #
        return jsonString

    @classmethod
    def uploadJSONstring(myClass, jsonString):
        successFlag = False
        #
        try:
            # MonIT needs an array and without newline characters:
            # Disabled for now
            #requestsObj = requests.post(EVFTS_MONIT_URL,
            #    data="[" + json.dumps(json.loads(jsonString)) + "]",
            #    headers={'Content-Type': "application/json; charset=UTF-8"},
            #    timeout=15)
            #requests.post('http://some.url/streamed', data=f, verify=False,
            #    cert=('/path/client.cert', '/path/client.key'))
            #requests.post('http://some.url/streamed', data=f, verify=False,
            #    cert='/path/client.cert')
            pass
        #except requests.exceptions.ConnectionError:
         #   logging.error("[E]: Failed to upload JSON, connection error")
        #except requests.exceptions.Timeout:
         #   logging.error("[E]: Failed to upload JSON, reached 15 sec timeout")
        
        #except Exception as excptn:
         #   logging.error("[E]: Failed to upload JSON, %s" % str(excptn))
       #else:
        except:
            #if ( requestsObj.status_code == requests.codes.ok ):
                successFlag = True
            #    logging.info("JSON string uploaded to MonIT")
            #else:
            #    logging.error("[E]: Failed to upload JSON, %d \"%s\"" %
             #             requestsObj.status_code, requestsObj.text)
        #
        return successFlag
####################
      #Should dateto be added??
    def evaluateFTS(self, dateFrom, interval=15):
        #dateTo = dateFrom + timedelta(minutes=interval)
        dateTo = dateFrom + timedelta(minutes=interval)
        #OUTPUT_FILE_NAME = os.path.join(options.outputDir,"fts15min.txt")
        print "Retrieving ES data for FTS files from " + str(dateFrom) + " to " + str(dateTo)
        try:
            data = monitES.getResults(dateFrom,dateTo)
            logging.info("[I] Processing monit data ....")
            for tier in data['responses']:
                count = 0
                for src in tier['aggregations']['source']['buckets']:
                    src_data=src['key'].split("://")
                    if len(src_data) < 2:
                         logging.info("[I] Got a bad SRM response: "+src['key'])
                         continue
                    src_se=src_data[1]
                    src_protocol=src_data[0]
                    src_site = self.getOwnerSite(src_se)
                    if src_site:
                        #print "Source start "+src_site
                        if self.siteExists(src_site):
                            source=self.siteByName(src_site)
                        else:
                            source=Site(src_site)
                            self.active_sites.append(source)

                        #print len(self.active_sites)
                        for dest in src['dest']['buckets']:
                            dest_data=dest['key'].split("://")
                            if len(dest_data) < 2:
                                logging.info("[I] Got a bad SRM response: "+dest['key'])
                                continue
                            dest_se=dest_data[1]
                            dest_protocol=dest_data[0]
                            dest_site = self.getOwnerSite(dest_se)
                            if dest_site:

                                if self.siteExists(dest_site):
                                    destination=self.siteByName(dest_site)
                                else:
                                    destination=Site(dest_site)
                                    self.active_sites.append(destination)
                                n_files = 0
                                for fts in dest['reason']['buckets']:
                                    status = fts['key']
                                    n_files = fts['doc_count']
                                    count += n_files
                                    if status:
                                        self.blame(status,n_files,source,destination)
                                        continue
                                    else:
                                        source.successful += n_files
                                        source.totalrecords += n_files
                    else:
                        continue
            self.count = count
        except Exception:
            print(traceback.format_exc())
        self.finish()
        logging.info("[I] FTS%s results were successfully stored")

    def finish(self):
        for vof_site in sites.getSites():
            obj = self.siteByName(vof_site)
            if obj:
                obj.calculate()
                self.addEntryFromSite(obj)   
            else:
                self.addEntry(vof_site,"white",-1.0)

    #def finish(self):
    #    for site in self.active_sites:
    #        site.calculate()
    #        self.addEntryFromSite(site)
            #print site.totalrecords
            #pprint.pprint(site.failed)


    def siteByName(self,sitename):
        return next(iter(filter(lambda site: site.site_name == sitename,  self.active_sites)),None) 

    def siteExists(self,nsite):
        if next(iter(filter(lambda site: site.site_name == nsite, self.active_sites)),None):
            return True
        else:
            return False

    def getOwnerSite(self,endpt_hostname):
        try:
            return sites.getInvertedSRMEndpoints()[endpt_hostname]
        except:
            return None

    def blame(self,message,n_files,src,dest):
       category = message.split('[')[0].strip()
       #print category
       if "SOURCE" in category:
            self.failType(message,n_files,src)
       elif "DESTINATION" in category:
            self.failType(message,n_files,dest)
       elif "TRANSFER" in category:
            self.failType(message,n_files,src)
            #dest.failed['other'] += n_files
            #dest.totalrecords += n_files
       else:
            src.totalrecords += n_files
            src.successful += n_files

    def failType (self,message,n_files,site):
      srch = message.lower()
      site.totalrecords += n_files
      if 'over-load limit' or 'connection limit' in srch:
          site.failed['quota'] += n_files
          return
      if 'timeout' or 'unreachable' or 'timed out' in srch:
          site.failed['unreachable'] += n_files
          return
      elif 'no such file' or 'an end of file' or 'file exists' in srch:
          site.failed['file'] += n_files
          return
      elif 'protocol family' in srch:
          site.failed['other'] += n_files
          return
      else:
          site.failed['other'] += n_files
          return

# ########################################################################### #


def evalFTSpost(metricName, dateFrom, interval, ssbFlag, monitFlag):
    """function to query job dashboard and post initial HC 15min results"""
    #
    # create ssbMetric object for FTS 15min/1hour/6hours/1day:
    metricObj = ssbMetric(metricName, 1000, 15)
    #
    metricObj.evaluateFTS(dateFrom, interval)
    if ( metricObj.isEmpty() ):
        del metricObj
        return
    #
    if ssbFlag:
        # update the SSB file with the new HC 15min results:
        metricObj.updateSSB(dateFrom)
    #
    # flatten ssbMetric object into JSON string:
    jsonString = metricObj.compJSONstring()
    #
    filePath = metricObj.compJSONcacheFileName()
    # write JSON string into a file in the cache area
    ssbMetric.writeJSONfile(filePath, jsonString)
    #
    if monitFlag:
        # upload JSON string to MonIT
        successFlag = ssbMetric.uploadJSONstring( jsonString )
        if ( not successFlag ):
            ssbMetric.writeJSONfile(filePath + "_upload", jsonString)
        del successFlag
    del filePath
    #
    #
    del jsonString
    del metricObj
    return

def verifyFTS15min(dateFrom, interval, postFlag):
    """function to query job dashboard and verify initial HC 15min results"""
    #
    # create ssbMetric object for HC 15min:
#CHECK THIS??
#wth is timebin -> making it 1000 (?) for now
    #metricObj = ssbMetric("fts15min", timeBin, 900)
    metricObj = ssbMetric("fts15min", 1000, 900)
    #
    # query CMS job dashboard, evaluate HC 15min result, and fill metric:
    metricObj.evaluateFTS(dateFrom,interval)
    if ( metricObj.isEmpty() ):
        del metricObj
        return
    #
    # flatten ssbMetric object into JSON string:
    nowJSONstring = metricObj.compJSONstring()
    #
    # read initial HC 15min JSON file into a string:
    filePath = metricObj.compJSONcacheFileName()
    oldJSONstring = ssbMetric.readJSONfile(filePath)
    #
    # compare the two strings:
    if ( nowJSONstring != oldJSONstring ):
        ssbMetric.writeJSONfile(filePath, nowJSONstring)
        #
        if postFlag:
            successFlag = ssbMetric.uploadJSONstring( nowJSONstring )
            #
            if ( not successFlag ):
                ssbMetric.writeJSONfile(filePath + "_upload", nowJSONstring)
                # JSON upload and write to cache failed, not much more we can do
            del successFlag

    del oldJSONstring
    del filePath
    del nowJSONstring
    del metricObj
    return



def uploadFTScache(timeStamp, qhourFlag, hourFlag, qdayFlag, dayFlag):
    for fileName in os.listdir(EVFTS_JSON_DIR):
        if fnmatch.fnmatch(fileName, "fts*.json_*_upload"):
            # filename matches our JSON re-upload filename pattern
            filePath = os.path.join(EVFTS_JSON_DIR, fileName)
            fileAge = timeStamp - int( os.path.getmtime(filePath) )
            if ( fileAge >= 300 ):
                # only files older than 5 minutes are eligible for re-upload
                if ( qhourFlag and ( fileName[:13] == "fts15min.json_" )):
                    if not fileName[13:-7].isdigit():
                        continue
                elif ( hourFlag and ( fileName[:13] == "fts1hour.json_" )):
                    if not fileName[13:-7].isdigit():
                        continue
                elif ( qdayFlag and ( fileName[:13] == "fts6hour.json_" )):
                    if not fileName[13:-7].isdigit():
                        continue
                elif ( dayFlag and ( fileName[:12] == "fts1day.json_" )):
                    if not fileName[12:-7].isdigit():
                        continue
                else:
                    continue
                #
                # read JSON file into string
                jsonString = ssbMetric.readJSONfile(filePath)
                if ( jsonString != "{}" ):
                    # upload JSON string to MonIT
                    successFlag = ssbMetric.uploadJSONstring(jsonString)
                    if successFlag:
                        os.unlink(filePath)
                        logging.info("[I] File %s from JSON cache uploaded" %
                                     fileName)



def cleanFTScache(timeStamp, qhourFlag, hourFlag, qdayFlag, dayFlag):
    for fileName in os.listdir(EVFTS_JSON_DIR):
        if fnmatch.fnmatch(fileName, "fts*.json_*"):
            # filename matches our JSON filename pattern
            tbIndex = fileName.index("_") + 1
            if fileName[tbIndex:].isdigit():
                # only digits after the underscore identifies it as cache
                filePath = os.path.join(EVFTS_JSON_DIR, fileName)
                fileAge = timeStamp - int( os.path.getmtime(filePath) )
                if ( fileAge >= 600 ):
                    # only files older than 10 minutes are eligible for cleanup
                    timeBin = int(fileName[tbIndex:])
                    if ( qhourFlag and ( fileName[:13] == "fts15min.json_" )):
                       if ( timeBin >= int( timeStamp / 900 ) - 9 ):
                           continue
                    elif ( hourFlag and ( fileName[:13] == "fts1hour.json_" )):
                       if ( timeBin >= int( timeStamp / 3600 ) - 8 ):
                           continue
                    elif ( qdayFlag and ( fileName[:13] == "fts6hour.json_" )):
                       if ( timeBin >= int( timeStamp / 21600 ) - 6 ):
                           continue
                    elif ( dayFlag and ( fileName[:12] == "fts1day.json_" )):
                       if ( timeBin >= int( timeStamp / 86400 ) - 2 ):
                           continue
                    else:
                       continue
                    logging.info("[I] Deleting file %s from JSON cache" %
                                 fileName)
                    os.unlink(filePath)
# ########################################################################### #



if __name__ == '__main__':
    #
    parserObj = argparse.ArgumentParser(description="Script to evaluate FTS " +
        "file success rate (for the currently processable 15 minute, 1 hou" +
        "r, 6 hour, and 1 day time bin). Results are posted to the SSB and M" +
        "onIT.")
    parserObj.add_argument("-q", dest="qhour", action="store_true",
                                 help="restrict evaluation to 15 min results")
    parserObj.add_argument("-1", dest="hour", action="store_true",
                                 help="restrict evaluation to 1 hour results")
    parserObj.add_argument("-6", dest="qday", action="store_true",
                                 help="restrict evaluation to 6 hours results")
    parserObj.add_argument("-d", dest="day", action="store_true",
                                 help="restrict evaluation to 1 day results")
    parserObj.add_argument("-P", dest="post", default=True,
        action="store_false", help="do not post results to SSB or MonIT")
    parserObj.add_argument("-C", dest="clean", default=True,
        action="store_false", help="do not clean JSON files from cache area")
    parserObj.add_argument("-v", action="count", default=0, help="increase v" +
        "erbosity")
    parserObj.add_argument("timeSpec", nargs="?", metavar="Time Specification",
                           help="time specification, either an integer with " +
                                "the time in seconds since the epoch or time" +
                                " in the format \"YYYY-Mmm-dd HH:MM\"")
    argStruct = parserObj.parse_args()
    if   ( argStruct.v >= 2 ):
        logging.basicConfig(format="%(levelname)s: %(message)s",
                            level=logging.DEBUG)
    elif ( argStruct.v == 1 ):
        logging.basicConfig(format="%(message)s", level=logging.INFO)
    else:
        logging.basicConfig(format="%(message)s", level=logging.WARNING)
    if not ( argStruct.qhour or argStruct.hour or argStruct.qday or
             argStruct.day ):
        argStruct.qhour = True
        argStruct.hour = True
        argStruct.qday = True
        argStruct.day = True
    #
    #
    if argStruct.timeSpec is None:
    #if argStruct.timeSpec:
        # no argument
        dateFrom = datetime.now()
        #
        if ( argStruct.qhour ):
            # evaluate HC 15min results for time bin that started 30 min ago
            # ==============================================================
            # evaluate HC 15min, update SSB, write JSON to cache, and upload
            evalFTSpost("fts15min", dateFrom, 15, argStruct.post, argStruct.post)
            #
            #
            # check HC 15min results for time bin that started 75 min ago
            # ===========================================================
            # evaluate HC 15min and upload if different from initial evaluation
            verifyFTS15min(dateFrom, 15, argStruct.post)
        #
        #
        #if ( argStruct.hour ) and ( int( timeStamp / 900 ) % 4 == 0 ):
        if ( argStruct.hour ):
            # evaluate HC 1hour results for time bin that started 2 hours ago
            # ===============================================================
            #evalHCpost("hc1hour", timeBin, 3600, False, argStruct.post, True)
            evalFTSpost("fts1hour", dateFrom, 60, False, argStruct.post)
        #
        #
        if ( argStruct.qday ):
            # evaluate HC 6hour results for time bin that started 7 hours ago
            # ===============================================================
            #evalHCpost("hc6hour", timeBin, 21600, False, argStruct.post, False)
            evalFTSpost("fts6hour", dateFrom, 360, False, argStruct.post)
        #
        #
## TODO ------>>>>  Getting 1d data from MOnit would be TOOO much
        #if ( argStruct.day ) and ( int( timeStamp / 900 ) % 96 == 4 ):
            # evaluate HC 1day results for time bin that started 25 hours ago
            # ===============================================================
        #    timeBin = int( timeStamp / 86400 ) - 1
        #    evalHCpost("hc1day", timeBin, 86400,
        #               argStruct.post, argStruct.post, False)
    else:
            # argument should be the time in "YYYY-Mmm-dd HH:MM" format
        datetmp = dateutil.parser.parse(argStruct.timeSpec, ignoretz=True)
        #
        if ( argStruct.qhour ):
            # evaluate/upload HC 15min results for time bin
            # =============================================
            # evaluate HC 15min, write and upload JSON
            #Why isn't validation being done here?
            dateFrom = datetmp - timedelta(minutes=datetmp.minute % 15,
                             seconds=datetmp.second,
                             microseconds=datetmp.microsecond)
        
            evalFTSpost("fts15min", dateFrom, 15, argStruct.post, argStruct.post)
        #
        #
        #if ( argStruct.hour ) and ( int( timeStamp / 900 ) % 4 == 0 ):
        if ( argStruct.hour ):
            # evaluate/upload HC 1hour results for time bin
            # =============================================
            # evaluate HC 1hour, write and upload JSON
            dateFrom = datetmp - timedelta(minutes=datetmp.minute % 60,
                             seconds=datetmp.second,
                             microseconds=datetmp.microsecond)
 
            evalFTSpost("fts1hour", dateFrom, 60, argStruct.post, argStruct.post)
    #
    #
    # re-upload any previous JSON post failures
    # =========================================
    timeStamp = time.time()
    #print timeStamp

    if ( argStruct.post ):
        uploadFTScache(timeStamp, argStruct.qhour, argStruct.hour,
                                 argStruct.qday, argStruct.day)
    #
    #
    # cleanup files in JSON cache area
    # ================================
    if ( argStruct.clean ):
        cleanFTScache(timeStamp, argStruct.qhour, argStruct.hour,
                                argStruct.qday, argStruct.day)
        # cleanFTScache(timeStamp, argStruct.qhour, argStruct.hour,
        #                        argStruct.qday, argStruct.day)
    
    #import pdb; pdb.set_trace()

