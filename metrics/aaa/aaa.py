# conditions to mark a site as 'bad'
#- AAA-related ticket open for longer than two weeks
#- SAM access test < 50% for two weeks
#- HammerCloud[1] test success rete < 70% for two weeks

import sys, time, urllib
from lib import fileOps, url, dashboard, sites
try: import json
except ImportError: import simplejson as json
try: import xml.etree.ElementTree as ET
except ImportError: from elementtree import ElementTree as ET

if len(sys.argv) < 6:
    sys.stderr.write('not enough parameter!\n')
    sys.exit(1)

siteList     = sites.getSites()
ggusXMLFile  = fileOps.read(sys.argv[1])
ggus         = {}
samAccessURL = sys.argv[2]
samAccess    = {}
hcURL        = sys.argv[3]
hammerCloud  = {}
downTimesURL = sys.argv[4]
downTimes    = dashboard.parseJSONMetric(url.read(downTimesURL))
siteDownTimes = {}
federations  = json.loads(url.read(sys.argv[5]))
reportFile   = sys.argv[6]
reportURL    = sys.argv[7]
output       = sys.argv[8]
report       = {}

def check_federation_history(site_name):
    federationHistoryURL="http://dashb-ssb.cern.ch/dashboard/request.py/getplotdata?columnid=233&time=336&dateFrom=&dateTo=&site=T0_CH_CERN&sites=all&clouds=all&batch=1"
    federationHistory=dashboard.parseJSONMetric(url.read(federationHistoryURL))
    for entry in federationHistory.getSiteEntries(site_name).values():
        if entry.value == "prod" or entry.value == "trans":
            return entry.value
              
        

for site in siteList:
    samAccess[site] = 'n/a'
    hammerCloud[site] = 'n/a'
    ggus[site] = []
    siteDownTimes[site] = str(downTimes.getLatestEntry(site).color)
    print site + " " + siteDownTimes[site]

## parse ggus xml file
for ticket in ET.fromstring(ggusXMLFile).findall('ticket'):
    cmsSiteName  = ticket.find('cms_site').text
    ticketId     = ticket.find('request_id').text
    realSiteName = ticket.find('affected_site').text

    # if you don't have CMS site name AND have real site name,
    # try to find its CMS name and add it to the ggus array
    if not cmsSiteName and realSiteName:
        for site in siteList:
            if siteList[site]['name'] == realSiteName:
                cmsSiteName = site

    if not cmsSiteName: continue

    if not ggus.has_key(cmsSiteName):
        ggus[cmsSiteName] = []
    if not ticketId in ggus[cmsSiteName]: ggus[cmsSiteName].append(ticketId)

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

production   = dashboard.metric()
transitional = dashboard.metric()

for site in siteList:
    badSiteFlag = False
    errMsg      = 'bad'
    siteDownTimeFlag = False
    downTimeColors = ['grey', 'yellow', 'saddlebrown']

    # conditions to mark a site as bad
    if samAccess[site] < 50.0 or samAccess[site] == 'n/a':
        badSiteFlag = badSiteFlag | True
        if samAccess[site] == 'n/a': val = samAccess[site]
        else: val = round(samAccess[site], 2)
        errMsg = errMsg + '_SAM(%s)' % val
    if (hammerCloud[site] < 70.0 or hammerCloud[site] == 'n/a') and sites.getTier(site) != 3:
        badSiteFlag = badSiteFlag | True
        if hammerCloud[site] == 'n/a': val = hammerCloud[site]
        else: val = round(hammerCloud[site], 2)
        errMsg = errMsg + '_HC(%s)' % val
    if site in ggus.keys() and len(ggus[site]):
        badSiteFlag = badSiteFlag | True
        errMsg = errMsg + '_GGUS(%s)' % str(ggus[site])
    if siteDownTimes[site] in downTimeColors:
        siteDownTimeFlag = True
    if badSiteFlag:
        entry = dashboard.entry(None, site, errMsg, dashboard.red, reportURL % site)
        if siteDownTimeFlag:
            entry = dashboard.entry(None, site, 'site is on downtime', siteDownTimes[site], reportURL % site)
    else:
        entry = dashboard.entry(None, site, 'on', dashboard.green, reportURL % site)

    if site in federations["prod"]: production.append(entry)
    elif site in federations["trans"]: transitional.append(entry)
    else:
        historic_federation = check_federation_history(site)
        if historic_federation == "trans" and siteDownTimeFlag == False:
            transitional.append(dashboard.entry(None, site, 'site lost subscription to transitional federation', 'blue', reportURL % site))
        elif historic_federation == "trans" and siteDownTimeFlag == True:
            transitional.append(dashboard.entry(None, site, 'site is on downtime', siteDownTimes[site], reportURL % site))
        elif historic_federation == "prod" and siteDownTimeFlag == False:
            production.append(dashboard.entry(None, site, 'site lost subscription to prod federation', 'blue', reportURL % site))
        elif historic_federation == "prod" and siteDownTimeFlag == True:
            production.append(dashboard.entry(None, site, 'site is on downtime', siteDownTimes[site], reportURL % site))
        

report['lastUpdate'] = time.time()
report['data']       = {}
for site in siteList:
    report['data'][site] = {}
    if samAccess.has_key(site):
        report['data'][site]['sam']  = samAccess[site]
    if hammerCloud.has_key(site):
        report['data'][site]['hc']   = hammerCloud[site]
    if ggus.has_key(site):
        report['data'][site]['ggus'] = ggus[site]

fileOps.write(reportFile, json.dumps(report))
fileOps.write('%s/aaaProd.txt' % output, str(production))
fileOps.write('%s/aaaTrans.txt' % output, str(transitional))
