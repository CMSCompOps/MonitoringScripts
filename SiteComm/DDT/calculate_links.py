#! /usr/bin/env python

import os, sys, time, datetime, logging
from phedex_monitor.service.calculate_links import DDTCommissionCalculator
from phedex_monitor.model.state import State
from phedex_monitor.service.data_parser import DDTDataParser
from phedex_monitor.service.link_status_parser import DDTLinkStatusParser

log = logging.getLogger()
#log.addHandler( logging.StreamHandler() )
log.setLevel( logging.INFO )
log.propagate = False

""" @author: Brian Bockelman """

def parseOpts( args ):
  # Stupid python 2.2 on SLC3 doesn't have optparser...
  keywordOpts = {}
  passedOpts = []
  givenOpts = []
  length = len(args)
  optNum = 0
  while ( optNum < length ):
    opt = args[optNum]
    hasKeyword = False
    if len(opt) > 2 and opt[0:2] == '--':
      keyword = opt[2:]
      hasKeyword = True
    elif opt[0] == '-':
      keyword = opt[1:]
      hasKeyword = True
    if hasKeyword:
      if keyword.find('=') >= 0:
        keyword, value = keyword.split('=', 1)
        keywordOpts[keyword] = value
      elif optNum + 1 == length:
        passedOpts.append( keyword )
      elif args[optNum+1][0] == '-':
        passedOpts.append( keyword )
      else:
        keywordOpts[keyword] = args[optNum+1]
        optNum += 1
    else:
      givenOpts.append( args[optNum] )
    optNum += 1
  return keywordOpts, passedOpts, givenOpts

def printHelp():
    help = """
    The calculate_links.py script calculates the status of various PhEDEx links
    according to the rules set forth by the DDT starting from 1st of June 2007

    Options:
      -url=<URL>\t\tManually set the data feed to <URL>.
      -debug_links=<link1>,<link2>\tComma-separated list of links to enable debugging.
      -debug\t\t\tEnable debug for calculator and parser on the debug links.
      -debug_calc\t\tEnable just the debug on the calculator for the debug links.
      -debug_parser\t\tEnable just the debug on the parser for the debug links
      -y=<year> \t\tyear of end cutoff date
      -m=<month> \t\tmonth of end cutoff date
      -d=<day>\t\tday of end cutoff date
      -sy=<year> \t\tyear of start cutoff date
      -sm=<month> \t\tmonth of start cutoff date
      -sd=<day>\t\tday of start cutoff date
      -dd\t\tdaily data span 
    """
    print help

if __name__ == '__main__':
    os.chdir("/data/ProdNodes/DDTLinksManage/")

    kwOpts, passedOpts, givenOpts = parseOpts( sys.argv[1:] )

    if 'h' in passedOpts or 'help' in passedOpts:
        printHelp()
        sys.exit(-1)

   
    #surl = 'http://t2.unl.edu/phedex/xml/enabled?from_node=.*&excludefrom=XT%7CCH_CAF&excludeto=XT%7CCH_CAF&to_node=.*&conn=Prod%2FNEBRASKA'
    surl='https://cmsweb.cern.ch/phedex/datasvc/xml/prod/links'
    durl2='https://cmsweb.cern.ch/phedex/datasvc/xml/debug/transferhistory?binwidth=%s&starttime=%s&endtime=%s'
       
    year = kwOpts.get('y')
    month = kwOpts.get('m')
    day = kwOpts.get('d')
    if year != None and month != None and day != None:
        year, month, day = int(year),int(month),int(day)
        etime = int(time.mktime(datetime.datetime(year,month,day).timetuple()))
        edate = datetime.datetime( year, month, day, 0 )
    else:
        etime = int(time.time())
        edate = datetime.datetime.today()

    start_year =  kwOpts.get('sy')
    start_month =  kwOpts.get('sm')
    start_day = kwOpts.get('sd')

    if start_year != None and start_month != None and start_day != None:
	start_year, start_month, start_day = int(start_year),int(start_month),int(start_day)
	stime = max(int(time.mktime(datetime.datetime(start_year,start_month,start_day).timetuple())),int(time.time() - 15*86400))
        sdate = datetime.date( start_year, start_month, start_day )
    else:
        #Default starting date is 3 days ago
        #stime = 1180645200 # 2008-12-01
        stime = int(time.time() - 3*86400)

    if ('dd' in passedOpts):
      span=str(86400)
    else:
      span=str(3600)

    url = durl2 % (span,stime,etime)
 
    log.info( "Using URL: %s" % url )
    log.info( "Using URL for current link status: %s" % surl )

    set_debug = 'debug' in passedOpts
    debug_links = [i.strip() for i in kwOpts.get('debug_links','').split(',')]

    if ('debug_parser' in passedOpts) or set_debug:
        log.setLevel( logging.DEBUG )

    data_parser = DDTDataParser( url )
    data_parser.run( debug_links )
    data = data_parser.getData()

    if ('debug_calc' in passedOpts) or set_debug:
        log.setLevel( logging.DEBUG )
    else:
        log.setLevel( logging.INFO )

    status_parser = DDTLinkStatusParser( surl )
    status_parser.run()
    statusdata = status_parser.getCommissionedLinks()
    print "\nLink state as defined by https://twiki.cern.ch/twiki/bin/view/CMS/DDTLinkStateChangeProcedure"
    print "\nPreviously COMMISSIONED links:"
    status_parser.print_all_links_in_state( State.COMMISSIONED )


    calc = DDTCommissionCalculator( data, statusdata, edate )
    calc.run( debug_links )
    print "\nLink state as defined by https://twiki.cern.ch/twiki/bin/view/CMS/DDTLinkStateChangeProcedure"
    print "\nCommissioned links (COMMISSIONED):"
    calc.print_all_links_in_state( State.COMMISSIONED )
    print "\nCommissioned links in danger of uncommissioning (COMMISSIONED-" \
          "DANGER):"
    calc.print_all_links_in_state(State.COMMISSIONED_DANGER)
    print "\nLinks out of commission due to low rate (PROBLEM-RATE):" 
    calc.print_all_links_in_state( State.PROBLEM_RATE )
    print "\nLinks not in commission due to inability to keep target rate for a full day (PENDING-RATE):"
    calc.print_all_links_in_state( State.PENDING_RATE )
    print "\nLinks pending commissioning (PENDING-COMMISSIONING):"
    calc.print_all_links_in_state( State.PENDING_COMMISSIONING )
    print "\n NEW Links in state COMMISSIONIED:"
    calc.print_all_new_links_in_commissioned_state()
