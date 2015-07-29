# this script generates IN/OUT waiting room statistics by sites

from lib import url, dashboard
try: import json
except ImportError: import simplejson as json
import time, sys

if len(sys.argv) < 2:
    sys.stderr.write('not enough parameter!\n')
    sys.exit(1)

data   = url.read(sys.argv[1])
wr     = dashboard.parseJSONMetric(data)
wrStat = {}

for site in wr.getSites():
    # initialize country statistics
    if not wrStat.has_key(site):
        wrStat[site] = {dashboard.green : 0, dashboard.red : 0}

    # to remember the parsed json metric data structure, please see dashboard.py
    entries = wr.getSiteEntries(site)
    for endTime in entries:
        entry = entries[endTime]
        diff  = endTime - entry.date
        if entry.color == dashboard.green or entry.color == dashboard.yellow:
            wrStat[site][dashboard.green] += diff
        elif entry.color == dashboard.red:
            wrStat[site][dashboard.red] += diff

sites = wrStat.keys()
sites.sort()
print "SITE\tOUT\tIN"
for site in sites:
    green = wrStat[site][dashboard.green]
    red   = wrStat[site][dashboard.red]
    print "%s\t%s\t%s" % (site, round(green / float(green + red), 2), round(red / float(green + red), 2))
