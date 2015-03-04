import sys, time, urllib
from lib import fileOps, sites, url, dashboard

try: import xml.etree.ElementTree as ET
except ImportError: from elementtree import ElementTree as ET

if len(sys.argv) < 3:
    print 'not enough parameters'
    sys.exit(1)

siteList = sites.getSites()
# HC test entries will be stored in the results variable.
# by site name and site names will be only T1s and T2s.
results  = {}
for site in siteList:
    # please keep in mind that you may want to run this script
    # also for T3s in future, in that case you will need to
    # edit this filter. you will also need to update thresholds
    # for tiers.
    if (sites.parseSiteName(sites.t1Pattern, site) or sites.parseSiteName(sites.t2Pattern, site)):
        results[site] = 'n/a'

# prepare dashboard link parameters
now      = time.time()
# one day time range
start    = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(now - 24*60*60))
start    = urllib.quote(start)
end      = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(now))
end      = urllib.quote(end)
activity = sys.argv[1]
# parameter order (pelase notice '%s' stamps in the url):
# activity, end date, start date
hcURL    =  "http://dashb-cms-job.cern.ch/dashboard/request.py/jobsummary-plot-or-table?user=&site=&ce=&submissiontool=&datset=&application=&rb=&activity=%s&grid=&date2=%s&date1=%s&sortby=site&nbars=&scale=linear&jobtype=&tier=&check=terminated"
hcURL    = hcURL % (activity, end, start)
# get HC results in xml
data     = url.read(hcURL, header = {'Accept' : 'text/xml'})
data     = ET.fromstring(data)
entries  = data.find('summaries').findall('item')

# parse cms job xml tree
for i in entries:
    succ   = float(i.find('app-succeeded').text)
    unsucc = float(i.find('unsuccess').text)
    term   = float(i.find('terminated').text)
    unkn   = float(i.find('allunk').text)
    canc   = float(i.find('cancelled').text)
    name   = i.find('name').text
    # check if enough number of job existing to calculate the hc rate
    if term - canc - unkn < 10: continue
    # core hammercloud calculation
    result = (succ - unsucc) / (term - canc - unkn) * 100.;
    # check extreme cases
    if (result < 0.0 or result > 100.0) or (term - canc - unkn < 0.0):
        print "something went really wrong! extreme case:"
        print "site:%s, app-succeeded:%s, unsuccess:%s, terminated:%s, allunk:%s, cancelled:%s" % (name, succ, unsucc, term, unkn, canc)
        continue
    result = round(result, 1)
    if name in results: results[name] = result

# prepare metric text file
metric   = []
# (site, act, start, end)
dashboardURL = 'http://dashb-cms-job.cern.ch/dashboard/templates/web-job2/#user=&refresh=0&table=Jobs&p=1&records=25&activemenu=0&usr=&site=%s&submissiontool=&application=&activity=%s&status=&check=terminated&tier=&date1=%s&date2=%s&sortby=ce&scale=linear&bars=20&ce=&rb=&grid=&jobtype=&submissionui=&dataset=&submissiontype=&task=&subtoolver=&genactivity=&outputse=&appexitcode=&accesstype='
for i in results:
    name      = i
    value     = results[i]
    color     = dashboard.red
    url       = dashboardURL % (name, sys.argv[1], start, end)

    # default value for the threshold is 90% (we assume that,
    # we have a T1 site). 
    threshold = 90.0
    if sites.getTier(name) == 2:
       # threshold for T2s is 80%
       threshold = 80.0

    if value == 'n/a': color = dashboard.white
    elif value > threshold: color = dashboard.green

    metric.append(dashboard.entry(None, name, value, color, url))

fileOps.write(sys.argv[2], "\n".join(str(row) for row in metric))
