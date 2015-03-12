import cherrypy
import datetime
import logging
import logging.config
from ConfigParser import ConfigParser

from phedex_monitor.service.data_manager import DataManager
from phedex_monitor.controller.application_controller import ApplicationController

# Create a logger
logging.config.fileConfig("logging.conf")
logger = logging.getLogger()

# Load the configuration
logger.info("reading the configuration..")
conf_parser = ConfigParser()
conf_parser.read("configuration.ini")

# Configure the CherryPy server:
listen_port = conf_parser.getint("CherryPy", "listen_port")
server_log_filename = conf_parser.get("CherryPy", "server_log_filename")
mount_path = conf_parser.get("CherryPy", "mount_path")

conf = {"server.socket_port" : listen_port,
        "log.error_file" : server_log_filename}
cherrypy.config.update(conf)


# Instantiate the controller
logger.info("Instantiating the DataManager.")
data_manager = DataManager(conf_parser)
logger.info("instantiating the ApplicationController..")
controller = ApplicationController(data_manager)

# Start the server
cherrypy.tree.mount(controller, mount_path)
cherrypy.server.quickstart()

cherrypy.engine.start()
data_manager.kill()

