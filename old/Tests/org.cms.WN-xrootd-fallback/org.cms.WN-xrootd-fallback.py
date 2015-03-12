#aaltunda - ali.mehmet.altundag@cern.ch

import urllib2, time, json, datetime
import xml.etree.ElementTree as ET

# file op function
def Read(fileName, printFlag = True, binary = False):
    if binary: fh = open(fileName, 'rb')
    else: fh = open(fileName)
    data = fh.read()
    fh.close()
    if printFlag: print 'Read:', fileName
    return data

def Write(fileName, data, printFlag = True, binary = False):
    if binary: fh = open(fileName, 'wb')
    else: fh = open(fileName, 'w')
    fh.write(data)
    fh.close()
    if printFlag: print 'Write:', fileName

# returns content from the web
def URLRead(url, printFlag = True):
    URLObj = urllib2.urlopen(url)
    data   = URLObj.read()
    if printFlag: print 'Read:', url
    return data

# returns all sites
def GetSites():
    XML   = URLRead('http://dashb-cms-vo-feed.cern.ch/dashboard/request.py/cmssitemapbdii')
    XML   = ET.fromstring(XML)
    sites = XML.findall('atp_site')
    ret   = {}
    for site in sites:
        groups   = site.findall('group')
        siteName = groups[1].attrib['name']
        services = site.findall('service')
        ret[siteName] = []
        for service in services:
            # ignore all SRMs
            if 'SRMv2' in service.attrib['flavour']: continue
            serviceName = service.attrib['hostname']
            ret[siteName].append(serviceName)
    return ret

# dashboard json interface
url       = 'http://dashb-cms-sum.cern.ch/dashboard/request.py/getTestResults?profile_name=CMS_CRITICAL_FULL&metrics=org.cms.WN-xrootd-fallback'
url       = url + '&hostname=%s&flavours=CREAM-CE,OSG-CE,ARC-CE,SRMv2&time_range=individual&start_time=%s&end_time=%s'
template  = Read('template.html')
sites     = GetSites()

# current unix time stamp
now       = time.time()
# time range
slot      = 36*60*60
endTime   = time.strftime("%Y-%m-%dZT%H:%M:00Z", time.localtime(int(now)))
startTime = time.strftime("%Y-%m-%dZT%H:%M:00Z", time.localtime(int(now-slot)))
print startTime, endTime

hTable    = ''
siteNames = sites.keys()
siteNames.sort()
for site in siteNames:
    print site
    for hostName in sites[site]:
        hRow = '<tr><td> <b>%s</b> - %s </td>' % (site, hostName)
        print '\t', hostName
        # prepare the URL to get xrood-fallback metric for the site
        dest = url % (hostName, startTime, endTime)
        # get the JSON and parse it
        data = json.loads(URLRead(dest, False))
        data = data['data']
        # if data doesn't exist for the site, put the 'no metric' comment and skip it
        if not len(data):
            hRow = hRow + '<td>No metric</td></tr>'
            hTable = hTable + hRow + "\n"
            continue
        hRow = hRow + '<td>'
        # please have a look at dashboard JSON interface output structure to understand the indices
        for entry in data[0][1]:
            # in the JSON we have unix time stamp for the test result time. convert it into
            # human readable time format
            date = datetime.datetime.fromtimestamp(entry[0]).strftime('%Y-%m-%d %H:%M:%S')
            stat = entry[1]
            hCellClass = 'unknown'
            if 'OK' in stat: hCellClass = 'success'
            elif 'WARNING' in stat: hCellClass = 'warning'
            elif 'MISSING' in stat: hCellClass = 'error'
            elif 'CRITICAL' in stat: hCellClass = 'error'
            hRow = hRow + '<div class="box %s"> <div><b>%s</b> - %s</div> </div>' % (hCellClass, date, stat)
        hRow = hRow + '<td></tr>\n'
        hTable = hTable + hRow

template = template.replace('%%DATE%%', time.strftime("%Y-%m-%d %H:%M"))
template = template.replace('%%TIME_RANGE%%', '%s, %s (%s hours)' % (startTime, endTime, slot/(60*60)))
template = template.replace('%%TABLE_CONTENT%%', hTable)
Write('org.cms.WN-xrootd-fallback.html', template)
