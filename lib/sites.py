# aaltunda - ali.mehmet.altundag@cern.ch

import url, re
try: import xml.etree.ElementTree as ET
except ImportError: from elementtree import ElementTree as ET

# general cms site name pattern. notice the last section,
# '_' is not excluded because we have sites named: T2_RU_RRC_KI,
# T2_UK_London_Brunel, T2_PT_NCG_Lisbon...
cmsSiteName       = re.compile(r'^(T[0,1,2,3])_([^_]{2})_(.*)$')

t1CompiledPattern = re.compile(r'^(T1)_([^_]{2})_(.*)$')
t2CompiledPattern = re.compile(r'^(T2)_([^_]{2})_(.*)$')
t3compiledPattern = re.compile(r'^(T3)_([^_]{2})_(.*)$')

def isValidCMSSiteName(site):
    """return True if it is cms site name"""
    match = cmsSiteName.match(site)
    if match: return True
    return False

def parseSiteName(site, compiledPattern = cmsSiteName):
    """parse cms site name and return its sub-sections"""
    match = compiledPattern.match(site)
    if match: return match.groups()
    return False

def getTier(site):
    """return tier number of given cms site name"""
    # check if not cms site name
    if not isValidCMSSiteName(site): return None
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
        if not siteName in ret: ret[siteName] = {}
        if not 'hosts' in ret[siteName]: ret[siteName]['hosts'] = []
        ret[siteName]['name']  = site.attrib['name']
        for service in services:
            if not 'production_status' in service.attrib:
                serviceName = service.attrib['hostname']
                ret[siteName]['hosts'].append(serviceName)
    return ret

if __name__ == '__main__':
    siteList = getSites()
    for i in siteList:
       print 'isValidCMSSiteName:', i, isValidCMSSiteName(i)
       print 'parseSiteName     :', parseSiteName(i)
       print 'getTier           :', getTier(i)
