import sys
from lib import sites, dashboard, url, fileOps

# this script provides data for the 'usable sites - manual changes' metric,
# which is created to control the 'usable sites' metric by hand, and creates
# a closed loop for the metric. when someone changes a value in the 
# 'usable sites - manual changes' metric by using dashboard web interface,
# the script reflects this change to the input text file of the metric.

if len(sys.argv) < 3:
    print 'not enough parameter!'
    sys.exit(1)

# output path
output        = sys.argv[2]

# get the source metric url
metricURL     = sys.argv[1]
# get the entries of the metric
updatedMetric = dashboard.parseMetric(url.read(metricURL))

# get site list and loop it
for i in sites.getSites():
    # if the site is not in the list add it (this is the
    # case that will be happaned when they create new site
    # in the site db)
    if not updatedMetric.hasSite(i):
        updatedMetric.append(dashboard.entry(None, i, 'on', dashboard.green, metricURL))

for i in updatedMetric.entries:
    i.dateTimeNow()

fileOps.write(output, str(updatedMetric))
