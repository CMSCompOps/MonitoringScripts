'''
Created on Sep 28, 2015

@author: gastonlp
'''
import json
import time
from datetime import datetime
import pytz
from calendar import timegm
import urllib
import sys
import re
from optparse import OptionParser
import httplib
import os
import subprocess

def  main():
    parser = OptionParser(usage="usage: %prog [options] filename",
                          version="%prog 1.0")
    parser.add_option("-c", "--column",
                      dest="column",
                      help="The column from which you wish to delete data.")
    parser.add_option("-a", "--allSites",
                      action='store_true',
                      dest= "allsites",
                      help="Delete data for all sites")
    parser.add_option("-d", "--delete",
                      action='store_true',
                      dest= "delete",
                      help="Delete data for all sites")
    parser.add_option("-s", "--site",
                      help='site from which to delete data',
                      dest="site")
    parser.add_option("-f", "--from",
                      help='Date From which to delete data in format 2016-12-31',
                      dest="dateFrom")
    parser.add_option("-t", "--to",
                      help='Date up to which (including) to delete data in format 2016-12-31',
                      dest="dateTo")
    (options, args) = parser.parse_args()
    
    pattern = re.compile("\d\d\d\d-\d\d-\d\d")
    if options.dateFrom is not None and options.dateTo is not None: 
        if not pattern.match(options.dateFrom) or not pattern.match(options.dateTo):
            print "Date in incorrect format format should be 2016-12-31."
            sys.exit(-1)
    else: 
        print "Please add dates"
        sys.exit(-1)
    if options.column is not None:
        try :
            int(options.column)
        except:
            print "Column must be integer!"
            sys.exit(-1)
    print "Hello! I will help you delete data!"
    allsites = options.allsites
    column = options.column
    site = options.site
    dateFrom = options.dateFrom
    dateTo = options.dateTo
    #column = 211
    #dateFrom = "2016-02-19"
    #dateTo = "2016-02-20"
    #allsites = True
    #site = "T2_CH_CERN"
    
    #siteName = sys.argv[2]
    outfile = open('datatoDelete.txt', 'w')
    urlDashboard = "https://dashb-ssb.cern.ch/dashboard/request.py/modifymetriccelldata"
    if allsites == True :
        dataUrl = 'http://dashb-ssb.cern.ch/dashboard/request.py/getplotdata?columnid=%s&time=custom&dateFrom=%s&dateTo=%s&site=%s&sites=all&clouds=all&batch=1' % (column,dateFrom, dateTo, "")
    else :
        dataUrl = 'http://dashb-ssb.cern.ch/dashboard/request.py/getplotdata?columnid=%s&time=custom&dateFrom=%s&dateTo=%s&site=%s&sites=%s&clouds=all&batch=1' % (column,dateFrom, dateTo, site, "one")
    response = urllib.urlopen(dataUrl)
    data = json.loads(response.read())
    
    csvdata = data['csvdata']
    if csvdata is not None:
        if len(csvdata) > 0: 
            indexoutput =0 
            if allsites:
                print "I found " + str(len(csvdata)) + " lines on column " +str(column) + " for all sites " + " from " + dateFrom + " to " + dateTo
            else:
                print "I found " + str(len(csvdata)) + " lines on column " +str(column) + " for site " + str(site) + " from "+ dateFrom + " to " + dateTo
            print "Entry 0 is : \n site: %s \n Time: %s \n EndTime: %s \n Colour: %s \n Value: %s " %(str(csvdata[0]['VOName']),str(csvdata[0]['Time']),str(csvdata[0]['EndTime']),str(csvdata[0]['COLOR']), str(csvdata[0]['Status']))
            usr_choice = raw_input("Press n to see next entry, d proceed with deletion : \n")
            while usr_choice == "n" : 
                            indexoutput +=1
                            indexoutput = max(indexoutput, len(csvdata))
                            print "Entry " + str(indexoutput) +" is : \n site: %s \n Time: %s \n EndTime: %s \n Colour: %s \n Value: %s " %(str(csvdata[indexoutput]['VOName']),str(csvdata[indexoutput]['Time']),str(csvdata[indexoutput]['EndTime']),str(csvdata[indexoutput]['COLOR']), str(csvdata[indexoutput]['Status']))
                            usr_choice = "die"
                            usr_choice = raw_input("Press n to see next entry, d to delete all :\n")
            if usr_choice == "d":
                for line in csvdata:
                    timefrom = line['Time'].split('T')[1]
                    datefrom = line['Time'].split('T')[0]
                    timeto = line['EndTime'].split('T')[1]
                    dateto = line['EndTime'].split('T')[0]
                    columnid = column
                    sitename = line['VOName']
                    variableRara = int(time.time())
                    timestamp = timegm(((datetime.strptime(line['Time'], '%Y-%m-%dT%H:%M:%S')).replace(tzinfo=pytz.UTC)).timetuple())
                    colorid = line['COLOR']
                    status = line['Status']
                    url = line['URL']
                    value = line['Value']
                    remove = "true"
                    modifyMetricHistoryData = "2"
                    modifyall = "false"
                    insert = "false"
                    params = {'_': variableRara, "columnid": columnid, "sitename" : sitename, 'timestamp' : timestamp, 'timefrom': timefrom, 'timeto': timeto, "datefrom":datefrom, "dateto" : dateto, "colorid": colorid, "status":status, "url" : url, "value" : value, "remove" : remove, "insert" : insert, "modifyMetricHistoryData" : modifyMetricHistoryData, "modifyall" : modifyall }
                    outline = urlDashboard + "?" + urllib.urlencode(params)
                    outfile.write("'" + outline + "'\n")
                print """Please create an unencrypted key with 'openssl rsa -in  ~/.globus/userkey.pem -out  ~/.globus/unencr_key.pem' and execute :
cat datatoDelete.txt | xargs -n 1 curl -k -H "Accept : application/json" -X GET --cert ~/.globus/usercert.pem --key ~/.globus/unencr_key.pem"""
                outfile.close()    
            else:
                print "Sorry, didn't catch that, I quit!"
        else:
            print "I found  no info for column " + str(column)  + " from " + dateFrom + " to " + dateTo
    else : 
        print "Communications break down"
        
def getData(url):
    proc = subprocess.Popen(["curl", '-k -H -X GET --cert ~/.globus/usercert.pem --key ~/.globus/unencr_key.pem', url], stdout=subprocess.PIPE)
    (out, err) = proc.communicate()
    return out

if __name__ == '__main__':
    main()
