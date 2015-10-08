from lib import url, fileOps
import sys, os, time
try: import json
except ImportError: import simplejson as json

if len(sys.argv) < 2:
    sys.exit('not enough arguments!')

tests = ['sam', 'hc', 'ggus']
# python report.py $TMP/report.json $TMP/report_2weeks.json
# set variables given from outside
currentReport   = json.loads(fileOps.read(sys.argv[1]))
htmlTemplate    = fileOps.read(sys.argv[2])
finalReportFile = sys.argv[3]
htmlOutputPath  = sys.argv[4]

if os.path.isfile(finalReportFile):
    print 'loading 2 weeks report...'
    finalReport = json.loads(fileOps.read(finalReportFile))
else:
    print 'creating new 2 weeks report...'
    finalReport = {'data' : {}}

# insert new test results
data = currentReport['data']
for site in data:
    if not finalReport['data'].has_key(site):
        finalReport['data'][site] = {}
    for test in tests:
        if not finalReport['data'][site].has_key(test):
            finalReport['data'][site][test] = {}
        if not data[site].has_key(test):
            continue
        finalReport['data'][site][test][currentReport['lastUpdate']] = data[site][test]

# merge current report with old ones (delete test results older than 2 weeks!)
data = finalReport['data']
for site in data:
    for test in tests:
        for timeStamp in data[site][test]:
            # delete value if it is older than 2 weeks
            if time.time() - float(timeStamp) > 60*60*24*14:
                del data[site][test][timeStamp]

# update time stamp
finalReport['lastUpdate'] = time.time()
finalReport = json.dumps(finalReport)

htmlTemplate = htmlTemplate.replace('@report@', finalReport)
htmlTemplate = htmlTemplate.replace('@date@', time.strftime("%Y-%m-%d at %H:%M:%S", time.localtime(time.time())))

# write files and exit
fileOps.write(finalReportFile, finalReport)
fileOps.write('%s/report.html' % htmlOutputPath, htmlTemplate)
