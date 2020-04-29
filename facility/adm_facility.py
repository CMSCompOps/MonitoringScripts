#!/eos/user/c/cmssst/packages/bin/python3.7
# ########################################################################### #
# python CGI script to display theefacility information, allow to change it,  #
#    upload to MonIT, and compile a acknowledgement LaTeX file.               #
#                                                                             #
# 2020-Mar-23   Stephan Lammel                                                #
# ########################################################################### #
#
# PATH_INFO = /FacilityInfo/US_FNAL%20Tier-3
# REQUEST_METHOD = POST
# CONTENT_LENGTH = 16
# 
# ADFS_LOGIN = jonny
# ADFS_FULLNAME = John Doe
# ADFS_GROUP = cms-comp-ops-site-support-team;cms-zh;cms-members;cms-web-access;cms-authorized-users;cms-US_Fermilab-admin;
#
# /eos/home-c/cmssst/www/facility/FacilityInfo.json:
# [
#   { "name": "US_FNAL",
#     "institute": "Fermi National Accelerator Laboratory",
#     "location": "Batavia, Illinois, United States",
#     "timezone": [ "-06:00", "America/Chicago" ],
#     "latex": "Fermi National Accelerator Laboratory, Batavia, USA",
#     "exec": "cms-US_FNAL-exec@cern.ch",
#     "admin": "cms-US_FNAL-admin@cern.ch",
#     "sites": [ "T1_US_FNAL", "T1_US_FNAL_Disk", "T3_US_HEPCloud" ],
#     "who": null,
#     "when": null
#   },
#   { ... }
# ]
#
#
#
import os, sys, shutil
import io
import fcntl
import time, calendar
import json
import gzip
import re
import urllib.request, urllib.parse
import http
import argparse
import logging
#
# setup the Java/HDFS/PATH environment for pydoop to work properly:
os.environ["HADOOP_CONF_DIR"] = "/opt/hadoop/conf/etc/analytix/hadoop.analytix"
os.environ["JAVA_HOME"]       = "/etc/alternatives/jre"
os.environ["HADOOP_PREFIX"]   = "/usr/hdp/hadoop"
# ########################################################################### #



ADMF_CGIURL = "https://test-cmssst.web.cern.ch/cgi-bin/set/FacilityInfo"
#ADMF_CGIURL = "https://test-cmssst.web.cern.ch/cgi-bin/test.sh"
#
ADMF_FACILITY_JSON = "/eos/home-c/cmssst/www/facility/FacilityInfo.json"
ADMF_ACKNWLDG_WORK = "/data/cmssst/MonitoringScripts/facility/"
ADMF_ACKNWLDG_PUBL = "/eos/home-c/cmssst/www/facility/"
ADMF_CACHE = "/eos/home-c/cmssst/www/cache/"
#ADMF_FACILITY_JSON = "./FacilityInfo.json"
#ADMF_ACKNWLDG_WORK = "./junk/"
#ADMF_ACKNWLDG_PUBL = "./"
#ADMF_CACHE = "/afs/cern.ch/user/l/lammel/cms/site_support/monit/cache/"
#
ADMF_AUTH_CMSSST = [ "cms-comp-ops-site-support-team" ]
ADMF_AUTH_VIEW   = [ "cms-zh", "cms-members", "cms-authorized-users" ]
# ########################################################################### #



# pytz is unusably slow, especially from EOS, compile our own static dict:
ADMF_TIMEZONES = { 'AT': [ ( "+00:00", "UTC" ),
                           ( "+01:00", "Europe/Vienna" ) ],
                   'BE': [ ( "+00:00", "UTC" ),
                           ( "+01:00", "Europe/Brussels" ) ],
                   'BG': [ ( "+00:00", "UTC" ),
                           ( "+02:00", "Europe/Sofia" ) ],
                   'BR': [ ( "+00:00", "UTC" ),
                           ( "-02:00", "America/Noronha" ),
                           ( "-03:00", "America/Belem" ),
                           ( "-03:00", "America/Fortaleza" ),
                           ( "-03:00", "America/Recife" ),
                           ( "-03:00", "America/Araguaina" ),
                           ( "-03:00", "America/Maceio" ),
                           ( "-03:00", "America/Bahia" ),
                           ( "-03:00", "America/Sao_Paulo" ),
                           ( "-04:00", "America/Campo_Grande" ),
                           ( "-04:00", "America/Cuiaba" ),
                           ( "-03:00", "America/Santarem" ),
                           ( "-04:00", "America/Porto_Velho" ),
                           ( "-04:00", "America/Boa_Vista" ),
                           ( "-04:00", "America/Manaus" ),
                           ( "-05:00", "America/Eirunepe" ),
                           ( "-05:00", "America/Rio_Branco" ) ],
                   'BY': [ ( "+00:00", "UTC" ),
                           ( "+03:00", "Europe/Minsk" ) ],
                   'CH': [ ( "+00:00", "UTC" ),
                           ( "+01:00", "Europe/Zurich" ) ],
                   'CN': [ ( "+00:00", "UTC" ),
                           ( "+08:00", "Asia/Shanghai" ),
                           ( "+06:00", "Asia/Urumqi" ) ],
                   'DE': [ ( "+00:00", "UTC" ),
                           ( "+01:00", "Europe/Berlin" ),
                           ( "+01:00", "Europe/Busingen" ) ],
                   'EE': [ ( "+00:00", "UTC" ),
                           ( "+02:00", "Europe/Tallinn" ) ],
                   'ES': [ ( "+00:00", "UTC" ),
                           ( "+01:00", "Europe/Madrid" ),
                           ( "+01:00", "Africa/Ceuta" ),
                           ( "+00:00", "Atlantic/Canary" ) ],
                   'FI': [ ( "+00:00", "UTC" ),
                           ( "+02:00", "Europe/Helsinki" ) ],
                   'FR': [ ( "+00:00", "UTC" ),
                           ( "+01:00", "Europe/Paris" ) ],
                   'GR': [ ( "+00:00", "UTC" ),
                           ( "+02:00", "Europe/Athens" ) ],
                   'HR': [ ( "+00:00", "UTC" ),
                           ( "+01:00", "Europe/Zagreb" ) ],
                   'HU': [ ( "+00:00", "UTC" ),
                           ( "+01:00", "Europe/Budapest" ) ],
                   'IN': [ ( "+00:00", "UTC" ),
                           ( "+05:30", "Asia/Kolkata" ) ],
                   'IR': [ ( "+00:00", "UTC" ),
                           ( "+03:30", "Asia/Tehran" ) ],
                   'IT': [ ( "+00:00", "UTC" ),
                           ( "+01:00", "Europe/Rome" ) ],
                   'KR': [ ( "+00:00", "UTC" ),
                           ( "+09:00", "Asia/Seoul" ) ],
                   'LV': [ ( "+00:00", "UTC" ),
                           ( "+02:00", "Europe/Riga" ) ],
                   'MX': [ ( "+00:00", "UTC" ),
                           ( "-06:00", "America/Mexico_City" ),
                           ( "-05:00", "America/Cancun" ),
                           ( "-06:00", "America/Merida" ),
                           ( "-06:00", "America/Monterrey" ),
                           ( "-06:00", "America/Matamoros" ),
                           ( "-07:00", "America/Mazatlan" ),
                           ( "-07:00", "America/Chihuahua" ),
                           ( "-07:00", "America/Ojinaga" ),
                           ( "-07:00", "America/Hermosillo" ),
                           ( "-08:00", "America/Tijuana" ),
                           ( "-06:00", "America/Bahia_Banderas" ) ],
                   'PK': [ ( "+00:00", "UTC" ),
                           ( "+05:00", "Asia/Karachi" ) ],
                   'PL': [ ( "+00:00", "UTC" ),
                           ( "+01:00", "Europe/Warsaw" ) ],
                   'PT': [ ( "+00:00", "UTC" ),
                           ( "+00:00", "Europe/Lisbon" ),
                           ( "+00:00", "Atlantic/Madeira" ),
                           ( "-01:00", "Atlantic/Azores" ) ],
                   'RU': [ ( "+00:00", "UTC" ),
                           ( "+02:00", "Europe/Kaliningrad" ),
                           ( "+03:00", "Europe/Moscow" ),
                           ( "+03:00", "Europe/Kirov" ),
                           ( "+04:00", "Europe/Astrakhan" ),
                           ( "+04:00", "Europe/Volgograd" ),
                           ( "+04:00", "Europe/Saratov" ),
                           ( "+04:00", "Europe/Ulyanovsk" ),
                           ( "+04:00", "Europe/Samara" ),
                           ( "+05:00", "Asia/Yekaterinburg" ),
                           ( "+06:00", "Asia/Omsk" ),
                           ( "+07:00", "Asia/Novosibirsk" ),
                           ( "+07:00", "Asia/Barnaul" ),
                           ( "+07:00", "Asia/Tomsk" ),
                           ( "+07:00", "Asia/Novokuznetsk" ),
                           ( "+07:00", "Asia/Krasnoyarsk" ),
                           ( "+08:00", "Asia/Irkutsk" ),
                           ( "+09:00", "Asia/Chita" ),
                           ( "+09:00", "Asia/Yakutsk" ),
                           ( "+09:00", "Asia/Khandyga" ),
                           ( "+10:00", "Asia/Vladivostok" ),
                           ( "+10:00", "Asia/Ust-Nera" ),
                           ( "+11:00", "Asia/Magadan" ),
                           ( "+11:00", "Asia/Sakhalin" ),
                           ( "+11:00", "Asia/Srednekolymsk" ),
                           ( "+12:00", "Asia/Kamchatka" ),
                           ( "+12:00", "Asia/Anadyr" ) ],
                   'TH': [ ( "+00:00", "UTC" ),
                           ( "+07:00", "Asia/Bangkok" ) ],
                   'TR': [ ( "+00:00", "UTC" ),
                           ( "+03:00", "Europe/Istanbul" ) ],
                   'TW': [ ( "+00:00", "UTC" ),
                           ( "+08:00", "Asia/Taipei" ) ],
                   'UA': [ ( "+00:00", "UTC" ),
                           ( "+03:00", "Europe/Simferopol" ),
                           ( "+02:00", "Europe/Kiev" ),
                           ( "+02:00", "Europe/Uzhgorod" ),
                           ( "+02:00", "Europe/Zaporozhye" ) ],
                   'UK': [ ( "+00:00", "UTC" ),
                           ( "+00:00", "Europe/London" ) ],
                   'US': [ ( "+00:00", "UTC" ),
                           ( "-05:00", "America/New_York" ),
                           ( "-05:00", "America/Detroit" ),
                           ( "-05:00", "America/Kentucky/Louisville" ),
                           ( "-05:00", "America/Kentucky/Monticello" ),
                           ( "-05:00", "America/Indiana/Indianapolis" ),
                           ( "-05:00", "America/Indiana/Vincennes" ),
                           ( "-05:00", "America/Indiana/Winamac" ),
                           ( "-05:00", "America/Indiana/Marengo" ),
                           ( "-05:00", "America/Indiana/Petersburg" ),
                           ( "-05:00", "America/Indiana/Vevay" ),
                           ( "-06:00", "America/Chicago" ),
                           ( "-06:00", "America/Indiana/Tell_City" ),
                           ( "-06:00", "America/Indiana/Knox" ),
                           ( "-06:00", "America/Menominee" ),
                           ( "-06:00", "America/North_Dakota/Center" ),
                           ( "-06:00", "America/North_Dakota/New_Salem" ),
                           ( "-06:00", "America/North_Dakota/Beulah" ),
                           ( "-07:00", "America/Denver" ),
                           ( "-07:00", "America/Boise" ),
                           ( "-07:00", "America/Phoenix" ),
                           ( "-08:00", "America/Los_Angeles" ),
                           ( "-09:00", "America/Anchorage" ),
                           ( "-09:00", "America/Juneau" ),
                           ( "-09:00", "America/Sitka" ),
                           ( "-09:00", "America/Metlakatla" ),
                           ( "-09:00", "America/Yakutat" ),
                           ( "-09:00", "America/Nome" ),
                           ( "-10:00", "America/Adak" ),
                           ( "-10:00", "Pacific/Honolulu" ) ] }
# ########################################################################### #



def admf_cric_facility():
    # ################################################# #
    # return list with all the valid CMS facility names #
    # ################################################# #
    URL_CRIC_FACILITY = "https://cms-cric.cern.ch/api/cms/facility/query/?json"
    #
    facilityRegex = re.compile(r"[A-Z]{2,2}_\w+")

    logging.info("Fetching CMS facility information from CRIC")
    try:
        with urllib.request.urlopen(URL_CRIC_FACILITY) as urlHandle:
            urlCharset = urlHandle.headers.get_content_charset()
            if urlCharset is None:
                urlCharset = "utf-8"
            myData = urlHandle.read().decode( urlCharset )
        #
        # sanity check:
        if ( len(myData) < 4096 ):
            raise ValueError("CRIC facility query result failed sanity check")
        #
        # decode JSON:
        myDict = json.loads( myData )
        del myData
        #
        # loop over entries and add site with facility name:
        facilityList = set()
        for myKey in myDict:
            facility = myDict[myKey]['name'].split(" ")[0]
            if ( facilityRegex.match( facility ) is None ):
                continue
            #
            facilityList.add( facility )
        facilityList = sorted( facilityList )
        #
        #
        # update cache:
        cacheFile = ADMF_CACHE + "/cric_facility.json"
        cacheUpdate = False
        try:
             myAge = time.time() - os.stat(cacheFile).st_mtime
             if ( myAge > 86400 ):
                 cacheUpdate = True
        except FileNotFoundError:
             cacheUpdate = True
        #
        if ( cacheUpdate ):
            jsonString = "["
            commaFlag = False
            for facility in facilityList:
                if commaFlag:
                    jsonString += ",\n"
                else:
                    jsonString += "\n"
                jsonString += "   \"%s\"" % ( facility )
                commaFlag = True
            jsonString += "\n]\n"
            #
            try:
                with open(cacheFile + "_new", "w") as myFile:
                    myFile.write( jsonString )
                os.rename(cacheFile + "_new", cacheFile)
            except:
                pass
            #
            logging.log(25, "Facility list cache updated")
    except Exception as excptn:
        logging.error("Failed to fetch CMS facility information from CRIC: %s"
                                                                 % str(excptn))
        #
        cacheFile = ADMF_CACHE + "/cric_facility.json"
        try:
            with open(cacheFile, "rt") as myFile:
                myData = myFile.read()
            #
            # decode JSON:
            facilityList = json.loads( myData )
            del myData
        except:
            logging.critical("Failed to read facility list cache: %s" %
                                                                   str(excptn))
            raise
        #
    return facilityList
# ########################################################################### #



def admf_read_jsonfile(filepath = None):
    """read JSON list from file and return content as list of dictionaries"""
    # ####################################################################### #
    if filepath is None:
        filepath = ADMF_FACILITY_JSON
    if ( os.path.isfile( filepath ) != True ):
        raise ValueError("Inaccessible JSON file, \"%s\"" % filepath)
    if ( filepath[-5:] != ".json" ):
        raise ValueError("Illegal JSON filename, \"%s\"" % filepath)
    lockpath = filepath[:-4] + "lock"
    logging.info("Fetching facility information, %s" %
                                                    os.path.basename(filepath))

    # acquire lock and read facility file:
    remainWait = 3.0
    while ( remainWait > 0.0 ):
        with open(lockpath, "w") as lckFile:
            try:
                fcntl.lockf(lckFile, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError:
                logging.log(25, "Lock busy, retry in 250 msec")
                time.sleep(0.250)
                remainWait -= 0.250
                continue
            #
            with open(filepath, "rt") as myFile:
                jsonString = myFile.read()
            #
            fcntl.lockf(lckFile, fcntl.LOCK_UN)
            break
    if ( remainWait <= 0.0 ):
        raise TimeoutError("Failed to acquire lock %s" % lckFile)
    #
    # decode JSON:
    facilityList = json.loads( jsonString )
    del jsonString
    #
    # convert list of dictionaries to dictionary of dictionaries:
    facilityDict = {}
    for entry in facilityList:
        if (( 'name' not in entry ) or ( 'institute' not in entry ) or
            ( 'location' not in entry ) or ( 'timezone' not in entry ) or
            ( 'latex' not in entry ) or ( 'exec' not in entry ) or
            ( 'admin' not in entry ) or ( 'sites' not in entry )):
                logging.error("Missing key(s) in facility entry %s of %s" %
                                                        (str(entry), filepath))
                continue
        if ( entry['exec'] == "" ):
            entry['exec'] = None
        if ( entry['admin'] == "" ):
            entry['admin'] = None
        if 'who' not in entry:
            entry['who'] = ""
        if 'when' not in entry:
            entry['when'] = ""
        facilityDict[ entry['name'] ] = entry
    del facilityList

    return facilityDict
# ########################################################################### #



def admf_compose_jsonstring(facilityList):
    """compose JSON string from list of facilities"""
    # ####################################################################### #
    latexTransTable = { 34: "\\\"", 92: "\\\\" }

    jsonString = "["
    commaFlag = False
    #
    for entry in sorted( facilityList, key=lambda e: e['name'] ):
        if commaFlag:
            jsonString += ",\n {\n"
        else:
            jsonString += "\n {\n"
        jsonString += (("   \"name\": \"%s\",\n" +
                        "   \"institute\": \"%s\",\n" +
                        "   \"location\": \"%s\",\n" +
                        "   \"timezone\": [ \"%s\", \"%s\" ],\n" +
                        "   \"latex\": \"%s\",\n") %
                       (entry['name'], entry['institute'], entry['location'],
                        entry['timezone'][0], entry['timezone'][1],
                        entry['latex'].translate( latexTransTable )))
        if (( entry['exec'] is None ) or ( entry['exec'] == "" )):
            jsonString += ("   \"exec\": null,\n")
        else:
            jsonString += ("   \"exec\": \"%s\",\n" % entry['exec'])
        if (( entry['admin'] is None ) or ( entry['admin'] == "" )):
            jsonString += ("   \"admin\": null,\n")
        else:
            jsonString += ("   \"admin\": \"%s\",\n" % entry['admin'])
        #
        commaSiteFlag = False
        jsonString += "   \"sites\": ["
        for site in entry['sites']:
            if commaSiteFlag:
                jsonString += (", \"%s\"" % site)
            else:
                jsonString += (" \"%s\"" % site)
            commaSiteFlag = True
        jsonString += " ],\n"
        #
        if entry['who'] is not None:
            jsonString += ("   \"who\": \"%s\",\n" % entry['who'])
        else:
            jsonString += ("   \"who\": null,\n")
        if entry['when'] is not None:
            jsonString += ("   \"when\": \"%s\"\n }" % entry['when'])
        else:
            jsonString += ("   \"when\": null\n }")
        commaFlag = True
    jsonString += "\n]\n"
    #
    return jsonString
# ########################################################################### #



def admf_update_jsonfile(entry, keepKeyList, filepath = None):
    """update the facility file with a facility entry"""
    # ###################################################################### #
    # name, institute, location, timezone, latex, exec, admin, and sites are #
    # mandatory keys in the dictionary entry.                                #
    # ###################################################################### #
    if filepath is None:
        filepath = ADMF_FACILITY_JSON
    if ( os.path.isfile( filepath ) != True ):
        raise ValueError("Inaccessible JSON file, \"%s\"" % filepath)
    if ( filepath[-5:] != ".json" ):
        raise ValueError("Illegal JSON filename, \"%s\"" % filepath)
    lockpath = filepath[:-4] + "lock"
    #
    facilityRegex = re.compile(r"[A-Z]{2,2}_\w+")

    if (( 'name' not in entry ) or ( 'institute' not in entry ) or
        ( 'location' not in entry ) or ( 'timezone' not in entry ) or
        ( 'latex' not in entry ) or ( 'exec' not in entry ) or
        ( 'admin' not in entry ) or ( 'sites' not in entry )):
            logging.error("Missing key(s) in facility entry %s for %s" %
                                                        (str(entry), filepath))
            return {}
    if ( facilityRegex.match( entry['name'] ) is None ):
        logging.error("Illegal facility name %s" % entry['name'])
        return {}
    facility = entry['name']
    try:
        who = entry['who']
    except KeyError:
        try:
            who = os.environ['ADFS_LOGIN']
        except KeyError:
            who = os.getlogin()
    try:
        when = entry['when']
    except KeyError:
        when = time.strftime("%Y-%b-%d %H:%M:%S", time.gmtime(time.time()))
    #
    logging.info("Updating facility information, %s" %
                                                    os.path.basename(filepath))

    changeDict = { 'name': facility, 'who': who, 'when': when }
    # acquire lock and read override file:
    remainWait = 5.0
    while ( remainWait > 0.0 ):
        with open(lockpath, "w") as lckFile:
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
                with open(filepath, "r+t") as myFile:
                    #
                    jsonString = myFile.read()
                    #
                    facilityList = json.loads( jsonString )
                    #
                    #
                    oldEntry = {}
                    for fclty in facilityList:
                        if ( fclty['name'] == facility ):
                            oldEntry = fclty
                            break
                    for key in keepKeyList:
                         entry[key] = oldEntry[key]
                    for key in entry:
                        if (( key == "name" ) or
                            ( key == "who" ) or ( key == "when" )):
                            continue
                        try:
                            if ( entry[key] == oldEntry[key] ):
                                continue
                            changeDict[key] = (oldEntry[key], entry[key])
                        except KeyError:
                            changeDict[key] = (None, entry[key])
                    #
                    #
                    facilityList = [ e for e in facilityList \
                                                 if ( e['name'] != facility ) ]
                    facilityList.append(entry)
                    #
                    jsonString = admf_compose_jsonstring(facilityList)
                    #
                    myFile.seek(0)
                    myFile.write(jsonString)
                    myFile.truncate()
                    #
                logging.info("Successfully updated facility file %s" %
                                                                      filepath)
            except Exception as excptn:
                logging.error("Failed to update facility file %s, %s" %
                                                       (filepath, str(excptn)))
                return {}
            #
            fcntl.lockf(lckFile, fcntl.LOCK_UN)
            break
    if ( remainWait <= 0.0 ):
        logging.error("Timeout acquiring lock %s" % lckFile)

    return changeDict
# ########################################################################### #



def admf_append_log(changeDict, filepath = None):
    """append changeDict entry to the facility log file"""
    # ##################################################################### #
    if filepath is None:
        filepath = ADMF_FACILITY_JSON
    if ( filepath[-5:] != ".json" ):
        raise ValueError("Illegal JSON filename, \"%s\"" % filepath)
    logpath = filepath[:-4] + "log"
    #
    facilityRegex = re.compile(r"[A-Z]{2,2}_\w+")

    if (( 'name' not in changeDict ) or
        ( 'who' not in changeDict ) or ( 'when' not in changeDict )):
        logging.error("Missing key(s) in facility changeDict %s of %s" %
                                                   (str(changeDict), filepath))
        return

    logging.info("Logging update of facility information, %s" %
                                                    os.path.basename(filepath))

    facility = changeDict['name']
    who = changeDict['who']
    when  = changeDict['when']
    #
    del changeDict['name']
    del changeDict['who']
    del changeDict['when']
    #
    try:
        with open(logpath, "at") as myFile:
            #
            logString = "%s\t%s\t%s\t%s\n" % (facility, when, who, 
                                                               str(changeDict))
            #
            myFile.write(logString)
            #
        logging.info("Successfully appended entry to log file %s" % logpath)
    except Exception as excptn:
        logging.error("Failed to update facility log file %s, %s" %
                                                        (logpath, str(excptn)))

    return
# ########################################################################### #



def admf_compose_json(facilityDict, time15bin):
    """function to compose a JSON string from the facilities dictionary"""
    # ############################################################# #
    # compose a JSON string from the facilities dictionary provided #
    # ############################################################# #
    latexTransTable = { 34: "\\\"", 92: "\\\\" }


    # convert facility dictionary into JSON document array string:
    # ============================================================
    jsonString = "["
    commaFlag = False
    #
    timestamp = ( time15bin * 900 ) + 450
    hdrString = ((",\n {\n   \"producer\": \"cmssst\",\n" +
                         "   \"type\": \"ssbmetric\",\n" +
                         "   \"path\": \"facil15min\",\n" +
                         "   \"timestamp\": %d000,\n" +
                         "   \"type_prefix\": \"raw\",\n" +
                         "   \"data\": {\n") % timestamp)
    #
    for myName in sorted( facilityDict.keys() ):
        myEntry = facilityDict[myName]
        #
        if commaFlag:
            jsonString += hdrString
        else:
            jsonString += hdrString[1:]
        if ( myEntry['exec'] is None ):
            myExec = ""
        else:
            myExec = myEntry['exec']
        if ( myEntry['admin'] is None ):
            myAdmin = ""
        else:
            myAdmin = myEntry['admin']
        jsonString += (("      \"name\": \"%s\",\n" +
                        "      \"institute\": \"%s\",\n" +
                        "      \"location\": \"%s\",\n" +
                        "      \"timezone\": [ \"%s\", \"%s\" ],\n" +
                        "      \"latex\": \"%s\",\n" +
                        "      \"exec\": \"%s\",\n" +
                        "      \"admin\": \"%s\",\n") %
                       (myEntry['name'], myEntry['institute'],
                        myEntry['location'],
                        myEntry['timezone'][0], myEntry['timezone'][1],
                        myEntry['latex'].translate( latexTransTable ),
                        myExec, myAdmin))
        #
        commaSiteFlag = False
        jsonString += "      \"sites\": ["
        for mySite in myEntry['sites']:
            if commaSiteFlag:
                jsonString += (", \"%s\"" % mySite)
            else:
                jsonString += (" \"%s\"" % mySite)
            commaSiteFlag = True
        jsonString += " ],\n"
        #
        if myEntry['who'] is not None:
            jsonString += ("      \"who\": \"%s\",\n" % myEntry['who'])
        else:
            jsonString += ("      \"who\": null,\n")
        if myEntry['when'] is not None:
            jsonString += ("      \"when\": \"%s\"\n }" % myEntry['when'])
        else:
            jsonString += ("      \"when\": null\n   }\n }")
        commaFlag = True
    jsonString += "\n]\n"

    return jsonString



def admf_monit_upload(facilityDict, time15bin):
    """function to upload FacilityInfo metric(s) to MonIT/HDFS"""
    # ################################################################# #
    # upload FacilityInfo information as JSON metric documents to MonIT #
    # ################################################################# #
    #MONIT_URL = "http://monit-metrics.cern.ch:10012/"
    MONIT_URL = "http://fail.cern.ch:10001/"
    MONIT_HDR = {'Content-Type': "application/json; charset=UTF-8"}
    #
    logging.info("Composing FacilityInfo JSON array and uploading to MonIT")


    # compose JSON array string:
    # ==========================
    jsonString = admf_compose_json(facilityDict, time15bin)
    if ( jsonString == "[\n]\n" ):
        logging.warning("skipping upload of document-devoid JSON string")
        return False
    cnt_docs = jsonString.count("\"producer\": \"cmssst\"")
    #
    jsonString = jsonString.replace("ssbmetric", "metrictest")


    # upload string with JSON document array to MonIT/HDFS:
    # =====================================================
    docs = json.loads(jsonString)
    ndocs = len(docs)
    successFlag = True
    for myOffset in range(0, ndocs, 4096):
        if ( myOffset > 0 ):
            # give importer time to process documents
            time.sleep(1.500)
        # MonIT upload channel can handle at most 10,000 docs at once
        dataString = json.dumps( docs[myOffset:min(ndocs,myOffset+4096)] )
        #
        try:
            # MonIT needs a document array and without newline characters:
            requestObj = urllib.request.Request(MONIT_URL,
                         data=dataString.encode("utf-8"),
                         headers=MONIT_HDR, method="POST")
            responseObj = urllib.request.urlopen( requestObj, timeout=90 )
            if ( responseObj.status != http.HTTPStatus.OK ):
                logging.error(("Failed to upload JSON [%d:%d] string to MonI" +
                               "T, %d \"%s\"") %
                              (myOffset, min(ndocs,myOffset+4096),
                               responseObj.status, responseObj.reason))
                successFlag = False
            responseObj.close()
        except urllib.error.URLError as excptn:
            logging.error("Failed to upload JSON [%d:%d], %s" %
                             (myOffset, min(ndocs,myOffset+4096), str(excptn)))
            successFlag = False
    del docs

    if ( successFlag ):
        logging.log(25, "JSON array with %d docs uploaded to MonIT" % cnt_docs)
    return successFlag
# ########################################################################### #



def admf_monit_disk(firstTIS, limitTIS):
    """fetch SiteCapacity docs from MonIT/HDFS and return a site list"""
    import pydoop.hdfs
    # ####################################################################### #
    # fetch SiteCapacity docs from MonIT/HDFS covering firstTIS to limitTIS   #
    #       time period and return a list of sites that provided 100 TBytes   #
    #       or more of disk space during that period.                         #
    # SiteCapacity docs are uploaded in 15 minute granularity upon change and #
    #       at the beginning of each day. The time period will be full days   #
    #       and the first half hour of a day before the doc for the day is    #
    #       uploaded we can ignore.                                           #
    # ####################################################################### #
    HDFS_PREFIX = "/project/monitoring/archive/cmssst/raw/ssbmetric/scap15min/"
    #
    first15m = int( firstTIS / 86400 ) * 96
    limit15m = int( limitTIS / 86400 ) * 96
    if ( first15m >= limit15m ):
        logging.critical("Empty time interval for sites to provide disk space")
        return []
    #
    siteRegex = re.compile(r"T\d_[A-Z]{2,2}_\w+")
    #
    logging.info("Retrieving SiteCapacity docs from MonIT HDFS")
    logging.log(15, "   between %s and %s" %
                       (time.strftime("%Y-%m-%d", time.gmtime(first15m * 900)),
                   time.strftime("%Y-%m-%d", time.gmtime((limit15m * 900)-1))))


    # prepare HDFS subdirectory list:
    # ===============================
    dirList = set()
    for dirDay in range((first15m * 900), (limit15m * 900), 86400):
        dirList.add( time.strftime("%Y/%m/%d", time.gmtime(dirDay)) )
    #
    now = int( time.time() )
    sixDaysAgo = calendar.timegm( time.gmtime(now - (6 * 86400)) )
    startLclTmpArea = max( calendar.timegm( time.localtime( sixDaysAgo ) ),
                           calendar.timegm( time.localtime(first15m * 900) ) )
    midnight = ( int( now / 86400 ) * 86400 )
    limitLclTmpArea = calendar.timegm( time.localtime( midnight + 86399 ) )
    for dirDay in range( startLclTmpArea, limitLclTmpArea, 86400):
        dirList.add( time.strftime("%Y/%m/%d.tmp", time.gmtime(dirDay)) )
    #
    dirList = sorted( dirList )


    # connect to HDFS, loop over directories and read status docs:
    # ============================================================
    tmpDict = {}
    try:
        with pydoop.hdfs.hdfs() as myHDFS:
            for subDir in dirList:
                logging.debug("   checking HDFS subdir scap15min/%s" % subDir)
                if not myHDFS.exists( HDFS_PREFIX + subDir ):
                    continue
                # get list of files in directory:
                myList = myHDFS.list_directory( HDFS_PREFIX + subDir )
                fileNames = [ d['name'] for d in myList
                              if (( d['kind'] == "file" ) and
                                  ( d['size'] != 0 )) ]
                del myList
                for fileName in fileNames:
                    logging.debug("   reading file %s" %
                                                    os.path.basename(fileName))
                    fileHndl = fileObj = None
                    try:
                        if ( os.path.splitext(fileName)[-1] == ".gz" ):
                            fileHndl = myHDFS.open_file(fileName)
                            fileObj = gzip.GzipFile(fileobj=fileHndl)
                        else:
                            fileObj = myHDFS.open_file(fileName)
                        # read SiteCapacity documents in file:
                        for myLine in fileObj:
                            myJson = json.loads(myLine.decode('utf-8'))
                            try:
                                if ( myJson['metadata']['path'] !=
                                                                 "scap15min" ):
                                    continue
                                tbin = int( myJson['metadata']['timestamp']
                                                                     / 900000 )
                                if (( tbin < first15m ) or
                                    ( tbin >= limit15m )):
                                    continue
                                myData = myJson['data']
                                if (( 'disk_usable' not in myData ) or
                                    ( 'disk_experiment_use' not in myData )):
                                    continue
                                #
                                name = myData['name']
                                vrsn = myJson['metadata']['kafka_timestamp']
                                #
                                value = (vrsn, myData)
                                #
                                if tbin not in tmpDict:
                                    tmpDict[tbin] = {}
                                if name in tmpDict[tbin]:
                                    if ( vrsn <= tmpDict[tbin][name][0] ):
                                        continue
                                tmpDict[tbin][name] = value
                            except KeyError:
                                continue
                    except json.decoder.JSONDecodeError as excptn:
                        logging.error("JSON decoding failure, file %s: %s"
                                                     % (fileName, str(excptn)))
                    except FileNotFoundError as excptn:
                        logging.error("HDFS file not found, %s: %s" %
                                                       (fileName, str(excptn)))
                    except IOError as excptn:
                        logging.error("IOError accessing HDFS file %s: %s"
                                                     % (fileName, str(excptn)))
                    finally:
                        if fileObj is not None:
                            fileObj.close()
                        if fileHndl is not None:
                            fileHndl.close()
    except Exception as excptn:
        logging.error("Failed to fetch SiteCapacity docs from MonIT/HDFS: %s" %
                                                                   str(excptn))


    # integrate provided disk space during time period:
    # =================================================
    myList = sorted( tmpDict.keys() )
    noList = len( myList )
    if ( noList == 0 ):
        logging.error("No SiteCapacity documents found in MonIT/HDFS")
        return []
    integrationDict = {}
    for indx in range( noList ):
        if ( indx == 0 ):
            s15m = first15m
        else:
            s15m = myList[indx]
        if ( indx == (noList - 1) ):
            e15m = limit15m
        else:
            e15m = myList[indx + 1]
        #
        tbin = myList[indx]
        for mySite in tmpDict[tbin]:
            if ( siteRegex.match( mySite ) is None ):
                continue
            myDisk = max( tmpDict[tbin][mySite][1]['disk_usable'],
                          tmpDict[tbin][mySite][1]['disk_experiment_use'] )
            myTime = ( e15m - s15m ) * 900
            #
            if ( mySite in integrationDict ):
                integrationDict[ mySite ] += myDisk * myTime
            else:
                integrationDict[ mySite ] = myDisk * myTime
    siteList = []
    myTime = ( limit15m - first15m ) * 900
    for mySite in sorted( integrationDict.keys() ):
        myDisk = integrationDict[ mySite ] / myTime
        logging.log(25, "Site %s provided %.1f TB disk" % (mySite, myDisk))
        if ( myDisk >= 100.0 ):
            siteList.append( mySite )


    logging.info("   found %d sites providing 100 TB or more" % len(siteList))
    #
    return siteList
# ########################################################################### #



def admf_influxdb_jobmon(firstTIS, limitTIS):
    """sum up CPU usage from MonIT/InfluxDB and return a site list"""
    # ####################################################################### #
    # fetch summed up core usage and count during firstTIS and limitTIS from  #
    #       MonIT/InfluxDB and return a list of sites that provided 100 cores #
    #       or more of CPU during that period.                                #
    # CMS job monitoring information in InfluxDB is aggregated from HTCondor  #
    #       12 minute job snapshots retaining tags. We thus have to sum over  #
    #       the tags that are not of interest and group by site and number of #
    #       cores, the tags of interest.                                      #
    # ####################################################################### #
    URL_INFLUXDB = "https://monit-grafana.cern.ch/api/datasources/proxy/7731/query?db=monit_production_cmsjm&q=SELECT%%20SUM%%28wavg_count%%29%%20FROM%%20%%22long%%22.%%22condor_1d%%22%%20WHERE%%20%%22Status%%22%%20=%%20%%27Running%%27%%20AND%%20time%%20%%3E=%%20%ds%%20and%%20time%%20%%3C%%20%ds%%20GROUP%%20BY%%20%%22RequestCpus%%22%%2C%%20%%22Site%%22"
    HDR_GRAFANA = {'Authorization': "Bearer eyJrIjoiZWRnWXc1bUZWS0kwbWExN011TGNTN2I2S1JpZFFtTWYiLCJuIjoiY21zLXNzYiIsImlkIjoxMX0=", 'Content-Type': "application/x-www-form-urlencoded; charset=UTF-8", 'Accept': "application/json"}
    #
    first15m = int( firstTIS / 86400 ) * 96
    limit15m = int( limitTIS / 86400 ) * 96
    if ( first15m >= limit15m ):
        logging.critical("Empty time interval for sites to provide disk space")
        return []
    #
    siteRegex = re.compile(r"T\d_[A-Z]{2,2}_\w+")
    #
    logging.info("Querying InfluxDB about job core usage via Grafana")
    logging.log(15, "   between %s and %s" %
                       (time.strftime("%Y-%m-%d", time.gmtime(first15m * 900)),
                   time.strftime("%Y-%m-%d", time.gmtime((limit15m * 900)-1))))


    # execute query and receive results from InfluxDB:
    # ================================================
    try:
        requestObj = urllib.request.Request((URL_INFLUXDB %
                                             (first15m * 900, limit15m * 900)),
                                            headers=HDR_GRAFANA, method="GET")
        with urllib.request.urlopen( requestObj, timeout=180 ) as responseObj:
            urlCharset = responseObj.headers.get_content_charset()
            if urlCharset is None:
                urlCharset = "utf-8"
            myData = responseObj.read().decode( urlCharset )
            del urlCharset
        #
        # sanity check:
        if ( len(myData) < 1024 ):
            raise ValueError("InfluxDB core usage data failed sanity check")
        #
        # decode JSON:
        myJson = json.loads( myData )
        del myData
    except urllib.error.URLError as excptn:
        logging.error("Failed to query ElasticSearch via Grafana, %s" %
                                                                   str(excptn))
        return []


    # loop over results and integrate core usage by site:
    # ===================================================
    integrationDict = {}
    for myResult in myJson['results']:
        for mySerie in myResult['series']:
            try:
                indx = mySerie['columns'].index("sum")
                mySite = mySerie['tags']['Site']
                if ( siteRegex.match( mySite ) is None ):
                    continue
                myCores = int( mySerie['tags']['RequestCpus'] )
                for myValue in mySerie['values']:
                    myCount = myValue[indx]
                    if ( mySite in integrationDict ):
                        integrationDict[ mySite ] += myCores * myCount
                    else:
                        integrationDict[ mySite ] = myCores * myCount
            except (ValueError, KeyError) as excptn:
                logging.warning("Bad query result entry, skipping, %s" %
                                                                   str(excptn))
                continue
    siteList = []
    myTime = ( limit15m - first15m ) / 96
    for mySite in sorted( integrationDict.keys() ):
        myCPU = integrationDict[ mySite ] / myTime
        logging.log(25, "Site %s provided %.1f CPU cores" % (mySite, myCPU))
        if ( myCPU >= 100.0 ):
            siteList.append( mySite )


    logging.info("   found %d sites providing 100 cores or more" %
                                                                 len(siteList))
    #
    return siteList
# ########################################################################### #



def admf_write_acknowledgement(quarterString, facilityDict, filepath = None):
    """write computing acknowledgement LaTex file"""
    # ####################################################################### #
    ADMF_QRTR_NAMES = {'1': "first", '2': "second", '3': "third", '4': "fourth"}
    year, quarter = quarterString.split("q")
    if filepath is None:
        filepath = ADMF_ACKNWLDG_WORK + "compack_" + quarterString + ".tex"
    logging.info("Writing LaTex acknowledgement file for %s, %s" %
                                                     (quarterString, filepath))

    latexStrng = ("%LaTeX\n\\documentclass[12pt]{article}\n\\usepackage{wrap" +
                  "fig}\n\\usepackage{graphicx}\n%\n\\textheight 648pt\n\\to" +
                  "pmargin 16pt\n\\oddsidemargin -8pt\n\\textwidth 480pt\n%" +
                  "\n\\begin{document}\n\\pagestyle{empty}\n\n\\begin{wrapfi" +
                  "gure}[3]{r}{0.16\\textwidth}\n   \\centering\n   \\includ" +
                  "egraphics[width=0.16\\textwidth]{cms_color.eps}\n\\end{wr" +
                  "apfigure}\n\n\\hspace{1 em}\\\\\n\n{\\LARGE \\bf \\noinde" +
                  "nt CMS Computing Acknowledgements}\\\\\n\n\\vspace{10 ex}" +
                  "\n\n\\noindent\n")
    latexStrng += ("The Compact Muon Solenoid (CMS) experiment is a truly in" +
                   "ternational\nendeavour. During operation of the Large Ha" +
                   "dron Collider (LHC) CMS\nrecords close to one hundred TB" +
                   "ytes per day. The collision data need\nto be processed t" +
                   "o reconstruct physics quantities, detector responses\nne" +
                   "ed to be simulated, and all those data analysed. Algorth" +
                   "ms are\nsteadily improved and shutdown periods of the LH" +
                   "C used to reprocess\nand reanalyse existing data. CMS us" +
                   "es grid technologies to accomplish\nthese very CPU-inten" +
                   "sive activities. The distributed computing\ninfrastructu" +
                   "re of CMS encompasses over 60 computing centers around\n" +
                   "the world. Many resources are pledged as part of the Wor" +
                   "ldwide LHC\nComputing Grid (WLCG) project. Additional re" +
                   "sources of the European\nGrid Infrastructure (EGI) and O" +
                   "pen Science Grid (OSG) organizations\nare contributed be" +
                   "yond the pledge or used opportunistically by CMS.\n\nWe " +
                   "thank all data centers, institutes, universities, and re" +
                   "source\nproviders for their support! The organizations b" +
                   "elow have contributed\nsignificantly to the CMS computin" +
                   "g grid in the %s quarter of %s.\n") % \
                                               (ADMF_QRTR_NAMES[quarter], year)

    latexStrng += "\n\\vspace{4 ex}\n\n{\\parindent 0pt"
    facilityList = sorted( facilityDict.keys() )
    prevCountry = facilityList[0][:2]
    for myFacility in facilityList:
        myCountry = myFacility[:2]
        if ( myCountry == prevCountry ):
            latexStrng += ("\n%s\\\\" % facilityDict[myFacility]['latex'])
        else:
            latexStrng += ("[0.5 ex]\n%s\\\\" %
                                             facilityDict[myFacility]['latex'])
        prevCountry = myCountry
    latexStrng += "\n}\n\n\\end{document}\n"


    with open(filepath, "wt") as myFile:
        myFile.write( latexStrng )


    logging.log(25, "LaTex acknowledgement file written with %d facilities" %
                                                             len(facilityList))
    return
# ########################################################################### #



def admf_latex_acknowledgement(quarterString, filepath = None):
    """run latex on a the acknowledgement file and generate a PDF file"""
    # ####################################################################### #
    if filepath is None:
        filepath = ADMF_ACKNWLDG_WORK + "compack_" + quarterString + ".tex"
    if ( filepath[-4:] != ".tex" ):
        raise ValueError("Illegal LaTex filename, \"%s\"" % filepath)
    #
    workdir = os.path.dirname(filepath)
    if ( workdir == "" ):
        workdir = "./"
    filename = os.path.basename(filepath)
    dvipath = filepath[:-3] + "dvi"
    pdfpath = filepath[:-3] + "pdf"
    pubpath = ADMF_ACKNWLDG_PUBL + os.path.basename(pdfpath)
    #
    logging.info("Generating PDF file from LaTeX file, %s" % filepath)


    # generate DVI file:
    # ==================
    myRC = os.system("cd %s; /usr/bin/latex %s 1>/dev/null" %
                                                           (workdir, filename))
    if ( myRC != 0 ):
        logging.error("First LaTeX run failed with rc=%d" % myRC)
    myRC = os.system("cd %s; /usr/bin/latex %s 1>/dev/null" %
                                                           (workdir, filename))
    if ( myRC != 0 ):
        logging.error("Second LaTeX run failed with rc=%d" % myRC)


    # generate PDF file:
    # ==================
    myRC = os.system("/usr/bin/dvipdf %s %s 1>/dev/null" % (dvipath, pdfpath))
    if ( myRC != 0 ):
        logging.error("DVI to PDF conversion failed with rc=%d" % myRC)


    # publish PDF file:
    # =================
    shutil.copyfile(pdfpath, pubpath)


    mySize = os.stat(pubpath).st_size
    logging.log(25, "PDF file generated, %d Bytes, %s" % (mySize, pubpath))
    return
# ########################################################################### #



def admf_html_header(cgiMTHD, cgiFACLTY):
    """write head of HTML page to stdout"""
    # ####################################################################### #
    ADMF_TITLE = "Facility Information View/Update"

    if (( cgiMTHD == "POST" ) and ( cgiFACLTY is not None )):
        myTitle = ADMF_TITLE + " for " + cgiFACLTY
    else:
        myTitle = ADMF_TITLE
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



def admf_html_facility(facilityList, cgiFACLTY):
    """write main section of HTML capacity page to stdout"""
    # ####################################################################### #
    latexTransTable = { 34: "&quot;" }
    #
    ADMF_NOENTRY = { 'name': None,
                     'institute': "unknown",
                     'location': "",
                     'timezone': [ "+00:00", "UTC" ],
                     'latex': "",
                     'exec': None,
                     'admin': None,
                     'sites': [],
                     'who': "nobody",
                     'when': "never" }


    # check authorization:
    # ====================
    authCmsst = False
    authExec = []
    authAdmin = []
    authView = False
    #
    grpList = [e for e in os.environ['ADFS_GROUP'].split(";") if ( e != "" ) ]
    #
    print(("<TABLE>\n<TR>\n   <TD VALIGN=\"top\" NOWRAP><B>%s</B> &nbsp;\n  " +
           " <TD VALIGN=\"top\" NOWRAP><B>e-group</B> member of &nbsp;\n   <" +
           "TD VALIGN=\"top\" NOWRAP>") % os.environ['ADFS_FULLNAME'])
    frstFlag = True
    for group in grpList:
        if ( group in ADMF_AUTH_CMSSST ):
            authView = True
            authCmsst = True
            descripton = "allows to change all"
        elif ( group in ADMF_AUTH_VIEW ):
            authView = True
            descripton = "allows to view all"
        elif ( len(group) >= 13 ):
            if (( group[:4] == "cms-" ) and
                ( group[4:6].isupper() == True ) and
                ( group[6] == "_" )):
                if ( group[-5:] == "-exec" ):
                    authExec.append( group[4:-5] )
                    descripton = "allows to change %s" % group[4:-5]
                elif ( group[-6:] == "-admin" ):
                    authAdmin.append( group[4:-6] )
                    descripton = "allows to view %s" % group[4:-6]
                else:
                    continue
            else:
                continue
        else:
            continue
        if ( frstFlag ):
            print("%s &nbsp; <I>(%s)</I>" % (group, descripton))
        else:
            print("<BR>\n%s &nbsp; <I>(%s)</I>" % (group, descripton))
        frstFlag = False
    print("</TABLE>\n<BR>\n<P>\n\n")


    if cgiFACLTY is not None:
        displayList = [ cgiFACLTY ]
    else:
        displayList = sorted( facilityList )


    if (( authView ) or ( len(authExec) >= 1 ) or ( len(authAdmin) >= 1 )):
        facilityDict = admf_read_jsonfile()


        print("<TABLE BORDER=\"0\" CELLPADDING=\"2\" CELLSPACING=\"1\">\n<TR" +
              ">\n   <TH STYLE=\"text-align: left; font-size: larger;\">CMS " +
              "Facility:\n   <TH STYLE=\"text-align: left; font-size: larger" +
              ";\">Facility Information:")
        #
        for facility in displayList:
            if (( authView == False ) and 
                ( facility not in authExec ) and
                ( facility not in authAdmin )):
                continue

            if facility in facilityDict:
                entry = facilityDict[facility]
            else:
                entry = ADMF_NOENTRY.copy()
                entry['name'] = facility
                entry['institute'] = facility[3:]
                entry['exec'] = "cms-" + facility + "-exec@cern.ch"
                entry['admin'] = "cms-" + facility + "-admin@cern.ch"
            #
            if (( authCmsst == False ) and ( facility not in authExec )):
                bckgnd = "#F4F4F4"
            else:
                bckgnd = "#FFFFFF"
            #
            print(("<TR HEIGHT=\"3\">\n   <TD COLSPAN=\"2\" STYLE=\"backgrou" +
                   "nd-color: black\">\n" +
                   "<TR style=\"background-color: %s; line-height: 175%%;\">" +
                   "\n   <TD VALIGN=\"top\" NOWRAP><B>%s</B>&nbsp;\n   <TD V" +
                   "ALIGN=\"top\" NOWRAP>\n       <FORM METHOD=\"POST\" ENCT" +
                   "YPE=\"application/x-www-form-urlencoded\" action=\"%s/%s" +
                   "\">\n      <TABLE BORDER=\"0\" CELLPADDING=\"1\" CELLSPA" +
                   "CING=\"1\">\n      <TR>\n         <TD NOWRAP>Institute:&" +
                   "nbsp;\n         <TD NOWRAP><INPUT TYPE=\"text\" MAXLENGT" +
                   "H=\"128\" SIZE=\"64\" NAME=\"institute\" VALUE=\"%s\">\n" +
                   "      <TR>\n         <TD NOWRAP>Location:&nbsp;\n       " +
                   "  <TD NOWRAP><INPUT TYPE=\"text\" MAXLENGTH=\"128\" SIZE" +
                   "=\"64\" NAME=\"location\" VALUE=\"%s\">\n      <TR>\n   " +
                   "      <TD NOWRAP>Timezone:&nbsp;\n         <TD><SELECT N" +
                   "AME=\"timezone\">") % (bckgnd, entry['name'], ADMF_CGIURL,
                         entry['name'], entry['institute'], entry['location']))
            #
            #try:
            #    timezoneList = pytz.country_timezones[ facility[:2] ]
            #except KeyError:
            #    timezoneList = [ "UTC" ]
            #noDayLightSavingsDate = datetime.datetime(1916,1,1)
            #for timezoneName in timezoneList:
            #    myTzone = pytz.timezone( timezoneName )
            #    ndls_date = myTzone.localize( noDayLightSavingsDate )
            #    myOffset = ndls_date.strftime('%z')
            #    #
            #    if ( timezoneName == entry['timezone'][1] ):
            #        mySelected = " SELECTED"
            #    else:
            #        mySelected = ""
            #    print(("            <OPTION VALUE=\"%s\"%s>%s:%s &nbsp; %s</" +
            #           "OPTION>") % (timezoneName, mySelected,
            #                        myOffset[:3], myOffset[-2:], timezoneName))
            #
            try:
                timezoneList = ADMF_TIMEZONES[ entry['name'][:2] ]
            except KeyError:
                timezoneList = [ ( "+00:00", "UTC" ) ]
            for tzEntry in timezoneList:
                if ( tzEntry[1] == entry['timezone'][1] ):
                    mySelected = " SELECTED"
                else:
                    mySelected = ""
                print(("            <OPTION VALUE=\"%s\"%s>%s &nbsp; %s</OPT" +
                       "ION>") % (tzEntry[1], mySelected,
                                                       tzEntry[0], tzEntry[1]))
            #
            if ( entry['exec'] is None ):
                myExec = ""
            else:
                myExec = entry['exec']
            if ( entry['admin'] is None ):
                myAdmin = ""
            else:
                myAdmin = entry['admin']
            mySites = ""
            for mySite in entry['sites']:
                mySites += " %s" % mySite
            mySites = mySites[1:]
            if ( authCmsst ):
                myReadonly = ""
                myDisabled = ""
            elif ( facility in authExec ):
                myReadonly = " READONLY"
                myDisabled = ""
            else:
                myReadonly = " READONLY"
                myDisabled = " DISABLED"
            if (( "when" not in entry ) or
                ( entry['when'] is None ) or
                ( entry['when'] == "" )):
                myWhen = ADMF_NOENTRY['when']
            else:
                myWhen = entry['when']
            if (( "who" not in entry ) or
                ( entry['who'] is None ) or
                ( entry['who'] == "" )):
                myWho = ADMF_NOENTRY['who']
            else:
                myWho = entry['who']
            print(("            </SELECT>\n      <TR>\n         <TD NOWRAP>L" +
                   "atex:&nbsp;\n         <TD NOWRAP><INPUT TYPE=\"text\" MA" +
                   "XLENGTH=\"192\" SIZE=\"64\" NAME=\"latex\" VALUE=\"%s\">" +
                   "\n      <TR>\n         <TD NOWRAP>Execs:&nbsp;\n        " +
                   " <TD NOWRAP><INPUT TYPE=\"text\" MAXLENGTH=\"80\" SIZE=" +
                   "\"64\" NAME=\"exec\" VALUE=\"%s\"%s>\n      <TR>\n      " +
                   "   <TD NOWRAP>Admins:&nbsp;\n         <TD NOWRAP><INPUT " +
                   "TYPE=\"text\" MAXLENGTH=\"80\" SIZE=\"64\" NAME=\"admin" +
                   "\" VALUE=\"%s\"%s>\n      <TR>\n         <TD NOWRAP>Site" +
                   " List:&nbsp;\n         <TD NOWRAP><INPUT TYPE=\"text\" M" +
                   "AXLENGTH=\"128\" SIZE=\"64\" NAME=\"sites\" VALUE=\"%s\"" +
                   "%s>\n      <TR>\n         <TD COLSPAN=\"2\" NOWRAP><INPU" +
                   "T TYPE=\"submit\" VALUE=\"Update Information\" STYLE=\"h" +
                   "eight:28px; width:164px; font-weight: 600; white-space: " +
                   "nowrap; background-color: #B0C0FF;\"%s> (previous update" +
                   ": <I>%s by %s</I>)\n      </TABLE>\n      </FORM>") %
                  (entry['latex'].translate(latexTransTable),
                                       myExec, myReadonly, myAdmin, myReadonly,
                               mySites, myReadonly, myDisabled, myWhen, myWho))
        #
        print("<TR HEIGHT=\"3\">\n   <TD COLSPAN=\"2\" STYLE=\"background-co" +
              "lor: black\">\n</TABLE>\n<BR>\n<P>\n")

    return
# ########################################################################### #



def admf_post_facility(cgiFACLTY, cgiPOST):
    """set capacity and write main section of HTML update page to stdout"""
    # ####################################################################### #
    siteRegex = re.compile(r"T\d_[A-Z]{2,2}_\w+")
    #
    latexTransTable = { 34: "&quot;" }
    #
    ADMF_NOENTRY = { 'name': None,
                     'institute': "unknown",
                     'location': "",
                     'timezone': [ "+00:00", "UTC" ],
                     'latex': "",
                     'exec': None,
                     'admin': None,
                     'sites': [],
                     'who': "nobody",
                     'when': "never" }

    # prepare facility entry:
    facilityEntry = {}
    try:
        facilityEntry['name'] = cgiFACLTY
        facilityEntry['institute'] = cgiPOST['institute'][0]
        facilityEntry['location'] = cgiPOST['location'][0]
        myTimezone = cgiPOST['timezone'][0]
        #noDayLightSavingsDate = datetime.datetime(1916,1,1)
        #try:
        #    myTzone = pytz.timezone( myTimezone )
        #    ndls_date = tzone.localize( noDayLightSavingsDate )
        #    myOffset = ndls_date.strftime('%z')
        #    myOffset = "%s:%s" % (myOffset[:3], myOffset[-2:])
        #except:
        #    myOffset = ADMF_NOENTRY['timezone'][0]
        #    myTimezone = ADMF_NOENTRY['timezone'][1]
        #facilityEntry['timezone'] = [ myOffset, myTimezone ]
        try:
            timezoneList = ADMF_TIMEZONES[ cgiFACLTY[:2] ]
            for tzEntry in timezoneList:
                if ( tzEntry[1] == myTimezone ):
                    break;
            if ( tzEntry[1] == myTimezone ):
                facilityEntry['timezone'] = [ tzEntry[0], tzEntry[1] ]
            else:
                facilityEntry['timezone'] = [ ADMF_NOENTRY['timezone'][0],
                                              ADMF_NOENTRY['timezone'][1] ]
        except:
            facilityEntry['timezone'] = [ ADMF_NOENTRY['timezone'][0],
                                          ADMF_NOENTRY['timezone'][1] ]
        facilityEntry['latex'] = cgiPOST['latex'][0]
        if ( "exec" not in cgiPOST ):
            facilityEntry['exec'] = "cms-" + cgiFACLTY + "-exec@cern.ch"
        elif ( cgiPOST['exec'][0] == "" ):
            facilityEntry['exec'] = None
        else:
            facilityEntry['exec'] = cgiPOST['exec'][0]
        if ( "admin" not in cgiPOST ):
            facilityEntry['admin'] = "cms-" + cgiFACLTY + "-admin@cern.ch"
        elif ( cgiPOST['admin'][0] == "" ):
            facilityEntry['admin'] = None
        else:
            facilityEntry['admin'] = cgiPOST['admin'][0]
        mySitelist = [ e for e in (cgiPOST['sites'][0]).split(" ") \
                                        if ( siteRegex.match(e) is not None ) ]
        facilityEntry['sites'] = sorted( mySitelist )
        facilityEntry['when'] = time.strftime("%Y-%b-%d %H:%M:%S",
                                                      time.gmtime(time.time()))
        facilityEntry['who'] = os.environ['ADFS_LOGIN']
    except (KeyError, IndexError) as excptn:
        logging.critical("Bad CGI data, %s" % str(excptn))
        return


    # check authorization:
    # ====================
    myAuth = None
    exeGroup = "cms-" + cgiFACLTY.split(" ")[0] + "-exec"
    admGroup = "cms-" + cgiFACLTY.split(" ")[0] + "-admin"
    grpList = [e for e in os.environ['ADFS_GROUP'].split(";") if ( e != "" ) ]
    for group in grpList:
        if ( group in ADMF_AUTH_CMSSST ):
            myAuth = "cmssst"
            break
        elif ( group == exeGroup ):
            myAuth = "exec"
        elif (( group == admGroup ) and ( myAuth is None )):
            myAuth = "view"
        elif (( group in ADMF_AUTH_VIEW ) and ( myAuth is None )):
            myAuth = "view"
    if (( myAuth != "cmssst" ) and ( myAuth != "exec" )):
        logging.critical(("User \"%s\" not authorized to change FacilityInfo" +
                          " of CMS facility \"%s\"") % (facilityEntry['who'], 
                                                        facilityEntry['name']))
        return


    # update facility file with new site entry:
    # =========================================
    if ( myAuth == "cmssst" ):
        changeDict = admf_update_jsonfile(facilityEntry, [])
    else:
        changeDict = admf_update_jsonfile(facilityEntry, ["exec", "admin",
                                                                      "sites"])


    # append operation to log file:
    # =============================
    admf_append_log(changeDict)


    # re-read facility file:
    # ======================
    facilityDict = admf_read_jsonfile()

    # write main section of HTML update page:
    print("<TABLE BORDER=\"0\" CELLPADDING=\"2\" CELLSPACING=\"1\">\n<TR>\n " +
          "  <TH STYLE=\"text-align: left; font-size: larger;\">CMS Facility" +
          ":\n   <TH STYLE=\"text-align: left; font-size: larger;\">Facility" +
          " Information:\n")
    #
    if cgiFACLTY in facilityDict:
        entry = facilityDict[ cgiFACLTY ]
    else:
        entry = ADMF_NOENTRY
    #
    print(("<TR HEIGHT=\"3\">\n   <TD COLSPAN=\"2\" STYLE=\"background-color" +
           ": black\">\n" +
           "<TR style=\"background-color: #FFFFFF; line-height: 175%%;\">\n " +
           "  <TD VALIGN=\"top\" NOWRAP><B>%s</B>&nbsp;\n   <TD VALIGN=\"top" +
           "\" NOWRAP>\n       <FORM METHOD=\"POST\" ENCTYPE=\"application/x" +
           "-www-form-urlencoded\" action=\"%s/%s\">\n      <TABLE BORDER=\"" +
           "0\" CELLPADDING=\"1\" CELLSPACING=\"1\">\n      <TR>\n         <" +
           "TD NOWRAP>Institute:&nbsp;\n         <TD NOWRAP><INPUT TYPE=\"te" +
           "xt\" MAXLENGTH=\"128\" SIZE=\"64\" NAME=\"institute\" VALUE=\"%s" +
           "\">\n      <TR>\n         <TD NOWRAP>Location:&nbsp;\n         <" +
           "TD NOWRAP><INPUT TYPE=\"text\" MAXLENGTH=\"128\" SIZE=\"64\" NAM" +
           "E=\"location\" VALUE=\"%s\">\n      <TR>\n         <TD NOWRAP>Ti" +
           "mezone:&nbsp;\n         <TD><SELECT NAME=\"timezone\">") %
          (entry['name'], ADMF_CGIURL, entry['name'], entry['institute'],
                                                            entry['location']))
    #
    #try:
    #    timezoneList = pytz.country_timezones[ cgiFACLTY[:2] ]
    #except KeyError:
    #    timezoneList = [ "UTC" ]
    #noDayLightSavingsDate = datetime.datetime(1916,1,1)
    #for timezoneName in timezoneList:
    #    myTzone = pytz.timezone( timezoneName )
    #    ndls_date = tzone.localize( noDayLightSavingsDate )
    #    myOffset = ndls_date.strftime('%z')
    #    #
    #    if ( timezoneName == entry['timezone'][1] ):
    #        mySelected = " SELECTED"
    #    else:
    #        mySelected = ""
    #    print(("            <OPTION VALUE=\"%s\"%s>%s:%s &nbsp; %s</OPTION>") %
    #          (timezoneName, mySelected, myOffset[:3], myOffset[-2:],
    #                                                             timezoneName))
    #
    try:
        timezoneList = ADMF_TIMEZONES[ entry['name'][:2] ]
    except KeyError:
        timezoneList = [ ( "+00:00", "UTC" ) ]
    for tzEntry in timezoneList:
        if ( tzEntry[1] == entry['timezone'][1] ):
            mySelected = " SELECTED"
        else:
            mySelected = ""
        print(("            <OPTION VALUE=\"%s\"%s>%s &nbsp; %s</OPTION>") %
                              (tzEntry[1], mySelected, tzEntry[0], tzEntry[1]))
    #
    if ( entry['exec'] is None ):
        myExec = ""
    else:
        myExec = entry['exec']
    if ( entry['admin'] is None ):
        myAdmin = ""
    else:
        myAdmin = entry['admin']
    mySites = ""
    for mySite in entry['sites']:
        mySites += " %s" % mySite
    mySites = mySites[1:]
    if ( myAuth == "cmssst" ):
        myReadonly = ""
        myDisabled = ""
    else:
        myReadonly = " READONLY"
        myDisabled = ""
    if (( "when" not in entry ) or
        ( entry['when'] is None ) or
        ( entry['when'] == "" )):
        myWhen = ADMF_NOENTRY['when']
    else:
        myWhen = entry['when']
    if (( "who" not in entry ) or
        ( entry['who'] is None ) or
        ( entry['who'] == "" )):
        myWho = ADMF_NOENTRY['who']
    else:
        myWho = entry['who']
    print(("            </SELECT>\n      <TR>\n         <TD NOWRAP>Latex:&nb" +
           "sp;\n         <TD NOWRAP><INPUT TYPE=\"text\" MAXLENGTH=\"192\" " +
           "SIZE=\"64\" NAME=\"latex\" VALUE=\"%s\">\n      <TR>\n         <" +
           "TD NOWRAP>Execs:&nbsp;\n         <TD NOWRAP><INPUT TYPE=\"text\"" +
           " MAXLENGTH=\"80\" SIZE=\"64\" NAME=\"exec\" VALUE=\"%s\"%s>\n   " +
           "   <TR>\n         <TD NOWRAP>Admins:&nbsp;\n         <TD NOWRAP>" +
           "<INPUT TYPE=\"text\" MAXLENGTH=\"80\" SIZE=\"64\" NAME=\"admin\"" +
           " VALUE=\"%s\"%s>\n      <TR>\n         <TD NOWRAP>Site List:&nbs" +
           "p;\n         <TD NOWRAP><INPUT TYPE=\"text\" MAXLENGTH=\"128\" S" +
           "IZE=\"64\" NAME=\"sites\" VALUE=\"%s\"%s>\n      <TR>\n         " +
           "<TD COLSPAN=\"2\" NOWRAP><INPUT TYPE=\"submit\" VALUE=\"Update I" +
           "nformation\" STYLE=\"height:28px; width:164px; font-weight: 600;" +
           " white-space: nowrap; background-color: #B0C0FF;\"%s> (previous " +
           "update: <I>%s by %s</I>)\n      </TABLE>\n      </FORM>") %
          (entry['latex'].translate(latexTransTable),
                         entry['exec'], myReadonly, entry['admin'], myReadonly,
                               mySites, myReadonly, myDisabled, myWhen, myWho))
    #
    print("<TR HEIGHT=\"3\">\n   <TD COLSPAN=\"2\" STYLE=\"background-color:" +
          " black\">\n</TABLE>\n<BR>\n<P>\n")

    return
# ########################################################################### #



def admf_html_trailer(msgLog):
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
    print("</BODY>\n</HTML>")

    return
# ########################################################################### #



def admf_make_tzlist():
    import  pytz, datetime
    ADMF_COUNTRIES = [ "AT", "BE", "BG", "BR", "BY", "CH", "CN", "DE", "EE",
                       "ES", "FI", "FR", "GR", "HR", "HU", "IN", "IR", "IT",
                       "KR", "LV", "MX", "PK", "PL", "PT", "RU", "TH", "TR",
                       "TW", "UA", "UK", "US" ]
    # no CMS sites in southern hemisphere with daylight-savings timezone
    noDayLightSavingsDate = datetime.datetime(2020,1,1)
    print("ADMF_TIMEZONES = {")
    for myCC in ADMF_COUNTRIES:
        myTZ = myCC
        if ( myTZ == "UK" ):
            myTZ = "GB"
        timezoneList = pytz.country_timezones[ myTZ ]
        print("                   '%s': [ ( \"+00:00\", \"UTC\" )" % myCC,
                                                                        end="")
        for timezoneName in timezoneList:
            myTzone = pytz.timezone( timezoneName )
            ndls_date = myTzone.localize( noDayLightSavingsDate )
            myOffset = ndls_date.strftime('%z')
            print(",\n                           ( \"%s:%s\", \"%s\" )" %
                           (myOffset[:3], myOffset[-2:], timezoneName), end="")
        print(" ],")
    print("                 }")
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
    parserObj.add_argument("-u", dest="upload", default=False,
                                 action="store_true",
                                 help="upload facility information to MonIT")
    parserObj.add_argument("-a", dest="acknowledge", action="store",
                                 default=None, const="", nargs="?",
                                 metavar="YYYYqN",
                                 help=("compile acknowledgement LaTeX file f" +
                                       "or previous (or specified) quarter"))
    parserObj.add_argument("-T", dest="timezone", default=False,
                                 action="store_true",
                                 help=argparse.SUPPRESS)
    argStruct = parserObj.parse_args()
    #
    # configure message logging:
    logging.addLevelName(25, "NOTICE")
    logging.addLevelName(15, "debug")
    logging.addLevelName(9, "XDEBUG")
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
    if argStruct.acknowledge is None:
        logStream = io.StringIO()
        #
        logging.basicConfig(datefmt="%Y-%b-%d %H:%M:%S",
                            format=logFormat, level=logLevel, stream=logStream)
    else:
        logging.basicConfig(datefmt="%Y-%b-%d %H:%M:%S",
                            format=logFormat, level=logLevel)
    #
    #
    #
    if ( argStruct.timezone ):
        admf_make_tzlist()
    elif ( argStruct.upload ):
        #
        now15m = int( time.time() / 900 )
        #
        # read current FacilityInfo:
        facilityDict = admf_read_jsonfile()
        #
        # upload SiteCapacity data as needed:
        admf_monit_upload( facilityDict, now15m )
        #
    elif argStruct.acknowledge is not None:
        if ( argStruct.acknowledge  == "" ):
            myYear, myMonth = time.gmtime( time.time() )[0:2]
            myQuarter = int( (myMonth - 1) / 3 ) + 1
            if ( myQuarter == 1 ):
                previousQuarter = "%4.4dq$1.1d" % (myYear - 1, 4)
            else:
                previousQuarter = "%4.4dq%1.1d" % (myYear, myQuarter - 1)
        else:
            # argument should be the quarter in YYYYqN format
            previousQuarter = argStruct.acknowledge
        prevYear = int( previousQuarter.split("q")[0] )
        prevQuarter = int( previousQuarter.split("q")[1] )
        prevMonth = ( (prevQuarter - 1) * 3 ) + 1
        frstDay = int( calendar.timegm( time.strptime("%d-%2.2d-01 UTC" %
                                      (prevYear, prevMonth), "%Y-%m-%d %Z") ) )
        if ( prevQuarter == 4 ):
            nxtYear = prevYear + 1
            nxtMonth = 1
        else:
            nxtYear = prevYear
            nxtMonth = prevMonth + 3
        nextDay = int( calendar.timegm( time.strptime("%d-%2.2d-01 UTC" %
                                        (nxtYear, nxtMonth), "%Y-%m-%d %Z") ) )
        #
        #
        # get list of sites contributing disk space:
        # ==========================================
        diskList = admf_monit_disk(frstDay, nextDay)
        #
        #
        # get list of sites contributing computing:
        # =========================================
        compList = admf_influxdb_jobmon(frstDay, nextDay)
        #
        #
        siteList = sorted( set( diskList + compList ) )
        logging.log(25, "Sites contributing: %s" % str(siteList))
        #
        #
        facilityDict = admf_read_jsonfile()
        #
        for myFacility in sorted( facilityDict.keys() ):
            keepFlag = False
            for mySite in facilityDict[myFacility]['sites']:
                if mySite in siteList:
                    keepFlag = True
                    break
            if (( keepFlag == False ) or
                ( facilityDict[myFacility]['latex'] == "" )):
                del facilityDict[myFacility]
        #
        admf_write_acknowledgement( previousQuarter, facilityDict )
        admf_latex_acknowledgement( previousQuarter )
    else:
        #
        # parse CGI parameters:
        cgiRegex = re.compile("[^a-zA-Z0-9_.=/+*-]")
        #
        cgiMTHD = None
        cgiFACLTY = None
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
                cgiFACLTY = cgiPATH[1]
            else:
                cgiMTRC = cgiPATH[1]
                cgiFACLTY = cgiPATH[2]
            if ( cgiMTRC != "FacilityInfo" ):
                raise ValueError("Unsupported metric \"%s\"" % cgiMTRC)
            if (( cgiMTHD == "POST" ) and ( cgiFACLTY is None )):
                raise ValueError("Missing CMS facility name")
        except Exception as excptn:
            logging.critical("Failed to decode CGI parameters, %s" %
                                                                   str(excptn))
        #
        logging.debug("CGI parameters: method=%s, path=%s" % (cgiMTHD, cgiPATH))
        #
        #
        #
        # write page header:
        admf_html_header(cgiMTHD, cgiFACLTY)
        #
        #
        #
        try:
            # get list of all facilities:
            facilityList = admf_cric_facility()
            #
            #
            if (( cgiFACLTY is not None ) and
                ( cgiFACLTY not in facilityList )):
                    raise ValueError("Unknown CMS facility name \"%s\"" %
                                                                     cgiFACLTY)
            #
            #
            if ( cgiMTHD == "GET" ):
                admf_html_facility(facilityList, cgiFACLTY)
            elif ( cgiMTHD == "POST" ):
                admf_post_facility(cgiFACLTY, cgiPOST)
        except Exception as excptn:
            logging.critical("CGI execution failure, %s" % str(excptn))
        #
        #
        #
        # shutdown logger:
        logging.shutdown()
        #
        admf_html_trailer( logStream.getvalue() )

    #import pdb; pdb.set_trace()
