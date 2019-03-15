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



VOFD_VERSION = "v1.02.01p"
#VOFD_OUTPUT_FILE = "vofeed.xml"
#VOFD_IN_USE_FILE = "in_use.txt"
#VOFD_CACHE_DIR = "."
VOFD_OUTPUT_FILE = "/afs/cern.ch/user/c/cmssst/www/vofeed/vofeed.xml"
VOFD_IN_USE_FILE = "/afs/cern.ch/user/c/cmssst/www/vofeed/in_use.txt"
VOFD_CACHE_DIR = "/data/cmssst/MonitoringScripts/vofeed/cache"

#VOFD_CERTIFICATE_CRT = "/lml/user/lammel/.globus/usercert.pem"
#VOFD_CERTIFICATE_KEY = "/lml/user/lammel/.globus/userkey.pem"
VOFD_CERTIFICATE_CRT = "/tmp/x509up_u79522"
VOFD_CERTIFICATE_KEY = "/tmp/x509up_u79522"
# ########################################################################### #



glbInfo = {}
glbHost2Site = {}
glbTopology = None
glbFlavours = {'CE': "CE",
               'gLite-CE': "CE",
               'ARC-CE': "CE",
               'CREAM-CE': "CE",
               'gLExec': "CE",
               'SE': "SE",
               'SRM': "SE",
               'SRMv2': "SE",
               'SRMv1': "SE",
               'globus-GRIDFTP': "SE",
               'GridFtp': "SE",
               'XROOTD': "XROOTD",
               'XRootD': "XROOTD",
               'XRootD.Redirector': "XROOTD",
               'XRootD origin server': "XROOTD",
               'XRootD component': "XROOTD",
               'perfSONAR': "perfSONAR",
               'net.perfSONAR.Bandwidth': "perfSONAR",
               'net.perfSONAR.Latency': "perfSONAR"}
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

    def addSite(self, cmssite):
        if cmssite not in self.topo:
            self.topo[cmssite] = []

    def addResource(self, cmssite, gridsite,
                    host, flavour, prod=True, queue="", batch="", endpoint=""):
        if cmssite not in self.topo:
            print("cmssite unknown, skipping %s(%s) at %s" %
                (host, flavour, cmssite))
            return
        if ( gridsite == "" ):
            if (host in glbHost2Site ) and ( flavour in glbFlavours):
                if glbFlavours[flavour] in glbHost2Site[host]:
                    gridsite = glbHost2Site[host][ glbFlavours[flavour] ]
            if ( gridsite == "" ):
                print("host not found in OSG/EGI list, %s (%s) at %s" %
                      (host, flavour, cmssite))

        if ( len(self.topo[cmssite]) == 0 ):
            self.topo[cmssite].append( {'gsite': gridsite, 'rsrcs': []} )
            index = 0
        else:
            for index in range( len(self.topo[cmssite]) ):
                if ( self.topo[cmssite][index]['gsite'] == gridsite ):
                    break
            if ( self.topo[cmssite][index]['gsite'] != gridsite ):
                self.topo[cmssite].append( {'gsite': gridsite, 'rsrcs': []} )
                index = len(self.topo[cmssite]) - 1

        for rsrc in self.topo[cmssite][index]['rsrcs']:
            if (( rsrc['host'] == host ) and ( rsrc['type'] == flavour )):
                #print("duplicate entry, skipping %s(%s) at %s" %
                #    (host, flavour, cmssite))
                return
        self.topo[cmssite][index]['rsrcs'].append( {'host': host,
            'type': flavour, 'prod': prod, 'queue': queue, 'batch': batch,
            'endpoint': endpoint} )

    def write(self, file=sys.stdout, offset=0):
        off = "".ljust(offset)
        #
        for cmssite in sorted(self.topo.keys()):
            file.write("%s%s\n" % (off, cmssite))
            for indx in range( len(self.topo[cmssite]) ):
                file.write("%s   %s\n" %
                    (off, self.topo[cmssite][indx]['gsite']))
                for rsrc in self.topo[cmssite][indx]['rsrcs']:
                    if ( rsrc['endpoint'] != "" ):
                        file.write("%s      %s (%s) prod=%r endpoint=%s\n" %
                            (off, rsrc['host'], rsrc['type'], rsrc['prod'],
                             rsrc['endpoint']))
                    elif ( rsrc['queue'] == "" ):
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



def vofd_cricsites():
    # ######################################################## #
    # fill vofdTopology object with site information from CRIC #
    # ######################################################## #
    URL_CRIC_SITES = 'https://cms-cric.cern.ch/api/core/site/query/?json'

    # get list of CMS sites from CRIC:
    # ================================
    print("Querying CRIC for site information")
    urlHandle = None
    try:
        urlHandle = urllib2.urlopen(URL_CRIC_SITES)
        myData = urlHandle.read()
        #
        # sanity check:
        if (( myData.count("T0_") < 2 ) or ( myData.count("T1_") < 10 ) or
            ( myData.count("T2_") < 64 ) or ( myData.count("T3_") < 64 )):
            raise IOError("CRIC-sites data failed sanity check")
        #
        # update cache:
        try:
            myFile = open("%s/cache_CRICsites.json_new" % VOFD_CACHE_DIR, 'w')
            try:
                myFile.write(myData)
                renameFlag = True
            except:
                renameFlag = False
            finally:
                myFile.close()
                del myFile
            if renameFlag:
                os.rename("%s/cache_CRICsites.json_new" % VOFD_CACHE_DIR,
                    "%s/cache_CRICsites.json" % VOFD_CACHE_DIR)
                print("   cache of CRIC-sites updated")
            del renameFlag
        except:
            pass
    except:
        print("   failed to fetch CRIC-sites data")
        try:
            myFile = open("%s/cache_CRICsites.json" % VOFD_CACHE_DIR, 'r')
            try:
                myData = myFile.read()
                print("   using cached CRIC-sites data")
            except:
                print("   failed to access cached CRIC-sites data")
                return
            finally:
                myFile.close()
                del myFile
        except:
            print("   no CRIC-sites cache available")
            return
    finally:
        if urlHandle is not None:
            urlHandle.close()
    del urlHandle
    #
    cric = json.loads( myData )

    # add CMS site to VO-feed topology:
    for entry in cric:
        cmssite = cric[entry]['name']
        if (( cmssite[0:1] != "T") or (not (cmssite[1:2]).isdigit()) or
            ( cmssite[2:3] != "_" ) or ( cmssite[5:6] != "_" )):
            continue
        glbTopology.addSite(cmssite)



def vofd_host2siteOSG():
    # ###########################################################
    # get topology information and fill host to site dictionary #
    # ###########################################################
    URL_OSG_RGSUM = "https://my.opensciencegrid.org/rgsummary/xml"
    global glbHost2Site

    # get resource group summary from myOSG:
    # ======================================
    print("Querying myOSG for resource group summary")
    urlHandle = None
    try:
        urlHandle = urllib2.urlopen(URL_OSG_RGSUM)
        myData = urlHandle.read()
        #
        #
        # update cache:
        try:
            myFile = open("%s/cache_myOSG.xml_new" % VOFD_CACHE_DIR, 'w')
            try:
                myFile.write(myData)
                renameFlag = True
            except:
                renameFlag = False
            finally:
                myFile.close()
                del myFile
            if renameFlag:
                os.rename("%s/cache_myOSG.xml_new" % VOFD_CACHE_DIR,
                    "%s/cache_myOSG.xml" % VOFD_CACHE_DIR)
                print("   cache of myOSG updated")
            del renameFlag
        except:
            pass
    except:
        print("   failed to fetch myOSG data")
        try:
            myFile = open("%s/cache_myOSG.xml" % VOFD_CACHE_DIR, 'r')
            try:
                myData = myFile.read()
                print("   using cached myOSG data")
            except:
                print("   failed to access cached myOSG data")
                return
            finally:
                myFile.close()
                del myFile
        except:
            print("   no myOSG cache available")
            return
    finally:
        if urlHandle is not None:
            urlHandle.close()
    del urlHandle
    #
    rgroups = ET.fromstring( myData )
    del myData
    #
    # loop over resource group elements:
    for rgroup in rgroups.findall('ResourceGroup'):
        gridsite = rgroup.find('GroupName').text
        resources = rgroup.find('Resources')
        for resource in resources.findall('Resource'):
            host = resource.find('FQDN').text
            services = resource.find('Services')
            for service in services.findall('Service'):
                flavour = service.find('Name').text
                if flavour not in glbFlavours:
                    continue
                flavor = glbFlavours[flavour]
                if host not in glbHost2Site:
                    glbHost2Site[host] = {}
                if flavor not in glbHost2Site[host]:
                    glbHost2Site[host][flavor] = gridsite
                elif ( gridsite != glbHost2Site[host][flavor] ):
                    if ( len(glbHost2Site[host][flavor]) <= len(gridsite) ):
                        print(("host %s (%s) belongs to mutiple sites, keepi" +
                               "ng %s, ignoring %s") % (host, flavor,
                               glbHost2Site[host][flavor], gridsite))
                    else:
                        print(("host %s (%s) belongs to mutiple sites, keepi" +
                               "ng %s, ignoring %s") % (host, flavor, gridsite,
                               glbHost2Site[host][flavor]))
                        glbHost2Site[host][flavor] = gridsite
# ########################################################################### #



def vofd_host2siteEGI():
    # ###########################################################
    # get topology information and fill host to site dictionary #
    # ###########################################################
    URL_EGI_RGSUM = "https://goc.egi.eu/gocdbpi/public/?method=get_service_endpoint&scope=cms"
    global glbHost2Site

    # get resource group summary from myOSG:
    # ======================================
    print("Querying GocDB for service endpoint list")
    urlHandle = None
    try:
        urlHandle = urllib2.urlopen(URL_EGI_RGSUM)
        myData = urlHandle.read()
        #
        #
        # update cache:
        try:
            myFile = open("%s/cache_GocDB.xml_new" % VOFD_CACHE_DIR, 'w')
            try:
                myFile.write(myData)
                renameFlag = True
            except:
                renameFlag = False
            finally:
                myFile.close()
                del myFile
            if renameFlag:
                os.rename("%s/cache_GocDB.xml_new" % VOFD_CACHE_DIR,
                    "%s/cache_GocDB.xml" % VOFD_CACHE_DIR)
                print("   cache of GocDB updated")
            del renameFlag
        except:
            pass
    except:
        print("   failed to fetch GocDB data")
        try:
            myFile = open("%s/cache_GocDB.xml" % VOFD_CACHE_DIR, 'r')
            try:
                myData = myFile.read()
                print("   using cached GocDB data")
            except:
                print("   failed to access cached GocDB data")
                return
            finally:
                myFile.close()
                del myFile
        except:
            print("   no GocDB cache available")
            return
    finally:
        if urlHandle is not None:
            urlHandle.close()
    del urlHandle
    #
    sendpoints = ET.fromstring( myData )
    del myData
    #
    # loop over services elements:
    for sendpoint in sendpoints.findall('SERVICE_ENDPOINT'):
        flavour = sendpoint.find('SERVICE_TYPE').text
        if flavour not in glbFlavours:
            continue
        flavor = glbFlavours[flavour]
        host = sendpoint.find('HOSTNAME').text
        if host not in glbHost2Site:
            glbHost2Site[host] = {}
        gridsite = sendpoint.find('SITENAME').text
        if flavor not in glbHost2Site[host]:
            glbHost2Site[host][flavor] = gridsite
        elif ( gridsite != glbHost2Site[host][flavor] ):
            if ( len(glbHost2Site[host][flavor]) <= len(gridsite) ):
                print(("host %s (%s) belongs to mutiple sites, keeping %s, " +
                       "ignoring %s") % (host, flavor,
                       glbHost2Site[host][flavor], gridsite))
            else:
                print(("host %s (%s) belongs to mutiple sites, keeping %s, " +
                       "ignoring %s") % (host, flavor, gridsite,
                       glbHost2Site[host][flavor]))
                glbHost2Site[host][flavor] = gridsite
# ########################################################################### #



def vofd_sitedb():
    # ########################################################## #
    # fill vofdTopology object with site information from SiteDB #
    # ########################################################## #
    URL_SITEDB_SITES = 'https://cmsweb.cern.ch:8443/sitedb/data/prod/site-names'

    # get list of CMS sites from SiteDB:
    # ==================================
    print("Querying SiteDB for site information")
    urlHandle = None
    try:
        request = urllib2.Request(URL_SITEDB_SITES,
                              headers={'Accept':'application/json'})
        urlOpener = urllib2.build_opener( HTTPSClientAuthHandler() )
        urlHandle = urlOpener.open( request )
        myData = urlHandle.read()
        #
        # sanity check:
        if (( myData.count("T0_") < 2 ) or ( myData.count("T1_") < 10 ) or
            ( myData.count("T2_") < 64 ) or ( myData.count("T3_") < 64 )):
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
    # patch to advance Purdue-Hammer grid site ahead of the SiteDB list:
    myDict['Purdue'] = {'cmssite':'T2_US_Purdue', 'gridsite':[]}
    myDict['Purdue']['gridsite'].append('Purdue-Hammer')
    for result in sitedb['result']:
        sitedbname = result[nameIndex]
        if sitedbname not in myDict:
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
    #for entry in myDict.keys():
    #    if ( myDict[entry]['cmssite'] != "" ):
    #        if ( len(myDict[entry]['gridsite']) != 0 ):
    #            for indx in range( len(myDict[entry]['gridsite']) ):
    #                glbTopology.addSite(myDict[entry]['cmssite'],
    #                                    myDict[entry]['gridsite'][indx])



    # ###################################################################### #
    # fill vofdTopology object with xrootd/perfSONAR information from SiteDB #
    # ###################################################################### #
    URL_SITEDB_XROOTD = 'https://cmsweb.cern.ch:8443/sitedb/data/prod/site-resources'

    # get list of xrootd and perfSONAR endpoints from SiteDB:
    # =======================================================
    print("Querying SiteDB for xrootd/perfSONAR information")
    urlHandle = None
    try:
        request = urllib2.Request(URL_SITEDB_XROOTD,
                              headers={'Accept':'application/json'})
        urlOpener = urllib2.build_opener( HTTPSClientAuthHandler() )
        urlHandle = urlOpener.open( request )
        myData = urlHandle.read()
        #
        # update cache:
        try:
            myFile = open("%s/cache_SiteDBxrootd.json_new" % VOFD_CACHE_DIR, 'w')
            try:
                myFile.write(myData)
                renameFlag = True
            except:
                renameFlag = False
            finally:
                myFile.close()
                del myFile
            if renameFlag:
                os.rename("%s/cache_SiteDBxrootd.json_new" % VOFD_CACHE_DIR,
                    "%s/cache_SiteDBxrootd.json" % VOFD_CACHE_DIR)
                print("   cache of SiteDB xrootd updated")
            del renameFlag
        except:
            pass
    except:
        print("   failed to fetch SiteDB xrootd data")
        try:
            myFile = open("%s/cache_SiteDBxrootd.json" % VOFD_CACHE_DIR, 'r')
            try:
                myData = myFile.read()
                print("   using cached SiteDB xrootd data")
            except:
                print("   failed to access cached SiteDB xrootd data")
                return
            finally:
                myFile.close()
                del myFile
        except:
            print("   no SiteDB xrootd cache available")
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
    fqdnIndex = columns.index('fqdn')
    prmyIndex = columns.index('is_primary')

    for result in sitedb['result']:
        sitedbname = result[nameIndex]
        if sitedbname not in myDict:
            continue
        if ( result[typeIndex] == "xrootd" ):
            endpoint = result[fqdnIndex]
            hostname, port = (endpoint.split(":",1) + ["1094"])[:2]
            hostname = hostname.lower()
            if ( result[prmyIndex][0].lower() == 'y' ):
                glbTopology.addResource(myDict[sitedbname]['cmssite'], "",
                                        hostname, "XROOTD", True, "", "",
                                        hostname + ":" + port)
            else:
                glbTopology.addResource(myDict[sitedbname]['cmssite'], "",
                                        hostname, "XROOTD", False, "", "",
                                        hostname + ":" + port)
        elif ( result[typeIndex] == "perfSONAR" ):
            endpoint = result[fqdnIndex]
            hostname = endpoint.split(":",1)[0].lower()
            if ( result[prmyIndex][0].lower() == 'y' ):
                glbTopology.addResource(myDict[sitedbname]['cmssite'], "",
                                        hostname, "perfSONAR", True)
            else:
                glbTopology.addResource(myDict[sitedbname]['cmssite'], "",
                                        hostname, "perfSONAR", False)
# ########################################################################### #



def vofd_phedex():
    # ############################################################## #
    # fill vofdTopology object with SE/SRMv2 information from PhEDEx #
    # ############################################################## #
    URL_PHEDEX_LFN2PFN = 'https://cmsweb.cern.ch:8443/phedex/datasvc/json/prod/lfn2pfn?node=T*&lfn=/store/data&lfn=/store/hidata&lfn=/store/mc&lfn=/store/himc&lfn=/store/relval&lfn=/store/hirelval&lfn=/store/user&lfn=/store/group&lfn=/store/results&lfn=/store/unmerged&lfn=/store/temp&lfn=/store/temp/user&lfn=/store/backfill/1&lfn=/store/backfill/2&lfn=/store/generator&lfn=/store/local&protocol=srmv2&custodial=n'

    # get list of LFN-to-PFN translations for all sites:
    # ==================================================
    print("Querying PhEDEx for SRMv2 LFN-to-PFN translations")
    urlHandle = None
    try:
        request = urllib2.Request(URL_PHEDEX_LFN2PFN,
                              headers={'Accept':'application/json'})
        urlHandle = urllib2.urlopen( request )
        myData = urlHandle.read()
        #
        # sanity check:
        if (( myData.count("T0_") < 24 ) or ( myData.count("T1_") < 160 ) or
            ( myData.count("T2_") < 440 ) or ( myData.count("T3_") < 250 )):
            raise IOError("PhEDEx LFN2PFN data failed sanity check")
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
                print("   cache of PhEDEx SRMv2 LFN-to-PFN data updated")
            del renameFlag
        except:
            pass
    except:
        print("   failed to fetch PhEDEx SRMv2 LFN-to-PFN translation data")
        try:
            myFile = open("%s/cache_PhEDEx.json" % VOFD_CACHE_DIR, 'r')
            try:
                myData = myFile.read()
                print("   using cached PhEDEx SRMv2 LFN-to-PFN data")
            except:
                print("   failed to access cached PhEDEx SRMv2 LFN-to-PFN data")
                return
            finally:
                myFile.close()
                del myFile
        except:
            print("   no PhEDEx SRMv2 SRMv2 LFN-to-PFN cache available")
            return
    finally:
        if urlHandle is not None:
            urlHandle.close()
    del urlHandle
    #
    # unpack JSON data of PhEDEx SRMv2 LFN-to-PFN translation:
    phedex = json.loads( myData )
    
    # PhEDEx provides a snapshot in time:
    lfn2psn = phedex['phedex']['mapping']

    for entry in lfn2psn:
        if (( entry['node'] is None ) or ( entry['pfn'] is None )):
            continue
        phedex_site = entry['node']
        phedex_pfn = entry['pfn']
        #
        phedex_prot = phedex_pfn.split("://")[0]
        if ( phedex_prot == phedex_pfn ):
            phedex_prot = "srm"
            phedex_epnt = phedex_pfn.split("/")[0]
        else:
            phedex_epnt = phedex_pfn.split("://")[1].split("/")[0]
        phedex_host = phedex_epnt.split(":")[0]
        if ( phedex_host == "" ):
            continue
        if ( phedex_epnt == phedex_host ):
            if ( phedex_prot == "gsiftp" ):
                phedex_epnt = phedex_host + ":2811"
            else:
                phedex_epnt = ""
        #
        # remove any "_Disk", "_Buffer", and "_MSS" from site names
        phedex_site = phedex_site.replace('_Disk','')
        phedex_site = phedex_site.replace('_Buffer','')
        phedex_site = phedex_site.replace('_Export','')
        phedex_site = phedex_site.replace('_MSS','')
        if ( phedex_site == "T2_KR_KNU" ):
            # site kept T2* PhEDEx nodename when switching to Tier-3
            phedex_site = "T3_KR_KNU"
        #print("SE: %s\t%s" % (phedex_site, phedex_host))
        if (( phedex_site == "T1_US_FNAL" ) and
            ( phedex_host == "cmslmon.fnal.gov" )):
            phedex_prod = False
        else:
            phedex_prod = True
        glbTopology.addResource(phedex_site, "", phedex_host, "SRM",
                                phedex_prod, "", "", phedex_epnt)
        if (( phedex_site == "T2_CH_CERN" ) and
            ( phedex_host == "eoscmsftp.cern.ch" )):
            glbTopology.addResource("T0_CH_CERN", "", phedex_host, "SRM",
                                    phedex_prod, "", "", phedex_epnt)
# ########################################################################### #



def vofd_glideinWMSfactory():
    # ###################################################################### #
    # fill vofdTopology object with CE information from glide-in WMS factory #
    # ###################################################################### #
    DICT_GLIDEIN_FACTORIES = [
       {'lbl': "UCSD",    'uri': "gfactory-1.t2.ucsd.edu",   'prd': True},
       {'lbl': "CERN",    'uri': "vocms0206.cern.ch",        'prd': True},
       {'lbl': "CERNint", 'uri': "vocms0204.cern.ch",        'prd': False},
       {'lbl': "FNAL",    'uri': "cmsgwms-factory.fnal.gov", 'prd': True} ]

    # get list of CEs used by CMS from the glide-in WMS factories:
    # ============================================================
    for factory in DICT_GLIDEIN_FACTORIES:
        #
        #print("\n\n\n\n\n\n")
        print("Querying %s factory for CE information" % factory['lbl'])
        collector = None
        try:
            collector = htcondor.Collector(factory['uri'])
            classAds = collector.query(htcondor.AdTypes.Any, "(MyType =?= \"glidefactory\") && (GLIDEIN_CMSSite isnt Undefined) && (GLIDEIN_ResourceName isnt Undefined) && (GLIDEIN_Gatekeeper isnt Undefined) && (GLIDEIN_GridType isnt Undefined) && (GLIDEIN_Supported_VOs isnt Undefined)", ['GLIDEIN_CMSSite', 'GLIDEIN_ResourceName', 'GLIDEIN_Gatekeeper', 'GLIDEIN_GridType', 'GLIDEIN_GlobusRSL', 'GLIDEIN_In_Downtime', 'GLIDEIN_Supported_VOs'])
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
                if 'GLIDEIN_In_Downtime' in classAd:
                    inDowntime = classAd['GLIDEIN_In_Downtime']
                else:
                    inDowntime = "False"
                myData.append( {
                    'GLIDEIN_ResourceName': classAd['GLIDEIN_ResourceName'],
                    'GLIDEIN_GridType': classAd['GLIDEIN_GridType'],
                    'GLIDEIN_Gatekeeper': classAd['GLIDEIN_Gatekeeper'],
                    'GLIDEIN_GlobusRSL': globusRSL,
                    'GLIDEIN_In_Downtime': inDowntime,
                    'GLIDEIN_Supported_VOs': classAd['GLIDEIN_Supported_VOs'],
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
            if ( classAd['GLIDEIN_In_Downtime'] == "True" ):
                # exclude entries set to indefinite downtime by factory team
                continue
            if 'CMS' not in classAd['GLIDEIN_Supported_VOs']:
                continue
            gridsite = classAd['GLIDEIN_ResourceName']
            gkeeper = classAd['GLIDEIN_Gatekeeper'].split()[-1]
            host = gkeeper.split(":")[0]
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
            endpoint = gkeeper.split("/")[0]
            if ( endpoint == host ):
                endpoint = ""
            queue = ""
            if ( gkeeper.find("/") <= 0 ):
                batch = ""
            else:
                batch = gkeeper.split("/")[1]
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
            #-LML DESY SL 6 patch, start !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
            #glbTopology.addResource(classAd['GLIDEIN_CMSSite'], gridsite,
            #    host, ceType, factory['prd'], queue, batch, endpoint)
            # !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
            if ((( host != "grid-arcce0.desy.de" ) and
                 ( host != "grid-arcce1.desy.de" )) or
                (( queue != "grid" ) and ( queue != "gridsl6" ))):
                #-LML T1_FR_CCIN2P3 HTCondor-CE patch, start !!!!!!!!!!!!!!!!!!
                if (( host == "cccondorce01.in2p3.fr" ) or
                    ( host == "cccondorce02.in2p3.fr" )):
                    glbTopology.addResource(classAd['GLIDEIN_CMSSite'],
                        gridsite, host, ceType, False, queue, batch, endpoint)
                else:
                    #-LML T[12]_FR_CCIN2P3 HTCondor-CE patch, end !!!!!!!!!!!!!
                    glbTopology.addResource(classAd['GLIDEIN_CMSSite'], gridsite,
                        host, ceType, factory['prd'], queue, batch, endpoint)
            #-LML DESY SL 6 patch, end !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
            if (( classAd['GLIDEIN_CMSSite'] == "T2_CH_CERN" ) and
                ( factory['prd'] == True )):
                glbTopology.addResource("T0_CH_CERN", gridsite,
                    host, ceType, True, queue, batch, endpoint)
            if ( classAd['GLIDEIN_CMSSite'] == "T2_CH_CERN" ):
                glbTopology.addResource("T3_CH_CERN_CAF", gridsite,
                    host, ceType, factory['prd'], queue, batch, endpoint)
# ########################################################################### #



def vofd_write_xml():
    # ################################################################# #
    # write VO-feed XML based on information in the vofdTopology object #
    # ################################################################# #
    FIRST_PASS_SITES = [
       {'cmssite': "T0_CH_CERN", 'gridsite': "CERN-PROD"},
       {'cmssite': "T2_CH_CSCS", 'gridsite': "CSCS-LCG2"},
       {'cmssite': "T2_US_Purdue", 'gridsite': "Purdue-Hammer"},
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
        myFile.write("   <version>%s</version>\n" % VOFD_VERSION)
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
                        if ( rsrc['endpoint'] != "" ):
                            myFile.write(" endpoint=\"%s\"" % rsrc['endpoint'])
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
                    if ( rsrc['endpoint'] != "" ):
                        myFile.write(" endpoint=\"%s\"" % rsrc['endpoint'])
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
            ( tierCnt['2'] >= 32 ) and ( tierCnt['3'] >= 32 )):
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

    #import pdb; pdb.set_trace()

    vofd_init()
    vofd_cricsites()
    vofd_host2siteOSG()
    vofd_host2siteEGI()
    vofd_sitedb()
    vofd_phedex()
    vofd_glideinWMSfactory()
    #glbTopology.write()
    vofd_write_xml()
    vofd_write_metric()
