#!/usr/bin/env python
# Rev. history
# original by Burt Holzman, ~summer 2008
# 15 Jan 2009 - S.Belforte add ACBR for production role in OR
# 20 Jan 2009 - S.Belforte add ACBR for lcgadmin rolde in OR
#

import re, sys, ldap

def ldapquery(filter, attributes, bdii):
    attributes = attributes.split(' ')

    filter = filter.lstrip("'").rstrip("'")

    bdiiuri = 'ldap://' + bdii + ':2170'
    l = ldap.initialize(bdiiuri)
    
    l.simple_bind_s('', '')

    base = "o=grid"
    scope = ldap.SCOPE_SUBTREE
    timeout = 0
    result_set = []
    filter = filter.strip("'")
    #print filter
    try:
        result_id = l.search(base, scope, filter, attributes)
        while 1:
            result_type, result_data = l.result(result_id, timeout)
            if (result_data == []):
                break
            else:
                if result_type == ldap.RES_SEARCH_ENTRY:
                    result_set.append(result_data)

    except ldap.LDAPError, error_message:
        print error_message

    return result_set

def listAllCEs(bdii='lcg-bdii.cern.ch'):
    ''' List all GlueCEUniqueIDs that advertise support for CMS '''
    
    RE_cename = re.compile('^GlueCEUniqueID: (.*)', re.IGNORECASE)
    filt1 = '(&(GlueCEUniqueID=*)(GlueCEAccessControlBaseRule=VO:cms))'
    filt2 = '(&(GlueCEUniqueID=*)(GlueCEAccessControlBaseRule=VOMS:/cms/Role=production))'
    filt3 = '(&(GlueCEUniqueID=*)(GlueCEAccessControlBaseRule=VOMS:/cms/Role=lcgadmin))'
    filt='(|(|'+filt1+filt2+')'+filt3+')'    
    res = ldapquery(filt, 'GlueCEUniqueID', bdii)
    ceList = [x[0][1]['GlueCEUniqueID'][0] for x in res]
    return ceList
    
def getSW(ceList, bdii='lcg-bdii.cern.ch'):
    ''' Given a list of GlueCEUniqueIDs, returns a dict of
    {gatekeeper, ['SWtag1', 'SWtag2', ... ]}
    '''
    
    filt = '(&(GlueForeignKey=GlueClusterUniqueID=*)(|'
    for host in ceList:
        filt += '(GlueCEUniqueID=' + host + ')'
    filt += '))'

    res = ldapquery(filt, 'GlueForeignKey GlueCEUniqueID', bdii)

    CE_to_Cluster = {}
    for x in res:
        key = x[0][1]['GlueCEUniqueID'][0]
        val = x[0][1]['GlueForeignKey'][0]
        CE_to_Cluster[key] = val

    clusterList = []

    for cluster in CE_to_Cluster.values():
        if not clusterList.count(cluster): clusterList.append(cluster)

    filt = '(&(GlueHostApplicationSoftwareRunTimeEnvironment=*)(|'
    for cluster in clusterList:
        filt += '(GlueChunkKey=' + cluster + ')'

    filt += '))'    

    res = ldapquery(filt, 'GlueChunkKey GlueHostApplicationSoftwareRunTimeEnvironment', bdii)
    Cluster_to_SW = {}
    for x in res:
        key = x[0][1]['GlueChunkKey'][0]
        val = x[0][1]['GlueHostApplicationSoftwareRunTimeEnvironment']
        cmstag=[]
        for tag in val:
            if tag.startswith("VO-cms"):
                cmstag.append(tag.replace("VO-cms-",""))
        Cluster_to_SW[key] = cmstag

    CE_to_SW = {}
    for key in CE_to_Cluster.keys():
        cluster = CE_to_Cluster[key]
        try:
            SW = Cluster_to_SW[cluster]
            CE_to_SW[key] = SW
        except KeyError:
            print 'Error: Software not found for %s' % cluster

    GK_to_SW = {}
    for key in CE_to_SW.keys():
        SW = CE_to_SW[key]
        gk = key.split(':')[0] # assumes we are showing the port in the info system
        GK_to_SW[gk] = SW

    return GK_to_SW
    
if __name__ == '__main__':
    import string
    from pprint import pprint
#    bdii = 'uscmsbd2.fnal.gov'
    bdii = 'lcg-bdii.cern.ch'
#    bdii = 'sam-bdii.cern.ch'
    celist = listAllCEs(bdii)
    #pprint (celist)
    swmap = getSW(celist, bdii)
    #pprint(swmap)
    for ce in swmap.keys():
        ceWithCommas=string.replace(ce,'.',',')
        fname="./published-tags/%s" % ceWithCommas
        file=open(fname,'w')
        for tag in swmap[ce]:
            file.write("%s\n" % tag)
        file.close
