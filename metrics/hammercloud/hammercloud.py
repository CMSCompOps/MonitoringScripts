#!/usr/bin/python

''''
This script fetches the HammerCloud job success rate from the dashboard 
and writes a textfile as input for the HammerCloud metric

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
# Constants:
    # Dashboard API for Hammercloud
    # replace (site, startTimeStamp, endTimeStamp)
    interval = 15
    dateFrom = datetmp- timedelta(minutes=datetmp.minute % interval,
                             seconds=datetmp.second,
                             microseconds=datetmp.microsecond)
    dateTo = dateFrom + timedelta(minutes=interval)
    dateFormat = "%Y-%m-%d+%H%%3A%M"
    dateFromStr = datetime.strftime(dateFrom, dateFormat)
    dateToStr = datetime.strftime(dateTo, dateFormat)
    OUTPUT_FILE_NAME = os.path.join(options.outputDir,"hammercloud.txt")
    print "Calcuating Hammercloud Score from " + str(dateFrom) + " to " + str(dateTo)
    urlHC = "http://dashb-cms-job.cern.ch/dashboard/request.py/jobsummary-plot-or-table2?user=&site=&submissiontool=&application=&activity=hctest&status=&check=terminated&tier=&sortby=site&ce=&rb=&grid=&jobtype=&submissionui=&dataset=&submissiontype=&task=&subtoolver=&genactivity=&outputse=&appexitcode=&accesstype=&inputse=&cores=&date1=%s&date2=%s&prettyprint" % (dateFromStr, dateToStr)    
    # Download the url or die
    try:
        print "Fetching url : " + urlHC
        jsonStr = url.read(urlHC)
        hcInfo = json.loads(jsonStr)
    except:
        exit(100)
    print "Data retrieved!"
    sitesfromDashboard = []
    for hcSummary in hcInfo['summaries']:
        sitesfromDashboard.append(hcSummary['name'])
    
    hcScoreSites = []
    noNa = 0
    print"Calculating HammerCloud scores"
    for site in sitesfromDashboard:
        for hcSummary in hcInfo['summaries']: 
            if hcSummary['name'] == site and site != "unknown":
                siteTerminated = hcSummary['terminated']
                siteSuccesful = hcSummary['app-succeeded']
                siteUnsuccesful = hcSummary['unsuccess']
                siteCancelled = hcSummary['cancelled']
                siteUnk = hcSummary['allunk']
                siteScore = None 
                if (siteTerminated - siteCancelled - siteUnk) > 0:
                    siteScore = (float(siteSuccesful - siteUnsuccesful) / float(siteTerminated - siteCancelled - siteUnk)) * 100.0
                    siteColor = "cNotOk"
                    if (sites.getTier(site) == 2 or sites.getTier(site) == 3) and siteScore > 79.9:
                        siteColor = "cOk"
                    if sites.getTier(site) == 1 and siteScore > 89.9:
                        siteColor = "cOk"
                    print site + " (" + str(siteSuccesful) + " - " + str(siteUnsuccesful) + ")/(" +str(siteTerminated)+" - "+str(siteCancelled)+" - "+str(siteUnk)+") =" + str(siteScore)
                elif siteTerminated > 0 or siteCancelled > 0 or siteUnk > 0 or siteUnsuccesful > 0 or siteSuccesful >0:
                    siteScore = "Error"
                    noNa += 1
                    siteColor = "cError"
                if siteScore is not None:
                	hcScoreSites.append(dashboard.entry(date = dateFrom.strftime("%Y-%m-%d %H:%M:%S"), name = site, value = siteScore, color = siteColor, url = getSuccessrateUrl (site, dateFromStr, dateToStr)))
    #print str(hcScoreSites)
    if len(hcScoreSites) >  noNa: 
        OutputFile = open(OUTPUT_FILE_NAME, 'w')
        for site in hcScoreSites:
            if site.name != "unknown":
                OutputFile.write(str(site) + '\n')
        print "\n--HC Score output written to %s" % OUTPUT_FILE_NAME
        OutputFile.close()
    else:
        print "There's no data, I quit!"

def getSuccessrateUrl (site, dateFromStr, dateToStr):
    return "http://dashb-cms-job.cern.ch/dashboard/templates/web-job2/#user=&refresh=0&table=Jobs&p=1&records=25&activemenu=0&usr=&site=%s&submissiontool=&application=&activity=hctest&status=&check=terminated&tier=&date1=%s&date2=%s&sortby=ce&scale=linear&bars=20&ce=&rb=&grid=&jobtype=&submissionui=&dataset=&submissiontype=&task=&subtoolver=&genactivity=&outputse=&appexitcode=&accesstype=" % (site, dateFromStr, dateToStr)

if __name__ == '__main__':
    main()
