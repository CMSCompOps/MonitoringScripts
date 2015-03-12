# cloned from: https://git.cern.ch/web/sitecomm.git/blob/HEAD:/SSBScripts/site_avail_sum.pl

import sys, time, urllib
from lib import fileOps, url, dashboard, sites
try: import json
except ImportError: import simplejson as json

if len(sys.argv) <2:
    print 'not enough parameters'
    sys.exit(1)

# get cms site list
siteList = sites.getSites()

# prepare result array. note that for SAM tests
# we don't filter sites by tier number because some
# T3s have SAM tests.
results  = {}
for site in siteList:
    results[site] = 'n/a'

now      = time.time()
start    = time.strftime("%Y-%m-%dT00:00:00Z", time.localtime(now - 24*60*60))
# remember, in urllib.quote, '/' is safe by default
# this is why we used quote_plus.
start    = urllib.quote(start)
end      = time.strftime("%Y-%m-%dT23:00:00Z", time.localtime(now - 24*60*60))
end      = urllib.quote(end)

# start, end, site
samURL   = 'http://wlcg-sam-cms.cern.ch/dashboard/request.py/getstatsresultsmin?profile_name=CMS_CRITICAL_FULL&plot_type=quality&start_time=%s&end_time=%s&granularity=single&group_name=%s&view=siteavl'
for site in results:
    source = samURL % (start, end, site)
    data   = json.loads(url.read(source))
    if not (data.has_key('data') and len(data['data']) and data['data'][0].has_key('data')): continue
    data   = data['data'][0]['data'][0]
    if not data['OK'] + data['CRIT'] + data['SCHED'] > 0: continue
    result = data['OK'] / (data['OK'] + data['CRIT'] + data['SCHED']) * 100.0
    results[site] = round(result, 1)

metric   = []
# the web page wanst to have different time stamp 
# formats... and remember, in urllib.quote, '/' is
# safe by default this is why we used quote_plus.
start    = urllib.quote_plus(time.strftime("%Y/%m/%d", time.localtime(now - 24*60*60)))
end      = urllib.quote_plus(time.strftime("%Y/%m/%d", time.localtime(now)))
dashboardURL = 'http://wlcg-sam-cms.cern.ch/templates/ember/#/historicalsmry/heatMap?end_time=%s%%2023%%3A00&group=AllGroups&profile=CMS_CRITICAL_FULL&site=%s&site_metrics=undefined&start_time=%s%%2000%%3A00&type=Availability%%20Ranking%%20Plot'
for site in results:
    name  = site
    value = results[site]
    color = dashboard.red
    url   = dashboardURL % (end, site, start)
    # SAM threshold for T1s is 90
    threshold = 90.0
    # if it is T2 site
    if sites.getTier(name) == 2:
        threshold = 80.0

    if value > threshold:
        color = dashboard.green
    elif sites.getTier(site) == 3:
        # if the site is T3, no need to worry.
        color = dashboard.green

    metric.append(dashboard.entry(None, name, value, color, url))

fileOps.write(sys.argv[1], "\n".join(str(row) for row in metric))
