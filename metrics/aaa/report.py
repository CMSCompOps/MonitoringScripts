from lib import url, fileOps
import sys, os, time, copy
try:
    import json
    from json import encoder
    encoder.FLOAT_REPR = lambda o: format(o, '.2f')
except ImportError: import simplejson as json

if len(sys.argv) < 2:
    sys.exit('not enough arguments!')

tests = ['sam', 'hc', 'ggus']
# python report.py $TMP/report.json $TMP/report_2weeks.json
# set variables given from outside
currentReport   = json.loads(fileOps.read(sys.argv[1]))
htmlTemplate    = fileOps.read(sys.argv[2])
reportFile = sys.argv[3]
htmlOutputPath  = sys.argv[4]

if os.path.isfile(reportFile):
    print 'loading 2 weeks report...'
    report = json.loads(fileOps.read(reportFile))
else:
    print 'creating new 2 weeks report...'
    report = {'data' : {}}

# insert new test results
data = currentReport['data']
for site in data:
    if not report['data'].has_key(site):
        report['data'][site] = {}
    for test in tests:
        if not report['data'][site].has_key(test):
            report['data'][site][test] = {}
        if not data[site].has_key(test):
            continue
        report['data'][site][test][currentReport['lastUpdate']] = data[site][test]

# merge current report with old ones (delete test results older than 2 weeks!)
tmpData = copy.deepcopy(report['data'])
for site in tmpData:
    for test in tests:
        for timeStamp in tmpData[site][test]:
            # delete value if it is older than 2 weeks
            if time.time() - float(timeStamp) > 60*60*24*14:
                del report['data'][site][test][timeStamp]

# update time stamp
report['lastUpdate'] = time.time()
report['timeOffset'] = time.timezone

htmlTemplate = htmlTemplate.replace('@date@', time.strftime("%Y-%m-%d at %H:%M:%S", time.localtime(time.time())))

# write files and exit
fileOps.write(reportFile, json.dumps(report))
for site in data:
    siteReport = {'lastUpdate' : report['lastUpdate'], 'timeOffset' : report['timeOffset'],
                  'data' : {site : report['data'][site]}}
    siteReport = htmlTemplate.replace('@report@', json.dumps(siteReport))
    fileOps.write('%s/%s_report.html' % (htmlOutputPath, site), siteReport)
