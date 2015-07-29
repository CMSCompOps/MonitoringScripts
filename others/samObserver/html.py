import sys, os, time
try: import json
except ImportError: import simplejson as json
from lib import fileOps

if len(sys.argv) < 4:
    sys.stderr.write("not enough prameter!\n")
    sys.exit(1)

htmlTemplate = fileOps.read(sys.argv[1])
info         = sys.argv[2]
inOutPath    = sys.argv[3]

data         = {}
for i in os.listdir(inOutPath):
    if not '.json' in i: continue
    date     =  time.strftime("%B %d, %Y %H:%M:%S", time.localtime(int(i.replace('.json', ''))))
    data[date]  = json.loads(fileOps.read("{0}/{1}".format(inOutPath, i)))

jsData       = {}
for date in data:
    for site in data[date]:
        if not site in jsData:
            jsData[site] = {}
        if data[date][site] == 'n/a': data[date][site] = -1.0
        jsData[site][date] = data[date][site]

def allTheSame(data):
    oldVal = None
    val    = None
    for i in data:
        val = data[i]
        if oldVal != None and (val != oldVal): return False;
        oldVal = data[i]
    return True

for site in jsData.keys():
    if allTheSame(jsData[site]): del jsData[site]

report = htmlTemplate.replace('@DATA@', json.dumps(jsData))
report = report.replace('@INFO@', json.dumps(info))
fileOps.write("{0}/samObservationReport.html".format(inOutPath), report)
