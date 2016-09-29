import sys
try: import json
except ImportError: import simplejson as json
from lib import fileOps, url, dashboard, sites

if len(sys.argv) < 3:
    sys.stderr.write('not enough parameter!\n')
    sys.exit(1)

federationSource = sys.argv[1]
metricOutput     = sys.argv[2]

federations = json.loads(url.read(federationSource))

federationMetric = dashboard.metric()
for fedName in federations:
    for site in federations[fedName]:
        if fedName == 'prod':
            color = dashboard.green
        elif fedName == 'trans':
            color = dashboard.cyan
        elif fedName == 'nowhere':
            color = dashboard.gray
        else:
            # basically, this is impossible state considering possible
            # federation names but I wanted to consider this in case of
            # a change. --and this change must be reflected to the metric.
            color = dashboard.white
        entry = dashboard.entry(None, site, fedName, color, federationSource)
        federationMetric.append(entry)

fileOps.write(metricOutput, str(federationMetric))
