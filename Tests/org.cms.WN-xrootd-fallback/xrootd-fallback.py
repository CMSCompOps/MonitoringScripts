#aaltunda - ali.mehmet.altundag@cern.ch
import urllib2, time, json, datetime
import xml.etree.ElementTree as ET

## file access functions
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

## function to get content from web
def URLRead(url, printFlag = True):
    URLObj = urllib2.urlopen(url)
    data   = URLObj.read()
    if printFlag: print 'Read:', url
    return data

## GetSites returns all sites with their elements
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
            serviceName = service.attrib['hostname']
            ret[siteName].append(serviceName)
    return ret

# url for xrootd-fallback.  parameters: hostname, start, end
url       = 'http://dashb-cms-sum.cern.ch/dashboard/request.py/getTestResults?profile_name=CMS_CRITICAL_FULL&hostname=%s&flavours=CREAM-CE,SRMv2&metrics=org.cms.WN-xrootd-fallback&time_range=individual&start_time=%s&end_time=%s'
# read output template
template  = Read('template.html')
# get all sites
sites     = GetSites()

# define the time range (now, now - 1 day)
now       = time.time()
endTime   = time.strftime("%Y-%m-%dZT%H:%M:00Z", time.localtime(int(now)))
startTime = time.strftime("%Y-%m-%dZT%H:%M:00Z", time.localtime(int(now-24*60*60)))

# html table
hTable    = ''
siteNames = sites.keys()
siteNames.sort()
for site in siteNames:
    print site
    for hostName in sites[site]:
        hRow = '<tr><td> <b>%s</b> - %s </td>' % (site, hostName)
        print '\t', hostName
        dest = url % (hostName, startTime, endTime)
        data = json.loads(URLRead(dest, False))
        data = data['data']
        if not len(data):
            hRow = hRow + '<td>No metric</td></tr>'
            hTable = hTable + hRow + "\n"
            continue
        hRow = hRow + '<td>'
        for entry in data[0][1]:
            date = datetime.datetime.fromtimestamp(entry[0]).strftime('%Y-%m-%d %H:%M:%S')
            stat = entry[1]
            hCellClass = 'unknown'
            if 'OK' in stat: hCellClass = 'success'
            elif 'WARNING' in stat: hCellClass = 'warning'
            hRow = hRow + '<div class="box %s"> <div><b>%s</b> - %s</div> </div>' % (hCellClass, date, stat)
        hRow = hRow + '<td></tr>\n'
        hTable = hTable + hRow
template = template.replace('%%DATE%%', time.strftime("%Y-%m-%d %H:%M"))
template = template.replace('%%TABLE_CONTENT%%', hTable)
Write('out.html', template)
