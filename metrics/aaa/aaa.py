# conditions to mark a site as 'bad'
#- AAA-related ticket open for longer than two weeks
#- SAM access test < 50% for two weeks
#- HammerCloud[1] test success rete < 80% for two weeks

import sys, time, urllib
from lib import fileOps, url, dashboard, sites
try: import json
except ImportError: import simplejson as json
try: import xml.etree.ElementTree as ET
except ImportError: from elementtree import ElementTree as ET

if len(sys.argv) < 5:
    sys.stderr.write('not enough parameter!\n')
    sys.exit(1)

siteList     = sites.getSites()
ggusXMLFile  = fileOps.read(sys.argv[1])
ggus         = []
samAccessURL = sys.argv[2]
samAccess    = {}
hcURL        = sys.argv[3]
hammerCloud  = {}
output       = sys.argv[4]

for site in siteList:
    samAccess[site] = 'n/a'
    hammerCloud[site] = 'n/a'

## parse ggus xml file
for ticket in ET.fromstring(ggusXMLFile).findall('ticket'):
    cmsSiteName  = ticket.find('cms_site').text
    realSiteName = ticket.find('affected_site').text

    # if you don't have CMS site name AND have real site name,
    # try to find its CMS name and add it to the ggus array
    if not cmsSiteName and realSiteName:
        for site in siteList:
            if siteList[site]['name'] == realSiteName:
                cmsSiteName = site

    if not cmsSiteName: continue

    ggus.append(cmsSiteName)

## for SAM::access test results
for site in siteList:
    numOfSample = 0.0
    numOfOK     = 0.0
    for host in siteList[site]['hosts']:
        # get test results for the host
        data = json.loads(url.read(samAccessURL.format(host)))
        data = data['data']
        # if there is no test result, pass it
        if len(data) == 0: continue
        # get the test results (please see the json data structure)
        data = data[0][1]
        # add number of sample for the host
        numOfSample = numOfSample + len(data)
        for sample in data:
            if sample[1] == 'OK': numOfOK = numOfOK + 1.0
    if numOfSample == 0:
        # there is no enough sample to say something about the site
        samAccess[site] = 'n/a'
    else:
        # get the ratio of OKs to all samples
        samAccess[site] = 100.0 * (numOfOK / numOfSample)

## for hammercloud:: test results
# generate time stamp
now     = time.time()
# 2 weeks time range (notice the calculation over the unix time)
start   = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(now - 14*24*60*60))
start   = urllib.quote(start)
end     = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(now))
end     = urllib.quote(end)
data    = url.read(hcURL.format(start, end), header = {'Accept' : 'text/xml'})
data    = ET.fromstring(data)
entries = data.find('summaries').findall('item')
for i in entries:
    succ   = float(i.find('app-succeeded').text)
    unsucc = float(i.find('unsuccess').text)
    term   = float(i.find('terminated').text)
    unkn   = float(i.find('allunk').text)
    canc   = float(i.find('cancelled').text)
    name   = i.find('name').text
    ## Andrea's approach
    # check if enough number of job existing to calculate the hc value
    if term - canc - unkn < 10: continue
    # hammercloud value calculation
    result = (succ - unsucc) / (term - canc - unkn) * 100.;
    # check extreme cases
    if (result < 0.0 or result > 100.0) or (term - canc - unkn < 0.0):
        sys.stderr.write("something went really wrong! extreme case:\n")
        sys.stderr.write("site:%s, app-succeeded:%s, unsuccess:%s, terminated:%s, allunk:%s, cancelled:%s" % (name, succ, unsucc, term, unkn, canc))
        continue
    if name in hammerCloud: hammerCloud[name] = result

metric = dashboard.metric()

for site in siteList:
    badSiteFlag = False

    # conditions to mark a site as bad
    if samAccess[site] < 50.0:
        badSiteFlag = True
    elif hammerCloud[site] < 80.0:
        badSiteFlag = True
    elif site in ggus:
        badSiteFlag = True

    if badSiteFlag:
        metric.append(dashboard.entry(None, site, 'bad', dashboard.red, '#'))
    else:
        metric.append(dashboard.entry(None, site, 'on', dashboard.green, '#'))

fileOps.write(output, str(metric))
