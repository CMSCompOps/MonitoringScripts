#!/usr/bin/python
# ########################################################################### #
# python script to write the CMS VO-feed XML and JSON files. The script is    #
#    based on earlier versions that run inside the SAM3 dashboard.            #
#                                                                             #
# 2016-Dec-28   Stephan Lammel                                                #
# ########################################################################### #


import os, sys, getpass
import time, calendar
import socket
import httplib, urllib2
from OpenSSL import crypto
import json
import xml.etree.ElementTree as ET
import htcondor
# ########################################################################### #



VOFD_VERSION = "v0.01.03"
#VOFD_OUTPUT_FILE = "vofeed.xml"
#VOFD_IN_USE_FILE = "in_use.txt"
#VOFD_CACHE_DIR = "."
VOFD_OUTPUT_FILE = "/afs/cern.ch/user/c/cmssst/www/vofeed/vofeed.xml"
VOFD_IN_USE_FILE = "/afs/cern.ch/user/c/cmssst/www/vofeed/in_use.txt"
VOFD_CACHE_DIR = "/data/cmssst/MonitoringScripts/vofeed"

#VOFD_CERTIFICATE_CRT = "/lml/user/lammel/.globus/usercert.pem"
#VOFD_CERTIFICATE_KEY = "/lml/user/lammel/.globus/userkey.pem"
VOFD_CERTIFICATE_CRT = "/tmp/x509up_u79522"
VOFD_CERTIFICATE_KEY = "/tmp/x509up_u79522"
# ########################################################################### #



glbInfo = {}
glbTopology = None
# ########################################################################### #



class HTTPSClientAuthHandler(urllib2.HTTPSHandler):
    'Urllib2.HTTPSHandler class with certificate access'

    def __init__(self):
        urllib2.HTTPSHandler.__init__(self)

    def https_open(self, req):
        return self.do_open(self.getConnection, req)

    def getConnection(self, host, timeout=90):
        return httplib.HTTPSConnection(host, key_file=VOFD_CERTIFICATE_KEY,
                                             cert_file=VOFD_CERTIFICATE_CRT)
# ########################################################################### #



class vofdTopology:
    'Site Topology class of the CMS VO-feed module'

    def __init__(self):
        self.topo = {}

    def addSite(self, cmssite, gridsite=""):
        if not self.topo.has_key(cmssite):
            self.topo[cmssite] = []
        if ( gridsite != "" ):
            for site in self.topo[cmssite]:
                if ( site['gsite'] == gridsite ):
                   return
            self.topo[cmssite].append( {'gsite': gridsite, 'rsrcs': []} )

    def addResource(self, cmssite, gridsite,
                    host, flavour, prod=True, queue="", batch=""):
        if not self.topo.has_key(cmssite):
            print("cmssite unknown, skipping %s(%s) at %s" %
                (host, flavour, cmssite))
            return
        if ( gridsite == "" ):
            if ( len(self.topo[cmssite]) >= 1 ):
                index = 0
            else:
                print("no gridsite, skipping %s(%s) at %s" %
                    (host, flavour, cmssite))
                return
        else:
            for index in range( len(self.topo[cmssite]) ):
                if ( self.topo[cmssite][index]['gsite'] == gridsite ):
                    break
            if ( self.topo[cmssite][index]['gsite'] != gridsite ):
                self.topo[cmssite].append( {'gsite': gridsite, 'rsrcs': []} )
                index = len(self.topo[cmssite]) - 1

        for rsrc in self.topo[cmssite][index]['rsrcs']:
            if (( rsrc['host'] == host ) and ( rsrc['type'] == flavour )):
                print("duplicate entry, skipping %s(%s) at %s" %
                    (host, flavour, cmssite))
                return
        self.topo[cmssite][index]['rsrcs'].append( {'host': host,
            'type': flavour, 'prod': prod, 'queue': queue, 'batch': batch} )

    def write(self, file=sys.stdout, offset=0):
        off = "".ljust(offset)
        #
        for cmssite in sorted(self.topo.keys()):
            file.write("%s%s\n" % (off, cmssite))
            for indx in range( len(self.topo[cmssite]) ):
                file.write("%s   %s\n" %
                    (off, self.topo[cmssite][indx]['gsite']))
                for rsrc in self.topo[cmssite][indx]['rsrcs']:
                    if ( rsrc['queue'] == "" ):
                        file.write("%s      %s (%s) prod=%r\n" %
                            (off, rsrc['host'], rsrc['type'], rsrc['prod']))
                    elif ( rsrc['batch'] == "" ):
                        file.write("%s      %s (%s) prod=%r queue=%s\n" %
                            (off, rsrc['host'], rsrc['type'], rsrc['prod'],
                             rsrc['queue']))
                    else:
                        file.write(("%s      %s (%s) prod=%r queue=%s batch=" +
                            "%s\n") % (off, rsrc['host'], rsrc['type'],
                            rsrc['prod'], rsrc['queue'], rsrc['batch']))
# ########################################################################### #



def vofd_init():
    global glbInfo
    global glbTopology

    glbInfo['timestamp'] = int( time.time() )
    #
    cert = crypto.load_certificate(crypto.FILETYPE_PEM,
                                   file(VOFD_CERTIFICATE_CRT, 'r').read() )
    subject = str( cert.get_subject() )
    subject = subject.split("'")[1::2][0].replace("'", "")
    glbInfo['certowner'] = subject.replace("<", "[").replace(">", "]")
    del subject
    del cert
    #
    glbInfo['url'] = "http://cmssst.web.cern.ch/cmssst/vofeed/vofeed.xml"

    glbTopology = vofdTopology()
# ########################################################################### #



def vofd_sitedb():
    # ########################################################## #
    # fill vofdTopology object with site information from SiteDB #
    # ########################################################## #
    URL_SITEDB_SITES = 'https://cmsweb.cern.ch/sitedb/data/prod/site-names'

    # get list of CMS sites from SiteDB:
    # ==================================
    print("Querying SiteDB for site information")
    urlHandle = None
    try:
        request = urllib2.Request(URL_SITEDB_SITES,
                              headers={'Accept':'application/json'})
        urlHandle = urllib2.urlopen( request )
        myData = urlHandle.read()
        #
        # sanity check:
        if (( myData.count("T0_") < 2 ) or ( myData.count("T1_") < 10 ) or
            ( myData.count("T2_") < 64 ) or ( myData.count("T3_") < 96 )):
            raise IOError("SiteDB data failed sanity check")
        #
        # update cache:
        try:
            myFile = open("%s/cache_SiteDB.json_new" % VOFD_CACHE_DIR, 'w')
            try:
                myFile.write(myData)
                renameFlag = True
            except:
                renameFlag = False
            finally:
                myFile.close()
                del myFile
            if renameFlag:
                os.rename("%s/cache_SiteDB.json_new" % VOFD_CACHE_DIR,
                    "%s/cache_SiteDB.json" % VOFD_CACHE_DIR)
                print("   cache of SiteDB updated")
            del renameFlag
        except:
            pass
    except:
        print("   failed to fetch SiteDB data")
        try:
            myFile = open("%s/cache_SiteDB.json" % VOFD_CACHE_DIR, 'r')
            try:
                myData = myFile.read()
                print("   using cached SiteDB data")
            except:
                print("   failed to access cached SiteDB data")
                return
            finally:
                myFile.close()
                del myFile
        except:
            print("   no SiteDB cache available")
            return
    finally:
        if urlHandle is not None:
            urlHandle.close()
    del urlHandle
    #
    sitedb = json.loads( myData )

    # find indices with information of interest:
    columns = sitedb['desc']['columns']
    nameIndex = columns.index('site_name')
    typeIndex = columns.index('type')
    siteIndex = columns.index('alias')

    myDict = {}
    # patch to advance Purdue-Hadoop grid site ahead of the SiteDB list:
    myDict['Purdue'] = {'cmssite':'T2_US_Purdue', 'gridsite':[]}
    myDict['Purdue']['gridsite'].append('Purdue-Hadoop')
    for result in sitedb['result']:
        sitedbname = result[nameIndex]
        if not myDict.has_key(sitedbname):
            myDict[sitedbname] = {'cmssite':'', 'gridsite':[]}
        if ( result[typeIndex] == 'cms' ):
            cmssite = result[siteIndex]
            # filter out fake "*_Disk", "*_Buffer", and "*_MSS" sites
            if ( cmssite.find('_Disk', 5) > 0 ): continue
            if ( cmssite.find('_Buffer', 5) > 0 ): continue
            if ( cmssite.find('_MSS', 5) > 0 ): continue
            myDict[sitedbname]['cmssite'] = cmssite
        elif ( result[typeIndex] == 'lcg' ):
            gridsite = result[siteIndex]
            myDict[sitedbname]['gridsite'].append(gridsite)

    # add CMS site to VO-feed topology:
    for entry in myDict.keys():
        if ( myDict[entry]['cmssite'] != "" ):
            if ( len(myDict[entry]['gridsite']) == 0 ):
               glbTopology.addSite(myDict[entry]['cmssite'])
            else:
                for indx in range( len(myDict[entry]['gridsite']) ):
                    glbTopology.addSite(myDict[entry]['cmssite'],
                                        myDict[entry]['gridsite'][indx])
# ########################################################################### #



def vofd_phedex():
    # ############################################################## #
    # fill vofdTopology object with SE/SRMv2 information from PhEDEx #
    # ############################################################## #
    URL_PHEDEX_SENAME = 'https://cmsweb.cern.ch/phedex/datasvc/json/prod/senames?protocol=srmv2'

    # get list of CMS sites from SiteDB:
    # ==================================
    print("Querying PhEDEx for SRMv2 SE name information")
    urlHandle = None
    try:
        request = urllib2.Request(URL_PHEDEX_SENAME,
                              headers={'Accept':'application/json'})
        urlHandle = urllib2.urlopen( request )
        myData = urlHandle.read()
        #
        # sanity check:
        if (( myData.count("T0_") < 2 ) or ( myData.count("T1_") < 10 ) or
            ( myData.count("T2_") < 48 ) or ( myData.count("T3_") < 16 )):
            raise IOError("PhEDEx SRMv2 data failed sanity check")
        #
        # update cache:
        try:
            myFile = open("%s/cache_PhEDEx.json_new" % VOFD_CACHE_DIR, 'w')
            try:
                myFile.write(myData)
                renameFlag = True
            except:
                renameFlag = False
            finally:
                myFile.close()
                del myFile
            if renameFlag:
                os.rename("%s/cache_PhEDEx.json_new" % VOFD_CACHE_DIR,
                    "%s/cache_PhEDEx.json" % VOFD_CACHE_DIR)
                print("   cache of PhEDEx SRMv2 SE name updated")
            del renameFlag
        except:
            pass
    except:
        print("   failed to fetch PhEDEx SRMv2 SE name data")
        try:
            myFile = open("%s/cache_PhEDEx.json" % VOFD_CACHE_DIR, 'r')
            try:
                myData = myFile.read()
                print("   using cached PhEDEx SRMv2 SE name data")
            except:
                print("   failed to access cached PhEDEx SRMv2 SE name data")
                return
            finally:
                myFile.close()
                del myFile
        except:
            print("   no PhEDEx SRMv2 SE name cache available")
            return
    finally:
        if urlHandle is not None:
            urlHandle.close()
    del urlHandle
    #
    # unpack JSON data of PhEDEx SRMv2 SE name information:
    phedex = json.loads( myData )
    
    # PhEDEx provides a snapshot in time:
    senames = phedex['phedex']['senames']

    for entry in senames:
        phedex_site = entry['node']
        phedex_host = entry['sename']

        # remove any "_Disk", "_Buffer", and "_MSS" from site names
        phedex_site = phedex_site.replace('_Disk','')
        phedex_site = phedex_site.replace('_Buffer','')
        phedex_site = phedex_site.replace('_Export','')
        phedex_site = phedex_site.replace('_MSS','')
        #print("SE: %s\t%s" % (phedex_site, phedex_host))
        if (( phedex_site == "T1_US_FNAL" ) and
            ( phedex_host == "cmslmon.fnal.gov" )):
            glbTopology.addResource(phedex_site, "", phedex_host, "SRM", False)
        else:
            glbTopology.addResource(phedex_site, "", phedex_host, "SRM")
# ########################################################################### #



def vofd_glideinWMSfactory():
    # ###################################################################### #
    # fill vofdTopology object with CE information from glide-in WMS factory #
    # ###################################################################### #
    DICT_GLIDEIN_FACTORIES = [
       {'lbl': "UCSD",   'uri': "gfactory-1.t2.ucsd.edu",   'prd': True},
       {'lbl': "OSG",    'uri': "glidein.grid.iu.edu",      'prd': True},
       {'lbl': "CERN",   'uri': "vocms0805.cern.ch",        'prd': True},
       {'lbl': "FNAL",   'uri': "cmsgwms-factory.fnal.gov", 'prd': True},
       {'lbl': "OSGint", 'uri': "glidein-itb.grid.iu.edu",  'prd': False} ]

    # get list of CEs used by CMS from the glide-in WMS factories:
    # ============================================================
    for factory in DICT_GLIDEIN_FACTORIES:
        #
        #print("\n\n\n\n\n\n")
        print("Querying %s factory for CE information" % factory['lbl'])
        collector = None
        try:
            collector = htcondor.Collector(factory['uri'])
            classAds = collector.query(htcondor.AdTypes.Any, "(MyType =?= \"glidefactory\") && (GLIDEIN_CMSSite isnt Undefined) && (GLIDEIN_ResourceName isnt Undefined) && (GLIDEIN_Gatekeeper isnt Undefined) && (GLIDEIN_GridType isnt Undefined)", ['GLIDEIN_CMSSite', 'GLIDEIN_ResourceName', 'GLIDEIN_Gatekeeper', 'GLIDEIN_GridType', 'GLIDEIN_GlobusRSL'])
            # catch HT Condor's faulty error handling:
            if not classAds:
                raise IOError("Empty Collector ClassAd List")
            if ( len(classAds) < 16 ):
                raise IOError("Collector ClassAd list failed sanity check")
            # convert list of classAd objects into list of dictionaries:
            myData = []
            for classAd in classAds:
                if 'GLIDEIN_GlobusRSL' in classAd:
                    globusRSL = classAd['GLIDEIN_GlobusRSL']
                else:
                    globusRSL = ""
                myData.append( {
                    'GLIDEIN_ResourceName': classAd['GLIDEIN_ResourceName'],
                    'GLIDEIN_GridType': classAd['GLIDEIN_GridType'],
                    'GLIDEIN_Gatekeeper': classAd['GLIDEIN_Gatekeeper'],
                    'GLIDEIN_GlobusRSL': globusRSL,
                    'GLIDEIN_CMSSite': classAd['GLIDEIN_CMSSite']
                    } )
            #
            # update cache:
            try:
                myFile = open("%s/cache_%s_factory.json_new" %
                    (VOFD_CACHE_DIR, factory['lbl']), 'w')
                try:
                    json.dump(myData, myFile)
                    renameFlag = True
                except:
                    renameFlag = False
                finally:
                    myFile.close()
                    del myFile
                if renameFlag:
                    os.rename("%s/cache_%s_factory.json_new" %
                        (VOFD_CACHE_DIR, factory['lbl']),
                        "%s/cache_%s_factory.json" %
                        (VOFD_CACHE_DIR, factory['lbl']))
                    print("   cache of %s factory updated" % factory['lbl'])
                del renameFlag
            except:
                pass
        except:
            print("   failed to fetch %s factory data" % factory['lbl'])
            try:
                myFile = open("%s/cache_%s_factory.json" %
                    (VOFD_CACHE_DIR, factory['lbl']), 'r')
                try:
                    myData = json.load( myFile )
                    print("   using cached %s factory data" % factory['lbl'])
                except:
                    print("   failed to access cached %s factory data" %
                          factory['lbl'])
                    return
                finally:
                    myFile.close()
                    del myFile
            except:
                print("   no %s factory cache available" % factory['lbl'])
                return
        finally:
            if collector is not None:
                pass
        del collector
        #
        for classAd in myData:
            gridsite = classAd['GLIDEIN_ResourceName']
            host = classAd['GLIDEIN_Gatekeeper']
            host = host.split()[-1].split(":")[0]
            ceType = "CE"
            if classAd['GLIDEIN_GridType'] == 'cream':
                ceType = "CREAM-CE"
            elif classAd['GLIDEIN_GridType'] == 'nordugrid':
                ceType = "ARC-CE"
            elif classAd['GLIDEIN_GridType'] == 'condor':
                ceType = "HTCONDOR-CE"
            elif ( classAd['GLIDEIN_GridType'].find('gt') == 0 ):
                ceType = "GLOBUS"
            #
            queue = ""
            batch = classAd['GLIDEIN_Gatekeeper'].split()[-1]
            if ( batch.find("/") <= 0 ):
                batch = ""
            else:
                batch = batch.split("/")[1]
                if ( batch.find("-") <= 0 ):
                    batch = ""
                else:
                    if ( batch.find("-") != batch.rfind("-") ):
                        queue = batch.split("-")[2]
                    batch = batch.split("-")[1]
            #
            if ( queue == "" ):
                indx1 = classAd['GLIDEIN_GlobusRSL'].find("(queue=")
                if ( indx1 >= 0 ):
                    indx1 += 7
                    indx2 = classAd['GLIDEIN_GlobusRSL'].find(")", indx1)
                    queue = classAd['GLIDEIN_GlobusRSL'][indx1:indx2]

            #print("CE: %s\t%s\t%s\t%s\t%s" %
            #    (gridsite, classAd['GLIDEIN_CMSSite'], host, ceType, queue))
            glbTopology.addResource(classAd['GLIDEIN_CMSSite'], gridsite,
                host, ceType, factory['prd'], queue, batch)
            if ( classAd['GLIDEIN_CMSSite'] == "T2_CH_CERN" ):
                glbTopology.addResource("T0_CH_CERN", gridsite,
                    host, ceType, factory['prd'], queue, batch)
                glbTopology.addResource("T3_CH_CERN_CAF", gridsite,
                    host, ceType, factory['prd'], queue, batch)
# ########################################################################### #



def vofd_write_xml():
    # ################################################################# #
    # write VO-feed XML based on information in the vofdTopology object #
    # ################################################################# #
    FIRST_PASS_SITES = [
       {'cmssite': "T0_CH_CERN", 'gridsite': "CERN-PROD"},
       {'cmssite': "T2_CH_CSCS", 'gridsite': "CSCS-LCG2"},
       {'cmssite': "T2_US_Purdue", 'gridsite': "Purdue-Hadoop"},
       {'cmssite': "T2_US_Nebraska", 'gridsite': "Nebraska"},
    ]
    SAM3_GROUPS = {
        '0': ['AllGroups', 'Tier1s + Tier0', 'Tier2s + Tier1s + Tier0'],
        '1': ['AllGroups', 'Tier1s + Tier0', 'Tier2s + Tier1s + Tier0',
              'Tier3s + Tier2s + Tier1s'],
        '2': ['AllGroups', 'Tier2s', 'Tier3s + Tier2s',
              'Tier2s + Tier1s + Tier0', 'Tier3s + Tier2s + Tier1s'],
        '3': ['AllGroups', 'Tier3s', 'Tier3s + Tier2s',
              'Tier3s + Tier2s + Tier1s'],
        '9': ['AllGroups']
    }

    renameFlag = False
    tierCnt = {'0': 0, '1': 0, '2': 0, '3': 0, '9': 0}
    myFile = open(VOFD_OUTPUT_FILE + "_new", 'w')
    try:
        myFile.write("<root>\n   <title>CMS Topology Information</title>\n")
        myFile.write("   <description>List of CMS grid sites and resources f" +
            "or SAM/WLCG monitoring</description>\n")
        myFile.write("   <feed_responsible>DN=\"%s\"</feed_responsible>\n" %
            glbInfo['certowner'])
        myFile.write("   <last_update>%s</last_update>\n" %
            time.strftime("%Y-%m-%dT%H:%M:%SZ",
                         
                           time.gmtime(glbInfo['timestamp'])))
        myFile.write("   <vo>cms</vo>\n")
        #
        # write main multi-CMS and multi-grid site in first pass for GGUS:
        for site in FIRST_PASS_SITES:
            tier = site['cmssite'][1:2]
            if tier not in ['0', '1', '2', '3']:
                tier = '9'
            toposite = glbTopology.topo[ site['cmssite'] ]
            for indx in range( len( toposite ) ):
                if ( site['gridsite'] == toposite[indx]['gsite'] ):
                    tierCnt[tier] += 1
                    myFile.write("   <atp_site name=\"%s\">\n" %
                        toposite[indx]['gsite'])
                    for rsrc in toposite[indx]['rsrcs']:
                        myFile.write(("      <service hostname=\"%s\" flavou" +
                            "r=\"%s\"") % (rsrc['host'], rsrc['type']))
                        if ( not rsrc['prod'] ):
                            myFile.write(" production_status=\"false\"")
                        if (( rsrc['queue'] != "" ) and
                            ( rsrc['type'] in ["GLOBUS", "CREAM-CE"] ) and
                            ( rsrc['batch'] != "" )):
                            myFile.write((">\n         <ce_resource batch_sy" +
                                "stem=\"%s\" queue=\"%s\"/>\n      </service" +
                                ">\n") % (rsrc['batch'], rsrc['queue']))
                        elif ( rsrc['queue'] != "" ):
                            myFile.write((">\n         <ce_resource queue=\"" +
                                "%s\"/>\n      </service>\n") % rsrc['queue'])
                        elif (( rsrc['type'] in ["GLOBUS", "CREAM-CE"] ) and
                              ( rsrc['batch'] != "" )):
                            myFile.write((">\n         <ce_resource batch_sy" +
                                "stem=\"%s\"/>\n      </service>\n") %
                                rsrc['batch'])
                        else:
                            myFile.write("/>\n")
                    myFile.write(("      <group name=\"Tier-%s\" type=\"CMS" +
                         "_Tier\"/>\n") % tier)
                    myFile.write(("      <group name=\"%s\" type=\"CMS_Site" +
                         "\"/>\n") % site['cmssite'])
                    for tierGroup in SAM3_GROUPS[tier]:
                        myFile.write(("      <group name=\"%s\" type=\"%s\"" +
                            "/>\n") % (site['cmssite'], tierGroup))
                    myFile.write("   </atp_site>\n")
        # write all other sites in a second pass:
        for cmssite in sorted(glbTopology.topo.keys()):
            tier = cmssite[1:2]
            if tier not in ['0', '1', '2', '3']:
                tier = '9'
            toposite = glbTopology.topo[cmssite]
            for indx in range( len(toposite) ):
                if {'cmssite': cmssite, 'gridsite': toposite[indx]['gsite']} \
                    in FIRST_PASS_SITES:
                    continue
                # supress sites without CE or SE resource:
                if ( len( toposite[indx]['rsrcs'] ) == 0 ):
                    print("Skipping resource-less site %s/%s" %
                        (cmssite, toposite[indx]['gsite']))
                    continue
                tierCnt[tier] += 1
                myFile.write("   <atp_site name=\"%s\">\n" %
                    toposite[indx]['gsite'])
                for rsrc in toposite[indx]['rsrcs']:
                    myFile.write(("      <service hostname=\"%s\" flavour=" +
                        "\"%s\"") % (rsrc['host'], rsrc['type']))
                    if ( not rsrc['prod'] ):
                        myFile.write(" production_status=\"false\"")
                    if (( rsrc['queue'] != "" ) and
                        ( rsrc['type'] in ["GLOBUS", "CREAM-CE"] ) and
                        ( rsrc['batch'] != "" )):
                        myFile.write((">\n         <ce_resource batch_system" +
                            "=\"%s\" queue=\"%s\"/>\n      </service>\n") %
                            (rsrc['batch'], rsrc['queue']))
                    elif ( rsrc['queue'] != "" ):
                        myFile.write((">\n         <ce_resource queue=\"%s\"" +
                            "/>\n      </service>\n") % rsrc['queue'])
                    elif (( rsrc['type'] in ["GLOBUS", "CREAM-CE"] ) and
                          ( rsrc['batch'] != "" )):
                        myFile.write((">\n         <ce_resource batch_system" +
                            "=\"%s\"/>\n      </service>\n") % rsrc['batch'])
                    else:
                        myFile.write("/>\n")
                myFile.write(("      <group name=\"Tier-%s\" type=\"CMS_Tier" +
                    "\"/>\n") % tier)
                myFile.write("      <group name=\"%s\" type=\"CMS_Site\"/>\n" %
                    cmssite)
                for tierGroup in SAM3_GROUPS[tier]:
                   myFile.write("      <group name=\"%s\" type=\"%s\"/>\n" %
                       (cmssite, tierGroup))
                myFile.write("   </atp_site>\n")
        myFile.write("</root>\n")
        renameFlag = True
    finally:
        myFile.close()
    if renameFlag:
        # sanity check:
        if (( tierCnt['0'] >= 1 ) and ( tierCnt['1'] >= 5 ) and
            ( tierCnt['2'] >= 32 ) and ( tierCnt['3'] >= 48 )):
            os.rename(VOFD_OUTPUT_FILE + "_new", VOFD_OUTPUT_FILE)
        else:
            print("Tier count sanity check failed, %d/%d/%d/%d" %
                (tierCnt['0'], tierCnt['1'], tierCnt['2'], tierCnt['3']))
    else:
        print("Failed to write VO-feed file")
# ########################################################################### #



def vofd_write_metric():
    # #################################################################### #
    # write metric file with grid resources in prod use for SAM3 dashboard #
    # #################################################################### #

    resourceCnt = -1
    myFile = open(VOFD_IN_USE_FILE + "_new", 'w')
    try:
        myFile.write(("#txt\n#\n# Site Support Team, Resources in Production" +
            " Use Metric\n#    written at %s by %s\n#    in account %s on no" +
            "de %s\n#    maintained by cms-comp-ops-site-support-team@cern.c" +
            "h\n#    https://twiki.cern.ch/twiki/bin/viewauth/CMS/SiteSuppor" +
            "tSiteStatusSiteReadiness\n# ===================================" +
            "=====================================\n#\n") %
            (time.strftime("%Y-%b-%d %H:%M:%S UTC",
                           time.gmtime(glbInfo['timestamp'])),
             sys.argv[0], getpass.getuser(), socket.getfqdn()))
        #
        # write CEs and SEs in production use:
        sList = []
        for cmssite in sorted(glbTopology.topo.keys()):
            toposite = glbTopology.topo[cmssite]
            for indx in range( len(toposite) ):
                for rsrc in toposite[indx]['rsrcs']:
                    if ( rsrc['prod'] ):
                        sDict = {'host': rsrc['host'], 'flavour': rsrc['type']}
                        if sDict in sList:
                            continue
                        myFile.write("%s\t%s %s\tproduction\tgreen\t%s\n" %
                            (time.strftime("%Y-%m-%d %H:%M:%S",
                                           time.gmtime(glbInfo['timestamp'])),
                             rsrc['type'], rsrc['host'], glbInfo['url']))
                        sList.append( sDict )
        resourceCnt = len( sList )
        del sList
    finally:
        myFile.close()
    # sanity check:
    if ( resourceCnt >= 100 ):
        os.rename(VOFD_IN_USE_FILE + "_new", VOFD_IN_USE_FILE)
    elif (resourceCnt >= 0 ):
        print("Resource count sanity check failed, %d" % resourceCnt)
    else:
        print("Failed to write metric file with grid resources in prod use")
# ########################################################################### #



if __name__ == '__main__':

    # install URL opener that connects with a certificate and key:
    # ============================================================
    url_opnr = urllib2.build_opener( HTTPSClientAuthHandler() )
    urllib2.install_opener( url_opnr )

    #import pdb; pdb.set_trace()

    vofd_init()
    vofd_sitedb()
    vofd_phedex()
    vofd_glideinWMSfactory()
    #glbTopology.write()
    vofd_write_xml()
    vofd_write_metric()
