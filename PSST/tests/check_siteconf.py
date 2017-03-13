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

local_siteconf = os.path.join(get_siteconf_path(), "local")
if not os.path.exists(local_siteconf):
	if glidein_config.get("PARROT_RUN_WORKS", "FALSE") == "TRUE":
		print "Using parrot -- skipping SITECONF processing."
		sys.exit(0)
	print "CVMFS siteconf path (%s) does not exist; is CVMFS running and configured properly?" % local_siteconf
else:
	print "Using SITECONF found at %s." % local_siteconf

job_config = os.path.join(local_siteconf, "JobConfig", "site-local-config.xml")
try:
	tree = xml.etree.ElementTree.parse(job_config)
except IOError:
	print "ERROR: site-local-config.xml was not found in %s" %job_config
	sys.exit(0)
job_config_root = tree.getroot()

if job_config_root[0].tag == 'site':
	print "Site name: %s" %job_config_root[0].attrib['name']
else:
	print os.environ["ERROR_NO_SITENAME_IN_SITECONG_MSG"]
	sys.exit(os.environ["ERROR_NO_SITENAME_IN_SITECONF"])

local_stage_out = job_config_root[0].find("local-stage-out")
pnn_found = False
if local_stage_out:
	phedex_node = local_stage_out.find("phedex-node")
	if (phedex_node != None) and phedex_node.get("value"):
		pnn_found = True
		print "Locall stage-out node value: %s" %phedex_node.get("value")
	if not pnn_found:
		print os.environ["ERROR_PNN_NOT_FOUND_MSG"]
		sys.exit(int(os.environ["ERROR_PNN_NOT_FOUND"]))
else:
	print os.environ["ERROR_LOCAL_STAGEOUT_NOT_FOUND_MSG"]
	sys.exit(int(os.environ["ERROR_LOCAL_STAGEOUT_NOT_FOUND"]))

calib_data = job_config_root[0].find("calib-data")
if calib_data:
	frontier_connect=calib_data.find("frontier-connect")
	if frontier_connect:
		print "frontier-connect section was found"
	else:
		print os.environ["ERROR_FRONTIER_CONNECT_NOT_FOUND_MSG"]
		sys.exit(int(os.environ["ERROR_FRONTIER_CONNECT_NOT_FOUND"]))
else:
	print os.environ["ERROR_CALIB_DATA_NOT_FOUND_MSG"]
	sys.exit(int(os.environ["ERROR_CALIB_DATA_NOT_FOUND"]))


fallback_stage_out = job_config_root[0].find("fallback-stage-out")
if fallback_stage_out:
	phedex_node = fallback_stage_out.find("phedex-node")
	if (phedex_node != None) and phedex_node.get("value"):
		pnn_found = True
		print "Fallback stage-out node value: %s" %phedex_node.get("value")
	if not pnn_found:
		print os.environ["WARNING_PNN_NOT_FOUND_MSG"]
		sys.exit(int(os.environ["WARNING_PNN_NOT_FOUND"]))
else:
	print os.environ["WARNING_FALLBACK_STAGEOUT_NOT_FOUND_MSG"]
	sys.exit(int(os.environ["WARNING_FALLBACK_STAGEOUT_NOT_FOUND"]))