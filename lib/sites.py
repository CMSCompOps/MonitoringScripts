import url, re
try: import xml.etree.ElementTree as ET
except ImportError: from elementtree import ElementTree as ET

cmsSiteName = re.compile(r'^(T[0,1,2,3])_([^_]{1,}?)_(.*?)$')
t1Pattern   = re.compile(r'^(T1)_([^_]{1,}?)_(.*)$')
t2Pattern   = re.compile(r'^(T2)_([^_]{1,}?)_(.*)$')
t3Pattern   = re.compile(r'^(T3)_([^_]{1,}?)_(.*)$')

def isValidCMSSiteName(site):
    match = cmsSiteName.match(site)
    if match: return True
    return False

def parseSiteName(compiledPattern, site):
    match = compiledPattern.match(site)
    if match: return match.groups()
    return False

def getTier(site):
    try:
        return int(site[1:2])
    except ValueError:
        return None
    return None

def getSites():
    XML   = url.read('http://dashb-cms-vo-feed.cern.ch/dashboard/request.py/cmssitemapbdii')
    XML   = ET.fromstring(XML)
    sites = XML.findall('atp_site')
    ret   = {}
    for site in sites:
        groups   = site.findall('group')
        siteName = None
        for i in groups:
            if i.attrib['type'] == 'CMS_Site':
                siteName = groups[1].attrib['name']
                break
        if not siteName: 
            continue
        services = site.findall('service')
        ret[siteName] = []
        for service in services:
            serviceName = service.attrib['hostname']
            ret[siteName].append(serviceName)
    return ret

if __name__ == '__main__':
    siteList = getSites()
    for i in siteList:
       print 'isValidCMSSiteName:\t', isValidCMSSiteName(i), i
       print 'parseSiteName:\t', parseSiteName(cmsSiteName, i)
       print 'getTier:\t', getTier(i)
