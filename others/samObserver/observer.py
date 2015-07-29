import sys, time, urllib
try: import json
except ImportError: import simplejson as json
from lib import sites, url, fileOps
if len(sys.argv) < 4:
    sys.stderr.write("not enough parameter!\n")
    sys.exit(1)

out    = sys.argv[1]
samURL = sys.argv[2]
date   = sys.argv[3]
siteList = sites.getSites()

# prepare result array. note that for SAM tests
# we don't filter sites by tier number because some
# T3s have SAM tests.
results  = {}
for site in siteList:
    results[site] = 'n/a'

now      = time.time()
start    = date.format(time.strftime("T00:00:00Z", time.localtime(now - 24*60*60)))
# remember, in urllib.quote, '/' is safe by default
# this is why we used quote_plus.
start    = urllib.quote(start)
end      = date.format(time.strftime("T23:00:00Z", time.localtime(now - 24*60*60)))
end      = urllib.quote(end)

print 'SAM test time range:', start, end

# start, end, site
for site in results:
    source = samURL.format(start, end, site)
    data   = json.loads(url.read(source))
    if not (data.has_key('data') and len(data['data']) and data['data'][0].has_key('data')): continue
    data   = data['data'][0]['data'][0]
    if not data['OK'] + data['CRIT'] + data['SCHED'] > 0: continue
    result = data['OK'] / (data['OK'] + data['CRIT'] + data['SCHED']) * 100.0
    results[site] = round(result, 3)

fileOps.write("{0}/{1}.json".format(out, int(time.time())), json.dumps(results, indent = 2))
