
import calculate_links, threading, time, cPickle, logging, cStringIO, traceback
from phedex_monitor.model.bidirectional_link import BidirectionalLink
from phedex_monitor.model.link import Link

from sets import Set as set

class DDTData:

    expiration_time = 3600
    data_file = 'info.pickle'

    def __init__( self, conf_parser ):
        self.logger = logging.getLogger("root.Datasource")
        self.expiration_time = conf_parser.getint("Datasource", "expiration_time")
        self.url = conf_parser.get("Datasource", "url")
        print self.url
        self.statusurl = conf_parser.get("Datasource", "statusurl")
        self.status_parser = calculate_links.DDTLinkStatusParser( self.statusurl )
        print self.statusurl
        self.status_parser.run()
        self.statusdata = self.status_parser.getCommissionedLinks()
        self.data_file = conf_parser.get("Datasource", "data_file")
        self.override_file = conf_parser.get("Datasource", "override_file")
        self.debug_links = conf_parser.get("Datasource", "debug_links").split(',')
        self.debug_links = [i.strip() for i in self.debug_links]
        self.info_lock = threading.Lock()
        self.nodes = set()
        try:
            self.data, self.info_source_time = cPickle.load( open(self.data_file, 'r') )
            self.build_nodes()
            self.calc = calculate_links.DDTCommissionCalculator( self.data, self.statusdata )
            self.calc.run( )
            self.build_linkmap()
            self.build_bidirectional_links()
            self.override_link_states()
        except Exception, e:
            st = cStringIO.StringIO()
            traceback.print_exc( file=st )
            self.logger.warning( e )
            self.logger.warning( st.getvalue() )
            self.info_source_time = 0
            self.data = getattr(self, 'data', [])
        self.logger.info("Running update.")
        try:
            self.run_update()
        except (SystemExit, KeyboardInterrupt):
            raise
        except:
            pass
        self.logger.info("Finished initial update.")
        try:
            self.override = cPickle.load( open(self.override_file, 'r') )
        except:
            self.override = {}
        self.kill_flag = False
        self.update_thread = threading.Thread( target=self.updater )
        self.update_thread.start()
        self.logger.info("Returning from DDTData constructor.")

    def kill(self):
        self.kill_flag = True

    def build_nodes( self ):
        self.nodes_map = {}
        for link in self.data:
            from_node, to_node = link.from_node, link.to_node
            from_node_str = str(from_node)
            if from_node_str not in self.nodes_map:
                self.nodes_map[from_node_str] = from_node
            to_node_str = str(to_node)
            if to_node_str not in self.nodes_map:
                self.nodes_map[to_node_str] = to_node
        self.nodes = []
        keys = self.nodes_map.keys()
        keys.sort()
        for node_str in keys:
            self.nodes.append( self.nodes_map[node_str] )

    def updater( self ):
        while not self.kill_flag:
            time.sleep( 1 )
            try:
                self.run_update()
            except (KeyboardInterrupt, SystemExit):
                raise
            except:
                pass

    def run_update(self):
        now = time.time()
        if now - self.info_source_time < self.expiration_time:
           return
        self.logger.info("Updating all data.")
        self.status_parser.run()
        self.statusdata = self.status_parser.getCommissionedLinks()
        data_parser = calculate_links.DDTDataParser( self.url )
        data_parser.run( self.debug_links )
        data = data_parser.getData()
        self.info_lock.acquire()
        try:
            self.data = data
            self.build_nodes()
            self.info_source_time = now
            cPickle.dump( (self.data, self.info_source_time), \
                          open(self.data_file, 'w') )
            self.calc = calculate_links.DDTCommissionCalculator(data, self.statusdata) 
            self.calc.run( )
            self.data = self.calc.links
            self.build_linkmap()
            self.build_bidirectional_links()
            self.override_link_states()
        finally:
            self.info_lock.release()

    def override_link_states( self, override=True):
        if override == True:
            try:
                self.override = cPickle.load( open(self.override_file, 'r') )
            except:
                self.override = {}
        for key, value in self.override.items():
            from_node, to_node = key
            link = self.get_link( from_node, to_node )
            if link.state.state != value:
                link.state.state = value
                link.overridden = True

    def get_all_links( self ):
        return self.data

    def get_link( self, from_node, to_node ):
        return self.linkmap[str(from_node), str(to_node)]

    def get_links_by_from_tier(self, tier):
        filtered_links = []
        for link in self.linkmap.values():
            if link.from_node.tier == tier:
                filtered_links.append( link )
        return filtered_links

    def override_state(self, link, status):
        self.info_lock.acquire()
        try:
            key = str(link.from_node), str(link.to_node)
            link = self.get_link(*key)
            if status != 'RELEASE-OVERRIDE':
                self.override[key] = status
                if link.state.state != status:
                    link.state.state = status
                    link.overridden = True
            else:
                del self.override[key]
                link.overridden = False
                self.calc.run(all_debug=True)
                self.override_link_states(override=False)
            cPickle.dump( self.override, open(self.override_file, 'w') )
        finally:
            self.info_lock.release()

    def build_linkmap( self, ):
        self.linkmap = {}
        for link in self.data:
            key = str(link.from_node), str(link.to_node)
            self.linkmap[key] = link
        for from_node in self.nodes:
            for to_node in self.nodes:
                key = str(from_node), str(to_node)
                if key not in self.linkmap:
                    new_link = Link(from_node, to_node)
                    self.linkmap[key] = new_link

    def build_bidirectional_links( self ):
        self.bid_links = {}
        for from_node in self.nodes:
            for to_node in self.nodes:
                key = str(from_node), str(to_node)
                if key in self.bid_links:
                    continue
                other_key = (key[1], key[0])
                from_link = self.linkmap[key]
                to_link = self.linkmap[other_key]
                bid = BidirectionalLink( from_node, to_node, from_link, \
                                         to_link )
                if key[0] not in self.bid_links:
                    self.bid_links[key[0]] = {}
                self.bid_links[key[0]][key[1]] = bid

    def get_bidirectional_links( self ):
        links = []
        from_nodes = self.bid_links.keys()
        from_nodes.sort()
        for from_node in from_nodes:
            from_node_str = str(from_node)
            to_nodes = self.bid_links[from_node_str].keys()
            to_nodes.sort()
            for to_node in to_nodes:
                to_node_str = str(to_node)
                links.append( self.bid_links[from_node_str][to_node_str] )
        return links

    def get_bidirectional_link( self, from_node, to_node ):
        return self.bid_links[str(from_node)][str(to_node)]

    def get_bid_links_by_tiers(self, from_tier, to_tier):
        filtered_links = []
        from_nodes = self.bid_links.keys()
        from_nodes = [str(i) for i in from_nodes]
        from_nodes.sort()
        for from_node_str in from_nodes:
            from_node = self.get_node( from_node_str )
            if from_tier != None and from_node.tier != from_tier:
                continue
            to_nodes = self.bid_links[from_node_str].keys()
            to_nodes = [str(i) for i in to_nodes]
            to_nodes.sort()
            for to_node_str in to_nodes:
                to_node = self.get_node( to_node_str )
                if to_tier == None or to_node.tier == to_tier:
                    link = self.bid_links[from_node_str][to_node_str]
                    filtered_links.append( \
                        self.bid_links[from_node_str][to_node_str] )
        return filtered_links

    def get_link_state_counts(self, from_tier, to_tier):
        links = self.get_bid_links_by_tiers(from_tier, to_tier)
        state = {}
        link_cache = []
        for bid_link in links:
            for link in [bid_link.from_link, bid_link.to_link]:
                link_str = str(link)
                if link_str in link_cache:
                    continue
                elif link.from_node.shortname == link.to_node.shortname:
                    continue
                else:
                    link_cache.append(link_str)
                val = state.get(link.state.state,0)
                state[link.state.state] = val + 1
        return state

    def get_nodes( self ):
        return self.nodes

    def get_node( self, node ):
        return self.nodes_map[str(node)]

    def get_nodes_by_tier( self, tier):
        filtered_nodes = []
        for node in self.nodes:
            if node.tier == tier:
                filtered_nodes.append( node )
        return filtered_nodes

