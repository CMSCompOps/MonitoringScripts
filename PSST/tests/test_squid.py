#!/usr/bin/env python
"""
Tests the local FroNtier squid
"""
#
# Assumes:
#
#   1) environmental variables SAME_OK,SAME_WARNING and SAME_ERROR are defined
#   2) environmental variable $CMS_PATH is defined
#   3) file $CMS_PATH/SITECONF/local/JobConfig/site-local-config.xml
#      contains the location of the local FroNtier squid server
#
__revision__ = "$Id: test_squid.py,v 1.31 2013/03/20 16:27:34 llinares Exp $"
import os
import sys
import urllib2
from xml.dom.minidom import parseString
from xml.dom.minidom import parse
import base64
import zlib 
import curses.ascii
import time
#
#---------------- define timeout on urllib2 socket ops -------------#
#  Adapted from http://code.google.com/p/timeout-urllib2/

from httplib import HTTPConnection as _HC
import socket
from urllib2 import HTTPHandler as _H

def sethttptimeout(timeout):
  """Use TimeoutHTTPHandler and set the timeout value.
  
  Args:
    timeout: the socket connection timeout value.
  """
  if _under_26():
    opener = urllib2.build_opener(TimeoutHTTPHandler(timeout))
    urllib2.install_opener(opener)
  else:
    raise Error("This python version has timeout builtin")

def _clear(sock):
  sock.close()
  return None

def _under_24():
  import sys
  if sys.version_info[0] < 2: return True
  if sys.version_info[0] == 2:
    return sys.version_info[1] < 4
  return False

def _under_26():
  import sys
  if sys.version_info[0] < 2: return True
  if sys.version_info[0] == 2:
    return sys.version_info[1] < 6
  return False

class Error(Exception): pass

class HTTPConnectionTimeoutError(Error): pass

class TimeoutHTTPConnection(_HC):
  """A timeout control enabled HTTPConnection.
  
  Inherit httplib.HTTPConnection class and provide the socket timeout
  control.
  """
  _timeout = None

  def __init__(self, host, port=None, strict=None, timeout=None):
    """Initialize the object.
    Args:
      host: the connection host.
      port: optional port.
      strict: strict connection.
      timeout: socket connection timeout value.
    """
    _HC.__init__(self, host, port, strict)
    self._timeout = timeout or TimeoutHTTPConnection._timeout
    if self._timeout: self._timeout = float(self._timeout)

  def connect(self):
    """Perform the socket level connection.
    A new socket object will get built everytime. If the connection
    object has _timeout attribute, it will be set as the socket
    timeout value.
    Raises:
      HTTPConnectionTimeoutError: when timeout is hit
      socket.error: when other general socket errors encountered.
    """
    msg = "getaddrinfo returns an empty list"
    err = socket.error
    for res in socket.getaddrinfo(self.host, self.port, 0,
                                  socket.SOCK_STREAM):
      af, socktype, proto, canonname, sa = res
      try:
        try:
          self.sock = socket.socket(af, socktype, proto)
          if self._timeout: self.sock.settimeout(self._timeout)
          if self.debuglevel > 0:
            print "connect: (%s, %s)" % (self.host, self.port)
          self.sock.connect(sa)
        except socket.timeout, msg:
          err = socket.timeout
          if self.debuglevel > 0:
            print 'connect timeout:', (self.host, self.port)
          self.sock = _clear(self.sock)
          continue
        break
      except socket.error, msg:
        if self.debuglevel > 0:
          print 'general connect fail:', (self.host, self.port)
        self.sock = _clear(self.sock)
        continue
      break
    if not self.sock:
      if err == socket.timeout:
        raise HTTPConnectionTimeoutError, msg
      raise err, msg

class TimeoutHTTPHandler(_H):
  """A timeout enabled HTTPHandler for urllib2."""
  def __init__(self, timeout=None, debuglevel=0):
    """Initialize the object.
    Args:
      timeout: the socket connect timeout value.
      debuglevel: the debuglevel level.
    """
    _H.__init__(self, debuglevel)
    TimeoutHTTPConnection._timeout = timeout

  def http_open(self, req):
    """Use TimeoutHTTPConnection to perform the http_open"""
    return self.do_open(TimeoutHTTPConnection, req)

#---------------- end timeout on socket ops ----------------#
#
# Print out node name
#
print "node: " + os.uname()[1] 
#
# Check that environmental variable SAME_OK is set
#
if not os.environ.has_key("SAME_OK"):
	print "test_squid.py: Error. SAME_OK not defined"
	print >> sys.stderr, 1
	sys.exit(1)
same_ok = int(os.environ["SAME_OK"])    
#
# Check that environmental variable SAME_ERROR is set
#
if not os.environ.has_key("SAME_ERROR"):
	print "test_squid.py: Error. SAME_ERROR not defined"
	print >> sys.stderr, 1
	sys.exit(1)
same_error = int(os.environ["SAME_ERROR"])    
#
# Check that envrionmental variable SAME_WARNING is set
#
if not os.environ.has_key("SAME_WARNING"):
	print "test_squid.py: Error. SAME_WARNING not defined"
	print >> sys.stderr, 1
	sys.exit(1)
same_warning = int(os.environ["SAME_WARNING"])
#
# Check that environmental variable CMS_PATH is set
#
if not os.environ.has_key("CMS_PATH"):
	print "test_squid.py: Error. CMS_PATH not defined"
	print >> sys.stderr, same_error
	sys.exit(same_error)
#
# Check that file $CMS_PATH/SITECONF/local/JobConfig/site-local-config.xml
# exists
#
slcfil = os.environ["CMS_PATH"] + \
         "/SITECONF/local/JobConfig/site-local-config.xml"
print 'SiteLocalConfig: ' + slcfil
if not os.path.exists(slcfil):
	print "test_squid.py: Error. file " + slcfil + " does not exist"
	print >> sys.stderr, same_error
	sys.exit(same_error)
#
# Print out site-local-config.xml
#
print "\nContents of site-local-config.xml are:"
fileobj = open(slcfil,'r')
slcprint = fileobj.read()
slcprint = slcprint.replace('<','&lt;')
print slcprint
fileobj.close()
#
# Read and parse site-local-config.xml into a dom
# See http://docs.python.org/lib/module-xml.dom.minidom.html
#
slcdom = parse(slcfil)
#
# Work out site name from site-local-config.xml
#
silist = slcdom.getElementsByTagName("site")
if len(silist) == 0:
	site = "UNKNOWN"
else:
	stag = silist[0]
	site = stag.getAttribute("name")
print "site: " + site    
#
# Work out local FroNtier squid server from site-local-config.xml
#
# Check for at least one proxy or proxyconfig tag
#
prlist = [x.getAttribute('url') for x in slcdom.getElementsByTagName("proxy")]
if len(prlist) == 0:
	prcfglist = [x.getAttribute('url') for x in slcdom.getElementsByTagName("proxyconfig")]
	if len(prcfglist) == 0:
		print "test_squid.py: Error. no proxy or proxyconfig tag in file " + slcfil
		print >> sys.stderr, same_error
		sys.exit(same_error)    
	print
	print "test_squid.py: only proxyconfig urls defined, ignoring squids for now"
	print
# 
# Check whether has load balance proxies from site-local-config.xml
# 
load = slcdom.getElementsByTagName("load")
if len(load) == 0:
	loadtag = "None"
else:
	loadtag = load[0].getAttribute("balance")
print "loadtag: " + loadtag
#
# Print script version information
#
print "script version: " + __revision__
#
# Set server for urllib2
#
frontierUrl = "http://cmsfrontier.cern.ch:8080/FrontierProd/Frontier"
#
# Set frontierId for later use
#
tvers = __revision__.split()[2]
# print "tvers: " + tvers
frontierId = "test_squid.py " + tvers
# print "frontierId: " + frontierId
#
# The following follows code from Sinisa Veseli 
#
# Set parameters
#
frontierQuery = "SELECT 1 FROM DUAL"
decodeFlag = True
refreshFlag = True
retrieveZiplevel = ""
#
# Print parameters
#  
print "Using Frontier URL: " + frontierUrl
print "Query: " + frontierQuery
# print "Decode results: " + str(decodeFlag)
# print "Refresh cache: " + str(refreshFlag)
#
# Encode query
#
compQuery = zlib.compress(frontierQuery, 9)
encQuery = base64.binascii.b2a_base64(compQuery).replace("+", ".")
#
# Set up FroNtier request
#
format = "%s?type=frontier_request:1:DEFAULT&encoding=BLOB%s&p1=%s"
#
# Start and time query
#
queryStart = time.localtime()
print "\nQuery started: " + time.strftime("%m/%d/%y %H:%M:%S %Z", queryStart)
t1 = time.time()
if len(prlist) == 0:
    test_result = "OK"
else:
    test_result = "Failed"
ever_failed = "False"
#
for squid in prlist:
    #
    # Set proxy server
    #
	print "squid: " + squid   
	os.environ["http_proxy"] = squid
	os.environ["HTTP_PROXY"] = squid
    #
    # Create request
    #
	frontierRequest = format % (frontierUrl, retrieveZiplevel, encQuery)
	print "\nFrontier Request:\n", frontierRequest.replace('&','&amp;') 
    #
    # Add refresh header if needed
    #
	proxy_support = urllib2.ProxyHandler({'http': squid})
	opener = urllib2.build_opener(proxy_support, urllib2.HTTPHandler)
	urllib2.install_opener(opener)
	request = urllib2.Request(frontierRequest)
	if refreshFlag:
		request.add_header("pragma", "no-cache")
    #
    # Add Frontier-ID header
    #
	request.add_header("X-Frontier-Id", frontierId)
    #
	try:
		if _under_24():
					#stderr is for exit codes, let's print to stdout
                	#print >> sys.stderr, "*WARNING:* no timeout available in python older than 2.4"
            		print "*WARNING:* no timeout available in python older than 2.4"
            		result = urllib2.urlopen(request).read()
		elif _under_26():
			sethttptimeout(10)
			result = urllib2.urlopen(request).read()
		else:
			result = urllib2.urlopen(request,None,10).read()
	except urllib2.HTTPError, e1:
		message1 = e1.msg
		if message1 == "Forbidden":
			print "test_squid.py: Error. squid " + squid + " refused request."
			print "                      urllib2.HTTPError: " + message1
			ever_failed = "True"
			continue
		else:
			print "test_squid.py: Error. squid " + squid + " is down, "
			print "                      unreachable or will not reply."
			print "                      urllib2.HTTPError: " + message1
			ever_failed = "True"
			continue
	except urllib2.URLError, e2:
		message2 = e2.reason
		print "test_squid.py: Error. squid " + squid + " is down, "
		print "                      unreachable or will not reply."
		print "                      urllib2.URLError: "
		print message2
                ever_failed = "True"
		continue
	except:
		print "test_squid.py: Error."
		ever_failed = "True"
		continue
    #
	t2 = time.time()
	queryEnd = time.localtime()
    #
    # Check on length of output
    # 
	size = len(result)
    # print "size: " + str(size)
	if size == 0:
		print "test_squid.py: Error. no output"
		ever_failed = "True"
		continue
	print "Query ended: " + time.strftime("%m/%d/%y %H:%M:%S %Z", queryEnd)
	print "Query time: %0.2f [seconds]\n" % (t2-t1)
    # duration = (t2-t1)
    # print duration, size, size/duration
    #
    # Print out result
    #
	if decodeFlag:
		webprint = result.replace('<','&lt;')
		print "Query result:\n" + webprint
		dom = parseString(result)
        #
        # Check error code in result
        #
		qlist = dom.getElementsByTagName("quality")
		qtag = qlist[0]
		ecode = int(qtag.getAttribute("error"))
        # print "ecode: " + str(ecode)
		if ecode != 0:
			message3 = qtag.getAttribute("message")
			print "test_squid.py: Error. " + message3
			ever_failed = "True"
			continue
        #
        # Decode result
        #      
		dataList = dom.getElementsByTagName("data")
        # Control characters represent records, but I won't bother with that now,
        # and will simply replace those by space.
		keepalives = 0
		for data in dataList:
			for node in data.childNodes:
				# <keepalive /> elements may be present, combined with whitespace text
				if node.nodeName == "keepalive":
				# this is of type Element
					keepalives += 1
        				continue
      				# else assume of type Text
      				if node.data.strip() == "":
        				continue
      				if keepalives > 0:
					print keepalives, "keepalives received\n"
					keepalives = 0


				row = base64.decodestring(node.data)
				if retrieveZiplevel != "":
					row = zlib.decompress(row)
				control = [ '\x00', '\x01', '\x02', '\x03', '\x04',
                            '\x05', '\x06', '\x08', '\x09', '\x0a',
                            '\x0b', '\x0c', '\x0d', '\x1b', '\x17'  ]    
				for c in control:
					row = row.replace(c, ' ')
				print "\nFields: "
				endFirstRow = row.find('\x07')
				firstRow = row[:endFirstRow]
				for c in firstRow:
					if curses.ascii.isctrl(c):
						firstRow = firstRow.replace(c, '\n')
				print firstRow
				print "\nRecords:"
				pos = endFirstRow + 1
				while True:
					newrow = row[pos:]
					endRow = newrow.find('\x07')
					if endRow < 0:
						break
					fixedRow = newrow[:endRow]
					pos = pos + endRow + 1
					fixedRow = fixedRow.replace('\n', '')
					print fixedRow
		test_result = "OK"
#
# chek test_result here
# test_result = OK - one of the load balance proxies success
# test_result = Failed - all squids failed
#
if test_result == "OK" and ever_failed == "False":
	print "OK"
	sys.exit(same_ok)
	print >> sys.stderr, same_ok
if test_result == "OK" and ever_failed == "True":
	print "test_squid.py: One of the load balance Squid proxies " + test_result
	sys.exit(same_warning)
	print >> sys.stderr, same_warning
print "test_squid.py: All squid(s) failed"
sys.exit(same_error)
print >> sys.stderr, same_error
