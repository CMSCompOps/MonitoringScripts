#!/usr/bin/python3
# #############################################################################



import os, sys
import time, calendar
import socket
import urllib.request, urllib.parse, urllib.error
import http
import json
import xml.etree.ElementTree
import re
# #############################################################################



MEET_DEBUG = True
# #############################################################################



def meet_fetch_vofeed():
    # #########################################################################
    VOFEED_FILE = "/afs/cern.ch/user/c/cmssst/www/vofeed/vofeed.xml"
    VOFEED_URL  = "http://cmssst.web.cern.ch/cmssst/vofeed/vofeed.xml"

    try:
       with open(VOFEED_FILE, 'r') as myFile:
           myData = myFile.read()
    except:
        try:
            with urllib.request.urlopen(VOFEED_URL, timeout=90) as urlHandle:
                urlCharset = urlHandle.headers.get_content_charset()
                if urlCharset is None:
                    urlCharset = "utf-8"
                myData = urlHandle.read().decode( urlCharset )
        except Exception as excptn:
            print("Failed to fetch VO-feed: %s" % str(excptn))
            return {}

    # decode XML:
    myVofeed = xml.etree.ElementTree.fromstring( myData )
    del myData

    gridDict = {}
    for myAtpsite in myVofeed.findall('atp_site'):
        cmsSite = None
        for myGroup in myAtpsite.findall('group'):
            if ( 'type' in myGroup.attrib ):
                if ( myGroup.attrib['type'] == "CMS_Site" ):
                    cmsSite = myGroup.attrib['name']
                    break
        if ( cmsSite is None ):
            continue
        gridSite = myAtpsite.attrib['name']
        if (( gridSite is None ) or ( gridSite == "" )):
            continue
        if ( gridSite not in gridDict ):
             gridDict[gridSite] = cmsSite

    if ( MEET_DEBUG ):
        print("Found %d CMS grid sites in the VO-feed" % len(gridDict))
    #
    return gridDict
# #############################################################################



def meet_ggus_query(queryStrng = None):
    # #########################################################################
    GGUS_API_URL = "https://helpdesk.ggus.eu/api/v1/tickets/search"
    GGUS_QUERY   = "(cms_site_names:T AND !((state.name:solved) OR " + \
                   "(state.name:unsolved)) AND id:>%d)"
    GGUS_PARAM   = "&sort_by=id&order_by=asc&limit=32&expand=false"
    GGUS_HEADER = { 'User-Agent': "CMS siteStatus", \
                    'Authorization': "Token xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx", \
                    'Content-Type': "application/json; charset=UTF-8" }

    # get list of all tickets for the query string:
    ticketList = []
    lastTicket = 0
    for myBatch in range(0, 64, 1):
        if ( queryStrng is None ):
            ggusQuery = '?query=' + urllib.parse.quote_plus(GGUS_QUERY %
                                                                    lastTicket)
        else:
            ggusQuery = '?query=' + urllib.parse.quote_plus( "(" + queryStrng +
                                               ( " AND id:>%d)" % lastTicket) )
        #
        requestURL = GGUS_API_URL + ggusQuery + GGUS_PARAM
        requestObj = urllib.request.Request(requestURL, headers=GGUS_HEADER)
        #
        for myRetry in range(0, 2, 1):
            try:
                responseObj = urllib.request.urlopen(requestObj, timeout=90)
                if ( responseObj.status == http.HTTPStatus.OK ):
                    break
            except Exception as excptn:
                time.sleep(0.250 + (myRetry * 0.500))
        if ( responseObj.status != http.HTTPStatus.OK ):
            return []
        #
        try:
            myCharset = responseObj.headers.get_content_charset()
            if ( myCharset is None ):
                myCharset = "utf-8"
            ggusData = responseObj.read().decode( myCharset )
            if (( ggusData is None ) or
                ( ggusData == "[]" ) or ( ggusData == "" )):
                break
            #
            ggusList = json.loads(ggusData)
            #
            ticketList.extend( ggusList )
            #
            lastTicket = int( ggusList[-1]['id'] )
        except Exception as excptn:
            print("Failed to decode GGUS result: %s" % str(excptn))
            return []

    if ( MEET_DEBUG ):
        print("Retrieved %d tickets from GGUS" % len(ticketList))
    #
    return ticketList
# #############################################################################



def meet_ticket2site(ticketList, gridDict = None):
    # #########################################################################
    siteRegex = re.compile(r"T\d_[A-Z]{2,2}_\w+")

    if (( ticketList is None ) or ( len(ticketList) == 0 )):
        return {}

    siteDict = {}
    cmsTickets = 0
    for myTicket in ticketList:
        try:
            cmsSite = myTicket['cms_site_names']
            voSupport = myTicket['vo_support']
            if (( voSupport != "cms" ) and ( voSupport != "" )):
                continue
        except KeyError:
            cmsSite = None
        #
        if (( cmsSite is None ) or ( cmsSite == "" )):
            if (( gridDict is None ) or ( len(gridDict) == 0 )):
                continue
            try:
                gridSite = myTicket['wlcg_sites']
                voSupport = myTicket['vo_support']
            except KeyError:
                continue
            if (( cmsSite is None ) or ( cmsSite == "" ) or
                ( voSupport != "cms" )):
                continue
            try:
                cmsSite = gridDict[gridSite]
                if (( cmsSite is None ) or ( cmsSite == "" )):
                    continue
                # override CMS site seting in ticket
                myTicket['cms_site_names'] = cmsSite
            except KeyError:
                continue
        if ( siteRegex.match(cmsSite) is None ):
            print("Illegal CMS sitename \"%s\" in GGUS ticket %s, skipping" %
                                                     (cmsSite, myTicket['id']))
            continue
        #
        if ( cmsSite not in siteDict ):
            siteDict[cmsSite] = []
        siteDict[cmsSite].append( myTicket )
        cmsTickets += 1

    if ( MEET_DEBUG ):
        print("Found %d CMS sites tickets at %d sites" %
                                                   (cmsTickets, len(siteDict)))
    #
    return siteDict
# #############################################################################



def meet_twiki_table(siteList, ticketDict, outputDir, flagT12notT23 = True):
    # #########################################################################
    GGUS_TICKET_URL = "https://helpdesk.ggus.eu/#ticket/zoom/"

    if (( siteList is None ) or (ticketDict is None )):
        print("No site list or site/ticket dictionary")
        return
    if ( outputDir is None ):
        print("No output directory path provided, using current directory")
        outputDir = "."

    if ( flagT12notT23 ):
        mySiteGroup = "Tier-0,1"
        myFileName  = "ggus_tier01_section.txt"
    else:
        mySiteGroup = "Tier-2,3"
        myFileName  = "ggus_tier23_section.txt"

    myNow = int( time.time() )
    # UNIX Epoch started at midnight on a Thursday (allow Saturday execution)
    myPastWeek = int( (myNow - 172800 ) / (7 * 24 * 60 * 60 ) ) - 1
    if ( MEET_DEBUG ):
        print("myPastWeek = %d   (%s)" % (myPastWeek, time.strftime(\
                     "%Y-%b-%d %H:%M:%S UTC", time.gmtime(myPastWeek*604800))))
    mySelf = os.path.basename(__file__)
    myHost = socket.gethostname().lower()

    outString = ("<!-- GGUS ticket twiki section written by cmssst script " + \
                 "%s on %s at %s -->\n<noautolink>\n\n---+++ Open %s Site " + \
                 "Tickets in GGUS:\n") % (mySelf, myHost,
                    time.strftime("%Y-%b-%d %H:%M:%S UTC", time.gmtime(myNow)),
                                                                   mySiteGroup)
    outString += "| |  *Tickets*  ||||\n|  *Site*  |  *Total*  |  *&ge; tw" + \
                 "o weeks*  |  *previous week*  |  *last week*  |\n"

    for mySite in siteList:
        if ( flagT12notT23 ):
            if (( mySite[1] != "0" ) and ( mySite[1] != "1" )):
                continue
        else:
            if (( mySite[1] != "2" ) and ( mySite[1] != "3" )):
                continue
        #
        try:
            myTickets = ticketDict[mySite]
            myTotal = len( myTickets )
            myOver2 = ""
            myPrevW = ""
            myPastW = ""
            for myTicket in myTickets:
                try:
                    ticketId = int( myTicket['id'] )
                except (KeyError, AttributeError):
                    continue
                try:
                    ticketType = myTicket['type']
                    ticketPriority = myTicket['priority_id']
                    myColour1 = "%BLACK%"
                    myColour2 = "%ENDCOLOR%"
                    if ( ticketType == "Incident" ):
                        if ( ticketPriority == 1 ):
                           myColour1 = "%BLUE%"
                           myColour2 = "%ENDCOLOR%"
                        else:
                           myColour1 = "%RED%<B>"
                           myColour2 = "</B>%ENDCOLOR%"
                    elif ( ticketType == "Service request" ):
                        myColour1 = "%BLUE%"
                        myColour2 = "%ENDCOLOR%"
                except (KeyError, AttributeError):
                    myColour = "%BLACK%"
                try:
                    ticketCreated = myTicket['created_at']
                    ts = time.strptime(ticketCreated[:19] + " UTC",
                                                        "%Y-%m-%dT%H:%M:%S %Z")
                    myBirth = calendar.timegm(ts)
                except (KeyError, AttributeError):
                    myBirth = 0
                #
                myWeek = int( (myBirth - 259200 ) / (7 * 24 * 60 * 60 ) )
                if ( MEET_DEBUG ):
                   print("ticket myBirth %s   myWeek = %d" % (time.strftime(\
                       "%Y-%b-%d %H:%M:%S UTC", time.gmtime(myBirth)), myWeek))
                if ( myWeek >= myPastWeek ):
                    if ( len( myPastW ) != 0 ):
                        myPastW += ", "
                    myPastW += "[[%s%d][%s%d%s]]" % (GGUS_TICKET_URL, \
                                      ticketId, myColour1, ticketId, myColour2)
                elif ( myWeek == (myPastWeek - 1) ):
                    if ( len( myPrevW ) != 0 ):
                        myPrevW += ", "
                    myPrevW += "[[%s%d][%s%d%s]]" % (GGUS_TICKET_URL, \
                                      ticketId, myColour1, ticketId, myColour2)
                else:
                    if ( len( myOver2 ) != 0 ):
                        myOver2 += ", "
                    myOver2 += "[[%s%d][%s%d%s]]" % (GGUS_TICKET_URL, \
                                      ticketId, myColour1, ticketId, myColour2)
        except:
            myTotal = 0
            myOver2 = "&nbsp;"
            myPrevW = "&nbsp;"
            myPastW = "&nbsp;"
        outString += "| *%s* |  <B>%d</B>  | %s | %s | %s |\n" % (mySite, \
                                            myTotal, myOver2, myPrevW, myPastW)

    outString += ("| |%%RED%%<B>Incidents</B>%%ENDCOLOR%%, %%BLUE%%Service" + \
                  " or Low Priority Incidents%%ENDCOLOR%%, %%BLACK%%Other " + \
                  "Tickets%%ENDCOLOR%% &nbsp; <DIV STYLE=\"float: right\">" + \
                  "as of %s</DIV>||||\n") % \
                        time.strftime("%Y-%b-%d %H:%M UTC", time.gmtime(myNow))
    outString += "\n</noautolink>\n"

    outPath = outputDir + "/" + myFileName
    try:
        with open(outPath, 'w') as myFile:
            myFile.write( outString )
    except Exception as excptn:
        print("Failed to write twiki section %s: %s" % (outPath, str(excptn)))

    return
# #############################################################################
    


if __name__ == '__main__':
    #
    bruteForce = "!((state.name:solved) OR (state.name:unsolved))"
    #
    gridDict = meet_fetch_vofeed()
    siteSet = set()
    for gridSite in gridDict:
        siteSet.add( gridDict[gridSite] )
    siteList = sorted( siteSet )
    del siteSet
    #
    # fetch tickets from GGUS:
    tcktList = meet_ggus_query(bruteForce)
    #
    # convert ticket list into site dictionary:
    siteDict = meet_ticket2site(tcktList, gridDict)
    #
    # write Tier-0,1 twiki section:
    meet_twiki_table(siteList, siteDict, "/eos/home-c/cmssst/www/meet_plots",
                                                                          True)
    #
    # write Tier-2,3 twiki section:
    meet_twiki_table(siteList, siteDict, "/eos/home-c/cmssst/www/meet_plots",
                                                                         False)
