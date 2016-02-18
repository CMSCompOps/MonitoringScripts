# aaltunda - ali.mehmet.altundag@cern.ch

try: import json
except ImportError: import simplejson as json
import time, re, os

green  = 'green'
yellow = 'yellow'
red    = 'red'
saddlebrown = 'saddlebrown'
cyan   = 'cyan'
gray   = 'gray'
white  = 'white'

def dashboardTime2UnixTime(dashboardTime):
    # try to convert dashboard input time format
    try:
        return time.mktime(time.strptime(dashboardTime, "%Y-%m-%d %H:%M:%S"))
    # try to convert dashboard JSON interface dashboard interface
    except ValueError:
        return time.mktime(time.strptime(dashboardTime, "%Y-%m-%dT%H:%M:%S"))

def unixTime2DashboardTime(unixTime):
    # the same story with the dashboardTime2UnixTime...
    try:
        return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(unixTime))
    except ValueError:
        return time.strftime("%Y-%m-%dT%H:%M:%S", time.localtime(unixTime))

# dashboard input entry structure
class entry:
    def __init__(self, date = None, name = None, value = None, color = None, url = None, nvalue=None):
        self.date = 0
        if date == None:
            self.date = int(time.time())
        elif type(date) == float or type(date) == int:
            self.date = date
        elif type(date) == str:
            self.date = dashboardTime2UnixTime(date)
        self.name  = name.strip()
        self.value = value
        self.color = color.strip()
        if nvalue is not None:
		self.nvalue = float(nvalue)
        else:
                self.nvalue = None
        if url == None:
            self.url = '#'
        else:
            self.url = url

    def __str__(self):
        if self.nvalue is None:
            return "%s\t%s\t%s\t%s\t%s" % (unixTime2DashboardTime(self.date), self.name, self.value, self.color, self.url)
        else:
            return "%s\t%s\t%s\t%s\t%s\tnvalue=%s" % (unixTime2DashboardTime(self.date), self.name, self.value, self.color, self.url, self.nvalue)

# dashboard input metric class
class metric:
    def __init__(self, header = {}):
        self.__entries = []
        if header == None:
            self.header = {}
        else:
            self.header    = {'user'  : os.getenv('USER'),
                              'host'  : str(os.uname()),
                              'email' : 'cms-comp-ops-site-support-team[at]cern.ch',
                              'repo'  : 'https://github.com/CMSCompOps/MonitoringScripts',
                              'responsible' : 'Site Support Team'}
            for key, val in header.items():
                self.header[key] = val

    def __str__(self):
        header  = "\n".join(['## %s: %s' % (key, value) for (key, value) in self.header.items()]) 
        content = "\n".join(str(row) for row in self.__entries)
        return "%s\n%s" % (header, content)

    def __list__(self):
        ret = []
        for i in self.__entries:
            ret.append(i.__dict__)
        return ret

    def append(self, entry):
        if entry.name in self.getSites():
            self.removeSiteEntry(entry.name)
        self.__entries.append(entry)

    def removeSiteEntry(self, name):
        self.__entries.remove(self.getSiteEntry(name))

    def hasSite(self, siteName):
        for i in self.__entries:
            if siteName == i.name: return True
        return False

    def getSites(self):
        siteList = []
        for i in self.__entries:
            siteList.append(i.name)
        return siteList

    def getSiteEntry(self, siteName):
        for i in self.__entries:
            if siteName == i.name: return i
        return None

    def getEntries(self):
        return self.__entries

def parseMetric(data):
    # remove python style comments
    data    = re.sub(re.compile(r'^#.*$', re.MULTILINE), "", data)
    # kudos to jbalcas for the dashboard entry pattern!
    rows = re.findall(r'([0-9-: ]*)\t(T[0-3][_A-Za-z0-9]*)\t([A-Za-z\.0-9]*)\t([A-Za-z]*)\t(.*)', data, re.M)
    # create metric object to return the result in this structure
    obj  = metric()
    # append parsed entries to the metric object
    for row in rows:
        obj.append(entry(row[0], row[1], row[2], row[3], row[4]))
    return obj

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
    def __init__(self):
        self.__entries    = {}

    def hasSite(self, siteName):
        if siteName in self.__entries: return True
        return False

    def getSites(self):
        return self.__entries.keys()

    def getSiteEntries(self, siteName):
        if self.__entries.has_key(siteName): return self.__entries[siteName]
        return {}

    def getLatestEntry(self, siteName):
        entries = self.getSiteEntries(siteName)
        if len(entries) == 0: return None
        return entries[max(entries)]

    def append(self, siteName, endTime, inEntry):
        if not siteName in self.__entries:
            self.__entries[siteName] = {}
        self.__entries[siteName][endTime] = inEntry

def parseJSONMetric(data):
    data  = json.loads(data)
    slots = data['csvdata']
    obj   = jsonMetric()
    for slot in slots:
        # get start & end time in unix time
        time     = dashboardTime2UnixTime(slot['Time'])
        endTime  = dashboardTime2UnixTime(slot['EndTime'])
        siteName = slot['VOName']
        value    = slot['Status']
        color    = slot['COLORNAME']
        url      = slot['URL']
        # add site names from the metric
        obj.append(siteName, endTime, entry(time, siteName, value, color, url))
    return obj

if __name__ == '__main__':
    import url
    wrURL = 'https://cmst1.web.cern.ch/CMST1/WFMon/WaitingRoom_Sites.txt'
    wr    = parseMetric(url.read(wrURL))
    for site in wr:
        print str(site)
    print 'Number of rows:', len(wr)
