
import datetime, cPickle

class DummyDatasource:
    
    def read_from_file(self, filename):
        return cPickle.load( filename )      

