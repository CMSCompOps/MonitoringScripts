from lib import dashboard, sites, url
from datetime import datetime, timedelta
import os, sys
import dateutil.parser
import json
from optparse import OptionParser

metricFileName = sys.argv[1]
overrideFileName = sys.argv[2]
outputFileName = sys.argv[3]

metricFile = open(metricFileName, 'r')
overrideFile = open(overrideFileName, 'r')

try:
    metricMetric = dashboard.parseMetric(metricFile.read())
    overrideMetric = dashboard.parseMetric(overrideFile.read())
except:
    print "Cannot read either metric or override"
    exit(1)

sites = set(metricMetric.getSites()).union(set(overrideMetric.getSites()))

outputEntries = []

#dateNow = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
for site in sites:
    entryFromMetric = metricMetric.getSiteEntry(site)
    entryFromOverride = overrideMetric.getSiteEntry(site)
    if entryFromMetric is not None and entryFromOverride is not None:
        newEntry = entryFromMetric
        newEntry.value = entryFromOverride.value
        newEntry.color = entryFromOverride.color
        newEntry.nvalue = entryFromOverride.nvalue
        newEntry.date = None
    elif entryFromMetric is not None:
        newEntry = entryFromMetric
        newEntry.date = None
    elif entryFromOverride is not None:
        newEntry = entryFromOverride
        newEntry.date = None
    outputEntries.append(newEntry)

if len(outputEntries) > 1:
    header = dashboard.printHeader(scriptName="Manual Override", documentationUrl="A combination file "+ metricFileName + " and override file " + overrideFileName )
    outputFile = open(outputFileName, 'w')
    outputFile.write(header)
    for entry in outputEntries:
        outputFile.write(str(entry) + '\n')
    outputFile.close()
