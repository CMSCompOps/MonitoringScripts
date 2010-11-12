from xml.sax import handler, make_parser
import datetime, getopt, sys, time, logging, re,os
from sets import Set as set

import phedex_monitor.model.state as state
from phedex_monitor.model.node import Node
from phedex_monitor.model.link import Link
from phedex_monitor.model.data import Data
from phedex_monitor.model.state import State

log = logging.getLogger()
log.addHandler( logging.StreamHandler() )
log.setLevel( logging.INFO )
log.propagate = False

T1_min_rate_tb = 20.*3600./1024./1024.
T2_min_rate_tb = 5.*3600./1024./1024.
T3_min_rate_tb = 5.*3600./1024./1024.
max_rate_tb = 100000./1024./24
T1_commission_amount = 20.*3600.*24./1024./1024.
T2_commission_amount = 5.*3600.*24./1024./1024.
T3_commission_amount = 5.*3600.*24./1024./1024.
T1_recommission_amount = 20.*3600.*12./1024./1024.
T2_recommission_amount =  5.*3600.*12./1024./1024.
T3_recommission_amount = 5.*3600.*24./1024./1024.
T1_commission_days = (1,24)
T2_commission_days = (1, 24)
T3_commission_days = (1, 24)
days_to_uncommission = 14
#days_to_danger = 7
#T1_recommission_days = (5, 6)
#T2_recommission_days = (3, 4)
T1_recommission_days = (1, 12)
T2_recommission_days = (1, 12)
T3_recommission_days = (1, 12)

""" @author: Brian Bockelman """

default_url='https://cmsweb.cern.ch/phedex/datasvc/xml/debug/transferhistory?binwidth=3600&starttime=1247868000&endtime=1248888241'
#default_url='http://t2.unl.edu/phedex/xml/quantity?span=86400&starttime=1180645200&no_mss=True&link=link&endtime=time.time%28%29&to_node=.*&from_node=.*'

default_status_url='http://t2.unl.edu/phedex/xml/enabled?from_node=.*&excludefrom=T3%7CMSS%7CT0%7CPIC_Disk%7CXT2%7CCH_CAF&excludeto=T3%7CMSS%7CT0%7CPIC_Disk%7CXT2%7CCH_CAF&to_node=.*&conn=Prod%2FNEBRASKA'

class DDTCommissionCalculator:

    def __init__( self, data, linkstatus, todays_date=None ):
        if todays_date == None:
            dat = datetime.datetime.utcnow()
            todays_date = datetime.datetime(dat.year, dat.month, dat.day, dat.hour)
        self._init_data = data
        self._starting_data = linkstatus

        # Set status of already enabled links to COMMISSIONED, possibly adding them to the list if not already present
        for commissioned_link in self._starting_data:
            indata = False
            for link in self._init_data:
                if commissioned_link.from_node.name == link.from_node.name and commissioned_link.to_node.name == link.to_node.name:
                    link.set_state(State.COMMISSIONED)
                    indata = True
            if indata == False:
                self._init_data.add(commissioned_link)
        
        # Add an entry for today's date, possibly 0
        for link in self._init_data:
            if todays_date not in link.get_dates():
                volume = link.get_data(todays_date)
                link.add_data(todays_date, volume)

        self.links = set()
                    
        

    def run( self, debug_links=[], all_debug=False ):
        for link in self._init_data:
            do_debug = (str(link) in debug_links) or all_debug
            if do_debug:
                log.debug("Starting calculator on link %s." % str(link) )
            self.check_commission_status( link, do_debug )
            self.links.add( link )

    def commission_rate_tb( self, link, cur_state ):
        if str(link).startswith('T1') :
            return T1_min_rate_tb
        elif str(link).startswith('T2'):
            return T2_min_rate_tb
	else:
 	    return T3_min_rate_tb	

    def commission_amount( self, link, cur_state ):
        dummy, days = self.commission_days(link, cur_state)
        min_rate_tb = self.commission_rate_tb(link, cur_state )
        return days*min_rate_tb
        
    def commission_days( self, link, cur_state ):
        if link.startswith('T1') :
            if ( cur_state.state == State.PROBLEM_RATE ) | cur_state.is_commissioned():
                return T1_recommission_days
            else:
                return T1_commission_days
        elif link.startswith('T2'):
            if ( cur_state.state == State.PROBLEM_RATE ) | cur_state.is_commissioned():
                return T2_recommission_days
            else:
                return T2_commission_days
	else:
	     if ( cur_state.state == State.PROBLEM_RATE ) | cur_state.is_commissioned():
                return T3_recommission_days
             else:
                return T3_commission_days

    def starts_as_commissioned( self, link ):
        pass

    def check_commission_status( self, link, debug=False ):
        # Link data is a dictionary mapping <date> -> <amount transferred>
        my_keys = link.data.keys()
        my_keys.sort()
        zero_days = datetime.timedelta(0)
        one_day = datetime.timedelta(1)
        date_of_last_commissioning = datetime.datetime(1999,1,1,0)
        #last_above_base = datetime.datetime(1999,1,1,0)
        
        # Start off in the PENDING_COMMISSIONING state
        cur_state = State()
        cur_state.state = State.PENDING_COMMISSIONING
        # Start off in the COMMISSIONED state if link was previously commissioned
        if link.get_state() == "COMMISSIONED":
            cur_state.state = State.COMMISSIONED

        # Link-specific numbers:
        link_str = str(link)

        # Iterate over each of the days of data
        for my_date in my_keys:
            
            if debug:
                log.debug("Examining data from date %s" % my_date.strftime('%x'))
            daily_volume = float(link.get_data(my_date))
           
            td = my_date - date_of_last_commissioning
            if debug and (not cur_state.is_commissioned()):
                log.debug("There have been %i days since last successful commissioning on uncommissioned link.", td.days)
            #if debug and cur_state.is_commissioned():
            #    log.debug("There have been %i days since link was above base rate on commissioned link;"
            #        " today's volume: %.2fTB" % (td.days, daily_volume))
            #if td.days > days_to_danger and cur_state.is_commissioned():
            #    if debug:
            #        td2 = datetime.timedelta(days_to_uncommission - td.days, 0)
            #        log.debug("Link is in danger of uncommissioning on %s." % \
            #                  ((my_date + td2).strftime('%x')))
            #    cur_state.state = State.COMMISSIONED_DANGER
                
            if td.days > days_to_uncommission and cur_state.is_commissioned():
                if debug:
                    log.debug("Link fell out of commissioning state on %s!" % \
                              my_date.strftime('%x'))
                cur_state.state = State.PROBLEM_RATE
                
            

            
            #td = my_date - last_above_base
            #if debug and (not cur_state.is_commissioned()):
            #    log.debug("There have been %i days since last above base rate on uncommissioned link.", td.days)
            #if debug and cur_state.is_commissioned():
            #    log.debug("There have been %i days since link was above base rate on commissioned link;"
            #        " today's volume: %.2fTB" % (td.days, daily_volume))
            #if td.days > days_to_danger and cur_state.is_commissioned():
            #    if debug:
            #        td2 = datetime.timedelta(days_to_uncommission - td.days, 0)
            #        log.debug("Link is in danger of uncommissioning on %s." % \
            #                  ((my_date + td2).strftime('%x')))
            #    cur_state.state = State.COMMISSIONED_DANGER
                
            #if td.days > days_to_uncommission and cur_state.is_commissioned():
            #    if debug:
            #        log.debug("Link fell out of commissioning state on %s!" % \
            #                  my_date.strftime('%x'))
            #    cur_state.state = State.PROBLEM_RATE
               
        
            min_rate_tb = self.commission_rate_tb(link, cur_state )
            
            #if (daily_volume >= min_rate_tb) & (daily_volume <= max_rate_tb) :
            #    if cur_state.state == State.COMMISSIONED_DANGER:
            #        cur_state.state = State.COMMISSIONED
            #    last_above_base = my_date + zero_days

            # If the amount transferred is above 50% of the base rate to start
            # the commissioning check...
            if (daily_volume >= 0.5*min_rate_tb) & (daily_volume <= max_rate_tb) :
                if debug:
                    log.debug("Link is at %.3fTB, above the base rate." % daily_volume)
                #if cur_state.is_commissioned():
                #    if debug:
                #        log.debug("* Link already is commissioned; last day above base %s" %
                #            my_date.strftime('%x'))
                #    continue
                elif debug:
                    log.debug("* Link is not commissioned; starting commissioning check.")
                
                transfer_days = 0
                transfer_volume = 0
                last_missed_day = 0
                last_missed_volume = 0
                # Iterate specifically over the next week of data to check
                # for commissioning of the link
                active_days, total_days = self.commission_days(link_str, cur_state)
                
                amt = self.commission_amount(link_str, cur_state)
                
                for i in range(total_days):
                    
                    offset_td = datetime.timedelta(0,i*3600)
                    offset_day = my_date + offset_td
                    volume = float(link.data.get(offset_day,Data()))
                    transfer_volume += volume
                    if (volume > min_rate_tb) & (volume <= max_rate_tb)  :
                        transfer_days += 1
                    else:
                        last_missed_day = i
                        last_missed_volume = volume
                if debug:
                    log.debug("* There were %i active days and %.2fTB transferred." % (transfer_days, transfer_volume))
                    if transfer_days < active_days:
                        log.debug("* This is less than the required %i active days." % active_days)
                    if transfer_volume < amt:
                        log.debug("* This is less than the required %.2fTB transfer volume." % amt)
                if transfer_days >= active_days and transfer_volume >= amt:
                    if debug:
                        log.debug("* Setting state to commissioned." )
                    cur_state.state = State.COMMISSIONED
                    date_of_last_commissioning = my_date + datetime.timedelta(0,total_days*3600)
                    
                    
#                elif transfer_days == active_days and transfer_volume < amt and last_missed_day == total_days-1:
#                    if debug:
#                        log.debug("* Checking volume on day before first above base." )
#                    transfer_volume_pre = transfer_volume - last_missed_volume
#                    offset_td = datetime.timedelta(-1)
#                    offset_day = my_date + offset_td
#                    volume = float(link.data.get(offset_day,Data()))
#                    transfer_volume_pre += volume
#                    if transfer_volume_pre >= amt:
#                        if debug:
#                            log.debug("* Setting state to commissioned." )
#                        cur_state.state = State.COMMISSIONED
                elif transfer_days > active_days:
                    if ( cur_state.state != State.PROBLEM_RATE ) & ( cur_state.state != State.COMMISSIONED ):
                        cur_state.state = State.PENDING_RATE
                        
        if debug:
            log.debug("Setting link %s to state %s", str(link), cur_state.state )
        link.state = cur_state
        calc_state = State()
        calc_state.state = cur_state.state
        link.calculated_state = calc_state
        return cur_state 

    def print_all_links_in_state( self, match_state ):
        counter = 0
        filtered_links = []
        for link in self._init_data:
            if link.state.state == match_state:
                filtered_links.append( str(link) )
        filtered_links.sort()
        for link in filtered_links:
            counter += 1
            from_site, dummy, to_site = link.split()
            print '%20s %20s' % (from_site, to_site)
        print "(%i links in state %s total)" % (counter, match_state)

    def print_link_state( self, link ):
        print link.state.state       

    def print_all_new_links_in_commissioned_state( self ):
        counter = 0
        filtered_links = []
        for link in self._init_data:
            if link.state.state == "COMMISSIONED":
                already_commissioned=False
                for commissioned_link in self._starting_data:
                    if commissioned_link.from_node.name == link.from_node.name and commissioned_link.to_node.name == link.to_node.name:
                        already_commissioned=True
                if  already_commissioned== False:
                    filtered_links.append( str(link) )
        filtered_links.sort()
        newlinkfilename=datetime.date.today().strftime("%Y%m%d")+"_changes.txt"
        newlinkoutputfile=os.path.abspath(newlinkfilename)
        fou=open(newlinkoutputfile,"w")
        for link in filtered_links:
            counter += 1
            from_site, dummy, to_site = link.split()
            print >> fou, '%20s %20s enable' % (from_site, to_site)
            print '%20s %20s enable' % (from_site, to_site)
        fou.close()
        print "(%i new links in state COMMISSIONED)" % (counter)
