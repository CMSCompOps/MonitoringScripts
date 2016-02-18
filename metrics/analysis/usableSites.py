# please have a look at the site support team metric script
# development documentation:
# https://twiki.cern.ch/twiki/bin/view/CMSPublic/SiteSupportMonitoringScripts

import sys, time
from lib import sites, dashboard, url, fileOps
try: import json
except ImportError: import simplejson as json

if len(sys.argv) < 7:
    print 'not enough parameter!'
    sys.exit(1)

# manually controlled usable sites list
usableSitesMC = dashboard.parseMetric(url.read(sys.argv[1]))
# morgue list
morgue        = dashboard.parseMetric(url.read(sys.argv[2]))
# prepare hammercloud metric url for last 3 days!
hcURL         = sys.argv[3] % (time.strftime("%Y-%m-%d", time.localtime(time.time()-3*24*60*60)),
                               time.strftime("%Y-%m-%d", time.localtime(time.time())))
hammerCloud   = dashboard.parseJSONMetric(url.read(hcURL))
# get the url stamp for the dashboard input file
urlStamp      = sys.argv[4]
# text output file location
txtOutput     = sys.argv[5]
# json output file location
jsonOutput    = sys.argv[6]

# create new metric object
metricHeader = {'twiki' : 'https://twiki.cern.ch/twiki/bin/view/CMSPublic/UsableSitesForAnalysis'}
metric = dashboard.metric(header = metricHeader)

def hasBadHistory(siteName):
    # if the site is not in the hc metric, return False

    # (you don't have any idea about the site, you cannot
    # talk about it!)
    if not siteName in hammerCloud.getSites():
        return False

    # if site has at least one green slot in the given time range
    # (please check the hammerCloud link given as a parameter to see
    # the time range), return False
    slots = hammerCloud.getSiteEntries(siteName).values()
    for slot in slots:
        if slot.color == dashboard.green: return False
    return True

# merge sites that are not in the vo-feed (sites.getSites)
# --look at the loop, we are getting some sites from the manual changes 
# metric. reason: some sites are not listed in the sites.getSites
siteList = sites.getSites()
for site in usableSitesMC.getSites():
    if not site in siteList:
        siteList[site] = {}

for i in siteList:
    badSiteFlag = False
    ## detect bad sites!
    # site has bad hammercloud history
    if sites.getTier(i) == 2 and hasBadHistory(i):
        print i + " hasBadHistory"
        badSiteFlag = True
    # site is in the morgue
    elif morgue.hasSite(i) and morgue.getSiteEntry(i).value == 'Morgue':
        print i + " is in the Morgue"
        badSiteFlag = True
    # site has been blocked
    elif usableSitesMC.hasSite(i) and usableSitesMC.getSiteEntry(i).color == dashboard.red:
        print i + " usableSitesMC.getSiteEntry color is red"
        badSiteFlag = True

    if badSiteFlag:
        metric.append(dashboard.entry(None, i, 'not_usable', dashboard.red, urlStamp))
    else:
        metric.append(dashboard.entry(None, i, 'usable', dashboard.green, urlStamp))

fileOps.write(txtOutput, str(metric))
fileOps.write(jsonOutput, json.dumps(metric.__list__(), indent=2))
