# aaltunda - ali.mehmet.altundag@cern.ch

import time, re

green  = 'green'
yellow = 'yellow'
red    = 'red'
saddlebrown = 'saddlebrown'
cyan   = 'cyan'
grey   = 'grey'
white  = 'white'

# dashboard entry structure
class entry:
    def __init__(self, date = None, name = None, value = None, color = None, url = None):
        if date == None:
            self.date = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
        else:
            self.date  = date
        self.name  = name
        self.value = value
        self.color = color
        if url == None:
            self.url = '#'
        else:
            self.url = url

    def __str__(self):
        return "%s\t%s\t%s\t%s\t%s" % (self.date, self.name, self.value, self.color, self.url)

def parseMetric(data):
    # remove python style comments
    data    = re.sub(re.compile(r'^#.*$', re.MULTILINE), "", data)
    # kudos to jbalcas for the dashboard entry pattern!
    rows = re.findall(r'([0-9-: ]*)\t(T[0-3][_A-Za-z0-9]*)\t([A-Za-z\.0-9]*)\t([A-Za-z]*)\t(.*)', data, re.M)
    ret  = []
    # convert them into dashboard entry structure
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
