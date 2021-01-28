#!/data/cmssst/packages/bin/python3.7
# ########################################################################### #
# python script to query the FTS results in ElasticSearch via the grafana
#    front-end or read documents from HDFS in MonIT, evaluate link and site
#    status, and upload new or changed results to MonIT HDFS. The script
#    checks/updates 15 min, 1 hour, 6 hour, and 1 day results, depending on
#    the execution time.
#
# 2019-Jun-24   Stephan Lammel
# ########################################################################### #
# 'metadata': {
#     'path':      "fts15min",
#     'timestamp': 1464871600000
# },
# "data": {
#      "name":    "T1_US_FNAL" | "cmsdcadisk01.fnal.gov___eoscmsftp.cern.ch",
#      "type":    "site" | "source" | "destination" | "link",
#      "status":  "ok" | "warning" | "error" | "unknown"
#      "quality": 0.000 | null,
#      "detail":  "ok: 2 files, 46.7 GB [...]\n
#                  src_permission: 1 file, 12.1 GB [...]\n
#                  trn_timeout: 5 files, 64.3 GB [...]\n
#                  trn-error: 2 files, 34.1 GB [...]"
#      "detail":  "excluded from the source endpoint evaluation\n
#                  Transfers: 12 files, 87.5 GBytes ok\n
#                  Errors: dst_perm: 1, trn_tout: 1, src_err: 2\n
#                  Links: 6 ok, 2 warning, 1 unknown, 2 bad-source"
#      "detail":  "Transfers (from/to):  21/3 files, 2.3/10.1 TBytes ok\n
#                  Errors: src_perm: 3, trn_usr: 1, dst_perm: 1, foreign: 1\n
#                  Links (from/to): 24/23 ok, 0/1 error, 1/1 bad-endpoint\n
#                  cmsdcatape01.fnal.gov (from/to): error/ok\n
#                  cmsdcadisk01.fnal.gov (from/to): ok/ok"
# }
# https://cmsfts3.fnal.gov:8449/fts3/ftsmon/#/18d86488-94d4-11e9-a93b-a0369f23d0c0
#                                            ^job/
# https://fts3.cern.ch:8449/fts3/ftsmon/#/0ba2268e-98d3-11e9-9127-02163e01845e
#                                        ^job/
# https://Imperial-FTS-IPv6:8449/fts3/ftsmon/#/ddba3826-98d0-11e9-9ff9-525400e091e6
#         ^fts00.grid.hep.ph.ic.ac.uk         ^job/
# https://FTS-MIT:8449/fts3/ftsmon/#/52c192be-9894-11e9-a1d6-001ec9adc410
#         ^t3serv019.mit.edu        ^job/



import os, sys
import logging
import time, calendar
import math
import socket
import urllib.request, urllib.error
import json
import re
import gzip
#
# setup the Java/HDFS/PATH environment for pydoop to work properly:
os.environ["HADOOP_CONF_DIR"] = "/opt/hadoop/conf/etc/analytix/hadoop.analytix"
os.environ["JAVA_HOME"]       = "/etc/alternatives/jre"
os.environ["HADOOP_PREFIX"]   = "/usr/hdp/hadoop"
import pydoop.hdfs
# ########################################################################### #



#EVFTS_BACKUP_DIR = "./junk"
EVFTS_BACKUP_DIR = "/data/cmssst/MonitoringScripts/fts/failed"
# ########################################################################### #



class FTSmetric:
    'CMS Site Support Team FTS metric class'

    staticErrorList = []

    def __init__(self):
        self.mtrc = {}
        return


    @staticmethod
    def interval(metric_name=None):
        FTS_METRICS = {'fts15min':  900, 'fts1hour':  3600,
                                         'fts6hour': 21600, 'fts1day':  86400 }
        #
        if metric_name is None:
            return FTS_METRICS
        #
        try:
            return FTS_METRICS[ metric_name ]
        except KeyError:
            return 0


    @staticmethod
    def metric_order(metric):
        """function to determine the sort order of FTS metrics"""
        SORT_ORDER = {'fts15min': 1, 'fts1hour': 2, 'fts6hour': 3, 'fts1day': 4}

        try:
            return [ SORT_ORDER[ metric[0] ], metric[1] ]
        except KeyError:
            return [ 0, metric[1] ]


    @staticmethod
    def hosts2link(source_host=None, destination_host=None):
        """function to compose a link string from source/destination hosts"""
        if (( source_host is None ) or ( destination_host is None )):
            logging.error("Missing host name(s) to compose link")
            return None
        #
        # in case provided hosts are really endpoints:
        source_host = source_host.split("/")[-1].split(":")[0]
        destination_host = destination_host.split("/")[-1].split(":")[0]
        if ( source_host.count(".") < 2 ):
            logging.error("Bad source host name: %s" % source_host)
            return None
        if ( destination_host.count(".") < 2 ):
            logging.error("Bad destination host name: %s" % destination_host)
            return None
        #
        link = source_host.lower() + "___" + destination_host.lower()
        link = link.replace(" ", "")
        #
        linkRegex = re.compile(r"^(([a-z0-9\-]+)\.)+[a-z0-9\-]+___(([a-z0-9\-]+)\.)+[a-z0-9\-]+$")
        if linkRegex.match(link) is None:
            logging.error("Bad link name composed: %s" % link)
            return None
        return link


    @staticmethod
    def link2hosts(link_name=None):
        """function to extract source/destinaton hosts from a link name"""
        if link_name is None:
            return [None, None]
        #
        linkRegex = re.compile(r"^(([a-z0-9\-]+)\.)+[a-z0-9\-]+___(([a-z0-9\-]+)\.)+[a-z0-9\-]+$")
        if linkRegex.match(link_name) is None:
            logging.error("Bad link name: %s" % link_name)
            return [None, None]
        return link_name.split("___")


    @staticmethod
    def classify(error_scope, error_code, error_message, link_name, \
                 file_size, transfer_activity):
        """function to classify transfer results into counting classes"""

        error_lower = error_message.lower()
        #
        if ( error_code == 0 ):
            return "trn_ok"
        elif (( file_size >= 21474836480 ) or
              ( error_lower.find("certificate has expired") >= 0 ) or
              ( error_lower.find("operation canceled by user") >= 0 ) or
              ( error_lower.find("path/url invalid") >= 0 ) or
              ( error_lower.find("file exists and overwrite is not enabled") \
                                                                       >= 0 )):
            return "trn_usr"
        elif (( transfer_activity == "ASO" ) and
              (( error_lower.find("disk quota exceeded") >= 0 ) or
               ( error_message.find("NoFreeSpaceException") >= 0 ) or
               ( error_lower.find("not enough space") >= 0 ) or
               ( error_lower.find("no free space") >= 0 ))):
            return "trn_usr"
        elif (( error_scope == "TRANSFER" ) and
              (( error_lower.find("no route to host") >= 0 ) or
               ( error_lower.find("could not open connection to") >= 0 ) or
               ( error_lower.find("unable to connect") >= 0 ) or
               ( error_lower.find("failed to connect") >= 0 ) or
               ( error_lower.find("network is unreachable") >= 0 ))):
            return "trn_err"
        #
        #
        elif ( error_scope == "SOURCE" ):
            classfcn = "src_err"
        elif ( error_scope == "DESTINATION" ):
            classfcn = "dst_err"
        elif ( error_message[:6] == "SOURCE" ):
            classfcn = "src_err"
        elif ( error_message[:11] == "DESTINATION" ):
            classfcn = "dst_err"
        elif (( error_message.find("SOURCE") > 0 ) and
              ( error_message.find("DESTINATION") < 0 )):
            classfcn = "src_err"
        elif (( error_message.find("DESTINATION") > 0 ) and
              ( error_message.find("SOURCE") < 0 )):
            classfcn = "dst_err"
        else:
            classfcn = "trn_err"
            #
            #
            src_host, dst_host = FTSmetric.link2hosts(link_name)
            #
            try:
                domain = src_host.split(".",1)[-1]
                if (( error_lower.find(src_host) >= 0 ) or
                    ( error_lower.find(domain) >= 0 )):
                    classfcn = "src_err"
                else:
                    ipaddrList = socket.getaddrinfo(src_host, None,
                                                       type=socket.SOCK_STREAM)
                    for tuple in ipaddrList:
                        if ( tuple[0] == socket.AddressFamily.AF_INET ):
                            domain = tuple[4][0].rsplit(".", 1)[0] + "."
                        elif ( tuple[0] == socket.AddressFamily.AF_INET6 ):
                            domain = tuple[4][0].rsplit(":", 1)[0]
                            if ( domain[-1] != ":" ):
                                domain = domain + ":"
                        else:
                            continue
                        ipAddr = tuple[4][0]
                        if (( error_lower.find(ipAddr) >= 0 ) or
                            ( error_lower.find(domain) >= 0 )):
                            classfcn = "src_err"
            except (TypeError, socket.gaierror, AttributeError):
                pass
            #
            try:
                domain = dst_host.split(".",1)[-1]
                if (( error_lower.find(dst_host) >= 0 ) or
                    ( error_lower.find(domain) >= 0 )):
                    if ( classfcn == "src_err" ):
                        classfcn = "trn_err"
                    else:
                        classfcn = "dst_err"
                else:
                    ipaddrList = socket.getaddrinfo(dst_host, None,
                                                       type=socket.SOCK_STREAM)
                    for tuple in ipaddrList:
                        if ( tuple[0] == socket.AddressFamily.AF_INET ):
                            domain = tuple[4][0].rsplit(".", 1)[0] + "."
                        elif ( tuple[0] == socket.AddressFamily.AF_INET6 ):
                            domain = tuple[4][0].rsplit(":", 1)[0]
                            if ( domain[-1] != ":" ):
                                domain = domain + ":"
                        else:
                            continue
                        ipAddr = tuple[4][0]
                        if (( error_lower.find(ipAddr) >= 0 ) or
                            ( error_lower.find(domain) >= 0 )):
                            if ( classfcn == "src_err" ):
                                classfcn = "trn_err"
                            else:
                                classfcn = "dst_err"
            except (TypeError, socket.gaierror, AttributeError):
                pass
        #
        #
        #
        #
        if ( classfcn == "src_err" ):
            # sub-classify source further: _perm, _miss, _err
            if (( error_code ==   1 ) or
                ( error_code ==  13 )):
                return "src_perm"
            elif ( error_code ==   2 ):
                return "src_miss"
            elif (( error_lower.find("credential") >= 0 ) or
                  ( error_lower.find("permission denied") >= 0 ) or
                  ( error_lower.find("insufficient user privileges") >= 0 ) or
                  ( error_message.find("Authorization denied") >= 0 ) or
                  ( error_lower.find("establishing access rights") >= 0 ) or
                  ( error_lower.find("authorization error") >= 0 ) or
                  ( error_lower.find("certificate issued for a diff") >= 0 )):
                return "src_perm"
            elif (( error_lower.find("no such file or directory") >= 0 ) or
                  ( error_lower.find("file not found") >= 0 ) or
                  ( error_lower.find("file is unavailable") >= 0 ) or
                  ( error_lower.find("file is not online") >= 0 ) or
                  ( error_lower.find("no read pools online") >= 0 ) or
                  ( error_lower.find("file invalidated while queuing") >= 0 )):
                return "src_miss"
            #
            if ( logging.getLogger().level > 25 ):
                return classfcn
        #
        #
        #
        elif ( classfcn == "trn_err" ):
            # sub-classify transfer further: _tout, _err (+ _ok, _usr)
            if (( error_lower.find("operation timed out") >= 0 ) or
                ( error_lower.find("connection timed out") >= 0 ) or
                ( error_lower.find("idle timeout") >= 0 ) or
                ( error_lower.find("performance marker timeout") >= 0 ) or
                ( error_lower.find("timeout expired") >= 0 )):
                return "trn_tout"
            elif ( error_lower.find("file not found") >= 0 ):
                return "src_miss"
            elif (( error_message.find("File exists") >= 0 ) or
                  ( error_lower.find("rm() fail") >= 0 ) or
                  ( error_lower.find("impossible to unlink") >= 0 )):
                return "dst_perm"
            elif ( error_lower.find("mkdir") >= 0 ):
                return "dst_path"
            elif (( error_lower.find("disk quota exceeded") >= 0 ) or
                  ( error_lower.find("all pools are full") >= 0 ) or
                  ( error_lower.find("unable to reserve space") >= 0 ) or
                  ( error_message.find("NoFreeSpaceException") >= 0 ) or
                  ( error_lower.find("no write pools online") >= 0 ) or
                  ( error_lower.find("no space left on device") >= 0 ) or
                  ( error_lower.find("not enough space") >= 0 ) or
                  ( error_lower.find("no free space") >= 0 ) or
                  ( error_lower.find("unable to get quota space") >= 0 )):
                return "dst_spce"
            elif ( error_message.find("error in write into HDFS") >= 0 ):
                return "dst_err"
            #
            if ( logging.getLogger().level > 25 ):
                return classfcn
        #
        #
        #
        elif ( classfcn == "dst_err" ):
            # sub-classify destination further: _perm, _path, _spce, _err
            if (( error_code ==   1 ) or
                ( error_code ==  13 ) or
                ( error_code ==  16 ) or
                ( error_code ==  17 ) or
                ( error_code ==  30 )):
                return "dst_perm"
            elif (( error_code ==   2 ) or
                  ( error_code ==  19 ) or
                  ( error_code ==  20 )):
                return "dst_path"
            elif (( error_code ==  23 ) or
                  ( error_code ==  28 ) or
                  ( error_code == 122 )):
                return "dst_spce"
            elif (( error_message.find("Operation not permitted") >= 0 ) or
                  ( error_message.find("Permission denied") >= 0 ) or
                  ( error_message.find("Device or resource busy") >= 0 ) or
                  ( error_message.find("File exists") >= 0 ) or
                  ( error_message.find("Read-only file system") >= 0 ) or
                  ( error_message.find("Authorization denied") >= 0 ) or
                  ( error_lower.find("authentication failed") >= 0 ) or
                  ( error_lower.find("system error in unlink") >= 0 ) or
                  ( error_lower.find("login incorrect") >= 0 ) or
                  ( error_lower.find("certificate verify failed") >= 0 ) or
                  ( error_lower.find("authentication negotiation") >= 0 ) or
                  ( error_lower.find("commands denied") >= 0 )):
                return "dst_perm"
            elif (( error_message.find("No such file or directory") >= 0 ) or
                  ( error_message.find("No such device") >= 0 ) or
                  ( error_message.find("Not a directory") >= 0 ) or
                  ( error_message.find("MAKE_PARENT") >= 0 ) or
                  ( error_message.find("][Mkdir][") >= 0 )):
                return "dst_path"
            elif (( error_message.find("File table overflow") >= 0 ) or
                  ( error_message.find("No space left on device") >= 0 ) or
                  ( error_lower.find("quota exceeded") >= 0 ) or
                  ( error_lower.find("no free space") >= 0 ) or
                  ( error_lower.find("unable to get quota space") >= 0 ) or
                  ( error_lower.find("space management step") >= 0 )):
                return "dst_spce"
            #
            if ( logging.getLogger().level > 25 ):
                return classfcn
        #
        #
        #
        #
        if ( classfcn == "src_err" ):
            if (( error_lower.find("communication error") >= 0 ) or
                ( error_lower.find("connection reset") >= 0 ) or
                ( error_lower.find("connection closed") >= 0 ) or
                ( error_lower.find("unable to connect") >= 0 ) or
                ( error_lower.find("could not connect to") >= 0 ) or
                ( error_lower.find("timed out") >= 0 ) or
                ( error_lower.find("timeout") >= 0 ) or
                ( error_lower.find("problem while connected to") >= 0 ) or
                ( error_lower.find("incompatible with current file") >= 0 ) or
                ( error_message.find("internal HDFS error") >= 0 ) or
                ( error_message.find("error in reading from HDFS") >= 0 ) or
                ( error_message.find(" 451 End") >= 0 ) or
                ( error_lower.find("open file for checksumming") >= 0 ) or
                ( error_lower.find("operation was aborted") >= 0 ) or
                ( error_lower.find("an end of file occurred") >= 0 ) or
                ( error_lower.find("commands denied") >= 0 ) or
                ( error_lower.find("checksum do not match") >= 0 ) or
                ( error_lower.find("checksum mismatch") >= 0 ) or
                ( error_lower.find("protocol(s) not supported") >= 0 ) or
                ( error_lower.find("internal server error") >= 0 ) or
                ( error_message.find("Broken pipe") >= 0 ) or
                ( error_message.find("Unable to build the TURL") >= 0 ) or
                ( error_message.find("TTL exceeded") >= 0 ) or
                ( error_lower.find("operation canceled") >= 0 ) or
                ( error_lower.find("input/output error") >= 0 ) or
                ( error_lower.find("connection limit exceeded") >= 0 ) or
                ( error_lower.find("local filesystem has problems") >= 0 ) or
                ( error_lower.find("failed to pin file") >= 0 ) or
                ( error_lower.find("stale file handle") >= 0 ) or
                ( error_lower.find("failed to abort transfer") >= 0 ) or
                ( error_lower.find("error in failed to open checksum") >= 0 ) or
                ( error_lower.find("error in failed to read checksum") >= 0 ) or                ( error_message.find("SURL is not pinned") >= 0 )):
                return classfcn
        elif ( classfcn == "trn_err" ):
            if (( error_lower.find("no such file or directory") >= 0 ) or
                ( error_lower.find("unable to open file") >= 0 ) or
                ( error_lower.find("login failed") >= 0 ) or
                ( error_lower.find("login incorrect") >= 0 ) or
                ( error_lower.find("transfer failed") >= 0 ) or
                ( error_lower.find("checksum mismatch") >= 0 ) or
                ( error_lower.find("connection reset") >= 0 ) or
                ( error_lower.find("connection timed out") >= 0 ) or
                ( error_lower.find("internal timeout") >= 0 ) or
                ( error_message.find("internal HDFS error") >= 0 ) or
                ( error_lower.find("an end of file occurred") >= 0 ) or
                ( error_lower.find("protocol family not supported") >= 0 ) or
                ( error_lower.find("problem while connected to") >= 0 ) or
                ( error_lower.find("no such file or directory") >= 0 ) or
                ( error_lower.find("authentication failed") >= 0 ) or
                ( error_lower.find("upload aborted") >= 0 ) or
                ( error_lower.find("operation canceled") >= 0 ) or
                ( error_lower.find("operation was aborted") >= 0 ) or
                ( error_lower.find("aborting transfer") >= 0 ) or
                ( error_lower.find("input/output error") >= 0 ) or
                ( error_lower.find("an unknown error occurred") >= 0 ) or
                ( error_lower.find("transfer was forcefully killed") >= 0 ) or
                ( error_lower.find("stream ended before eod") >= 0 ) or
                ( error_lower.find("file size mismatch") >= 0 ) or
                ( error_lower.find("internal server error") >= 0 ) or
                ( error_lower.find("operation not permitted") >= 0 ) or
                ( error_message.find("Permission denied") >= 0 ) or
                ( error_message.find("Broken pipe") >= 0 ) or
                ( error_message.find("Invalid argument") >= 0 ) or
                ( error_message.find("SSL handshake problem") >= 0 ) or
                ( error_message.find("IPC failed") >= 0 ) or
                ( error_message.find(" 501 Port number") >= 0 ) or
                ( error_message.find(" 500 Authorization error") >= 0 ) or
                ( error_message.find(" 500 End") >= 0 ) or
                ( error_message.find(" 530 Login denied") >= 0 ) or
                ( error_message.find(" 451 End") >= 0 ) or
                ( error_message.find(" 451 Failed to deliver Pool") >= 0 ) or
                ( error_message.find(" 451 FTP proxy did not shut") >= 0 ) or
                ( error_message.find(" 451 General problem") >= 0 ) or
                ( error_message.find(" 451 Post-processing failed") >= 0 ) or
                ( error_message.find(" 431 Internal error") >= 0 ) or
                ( error_lower.find("failed to deliver pnfs") >= 0 ) or
                ( error_lower.find("block with unknown descriptor") >= 0 ) or
                ( error_lower.find("certificate verify failed") >= 0 ) or
                ( error_lower.find("transfer has been aborted") >= 0 ) or
                ( error_lower.find("transfer cancelled") >= 0 ) or
                ( error_lower.find("handle not in the proper state") >= 0 ) or
                ( error_lower.find("error closing xrootd file handle") >= 0 ) or
                ( error_lower.find("stream was closed") >= 0 ) or
                ( error_lower.find("failed to open file") >= 0 ) or
                ( error_lower.find("copy failed with mode 3rd p") >= 0 ) or
                ( error_lower.find("connection limit exceeded") >= 0 ) or
                ( error_lower.find("error while searching for end") >= 0 ) or
                ( error_lower.find("stale file handle") >= 0 ) or
                ( error_lower.find("could not verify credential") >= 0 ) or
                ( error_lower.find("redirect limit has been reached") >= 0 ) or
                ( error_lower.find("operation expired") >= 0 ) or
                ( error_lower.find("invalid address") >= 0 ) or
                ( error_lower.find("upload not yet completed") >= 0 ) or
                ( error_lower.find("cannot allocate memory") >= 0 ) or
                ( error_lower.find("does not exist") >= 0 )):
                return classfcn
        elif ( classfcn == "dst_err" ):
            if (( error_lower.find("communication error") >= 0 ) or
                ( error_lower.find("no route to host") >= 0 ) or
                ( error_lower.find("could not open connection to") >= 0 ) or
                ( error_lower.find("unable to connect") >= 0 ) or
                ( error_lower.find("no route to host") >= 0 ) or
                ( error_lower.find("connection refused") >= 0 ) or
                ( error_lower.find("connection reset") >= 0 ) or
                ( error_lower.find("connection closed") >= 0 ) or
                ( error_lower.find("timed out") >= 0 ) or
                ( error_lower.find("timeout") >= 0 ) or
                ( error_lower.find("operation canceled") >= 0 ) or
                ( error_lower.find("problem while connected to") >= 0 ) or
                ( error_lower.find("incompatible with current file") >= 0 ) or
                ( error_message.find("internal HDFS error") >= 0 ) or
                ( error_message.find("error in write into HDFS") >= 0 ) or
                ( error_message.find("Failed to close file in HDFS") >= 0 ) or
                ( error_message.find(" 500 End") >= 0 ) or
                ( error_message.find(" 451 End") >= 0 ) or
                ( error_message.find("ERROR: deadlock detected") >= 0 ) or
                ( error_message.find(" 451 Failed to deliver Pool") >= 0 ) or
                ( error_lower.find("unable to open file") >= 0 ) or
                ( error_lower.find("no data available") >= 0 ) or
                ( error_lower.find("file size mismatch") >= 0 ) or
                ( error_lower.find("checksum mismatch") >= 0 ) or
                ( error_lower.find("internal server error") >= 0 ) or
                ( error_lower.find("an end of file occurred") >= 0 ) or
                ( error_message.find("][SRM_FILE_LIFETIME_EXPIRED]") >= 0 ) or
                ( error_message.find("][SRM_INTERNAL_ERROR]") >= 0 ) or
                ( error_message.find("][SRM_REQUEST_INPROGRESS]") >= 0 ) or
                ( error_message.find("][SRM_ABORTED]") >= 0 ) or
                ( error_message.find("][SRM_REQUEST_TIMED_OUT]") >= 0 ) or
                ( error_message.find("][SRM_FAILURE]") >= 0 ) or
                ( error_message.find("Broken pipe") >= 0 ) or
                ( error_lower.find("request aborted") >= 0 ) or
                ( error_lower.find("operation was aborted") >= 0 ) or
                ( error_lower.find("checksum value required") >= 0 ) or
                ( error_lower.find("protocol(s) not supported") >= 0 ) or
                ( error_lower.find("unknown error occurred") >= 0 ) or
                ( error_lower.find("service unavailable") >= 0 ) or
                ( error_message.find("Unable to build the TURL") >= 0 ) or
                ( error_lower.find("input/output error") >= 0 ) or
                ( error_lower.find("connection limit exceeded") >= 0 ) or
                ( error_lower.find("unexpected server error") >= 0 ) or
                ( error_lower.find("too many queued requests") >= 0 ) or
                ( error_lower.find("upload not yet completed") >= 0 ) or
                ( error_lower.find("no such request") >= 0 ) or
                ( error_lower.find("failed to process") >= 0 ) or
                ( error_lower.find("unable to write replica") >= 0 ) or
                ( error_lower.find("handshake_failure; redirections") >= 0 )):
                return classfcn
        if error_message not in FTSmetric.staticErrorList:
            FTSmetric.staticErrorList.append( error_message )
            #
            logging.log(25, "Unclassified %s error: %s [%d] %s" %
                        (classfcn[:3], error_scope, error_code, error_message))
        #
        return classfcn


    def fetch(self, metricList):
        """function to retrieve FTS link/site evaluation from MonIT"""
        # ############################################################## #
        # Retrieve all link/source/destination/site evaluations for the  #
        # (<metric-name>, <time-bin>) tuples in the provided metricList. #
        # ############################################################## #
        HDFS_PREFIX = "/project/monitoring/archive/cmssst/raw/ssbmetric/"
        oneDay = 24*60*60
        now = int( time.time() )
        #
        if metricList is None:
            timeFrst = 0
            timeLast = now
        else:
            t15mFrst = t1hFrst = t6hFrst = t1dFrst = now + oneDay
            timeLast = 0
            for mtrc in metricList:
                if ( mtrc[0] == "fts15min" ):
                    period = 900
                    t15mFrst = min(t15mFrst, mtrc[1] * period)
                elif ( mtrc[0] == "fts1hour" ):
                    period = 3600
                    t1hFrst = min(t1hFrst, mtrc[1] * period)
                elif ( mtrc[0] == "fts6hour" ):
                    period = 21600
                    t6hFrst = min(t6hFrst, mtrc[1] * period)
                elif ( mtrc[0] == "fts1day" ):
                    period = 86400
                    t1dFrst = min(t1dFrst, mtrc[1] * period)
                else:
                    continue
                timeLast = max(timeLast, ((mtrc[1] + 1) * period ) - 1)
            timeFrst = min(t15mFrst, t1hFrst, t6hFrst, t1dFrst)
        #
        oneDay = 24*60*60
        now = int( time.time() )
        start15mArea = max( calendar.timegm( time.gmtime(now - (6 * oneDay)) ),
                            t15mFrst - oneDay)
        start1hArea = max( calendar.timegm( time.gmtime(now - (6 * oneDay)) ),
                            t1hFrst - oneDay)
        start6hArea = max( calendar.timegm( time.gmtime(now - (6 * oneDay)) ),
                            t6hFrst - oneDay)
        start1dArea = max( calendar.timegm( time.gmtime(now - (6 * oneDay)) ),
                            t1dFrst - oneDay)
        limitLocalTmpArea = calendar.timegm( time.localtime( now ) ) + oneDay
        #
        logging.info("Retrieving FTS evaluation docs from MonIT HDFS")
        logging.log(15, "   between %s and %s" %
                       (time.strftime("%Y-%m-%d %H:%M", time.gmtime(timeFrst)),
                    time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime(timeLast))))
        #
        dirList = set()
        tis15min = now + oneDay
        tis1hour = now + oneDay
        tis6hour = now + oneDay
        tis1day  = now + oneDay
        tmp15mFlag = tmp1hFlag = tmp6hFlag = tmp1dFlag = False
        for mtrc in metricList:
            if ( mtrc[0] == "fts15min" ):
                tmp15mFlag = True
                dirDay = mtrc[1] * 900
                dirList.add( time.strftime("fts15min/%Y/%m/%d",
                                            time.gmtime( dirDay )) )
                tis15min = min(tis15min, dirDay)
            elif ( mtrc[0] == "fts1hour" ):
                tmp1hFlag = True
                dirDay = mtrc[1] * 3600
                dirList.add( time.strftime("fts1hour/%Y/%m/%d",
                                            time.gmtime( dirDay )) )
                tis1hour = min(tis1hour, dirDay)
            elif ( mtrc[0] == "fts6hour" ):
                tmp6hFlag = True
                dirDay = mtrc[1] * 21600
                dirList.add( time.strftime("fts6hour/%Y/%m/%d",
                                            time.gmtime( dirDay )) )
                tis6hour = min(tis6hour, dirDay)
            elif ( mtrc[0] == "fts1day" ):
                tmp1dFlag = True
                dirDay = mtrc[1] * 86400
                dirList.add( time.strftime("fts1day/%Y/%m/%d",
                                            time.gmtime( dirDay )) )
                tis1day = min(tis1day, dirDay)
        if ( tmp15mFlag ):
            for dirDay in range(start15mArea, limitLocalTmpArea, oneDay):
                dirList.add( time.strftime("fts15min/%Y/%m/%d.tmp",
                                            time.gmtime( dirDay )) )
        if ( tmp1hFlag ):
            for dirDay in range(start1hArea, limitLocalTmpArea, oneDay):
                dirList.add( time.strftime("fts1hour/%Y/%m/%d.tmp",
                                            time.gmtime( dirDay )) )
        if ( tmp6hFlag ):
            for dirDay in range(start6hArea, limitLocalTmpArea, oneDay):
                dirList.add( time.strftime("fts6hour/%Y/%m/%d.tmp",
                                            time.gmtime( dirDay )) )
        if ( tmp1dFlag ):
            for dirDay in range(start1dArea, limitLocalTmpArea, oneDay):
                dirList.add( time.strftime("fts1day/%Y/%m/%d.tmp",
                                            time.gmtime( dirDay )) )
        #
        dirList = sorted(dirList)

        # connect to HDFS, loop over directories and read FTs eval docs:
        # ==============================================================
        tmpDict = {}
        try:
            with pydoop.hdfs.hdfs() as myHDFS:
                for subDir in dirList:
                    logging.debug("   checking HDFS subdirectory %s" % subDir)
                    if not myHDFS.exists( HDFS_PREFIX + subDir ):
                        continue
                    # get list of files in directory:
                    myList = myHDFS.list_directory( HDFS_PREFIX + subDir )
                    fileNames = [ d['name'] for d in myList
                                  if (( d['kind'] == "file" ) and
                                      ( d['size'] != 0 )) ]
                    del myList
                    for fileName in fileNames:
                        logging.debug("   reading file %s" %
                                      os.path.basename(fileName))
                        fileHndl = fileObj = None
                        try:
                            if ( os.path.splitext(fileName)[-1] == ".gz" ):
                                fileHndl = myHDFS.open_file(fileName)
                                fileObj = gzip.GzipFile(fileobj=fileHndl)
                            else:
                                fileObj = myHDFS.open_file(fileName)
                            # read FTS evaluation documents in file:
                            for myLine in fileObj:
                                myJson = json.loads(myLine.decode('utf-8'))
                                try:
                                    metric = myJson['metadata']['path']
                                    if metric not in FTSmetric.interval():
                                        continue
                                    tbin = int( myJson['metadata']['timestamp']
                                       / ( FTSmetric.interval(metric) * 1000 ))
                                    mKey = (metric, tbin)
                                    if mKey not in metricList:
                                        continue
                                    if 'quality' not in myJson['data']:
                                        myJson['data']['quality'] = None
                                    if 'detail' not in myJson['data']:
                                        myJson['data']['detail'] = None
                                    name = myJson['data']['name']
                                    type = myJson['data']['type']
                                    vrsn = myJson['metadata']['kafka_timestamp']
                                    #
                                    eKey  = (name, type)
                                    value = (vrsn, myJson['data'])
                                    #
                                    if mKey not in tmpDict:
                                        tmpDict[mKey] = {}
                                    if eKey in tmpDict[mKey]:
                                        if ( vrsn <= tmpDict[mKey][eKey][0] ):
                                            continue
                                    tmpDict[mKey][eKey] = value
                                except KeyError:
                                    continue
                        except json.decoder.JSONDecodeError as excptn:
                            logging.error("JSON decoding failure, file %s: %s"
                                                     % (fileName, str(excptn)))
                        except FileNotFoundError as excptn:
                            logging.error("HDFS file not found, %s: %s" %
                                                       (fileName, str(excptn)))
                        except IOError as excptn:
                            logging.error("IOError accessing HDFS file %s: %s"
                                                     % (fileName, str(excptn)))
                        finally:
                            if fileObj is not None:
                                fileObj.close()
                            if fileHndl is not None:
                                fileHndl.close()
        except Exception as excptn:
            logging.error("Failed to fetch documents from MonIT HDFS: %s" %
                          str(excptn))


        # load FTS evaluation information into object:
        # ============================================
        cnt_docs = 0
        cnt_mtrc = len(tmpDict)
        for mtrcKey in tmpDict:
            self.add1metric(mtrcKey)
            for evalKey in tmpDict[mtrcKey]:
                cnt_docs += 1
                self.add1entry(mtrcKey, tmpDict[mtrcKey][evalKey][1])
        del tmpDict

        logging.info("   found %d relevant docs for %d (metric,time-bins)" %
                                                          (cnt_docs, cnt_mtrc))
        #
        return


    def metrics(self):
        """function to return list of FTS metrics in the object inventory"""
        # ############################################################# #
        # metrics are returned sorted by metric name (15m/1h/6h/1d) and #
        # time-bin                                                      #
        # ############################################################# #
        return sorted( self.mtrc.keys(),
                                      key=lambda m: FTSmetric.metric_order(m) )


    def evaluations(self, metric=None):
        """function to return a list of the evaluations for a metric tuple"""
        # ################################################################# #
        # metric is a tuple of metric-name and time-bin: ("fts1day", 16954) #
        # ################################################################# #
        if (( metric is None ) and ( len(self.mtrc) == 1 )):
            metric = next(iter( self.mtrc.keys() ))
        #
        return self.mtrc[ metric ]


    def links(self, metric=None):
        """function to return a list of links in the metric of the object"""
        # ################################################################# #
        # metric is a tuple of metric-name and time-bin: ("fts1day", 16954) #
        # ################################################################# #
        if (( metric is None ) and ( len(self.mtrc) == 1 )):
            metric = next(iter( self.mtrc.keys() ))
        #
        return [ e['name'] for e in self.mtrc[metric] \
                                                   if ( e['type'] == "link" ) ]


    def sites(self, metric=None):
        """function to return a list of sites in the metric of the object"""
        # ################################################################# #
        # metric is a tuple of metric-name and time-bin: ("fts1day", 16954) #
        # ################################################################# #
        if (( metric is None ) and ( len(self.mtrc) == 1 )):
            metric = next(iter( self.mtrc.keys() ))
        #
        return [ e['name'] for e in self.mtrc[metric] \
                                                   if ( e['type'] == "site" ) ]


    def status(self, metric, name, clss):
        """function to return the status of a link/source/destination/site"""
        # ################################################################# #
        # metric is a tuple of metric-name and time-bin: ("fts1day", 16954) #
        # name is a site (Tn_CC_*), source (*.*.*), destination (*.*.*), or #
        # link (*.*.*___*.*.*) name                                         #
        # clss is site, source, destination, or link                        #
        # return value is the status of the evaluation or None              #
        # ###################################################################
        if (( metric is None ) and ( len(self.mtrc) == 1 )):
            metric = next(iter( self.mtrc.keys() ))
        #
        for entry in self.mtrc[metric]:
            if (( entry['name'] == name ) and ( entry['type'] == clss )):
                return entry['status']
        #
        return "unknown"


    def get1entry(self, metric, name, clss):
        """return the entry of a link/source/destination/site evaluation"""
        # ################################################################# #
        # metric is a tuple of metric-name and time-bin: ("fts1day", 16954) #
        # name is a site (Tn_CC_*), source (*.*.*), destination (*.*.*), or #
        # link (*.*.*___*.*.*) name                                         #
        # clss is site, source, destination, or link                        #
        # return value is the evaluation dictionary {'name':,'status':,...} #
        # ###################################################################
        if (( metric is None ) and ( len(self.mtrc) == 1 )):
            metric = next(iter( self.mtrc.keys() ))
        #
        for entry in self.mtrc[metric]:
            if (( entry['name'] == name ) and ( entry['type'] == clss )):
                return entry
        #
        raise KeyError("No such entry %s / %s in (%s,%d)" % (name, clss,
                                                         metric[0], metric[1]))


    def add1metric(self, metric, data=None):
        """function to add an additional FTS metric to the object inventory"""
        if metric[0] not in FTSmetric.interval():
            raise ValueError("metric %s is not a valid FTS metric name" %
                             str(metric[0]))
        #
        if metric not in self.mtrc:
            if data is not None:
                self.mtrc[metric] = data
            else:
                self.mtrc[metric] = []
        elif data is not None:
            self.mtrc[metric].extend( data )
        return


    def add1entry(self, metric, entry):
        """function to add an additional link/site entry to a metric"""
        linkRegex = re.compile(r"^(([a-z0-9\-]+)\.)+[a-z0-9\-]+___(([a-z0-9\-]+)\.)+[a-z0-9\-]+$")
        hostRegex = re.compile(r"^(([a-z0-9\-]+)\.)+[a-z0-9\-]+$")
        siteRegex = re.compile(r"T\d_[A-Z]{2,2}_\w+")
        #
        # check entry has mandatory keys:
        if (( 'name' not in entry ) or ( 'type' not in entry ) or
                                       ( 'status' not in entry )):
            raise ValueError("Mandatory keys missing in entry %s" %
                             str(entry))
        #
        entry = entry.copy()
        if ( entry['type'] == "link" ):
            if ( linkRegex.match( entry['name'] ) is None ):
                raise ValueError("Illegal link name %s" % entry['name'])
            entry['name'] = entry['name'].lower()
        elif (( entry['type'] == "source" ) or
              ( entry['type'] == "destination" )):
            if ( hostRegex.match( entry['name'] ) is None ):
                raise ValueError("Illegal source/destination name %s" %
                                 entry['name'])
            entry['name'] = entry['name'].lower()
        elif ( entry['type'] == "site" ):
             if ( siteRegex.match( entry['name'] ) is None ):
                 raise ValueError("Illegal site name %s" % entry['name'])
        else:
            raise ValueError("Illegal type \"%s\" of name \"%s\"" % 
                             (entry['type'], entry['name']))
        #
        if 'quality' not in entry:
            entry['quality'] = None
        if 'detail' not in entry:
            entry['detail'] = None
        elif ( entry['detail'] == "" ):
            entry['detail'] = None
        #
        self.mtrc[metric].append( entry )
        #
        return


    def del1metric(self, metric):
        """function to remove an evaluation metric from the object inventory"""
        # ################################################################### #
        del self.mtrc[metric]


    def del1entry(self, metric, entry):
        """function to remove a link/.../site evaluation entry from a metric"""
        # ################################################################### #
        self.mtrc[metric].remove( entry )


    def compose_json(self):
        """function to extract a FTS-evaluations into a JSON string"""
        # ############################################################ #
        # compose a JSON string from the FTS evaluations in the object #
        # ############################################################ #

        jsonString = "["
        commaFlag = False
        #
        for metric in self.metrics():
            #
            interval = FTSmetric.interval( metric[0] )
            timestamp = ( interval * metric[1] ) + int( interval / 2 )
            hdrString = (",\n {\n   \"producer\": \"cmssst\",\n" +
                                "   \"type\": \"ssbmetric\",\n" +
                                "   \"path\": \"%s\",\n" +
                                "   \"timestamp\": %d000,\n" +
                                "   \"type_prefix\": \"raw\",\n" +
                                "   \"data\": {\n") % (metric[0], timestamp)
            #
            for type in ["link", "source", "destination", "site"]:
                tmpDict = {e['name']:e for e in self.mtrc[metric] \
                                                     if ( e['type'] == type ) }
                #
                for name in sorted( tmpDict.keys() ):
                    if commaFlag:
                        jsonString += hdrString
                    else:
                        jsonString += hdrString[1:]
                    jsonString += (("      \"name\": \"%s\",\n" +
                                    "      \"type\": \"%s\",\n" +
                                    "      \"status\": \"%s\",\n") %
                                   (tmpDict[name]['name'],
                                    tmpDict[name]['type'],
                                    tmpDict[name]['status']))
                    if tmpDict[name]['quality'] is not None:
                        jsonString += ("      \"quality\": %.3f,\n" %
                                       tmpDict[name]['quality'])
                    else:
                        jsonString += ("      \"quality\": null,\n")
                    if tmpDict[name]['detail'] is not None:
                        jsonString += ("      \"detail\": \"%s\"\n   }\n }" %
                                   tmpDict[name]['detail'].replace('\n','\\n'))
                    else:
                        jsonString += ("      \"detail\": null\n   }\n }")
                    commaFlag = True
        jsonString += "\n]\n"
        #
        return jsonString


    def dump(self, file=sys.stdout):
        """function to dump the contents of a FTS-evaluations object"""
        # ################################################################### #
        STATUS_CHAR = {'unknown': "?", 'ok': "o", 'warning': "w", 'error': "e"}
        #
        for metric in sorted( self.mtrc.keys() ):
            interval = FTSmetric.interval( metric[0] )
            timestamp = ( interval * metric[1] ) + int( interval / 2 )
            file.write("\nMetric \"%s\", %d (%s):\n" % (metric[0], metric[1],
                   time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime(timestamp))))
            #
            file.write("================================================\nLi" +
                       "nk Matrix:\n")
            hostList = set()
            lnkDict = {}
            for entry in self.mtrc[metric]:
                if ( entry['type'] != "link" ):
                    continue
                lnkDict[ entry['name'] ] = entry
                if ( entry['status'] == "unknown" ):
                    continue
                src_host, dst_host = FTSmetric.link2hosts(entry['name'])
                hostList.add(src_host)
                hostList.add(dst_host)
            hostList = sorted(hostList)
            for src_host in hostList:
                strng = ""
                for dst_host in hostList:
                    if ( dst_host == src_host ):
                        strng += "*"
                    else:
                        link = src_host + "___" + dst_host
                        try:
                            strng += STATUS_CHAR[ lnkDict[link]['status'] ]
                        except KeyError:
                            strng += "-"
                file.write("%-24s: %s\n" % (src_host, strng))
            del lnkDict
            del hostList
            #
            for type in ["link", "source", "destination", "site"]:
                file.write("-----------------------------------------------\n")
                tmpDict = {e['name']:e for e in self.mtrc[metric] \
                                                     if ( e['type'] == type ) }
                #
                for name in sorted( tmpDict.keys() ):
                    if tmpDict[name]['quality'] is not None:
                        quality = "%.3f" % tmpDict[name]['quality']
                    else:
                        quality = "null"
                    if tmpDict[name]['detail'] is not None:
                        detail = tmpDict[name]['detail'].replace('\n','\n           ')
                    else:
                        detail = "null"
                    file.write(("%s: %s\n   status: %s,   quality: %s\n   de" +
                                "tail: %s\n") % (tmpDict[name]['type'],
                                                 tmpDict[name]['name'],
                                                 tmpDict[name]['status'],
                                                 quality, detail))
        file.write("\n")
        file.flush()
        return
# ########################################################################### #



if __name__ == '__main__':
    #
    import argparse
    import getpass
    import shutil
    import http
    import vofeed



    def monit_fts(bins15min):
        """function to fetch FTS transfer documents from MonIT/HDFS"""
        # ################################################################### #
        # fetch FTS completed transfer documents from MonIT/HDFS and return a #
        # tuple (metric-name, time-bin) dictionary of link dictionaries of    #
        # transfer-classification dictionaries with summary information for   #
        # each classification that was present in the link of the time-bin:   #
        # { (metric-name, time-bin): {                                        #
        #                 link: { classification: [#files, #Bytes, log-file], #
        #                         classification: [ ... ] },                  #
        #                 link: { ... } },                                    #
        #   (metric-name, time-bin): { link: { classification: [...] } } }    #
        # ################################################################### #
        FTS_HDFS_PREFIX = "/project/monitoring/archive/fts/raw/complete/"
        FTS_KEYS = ["src_hostname", "dst_hostname", "tr_error_scope",
                    "t_error_code", "t__error_message", "f_size", "log_link",
                    "activity" ]

        # prepare HDFS subdirectory list:
        # ===============================
        logging.info("Retrieving FTS transfer docs from MonIT HDFS")
        logging.debug("   %d time bin(s)" % len(bins15min))
        #
        minTIS = min( bins15min ) * 900
        maxTIS = ( max( bins15min ) * 900 ) + 899
        logging.log(15, "   betwen %s and  %s" %
                        (time.strftime("%Y-%b-%d %H:%M", time.gmtime(minTIS)),
                         time.strftime("%Y-%b-%d %H:%M", time.gmtime(maxTIS))))
        #
        dirList = set()
        for bin15m in bins15min:
            dirList.add( time.strftime("%Y/%m/%d", time.gmtime(bin15m * 900)) )
        #
        now = int( time.time() )
        dayTIS = 24*60*60
        for tis in range(now, now-(7*dayTIS), -dayTIS):
            dirList.add( time.strftime("%Y/%m/%d.tmp", time.localtime( tis )) )
        #
        dirList = sorted( dirList )

        linkInfo = {}
        try:
            with pydoop.hdfs.hdfs() as myHDFS:
                for subDir in dirList:
                    logging.debug("   checking HDFS subdirectory %s" % subDir)
                    if not myHDFS.exists( FTS_HDFS_PREFIX + subDir ):
                        continue
                    # get list of files in directory:
                    myList = myHDFS.list_directory( FTS_HDFS_PREFIX + subDir )
                    fileNames = [ d['name'] for d in myList
                              if (( d['kind'] == "file" ) and
                                  ( d['size'] != 0 )) ]
                    del(myList)
                    for fileName in fileNames:
                        logging.debug("   reading file %s" %
                                      os.path.basename(fileName))
                        fileHndl = None
                        fileObj  = None
                        try:
                            if ( os.path.splitext(fileName)[-1] == ".gz" ):
                                fileHndl = myHDFS.open_file(fileName)
                                fileObj = gzip.GzipFile(fileobj=fileHndl)
                            else:
                                fileObj = myHDFS.open_file(fileName)
                            # read documents and add relevant records to list:
                            for myLine in fileObj:
                                try:
                                    myJson = json.loads(myLine.decode('utf-8'))
                                    #
                                    if (( myJson['metadata']['topic'] !=
                                                        "fts_raw_complete" ) or
                                        (( myJson['data']['vo'] != "cms" ) and
                                         ( myJson['data']['vo'][:4] != "cms/" ))):
                                        continue
                                    #
                                    bin15m = int(myJson['data']\
                                              ['tr_timestamp_complete']/900000)
                                    if bin15m not in bins15min:
                                        continue
                                    #-LML patch for Vanderbilt test endpoint:
                                    if (( myJson['data']['src_url'].find("gridftp-vanderbilt.sites.opensciencegrid.org:2814") >= 0 ) or
                                        ( myJson['data']['dst_url'].find("gridftp-vanderbilt.sites.opensciencegrid.org:2814") >= 0 )):
                                        continue
                                    #-LML patch end
                                    #
                                    # dictionary key is a tuple:
                                    tuple = ("fts15min", bin15m)
                                    #
                                    # link name:
                                    link = FTSmetric.hosts2link(
                                        myJson['data']['src_hostname'],
                                        myJson['data']['dst_hostname'])
                                    if link is None:
                                        continue
                                    #
                                    # concistency check:
                                    if ((( myJson['data']['t_error_code'] ==
                                                                        0 ) and
                                         ( myJson['data']['t_final_transfer_state'] != "Ok" )) or
                                        (( myJson['data']['t_error_code'] !=
                                                                        0 ) and
                                         (( myJson['data']['t_final_transfer_state'] != "Error" ) and
                                          ( myJson['data']['t_final_transfer_state'] != "Abort" )))):
                                        logging.error(("Error code --- Trans" +
                                              "fer state mismatch: %d vs %s") %
                                              ( myJson['data']['t_error_code'],
                                     myJson['data']['t_final_transfer_state']))
                                    #
                                    # fix up log file URL:
                                    logfile = myJson['data']['log_link'].replace("Imperial-FTS-IPv6", "fts00.grid.hep.ph.ic.ac.uk")
                                    logfile = logfile.replace("FTS-MIT", "t3serv019.mit.edu")
                                    if "/#/job/" not in logfile:
                                        logfile = logfile.replace("/#/", "/#/job/")
                                    #
                                    # classify transfer result:
                                    result = FTSmetric.classify(
                                        myJson['data']['tr_error_scope'],
                                        myJson['data']['t_error_code'],
                                        myJson['data']['t__error_message'],
                                        link,
                                        myJson['data']['f_size'],
                                        myJson['data']['activity'])
                                    #
                                    # file size:
                                    nb = max(0, myJson['data']['f_size'])
                                    #
                                    #
                                    # count transfer:
                                    if tuple not in linkInfo:
                                        # first timebin entry:
                                        linkInfo[tuple] = {}
                                    if link not in linkInfo[tuple]:
                                        # first link entry:
                                        linkInfo[tuple][link] = {}
                                    if result not in linkInfo[tuple][link]:
                                        linkInfo[tuple][link][result] = \
                                                               [1, nb, logfile]
                                    else:
                                        linkInfo[tuple][link][result][0] += 1
                                        linkInfo[tuple][link][result][1] += nb
                                except KeyError:
                                    logging.error(("Incomplete FTS record, f" +
                                                   "ile %s: %s") %
                                                       (fileName, str(excptn)))
                                except json.decoder.JSONDecodeError as excptn:
                                    logging.error(("JSON decoding failure, f" +
                                                   "ile %s: %s") %
                                                       (fileName, str(excptn)))
                        except FileNotFoundError as excptn:
                            logging.error("HDFS file not found, %s: %s" %
                                                       (fileName, str(excptn)))
                        except IOError as excptn:
                            logging.error("HDFS access failure, file %s: %s" %
                                                       (fileName, str(excptn)))
                        finally:
                            if fileObj is not None:
                                fileObj.close()
                            if fileHndl is not None:
                                fileHndl.close()
        except IOError:
            logging.error("Failed to fetch FTS records from MonIT HDFS")

        cnt = 0
        for tuple in linkInfo:
            for link in linkInfo[tuple]:
                for classfcn in linkInfo[tuple][link]:
                    cnt += linkInfo[tuple][link][classfcn][0]
        logging.info("   found %d file transfers in %d timebins in MonIT" %
                                                          (cnt, len(linkInfo)))
        return linkInfo
    # ####################################################################### #



    def sumup_timebins(linkDict, bins1hour, bins6hour, bins1day):
        """function to sum up 15 min FTS link information into 1h,6h,1d bins"""
        # ################################################################### #
        # sum up 15 min transfer classifications of the links into 1 hour     #
        # entries based on the provided 1 hour time-bin list.                 #
        # { (metric-name, time-bin): {                                        #
        #                 link: { classification: [#files, #Bytes, log-file], #
        #                         classification: [ ... ] },                  #
        #                 link: { ... } },                                    #
        #   (metric-name, time-bin): { link: { classification: [...] } } }    #
        # ################################################################### #
        tomorrow = int( time.time() ) + 86400
        #
        logging.info("Summing up 15min FTS information for 1h,6h,1d entries")
        logging.debug("   %d/%d/%d 1h/6h/1d time-bin(s)" %
                               (len(bins1hour), len(bins6hour), len(bins1day)))
        #
        minTIS = min( min( bins1hour, default=int(tomorrow/3600) ) * 3600,
                      min( bins6hour, default=int(tomorrow/21600) ) * 21600,
                      min( bins1day,  default=int(tomorrow/86400) ) * 86400 )
        maxTIS = max( ( max( bins1hour, default=0 ) * 3600 ) + 3599,
                      ( max( bins6hour, default=0 ) * 21600 ) + 21599,
                      ( max( bins1day,  default=0 ) * 86400 ) + 86399 )
        logging.log(15, "   betwen %s and  %s" %
                        (time.strftime("%Y-%b-%d %H:%M", time.gmtime(minTIS)),
                         time.strftime("%Y-%b-%d %H:%M", time.gmtime(maxTIS))))

        linkSums = {}
        cnt_file1h = 0
        cnt_file6h = 0
        cnt_file1d = 0
        for key in linkDict:
            mtrc = key[0]
            if ( mtrc != "fts15min" ):
                continue

            tbin = int( key[1] / 4 )
            if tbin in bins1hour:
                mKey = ("fts1hour", tbin )
                #
                if mKey not in linkSums:
                    linkSums[ mKey ] = {}

                for link in linkDict[key]:
                    if link not in linkSums[mKey]:
                        linkSums[mKey][ link ] = {}
                    #
                    for classfcn in linkDict[key][link]:
                        if classfcn in linkSums[mKey][link]:
                            linkSums[mKey][link][classfcn][0] += \
                                               linkDict[key][link][classfcn][0]
                            linkSums[mKey][link][classfcn][1] += \
                                               linkDict[key][link][classfcn][1]
                        else:
                            linkSums[mKey][link][classfcn] = \
                                           linkDict[key][link][classfcn].copy()

                        cnt_file1h += linkDict[key][link][classfcn][0]

            tbin = int( key[1] / 24 )
            if tbin in bins6hour:
                mKey = ("fts6hour", tbin )
                #
                if mKey not in linkSums:
                    linkSums[ mKey ] = {}

                for link in linkDict[key]:
                    if link not in linkSums[mKey]:
                        linkSums[mKey][ link ] = {}
                    #
                    for classfcn in linkDict[key][link]:
                        if classfcn in linkSums[mKey][link]:
                            linkSums[mKey][link][classfcn][0] += \
                                               linkDict[key][link][classfcn][0]
                            linkSums[mKey][link][classfcn][1] += \
                                               linkDict[key][link][classfcn][1]
                        else:
                            linkSums[mKey][link][classfcn] = \
                                           linkDict[key][link][classfcn].copy()

                        cnt_file6h += linkDict[key][link][classfcn][0]

            tbin = int( key[1] / 96 )
            if tbin in bins1day:
                mKey = ("fts1day", tbin )
                #
                if mKey not in linkSums:
                    linkSums[ mKey ] = {}

                for link in linkDict[key]:
                    if link not in linkSums[mKey]:
                        linkSums[mKey][ link ] = {}
                    #
                    for classfcn in linkDict[key][link]:
                        if classfcn in linkSums[mKey][link]:
                            linkSums[mKey][link][classfcn][0] += \
                                               linkDict[key][link][classfcn][0]
                            linkSums[mKey][link][classfcn][1] += \
                                               linkDict[key][link][classfcn][1]
                        else:
                            linkSums[mKey][link][classfcn] = \
                                           linkDict[key][link][classfcn].copy()

                        cnt_file1d += linkDict[key][link][classfcn][0]

        logging.info("   summed up %d/%d/%d file transfers for %d time-bins" %
                           (cnt_file1h, cnt_file6h, cnt_file1d, len(linkSums)))
        return linkSums
    # ####################################################################### #



    def eval_status(mtrcObj, linkDict, vofd):
        """function to evaluate FTS link, endpoint, and site transfer status"""
        # ################################################################### #
        # for each time bin in the linkDict evaluate the quality and status   #
        # of each link and derive a site status considering the storage       #
        # endpoints of the site and filtering out bad foreign sites...        #
        # ################################################################### #
        FTS_METRICS = {'fts15min': 900, 'fts1hour': 3600,
                                        'fts6hour': 21600, 'fts1day': 86400}
        CLASSIFICATION_STRING = { 'trn_ok':   "ok",
                                  'src_perm': "src_permission",
                                  'src_miss': "src_missing_file",
                                  'src_err':  "src_error",
                                  'trn_tout': "trn_timeout",
                                  'trn_usr':  "trn_user",
                                  'trn_err':  "trn_error",
                                  'dst_perm': "dst_permission",
                                  'dst_path': "dst_path",
                                  'dst_spce': "dst_space",
                                  'dst_err':  "dst_error" }

        logging.info("Evaluating link and site status for %d metric/time bins"
                                                               % len(linkDict))

        vofdTimes = sorted( vofd.times(), reverse=True )

        for key in linkDict:
            mtrc = key[0]
            tbin = key[1]
            startTIS = tbin * FTS_METRICS[ mtrc ]
            logging.log(15, "   metric %s for time-bin %d (%s)" %
                            (mtrc, tbin, time.strftime("%Y-%b-%d %H:%M",
                                                       time.gmtime(startTIS))))
            #
            mtrcObj.add1metric(key)
            #
            src_hosts = {}
            dst_hosts = {}
            #
            for link in linkDict[key]:
                src_host, dst_host = FTSmetric.link2hosts(link)
                if (( src_host is None ) or ( dst_host is None )):
                    continue
                if ( src_host == dst_host ):
                    continue
                if src_host not in src_hosts:
                    src_hosts[ src_host ] = {}
                if dst_host not in dst_hosts:
                    dst_hosts[ dst_host ] = {}
                #
                detail = ""
                #
                f_ok = f_trn = f_src = f_dst = 0
                b_ok = b_trn = b_src = b_dst = 0
                for classfcn in linkDict[key][link]:
                    if ( classfcn == "trn_ok" ):
                        f_ok  += linkDict[key][link][classfcn][0]
                        b_ok  += linkDict[key][link][classfcn][1]
                    elif ( classfcn == "trn_usr" ):
                        pass
                    elif ( classfcn[:4] == "trn_" ):
                        f_trn += linkDict[key][link][classfcn][0]
                        b_trn += linkDict[key][link][classfcn][1]
                    elif ( classfcn[:4] == "src_" ):
                        f_src += linkDict[key][link][classfcn][0]
                        b_src += linkDict[key][link][classfcn][1]
                    elif ( classfcn[:4] == "dst_" ):
                        f_dst += linkDict[key][link][classfcn][0]
                        b_dst += linkDict[key][link][classfcn][1]
                    #
                    if ( detail is not "" ):
                        detail += "\n"
                    detail += ("%s: %d files, %.1f GB [%s]" %
                               (CLASSIFICATION_STRING[classfcn],
                                linkDict[key][link][classfcn][0],
                                linkDict[key][link][classfcn][1]/1073741824,
                                linkDict[key][link][classfcn][2]))
                    #
                    if ( classfcn[:4] == "src_" ):
                        if classfcn not in src_hosts[ src_host ]:
                            src_hosts[ src_host ][classfcn] = [0, 0]
                        src_hosts[ src_host ][classfcn][0] += \
                                               linkDict[key][link][classfcn][0]
                        src_hosts[ src_host ][classfcn][1] += \
                                               linkDict[key][link][classfcn][1]
                        #
                        if 'src_err' not in dst_hosts[ dst_host ]:
                            dst_hosts[ dst_host ]['src_err'] = [0, 0]
                        dst_hosts[ dst_host ]['src_err'][0] += \
                                               linkDict[key][link][classfcn][0]
                        dst_hosts[ dst_host ]['src_err'][1] += \
                                               linkDict[key][link][classfcn][1]
                    elif ( classfcn[:4] == "trn_" ):
                        if classfcn not in src_hosts[ src_host ]:
                            src_hosts[ src_host ][classfcn] = [0, 0]
                        src_hosts[ src_host ][classfcn][0] += \
                                               linkDict[key][link][classfcn][0]
                        src_hosts[ src_host ][classfcn][1] += \
                                               linkDict[key][link][classfcn][1]
                        #
                        if classfcn not in dst_hosts[ dst_host ]:
                            dst_hosts[ dst_host ][classfcn] = [0, 0]
                        dst_hosts[ dst_host ][classfcn][0] += \
                                               linkDict[key][link][classfcn][0]
                        dst_hosts[ dst_host ][classfcn][1] += \
                                               linkDict[key][link][classfcn][1]
                    elif ( classfcn[:4] == "dst_" ):
                        if 'dst_err' not in src_hosts[ src_host ]:
                            src_hosts[ src_host ]['dst_err'] = [0, 0]
                        src_hosts[ src_host ]['dst_err'][0] += \
                                               linkDict[key][link][classfcn][0]
                        src_hosts[ src_host ]['dst_err'][1] += \
                                               linkDict[key][link][classfcn][1]
                        #
                        if classfcn not in dst_hosts[ dst_host ]:
                            dst_hosts[ dst_host ][classfcn] = [0, 0]
                        dst_hosts[ dst_host ][classfcn][0] += \
                                               linkDict[key][link][classfcn][0]
                        dst_hosts[ dst_host ][classfcn][1] += \
                                               linkDict[key][link][classfcn][1]
                #
                # calculate link quality and derive status:
                f_total = f_ok + f_trn + f_src + f_dst
                try:
                    quality = round( max(f_ok / f_total,
                                         b_ok / (b_ok + b_trn + b_src + b_dst))
                                                                           , 3)
                    if (( f_ok == f_total ) or
                        ( ((f_ok - 1) / f_total) > 0.500 )):
                        status = "ok"
                    elif ( ((f_ok + 1) / f_total) < 0.500 ):
                        status = "error"
                    else:
                        status = "warning"
                except ZeroDivisionError:
                    quality = 0.000
                    status = "unknown"
                mtrcObj.add1entry(key, { 'name': link, 'type': "link",
                                         'status': status, 'quality': quality,
                                         'detail': detail } )
                #
                # calculate quality and derive status for source endpoint:
                f_total = f_ok + f_trn + f_src
                try:
                    quality = round( max( f_ok / f_total,
                                          b_ok / (b_ok + b_trn + b_src)), 3)
                    if (( f_ok == f_total ) or
                        ( ((f_ok - 1) / f_total) > 0.500 )):
                        status = "ok"
                    elif ( ((f_ok + 1) / f_total) < 0.500 ):
                        status = "error"
                    else:
                        status = "warning"
                except ZeroDivisionError:
                    quality = 0.000
                    status = "unknown"
                src_hosts[src_host][dst_host] = {
                    'quality': quality, 'status': status,
                    'f_ok': f_ok, 'f_total': f_total,
                    'b_ok': b_ok, 'b_total': b_ok + b_trn + b_src }
                #
                # calculate quality and derive status for destination endpoint:
                f_total = f_ok + f_trn + f_dst
                try:
                    quality = round( max( f_ok / f_total,
                                          b_ok / (b_ok + b_trn + b_dst)), 3)
                    if (( f_ok == f_total ) or
                        ( ((f_ok - 1) / f_total) > 0.500 )):
                        status = "ok"
                    elif ( ((f_ok + 1) / f_total) < 0.500 ):
                        status = "error"
                    else:
                        status = "warning"
                except ZeroDivisionError:
                    quality = 0.000
                    status = "unknown"
                dst_hosts[dst_host][src_host] = {
                    'quality': quality, 'status': status,
                    'f_ok': f_ok, 'f_total': f_total,
                    'b_ok': b_ok, 'b_total': b_ok + b_trn + b_dst }
            #
            #
            # identify bad source endpoints:
            bad_src = []
            for src_host in src_hosts:
                warn_f_ok = warn_f_total = warn_b_ok = warn_b_total = 0
                cnt_bad = cnt_links = 0
                for dst_host in src_hosts[src_host]:
                    if ( dst_host.count(".") < 2 ):
                        continue
                    if ( src_hosts[src_host][dst_host]['status'] == "warning" ):
                        warn_f_ok    += src_hosts[src_host][dst_host]['f_ok']
                        warn_f_total += src_hosts[src_host][dst_host]['f_total']
                        warn_b_ok    += src_hosts[src_host][dst_host]['b_ok']
                        warn_b_total += src_hosts[src_host][dst_host]['b_total']
                    elif ( src_hosts[src_host][dst_host]['status'] !=
                                                                   "unknown" ):
                        if ( src_hosts[src_host][dst_host]['quality'] < 0.250 ):
                            cnt_bad += 1
                        cnt_links += 1
                # handle sum of unknown entries like a site:
                try:
                    warn_quality = round( max( warn_f_ok / warn_f_total ,
                                               warn_b_ok / warn_b_total ), 3)
                    if ( warn_quality < 0.250 ):
                       cnt_bad += 1
                    cnt_links += 1
                except ZeroDivisionError:
                    pass
                try:
                    if ( (cnt_bad - 1) / cnt_links > 0.750 ):
                        # bad source endpoint
                        bad_src.append(src_host)
                        logging.log(15, "      bad source endpoint %s: %d / %d"
                                              % (src_host, cnt_bad, cnt_links))
                        for dst_host in src_hosts[src_host]:
                            if ( dst_host.count(".") < 2 ):
                                continue
                            logging.debug(("      dst: %s: %.3f %s %d/%d fil" +
                                           "es %.1f/%.1f GB") % (dst_host,
                          src_hosts[src_host][dst_host]['quality'],
                          src_hosts[src_host][dst_host]['status'],
                          src_hosts[src_host][dst_host]['f_ok'],
                          src_hosts[src_host][dst_host]['f_total'],
                          src_hosts[src_host][dst_host]['b_ok']/1073741824,
                          src_hosts[src_host][dst_host]['b_total']/1073741824))
                except ZeroDivisionError:
                    pass
            #
            # identify bad destination endpoints:
            bad_dst = []
            for dst_host in dst_hosts:
                warn_f_ok = warn_f_total = warn_b_ok = warn_b_total = 0
                cnt_bad = cnt_links = 0
                for src_host in dst_hosts[dst_host]:
                    if ( src_host.count(".") < 2 ):
                        continue
                    if ( dst_hosts[dst_host][src_host]['status'] == "warning" ):
                        warn_f_ok    += dst_hosts[dst_host][src_host]['f_ok']
                        warn_f_total += dst_hosts[dst_host][src_host]['f_total']
                        warn_b_ok    += dst_hosts[dst_host][src_host]['b_ok']
                        warn_b_total += dst_hosts[dst_host][src_host]['b_total']
                    elif ( dst_hosts[dst_host][src_host]['status'] !=
                                                                   "unknown" ):
                        if ( dst_hosts[dst_host][src_host]['quality'] < 0.250 ):
                            cnt_bad += 1
                        cnt_links += 1
                # handle sum of unknown entries like a site:
                try:
                    warn_quality = round( max( warn_f_ok / warn_f_total ,
                                               warn_b_ok / warn_b_total ), 3)
                    if ( warn_quality < 0.250 ):
                       cnt_bad += 1
                    cnt_links += 1
                except ZeroDivisionError:
                    pass
                try:
                    if ( (cnt_bad - 1) / cnt_links > 0.750 ):
                        # bad destination endpoint
                        bad_dst.append(dst_host)
                        logging.log(15, ("      bad destination endpoint %s:" +
                                  " %d / %d") % (dst_host, cnt_bad, cnt_links))
                        for src_host in dst_hosts[dst_host]:
                            if ( src_host.count(".") < 2 ):
                                continue
                            logging.debug(("      src: %s: %.3f %s %d/%d fil" +
                                           "es %.1f/%.1f GB") % (src_host,
                          dst_hosts[dst_host][src_host]['quality'],
                          dst_hosts[dst_host][src_host]['status'],
                          dst_hosts[dst_host][src_host]['f_ok'],
                          dst_hosts[dst_host][src_host]['f_total'],
                          dst_hosts[dst_host][src_host]['b_ok']/1073741824,
                          dst_hosts[dst_host][src_host]['b_total']/1073741824))
                except ZeroDivisionError:
                    pass
            #
            #
            # evaluate source endpoints (excluding bad destination endpoints):
            # ================================================================
            for src_host in src_hosts:
                sum_quality = 0
                f_total = 0
                warn_f_ok = warn_f_total = warn_b_ok = warn_b_total = 0
                cnt_links = 0
                cnt_unknown = cnt_ok = cnt_warning = cnt_error = cnt_bad = 0
                err_strng = ""
                for hst in src_hosts[src_host]:
                    if ( hst.count(".") >= 2 ):
                        if hst in bad_dst:
                            cnt_bad += 1
                            continue
                        if ( src_hosts[src_host][hst]['status'] == "unknown" ):
                            cnt_unknown += 1
                        elif ( src_hosts[src_host][hst]['status'] ==
                                                                   "warning" ):
                            # prefer host summary over link level evaluation
                            warn_f_ok    += src_hosts[src_host][hst]['f_ok']
                            warn_f_total += src_hosts[src_host][hst]['f_total']
                            warn_b_ok    += src_hosts[src_host][hst]['b_ok']
                            warn_b_total += src_hosts[src_host][hst]['b_total']
                            cnt_warning += 1
                        else:
                            sum_quality += src_hosts[src_host][hst]['quality']
                            if ( src_hosts[src_host][hst]['status'] == "ok" ):
                                cnt_ok += 1
                            elif ( src_hosts[src_host][hst]['status'] ==
                                                                     "error" ):
                                cnt_error += 1
                            cnt_links += 1
                        f_total += src_hosts[src_host][hst]['f_total']
                    elif (( hst in CLASSIFICATION_STRING ) and
                          ( hst != "trn_ok" )):
                        if ( err_strng != "" ):
                            err_strng += ","
                        err_strng += " %s: %d" % (CLASSIFICATION_STRING[hst],
                                                  src_hosts[src_host][hst][0])
                # handle sum of warning entries like a site:
                try:
                    warn_quality = round( max( warn_f_ok / warn_f_total ,
                                               warn_b_ok / warn_b_total ), 3)
                    sum_quality += warn_quality
                    if ( ((warn_f_ok - 1) / warn_f_total) > 0.500 ):
                        cnt_ok += 1
                    elif ( ((warn_f_ok + 1) / warn_f_total) < 0.500 ):
                        cnt_error += 1
                    cnt_links += 1
                except ZeroDivisionError:
                    pass
                try:
                    quality = round( max( cnt_ok/cnt_links,
                                          sum_quality/cnt_links), 3)
                    if ( ((cnt_ok - 1) / cnt_links) > 0.500 ):
                        status = "ok"
                    elif ( ((cnt_ok + 1) / cnt_links) < 0.500 ):
                        status = "error"
                    else:
                        status = "warning"
                except ZeroDivisionError:
                    quality = 0.000
                    status = "unknown"
                src_hosts[src_host]['links'] = (cnt_ok, cnt_warning, cnt_error,
                                                          cnt_unknown, cnt_bad)
                src_hosts[src_host]['quality'] = quality
                src_hosts[src_host]['status'] = status
                #
                if src_host in bad_src:
                    detail = "excluded from destination endpoint evaluation\n"
                else:
                    detail = ""
                if 'trn_ok' in src_hosts[src_host]:
                    detail += ("Transfer: %d files, %.3f TB ok" %
                               (src_hosts[src_host]['trn_ok'][0],
                                src_hosts[src_host]['trn_ok'][1]/1099511627776))
                else:
                    detail += "Transfer: 0 files, 0.000 TB ok"
                if ( err_strng == "" ):
                    err_strng = "none"
                detail += "\nErrors: %s" % err_strng
                detail += (("\nLinks: %d ok, %d warning, %d error, %d unknow" +
                            "n, %d bad-destination") % (cnt_ok, cnt_warning,
                                              cnt_error, cnt_unknown, cnt_bad))
                mtrcObj.add1entry(key, { 'name': src_host, 'type': "source",
                                         'status': status, 'quality': quality,
                                         'detail': detail } )
            #
            #
            # evaluate destination endpoints (excluding bad source endpoints):
            # ================================================================
            for dst_host in dst_hosts:
                sum_quality = 0
                f_total = 0
                warn_f_ok = warn_f_total = warn_b_ok = warn_b_total = 0
                cnt_links = 0
                cnt_unknown = cnt_ok = cnt_warning = cnt_error = cnt_bad = 0
                err_strng = ""
                for hst in dst_hosts[dst_host]:
                    if ( hst.count(".") >= 2 ):
                        if hst in bad_src:
                            cnt_bad += 1
                            continue
                        if ( dst_hosts[dst_host][hst]['status'] == "unknown" ):
                            cnt_unknown += 1
                        elif ( dst_hosts[dst_host][hst]['status'] ==
                                                                   "warning" ):
                            # prefer host summary over link level evaluation
                            warn_f_ok    += dst_hosts[dst_host][hst]['f_ok']
                            warn_f_total += dst_hosts[dst_host][hst]['f_total']
                            warn_b_ok    += dst_hosts[dst_host][hst]['b_ok']
                            warn_b_total += dst_hosts[dst_host][hst]['b_total']
                            cnt_warning += 1
                        else:
                            sum_quality += dst_hosts[dst_host][hst]['quality']
                            if ( dst_hosts[dst_host][hst]['status'] == "ok" ):
                                cnt_ok += 1
                            elif ( dst_hosts[dst_host][hst]['status'] ==
                                                                     "error" ):
                                cnt_error += 1
                            cnt_links += 1
                        f_total += dst_hosts[dst_host][hst]['f_total']
                    elif (( hst in CLASSIFICATION_STRING ) and
                          ( hst != "trn_ok" )):
                        if ( err_strng != "" ):
                            err_strng += ","
                        err_strng += (" %s: %d" % (CLASSIFICATION_STRING[hst],
                                                  dst_hosts[dst_host][hst][0]))
                # handle sum of warning entries like a site:
                try:
                    warn_quality = round( max( warn_f_ok / warn_f_total ,
                                               warn_b_ok / warn_b_total ), 3)
                    sum_quality += warn_quality
                    if ( ((warn_f_ok - 1) / warn_f_total) > 0.500 ):
                        cnt_ok += 1
                    elif ( ((warn_f_ok + 1) / warn_f_total) < 0.500 ):
                        cnt_error += 1
                    cnt_links += 1
                except ZeroDivisionError:
                    pass
                try:
                    quality = round( max( cnt_ok/cnt_links,
                                          sum_quality/cnt_links), 3)
                    if ( ((cnt_ok - 1) / cnt_links) > 0.500 ):
                        status = "ok"
                    elif ( ((cnt_ok + 1) / cnt_links) < 0.500 ):
                        status = "error"
                    else:
                        status = "warning"
                except ZeroDivisionError:
                    quality = 0.000
                    status = "unknown"
                dst_hosts[dst_host]['links'] = (cnt_ok, cnt_warning, cnt_error,
                                                          cnt_unknown, cnt_bad)
                dst_hosts[dst_host]['quality'] = quality
                dst_hosts[dst_host]['status'] = status
                #
                if dst_host in bad_dst:
                    detail = "excluded from source endpoint evaluation\n"
                else:
                    detail = ""
                if 'trn_ok' in dst_hosts[dst_host]:
                    detail += ("Transfer: %d files, %.3f TB ok" %
                               (dst_hosts[dst_host]['trn_ok'][0],
                                dst_hosts[dst_host]['trn_ok'][1]/1099511627776))
                else:
                    detail += "Transfer: 0 files, 0.000 TB ok"
                if ( err_strng == "" ):
                    err_strng = "none"
                detail += "\nErrors: %s" % err_strng
                detail += (("\nLinks: %d ok, %d warning, %d error, %d unknow" +
                           "n, %d bad-source") % (cnt_ok, cnt_warning,
                                              cnt_error, cnt_unknown, cnt_bad))
                mtrcObj.add1entry(key, { 'name': dst_host,
                                         'type': "destination",
                                         'status': status, 'quality': quality,
                                         'detail': detail } )
            #
            #
            # evaluate site status:
            # =====================
            for vofdtime in vofdTimes:
                if ( vofdtime <= startTIS ):
                    break
            #
            # loop over CMS sites:
            for cms_site in sorted( vofd.sites(vofdtime) ):
                quality = 1.000
                status = None
                src_ok = src_warning = src_error = src_unknown = src_bad = 0
                dst_ok = dst_warning = dst_error = dst_unknown = dst_bad = 0
                src_classfcn = { 'trn_ok': [0,0], 'foreign': 0 }
                dst_classfcn = { 'trn_ok': [0,0], 'foreign': 0 }
                hst_strng = ""
                for srvc in vofd.services(vofdtime, cms_site, "SE"):
                    host = srvc['hostname']
                    #
                    # transfers from the host, i.e. host as source:
                    src_status = None
                    if host in src_hosts:
                        try:
                            if status is None:
                                status = src_hosts[host]['status']
                            elif ( src_hosts[host]['status'] == "error" ):
                                status = "error"
                            elif (( src_hosts[host]['status'] == "unknown" ) and
                                  ( status != "error" )):
                                status = "unknown"
                            elif (( src_hosts[host]['status'] == "warning" ) and
                                  ( status == "ok" )):
                                status = "warning"
                            src_status = src_hosts[host]['status']
                            quality = min(quality, src_hosts[host]['quality'])
                            src_ok      += src_hosts[host]['links'][0]
                            src_warning += src_hosts[host]['links'][1]
                            src_error   += src_hosts[host]['links'][2]
                            src_unknown += src_hosts[host]['links'][3]
                            src_bad     += src_hosts[host]['links'][4]
                        except KeyError:
                            if ( status != "error" ):
                                status = "unknown"
                            src_status = "unknown"
                            quality = 0.000
                        for cls in src_hosts[host]:
                            if ( cls == 'trn_ok' ):
                                src_classfcn[cls][0] += src_hosts[host][cls][0]
                                src_classfcn[cls][1] += src_hosts[host][cls][1]
                            elif ( cls == 'dst_err' ):
                                src_classfcn['foreign'] += \
                                                        src_hosts[host][cls][0]
                            elif cls in CLASSIFICATION_STRING:
                                if cls in src_classfcn:
                                    src_classfcn[cls] += src_hosts[host][cls][0]
                                else:
                                    src_classfcn[cls] = src_hosts[host][cls][0]
                    #
                    # transfers to the host, i.e. host as destination:
                    dst_status = None
                    if host in dst_hosts:
                        try:
                            if status is None:
                                status = dst_hosts[host]['status']
                            elif ( dst_hosts[host]['status'] == "error" ):
                                status = "error"
                            elif (( dst_hosts[host]['status'] == "unknown" ) and
                                  ( status != "error" )):
                                status = "unknown"
                            elif (( dst_hosts[host]['status'] == "warning" ) and
                                  ( status == "ok" )):
                                status = "warning"
                            dst_status = dst_hosts[host]['status']
                            quality = min(quality, dst_hosts[host]['quality'])
                            dst_ok      += dst_hosts[host]['links'][0]
                            dst_warning += dst_hosts[host]['links'][1]
                            dst_error   += dst_hosts[host]['links'][2]
                            dst_unknown += dst_hosts[host]['links'][3]
                            dst_bad     += dst_hosts[host]['links'][4]
                        except KeyError:
                            if ( status != "error" ):
                                status = "unknown"
                            dst_status = "unknown"
                            quality = 0.000
                        for cls in dst_hosts[host]:
                            if ( cls == 'trn_ok' ):
                                dst_classfcn[cls][0] += dst_hosts[host][cls][0]
                                dst_classfcn[cls][1] += dst_hosts[host][cls][1]
                            elif ( cls == 'src_err' ):
                                dst_classfcn['foreign'] += \
                                                        dst_hosts[host][cls][0]
                            elif cls in CLASSIFICATION_STRING:
                                if cls in dst_classfcn:
                                    dst_classfcn[cls] += dst_hosts[host][cls][0]
                                else:
                                    dst_classfcn[cls] = dst_hosts[host][cls][0]
                    if (( src_status is None ) and ( dst_status is None )):
                        continue
                    if src_status is None:
                        src_status = "unknown"
                        if ( status != "error" ):
                            status = "unknown"
                        quality = 0.000
                    if dst_status is None:
                        dst_status = "unknown"
                        if ( status != "error" ):
                            status = "unknown"
                        quality = 0.000
                    hst_strng += "%s: %s/%s\n" % (host, src_status, dst_status)
                if status is None:
                    continue
                detail = (("Transfer (from/to): %d/%d files, %.3f/%.3f TB ok" +
                           "\n") % (src_classfcn['trn_ok'][0],
                                    dst_classfcn['trn_ok'][0],
                                    src_classfcn['trn_ok'][1]/1099511627776,
                                    dst_classfcn['trn_ok'][1]/1099511627776))
                err_strng = ""
                for cls in CLASSIFICATION_STRING:
                    if (( cls == 'trn_ok' ) or
                        (( cls not in src_classfcn ) and
                         ( cls not in dst_classfcn ))):
                        continue
                    try:
                        src_files = src_classfcn[cls]
                    except KeyError:
                        src_files = 0
                    try: 
                        dst_files = dst_classfcn[cls]
                    except KeyError:
                        dst_files = 0
                    if ( err_strng != "" ):
                            err_strng += ","
                    err_strng += (" %s: %d/%d" % (CLASSIFICATION_STRING[cls],
                                                         src_files, dst_files))
                if (( src_classfcn['foreign'] > 0 ) or
                    ( dst_classfcn['foreign'] > 0 )):
                    err_strng += " foreign: %d/%d" % (src_classfcn['foreign'],
                                                      dst_classfcn['foreign'])
                if ( err_strng == "" ):
                    err_strng = "none"
                detail += "Errors: %s\n" % err_strng
                detail += ("Links: %d/%d ok, %d/%d warning, %d/%d error, %d/" +
                           "%d unknown, %d/%d bad-endpoint\n") % (src_ok,
                           dst_ok, src_warning, dst_warning, src_error,
                           dst_error, src_unknown, dst_unknown, src_bad,
                           dst_bad)
                detail += hst_strng[:-1]
                mtrcObj.add1entry(key, { 'name': cms_site, 'type': "site",
                                         'status': status, 'quality': quality,
                                         'detail': detail } )

        return
    # ####################################################################### #



    def monit_upload(mtrcObj):
        """function to upload CMS FTS link/.../site evaluations to MonIT"""
        # ############################################################# #
        # upload FTS evaluations as JSON metric documents to MonIT/HDFS #
        # ############################################################# #
        #MONIT_URL = "http://monit-metrics.cern.ch:10012/"
        MONIT_URL = "http://fail.cern.ch:10012/"
        MONIT_HDR = {'Content-Type': "application/json; charset=UTF-8"}
        #
        logging.info("Composing JSON array and uploading to MonIT")


        # compose JSON array string:
        # ==========================
        jsonString = mtrcObj.compose_json()
        if ( jsonString == "[\n]\n" ):
            logging.warning("skipping upload of document-devoid JSON string")
            return False
        cnt_15min = jsonString.count("\"path\": \"fts15min\"")
        cnt_1hour = jsonString.count("\"path\": \"fts1hour\"")
        cnt_6hour = jsonString.count("\"path\": \"fts6hour\"")
        cnt_1day  = jsonString.count("\"path\": \"fts1day\"")
        #
        jsonString = jsonString.replace("ssbmetric", "metrictest")


        # upload string with JSON document array to MonIT/HDFS:
        # =====================================================
        docs = json.loads(jsonString)
        ndocs = len(docs)
        successFlag = True
        for myOffset in range(0, ndocs, 2048):
            if ( myOffset > 0 ):
                # give importer time to process documents
                time.sleep(1.500)
            # MonIT upload channel can handle at most 10,000 docs at once
            dataString = json.dumps( docs[myOffset:min(ndocs,myOffset+2048)] )
            #
            try:
                # MonIT needs a document array and without newline characters:
                requestObj = urllib.request.Request(MONIT_URL,
                             data=dataString.encode("utf-8"),
                             headers=MONIT_HDR, method="POST")
                responseObj = urllib.request.urlopen( requestObj, timeout=90 )
                if ( responseObj.status != http.HTTPStatus.OK ):
                    logging.error(("Failed to upload JSON [%d:%d] string to " +
                                   "MonIT, %d \"%s\"") %
                                  (myOffset, min(ndocs,myOffset+2048),
                                   responseObj.status, responseObj.reason))
                    successFlag = False
                responseObj.close()
            except urllib.error.URLError as excptn:
                logging.error("Failed to upload JSON [%d:%d], %s" %
                             (myOffset, min(ndocs,myOffset+2048), str(excptn)))
                successFlag = False
        del docs

        if ( successFlag ):
            logging.log(25, ("JSON string with %d(15m)/%d(1h)/%d(6h)/%d(1d) " +
                             "docs uploaded to MonIT") %
                            (cnt_15min, cnt_1hour, cnt_6hour, cnt_1day))
        return successFlag
    # ####################################################################### #



    def write_evals(mtrcObj, filename=None):
        """function to write CMS FTS link/.../site evaluation JSON to a file"""
        # ######################################################## #
        # write FTS evaluations as JSON metric documents to a file #
        # ######################################################## #

        if filename is None:
            filename = "%s/eval_fts_%s.json" % (EVFTS_BACKUP_DIR,
                                    time.strftime("%Y%m%d%H%M", time.gmtime()))
        logging.info("Writing JSON array to file %s" % filename)

        # compose JSON array string:
        # ==========================
        jsonString = mtrcObj.compose_json()
        
        if ( jsonString == "[\n]\n" ):
            logging.warning("skipping writing of document-devoid JSON string")
            return False
        cnt_docs = jsonString.count("\"producer\": \"cmssst\"")


        # write string to file:
        # =====================
        try:
            with open(filename, 'w') as myFile:
                myFile.write( jsonString )
            logging.log(25, "JSON array with %d docs written to file" %
                                                                      cnt_docs)
        except OSError as excptn:
            logging.error("Failed to write JSON array, %s" % str(excptn))

        return
    # ####################################################################### #



    parserObj = argparse.ArgumentParser(description="Script to evaluate FTS " +
        "link and site status for the 15 minute (1 hour, 6 hours, and 1 day)" +
        " bin that started 30 minutes ago. FTS status for a specific time bi" +
        "n or time interval are evaluated in case of of one or two arguments.")
    parserObj.add_argument("-q", dest="qhour", action="store_true",
                                 help="restrict evaluation to 15 min results")
    parserObj.add_argument("-1", dest="hour", action="store_true",
                                 help="restrict evaluation to 1 hour results")
    parserObj.add_argument("-6", dest="qday", action="store_true",
                                 help="restrict evaluation to 6 hours results")
    parserObj.add_argument("-d", dest="day", action="store_true",
                                 help="restrict evaluation to 1 day results")
    parserObj.add_argument("-U", dest="upload", default=True,
                                 action="store_false",
                                 help="do not upload to MonIT but print FTS " +
                                 "evaluations")
    parserObj.add_argument("-v", action="count", default=0,
                                 help="increase verbosity")
    parserObj.add_argument("timeSpec", nargs="?",
                                 metavar="time-specification",
                                 help=("time specification in UTC, either an" +
                                       " integer with the time in seconds si" +
                                       "nce the epoch or time in the format " +
                                       "\"YYYY-Mmm-dd HH:MM\""))
    parserObj.add_argument("lastSpec", nargs="?",
                                 metavar="end-time",
                                 help=("end time specification in UTC, eithe" +
                                       "r an integer with the time in second" +
                                       "s since the epoch or time in the for" +
                                       "mat \"YYYY-Mmm-dd HH:MM\""))
    argStruct = parserObj.parse_args()
    #
    if not ( argStruct.qhour or argStruct.hour or argStruct.qday or
             argStruct.day ):
        argStruct.qhour = True
        argStruct.hour = True
        argStruct.qday = True
        argStruct.day = True


    # configure the message logger:
    # =============================
    logging.addLevelName(25, "NOTICE")
    logging.addLevelName(15, "debug")
    logging.addLevelName(9, "XDEBUG")
    if ( argStruct.v >= 5 ):
        logging.basicConfig(datefmt="%Y-%b-%d %H:%M:%S",
                            format="%(asctime)s [%(levelname).1s] %(message)s",
                            level=9)
    elif ( argStruct.v == 4 ):
        logging.basicConfig(datefmt="%Y-%b-%d %H:%M:%S",
                            format="%(asctime)s [%(levelname).1s] %(message)s",
                            level=logging.DEBUG)
    elif ( argStruct.v == 3 ):
        logging.basicConfig(datefmt="%Y-%b-%d %H:%M:%S",
                            format="%(asctime)s [%(levelname).1s] %(message)s",
                            level=15)
    elif ( argStruct.v == 2 ):
        logging.basicConfig(datefmt="%Y-%b-%d %H:%M:%S",
                            format="%(asctime)s [%(levelname).1s] %(message)s",
                            level=logging.INFO)
    elif ( argStruct.v == 1 ):
        logging.basicConfig(datefmt="%Y-%b-%d %H:%M:%S",
                            format="%(asctime)s [%(levelname).1s] %(message)s",
                            level=25)
    else:
        logging.basicConfig(datefmt="%Y-%b-%d %H:%M:%S",
                            format="%(asctime)s [%(levelname).1s] %(message)s",
                            level=logging.WARNING)


    # find what we need to do:
    # ========================
    eval15min = set()
    eval1hour = set()
    eval6hour = set()
    eval1day  = set()

    now15m = int( time.time() / 900 )
    if argStruct.timeSpec is None:
        # no time specified, evaluate time bin that started 30 min ago:
        eval15min.add( now15m - 2 )
        #
        # verify time bins that ended 15 min, 1h, 2h, and 3 hour ago:
        eval15min.add( now15m - 5 )
        eval15min.add( now15m - 9 )
        eval15min.add( now15m - 13 )
        #
        # evaluate the time bin as requested/needed:
        if (( argStruct.hour ) and ( now15m % 4 == 0 )):
            bin15m = now15m - 16
            eval1hour.add( int(bin15m / 4) )
        if (( argStruct.qday ) and ( now15m % 24 == 12 )):
            bin15m = now15m - 36
            eval6hour.add( int(bin15m / 24) )
        if (( argStruct.day ) and ( now15m % 96 == 12 )):
            bin15m = now15m - 108
            eval1day.add( int(bin15m / 96) )
        #
        logging.log(15, "No time specified: 15 min bin starting %s" %
                    time.strftime("%Y-%b-%d %H:%M", time.gmtime(now15m * 900)))
    elif argStruct.lastSpec is None:
        # single time specification:
        if ( argStruct.timeSpec.isdigit() ):
            # argument should be time in seconds of 15 min time bin
            bin15m = int( argStruct.timeSpec / 900 )
        else:
            # argument should be the time in "YYYY-Mmm-dd HH:MM" format
            bin15m = int( calendar.timegm( time.strptime("%s UTC" %
                             argStruct.timeSpec, "%Y-%b-%d %H:%M %Z") ) / 900 )
        #
        # evaluate the time bins as requested:
        if ( argStruct.qhour ):
            eval15min.add( bin15m )
        if ( argStruct.hour ):
            eval1hour.add( int(bin15m / 4) )
        if ( argStruct.qday ):
            eval6hour.add( int(bin15m / 24) )
        if ( argStruct.day ):
            eval1day.add( int(bin15m / 96) )
        #
        logging.log(15, "Time specified: 15 min bin starting %s" %
                    time.strftime("%Y-%b-%d %H:%M", time.gmtime(bin15m * 900)))
    else:
        # start and end time specification:
        if ( argStruct.timeSpec.isdigit() ):
            # argument should be time in seconds of 15 min time bin
            frst15m = int( argStruct.timeSpec / 900 )
        else:
            # argument should be the time in "YYYY-Mmm-dd HH:MM" format
            frst15m = int( calendar.timegm( time.strptime("%s UTC" %
                             argStruct.timeSpec, "%Y-%b-%d %H:%M %Z") ) / 900 )
        #
        if ( argStruct.lastSpec.isdigit() ):
            # argument should be time in seconds of 15 min time bin
            last15m = int( argStruct.lastSpec / 900 )
        else:
            # argument should be the time in "YYYY-Mmm-dd HH:MM" format
            last15m = int( calendar.timegm( time.strptime("%s UTC" %
                             argStruct.lastSpec, "%Y-%b-%d %H:%M %Z") ) / 900 )
        #
        # evaluate time bins as requested:
        if ( argStruct.qhour ):
            for tbin in range(frst15m, last15m + 1):
                eval15min.add( tbin )
        if ( argStruct.hour ):
            for tbin in range( int(frst15m / 4), int(last15m / 4) + 1):
                eval1hour.add( tbin )
        if ( argStruct.qday ):
            for tbin in range( int(frst15m / 24), int(last15m / 24) + 1):
                eval6hour.add( tbin )
        if ( argStruct.day ):
            for tbin in range( int(frst15m / 96), int(last15m / 96) + 1):
                eval1day.add( tbin )
        #
        logging.log(15, "Time range specified: %s to %s" %
                  (time.strftime("%Y-%b-%d %H:%M", time.gmtime(frst15m * 900)),
            time.strftime("%Y-%b-%d %H:%M", time.gmtime((last15m * 900)+899))))
    logging.debug("   15 min  evaluations for %s" % str( sorted(eval15min) ))
    logging.debug("   1 hour  evaluations for %s" % str( sorted(eval1hour) ))
    logging.debug("   6 hours evaluations for %s" % str( sorted(eval6hour) ))
    logging.debug("   1 day   evaluations for %s" % str( sorted(eval1day) ))


    # fetch storage endpoint information of sites:
    # ============================================
    vofd = vofeed.vofeed()
    if argStruct.timeSpec is None:
        # load latest/fetch previous VO-feed information:
        vofd.load()
    elif argStruct.lastSpec is None:
        # fetch VO-feed information for time bin:
        vofd.fetch( bin15m * 900 )
    else:
        # fetch VO-feed information for time range:
        vofd.fetch( (frst15m * 900, last15m * 900) )


    # fetch FTS transfer results:
    # ===========================
    fts15min = set()
    for tbin in eval15min:
        fts15min.add( tbin )
    for tbin in eval1hour:
        t15m = tbin * 4
        fts15min.update( [ t15m, t15m + 1, t15m + 2, t15m + 3 ] )
    for tbin in eval6hour:
        t15m = tbin * 24
        fts15min.update( list( range(t15m, t15m+24) ) )
    for tbin in eval1day:
        t15m = tbin * 96
        fts15min.update( list( range(t15m, t15m+96) ) )
    #
    ftsDict = monit_fts( fts15min )


    # sum up FTS 15 min transfer results into 1 hour bins as needed:
    # ==============================================================
    sumDict = sumup_timebins( ftsDict, eval1hour, eval6hour, eval1day )
    #
    #
    # delete fts15min entries we summed up/don't need to evaluate:
    # ------------------------------------------------------------
    for mtrc in list(ftsDict):
        if (( mtrc[0] == "fts15min" ) and ( mtrc[1] not in eval15min )):
            del ftsDict[ mtrc ]
    #
    #
    # add summed up transfer results to fetched 15 min transfer results:
    # ------------------------------------------------------------------
    ftsDict.update( sumDict )


    # evaluate link and site status:
    # ==============================
    evalDocs = FTSmetric()
    eval_status( evalDocs, ftsDict, vofd )


    # fetch existing FTS metric documents from MonIT:
    # ===============================================
    monitDocs = FTSmetric()
    #
    monitList = evalDocs.metrics()
    #
    monitDocs.fetch( monitList )


    # filter out metric/time bin entries with identical docs in MonIT:
    # ================================================================
    cnt_docs = 0
    for mtrcTpl in sorted( evalDocs.metrics() ):
        if mtrcTpl in monitDocs.metrics():
            monitEvals = monitDocs.evaluations(mtrcTpl)
            for eval in evalDocs.evaluations(mtrcTpl):
                if eval in monitEvals:
                    logging.debug(("filtering out %s (%d) %s / %s as identic" +
                                   "al entry exists in MonIT") % (mtrcTpl[0],
                                   mtrcTpl[1], eval['name'], eval['type']))
                    evalDocs.del1entry( mtrcTpl, eval )
                else:
                    cnt_docs += 1
            if ( len( evalDocs.evaluations(mtrcTpl) ) == 0 ):
                # no result left in metric/time-bin:
                evalDocs.del1metric( mtrcTpl )
        else:
            cnt_docs += len( evalDocs.evaluations(mtrcTpl) )


    # upload FTS metric docs to MonIT:
    # ================================
    if ( cnt_docs > 0 ):
        if ( argStruct.upload ):
            successFlag = monit_upload( evalDocs )
        else:
            successFlag = False
        #
        if ( not successFlag ):
            write_evals( evalDocs )

    #import pdb; pdb.set_trace()
