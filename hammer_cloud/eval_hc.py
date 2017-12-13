#!/usr/bin/python
# ########################################################################### #
# python script to query the CMS job dashboard on HammerCloud job results,    #
#    calculate success rate and status, and write an SSB metric file and a    #
#    JSON document for MonIT. Script queries and updates for a specific       #
#    15 min time slot or, if no time specified, queries/uploads the 15 min    #
#    time slot that started 30 min ago and checks/updates the 15 min time     #
#    slot that started 75 min ago (to catch any very late arriving/processes  #
#    results. Script should be run several minutes into the 15 min time slot, #
#    i.e. hour plus 10, 25, 40, and 55 minutes.
#                                                                             #
# 2017-Nov-13   Stephan Lammel                                                #
# ########################################################################### #



import os, sys
import time, calendar
import fnmatch
import json
import getpass, socket
import urllib2
import requests
import argparse
import logging
import smtplib
from email.mime.text import MIMEText
# ########################################################################### #



EVHC_SSB_DIR = "."
EVHC_JSON_DIR = "./cache"
#EVHC_SSB_DIR = "/afs/cern.ch/user/c/cmssst/www/hammercloud"
#EVHC_JSON_DIR = "/data/cmssst/MonitoringScripts/hammer_cloud/cache"
EVHC_MONIT_URL = "http://monit-metrics-dev.cern.ch:10012/"
# ########################################################################### #



# ########################################################################### #



class ssbMetric:
    'Site Status Board metric class of the CMS Site Support team'

    def __init__(self, metricName, timeBin, timeInterval):
        self.metric_name = metricName
        self.time_bin = timeBin
        self.time_interval = timeInterval
        self.data = {}

    def addEntry(self, name, status, value):
        if name not in self.data:
            self.data[name] = {'status': status, 'value': value}

    def entries(self):
        return sorted(self.data.keys())

    def isEmpty(self):
        return (not bool(self.data))

    def writeSSBfile(self, file=sys.stdout):
        UTCStart = time.strftime("%Y-%m-%d+%H:%M",
                       time.gmtime(self.time_bin * self.time_interval))
        UTCEnd   = time.strftime("%Y-%m-%d+%H:%M",
                       time.gmtime((self.time_bin + 1) * self.time_interval))
        URL_JOB_DASHBOARD_HC_SITE = "http://dashb-cms-job.cern.ch/dashboard/templates/web-job2/#user=&refresh=0&table=Jobs&p=1&records=25&activemenu=0&usr=&site=%%s&submissiontool=&application=&activity=hctest&status=&check=terminated&tier=&date1=%s&date2=%s&sortby=ce&scale=linear&bars=20&ce=&rb=&grid=&jobtype=&submissionui=&dataset=&submissiontype=&task=&subtoolver=&genactivity=&outputse=&appexitcode=&accesstype=" % (UTCStart, UTCEnd)

        if ( self.metric_name == "hc15min" ):
            lbl = "15 Minutes"
        elif ( self.metric_name == "hc1day" ):
            lbl = "1 Day"
        else:
            lbl = "\"%s\"" % self.metric_name
        now = time.strftime("%Y-%b-%d %H:%M:%S UTC", time.gmtime())
        file.write(("#txt\n#\n# Site Support Team, HammerCloud %s Metric" +
            "\n#    written at %s by %s\n#    in account %s on node %s\n#   " +
            " maintained by cms-comp-ops-site-support-team@cern.ch\n#    htt" +
            "ps://twiki.cern.ch/twiki/bin/view/CMSPublic/...\n# ============" +
            "===========================================\n#\n") %
            (lbl, now, sys.argv[0], getpass.getuser(), socket.gethostname()))

        timeStamp = time.strftime("%Y-%m-%d %H:%M:%S",
            time.gmtime(self.time_bin * self.time_interval))
        for siteName in self.entries():
            if self.data[siteName]['value'] is not None:
                value = self.data[siteName]['value']
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
            url = URL_JOB_DASHBOARD_HC_SITE % siteName
            #
            file.write("%s\t%s\t%s\t%s\t%s\n" %
                (timeStamp, siteName, value, colour, url))

    def updateSSB(self):
        filePath = os.path.join(EVHC_SSB_DIR, self.metric_name + ".txt")
        #
        try:
            fileObj = open(filePath + "_new", 'w')
            try:
                self.writeSSBfile(fileObj)
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
        filePath = os.path.join(EVHC_JSON_DIR,
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
                logging.info("JSON string written to file in cache area")
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
            logging.error("[W]: No JSON file %s in cache area" % fileName)
        #
        return jsonString

    @classmethod
    def uploadJSONstring(myClass, jsonString):
        successFlag = False
        #
        try:
            # MonIT needs an array and without newline characters:
            requestsObj = requests.post(EVHC_MONIT_URL,
                data="[" + json.dumps(json.loads(jsonString)) + "]",
                headers={'Content-Type': "application/json; charset=UTF-8"},
                timeout=15)
            #requests.post('http://some.url/streamed', data=f, verify=False,
            #    cert=('/path/client.cert', '/path/client.key'))
            #requests.post('http://some.url/streamed', data=f, verify=False,
            #    cert='/path/client.cert')
        except requests.exceptions.ConnectionError:
            logging.error("[E]: Failed to upload JSON, connection error")
        except requests.exceptions.Timeout:
            logging.error("[E]: Failed to upload JSON, reached 15 sec timeout")
        except Exception as excptn:
            logging.error("[E]: Failed to upload JSON, %s" % str(excptn))
        else:
            if ( requestsObj.status_code == requests.codes.ok ):
                successFlag = True
                logging.info("JSON string uploaded to MonIT")
            else:
                logging.error("[E]: Failed to upload JSON, %d \"%s\"" %
                          requestsObj.status_code, requestsObj.text)
        #
        return successFlag

    def evalHC(self):
        """function to query CMS job dashboard and evaluate HC job results"""
        UTCStart = time.strftime("%Y-%m-%d+%H:%M",
                       time.gmtime(self.time_bin * self.time_interval))
        UTCEnd   = time.strftime("%Y-%m-%d+%H:%M",
                       time.gmtime((self.time_bin + 1) * self.time_interval))
        URL_JOB_DASHBOARD_HC = "http://dashb-cms-job.cern.ch/dashboard/request.py/jobsummary-plot-or-table2?user=&site=&submissiontool=&application=&activity=hctest&status=&check=terminated&tier=&sortby=site&ce=&rb=&grid=&jobtype=&submissionui=&dataset=&submissiontype=&task=&subtoolver=&genactivity=&outputse=&appexitcode=&accesstype=&inputse=&cores=&date1=%s&date2=%s&prettyprint" % (UTCStart, UTCEnd)
    
        #
        # get HammerCloud summary counts from the job dashboard:
        # ======================================================
        logging.info("Querying job dashboard for %s summary counts of %s UTC" %
            (self.metric_name, UTCStart.replace("+", " ")))
        urlHandle = None
        try:
            requestObj = urllib2.Request(URL_JOB_DASHBOARD_HC,
                                         headers={'Accept':'application/json'})
            urlHandle = urllib2.urlopen( requestObj )
            jsonString = urlHandle.read()
        except:
            logging.error("[E]: Failed to query job dashboard for HC job su" +
                          "mmary")
            return
        finally:
            if urlHandle is not None:
                urlHandle.close()
                del requestObj
            del urlHandle
        #
        # unpack JSON data of HC summary counts:
        hcStruct = json.loads( jsonString )

        statusCount = [0, 0, 0, 0]
        for siteStruct in hcStruct['summaries']:
            if ( siteStruct['name'][0:1] != "T" or
                 (not siteStruct['name'][1:2].isdecimal()) or 
                 siteStruct['name'][2:3] != "_" or
                 (not siteStruct['name'][3:5].isalpha()) or
                 (not siteStruct['name'][3:5].isupper()) or
                 siteStruct['name'][5:6] != "_" ):
                if ( siteStruct['name'] != "unknown" ):
                    logging.warning("Illegal CMS site name %s" %
                                    siteStruct['name'])
                continue
            sumTerm = siteStruct['terminated']
            sumCancel = siteStruct['cancelled']
            sumUnknown = siteStruct['allunk']
            sumSucces = siteStruct['app-succeeded']
            sumUnsucc = siteStruct['unsuccess']
            #
            if ( (sumTerm - sumCancel - sumUnknown) >= 1 ):
                # evaluate success rate:
                value = float(sumSucces - sumUnsucc) / \
                        float(sumTerm - sumCancel - sumUnknown)
                if ( value >= 0.90 ):
                    status = "ok"
                    statusCount[0] += 1
                elif ( value < 0.80 ):
                    status = "error"
                    statusCount[2] += 1
                else:
                    tierLevel = siteStruct['name'][1:2]
                    if ( tierLevel == "0" or tierLevel == "1" ):
                        status = "error"
                        statusCount[2] += 1
                    else:
                        status = "warning"
                        statusCount[1] += 1
                logging.debug("HC eval, %s: %s" % (siteStruct['name'], status))
            elif ( sumTerm > 0 ) or ( siteStruct['running'] > 0 ):
                status = "unknown"
                value = None
                statusCount[3] += 1
                logging.debug("HC eval, %s: %s" % (siteStruct['name'], status))
            else:
                continue
    
            # fill ssbMetric with site evaluation:
            self.addEntry(siteStruct['name'], status, value)

        logging.info("[I] HC%s results for %s UTC o/w/e/u = %d/%d/%d/%d" %
            (self.metric_name[2:], UTCStart.replace("+", " "), statusCount[0],
            statusCount[1], statusCount[2], statusCount[3]))



    def missingTemplateAlert(self):
        """function to check we have results for all functional T* templates"""
        URL_HAMMERCLOUD_HOME = "http://hammercloud.cern.ch/testdirs/cms/cms__hp.json"

        #
        # get HammerCloud main page information:
        # ======================================
        logging.info("Querying HammerCloud for home page information")
        urlHandle = None
        try:
            requestObj = urllib2.Request(URL_HAMMERCLOUD_HOME,
                                         headers={'Accept':'application/json'})
            urlHandle = urllib2.urlopen( requestObj )
            jsonString = urlHandle.read()
        except:
            logging.error("[E]: Failed to fetch HammerCloud home page inform" +
                          "ation")
            return
        finally:
            if urlHandle is not None:
                urlHandle.close()
                del requestObj
            del urlHandle
        #
        # unpack JSON data of HC summary counts:
        hpStruct = json.loads( jsonString )

        msgText = ""
        # loop over functional tests and check at least one site has results
        for funcTest in hpStruct['golden']:
            if ( funcTest['test_state'] != "running" ):
                continue
            templateName = funcTest['test_template_description']
            if (( templateName[:12] == "functional T" ) and
                  templateName[12:13].isdigit() ):
                siteList = funcTest['sites']
                nodataFlag = True
                for siteName in siteList:
                    if siteName in self.data:
                        # site in the template with data
                        nodataFlag = False
                        break
                if nodataFlag:
                    msgText += (("HC %s\n has no site with results!\n     ti" +
                                 "me: %s to %s\n     sites: %s\n\n") %
                                (templateName, funcTest['test_starttime'],
                                 funcTest['test_endtime'],
                                 ", ".join(funcTest['sites'])))
                    logging.warning("HC %s\n has no site with results" %
                                    templateName)

        if ( msgText != "" ):
            # email out an alert
            mimeObj = MIMEText(msgText)
            mimeObj['Subject'] = "HC template(s) without result"
            mimeObj['From'] = "cmssst@cern.ch"
            mimeObj['To'] = "lammel@fnal.gov"
            #smtpConnection = smtplib.SMTP('localhost')
            #smtpConnection.sendmail(mimeObj['From'], mimeObj['To'],
            #                        mimeObj.as_string())
            #smtpConnection.quit()
            #del smtpConnection
            del mimeObj
        del msgText
# ########################################################################### #



def evalHCpost(metricName, timeBin, timeInterval,
               ssbFlag, monitFlag, alertFlag):
    """function to query job dashboard and post initial HC 15min results"""
    #
    # create ssbMetric object for HC 15min/1hour/6hours/1day:
    metricObj = ssbMetric(metricName, timeBin, timeInterval)
    #
    # query CMS job dashboard, evaluate HC results, and fill metric:
    metricObj.evalHC()
    if ( metricObj.isEmpty() ):
        del metricObj
        return
    #
    if ssbFlag:
        # update the SSB file with the new HC 15min results:
        metricObj.updateSSB()
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
    if alertFlag:
        # check if results for any of the functional templates is missing
        metricObj.missingTemplateAlert()

    del jsonString
    del metricObj
    return



def verifyHC15min(timeBin, postFlag):
    """function to query job dashboard and verify initial HC 15min results"""
    #
    # create ssbMetric object for HC 15min:
    metricObj = ssbMetric("hc15min", timeBin, 900)
    #
    # query CMS job dashboard, evaluate HC 15min result, and fill metric:
    metricObj.evalHC()
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



def uploadHCcache(timeStamp, qhourFlag, hourFlag, qdayFlag, dayFlag):
    for fileName in os.listdir(EVHC_JSON_DIR):
        if fnmatch.fnmatch(fileName, "hc*.json_*_upload"):
            # filename matches our JSON re-upload filename pattern
            filePath = os.path.join(EVHC_JSON_DIR, fileName)
            fileAge = timeStamp - int( os.path.getmtime(filePath) )
            if ( fileAge >= 300 ):
                # only files older than 5 minutes are eligible for re-upload
                if ( qhourFlag and ( fileName[:13] == "hc15min.json_" )):
                    if not fileName[13:-7].isdigit():
                        continue
                elif ( hourFlag and ( fileName[:13] == "hc1hour.json_" )):
                    if not fileName[13:-7].isdigit():
                        continue
                elif ( qdayFlag and ( fileName[:13] == "hc6hour.json_" )):
                    if not fileName[13:-7].isdigit():
                        continue
                elif ( dayFlag and ( fileName[:12] == "hc1day.json_" )):
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



def cleanHCcache(timeStamp, qhourFlag, hourFlag, qdayFlag, dayFlag):
    for fileName in os.listdir(EVHC_JSON_DIR):
        if fnmatch.fnmatch(fileName, "hc*.json_*"):
            # filename matches our JSON filename pattern
            tbIndex = fileName.index("_") + 1
            if fileName[tbIndex:].isdigit():
                # only digits after the underscore identifies it as cache
                filePath = os.path.join(EVHC_JSON_DIR, fileName)
                fileAge = timeStamp - int( os.path.getmtime(filePath) )
                if ( fileAge >= 600 ):
                    # only files older than 10 minutes are eligible for cleanup
                    timeBin = int(fileName[tbIndex:])
                    if ( qhourFlag and ( fileName[:13] == "hc15min.json_" )):
                       if ( timeBin > int( timeStamp / 900 ) - 8 ):
                           continue
                    elif ( hourFlag and ( fileName[:13] == "hc1hour.json_" )):
                       if ( timeBin > int( timeStamp / 3600 ) - 8 ):
                           continue
                    elif ( qdayFlag and ( fileName[:13] == "hc6hour.json_" )):
                       if ( timeBin > int( timeStamp / 21600 ) - 6 ):
                           continue
                    elif ( dayFlag and ( fileName[:12] == "hc1day.json_" )):
                       if ( timeBin > int( timeStamp / 86400 ) - 2 ):
                           continue
                    else:
                       continue
                    logging.info("[I] Deleting file %s from JSON cache" %
                                 fileName)
                    print("would delete file %s" % fileName)
                    #os.unlink(filePath)
# ########################################################################### #



if __name__ == '__main__':
    #
    parserObj = argparse.ArgumentParser(description="Script to evaluate Hamm" +
        "erCloud job results (for the currently processable 15 minute, 1 hou" +
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
    if ( argStruct.v >= 2 ):
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
        # no argument
        timeStamp = int( time.time() )
        #
        if ( argStruct.qhour ):
            # evaluate HC 15min results for time bin that started 30 min ago
            # ==============================================================
            timeBin = int( timeStamp / 900 ) - 2
            # evaluate HC 15min, update SSB, write JSON to cache, and upload
            evalHCpost("hc15min", timeBin, 900,
                       argStruct.post, argStruct.post, False)
            #
            #
            # check HC 15min results for time bin that started 75 min ago
            # ===========================================================
            timeBin = int( timeStamp / 900 ) - 5
            # evaluate HC 15min and upload if different from initial evaluation
            verifyHC15min(timeBin, argStruct.post)
        #
        #
        if ( argStruct.hour ) and ( int( timeStamp / 900 ) % 4 == 0 ):
            # evaluate HC 1hour results for time bin that started 2 hours ago
            # ===============================================================
            timeBin = int( timeStamp / 3600 ) - 2
            evalHCpost("hc1hour", timeBin, 3600, False, argStruct.post, True)
        #
        #
        if ( argStruct.qday ) and ( int( timeStamp / 900 ) % 24 == 4 ):
            # evaluate HC 6hour results for time bin that started 7 hours ago
            # ===============================================================
            timeBin = int( timeStamp / 21600 ) - 1
            evalHCpost("hc6hour", timeBin, 21600, False, argStruct.post, False)
        #
        #
        if ( argStruct.day ) and ( int( timeStamp / 900 ) % 96 == 4 ):
            # evaluate HC 1day results for time bin that started 25 hours ago
            # ===============================================================
            timeBin = int( timeStamp / 86400 ) - 1
            evalHCpost("hc1day", timeBin, 86400,
                       argStruct.post, argStruct.post, False)
    else:
        if argStruct.timeSpec.isdigit():
            # argument should be the time in seconds for which to evaluate HC
            timeStamp = int( argStruct.timeSpec )
        else:
            # argument should be the time in "YYYY-Mmm-dd HH:MM" format
            timeStamp = calendar.timegm( time.strptime("%s UTC" %
                argStruct.timeSpec, "%Y-%b-%d %H:%M %Z") )
        #
        #
        if ( argStruct.qhour ):
            # evaluate/upload HC 15min results for time bin
            # =============================================
            timeBin = int( timeStamp / 900 )
            # evaluate HC 15min, write and upload JSON
            evalHCpost("hc15min", timeBin, 900, False, argStruct.post, False)
        #
        #
        if ( argStruct.hour ) and ( int( timeStamp / 900 ) % 4 == 0 ):
            # evaluate/upload HC 1hour results for time bin
            # =============================================
            timeBin = int( timeStamp / 3600 )
            # evaluate HC 1hour, write and upload JSON
            evalHCpost("hc1hour", timeBin, 3600, False, argStruct.post, False)
        #
        #
        if ( argStruct.qday ) and ( int( timeStamp / 900 ) % 24 == 0 ):
            # evaluate/upload HC 6hour results for time bin
            # =============================================
            timeBin = int( timeStamp / 21600 )
            # evaluate HC 6hour, write and upload JSON
            evalHCpost("hc6hour", timeBin, 21600, False, argStruct.post, False)
        #
        #
        if ( argStruct.day ) and ( int( timeStamp / 900 ) % 96 == 0 ):
            # evaluate/upload HC 1day results for time bin
            # ============================================
            timeBin = int( timeStamp / 86400 )
            # evaluate HC 1day, write and upload JSON
            evalHCpost("hc1day", timeBin, 86400, False, argStruct.post, False)
    #
    #
    # re-upload any previous JSON post failures
    # =========================================
    if ( argStruct.post ):
        uploadHCcache(timeStamp, argStruct.qhour, argStruct.hour,
                                 argStruct.qday, argStruct.day)
    #
    #
    # cleanup files in JSON cache area
    # ================================
    if ( argStruct.clean ):
        cleanHCcache(timeStamp, argStruct.qhour, argStruct.hour,
                                argStruct.qday, argStruct.day)
    #import pdb; pdb.set_trace()
