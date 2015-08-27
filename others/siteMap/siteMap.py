import sys, time
from lib import dashboard, url, fileOps, sites
try: import json
except ImportError: import simplejson as json

if len(sys.argv) < 4:
    sys.stderr.write('not enough parameter!\n')
    sys.exit(1)

siteList  = sites.getSites()
config    = json.loads(fileOps.read(sys.argv[1]))
fieldList = config.keys()
fieldList.sort()
data      = {}
# add field names
data['fields'] = fieldList

# load all fields from dashboard
fields    = {}
for field in fieldList:
    fields[field] = dashboard.parseMetric(url.read(config[field]))
    print field, 'done...'

for site in siteList:
    data[site] = []
    for field in fieldList:
        if not fields[field].hasSite(site):
            data[site].append('black')
            continue
        data[site].append(fields[field].getSiteEntry(site).color)

template  = fileOps.read(sys.argv[2])
template  = template.replace('@DATE@', time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(time.time())))
template  = template.replace('@DATA@', json.dumps(data));

fileOps.write(sys.argv[3], template)
