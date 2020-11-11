#!/eos/user/c/cmssst/packages/bin/python3.7
# ########################################################################### #
# python CGI script to display the override status of sites and allow to set  #
#    a manual override for LifeStatus, ProdStatus, or CrabStatus. The script  #
#    acquires a lock, read the appropriate override file, and displays the    #
#    override status based on SSO permissions. In case of a POST, information #
#    and permissions are checked and the corresponding override file updated. #
#                                                                             #
# 2019-Dec-17   Stephan Lammel                                                #
# ########################################################################### #
#
# PATH_INFO = /LifeStatus/T9_US_Fermilab
# REQUEST_METHOD = POST
# CONTENT_LENGTH = 16
# 
# ADFS_LOGIN = jonny
# ADFS_FULLNAME = John Doe
# ADFS_GROUP = cms-comp-ops-site-support-team;cms-zh;cms-members;cms-web-access;cms-authorized-users;cms-US_Fermilab-admin;
#
# /eos/user/c/cmssst/www/override/CrabStatus.json:
# [
#   { "name": "T9_US_Fermilab",
#     "status": "enabled",
#     "mode": "latched",
#     "when": "2016-Jul-14 17:20:22",
#     "who": "jonny",
#     "why": "Because i like it"
#   },
#   { ... }
# ]
#
#
#
import os, sys
import stat
import io
import fcntl
import time, calendar
import json
import re
import urllib.request, urllib.parse
import argparse
import logging
# ########################################################################### #



OVRD_AUTH_EGROUP = {
    'LifeStatus':   { 'cms-zh':                         "",
                      'cms-members':                    "",
                      'cms-authorized-users':           "",
                      'cms-comp-ops':                   "",
                      'cms-comp-ops-site-support-team': "ALL" },
    'ProdStatus':   { 'cms-zh':                         "",
                      'cms-members':                    "",
                      'cms-authorized-users':           "",
                      'cms-comp-ops':                   "",
                      'cms-comp-ops-workflow-team':     "ALL",
                      'cms-tier0-operations':           ["T0_CH_CERN",
                                                         "T2_CH_CERN",
                                                         "T2_CH_CERN_HLT" ],
                    'cms-comp-ops-site-support-team': "ALL" },
    'CrabStatus':   { 'cms-zh':                         "",
                      'cms-members':                    "",
                      'cms-authorized-users':           "",
                      'cms-comp-ops':                   "",
                      'cms-service-crab3htcondor':      "ALL",
                      'cms-tier0-operations':           ["T0_CH_CERN",
                                                         "T2_CH_CERN_HLT" ],
                      'cms-comp-ops-site-support-team': "ALL" },
    'SiteCapacity': { 'cms-zh':                         "",
                      'cms-members':                    "",
                      'cms-authorized-users':           "",
                      'cms-comp-ops':                   "",
                      'cms-comp-ops-site-support-team': "ALL" }
}
OVRD_STATUS_DESC = {
    'LifeStatus': { 'enabled':      "Enabled",
                    'waiting_room': "Waiting Room",
                    'morgue':       "Morgue state" },
    'ProdStatus': { 'enabled':      "Enabled",
                    'drain':        "Drain",
                    'disabled':     "Disabled",
                    'test':         "Testing" },
    'CrabStatus': { 'enabled':      "Enabled",
                    'disabled':     "Disabled" }
}
OVRD_MODE_DESC = {
    'LifeStatus': [ "latched", "oneday", "toggle" ],
    'ProdStatus': [ "latched", "oneday", "toggle" ],
    'CrabStatus': [ "latched", "oneday", "toggle" ]
}
OVRD_CAPACITY_DESC = {
    'name':                     "CMS Site Name",
    'wlcg_federation_name':     "Name of the WLCG federation containing th" + \
                                "e site pledge",
    'wlcg_federation_fraction': "Fraction of WLCG federation pledge fulfil" + \
                                "led by site",
    'hs06_pledge':              "CPU pledge in HS06 (auto-calculated from " + \
                                "Rebus and core performance)",
    'hs06_per_core':            "Average HS06 performance of a core at the" + \
                                " site",
    'core_usable':              "Number of cores usable by CMS",
    'core_max_used':            "Max number of cores used recently by CMS " + \
                                "(auto-filled from gWMSmon)",
    'core_production':          "Number of cores for production (auto-set " + \
                                "to 80% or 50% of usable cores)",
    'core_cpu_intensive':       "Max number of cores to be used for CPU in" + \
                                "tensive jobs",
    'core_io_intensive':        "Max number of cores to be used for I/O in" + \
                                "tensive jobs",
    'disk_pledge':              "Disk space pledge in TBytes (auto-filled " + \
                                "from Rebus)",
    'disk_usable':              "Disk space in TBytes usable by CMS",
    'disk_experiment_use':      "Disk space in TBytes available for experi" + \
                                "ment use (auto-filled from DDM)",
    'tape_pledge':              "Tape space pledge in TBytes (auto-filled " + \
                                "from Rebus)",
    'tape_usable':              "Tape space in TBytes usable by CMS",
    'when':                     "Date of last non-automatic update",
    'who':                      "Username of last non-automatic update"
}
OVRD_LOCK_PATH = {
    'LifeStatus':   "/eos/user/c/cmssst/www/override/status.lock",
    'ProdStatus':   "/eos/user/c/cmssst/www/override/status.lock",
    'CrabStatus':   "/eos/user/c/cmssst/www/override/status.lock",
    'SiteCapacity': "/eos/user/c/cmssst/www/capacity/update.lock"
}
OVRD_FILE_PATH = {
    'LifeStatus':   "/eos/user/c/cmssst/www/override/LifeStatus.json",
    'ProdStatus':   "/eos/user/c/cmssst/www/override/ProdStatus.json",
    'CrabStatus':   "/eos/user/c/cmssst/www/override/CrabStatus.json",
    'SiteCapacity': "/eos/user/c/cmssst/www/capacity/SiteCapacity.json"
}
OVRD_CGIURL = "https://test-cmssst.web.cern.ch/cgi-bin/set"
#
OVRD_CACHE = "/eos/user/c/cmssst/www/cache"
# ########################################################################### #



def ovrd_cric_facility():
    # ##################################################### #
    # return dictionary with valid CMS-sites: facility-name #
    # ##################################################### #
    URL_CRIC_SITES = "https://cms-cric.cern.ch/api/cms/site/query/?json"
    #
    siteRegex = re.compile(r"T\d_[A-Z]{2,2}_\w+")
    facilityRegex = re.compile(r"[A-Z]{2,2}_\w+")

    logging.info("Fetching CMS site information from CRIC")
    try:
        with urllib.request.urlopen(URL_CRIC_SITES) as urlHandle:
            urlCharset = urlHandle.headers.get_content_charset()
            if urlCharset is None:
                urlCharset = "utf-8"
            myData = urlHandle.read().decode( urlCharset )
        #
        # sanity check:
        if ( len(myData) < 65536 ):
            raise ValueError("CRIC site query result failed sanity check")
        #
        # decode JSON:
        myDict = json.loads( myData )
        del myData
        #
        # loop over entries and add site with facility name:
        siteDict = {}
        for myKey in myDict:
            site = myDict[myKey]['name']
            if ( siteRegex.match( site ) is None ):
                continue
            try:
                facility = myDict[myKey]['facility'].split(" ")[0]
                if ( facilityRegex.match( facility ) is None ):
                    continue
            except KeyError:
                continue
            #
            if (( site[-5:] == "_Disk" ) or ( site[-7:] == "_Buffer" ) or
                ( site[-7:] == "_Export" ) or ( site[-4:] == "_MSS" )):
                continue
            #
            siteDict[ site ] = facility
        #
        #
        # update cache:
        cacheFile = OVRD_CACHE + "/cric_site2facility.json"
        cacheUpdate = False
        try:
             myAge = time.time() - os.stat(cacheFile)[stat.ST_MTIME]
             if ( myAge > 86400 ):
                 cacheUpdate = True
        except FileNotFoundError:
             cacheUpdate = True
        #
        if ( cacheUpdate ):
            jsonString = "["
            commaFlag = False
            for site in siteDict:
                if commaFlag:
                    jsonString += ",\n"
                else:
                    jsonString += "\n"
                jsonString += "   \"%s\": \"%s\"" % ( site, siteDict[site] )
                commaFlag = True
            jsonString += "\n]\n"
            #
            try:
                with open(cacheFile + "_new", 'w') as myFile:
                    myFile.write( jsonString )
                os.rename(cacheFile + "_new", cacheFile)
            except:
                pass
            #
            logging.log(25, "Site-to-Facility dictionary cache updated")
    except Exception as excptn:
        logging.error("Failed to fetch CMS site information from CRIC: %s" %
                                                                   str(excptn))
        #
        cacheFile = OVRD_CACHE + "/cric_site2facility.json"
        try:
            with open(cacheFile, 'rt') as myFile:
                myData = myFile.read()
            #
            # decode JSON:
            siteDict = json.loads( myData )
            del myData
        except:
            logging.critical("Failed to read Site-to-Facility dictionary cache")
            raise
        #
    return siteDict
# ########################################################################### #



def ovrd_cric_federation():
    # ########################################## #
    # return list of valid WLCG federation names #
    # ########################################## #
    URL_CRIC_FEDRN = "https://wlcg-cric.cern.ch/api/core/federation/query/?json"

    logging.info("Fetching WLCG federation information from CRIC")
    try:
        with urllib.request.urlopen(URL_CRIC_FEDRN) as urlHandle:
            urlCharset = urlHandle.headers.get_content_charset()
            if urlCharset is None:
                urlCharset = "utf-8"
            myData = urlHandle.read().decode( urlCharset )
        #
        # sanity check:
        if ( len(myData) < 16384 ):
            raise ValueError("WLCG federation query result failed sanity check")
        #
        # decode JSON:
        myDict = json.loads( myData )
        del myData
        #
        # loop over entries and add WLCG federation name to list:
        federationList = set()
        for myEntry in myDict:
            federation = None
            support = None
            try:
                federation = myDict[ myEntry ]['name']
                for voName in myDict[ myEntry ]['vos']:
                    if ( voName[:3].lower() == "cms" ):
                        support = "cms"
                        break
                if (( federation is None ) or ( federation == "" ) or
                    ( support is None )):
                    continue
            except KeyError:
                continue
            #
            federationList.add( federation )
        del myDict
        federationList = sorted( federationList )
        #
        #
        # update cache:
        cacheFile = OVRD_CACHE + "/cric_federation.json"
        cacheUpdate = False
        try:
             myAge = time.time() - os.stat(cacheFile)[stat.ST_MTIME]
             if ( myAge > 86400 ):
                 cacheUpdate = True
        except FileNotFoundError:
             cacheUpdate = True
        #
        if ( cacheUpdate ):
            jsonString = "{\n   \"Federations\": ["
            commaFlag = False
            for federation in federationList:
                if commaFlag:
                    jsonString += ", "
                else:
                    jsonString += " "
                jsonString += "\"%s\"" % federation
                commaFlag = True
            jsonString += " ]\n}\n"
            #
            try:
                with open(cacheFile + "_new", 'w') as myFile:
                    myFile.write( jsonString )
                os.rename(cacheFile + "_new", cacheFile)
            except:
                pass
            #
            logging.log(25, "WLCG federation information cache updated")
    except Exception as excptn:
        logging.error("Failed to fetch WLCG federation info from CRIC: %s" %
                                                                   str(excptn))
        #
        cacheFile = OVRD_CACHE + "/cric_federation.json"
        try:
            with open(cacheFile, 'rt') as myFile:
                myData = myFile.read()
            #
            # decode JSON:
            federationDict = json.loads( myData )
            del myData
            #
            federationList = set()
            for federation in federationDict['Federations']:
                federationList.add( federation )
            federationList = sorted( federationList )
        except:
            logging.critical("Failed to read WLCG federation information cache")
            raise
        #
    return federationList
# ########################################################################### #



def ovrd_read_jsonfile(cgiMTRC):
    """read override file and return contents as dictionary of dictionaries"""
    # ####################################################################### #

    if (( cgiMTRC not in OVRD_LOCK_PATH ) or ( cgiMTRC not in OVRD_FILE_PATH )):
        raise ValueError("Unsupported metric \"%s\"" % cgiMTRC)
    filename = OVRD_FILE_PATH[cgiMTRC]
    lockname = OVRD_LOCK_PATH[cgiMTRC]

    logging.info("Fetching %s information, %s" %
                                         (cgiMTRC, os.path.basename(filename)))
    # acquire lock and read override file:
    remainWait = 3.0
    while ( remainWait > 0.0 ):
        with open(lockname, 'w') as lckFile:
            try:
                fcntl.lockf(lckFile, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError:
                logging.log(25, "Lock busy, retry in 250 msec")
                time.sleep(0.250)
                remainWait -= 0.250
                continue
            #
            with open(filename, 'rt') as myFile:
                jsonString = myFile.read()
            #
            fcntl.lockf(lckFile, fcntl.LOCK_UN)
            break
    if ( remainWait <= 0.0 ):
        raise TimeoutError("Failed to acquire lock %s" % lckFile)
    #
    # decode JSON:
    overrideList = json.loads( jsonString )
    del jsonString
    #
    # convert list of dictionaries to dictionary of dictionaries:
    overrideDict = {}
    for entry in overrideList:
        if cgiMTRC in OVRD_STATUS_DESC:
            if (( 'name' not in entry ) or ( 'status' not in entry ) or
                ( 'mode' not in entry )):
                logging.error("Missing key(s) in override entry %s of %s" %
                                                        (str(entry), filename))
                continue
            if 'when' not in entry:
                entry['when'] = ""
            if 'who' not in entry:
                entry['who'] = ""
            if 'why' not in entry:
                entry['why'] = ""
        else:
            if ( 'name' not in entry ):
                logging.error("Missing key(s) in capacity entry %s of %s" %
                                                        (str(entry), filename))
                continue
            if 'wlcg_federation_name' not in entry:
                entry['wlcg_federation_name'] = None
            if 'wlcg_federation_fraction' not in entry:
                entry['wlcg_federation_fraction'] = 1.000
            if 'hs06_pledge' not in entry:
                entry['hs06_pledge'] = 0
            if 'hs06_per_core' not in entry:
                entry['hs06_per_core'] = 10.000
            if 'core_usable' not in entry:
                entry['core_usable'] = 0
            if 'core_max_used' not in entry:
                entry['core_max_used'] = 0
            if 'core_production' not in entry:
                entry['core_production'] = 0
            if 'core_cpu_intensive' not in entry:
                entry['core_cpu_intensive'] = 0
            if 'core_io_intensive' not in entry:
                entry['core_io_intensive'] = 0
            if 'disk_pledge' not in entry:
                entry['disk_pledge'] = 0.0
            if 'disk_usable' not in entry:
                entry['disk_usable'] = 0.0
            if 'disk_experiment_use' not in entry:
                entry['disk_experiment_use'] = 0.0
            if 'tape_pledge' not in entry:
                entry['tape_pledge'] = 0.0
            if 'tape_usable' not in entry:
                entry['tape_usable'] = 0.0
            if 'when' not in entry:
                entry['when'] = "never"
            if 'who' not in entry:
                entry['who'] = "anybody"
        overrideDict[ entry['name'] ] = entry
    del overrideList

    return overrideDict
# ########################################################################### #



def ovrd_compose_override(overrideList):
    """compose JSON string from list of overrides"""
    # ####################################################################### #
    jsonString = "["
    commaFlag = False
    #
    for entry in sorted( overrideList, key=lambda e: e['name'] ):
        if commaFlag:
            jsonString += ",\n {\n"
        else:
            jsonString += "\n {\n"
        jsonString += (("   \"name\": \"%s\",\n" +
                        "   \"status\": \"%s\",\n" +
                        "   \"mode\": \"%s\",\n") %
                       (entry['name'], entry['status'], entry['mode']))
        if entry['when'] is not None:
            jsonString += ("   \"when\": \"%s\",\n" % entry['when'])
        else:
            jsonString += ("   \"when\": null,\n")
        if entry['who'] is not None:
            jsonString += ("   \"who\": \"%s\",\n" % entry['who'])
        else:
            jsonString += ("   \"who\": null,\n")
        if entry['why'] is not None:
            jsonString += ("   \"why\": \"%s\"\n }" % entry['why'])
        else:
            jsonString += ("   \"why\": null\n }")
        commaFlag = True
    jsonString += "\n]\n"
    #
    return jsonString
# ########################################################################### #



def ovrd_compose_capacity(capacityList):
    """compose JSON string from list of capacities"""
    # ####################################################################### #
    jsonString = "["
    commaFlag = False
    #
    for entry in sorted( capacityList, key=lambda e: e['name'] ):
        if commaFlag:
            jsonString += ",\n {\n"
        else:
            jsonString += "\n {\n"
        jsonString += ("   \"name\": \"%s\",\n" % entry['name'])
        if (( 'wlcg_federation_name' in entry ) and
            ( entry['wlcg_federation_name'] is not None )):
            jsonString += ("   \"wlcg_federation_name\": \"%s\",\n" %
                                                 entry['wlcg_federation_name'])
        else:
            jsonString += ("   \"wlcg_federation_name\": null,\n")
        if (( 'wlcg_federation_fraction' in entry ) and
            ( entry['wlcg_federation_fraction'] is not None )):
            jsonString += ("   \"wlcg_federation_fraction\": %.3f,\n" %
                                             entry['wlcg_federation_fraction'])
        else:
            jsonString += ("   \"wlcg_federation_fraction\": 1.000,\n")
        if (( 'hs06_pledge' in entry ) and
            ( entry['hs06_pledge'] is not None )):
            jsonString += ("   \"hs06_pledge\": %d,\n" % entry['hs06_pledge'])
        else:
            jsonString += ("   \"hs06_pledge\": 0,\n")
        if (( 'hs06_per_core' in entry ) and
            ( entry['hs06_per_core'] is not None )):
            jsonString += ("   \"hs06_per_core\": %.3f,\n" %
                                                        entry['hs06_per_core'])
        else:
           jsonString += ("   \"hs06_per_core\": 10.000,\n")
        for cpctyKey in ['core_usable', 'core_max_used', 'core_production', \
                         'core_cpu_intensive', 'core_io_intensive' ]:
            if (( cpctyKey in entry ) and ( entry[cpctyKey] is not None )):
                jsonString += ("   \"%s\": %d,\n" % (cpctyKey, entry[cpctyKey]))
            else:
                jsonString += ("   \"%s\": 0,\n" % cpctyKey)
        for cpctyKey in ['disk_pledge', 'disk_usable', 'disk_experiment_use', \
                         'tape_pledge', 'tape_usable' ]:
            if (( cpctyKey in entry ) and ( entry[cpctyKey] is not None )):
                jsonString += ("   \"%s\": %.1f,\n" %
                                                   (cpctyKey, entry[cpctyKey]))
            else:
                jsonString += ("   \"%s\": 0.0,\n" % cpctyKey)
        
        if (( 'when' in entry ) and ( entry['when'] is not None )):
            jsonString += ("   \"when\": \"%s\",\n" % entry['when'])
        else:
            jsonString += ("   \"when\": null,\n")
        if (( 'who' in entry ) and ( entry['who'] is not None )):
            jsonString += ("   \"who\": \"%s\"\n }" % entry['who'])
        else:
            jsonString += ("   \"who\": null\n }")
        commaFlag = True
    jsonString += "\n]\n"
    #
    return jsonString
# ########################################################################### #



def ovrd_update_jsonfile(cgiMTRC, entry):
    """update the override file with a site entry"""
    # ##################################################################### #
    # name, status, and mode are mandatory keys in the dictionary entry. If #
    # status is set to None the existing entry of the site in the file will #
    # be removed.                                                           #
    # ##################################################################### #
    siteRegex = re.compile(r"T\d_[A-Z]{2,2}_\w+")

    if (( cgiMTRC not in OVRD_LOCK_PATH ) or ( cgiMTRC not in OVRD_FILE_PATH )):
        logging.error("Unsupported metric \"%s\"" % cgiMTRC)
        return
    filename = OVRD_FILE_PATH[cgiMTRC]
    lockname = OVRD_LOCK_PATH[cgiMTRC]
    #
    if cgiMTRC in OVRD_STATUS_DESC:
        if (( 'name' not in entry ) or ( 'status' not in entry ) or
            ( 'mode' not in entry )):
            logging.error("Missing key(s) in override entry %s of %s" %
                                                        (str(entry), filename))
            return
    else:
        if ( 'name' not in entry ):
            logging.error("Missing key(s) in capacity entry %s of %s" %
                                                        (str(entry), filename))
            return
    if ( siteRegex.match( entry['name'] ) is None ):
        logging.error("Illegal site name %s" % entry['name'])
        return
    site = entry['name']

    logging.info("Updating %s information, %s" %
                                         (cgiMTRC, os.path.basename(filename)))
    # acquire lock and read override file:
    remainWait = 5.0
    while ( remainWait > 0.0 ):
        with open(lockname, 'w') as lckFile:
            try:
                fcntl.lockf(lckFile, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError:
                logging.log(25, "Lock busy, retry in 250 msec")
                time.sleep(0.250)
                remainWait -= 0.250
                continue
            #
            #
            try:
                with open(filename, 'r+t') as myFile:
                    #
                    jsonString = myFile.read()
                    #
                    overrideList = json.loads( jsonString )
                    #
                    overrideList = [ e for e in overrideList \
                                                     if ( e['name'] != site ) ]
                    if cgiMTRC in OVRD_STATUS_DESC:
                        if entry['status'] is not None:
                            overrideList.append(entry)
                        #
                        jsonString = ovrd_compose_override(overrideList)
                    else:
                        overrideList.append(entry)
                        #
                        jsonString = ovrd_compose_capacity(overrideList)
                    #
                    myFile.seek(0)
                    myFile.write(jsonString)
                    myFile.truncate()
                    #
                logging.info("Successfully updated %s file %s" %
                                                           (cgiMTRC, filename))
            except Exception as excptn:
                logging.error("Failed to update %s file %s, %s" %
                                              (cgiMTRC, filename, str(excptn)))
                return
            #
            fcntl.lockf(lckFile, fcntl.LOCK_UN)
            break
    if ( remainWait <= 0.0 ):
        logging.error("Timeout acquiring lock %s" % lckFile)

    return
# ########################################################################### #



def ovrd_append_log(cgiMTRC, entry):
    """append entry to the override log file"""
    # ##################################################################### #
    siteRegex = re.compile(r"T\d_[A-Z]{2,2}_\w+")

    if cgiMTRC not in OVRD_FILE_PATH:
        logging.error("Unsupported metric \"%s\"" % cgiMTRC)
        return
    if ( OVRD_FILE_PATH[cgiMTRC][-5:] != ".json" ):
        logging.critical("Bad OVRD_FILE_PATH[\"%s\"] configuration" % cgiMTRC)
        return
    filename = OVRD_FILE_PATH[cgiMTRC][:-4] + "log"
    #
    if cgiMTRC in OVRD_STATUS_DESC:
        if (( 'name' not in entry ) or ( 'status' not in entry ) or
            ( 'mode' not in entry )):
            logging.error("Missing key(s) in override entry %s of %s" %
                                                        (str(entry), filename))
            return
    else:
        if ( 'name' not in entry ):
            logging.error("Missing key(s) in capacity entry %s of %s" %
                                                        (str(entry), filename))
            return
    if ( siteRegex.match( entry['name'] ) is None ):
        logging.error("Illegal site name %s" % entry['name'])
        return
    site = entry['name']
    if cgiMTRC in OVRD_STATUS_DESC:
        if (( entry['status'] is None ) or ( entry['status'] == "" )):
            status = "auto"
            mode = "none"
        else:
            status = entry['status']
            mode = entry['mode']
    else:
        if entry['wlcg_federation_name'] is None:
            federation = "none"
            fraction = "n/a"
        else:
            federation = entry['wlcg_federation_name'].replace(":", "")
            fraction = "%.3f" % entry['wlcg_federation_fraction']

    logging.info("Logging update of %s information, %s" %
                                         (cgiMTRC, os.path.basename(filename)))

    try:
        with open(filename, 'at') as myFile:
            #
            if cgiMTRC in OVRD_STATUS_DESC:
                logString = "%s\t%s\t%s\t%s\t%s\t%s\n" % (site, status, mode,
                                     entry['when'], entry['who'], entry['why'])
            else:
                logString = (("%s\t%s:%s:%d:%.3f:%d:%d:%d:%d:%d:%.1f:%.1f:" +
                              "%.1f:%.1f:%.1f\t%s\t%s\n") %
                             (site, federation, fraction, entry['hs06_pledge'],
                              entry['hs06_per_core'], entry['core_usable'],
                              entry['core_max_used'], entry['core_production'],
                              entry['core_cpu_intensive'],
                              entry['core_io_intensive'], entry['disk_pledge'],
                              entry['disk_usable'],
                              entry['disk_experiment_use'],
                              entry['tape_pledge'], entry['tape_usable'],
                              entry['when'], entry['who']))
            #
            myFile.write(logString)
            #
        logging.info("Successfully appended entry to log file %s" %
                                                                      filename)
    except Exception as excptn:
        logging.error("Failed to update override file %s, %s" %
                                                       (filename, str(excptn)))

    return
# ########################################################################### #



def ovrd_auth_cern_sso():
    # ####################################################################### #
    # function to get CGI access information at CERN                          #
    #          returns a dictionary {'username':, 'fullname':, 'egroups': }   #
    # ####################################################################### #
    #
    authDict = {'username': "unknown", 'fullname': "Not Known", 'egroups': []}


    # ADFS (old SSO) e-group list:
    try:
        myUser = os.environ['ADFS_LOGIN']
        authDict['username'] = myUser
        #
        myName = os.environ['ADFS_FULLNAME']
        authDict['fullname'] = myName
        #
        myGroup = os.environ['ADFS_GROUP']
        authDict['egroups'] = [e for e in myGroup.split(";") if ( e != "" ) ]
        #
        logging.info("CGI access by: %s / \"%s\" member of %s" %
                                   (authDict['username'], authDict['fullname'],
                                                     str(authDict['egroups'])))
        return authDict
    except KeyError:
        try:
            myUser = os.environ['OIDC_CLAIM_sub']
            authDict['username'] = myUser
            #
            myName = os.environ['OIDC_CLAIM_name']
            authDict['fullname'] = myName
        except KeyError:
            try:
                myUser = os.environ['REMOTE_USER']
                authDict['username'] = myUser.split("@")[0]
                #
                authDict['fullname'] = " ".join(myUser.split("@")[0:2])
            except KeyError:
                logging.error("Failed to identify username of executing CGI")
                #
                logging.info("CGI access by: %s / \"%s\" member of %s" %
                                   (authDict['username'], authDict['fullname'],
                                                     str(authDict['egroups'])))
                return authDict


    # OIDC (new SSO) e-group list:
    #
    # acquire API access token:
    OVRD_AT_URL = "https://auth.cern.ch/auth/realms/cern/api-access/token"
    OVRD_AT_HDR = {'Content-Type': "application/x-www-form-urlencoded"}
    OVRD_AT_DATA = {'grant_type': "client_credentials",
                    'client_id': "cmssst_cgi",
                    'client_secret': "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx",
                    'audience': "authorization-service-api"}
    try:
        requestObj = urllib.request.Request(OVRD_AT_URL,
                         data=urllib.parse.urlencode(OVRD_AT_DATA).encode(),
                         headers=OVRD_AT_HDR, method="POST")
        with urllib.request.urlopen( requestObj, timeout=90 ) as urlHndl:
            myCharset = urlHndl.headers.get_content_charset()
            if myCharset is None:
                myCharset = "utf-8"
            myData = urlHndl.read().decode( myCharset )
            del(myCharset)
    except urllib.error.URLError as excptn:
        logging.error(("Failed to access CERN Authorization Service access t" +
                       "oken API URL, %s") % str(excptn))
        #
        logging.info("CGI access by: %s / \"%s\" member of %s" %
                                   (authDict['username'], authDict['fullname'],
                                                     str(authDict['egroups'])))
        return authDict
    try:
        apiToken = json.loads( myData )['access_token']
    except (json.JSONDecodeError, KeyError) as excptn:
        logging.error("Failed to decode access token, %s" % str(excptn))
        #
        logging.info("CGI access by: %s / \"%s\" member of %s" %
                                   (authDict['username'], authDict['fullname'],
                                                     str(authDict['egroups'])))
        return authDict
    #
    # get user id:
    OVRD_ID_URL = "https://authorization-service-api.web.cern.ch/api/v1.0/Identity"
    OVRD_ID_QRY = {'filter': "upn:" + myUser}
    OVRD_ID_HDR = {'Accept': "application/json",
                   'Authorization': "Bearer " + apiToken}
    try:
        getURL = OVRD_ID_URL + "?" + urllib.parse.urlencode(OVRD_ID_QRY)
        requestObj = urllib.request.Request(getURL,
                         headers=OVRD_ID_HDR, method="GET")
        with urllib.request.urlopen( requestObj, timeout=90 ) as urlHndl:
            myCharset = urlHndl.headers.get_content_charset()
            if myCharset is None:
                myCharset = "utf-8"
            myData = urlHndl.read().decode( myCharset )
            del(myCharset)
    except urllib.error.URLError as excptn:
        logging.error(("Failed to access CERN Authorization Service identity" +
                       " API URL, %s") % str(excptn))
        #
        logging.info("CGI access by: %s / \"%s\" member of %s" %
                                   (authDict['username'], authDict['fullname'],
                                                     str(authDict['egroups'])))
        return authDict
    try:
        userId = json.loads( myData )['data'][0]['id']
    except (json.JSONDecodeError, KeyError, IndexError) as excptn:
        logging.error("Failed to decode user identity, %s" % str(excptn))
        #
        logging.info("CGI access by: %s / \"%s\" member of %s" %
                                   (authDict['username'], authDict['fullname'],
                                                     str(authDict['egroups'])))
        return authDict
    #
    # get user groups:
    OVRD_GRP_URL = "https://authorization-service-api.web.cern.ch/api/v1.0/Identity/" + userId + "/groups"
    OVRD_GRP_QRY = {'recursive': "false" }
    OVRD_GRP_HDR = {'Accept': "application/json",
                   'Authorization': "Bearer " + apiToken}
    try:
        getURL = OVRD_GRP_URL + "?" + urllib.parse.urlencode(OVRD_GRP_QRY)
        requestObj = urllib.request.Request(getURL,
                         headers=OVRD_GRP_HDR, method="GET")
        with urllib.request.urlopen( requestObj, timeout=90 ) as urlHndl:
            myCharset = urlHndl.headers.get_content_charset()
            if myCharset is None:
                myCharset = "utf-8"
            myData = urlHndl.read().decode( myCharset )
            del(myCharset)
    except urllib.error.URLError as excptn:
        logging.error(("Failed to access CERN Authorization Service groups A" +
                       "PI URL, %s") % str(excptn))
        #
        logging.info("CGI access by: %s / \"%s\" member of %s" %
                                   (authDict['username'], authDict['fullname'],
                                                     str(authDict['egroups'])))
        return authDict
    try:
        authDict['egroups'] = [ e['groupIdentifier'] for e in \
                                                 json.loads( myData )['data'] ]
    except (json.JSONDecodeError, KeyError, IndexError) as excptn:
        logging.error("Failed to decode e-group list, %s" % str(excptn))
        #
        logging.info("CGI access by: %s / \"%s\" member of %s" %
                                   (authDict['username'], authDict['fullname'],
                                                     str(authDict['egroups'])))
        return authDict


    logging.info("CGI access by: %s / \"%s\" member of %s" %
        (authDict['username'], authDict['fullname'], str(authDict['egroups'])))
    return authDict
# ########################################################################### #



def ovrd_html_header(cgiMTHD, cgiMTRC, cgiSITE):
    """write head of HTML page to stdout"""
    # ####################################################################### #
    OVRD_TITLES = {
        'LifeStatus':  "Life Status Manual Override",
        'ProdStatus':  "Production Status Manual Override",
        'CrabStatus':  "Analysis Status Manual Override",
        'SiteCapacity': "Site Capacity Update"
    }

    if cgiMTRC not in OVRD_TITLES:
        myTitle = "Unknown Manual Override"
    elif (( cgiMTHD == "POST" ) and ( cgiSITE is not None )):
        myTitle = OVRD_TITLES[ cgiMTRC ] + " " + cgiSITE
    else:
        myTitle = OVRD_TITLES[ cgiMTRC ]
    #
    #
    print("Content-type: text/html\n\n")
    print(("<HTML lang=en>\n<HEAD>\n   <META charset=\"UTF-8\">\n   <TITLE>" +
           "%s</TITLE>\n   <STYLE TYPE=\"text/css\">\n  " +           "    " +
           "BODY {\n         background-color: white\n      }\n      TD A, " +
           "TD A:LINK, TD A:VISITED {\n         color:black; text-decoratio" +
           "n:none\n      }\n   </STYLE>\n</HEAD>\n\n<BODY>\n<H1>\n   %s\n" +
           "</H1>\n<HR>\n<P>\n") % (myTitle, myTitle))

    return
# ########################################################################### #



def ovrd_html_override(authDict, cgiMTRC, siteFacility, cgiSITE):
    """write main section of HTML override page to stdout"""
    # ####################################################################### #
    OVRD_NOENTRY = { 'name': None, 'status': None, 'mode': 'oneday',
                     'when': "", 'who': "", 'why': "" }
    #
    viewFlag = False
    siteAuth = set()
    mstrFlag = False

    print(("<TABLE>\n<TR>\n   <TD VALIGN=\"top\" NOWRAP><B>%s</B> &nbsp;\n  " +
           " <TD VALIGN=\"top\" NOWRAP><B>e-group</B> member of &nbsp;\n   <" +
           "TD VALIGN=\"top\" NOWRAP>\n") % authDict['fullname'])
    frstFlag = True
    for group in authDict['egroups']:
        if group in OVRD_AUTH_EGROUP[cgiMTRC]:
            viewFlag = True
            descripton = "allows to view all"
            if ( OVRD_AUTH_EGROUP[cgiMTRC][group] == "ALL" ):
                mstrFlag = True
                descripton = "allows to change all"
            elif ( type( OVRD_AUTH_EGROUP[cgiMTRC][group] ) == type( [] ) ):
                descripton = "allows to change"
                for site in OVRD_AUTH_EGROUP[cgiMTRC][group]:
                    siteAuth.add( site )
                    descripton += " %s" % site
            if ( frstFlag ):
                print("%s &nbsp; <I>(%s)</I>" % (group, descripton))
            else:
                print("<BR>\n%s &nbsp; <I>(%s)</I>" % (group, descripton))
            frstFlag = False
    if ( frstFlag == False ):
        print("\n")
    for group in authDict['egroups']:
        if ( len(group) < 13 ):
            continue
        if (( group[:4] != "cms-" ) or ( group[4:6].isupper() != True ) or
            ( group[6] != "_" ) or ( group[-5:] != "-exec" )):
            continue
        viewFlag = True
        facility = group[4:-5]
        siteStrng = "nothing"
        for site in siteFacility:
            if ( siteFacility[site] != facility ):
                continue
            siteAuth.add( site )
            if ( siteStrng == "nothing" ):
                siteStrng = "%s" % site
            else:
                siteStrng += ", %s" % site
        print(("<TR>\n   <TD>\n<TD VALIGN=\"top\" NOWRAP><B>Executive</B> of" +
               " &nbsp;\n   <TD VALIGN=\"top\" NOWRAP>%s &nbsp; <I>(allows t" +
               "o change %s)</I>") % (facility, siteStrng))
    for group in authDict['egroups']:
        if ( len(group) < 14 ):
            continue
        if (( group[:4] != "cms-" ) or ( group[4:6].isupper() != True ) or
            ( group[6] != "_" ) or ( group[-6:] != "-admin" )):
            continue
        viewFlag = True
        facility = group[4:-6]
        siteStrng = "nothing"
        for site in siteFacility:
            if ( siteFacility[site] != facility ):
                continue
            siteAuth.add( site )
            if ( siteStrng == "nothing" ):
                siteStrng = "%s" % site
            else:
                siteStrng += ", %s" % site
        print(("<TR>\n   <TD>\n<TD VALIGN=\"top\" NOWRAP><B>Admin</B> of &nb" +
               "sp;\n   <TD VALIGN=\"top\" NOWRAP>%s &nbsp; <I>(allows to ch" +
               "ange %s)</I>") % (facility, siteStrng))
    #
    print("</TABLE>\n<BR>\n<P>\n\n")
    #
    siteAuth = sorted( siteAuth )
    #
    if cgiSITE is not None:
        siteList = [ cgiSITE ]
    else:
        siteList = sorted( siteFacility.keys() )

    if ( viewFlag ):
        overrideDict = ovrd_read_jsonfile(cgiMTRC)


        print(("<TABLE BORDER=\"0\" CELLPADDING=\"2\" CELLSPACING=\"1\">\n<T" +
               "R>\n   <TH STYLE=\"text-align: left; font-size: larger;\">CM" +
               "S Site:\n   <TH STYLE=\"text-align: left; font-size: larger;" +
               "\">%s Override:\n\n") % cgiMTRC)
        #
        for site in siteList:
            if site in overrideDict:
                entry = overrideDict[site]
            else:
                entry = OVRD_NOENTRY
            #
            if (( mstrFlag == False ) and ( site not in siteAuth )):
                bckgnd = "#F4F4F4"
            elif ( entry['status'] == "enabled" ):
                bckgnd = "#E8FFE8"
            elif (( entry['status'] == "waiting_room" ) or
                  ( entry['status'] == "drain" ) or
                  ( entry['status'] == "test" )):
                bckgnd = "#FFFFD0"
            elif (( entry['status'] == "morgue" ) or
                  ( entry['status'] == "disabled" )):
                bckgnd = "#FFE8E8"
            else:
                bckgnd = "#FFFFFF"
            #
            if ((( entry['when'] is not None ) and ( entry['when'] != "" )) or
                (( entry['who'] is not None ) and ( entry['who'] != "" )) or
                (( entry['why'] is not None ) and ( entry['why'] != "" ))):
                crrntInfo = (("      <DIV style=\"font-style: italic; white-" +
                              "space: nowrap;\">\n         &nbsp;(%s  &nbsp;" +                               " %s &nbsp; %s)\n      </DIV>\n      <HR>\n") %
                                 ( entry['when'], entry['who'], entry['why'] ))
            else:
                crrntInfo = ""
            #
            slctnInfo = "<INPUT TYPE=\"radio\" NAME=\"status\" VALUE=\"auto\""
            if (( site not in siteAuth ) or ( entry['status'] is None )):
                slctnInfo += " CHECKED"
            slctnInfo += (">Automatic state setting/no override\n         <B" +
                          "R>\n")
            for state in OVRD_STATUS_DESC[cgiMTRC]:
                slctnInfo += (("         <INPUT TYPE=\"radio\" NAME=\"status" +
                               "\" VALUE=\"%s\"") % state)
                if ( entry['status'] == state ):
                    slctnInfo += " CHECKED"
                slctnInfo += (">%s\n         &nbsp; &nbsp;\n" %
                                              OVRD_STATUS_DESC[cgiMTRC][state])
            slctnInfo += ("         <SELECT NAME=\"mode\">\n            <OPT" +
                          "ION VALUE=\"latched\"")
            if ( entry['mode'] == "latched" ):
                slctnInfo += " SELECTED"
            if ( mstrFlag == False ):
                slctnInfo += " DISABLED"
            slctnInfo += (">latched</OPTION>\n            <OPTION VALUE=\"on" +
                          "eday\"")
            if (( entry['mode'] == "" ) or ( entry['mode'] == "oneday" )):
                slctnInfo += " SELECTED"
            slctnInfo += (">one day</OPTION>\n            <OPTION VALUE=\"to" +
                          "ggle\"")
            if ( entry['mode'] == "toggle" ):
                slctnInfo += " SELECTED"
            slctnInfo += ">toggle</OPTION>\n         </SELECT>"
            #
            print(("<TR HEIGHT=\"3\">\n   <TD COLSPAN=\"2\" STYLE=\"backgrou" +
                   "nd-color: black\">\n" +
                   "<TR style=\"background-color: %s; line-height: 175%%;\">" +
                   "\n   <TD VALIGN=\"TOP\">\n      <B>%s</B>&nbsp;\n   <TD " +
                   "VALIGN=\"TOP\">\n%s      <FORM METHOD=\"POST\" ENCTYPE=" +
                   "\"application/x-www-form-urlencoded\" action=\"%s/%s/%s" +
                   "\">\n         %s\n         <BR>\n         Reason:&nbsp;" +
                   "\n         <INPUT TYPE=text NAME=\"why\" MAXLENGTH=128 " +
                   "SIZE=80 VALUE=\"\">\n         &nbsp;\n         <INPUT TY" +
                   "PE=\"submit\" VALUE=\"Apply\" style=\"height:32px; width" +
                   ":64px; font-weight: bold; background-color: #B0C0FF;\">" +
                   "\n      </FORM>\n") % (bckgnd, site, crrntInfo,
                                        OVRD_CGIURL, cgiMTRC, site, slctnInfo))
        #
        print("<TR HEIGHT=\"3\">\n   <TD COLSPAN=\"2\" STYLE=\"background-co" +
              "lor: black\">\n</TABLE>\n<BR>\n<P>\n")

    return
# ########################################################################### #



def ovrd_post_override(authDict, cgiMTRC, siteFacility, cgiSITE, cgiPOST):
    """set override and write main section of HTML update page to stdout"""
    # ####################################################################### #
    commentRegex = re.compile("[^a-zA-Z0-9_.,:;!?=/+*#~ -]")

    # prepare override entry:
    overrideEntry = {}
    try:
        overrideEntry['name'] = cgiSITE
        overrideEntry['status'] = cgiPOST['status'][0]
        if ( overrideEntry['status'] == "auto" ):
            overrideEntry['status'] = None
        overrideEntry['mode'] = cgiPOST['mode'][0]
        overrideEntry['when'] = time.strftime("%Y-%b-%d %H:%M:%S",
                                                      time.gmtime(time.time()))
        overrideEntry['who'] = authDict['username']
        overrideEntry['why'] = commentRegex.sub("", cgiPOST['why'][0])
    except (KeyError, IndexError) as excptn:
        logging.critical("Bad CGI data, %s" % str(excptn))
        return

    # check/validate override entry:
    if cgiMTRC not in OVRD_STATUS_DESC:
        logging.critical("Unsupported metric \"%s\"" % cgiMTRC)
        return
    #
    if overrideEntry['name'] not in siteFacility:
        logging.critical("Unknown CMS site \"%s\"" % overrideEntry['name'])
        return
    #
    if (( overrideEntry['status'] is not None ) and
        ( overrideEntry['status'] not in OVRD_STATUS_DESC[cgiMTRC] )):
        logging.critical("Illegal %s metric status \"%s\"" %
                                            (cgiMTRC, overrideEntry['status']))
        return
    #
    if overrideEntry['mode'] not in OVRD_MODE_DESC[cgiMTRC]:
        logging.critical("Illegal %s override mode \"%s\"" %
                                              (cgiMTRC, overrideEntry['mode']))
        return

    # check authorization:
    authFlag = False
    mstrFlag = False
    for group in authDict['egroups']:
        if group in OVRD_AUTH_EGROUP[cgiMTRC]:
            if ( OVRD_AUTH_EGROUP[cgiMTRC][group] == "ALL" ):
                authFlag = True
                mstrFlag = True
                break
            elif ( type( OVRD_AUTH_EGROUP[cgiMTRC][group] ) == type( [] ) ):
                for site in OVRD_AUTH_EGROUP[cgiMTRC][group]:
                    if ( site == overrideEntry['name'] ):
                         authFlag = True
        elif (( len(group) >= 13 ) and
              ( group[:4] == "cms-" ) and ( group[4:6].isupper() == True ) and
              ( group[6] == "_" ) and ( group[-5:] == "-exec" )):
            if ( siteFacility[ overrideEntry['name'] ] == group[4:-5] ):
                authFlag = True
        elif (( len(group) >= 14 ) and
              ( group[:4] == "cms-" ) and ( group[4:6].isupper() == True ) and
              ( group[6] == "_" ) and ( group[-6:] == "-admin" )):
            if ( siteFacility[ overrideEntry['name'] ] == group[4:-6] ):
                authFlag = True
    if ( authFlag == False ):
        logging.critical(("User \"%s\" not authorized to change %s of CMS si" +
                          "te \"%s\"") % (overrideEntry['who'], cgiMTRC,
                                                        overrideEntry['name']))
        return

    # update override file with new site entry:
    ovrd_update_jsonfile(cgiMTRC, overrideEntry)

    # append operation to log file:
    ovrd_append_log(cgiMTRC, overrideEntry)

    # re-read override file:
    overrideDict = ovrd_read_jsonfile(cgiMTRC)

    # write main section of HTML update page:
    print(("<TABLE BORDER=\"0\" CELLPADDING=\"2\" CELLSPACING=\"1\">\n<TR>\n" +
           "   <TH STYLE=\"text-align: left; font-size: larger;\">CMS Site:" +
           "\n   <TH STYLE=\"text-align: left; font-size: larger;\">%s Overr" +
           "ide:\n") % cgiMTRC)
    #
    if cgiSITE in overrideDict:
        if ( overrideDict[cgiSITE]['status'] == "enabled" ):
            bckgnd = "#E8FFE8"
        elif (( overrideDict[cgiSITE]['status'] == "waiting_room" ) or
              ( overrideDict[cgiSITE]['status'] == "drain" ) or
              ( overrideDict[cgiSITE]['status'] == "test" )):
            bckgnd = "#FFFFD0"
        elif (( overrideDict[cgiSITE]['status'] == "morgue" ) or
              ( overrideDict[cgiSITE]['status'] == "disabled" )):
            bckgnd = "#FFE8E8"
        else:
            bckgnd = "#FFFFFF"
        #
        crrntInfo = (("      <DIV style=\"font-style: italic; white-space: n" +
                      "owrap;\">\n         &nbsp;(%s  &nbsp; %s &nbsp; %s)\n" +                       "      </DIV>\n      <HR>\n") %
                     ( overrideDict[cgiSITE]['when'],
                  overrideDict[cgiSITE]['who'], overrideDict[cgiSITE]['why'] ))
        #
        slctnInfo = ("<INPUT TYPE=\"radio\" NAME=\"status\" VALUE=\"auto\">A" +
                     "utomatic state setting/no override\n         <BR>\n")
        for state in OVRD_STATUS_DESC[cgiMTRC]:
            slctnInfo += (("         <INPUT TYPE=\"radio\" NAME=\"status\" V" +
                           "ALUE=\"%s\"") % state)
            if ( overrideDict[cgiSITE]['status'] == state ):
                slctnInfo += " CHECKED"
            slctnInfo += (">%s\n         &nbsp; &nbsp;\n" %
                                              OVRD_STATUS_DESC[cgiMTRC][state])
        slctnInfo += ("         <SELECT NAME=\"mode\">\n            <OPTION " +
                      "VALUE=\"latched\"")
        if ( overrideDict[cgiSITE]['mode'] == "latched" ):
            slctnInfo += " SELECTED"
        if ( mstrFlag == False ):
            slctnInfo += " DISABLED"
        slctnInfo += ">latched</OPTION>\n            <OPTION VALUE=\"oneday\""
        if (( overrideDict[cgiSITE]['mode'] == "" ) or
            ( overrideDict[cgiSITE]['mode'] == "oneday" )):
            slctnInfo += " SELECTED"
        slctnInfo += ">one day</OPTION>\n            <OPTION VALUE=\"toggle\""
        if ( overrideDict[cgiSITE]['mode'] == "toggle" ):
            slctnInfo += " SELECTED"
        slctnInfo += ">toggle</OPTION>\n         </SELECT>"
        #
        print(("<TR HEIGHT=\"3\">\n   <TD COLSPAN=\"2\" STYLE=\"background-c" +
               "olor: black\">\n<TR style=\"background-color: %s; line-heigh" +
               "t: 175%%;\">\n   <TD VALIGN=\"TOP\">\n      <B>%s</B>&nbsp;" +
               "\n   <TD VALIGN=\"TOP\">\n%s      <FORM METHOD=\"POST\" ENCT" +
               "YPE=\"application/x-www-form-urlencoded\" action=\"%s/%s/%s" +
               "\">\n         %s\n         <BR>\n         Reason:&nbsp;\n   " +
               "      <INPUT TYPE=text NAME=\"why\" MAXLENGTH=128 SIZE=80 VA" +
               "LUE=\"\">\n         &nbsp;\n         <INPUT TYPE=\"submit\" " +
               "VALUE=\"Apply\" style=\"height:32px; width:64px; font-weight" +
               ": bold; background-color: #B0C0FF;\">\n      </FORM>\n") %
              (bckgnd, cgiSITE, crrntInfo, OVRD_CGIURL, cgiMTRC, cgiSITE,
                                                                    slctnInfo))
    else:
        slctnInfo = ("<INPUT TYPE=\"radio\" NAME=\"status\" VALUE=\"auto\" C" +
                     "HECKED>Automatic state setting/no override\n         <" +
                     "BR>\n")
        for state in OVRD_STATUS_DESC[cgiMTRC]:
            slctnInfo += (("         <INPUT TYPE=\"radio\" NAME=\"status\" V" +
                           "ALUE=\"%s\">%s\n         &nbsp; &nbsp;\n") %
                                     (state, OVRD_STATUS_DESC[cgiMTRC][state]))
        slctnInfo += ("         <SELECT NAME=\"mode\">\n            <OPTION " +
                      "VALUE=\"latched\">latched</OPTION>\n            <OPTI" +
                      "ON VALUE=\"oneday\" SELECTED>one day</OPTION>\n      " +
                      "      <OPTION VALUE=\"toggle\">toggle</OPTION>\n     " +
                      "    </SELECT>")
        #
        print(("<TR HEIGHT=\"3\">\n   <TD COLSPAN=\"2\" STYLE=\"background-c" +
               "olor: black\">\n<TR style=\"background-color: #FFFFFF; line-" +
               "height: 175%%;\">\n   <TD VALIGN=\"TOP\">\n      <B>%s</B>&n" +
               "bsp;\n   <TD>\n      <FORM METHOD=\"POST\" ENCTYPE=\"applica" +
               "tion/x-www-form-urlencoded\" action=\"%s/%s/%s\">\n         " +
               "%s\n         <BR>\n         Reason:&nbsp;\n         <INPUT T" +
               "YPE=text NAME=\"why\" MAXLENGTH=128 SIZE=80 VALUE=\"\">\n   " +
               "      &nbsp;\n         <INPUT TYPE=\"submit\" VALUE=\"Apply" +
               "\" style=\"height:32px; width:64px; font-weight: bold; backg" +
               "round-color: #B0C0FF;\">\n      </FORM>\n") % (cgiSITE,
                                     OVRD_CGIURL, cgiMTRC, cgiSITE, slctnInfo))
    print("<TR HEIGHT=\"3\">\n   <TD COLSPAN=\"2\" STYLE=\"background-color:" +
          " black\">\n</TABLE>\n<BR>\n<P>\n")

    return
# ########################################################################### #



def ovrd_html_capacity(authDict, siteFacility, federationNames, cgiSITE):
    """write main section of HTML capacity page to stdout"""
    # ####################################################################### #
    OVRD_NOENTRY = { 'name': None,           'wlcg_federation_name': None,
                     'wlcg_federation_fraction': 1.000,
                     'hs06_pledge': 0,       'hs06_per_core': 10.000,
                     'core_usable': 0,       'core_max_used': 0,
                     'core_production': 0,   'core_cpu_intensive': 0,
                     'core_io_intensive': 0, 'disk_pledge': 0.0,
                     'disk_usable': 0.0,     'disk_experiment_use': 0.0,
                     'tape_pledge': 0.0,     'tape_usable': 0.0,
                     'when': "never", 'who': "anybody" }
    #
    viewFlag = False
    siteAuth = set()
    mstrFlag = False

    print(("<TABLE>\n<TR>\n   <TD VALIGN=\"top\" NOWRAP><B>%s</B> &nbsp;\n  " +
           " <TD VALIGN=\"top\" NOWRAP><B>e-group</B> member of &nbsp;\n   <" +
           "TD VALIGN=\"top\" NOWRAP>\n") % authDict['fullname'])
    frstFlag = True
    for group in authDict['egroups']:
        if group in OVRD_AUTH_EGROUP['SiteCapacity']:
            viewFlag = True
            descripton = "allows to view all"
            if ( OVRD_AUTH_EGROUP['SiteCapacity'][group] == "ALL" ):
                mstrFlag = True
                descripton = "allows to change all"
            if ( frstFlag ):
                print("%s &nbsp; <I>(%s)</I>" % (group, descripton))
            else:
                print("<BR>\n%s &nbsp; <I>(%s)</I>" % (group, descripton))
            frstFlag = False
    if ( frstFlag == False ):
        print("\n")
    for group in authDict['egroups']:
        if ( len(group) < 13 ):
            continue
        if (( group[:4] != "cms-" ) or ( group[4:6].isupper() != True ) or
            ( group[6] != "_" ) or ( group[-5:] != "-exec" )):
            continue
        viewFlag = True
        facility = group[4:-5]
        siteStrng = "nothing"
        for site in siteFacility:
            if ( siteFacility[site] != facility ):
                continue
            siteAuth.add( site )
            if ( siteStrng == "nothing" ):
                siteStrng = "%s" % site
            else:
                siteStrng += ", %s" % site
        print(("<TR>\n   <TD>\n<TD VALIGN=\"top\" NOWRAP><B>Executive</B> of" +
               " &nbsp;\n   <TD VALIGN=\"top\" NOWRAP>%s &nbsp; <I>(allows t" +
               "o change %s)</I>") % (facility, siteStrng))
    for group in authDict['egroups']:
        if ( len(group) < 14 ):
            continue
        if (( group[:4] != "cms-" ) or ( group[4:6].isupper() != True ) or
            ( group[6] != "_" ) or ( group[-6:] != "-admin" )):
            continue
        viewFlag = True
        facility = group[4:-6]
        siteStrng = "nothing"
        for site in siteFacility:
            if ( siteFacility[site] != facility ):
                continue
            siteAuth.add( site )
            if ( siteStrng == "nothing" ):
                siteStrng = "%s" % site
            else:
                siteStrng += ", %s" % site
        print(("<TR>\n   <TD>\n<TD VALIGN=\"top\" NOWRAP><B>Admin</B> of &nb" +
               "sp;\n   <TD VALIGN=\"top\" NOWRAP>%s &nbsp; <I>(allows to ch" +
               "ange %s)</I>") % (facility, siteStrng))
    #
    print("</TABLE>\n<BR>\n<P>\n\n")
    #
    siteAuth = sorted( siteAuth )
    #
    if cgiSITE is not None:
        siteList = [ cgiSITE ]
    else:
        siteList = sorted( siteFacility.keys() )

    if ( viewFlag ):
        capacityDict = ovrd_read_jsonfile('SiteCapacity')


        print("<TABLE BORDER=\"0\" CELLPADDING=\"2\" CELLSPACING=\"1\">\n<TR" +
              ">\n   <TH STYLE=\"text-align: left; font-size: larger;\">CMS " +
              "Site:\n   <TH STYLE=\"text-align: left; font-size: larger;\">" +
              "Capacity Information:\n")
        #
        for site in siteList:
            if site in capacityDict:
                entry = capacityDict[site]
            else:
                entry = OVRD_NOENTRY
            #
            if (( mstrFlag == False ) and ( site not in siteAuth )):
                bckgnd = "#F4F4F4"
            else:
                bckgnd = "#FFFFFF"
            #
            if entry['wlcg_federation_name'] is None:
                slctnInfo = " SELECTED"
            else:
                slctnInfo = ""
            #
            print(("<TR HEIGHT=\"3\">\n   <TD COLSPAN=\"2\" STYLE=\"backgrou" +
                   "nd-color: black\">\n" +
                   "<TR style=\"background-color: %s; line-height: 150%%;\">" +
                   "\n   <FORM METHOD=\"POST\" ENCTYPE=\"application/x-www-f" +
                   "orm-urlencoded\" action=\"%s/SiteCapacity/%s\">\n   <TD " +
                   "VALIGN=\"TOP\" NOWRAP>\n      <B>%s</B>&nbsp;\n   <TD VA" +
                   "LIGN=\"TOP\" NOWRAP>\n      <SELECT ID=\"%s:wlcg_federat" +
                   "ion_name\" NAME=\"wlcg_federation_name\" onchange=\"hand" +
                   "lePledge(this.id, this.value)\">\n         <OPTION VALUE" +
                   "=\"*none*\"%s></OPTION>") %
                            (bckgnd, OVRD_CGIURL, site, site, site, slctnInfo))
            for federation in federationNames:
                if ( entry['wlcg_federation_name'] == federation ):
                    print(("         <OPTION VALUE=\"%s\" SELECTED>%s</OPTIO" +
                           "N>") % (federation, federation))
                else:
                    print(("         <OPTION VALUE=\"%s\">%s</OPTION>") %
                                                      (federation, federation))
            print("      </SELECT>%s<BR>" %
                                    OVRD_CAPACITY_DESC['wlcg_federation_name'])
            #
            if entry['wlcg_federation_name'] is None:
               print(("      <INPUT ID=\"%s:wlcg_federation_fraction\" TYPE=" +
                      "\"number\" STEP=\"0.001\" MIN=\"0.000\" NAME=\"wlcg_f" +
                      "ederation_fraction\" VALUE=\"%.3f\" READONLY>%s<BR>")
                     % (site, entry['wlcg_federation_fraction'],
                               OVRD_CAPACITY_DESC['wlcg_federation_fraction']))
               print(("      <INPUT ID=\"%s:hs06_pledge\" TYPE=\"number\" SI" +
                      "ZE=\"12\" STEP=\"1\" MIN=\"0\" NAME=\"hs06_pledge\" V" +
                      "ALUE=\"%d\">%s<BR>") % (site, entry['hs06_pledge'],
                                            OVRD_CAPACITY_DESC['hs06_pledge']))
            else:
               print(("      <INPUT ID=\"%s:wlcg_federation_fraction\" TYPE=" +
                      "\"number\" STEP=\"0.001\" MIN=\"0.000\" NAME=\"wlcg_f" +
                      "ederation_fraction\" VALUE=\"%.3f\">%s<BR>") %
                     (site, entry['wlcg_federation_fraction'],
                               OVRD_CAPACITY_DESC['wlcg_federation_fraction']))
               print(("      <INPUT ID=\"%s:hs06_pledge\" TYPE=\"number\" SI" +
                      "ZE=\"12\" STEP=\"1\" MIN=\"0\" NAME=\"hs06_pledge\" V" +
                      "ALUE=\"%d\" READONLY>%s<BR>") %
                     (site, entry['hs06_pledge'],
                                            OVRD_CAPACITY_DESC['hs06_pledge']))
            print(("      <INPUT TYPE=\"number\" STEP=\"0.001\" SIZE=\"9\" N" +
                   "AME=\"hs06_per_core\" VALUE=\"%.3f\">%s<BR>") %
                 (entry['hs06_per_core'], OVRD_CAPACITY_DESC['hs06_per_core']))
            print(("      <INPUT ID=\"%s:core_usable\" TYPE=\"number\" SIZE=" +
                   "\"12\" STEP=\"1\" MIN=\"0\" NAME=\"core_usable\" VALUE=" +
                   "\"%d\" onchange=\"updateProd(this.id, this.value)\">%s<B" +
                   "R>") % (site, entry['core_usable'],
                                            OVRD_CAPACITY_DESC['core_usable']))
            print(("      <INPUT TYPE=\"number\" SIZE=\"12\" STEP=\"1\" MIN=" +
                   "\"0\" NAME=\"core_max_used\" VALUE=\"%d\" READONLY>%s<BR" +
                   ">") % (entry['core_max_used'],
                                          OVRD_CAPACITY_DESC['core_max_used']))
            print(("      <INPUT ID=\"%s:core_production\" TYPE=\"number\" S" +
                   "IZE=\"12\" STEP=\"1\" MIN=\"0\" NAME=\"core_production\"" +
                   " VALUE=\"%d\">%s<BR>") %
                  (site, entry['core_production'],
                                        OVRD_CAPACITY_DESC['core_production']))
            print(("      <INPUT TYPE=\"number\" SIZE=\"12\" STEP=\"1\" MIN=" +
                   "\"0\" NAME=\"core_cpu_intensive\" VALUE=\"%d\">%s<BR>") %
                  (entry['core_cpu_intensive'],
                                     OVRD_CAPACITY_DESC['core_cpu_intensive']))
            print(("      <INPUT TYPE=\"number\" SIZE=\"12\" STEP=\"1\" MIN=" +
                   "\"0\" NAME=\"core_io_intensive\" VALUE=\"%d\">%s<BR>") %
                  (entry['core_io_intensive'],
                                      OVRD_CAPACITY_DESC['core_io_intensive']))
            if entry['wlcg_federation_name'] is None:
                print(("      <INPUT ID=\"%s:disk_pledge\" TYPE=\"number\" S" +
                       "IZE=\"12\" STEP=\"0.5\" MIN=\"0\" NAME=\"disk_pledge" +
                       "\" VALUE=\"%.1f\">%s<BR>") % (site,
                      entry['disk_pledge'], OVRD_CAPACITY_DESC['disk_pledge']))
            else:
                print(("      <INPUT ID=\"%s:disk_pledge\" TYPE=\"number\" S" +
                       "IZE=\"12\" STEP=\"0.5\" MIN=\"0\" NAME=\"disk_pledge" +
                       "\" VALUE=\"%.1f\" READONLY>%s<BR>") % (site,
                      entry['disk_pledge'], OVRD_CAPACITY_DESC['disk_pledge']))
            print(("      <INPUT TYPE=\"number\" SIZE=\"12\" STEP=\"0.5\" MI" +
                   "N=\"0\" NAME=\"disk_usable\" VALUE=\"%.1f\">%s<BR>") %
                  (entry['disk_usable'], OVRD_CAPACITY_DESC['disk_usable']))
            print(("      <INPUT TYPE=\"number\" SIZE=\"12\" STEP=\"0.5\" MI" +
                   "N=\"0\" NAME=\"disk_experiment_use\" VALUE=\"%.1f\" READ" +
                   "ONLY>%s<BR>") % (entry['disk_experiment_use'],
                                    OVRD_CAPACITY_DESC['disk_experiment_use']))
            if entry['wlcg_federation_name'] is None:
                print(("      <INPUT ID=\"%s:tape_pledge\" TYPE=\"number\" S" +
                       "IZE=\"12\" STEP=\"0.5\" MIN=\"0\" NAME=\"tape_pledge" +
                       "\" VALUE=\"%.1f\">%s<BR>") % (site,
                      entry['tape_pledge'], OVRD_CAPACITY_DESC['tape_pledge']))
            else:
                print(("      <INPUT ID=\"%s:tape_pledge\" TYPE=\"number\" S" +
                       "IZE=\"12\" STEP=\"0.5\" MIN=\"0\" NAME=\"tape_pledge" +
                       "\" VALUE=\"%.1f\" READONLY>%s<BR>") % (site,
                      entry['tape_pledge'], OVRD_CAPACITY_DESC['tape_pledge']))
            print(("      <INPUT TYPE=\"number\" SIZE=\"12\" STEP=\"0.5\" MI" +
                   "N=\"0\" NAME=\"tape_usable\" VALUE=\"%.1f\">%s<BR>") %
                  (entry['tape_usable'], OVRD_CAPACITY_DESC['tape_usable']))
            if (( mstrFlag == False ) and ( site not in siteAuth )):
                print(("      <INPUT TYPE=\"submit\" VALUE=\"Update Informat" +
                       "ion\" style=\"height:32px; width:144px; font-weight:" +
                       " 600; white-space: nowrap; background-color: #B0C0FF" +
                       ";\" READONLY>\n      (previous update: <I>%s by %s</" +
                       "I>)") % (entry['when'], entry['who']))
            else:
                print(("      <INPUT TYPE=\"submit\" VALUE=\"Update Informat" +
                       "ion\" style=\"height:32px; width:144px; font-weight:" +
                       " 600; white-space: nowrap; background-color: #B0C0FF" +
                       ";\">\n      (previous update: <I>%s by %s</I>)") %
                      (entry['when'], entry['who']))
            #
            print("   </FORM>\n")
        #
        print("<TR HEIGHT=\"3\">\n   <TD COLSPAN=\"2\" STYLE=\"background-co" +
              "lor: black\">\n</TABLE>\n<BR>\n<P>\n")

    return
# ########################################################################### #



def ovrd_post_capacity(authDict, siteFacility, federationNames,
                                                             cgiSITE, cgiPOST):
    """set capacity and write main section of HTML update page to stdout"""
    # ####################################################################### #
    OVRD_NOENTRY = { 'name': None,           'wlcg_federation_name': None,
                     'wlcg_federation_fraction': 1.000,
                     'hs06_pledge': 0,       'hs06_per_core': 10.000,
                     'core_usable': 0,       'core_max_used': 0,
                     'core_production': 0,   'core_cpu_intensive': 0,
                     'core_io_intensive': 0, 'disk_pledge': 0.0,
                     'disk_usable': 0.0,     'disk_experiment_use': 0.0,
                     'tape_pledge': 0.0,     'tape_usable': 0.0,
                     'when': "never", 'who': "anybody" }

    # prepare capacity entry:
    capacityEntry = {}
    try:
        capacityEntry['name'] = cgiSITE
        capacityEntry['wlcg_federation_name'] = \
                                             cgiPOST['wlcg_federation_name'][0]
        if ( capacityEntry['wlcg_federation_name'] == "*none*" ):
            capacityEntry['wlcg_federation_name'] = None
        capacityEntry['wlcg_federation_fraction'] = \
                      round(float( cgiPOST['wlcg_federation_fraction'][0] ), 3)
        capacityEntry['hs06_pledge'] = int( cgiPOST['hs06_pledge'][0] )
        capacityEntry['hs06_per_core'] = \
                                 round(float( cgiPOST['hs06_per_core'][0] ), 3)
        capacityEntry['core_usable'] = int( cgiPOST['core_usable'][0] )
        capacityEntry['core_max_used'] = int( cgiPOST['core_max_used'][0] )
        capacityEntry['core_production'] = int( cgiPOST['core_production'][0] )
        capacityEntry['core_cpu_intensive'] = \
                                        int( cgiPOST['core_cpu_intensive'][0] )
        capacityEntry['core_io_intensive'] = \
                                         int( cgiPOST['core_io_intensive'][0] )
        capacityEntry['disk_pledge'] = \
                           int( 2.0 * float( cgiPOST['disk_pledge'][0] )) / 2.0
        capacityEntry['disk_usable'] = \
                           int( 2.0 * float( cgiPOST['disk_usable'][0] )) / 2.0
        capacityEntry['disk_experiment_use'] = \
                   int( 2.0 * float( cgiPOST['disk_experiment_use'][0] )) / 2.0
        capacityEntry['tape_pledge'] = \
                           int( 2.0 * float( cgiPOST['tape_pledge'][0] )) / 2.0
        capacityEntry['tape_usable'] = \
                           int( 2.0 * float( cgiPOST['tape_usable'][0] )) / 2.0
        capacityEntry['when'] = time.strftime("%Y-%b-%d %H:%M:%S",
                                                      time.gmtime(time.time()))
        capacityEntry['who'] = authDict['username']
    except (KeyError, IndexError) as excptn:
        logging.critical("Bad CGI data, %s" % str(excptn))
        return

    # check/validate capacity entry:
    if capacityEntry['name'] not in siteFacility:
        logging.critical("Unknown CMS site \"%s\"" % capacityEntry['name'])
        return
    #
    if (( capacityEntry['wlcg_federation_name'] is not None ) and
        ( capacityEntry['wlcg_federation_name'] not in federationNames )):
        logging.critical("Illegal federation name, \"%s\"" %
                                    str(capacityEntry['wlcg_federation_name']))
        return

    # check authorization:
    authFlag = False
    for group in authDict['egroups']:
        if group in OVRD_AUTH_EGROUP['SiteCapacity']:
            if ( OVRD_AUTH_EGROUP['SiteCapacity'][group] == "ALL" ):
                authFlag = True
                break
        elif (( len(group) >= 13 ) and
              ( group[:4] == "cms-" ) and ( group[4:6].isupper() == True ) and
              ( group[6] == "_" ) and ( group[-5:] == "-exec" )):
            if ( siteFacility[ capacityEntry['name'] ] == group[4:-5] ):
                authFlag = True
        elif (( len(group) >= 14 ) and
              ( group[:4] == "cms-" ) and ( group[4:6].isupper() == True ) and
              ( group[6] == "_" ) and ( group[-6:] == "-admin" )):
            if ( siteFacility[ capacityEntry['name'] ] == group[4:-6] ):
                authFlag = True
    if ( authFlag == False ):
        logging.critical(("User \"%s\" not authorized to change SiteCapacity" +
                          " of CMS site \"%s\"") % (capacityEntry['who'], 
                                                        capacityEntry['name']))
        return

    # update capacity file with new site entry:
    ovrd_update_jsonfile("SiteCapacity", capacityEntry)

    # append operation to log file:
    ovrd_append_log("SiteCapacity", capacityEntry)

    # re-read capacity file:
    capacityDict = ovrd_read_jsonfile("SiteCapacity")

    # write main section of HTML update page:
    print("<TABLE BORDER=\"0\" CELLPADDING=\"2\" CELLSPACING=\"1\">\n<TR>\n " +
          "  <TH STYLE=\"text-align: left; font-size: larger;\">CMS Site:\n " +
          "  <TH STYLE=\"text-align: left; font-size: larger;\">Capacity Inf" +
          "ormation:\n")
    #
    if cgiSITE in capacityDict:
        entry = capacityDict[ cgiSITE ]
    else:
        entry = OVRD_NOENTRY
    #
    if entry['wlcg_federation_name'] is None:
        slctnInfo = " SELECTED"
    else:
        slctnInfo = ""
    #
    print(("<TR HEIGHT=\"3\">\n   <TD COLSPAN=\"2\" STYLE=\"background-color" +
           ": black\">\n" +
           "<TR style=\"background-color: #FFFFFF; line-height: 150%%;\">\n " +
           "  <FORM METHOD=\"POST\" ENCTYPE=\"application/x-www-form-urlenco" +
           "ded\" action=\"%s/SiteCapacity/%s\">\n   <TD VALIGN=\"TOP\" NOWR" +
           "AP>\n      <B>%s</B>&nbsp;\n   <TD VALIGN=\"TOP\" NOWRAP>\n     " +
           " <SELECT ID=\"%s:wlcg_federation_name\" NAME=\"wlcg_federation_n" +
           "ame\" onchange=\"handlePledge(this.id, this.value)\">\n         " +
           "<OPTION VALUE=\"*none*\"%s></OPTION>") %
                           (OVRD_CGIURL, cgiSITE, cgiSITE, cgiSITE, slctnInfo))
    for federation in federationNames:
        if ( entry['wlcg_federation_name'] == federation ):
            print(("         <OPTION VALUE=\"%s\" SELECTED>%s</OPTION>") %
                                                      (federation, federation))
        else:
            print(("         <OPTION VALUE=\"%s\">%s</OPTION>") %
                                                      (federation, federation))
    print("      </SELECT>%s<BR>" %
                                    OVRD_CAPACITY_DESC['wlcg_federation_name'])
    #
    if entry['wlcg_federation_name'] is None:
       print(("      <INPUT ID=\"%s:wlcg_federation_fraction\" TYPE=\"number" +
              "\" STEP=\"0.001\" MIN=\"0.000\" NAME=\"wlcg_federation_fracti" +
              "on\" VALUE=\"%.3f\" READONLY>%s<BR>") %
             (cgiSITE, entry['wlcg_federation_fraction'],
                               OVRD_CAPACITY_DESC['wlcg_federation_fraction']))
       print(("      <INPUT ID=\"%s:hs06_pledge\" TYPE=\"number\" SIZE=\"12" +
              "\" STEP=\"1\" MIN=\"0\" NAME=\"hs06_pledge\" VALUE=\"%d\">%s<" +
              "BR>") % (cgiSITE, entry['hs06_pledge'],
                                            OVRD_CAPACITY_DESC['hs06_pledge']))
    else:
       print(("      <INPUT ID=\"%s:wlcg_federation_fraction\" TYPE=\"number" +
              "\" STEP=\"0.001\" MIN=\"0.000\" NAME=\"wlcg_federation_fracti" +
              "on\" VALUE=\"%.3f\">%s<BR>") %
             (cgiSITE, entry['wlcg_federation_fraction'],
                               OVRD_CAPACITY_DESC['wlcg_federation_fraction']))
       print(("      <INPUT ID=\"%s:hs06_pledge\" TYPE=\"number\" SIZE=\"12" +
              "\" STEP=\"1\" MIN=\"0\" NAME=\"hs06_pledge\" VALUE=\"%d\" REA" +
              "DONLY>%s<BR>") % (cgiSITE, entry['hs06_pledge'],
                                            OVRD_CAPACITY_DESC['hs06_pledge']))
    print(("      <INPUT TYPE=\"number\" STEP=\"0.001\" SIZE=\"9\" NAME=\"hs" +
           "06_per_core\" VALUE=\"%.3f\">%s<BR>") %
                 (entry['hs06_per_core'], OVRD_CAPACITY_DESC['hs06_per_core']))
    print(("      <INPUT ID=\"%s:core_usable\" TYPE=\"number\" SIZE=\"12\" S" +
           "TEP=\"1\" MIN=\"0\" NAME=\"core_usable\" VALUE=\"%d\" onchange=" +
           "\"updateProd(this.id, this.value)\">%s<BR>") % (cgiSITE,
                      entry['core_usable'], OVRD_CAPACITY_DESC['core_usable']))
    print(("      <INPUT TYPE=\"number\" SIZE=\"12\" STEP=\"1\" MIN=\"0\" NA" +
           "ME=\"core_max_used\" VALUE=\"%d\" READONLY>%s<BR>") %
                 (entry['core_max_used'], OVRD_CAPACITY_DESC['core_max_used']))
    print(("      <INPUT ID=\"%s:core_production\" TYPE=\"number\" SIZE=\"12" +
           "\" STEP=\"1\" MIN=\"0\" NAME=\"core_production\" VALUE=\"%d\">%s" +
           "<BR>") % (cgiSITE, entry['core_production'],
                                        OVRD_CAPACITY_DESC['core_production']))
    print(("      <INPUT TYPE=\"number\" SIZE=\"12\" STEP=\"1\" MIN=\"0\" NA" +
           "ME=\"core_cpu_intensive\" VALUE=\"%d\">%s<BR>") %
       (entry['core_cpu_intensive'], OVRD_CAPACITY_DESC['core_cpu_intensive']))
    print(("      <INPUT TYPE=\"number\" SIZE=\"12\" STEP=\"1\" MIN=\"0\" NA" +
           "ME=\"core_io_intensive\" VALUE=\"%d\">%s<BR>") %
         (entry['core_io_intensive'], OVRD_CAPACITY_DESC['core_io_intensive']))
    if entry['wlcg_federation_name'] is None:
        print(("      <INPUT ID=\"%s:disk_pledge\" TYPE=\"number\" SIZE=\"12" +
               "\" STEP=\"0.5\" MIN=\"0\" NAME=\"disk_pledge\" VALUE=\"%.1f" +
               "\">%s<BR>") % (cgiSITE, entry['disk_pledge'],
                                            OVRD_CAPACITY_DESC['disk_pledge']))
    else:
        print(("      <INPUT ID=\"%s:disk_pledge\" TYPE=\"number\" SIZE=\"12" +
               "\" STEP=\"0.5\" MIN=\"0\" NAME=\"disk_pledge\" VALUE=\"%.1f" +
               "\" READONLY>%s<BR>") % (cgiSITE, entry['disk_pledge'],
                                            OVRD_CAPACITY_DESC['disk_pledge']))
    print(("      <INPUT TYPE=\"number\" SIZE=\"12\" STEP=\"0.5\" MIN=\"0\" " +
           "NAME=\"disk_usable\" VALUE=\"%.1f\">%s<BR>") %
                     (entry['disk_usable'], OVRD_CAPACITY_DESC['disk_usable']))
    print(("      <INPUT TYPE=\"number\" SIZE=\"12\" STEP=\"0.5\" MIN=\"0\" " +
           "NAME=\"disk_experiment_use\" VALUE=\"%.1f\" READONLY>%s<BR>") %
          (entry['disk_experiment_use'],
                                    OVRD_CAPACITY_DESC['disk_experiment_use']))
    if entry['wlcg_federation_name'] is None:
        print(("      <INPUT ID=\"%s:tape_pledge\" TYPE=\"number\" SIZE=\"12" +
               "\" STEP=\"0.5\" MIN=\"0\" NAME=\"tape_pledge\" VALUE=\"%.1f" +
               "\">%s<BR>") % (cgiSITE, entry['tape_pledge'],
                                            OVRD_CAPACITY_DESC['tape_pledge']))
    else:
        print(("      <INPUT ID=\"%s:tape_pledge\" TYPE=\"number\" SIZE=\"12" +
               "\" STEP=\"0.5\" MIN=\"0\" NAME=\"tape_pledge\" VALUE=\"%.1f" +
               "\" READONLY>%s<BR>") % (cgiSITE, entry['tape_pledge'],
                                            OVRD_CAPACITY_DESC['tape_pledge']))
    print(("      <INPUT TYPE=\"number\" SIZE=\"12\" STEP=\"0.5\" MIN=\"0\" " +
           "NAME=\"tape_usable\" VALUE=\"%.1f\">%s<BR>") %
                     (entry['tape_usable'], OVRD_CAPACITY_DESC['tape_usable']))
    print(("      <INPUT TYPE=\"submit\" VALUE=\"Update Information\" style=" +
           "\"height:32px; width:144px; font-weight: 600; white-space: nowra" +
           "p; background-color: #B0C0FF;\">\n      (previous update: <I>%s " +
           "by %s</I>)") % (entry['when'], entry['who']))
    #
    print("   </FORM>\n")
    #
    print("<TR HEIGHT=\"3\">\n   <TD COLSPAN=\"2\" STYLE=\"background-color:" +
          " black\">\n</TABLE>\n<BR>\n<P>\n")

    return
# ########################################################################### #



def ovrd_html_trailer(cgiMTRC, msgLog):
    """write trailer of HTML page to stdout"""
    # ####################################################################### #

    if ( len( msgLog ) > 0 ):
        msgStrng = msgLog.replace("\n", "<BR>\n")
        if ( msgStrng[-5:] == "<BR>\n" ):
            msgStrng = msgStrng[:-5]
        print("%s\n<HR>\n<P>\n\n" % msgStrng)

    timeStrng = time.strftime("%Y-%b-%d %H:%M GMT", time.gmtime(time.time()))
    #
    print(("<TABLE WIDTH=\"100%%\" BORDER=\"0\" CELLPADDING=\"0\" CELLSPACIN" +
           "G=\"2\">\n<TR>\n   <TD STYLE=\"text-align: left; color: blue; fo" +
           "nt-weight: bold; white-space: nowrap;\">Information as of %s\n  " +
           " <TD>&nbsp;\n   <TD STYLE=\"text-align: right;\"><A HREF=\"http:" +
           "//cern.ch/copyright\">&copy; Copyright author, CMS, Fermilab, an" +
           "d others 2019</A>\n</TABLE>\n") % timeStrng)
    #
    if ( cgiMTRC == "SiteCapacity" ):
        print("\n<SCRIPT type=\"text/javascript\" language=\"javascript\">\n" +
              "   \"use strict\";\n\n" +
              "   function handlePledge(fieldID, fieldVALUE) {\n      var cI" +
              "ndx = fieldID.indexOf(':');\n      if ( cIndx == -1 ) cIndx =" +
              " fieldID.length;\n      var stemID = fieldID.substr(0, cIndx)" +
              ";\n      if ( fieldVALUE == '*none*' ) {\n         document.g" +
              "etElementById(stemID + ':wlcg_federation_fraction').readOnly " +
              "= true;\n         document.getElementById(stemID + ':hs06_ple" +
              "dge').readOnly = false;\n         document.getElementById(ste" +
              "mID + ':disk_pledge').readOnly = false;\n         document.ge" +
              "tElementById(stemID + ':tape_pledge').readOnly = false;\n    " +
              "  } else {\n         document.getElementById(stemID + ':wlcg_" +
              "federation_fraction').readOnly = false;\n         document.ge" +
              "tElementById(stemID + ':hs06_pledge').readOnly = true;\n     " +
              "    document.getElementById(stemID + ':disk_pledge').readOnly" +
              " = true;\n         document.getElementById(stemID + ':tape_pl" +
              "edge').readOnly = true;\n      }\n   };\n\n" +
              "   function updateProd(fieldID, fieldVALUE) {\n      var cInd" +
              "x = fieldID.indexOf(':');\n      if ( cIndx == -1 ) cIndx = f" +
              "ieldID.length;\n      var stemID = fieldID.substr(0, cIndx);" +
              "\n      var updtID = stemID + ':core_production';\n      var " +
              "tierNO = parseInt( fieldID.substr(1,1) );\n      if ( tierNO " +
              "<= 1 ) {\n         var prodCores = Math.round( 0.80 * fieldVA" +
              "LUE );\n      } else {\n         var prodCores = Math.round( " +
              "0.50 * fieldVALUE );\n      }\n      document.getElementById(" +
              "updtID).value = prodCores;\n   }\n</SCRIPT>\n")
    print("</BODY>\n</HTML>")

    return



# ########################################################################### #

if __name__ == '__main__':
    #
    os.umask(0o022)
    #
    parserObj = argparse.ArgumentParser(description="Script to display and s" +
        "et the manual LifeStatus, ProdStatus, or CrabStatus override.")
    parserObj.add_argument("-v", action="count", default=0,
                                 help="increase logging verbosity")
    argStruct = parserObj.parse_args()
    #
    # configure message logging:
    logging.addLevelName(25, "NOTICE")
    logging.addLevelName(15, "debug")
    logging.addLevelName(9, "XDEBUG")
    #
    logStream = io.StringIO()
    #
    if ( argStruct.v >= 5 ):
        logLevel = 9
        logFormat = "%(asctime)s [%(levelname).1s] %(message)s"
    elif ( argStruct.v == 4 ):
        logLevel = logging.DEBUG
        logFormat = "%(asctime)s [%(levelname).1s] %(message)s"
    elif ( argStruct.v == 3 ):
        logLevel = 15
        logFormat = "%(asctime)s [%(levelname).1s] %(message)s"
    elif ( argStruct.v == 2 ):
        logLevel = logging.INFO
        logFormat = "[%(levelname).1s] %(message)s"
    elif ( argStruct.v == 1 ):
        logLevel = 25
        logFormat = "[%(levelname).1s] %(message)s"
    else:
        logLevel = logging.WARNING
        logFormat = "[%(levelname).1s] %(message)s"
    #
    logging.basicConfig(datefmt="%Y-%b-%d %H:%M:%S",
                        format=logFormat, level=logLevel, stream=logStream)
    #
    #
    #
    # parse CGI parameters:
    cgiRegex = re.compile("[^a-zA-Z0-9_.=/+*-]")
    #
    cgiMTHD = None
    cgiMTRC = None
    cgiSITE = None
    try:
        cgiMTHD = cgiRegex.sub("", os.environ['REQUEST_METHOD'])
        if ( cgiMTHD == "POST" ):
            cgiLen = min(4096, max(0, int( os.environ['CONTENT_LENGTH'] ) ))
            cgiPOST = urllib.parse.parse_qs( sys.stdin.read(cgiLen) )
        #
        cgiPATH = (cgiRegex.sub("", os.environ['PATH_INFO'] ).split("/") +
                                                        [None, None, None])[:3]
        if ( cgiPATH[0] != "" ):
            cgiMTRC = cgiPATH[0]
            cgiSITE = cgiPATH[1]
        else:
            cgiMTRC = cgiPATH[1]
            cgiSITE = cgiPATH[2]
    except Exception as excptn:
        logging.critical("Failed to decode CGI parameters, %s" % str(excptn))
    #
    logging.debug("CGI parameters: method=%s, path=%s" % (cgiMTHD, cgiPATH))
    #
    #
    #
    # get CGI authorization information:
    authDict = ovrd_auth_cern_sso()
    #
    #
    #
    # write page header:
    ovrd_html_header(cgiMTHD, cgiMTRC, cgiSITE)
    #
    #
    #
    try:
        # get site-to-facility mapping:
        siteFacility = ovrd_cric_facility()
        #
        if ( cgiMTRC == "SiteCapacity" ):
            # get WLCG federation list:
            federationList = ovrd_cric_federation()
            #
            #
            if ( cgiMTHD == "GET" ):
                ovrd_html_capacity(authDict, siteFacility, federationList, cgiSITE)
            elif ( cgiMTHD == "POST" ):
                ovrd_post_capacity(authDict, siteFacility, federationList, cgiSITE, cgiPOST)
        else:
            #
            #
            if ( cgiMTHD == "GET" ):
                ovrd_html_override(authDict ,cgiMTRC, siteFacility, cgiSITE)
            elif ( cgiMTHD == "POST" ):
                ovrd_post_override(authDict, cgiMTRC, siteFacility, cgiSITE, cgiPOST)
        #
    except Exception as excptn:
        logging.critical("CGI execution failure, %s" % str(excptn))
    #
    #
    #
    # shutdown logger:
    logging.shutdown()
    #
    ovrd_html_trailer( cgiMTRC, logStream.getvalue() )

    #import pdb; pdb.set_trace()
