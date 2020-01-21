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
# /eos/home-c/cmssst/www/override/CrabStatus.json:
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
    'LifeStatus': { 'cms-zh':                         "",
                    'cms-members':                    "",
                    'cms-authorized-users':           "",
                    'cms-comp-ops':                   "",
                    'cms-comp-ops-site-support-team': "ALL" },
    'ProdStatus': { 'cms-zh':                         "",
                    'cms-members':                    "",
                    'cms-authorized-users':           "",
                    'cms-comp-ops':                   "",
                    'cms-comp-ops-workflow-team':     "ALL",
                    'cms-tier0-operations':           ["T0_CH_CERN",
                                                       "T2_CH_CERN",
                                                       "T2_CH_CERN_HLT" ],
                    'cms-comp-ops-site-support-team': "ALL" },
    'CrabStatus': { 'cms-zh':                         "",
                    'cms-members':                    "",
                    'cms-authorized-users':           "",
                    'cms-comp-ops':                   "",
                    'cms-service-crab3htcondor':      "ALL",
                    'cms-tier0-operations':           ["T0_CH_CERN",
                                                       "T2_CH_CERN_HLT" ],
                    'cms-comp-ops-site-support-team': "ALL" }
}
OVRD_STATUS_NAME = {
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
OVRD_MODE_NAME = {
    'LifeStatus': [ "latched", "oneday", "toggle" ],
    'ProdStatus': [ "latched", "oneday", "toggle" ],
    'CrabStatus': [ "latched", "oneday", "toggle" ]
}
OVRD_FILE_PATH = {
    'LifeStatus': "/eos/home-c/cmssst/www/override/LifeStatus.json",
    'ProdStatus': "/eos/home-c/cmssst/www/override/ProdStatus.json",
    'CrabStatus': "/eos/home-c/cmssst/www/override/CrabStatus.json"
}
OVRD_CGIURL = "https://test-cmssst.web.cern.ch/cgi-bin/set"
#
OVRD_CACHE = "/eos/user/c/cmssst/www/cache"
#
#OVRD_LOCK = "./cache/status.lock"
OVRD_LOCK = "/eos/home-c/cmssst/www/override/status.lock"
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



def ovrd_read_override(cgiMTRC):
    """read override file and return contents as dictionary of dictionaries"""
    # ####################################################################### #

    if cgiMTRC not in OVRD_FILE_PATH:
        raise ValueError("Unsupported metric \"%s\"" % cgiMTRC)
    filename = OVRD_FILE_PATH[cgiMTRC]

    logging.info("Fetching man override information, %s" %
                                                    os.path.basename(filename))
    # acquire lock and read override file:
    remainWait = 3.0
    while ( remainWait > 0.0 ):
        with open(OVRD_LOCK, 'w') as lckFile:
            try:
                fcntl.lockf(lckFile, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError:
                logging.log(25, "Lock busy, retry in 250 msec")
                sleep(0.250)
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



def ovrd_update_override(cgiMTRC, entry):
    """update the override file with a site entry"""
    # ##################################################################### #
    # name, status, and mode are mandatory keys in the dictionary entry. If #
    # status is set to None the existing entry of the site in the file will #
    # be removed.                                                           #
    # ##################################################################### #
    siteRegex = re.compile(r"T\d_[A-Z]{2,2}_\w+")

    if cgiMTRC not in OVRD_FILE_PATH:
        logging.error("Unsupported metric \"%s\"" % cgiMTRC)
        return
    filename = OVRD_FILE_PATH[cgiMTRC]
    #
    if (( 'name' not in entry ) or ( 'status' not in entry ) or
        ( 'mode' not in entry )):
        logging.error("Missing key(s) in override entry %s of %s" %
                                                        (str(entry), filename))
        return
    elif ( siteRegex.match( entry['name'] ) is None ):
        logging.error("Illegal site name %s" % entry['name'])
        return
    site = entry['name']

    logging.info("Updating man override information, %s" %
                                                    os.path.basename(filename))
    # acquire lock and read override file:
    remainWait = 5.0
    while ( remainWait > 0.0 ):
        with open(OVRD_LOCK, 'w') as lckFile:
            try:
                fcntl.lockf(lckFile, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError:
                logging.log(25, "Lock busy, retry in 250 msec")
                sleep(0.250)
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
                    if entry['status'] is not None:
                        overrideList.append(entry)
                    #
                    jsonString = ovrd_compose_override(overrideList)
                    #
                    myFile.seek(0)
                    myFile.write(jsonString)
                    myFile.truncate()
                    #
                logging.info("Successfully updated override file %s" %
                                                                      filename)
            except Exception as excptn:
                logging.error("Failed to update override file %s, %s" %
                                                       (filename, str(excptn)))
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
    if (( 'name' not in entry ) or ( 'status' not in entry ) or
        ( 'mode' not in entry )):
        logging.error("Missing key(s) in override entry %s of %s" %
                                                        (str(entry), filename))
        return
    elif ( siteRegex.match( entry['name'] ) is None ):
        logging.error("Illegal site name %s" % entry['name'])
        return
    site = entry['name']
    if (( entry['status'] is None ) or ( entry['status'] == "" )):
        status = "auto"
        mode = "none"
    else:
        status = entry['status']
        mode = entry['mode']

    logging.info("Updating man override information, %s" %
                                                    os.path.basename(filename))

    try:
        with open(filename, 'at') as myFile:
            #
            logString = "%s\t%s\t%s\t%s\t%s\t%s\n" % (site, status, mode,
                                     entry['when'], entry['who'], entry['why'])
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



def ovrd_html_header(cgiMTHD, cgiMTRC, cgiSITE):
    """write head of HTML page to stdout"""
    # ####################################################################### #
    OVRD_TITLES = {
        'LifeStatus':  "Life Status Manual Override",
        'ProdStatus':  "Production Status Manual Override",
        'CrabStatus':  "Analysis Status Manual Override"
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
           "</H1>\n<HR>\n<P>\n\n") % (myTitle, myTitle))

    return
# ########################################################################### #



def ovrd_html_override(cgiMTRC, siteFacility, cgiSITE):
    """write main section of HTML override page to stdout"""
    # ####################################################################### #
    OVRD_NOENTRY = { 'name': None, 'status': None, 'mode': 'oneday',
                     'when': "", 'who': "", 'why': "" }
    #
    viewFlag = False
    siteAuth = set()
    mstrFlag = False

    grpList = [e for e in os.environ['ADFS_GROUP'].split(";") if ( e != "" ) ]

    print(("<TABLE>\n<TR>\n   <TD VALIGN=\"top\" NOWRAP><B>%s</B> &nbsp;\n  " +
           " <TD VALIGN=\"top\" NOWRAP><B>e-group</B> member of &nbsp;\n   <" +
           "TD VALIGN=\"top\" NOWRAP>\n") % os.environ['ADFS_FULLNAME'])
    frstFlag = True
    for group in grpList:
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
    for group in grpList:
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
    for group in grpList:
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
        overrideDict = ovrd_read_override(cgiMTRC)


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
            for state in OVRD_STATUS_NAME[cgiMTRC]:
                slctnInfo += (("         <INPUT TYPE=\"radio\" NAME=\"status" +
                               "\" VALUE=\"%s\"") % state)
                if ( entry['status'] == state ):
                    slctnInfo += " CHECKED"
                slctnInfo += (">%s\n         &nbsp; &nbsp;\n" %
                                              OVRD_STATUS_NAME[cgiMTRC][state])
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
                   "\n      </FORM>\n\n") % (bckgnd, site, crrntInfo,
                                        OVRD_CGIURL, cgiMTRC, site, slctnInfo))
        #
        print("<TR HEIGHT=\"3\">\n   <TD COLSPAN=\"2\" STYLE=\"background-co" +
              "lor: black\">\n</TABLE>\n<BR>\n<P>\n\n")

    return
# ########################################################################### #



def ovrd_post_override(cgiMTRC, siteFacility, cgiSITE, cgiPOST):
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
        overrideEntry['who'] = os.environ['ADFS_LOGIN']
        overrideEntry['why'] = commentRegex.sub("", cgiPOST['why'][0])
    except (KeyError, IndexError) as excptn:
        logging.critical("Bad CGI data, %s" % str(excptn))
        return

    # check/validate override entry:
    if cgiMTRC not in OVRD_STATUS_NAME:
        logging.critical("Unsupported metric \"%s\"" % cgiMTRC)
        return
    #
    if overrideEntry['name'] not in siteFacility:
        logging.critical("Unknown CMS site \"%s\"" % overrideEntry['name'])
        return
    #
    if (( overrideEntry['status'] is not None ) and
        ( overrideEntry['status'] not in OVRD_STATUS_NAME[cgiMTRC] )):
        logging.critical("Illegal %s metric status \"%s\"" %
                                            (cgiMTRC, overrideEntry['status']))
        return
    #
    if overrideEntry['mode'] not in OVRD_MODE_NAME[cgiMTRC]:
        logging.critical("Illegal %s override mode \"%s\"" %
                                              (cgiMTRC, overrideEntry['mode']))
        return

    # check authorization:
    authFlag = False
    mstrFlag = False
    grpList = [e for e in os.environ['ADFS_GROUP'].split(";") if ( e != "" ) ]
    for group in grpList:
        if group in OVRD_AUTH_EGROUP[cgiMTRC]:
            if ( OVRD_AUTH_EGROUP[cgiMTRC][group] == "ALL" ):
                authFlag = True
                mstrFlag = True
                break
            elif ( type( OVRD_AUTH_EGROUP[cgiMTRC][group] ) == type( [] ) ):
                for site in OVRD_AUTH_EGROUP[cgiMTRC][group]:
                    if ( site == overrideEntry['name'] ):
                         authFlag = True
        elif (( group[:4] == "cms-" ) and ( group[4:6].isupper() == True ) and
              ( group[6] == "_" ) and ( group[-5:] == "-exec" )):
            if ( siteFacility[ overrideEntry['name'] ] == group[4:-5] ):
                authFlag = True
        elif (( group[:4] == "cms-" ) and ( group[4:6].isupper() == True ) and
              ( group[6] == "_" ) and ( group[-6:] == "-admin" )):
            if ( siteFacility[ overrideEntry['name'] ] == group[4:-6] ):
                authFlag = True
    if ( authFlag == False ):
        logging.critical(("User \"%s\" not authorized to change %s of CMS si" +
                          "te \"%s\"") % (overrideEntry['who'], cgiMTRC,
                                                        overrideEntry['name']))
        return

    # update override file with new site entry:
    ovrd_update_override(cgiMTRC, overrideEntry)

    # append operation to log file:
    ovrd_append_log(cgiMTRC, overrideEntry)

    # re-read override file:
    overrideDict = ovrd_read_override(cgiMTRC)

    # write main section of HTML update page:
    print(("<TABLE BORDER=\"0\" CELLPADDING=\"2\" CELLSPACING=\"1\">\n<T" +
               "R>\n   <TH STYLE=\"text-align: left; font-size: larger;\">CM" +
               "S Site:\n   <TH STYLE=\"text-align: left; font-size: larger;" +
               "\">%s Override:\n\n") % cgiMTRC)
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
        for state in OVRD_STATUS_NAME[cgiMTRC]:
            slctnInfo += (("         <INPUT TYPE=\"radio\" NAME=\"status\" V" +
                           "ALUE=\"%s\"") % state)
            if ( overrideDict[cgiSITE]['status'] == state ):
                slctnInfo += " CHECKED"
            slctnInfo += (">%s\n         &nbsp; &nbsp;\n" %
                                              OVRD_STATUS_NAME[cgiMTRC][state])
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
               ": bold; background-color: #B0C0FF;\">\n      </FORM>\n\n") %
              (bckgnd, cgiSITE, crrntInfo, OVRD_CGIURL, cgiMTRC, cgiSITE,
                                                                    slctnInfo))
    else:
        slctnInfo = ("<INPUT TYPE=\"radio\" NAME=\"status\" VALUE=\"auto\" C" +
                     "HECKED>Automatic state setting/no override\n         <" +
                     "BR>\n")
        for state in OVRD_STATUS_NAME[cgiMTRC]:
            slctnInfo += (("         <INPUT TYPE=\"radio\" NAME=\"status\" V" +
                           "ALUE=\"%s\">%s\n         &nbsp; &nbsp;\n") %
                                     (state, OVRD_STATUS_NAME[cgiMTRC][state]))
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
               "round-color: #B0C0FF;\">\n      </FORM>\n\n") % (cgiSITE,
                                     OVRD_CGIURL, cgiMTRC, cgiSITE, slctnInfo))
    print("<TR HEIGHT=\"3\">\n   <TD COLSPAN=\"2\" STYLE=\"background-color:" +
          " black\">\n</TABLE>\n<BR>\n<P>\n\n")

    return
# ########################################################################### #



def ovrd_html_trailer(msgLog):
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
           "d others 2019</A>\n</TABLE>\n\n</BODY>\n</HTML>\n") % timeStrng)

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
    # write page header:
    ovrd_html_header(cgiMTHD, cgiMTRC, cgiSITE)
    #
    #
    #
    try:
        # get site-to-facility mapping:
        siteFacility = ovrd_cric_facility()
        #
        #
        if ( cgiMTHD == "GET" ):
            ovrd_html_override(cgiMTRC, siteFacility, cgiSITE)
        elif ( cgiMTHD == "POST" ):
            ovrd_post_override(cgiMTRC, siteFacility, cgiSITE, cgiPOST)
        #
    except Exception as excptn:
        logging.critical("CGI execution failure, %s" % str(excptn))
    #
    #
    #
    # shutdown logger:
    logging.shutdown()
    #
    ovrd_html_trailer( logStream.getvalue() )

    #import pdb; pdb.set_trace()
