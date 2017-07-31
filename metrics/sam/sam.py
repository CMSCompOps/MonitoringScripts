#!/usr/bin/python

''''
This script fetches the SAM success rate from the dashboard 
and writes a textfile as input for the SAM metric

Inputs: Starting Timestamp in format "YYYY-mm-dd-hh-mm", Directory in which to output data
Output: Text file in current directory, named Hammercloud.txt

'''

from lib import dashboard, sites, url
from datetime import datetime, timedelta
import  os
import dateutil.parser
from sys import exit
import json
from optparse import OptionParser

def  main():
    parser = OptionParser(usage="usage: %prog [options] filename",
                          version="%prog 1.0")
    parser.add_option("-d", "--date",
                      dest="inputDate",
                      help="date from which to fetch the results for HC in format %Y-%m-%dT%H:%M:%SZ ")
    parser.add_option("-o", "--outputDir",
                      dest="outputDir",
                      help="Directory in which to save the output")
    (options, args) = parser.parse_args()
    if options.inputDate is None:
        print "Please input a date with the --date option"
        exit(-1)
    else:
        try:
            datetmp = dateutil.parser.parse(options.inputDate, ignoretz=True)
        except:
            print "I couldn't recognize the date, please give me one like 2015-12-31T23:59:59Z"
            exit(-1)
    if options.outputDir is None:
        print "Please add a directory with option --outputDir"
        exit(-1)
    else:
        if os.path.isdir(options.outputDir) == False:
            print options.outputDir + " is not a valid directory or you don't have read permissions"
            exit(-1)
# Constants
    interval = 30
    dateFrom = datetmp- timedelta(minutes=datetmp.minute % interval,
                             seconds=datetmp.second,
                             microseconds=datetmp.microsecond)
    dateTo = dateFrom + timedelta(minutes=interval)
    dateFormat = "%Y-%m-%dT%H:%M:%SZ"
    dateFromStr = datetime.strftime(dateFrom, dateFormat)
    print dateFromStr
    dateToStr = datetime.strftime(dateTo, dateFormat)
    OUTPUT_FILE_NAME = os.path.join(options.outputDir,"sam.txt")
    print "Getting SAM Score from " + str(dateFrom) + " to " + str(dateTo)
    samUrl = "http://wlcg-sam-cms.cern.ch/dashboard/request.py/getstatsresultsmin?profile_name=CMS_CRITICAL_FULL&plot_type=quality&start_time=%s&end_time=%s&granularity=single&view=siteavl" % (dateFromStr, dateToStr)    
    print samUrl
    # Download the url or die
    try:
        print "Fetching url : " + samUrl
        jsonStr = url.read(samUrl)
        samInfo = json.loads(jsonStr)
    except:
        exit(100)
    print "Data retrieved!"
    sitesfromDashboard = []
    for samSummary in samInfo['data']:
        sitesfromDashboard.append(samSummary['name'])
    print sitesfromDashboard
    samScoreSites = []
    print"Getting SAM for all sites"
    for site in sitesfromDashboard:
        for samSummary in samInfo['data']:
            if samSummary['name'] == site:
                try:
                    siteOK = float(samSummary['data'][0]['OK'])
                    siteCritical = float(samSummary['data'][0]['CRIT'])
                    siteSched = float(samSummary['data'][0]['SCHED'])
                    if (siteOK + siteCritical + siteSched) > 0.0:
                        siteAvailabilityNum = (float(siteOK) / (float(siteOK + siteCritical + siteSched)))*100.0
                        siteAvailability = int(siteAvailabilityNum)
                        if siteAvailabilityNum > 89.9:
                            siteColor = "cOk"
                        elif (sites.getTier(site) == 2 or sites.getTier(site) == 3)and siteAvailabilityNum > 79.9:
                            siteColor = "cOk" 
                        else:
                            siteColor = "cNotOk"
                    else:
                        siteAvailability = "n/a"
                        siteAvailabilityNum = None
                        siteColor = "cNA"
                except:
                    siteAvailability = "Error"
                    siteAvailabilityNum = None
                    siteColor = "cError"
                print site + "  OK " + str(siteOK) + " CRIT " + str(siteCritical) + " SCHED " + str(siteSched) + " SCORE : " + str(siteAvailability) 
                samScoreSites.append(dashboard.entry(date = dateFrom.strftime("%Y-%m-%d %H:%M:%S"), name = site, value = siteAvailability, color = siteColor, url = getSuccessrateUrl (site, dateFrom, dateTo), nvalue=siteAvailabilityNum))
    print str(samScoreSites)
    if len(samScoreSites) > 1 : 
        OutputFile = open(OUTPUT_FILE_NAME, 'w')
        for site in samScoreSites:
            if site.name != "unknown":
                OutputFile.write(str(site) + '\n')
        print "\n--SAM Score output written to %s" % OUTPUT_FILE_NAME
        OutputFile.close()
    else:
        print "There's no data, I quit!"

def getSuccessrateUrl (site, dateFrom, dateTo):
    dateFormat = "%Y%%2F%m%%2F%d%%20%H%%3A%M" 
    dateFromStr = datetime.strftime(dateFrom, dateFormat)
    dateToStr = datetime.strftime(dateTo, dateFormat)
    return "http://wlcg-sam-cms.cern.ch/templates/ember/#/historicalsmry/heatMap?end_time=%s&granularity=Default&group=AllGroups&profile=CMS_CRITICAL_FULL&site=%s&site_metrics=undefined&start_time=%s&time=Enter%%20Date...&type=Availability%%20Ranking%%20Plot&view=Site%%20Availability" % (dateToStr, site, dateFromStr)

if __name__ == '__main__':
    main()
