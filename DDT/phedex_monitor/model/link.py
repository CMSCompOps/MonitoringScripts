import datetime
import logging

from node import Node
from state import State
from data import Data

GRAPH_URL = "https://cmsdoc.cern.ch:8443/cms/aprom/phedex/prod/Activity::Rate"\
            "Plots?src_filter=%s;period=l30d;no_mss=true;dest_filter=%s;entit"\
            "y=link;graph=quantity"

GRAPH_URL='http://t2.unl.edu/phedex/xml/quantity?span=3600&starttime=time.ti'\
          'me()-12*3600&from_node=%s&to_node=%s'

class Link:
    """ A class that holds data for link status from Node instance A to Node instance
        B and knows how to layer it's data as HTML in the web interface. The Link
        is one-directional. Class BidirectionalLink wraps 2 Link instances, one in
        each direction."""
    
    def __init__( self, from_node, to_node, data={} ):
        self.from_node = from_node
        self.to_node = to_node
        self.data = dict(data)
        self._state = State()
        self.calculated_state = State()
        self.overridden = False

    def begins_at_T1(self):
        if str(self.from_node).startswith('T1') :
            return True
        else:
            return False
            
    def get_dates(self):
        return self.data.keys()
  
    def add_data( self, date, data ):
        if date in self.data:
            self.data[date].data += float(data)
        else:
            self.data[date] = data

    def get_data( self, my_date, default=Data() ):
        return self.data.get( my_date, default )

    def link_history( self, days=12 ):
        dat = datetime.datetime.utcnow()
        today = datetime.datetime(dat.year, dat.month, dat.day, dat.hour)
        one_day = datetime.timedelta(1)
        one_hour=datetime.timedelta(0,3600)
        history = []
        for i in range(int(days)):
            datum = self.data.get( today - i*one_hour, Data() )
            history.insert(0, datum)
        return history

    def set_state( self, state ):
        self._state = state

    def get_state( self ):
        return self._state

    state = property( get_state, set_state )

    def formatted_history( self, days=12 ):
        history = self.link_history( days )
        strng = ''
        for data in history[:-1]:
            strng += data.to_str() + ', '
        strng += history[-1].to_str()
        return strng

    def url_to_graph( self ):
        return GRAPH_URL % (str(self.from_node), str(self.to_node))

    def __str__( self ):
        return '%s to %s' % (str(self.from_node), str(self.to_node))

