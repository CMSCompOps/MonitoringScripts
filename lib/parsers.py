# aaltunda - ali.mehmet.altundag@cern.ch
# gkandemi - gokhan.kandermir@cern.ch

import re, dashboard

def metricParser(data):
    # remove python style comments
    data    = re.sub(re.compile(r'#.*$', re.MULTILINE), "", data)
    # this function has been written in order to parse metrics from dashboard
    rows = re.findall(r'(.*?)\t(.*?)\t(.*?)\t(.*?)\t(.*?)\n', data, re.M)
    ret  = []
    # convert them into dashboard entry structure
    for row in rows:
        ret.append(dashboard.entry(row[0], row[1], row[2], row[3], row[4]))
    return ret

if __name__ == '__main__':
    import url
    wrURL = 'https://cmst1.web.cern.ch/CMST1/WFMon/WaitingRoom_Sites.txt'
    wr    = metricParser(url.read(wrURL))
    for site in wr:
        print str(site)
