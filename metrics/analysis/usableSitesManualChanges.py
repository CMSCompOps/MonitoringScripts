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
metric        = dashboard.parseJSONMetric(url.read(metricURL))
updatedMetric = dashboard.metric()

# merege sites from the vo-feed and manual control meteric.
siteList     = sites.getSites()
for site in metric.getSites():
    if not site in siteList:
        siteList[site] = {}

for i in siteList:
    # if the site is not in the list add it (this is the
    # case that will be happaned when they create new site
    # in the site db)
    if not metric.hasSite(i):
        updatedMetric.append(dashboard.entry(None, i, 'ready', dashboard.green, metricURL))
    else:
        latestEntry = metric.getLatestEntry(i)
        updatedMetric.append(dashboard.entry(None, i, latestEntry.value, latestEntry.color, metricURL))
        print latestEntry.value + " " + i

#######################
blist = ['T2_RU_RRC_KI','T3_BY_NCPHEP','T3_CH_PSI','T3_CN_PKU','T3_ES_Oviedo','T3_IN_PUHEP','T3_IR_IPM','T3_KR_UOS','T3_UK_London_RHUL','T3_UK_London_UCL','T3_UK_ScotGrid_ECDF','T3_US_FNALLPC','T3_US_FNALXEN','T3_US_FSU','T3_US_JHU','T3_US_Kansas','T3_US_MIT','T3_US_NU','T3_US_Princeton','T3_US_Princeton_ICSE','T3_US_Rice', 'T3_BG_UNI_SOFIA']
for bsite in blist:
    updatedMetric.append(dashboard.entry(None, bsite, 'blocked', dashboard.red, metricURL))
#######################

fileOps.write(output, str(updatedMetric))
