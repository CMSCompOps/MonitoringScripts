from Cheetah.Template import Template
import cherrypy
import logging

class ApplicationController:
    """ A controller class for CherryPy that encapsulates all actions
        and is therefore a general entry-point to everything else in this app.
        All communication with the local database and xml data portal are
        done through a DataManager instance for cleaner disain purposes. 

        @author Sander S6najalg
    """

    def __init__(self, data_manager):
        self.logger = logging.getLogger("root.ApplicationController")
        self.data_manager = data_manager
    
    def index(self):
        """ Action that displays the main data table. """
        self.logger.info("recieved a request to layer data from local database")
        dto = self.data_manager.get_data()
        data = [{'dto' : dto}]
        template = Template ( file = 'phedex_monitor/template/data_table.tmpl',
            searchList = data)
        return template.__str__()

    def xml(self):
        """ Action which writes link status in XML form. """
        self.logger.info("Recieved a request for XML format.")
        links = self.data_manager.get_links()
        data = [{'links':links}]
        template = Template( file='phedex_monitor/template/xml.tmpl', 
            searchList=data)
        cherrypy.response.headers['Content-Type'] = 'text/xml'
        return str(template)
    
    def set_state_manually(self, from_node=None, to_node=None, new_state=None):
        """ Action for over-riding links statuses manually. """
        # this is a request..
        if from_node==None and to_node==None and new_state==None:
            
            data = self.data_manager.get_data_for_manual_status_setting()
            data = [{'data' : data}]
            template = Template ( file = 'phedex_monitor/template/set_state_manually.tmpl',
                searchList = data)
            return template.__str__()
    
        # this is a form submit..
        else:
            result_string = self.data_manager.set_state_manually(from_node, to_node, new_state)
            return result_string
    
    index.exposed = True
    set_state_manually.exposed = True
    xml.exposed=True

