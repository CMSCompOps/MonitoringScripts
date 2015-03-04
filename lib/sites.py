import url, re
try: import xml.etree.ElementTree as ET
except ImportError: from elementtree import ElementTree as ET

t1Pattern = r'^(T1)_([^_]*?)_([^_]*?)$'
t2Pattern = r'^(T2)_([^_]*?)_([^_]*?)$'
t3Pattern = r'^(T3)_([^_]*?)_([^_]*?)$'

def parseSiteName(pattern, site):
    match = re.match(pattern, site)
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
    print getSites()
