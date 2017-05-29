import sys
import json
import socket
import time
import os.path
import xml.etree.ElementTree as ET
import stomp
import logging


class StompyListener(object):
    """
    Auxiliar listener class to fetch all possible states in the Stomp
    connection.
    """

    def __init__(self):
        self.logr = logging.getLogger(__name__)
        # logging.basicConfig(filename='example.log',level=logging.DEBUG)

    def on_connecting(self, host_and_port):
        self.logr.info('on_connecting %s', str(host_and_port))

    def on_error(self, headers, message):
        self.logr.info('received an error %s %s', str(headers), str(message))

    def on_message(self, headers, body):
        self.logr.info('on_message %s %s', str(headers), str(body))

    def on_receipt(self, headers, message):
        self.logr.info('on_message %s %s', str(headers), str(message))

    def on_heartbeat(self):
        self.logr.info('on_heartbeat')

    def on_send(self, frame):
        self.logr.info('on_send HEADERS: %s, BODY: %s ...', str(frame.headers), str(frame.body)[:160])

    def on_connected(self, headers, body):
        self.logr.info('on_connected %s %s', str(headers), str(body))

    def on_disconnected(self):
        self.logr.info('on_disconnected')

    def on_heartbeat_timeout(self):
        self.logr.info('on_heartbeat_timeout')

    def on_before_message(self, headers, body):
        self.logr.info('on_before_message %s %s', str(headers), str(body))
        return (headers, body)


class Stompy(object):
    """
    Class to generate send messages to a given Stomp broker
    on a given topic.
    :param username: The username to connect to the broker.
    :param password: The password to connect to the broker.
    :param host_and_ports: The hosts and ports list of the brokers.
        Default: [('agileinf-mb.cern.ch', 61213)]
    """

    def __init__(self, username, password, topic):
        # self._host_and_ports = [('188.184.93.36', 61113)]
        self._host_and_ports = [('dashb-mb.cern.ch', 61113)]
        self._username = username
        self._password = password
        self._topic = topic

    def produce(self, messages):
        """
        Dequeue all the messages on the list and sent them to the
        Stomp broker.
        """
        conn = stomp.Connection(host_and_ports=self._host_and_ports
                                # user=self._username,
                                # passcode=self._password
                                )
        conn.set_listener('StompyListener', StompyListener())
        conn.start()
        conn.connect(username=self._username,
                     passcode=self._password,
                     reconnect_sleep_initial=2,
                     reconnect_sleep_jitter=2,
                     wait=True)
        # Send all the messages together
        while len(messages) > 0:
            try:
                message = messages.pop(0)
                message_body = json.dumps(message.pop('body'))
                conn.send(destination=self._topic,
                          body=message_body,
                          headers=message,
                          ack='auto')
                time.sleep(2)
            except Exception, msg:
                logging.error('ERROR message: %s not send, error: %s' %
                              (str(messages), str(msg)))
        if conn.is_connected():
            conn.disconnect()


def parse_xml(raw_log):
    tree = ET.parse(raw_log)
    root = tree.getroot()
    document = {}
    if root.tag == "OSGTestResult" and root.attrib["id"] == "psst.sh":
        # if root.find("result/status") is not None:
        #     document['status'] = root.find("result/status").text
        if root.findall("result/metric") is not None:
            for item in root.findall("result/metric"):
                document[item.attrib['name']] = item.text
        if root.find("detail") is not None:
            document['logs'] = root.find("detail").text
        # if "logs" in document.keys():
        #     document['logs'] = document['logs'].replace('\n', '\\n')
    return document


def produce_doc(raw_document):
    basic_document = {
        "producer": "glideinwms",
        "type_prefix": "raw",
        "type": "psst_raw",
        "body": {
            "hostname": socket.gethostname(),
            "metric_name": "org.cms.WN-PSST",
            "CMSUser": "rmaciula",
            "GridName": "/DC=ch/DC=cern/OU=OrganicUnits/OU=Users/\
            CN=rmaciula/CN=780070/CN=Rokas Maciulaitis",
        }
    }
    for key in raw_document:
        basic_document["body"][key] = raw_document[key]
    basic_document["timestamp"] = basic_document["body"]["timestamp"]
    del basic_document["body"]["timestamp"]
    return basic_document

if __name__ == '__main__':
    if os.path.isfile(sys.argv[1]):
        raw_doc = parse_xml(sys.argv[1])
        doc = produce_doc(raw_doc)
        send_doc = Stompy(username="xxxxxx",
                          password="xxxxxx",
                          topic="/topic/cms.jobmon.glideinwms")
        doc = [doc]
        send_doc.produce(doc)
    else:
        print "%s file was not found" % sys.argv[1]
        sys.exit(1)
