from xml.sax import handler, make_parser
import datetime, getopt, sys, time, logging, re
from sets import Set as set
import urllib2
import platform

import phedex_monitor.model.state as state
from phedex_monitor.model.node import Node
from phedex_monitor.model.link import Link
from phedex_monitor.model.data import Data
from phedex_monitor.model.state import State


""" @author: Nicolo Magini """

log = logging.getLogger()
log.addHandler( logging.StreamHandler() )
log.setLevel( logging.INFO )
log.propagate = False

class DDTDataParser(handler.ContentHandler):

    """
    Retrieve the transferred data from the PhEDEx XML data.
    """

    
    default_from_node = "Unknown"
    default_to_node = "Unknown" 
    default_group = datetime.datetime(1999, 01, 01, 00)
    default_datum = Data(float(0.))
    default_timebin_str="0"
    #default_binwidth_str="3600"
    default_cur_donebytes_str="0"

    def __init__( self, url ):
        self.url = url
        self.opener = urllib2.build_opener()
        self.opener.addheaders = [('User-agent','DDT/1.0 (CMS) %s/%s %s/%s (%s)' % (urllib2.__name__,urllib2.__version__,platform.system(),platform.release(),platform.processor()))]
        self.parser = make_parser()
        self.parser.setContentHandler( self )
        self.in_data = False

        self.cur_from_node_name=None
        self.cur_to_node_name=None
        self.cur_link_str=None
        self.cur_link_obj=None

        self.cur_timebin_str=None        
        self.cur_group_obj = None
        
        self.cur_donebytes_str=None
        self.cur_datum_obj = None
        
        self.links = set()
        self.nodes = set()

    def run( self, debug_links = [] ):
        self.debug_links = debug_links
        self.parser.parse( self.opener.open(self.url) )
 
    def node_str_to_link( self, from_node_name, to_node_name):
        from_node, to_node = Node(from_node_name), Node(to_node_name)
        self.nodes.add( from_node )
        self.nodes.add( to_node )
        link = Link( from_node, to_node )
        is_present = False
        for tlink in self.links:
            if tlink.from_node.name == from_node.name and \
                    tlink.to_node.name == to_node.name:
                is_present = True
                link = tlink
        if not is_present:
            self.links.add( link )
        return link


    def startElement( self, name, attrs ):
        if name == 'phedex':
            log.debug("Started parsing data.")
            self.in_data = True
        elif self.in_data == False:
           return
        elif name == 'link':
            self.cur_from_node_name=attrs.get('from',self.default_from_node)
            self.cur_to_node_name=attrs.get('to',self.default_to_node)
            self.cur_link_str = self.cur_from_node_name+" to "+self.cur_to_node_name
            if self.cur_link_str in self.debug_links:
                self.do_debug = True
                log.debug("Starting processing of link %s" % self.cur_link_str)
            else:
                self.do_debug = False
            self.cur_link_obj = self.node_str_to_link( self.cur_from_node_name, self.cur_to_node_name)
            self.cur_group_obj = self.default_group
        elif name == 'transfer':
            self.cur_timebin_str=attrs.get('timebin','None')
            if self.cur_timebin_str == 'None':
               self.cur_group_obj = self.default_group
            else:
               d = datetime.datetime.utcfromtimestamp(float(self.cur_timebin_str))
               self.cur_group_obj = datetime.datetime( d.year, d.month, d.day, d.hour )
            self.cur_datum_obj = self.default_datum
            #self.cur_binwidth_str=attrs.get('binwidth',self.default_binwidth_str)
            self.cur_donebytes_str=attrs.get('done_bytes', self.default_cur_donebytes_str)
            self.cur_datum_obj = Data( float(self.cur_donebytes_str)/(1024*1024*1024*1024))
            
    def endElement( self, name ):
        if name == 'phedex':
            log.debug("Finished parsing data.")
            self.in_data = False
        elif name == 'transfer':
            if self.do_debug:
                log.debug("Link %s had %.3fTB of data on date %s" % \
                      (self.cur_link_obj, self.cur_datum_obj, self.cur_group_obj.strftime('%x %X')))
            self.cur_link_obj.add_data(self.cur_group_obj, \
                                        self.cur_datum_obj)

    def getData( self ):
        """ Returns the data of all the links. """
        return self.links

    def getNodes( self ):
        """ Returns all the nodes. """
        return self.nodes
