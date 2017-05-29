import os
import sys

try:
    import xml.etree.ElementTree
except Exception, e:
    print "Unable to import ElementTree for parsing XML."
    print "Exception message: %s" % str(e)
    sys.exit(0)


def get_siteconf_path():
    if 'VO_CMS_SW_DIR' in os.environ:
        siteconf_path = os.path.join(os.environ['VO_CMS_SW_DIR'], "SITECONF")
    else:
        cvmfs_path = os.environ.get("CVMFS", "/cvmfs")
        siteconf_path = os.path.join(cvmfs_path, "cms.cern.ch", "SITECONF")
    return siteconf_path

if 'glidein_config' not in os.environ:
    print ("No glidein_config environment variable present; defaulting value \
           to 'glidein_config'")
    os.environ.setdefault('glidein_config', 'glidein_config')
    if not os.path.exists(os.environ['glidein_config']):
        print ("Unable to locate the glidein configuration file %s; failing  \
               script." % os.environ['glidein_config'])
        sys.exit(int(os.environ["ERROR_NO_GLIDEIN_CONFIG"]))

    glidein_config = {}
    for line in open(os.environ['glidein_config'], 'r').xreadlines():
        line = line.strip()
        if line.startswith("#"):
            continue
        info = line.split(" ", 1)
        if len(info) != 2:
            continue
        glidein_config[info[0]] = info[1]

local_siteconf = os.path.join(get_siteconf_path(), "local")
if not os.path.exists(local_siteconf):
    if glidein_config.get("PARROT_RUN_WORKS", "FALSE") == "TRUE":
        print "Using parrot -- skipping SITECONF processing."
        sys.exit(0)
    print ("CVMFS siteconf path (%s) does not exist; is CVMFS running and \
            configured properly?" % local_siteconf)
else:
    print "Using SITECONF found at %s." % local_siteconf

job_config = os.path.join(local_siteconf, "JobConfig", "site-local-config.xml")
try:
    tree = xml.etree.ElementTree.parse(job_config)
except IOError:
    print os.environ["ERROR_NO_SITE_LOCAL_CONF_MSG"] + job_config
    sys.exit(int(os.environ["ERROR_NO_SITE_LOCAL_CONF"]))
job_config_root = tree.getroot()

if job_config_root[0].tag == 'site':
    print "Site name: %s" % job_config_root[0].attrib['name']
else:
    print os.environ["ERROR_NO_SITENAME_IN_SITECONG_MSG"]
    sys.exit(os.environ["ERROR_NO_SITENAME_IN_SITECONF"])

local_stage_out = job_config_root[0].find("local-stage-out")
pnn_found = False
if local_stage_out:
    phedex_node = local_stage_out.find("phedex-node")
    if (phedex_node is not None) and phedex_node.get("value"):
        pnn_found = True
        print "Locall stage-out node value: %s" % phedex_node.get("value")
    if not pnn_found:
        print os.environ["ERROR_PNN_NOT_FOUND_MSG"]
        sys.exit(int(os.environ["ERROR_PNN_NOT_FOUND"]))
else:
    print os.environ["ERROR_LOCAL_STAGEOUT_NOT_FOUND_MSG"]
    sys.exit(int(os.environ["ERROR_LOCAL_STAGEOUT_NOT_FOUND"]))

calib_data = job_config_root[0].find("calib-data")
if calib_data:
    frontier_connect = calib_data.find("frontier-connect")
    if frontier_connect:
        print "frontier-connect section was found"
        # site-local-config.xml has a proxy or a proxyconfig tag
        if frontier_connect.find("proxyconfig") is not None:
            proxy = frontier_connect.find("proxyconfig")
        else:
            proxy = frontier_connect.find("proxy")
        if proxy is not None and proxy.get("url"):
            print "Proxy string was found"
            print proxy.get("url")
        else:
            print os.environ["ERROR_NO_PROXY_STRING_MSG"]
            sys.exit(int(os.environ["ERROR_NO_PROXY_STRING"]))
    else:
        print os.environ["ERROR_FRONTIER_CONNECT_NOT_FOUND_MSG"]
        sys.exit(int(os.environ["ERROR_FRONTIER_CONNECT_NOT_FOUND"]))
else:
    print os.environ["ERROR_CALIB_DATA_NOT_FOUND_MSG"]
    sys.exit(int(os.environ["ERROR_CALIB_DATA_NOT_FOUND"]))

event_data = job_config_root[0].find("event-data")
if event_data:
    tfc = event_data.find("catalog")
    if (tfc is not None) and tfc.get("url"):
        print "TrivialFileCatalog string was found"
        print tfc.get("url")
    else:
        print os.environ["ERROR_NO_TFC_MSG"]
        sys.exit(int(os.environ['ERROR_NO_TFC']))
else:
    print os.environ["ERROR_NO_EVENT_DATA_MSG"]
    sys.exit(int(os.environ['ERROR_NO_EVENT_DATA']))

fallback_stage_out = job_config_root[0].find("fallback-stage-out")
if fallback_stage_out:
    phedex_node = fallback_stage_out.find("phedex-node")
    if (phedex_node is not None) and phedex_node.get("value"):
        pnn_found = True
        print "Fallback stage-out node value: %s" % phedex_node.get("value")
    if not pnn_found:
        print os.environ["ERROR_PNN_NOT_FOUND_MSG"]
        sys.exit(int(os.environ["ERROR_PNN_NOT_FOUND"]))
# else:
#     print os.environ["WARNING_FALLBACK_STAGEOUT_NOT_FOUND_MSG"]
#     sys.exit(int(os.environ["WARNING_FALLBACK_STAGEOUT_NOT_FOUND"]))
