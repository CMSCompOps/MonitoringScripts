#!/usr/bin/python

import os
import re
import sys
import tempfile

try:
	import xml.etree.ElementTree
except Exception, e:
	print "Unable to import ElementTree for parsing XML."
	print "Skipping this script; SITECONF data will be missing."
	print "This can be ignored if this is a RHEL5 host."
	print "Exception message: %s" % str(e)
	sys.exit(0)


def add_condor_config_var(glidein_config, name=None, kind="C", value=None, publish=True, condor_name=None):
	if (name == None) or (value == None):
		print "Invalid condor configuration specified (name=%s; value=%s)" % (str(name), str(value))
		return

	if 'CONDOR_VARS_FILE' not in glidein_config:
		print "Warning: Missing condor vars file from configuration; ignoring (%s=%s)" % (name, value)
		return

	has_whitespace = re.compile("\s")
	if has_whitespace.search(name):
		print "Ignoring specified name as it contains whitespace (name=%s)." % name
		return
	if has_whitespace.search(value):
		print "Ignoring specified value as it contains whitespace (value=%s)." % name
		return
	if condor_name and has_whitespace.search(condor_name):
		print "Ignoring specified HTCondor variable name as it contains whitespace (condor_name=%s)." % condor_name
		return

	if condor_name == None:
		condor_name = name
	if publish:
		exp_condor = "Y"
	else:
		exp_condor = "N"

	fname = glidein_config['CONDOR_VARS_FILE']
	vars_dir, vars_file = os.path.split(fname)
	tempfd = tempfile.NamedTemporaryFile(dir=vars_dir, prefix=vars_file, delete=False)
	try:
		fd = open(fname, "r")
		for line in fd.xreadlines():
			if line.startswith(name):
				continue
			tempfd.write(line)
		tempfd.write("%s %s %s %s N %s -\n" % (name, kind, value, condor_name, exp_condor))
	except:
		os.unlink(tempfd.name)
		raise
	tempfd.close()
	fd.close()
	os.rename(tempfd.name, fname)

	print "Setting value of %s to %s." % (name, value)


def add_glidein_config(name, value):
	if (name == None) or (value == None):
		print "Invalid condor configuration specified (name=%s; value=%s)" % (str(name), str(value))
		return

	fname = os.environ['glidein_config']
	conf_dir, conf_file = os.path.split(fname)
	tempfd = tempfile.NamedTemporaryFile(dir=conf_dir, prefix=conf_file, delete=False)
	try:
		fd = open(fname, "r")
		for line in fd.xreadlines():
			if line.startswith(name):
				continue
			tempfd.write(line)
		tempfd.write("%s %s\n" % (name, value))
	except:
		os.unlink(tempfd.name)
		raise
	tempfd.close()
	os.rename(tempfd.name, fname)

	print "Setting glidein config value of %s to %s." % (name, value)
	fd.close()
 

def get_siteconf_path():
	if 'VO_CMS_SW_DIR' in os.environ:
		siteconf_path = os.path.join(os.environ['VO_CMS_SW_DIR'], "SITECONF")
	else:
		cvmfs_path = os.environ.get("CVMFS", "/cvmfs")
		siteconf_path = os.path.join(cvmfs_path, "cms.cern.ch", "SITECONF")
	return siteconf_path


def create_local_glidein(glidein_config):
	local_gconf = os.path.join(get_siteconf_path(), "local", "GlideinConfig", 'local-groups.txt')
	cmssite = glidein_config.get("GLIDEIN_CMSSite")

	if not os.path.exists(local_gconf) and not cmssite:
		print "WARNING: Local group name list (%s) does not exist!" % local_gconf
		return

	groups = set()
	if cmssite:
		groups.add(cmssite)
	valid_group_re = re.compile(r"[-_=/A-Za-z0-9]+")
	if os.path.exists(local_gconf):
		for line in open(local_gconf).xreadlines():
			line = line.strip()
			if valid_group_re.match(line):
				groups.add(line)

	if not groups:
		return

	value = "stringListsIntersect(CMSGroups, \"%s\")" % ",".join([gname for gname in groups])
	add_glidein_config("GLIDEIN_Start", value)


def main():

	if 'glidein_config' not in os.environ:
		print "No glidein_config environment variable present; defaulting value to 'glidein_config'"
	os.environ.setdefault('glidein_config', 'glidein_config')
	if not os.path.exists(os.environ['glidein_config']):
		print "Unable to locate the glidein configuration file %s; failing script." % os.environ['glidein_config']
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
		print "CVMFS siteconf path (%s) does not exist; is CVMFS running and configured properly?" % local_siteconf
	else:
		print "Using SITECONF found at %s." % local_siteconf

	job_config = os.path.join(local_siteconf, "JobConfig", "site-local-config.xml")
	if not os.path.exists(job_config):
		print "site-local-config.xml does not exist in CVMFS (looked at %s); is CVMFS running and configured properly?" % job_config

	tree = xml.etree.ElementTree.parse(job_config)
	job_config_root = tree.getroot()

	site_name = None
	if job_config_root[0].get('name'):
		site_name = job_config_root[0].get('name')

	if site_name:
		add_condor_config_var(glidein_config, name="CMSProcessingSiteName", kind="S", value=site_name)
	else:
		print "No sitename detected!  Invalid SITECONF file?"
		sys.exit(os.environ["ERROR_NO_SITENAME_IN_SITECONF"])

	local_stage_out = job_config_root[0].find("local-stage-out")
	pnn_found = False
	if local_stage_out:
		phedex_node = local_stage_out.find("phedex-node")
		if (phedex_node != None) and phedex_node.get("value"):
			add_condor_config_var(glidein_config, name="CMSPhedexNodeName", kind="S", value=phedex_node.get("value"))
			pnn_found = True
	if not pnn_found:
		print "No PhEDEx node name found for local stageout."

	fallback_stage_out = job_config_root[0].find("fallback-stage-out")
	pnn_found = False
	if fallback_stage_out:
		phedex_node = fallback_stage_out.find("phedex-node")
		if (phedex_node != None) and phedex_node.get("value"):
			add_condor_config_var(glidein_config, name="CMSFallback_PhedexNodeName", kind="S", value=phedex_node.get("value"))
			pnn_found = True
	if not pnn_found:
		print "No PhEDEx node name found for fallback stageout."

	if 'USER_DN' in os.environ:
		dn = os.environ.get("USER_DN")
		r = re.compile("[-._@A-Za-z0-9=/]+")
		if r.match(dn):
			print "Based on USER_DN environment variable, limiting the pilot's running jobs to user %s" % dn
			add_glidein_config("GLIDEIN_USER", '"%s"' % dn)
			add_condor_config_var(glidein_config, name="GLIDEIN_USER", kind="C", value="-")
		else:
			print

	if 'GLIDEIN_CMSSite_Override' in glidein_config:
		add_glidein_config('GLIDEIN_CMSSite', glidein_config['GLIDEIN_CMSSite_Override'])

	if ('CMSIsLocal' in glidein_config) and (glidein_config['CMSIsLocal'].lower() == 'true'):
		create_local_glidein(glidein_config)

	sys.exit(0)	

if __name__ == "__main__":
	main()