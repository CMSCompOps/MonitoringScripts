from xml.sax import handler, make_parser
from sets import Set as set
import logging
import urllib2
import platform

import phedex_monitor.model.state as state
from phedex_monitor.model.node import Node
from phedex_monitor.model.link import Link
from phedex_monitor.model.state import State

""" @author: Nicolo Magini """

log = logging.getLogger()
log.addHandler( logging.StreamHandler() )
log.setLevel( logging.INFO )
log.propagate = False

class DDTLinkStatusParser(handler.ContentHandler):

    """
    Retrieve the current link status from the PhEDEx XML data.
    """

    default_pivot = "Unknown"
    default_group = "Unknown"
    default_datum = "deactivated"

    def __init__( self, url ):
        self.url = url
        self.opener = urllib2.build_opener()
        self.opener.addheaders = [('User-agent','DDT/1.0 (CMS) %s/%s %s/%s (%s)' % (urllib2.__name__,urllib2.__version__,platform.system(),platform.release(),platform.processor()))]
        self.parser = make_parser()
        self.parser.setContentHandler( self )
        self.in_data = False
        self.cur_pivot_str = None
        self.cur_group_str = None
        self.cur_pivot_obj = None
        self.cur_group_obj = None
        self.cur_datum_obj = None
        
        self.links = set()

    def run( self, debug_links = [] ):
        self.debug_links = debug_links
        self.parser.parse( self.opener.open(self.url) )
 
    def node_str_to_link( self, source_str, dest_str ):
        from_node, to_node = Node(source_str), Node(dest_str)
        link = Link( from_node, to_node )
        return link

    def startElement( self, name, attrs ):
        if name == 'phedex':
            log.debug("Started parsing data.")
            self.in_data = True
        elif self.in_data == False:
           return
        elif name == 'link':
           self.cur_pivot_str = str( attrs.get('from',self.default_pivot) )
#           if self.cur_pivot_str in self.debug_links:
#               self.do_debug = True
#               log.debug("Starting processing of link %s" % self.cur_pivot_str)
#           else:
#               self.do_debug = False
           self.cur_pivot_obj = self.cur_pivot_str
           self.cur_group_obj = self.default_group
           self.cur_group_str = str( attrs.get('to','None') )
           if self.cur_group_str == 'None':
               self.cur_group_obj = self.default_group
           else:
               self.cur_group_obj = self.node_str_to_link(self.cur_pivot_obj,self.cur_group_str)
           self.cur_datum_obj = self.default_datum
           self.cur_datum_obj=attrs.get('status', self.default_datum)

    def endElement( self, name ):
        if name == 'link':
            #            if self.do_debug:
            #                log.debug("Link had %.3fTB of data on date %s" % \
            #                    (self.cur_datum_obj, self.cur_group_obj.strftime('%x')))
            if (self.cur_datum_obj == "deactivated"):
                self.cur_group_obj.set_state(State.NOT_TESTED)
            else:
                self.cur_group_obj.set_state(State.COMMISSIONED)
            self.links.add(self.cur_group_obj) 
        elif name == 'phedex':
            log.debug("Finished parsing data.")
            self.in_data = False

    def getData( self ):
        """ Returns the set of all links with their status. """
        return self.links

    def getCommissionedLinks( self ):
        """ Returns the set of commissioned links only. """
        commissioned_links = set()
        for link in self.links:
            if link.get_state() == "COMMISSIONED":
                commissioned_links.add(link)
        return commissioned_links

    def print_all_links_in_state( self, match_state ):
        counter = 0
        filtered_links = []
        for link in self.links:
            if link.state == match_state:
                filtered_links.append( str(link) )
        filtered_links.sort()
        for link in filtered_links:
            counter += 1
            from_site, dummy, to_site = link.split()
            print '%20s %20s' % (from_site, to_site)
        print "(%i links in state %s total)" % (counter, match_state)
