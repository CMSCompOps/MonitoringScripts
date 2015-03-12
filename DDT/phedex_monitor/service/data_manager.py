from ConfigParser import ConfigParser
import datetime
import logging
import logging.config

from live_datasource import DDTData
from phedex_monitor.model.node import Node
from phedex_monitor.model.link import Link
from phedex_monitor.model.state import State
from phedex_monitor.model.bidirectional_link import BidirectionalLink

class DataManager:
    """ Class responsible for orchestrating all data manipulation operations.
        Some of that logic made more sense to implement in model classes,
        but it gets executed through DataManager anyway.
        @author Sander S6najalg"""
    
    
    def __init__(self, conf_parser):
        # Initialize the configuration
        self.conf_parser = conf_parser
        self.logger = logging.getLogger("root.DataManager")
        self.datasource = DDTData( conf_parser )

    def kill(self):
        self.logger.info("Killing DataManager.")
        if getattr(self, 'datasource',False):
            self.datasource.kill()

    def get_links(self):
        return self.datasource.get_all_links()

    def get_data(self):
        """ This method is run on every request to the application. Only gets
            the data from the local database. No refreshing is done whatsoever.
            (The responsible method for the local database to stay up-to-date
            with a delay of maximum one hour is DataManager.update_data. """
        
        logger = self.logger
        logger.info("getting data from the local database..")

        table_dto = {}
        #table_dto["tier_zero"] = self.datasource.get_bid_links_by_tiers(Node.Tier.T0, Node.Tier.T1)
        table_dto["tier_one"] = self.datasource.get_bid_links_by_tiers(Node.Tier.T1, Node.Tier.T1)
        table_dto["tier_one_nodes"] = self.datasource.get_nodes_by_tier(Node.Tier.T1)
        table_dto["tier_two"] = self.datasource.get_bid_links_by_tiers(Node.Tier.T2, Node.Tier.T1)
        table_dto["tier_two_nodes"] = self.datasource.get_nodes_by_tier(Node.Tier.T2)
        table_dto["bid_links"] = self.datasource.get_bid_links_by_tiers(None, Node.Tier.T1)
        table_dto["nodes"] = self.datasource.get_nodes()
        table_dto["state_count_t1_t1"] = self.datasource.get_link_state_counts(Node.Tier.T1, Node.Tier.T1)
        table_dto["state_count_t1_t2"] = self.datasource.get_link_state_counts(Node.Tier.T1, Node.Tier.T2)
        table_dto["state_count_t1_all"] = self.datasource.get_link_state_counts(Node.Tier.T1, None)
        #print len(table_dto["bid_links"]), len(table_dto["nodes"]), len(table_dto["tier_one_nodes"])
        

        logger.info("found %i T1 nodes, %i T2 nodes, %i all nodes, and %i all links from local database" \
            % (len(table_dto["tier_one_nodes"]), len(table_dto["tier_two_nodes"]), len(table_dto["nodes"]), 
              len(table_dto["bid_links"])) )

        return table_dto
    
    
    def get_data_for_manual_status_setting(self):
        data = {}
        nodes = [str(i) for i in self.datasource.get_nodes()]
        nodes.sort()
        data["nodes"] = nodes
        data["states"] = State.ALL_STATES
        data["states"].append( 'RELEASE-OVERRIDE' )
        return data
        
    def set_state_manually(self, from_node, to_node, new_state):
        """ Logics behind the set_state_manually form submission."""
        
        if from_node == to_node:
            return "Invalid selection: from_node and to_node are one and the same!"

        from_node = self.datasource.get_node( from_node )
        to_node = self.datasource.get_node( to_node )
        if from_node.tier != Node.Tier.T1 and to_node.tier != Node.Tier.T1:
           return """Neither of the nodes selected was a T1 node.
                     No statistics are kept for this kind link!""" 
        
        self.logger.info("""Trying to set new link state manually. 
            [from_node=%s, to_node=%s, new_state=%s]""" %  \
            (from_node, to_node, new_state) )
        link = self.datasource.get_link( from_node, to_node )

        try:
            self.datasource.override_state( link, new_state )
            return "Link status successfully overridden."
        except Exception, e:
            self.logger.warn(str(e))
            return "Unable to override link status."
        
        
