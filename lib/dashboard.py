# aaltunda - ali.mehmet.altundag@cern.ch

try: import json
except ImportError: import simplejson as json
import time, re

green  = 'green'
yellow = 'yellow'
red    = 'red'
saddlebrown = 'saddlebrown'
cyan   = 'cyan'
grey   = 'grey'
white  = 'white'

# dashboard input entry structure
class entry:
    def __init__(self, date = None, name = None, value = None, color = None, url = None):
        if date == None:
            self.date = self.dateTimeNow()
        elif type(date) == float or type(date) == int:
            self.date = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(date))
        else:
            self.date  = date
        self.name  = name
        self.value = value
        self.color = color
        if url == None:
            self.url = '#'
        else:
            self.url = url

    def dateTimeNow(self):
        self.date = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())

    def __str__(self):
        return "%s\t%s\t%s\t%s\t%s" % (self.date, self.name, self.value, self.color, self.url)

# dashboard input metric class
class metric:
    def __init__(self):
        self.entries = []
        self._currentIndex = 0

    def __str__(self):
        return "\n".join(str(row) for row in self.entries)

    def append(self, entry):
        self.entries.append(entry)

    def hasSite(self, siteName):
        for i in self.entries:
            if siteName == i.name: return i
        return False

# dashboard json interface metric format
# since we get the metric data from the dashboard interface, we also
# have time information that defines slots in the metric plot.
# it is obvious that dashboard input entry structure does not have
# enough time field to support slots (it does only have entry creation
# time stamp, but in the dashboard we have slot start time and end time
# to define time range). in order to get rid of this problem, we will
# use end time of the slot as key value in the python dict type (entries)
# The structure for the jsonMetric.entries will be like following:
# entries['siteName' : {TheEndTime : dashboard.entry, 
#                       TheEndTime : dashboard.entry...}, ...]
class jsonMetric:
    def __init__(self, inJSON = '{}'):
        self.data  = json.loads(inJSON)
        self.slots = self.data['csvdata']
        self.entries    = {}
        self._parse()

    def _parse(self):
        for slot in self.slots:
            # get start & end time in unix time
            time     = self.dashboardTime2UnixTime(slot['Time'])
            endTime  = self.dashboardTime2UnixTime(slot['EndTime'])
            siteName = slot['VOName']
            value    = slot['Status']
            color    = slot['COLORNAME']
            url      = slot['URL']
            # add site names from the metric
            if not siteName in self.entries:
                self.entries[siteName] = {}
            self.entries[siteName][endTime] = entry(time, siteName, value, color, url)

    def dashboardTime2UnixTime(self, dashboardTime):
        # keep in mind that it will be returned in GMT!
        return time.mktime(time.strptime(dashboardTime, "%Y-%m-%dT%H:%M:%S"))

    def unixTime2DashboardTime(self, unixTime):
        return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(unixTime))

    def getSiteEntries(self, siteName):
        if self.entries.has_key(siteName): return self.entries[siteName]
        return {}

    def getLatestEntry(self, siteName):
        entries = self.getSiteEntries(siteName)
        if len(entries) == 0: return None
        entryKeys = entries.keys()
        entryKeys.sort(reverse=True)
        return entries[entryKeys[0]]

def parseMetric(data):
    # remove python style comments
    data    = re.sub(re.compile(r'^#.*$', re.MULTILINE), "", data)
    # kudos to jbalcas for the dashboard entry pattern!
    rows = re.findall(r'([0-9-: ]*)\t(T[0-3][_A-Za-z0-9]*)\t([A-Za-z\.0-9]*)\t([A-Za-z]*)\t(.*)', data, re.M)
    # create metric object to return the result in this structure
    ret  = metric()
    # append parsed entries to the metric object
    for row in rows:
        ret.append(entry(row[0], row[1], row[2], row[3], row[4]))
    return ret

if __name__ == '__main__':
    import url
    wrURL = 'https://cmst1.web.cern.ch/CMST1/WFMon/WaitingRoom_Sites.txt'
    wr    = parseMetric(url.read(wrURL))
    for site in wr:
        print str(site)
    print 'Number of rows:', len(wr)
