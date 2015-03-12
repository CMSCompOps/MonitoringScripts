# aaltunda - ali.mehmet.altundag@cern.ch
# mtaze    - maric.taze@cern.ch

import urllib2, httplib, os

def read(url, request = False, header = {}):
    if request: return readCert(url, request)
    request = urllib2.Request(url, headers=header)
    urlObj  = urllib2.urlopen(request)
    data    = urlObj.read()
    return data

def readCert(url, request):
    conn  =  httplib.HTTPSConnection(url, cert_file = os.getenv('X509_USER_PROXY'),
                                          key_file  = os.getenv('X509_USER_PROXY'))
    r1=conn.request("GET", request)
    r2=conn.getresponse()
    request = r2.read()
    return request
