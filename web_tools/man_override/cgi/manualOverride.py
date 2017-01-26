#!/afs/cern.ch/user/c/cmssst/www/man_override/cgi/venv/bin/python

#python modules
import os
import cgitb
import re
import cgi
from datetime import datetime
from operator import itemgetter

#project modules
from sites import Sites
from rights import User
from reason import Reason
from log import Log

#3d party modules
from jinja2 import Environment, FileSystemLoader

cgitb.enable()
env = Environment(loader=FileSystemLoader('../templates'))

crabstatus_original_file = '/afs/cern.ch/user/c/cmssst/www/analysis/usableSites.txt'
crabstatus_file = '/afs/cern.ch/user/c/cmssst/www/man_override/crabstatus/manualCrabStatus.txt'
crabstatus_reasons_file = '/afs/cern.ch/user/c/cmssst/www/man_override/crabstatus/manualCrabStatus_reasons.txt'
crabstatus_log_file = '/afs/cern.ch/user/c/cmssst/www/man_override/crabstatus/manualCrabStatus_log.txt'
crabstatus_groups = ['SiteDB', 'CRAB3']
crabstatus_states = ['enabled', 'disabled', 'no_override']
crabstatus_adfs_groups = ['cms-comp-ops-site-support-team']

lifeStatus_original_file = '/afs/cern.ch/user/c/cmssst/www/lifestatus/lifeStatus.txt'
lifeStatus_file = '/afs/cern.ch/user/c/cmssst/www/man_override/lifestatus/manualLifeStatus.txt'
lifeStatus_reasons_file = '/afs/cern.ch/user/c/cmssst/www/man_override/lifestatus/manualLifeStatus_reason.txt'
lifeStatus_log_file = '/afs/cern.ch/user/c/cmssst/www/man_override/lifestatus/manualLifeStatus_log.txt'
lifeStatus_groups = ['SiteDB']
lifeStatus_states = ['enabled', 'waiting_room', 'morgue', 'no_override']
lifeStatus_adfs_groups = ['cms-comp-ops-site-support-team']

prodStatus_original_file = '/afs/cern.ch/user/c/cmssst/www/prodstatus/ProdStatus.txt'
prodStatus_file = '/afs/cern.ch/user/c/cmssst/www/man_override/prodstatus/manualProdStatus.txt'
prodStatus_reasons_file = '/afs/cern.ch/user/c/cmssst/www/man_override/prodstatus/manualProdStatus_reason.txt'
prodStatus_log_file = '/afs/cern.ch/user/c/cmssst/www/man_override/prodstatus/manualProdStatus_log.txt'
prodStatus_groups = ['SiteDB']
prodStatus_states = ['enabled', 'disabled', 'drain', 'test', 'no_override']
prod_adfs_groups = ['cms-comp-ops-site-support-team', 'cms-tier0-operations', 'cms-comp-ops-workflow-team']

path = os.environ.get('PATH_INFO','')
adfs_login = os.environ.get('ADFS_LOGIN','')
adfs_groups = os.environ.get('ADFS_GROUP','')

def index(metric, original_metric_file, metric_file, metric_reasons_file, metric_groups, metric_adfs_groups):
	"""Function generates main page.
	For example - manualOverride.py/lifestatus
	"""
	template = env.get_template('%s.html' % metric)
	metric_name = Sites(metric_file, original_metric_file)
	user = User(adfs_login, metric_name.sites, metric_groups, adfs_groups, metric_adfs_groups, metric)
	reasons = Reason(metric_reasons_file)	
	metric_name.sites = sorted(metric_name.sites, key = itemgetter(1))
	for site in metric_name.sites:
		for item in reasons.sites:
			if site[1] == item[0]:
				site.append(item[1])
	print template.render(sites = metric_name.sites, adfs_login = adfs_login, user_info = user.user_info, metricName = metric)	

def update_site(site_name, metric, form, original_metric_file, metric_file, metric_reasons_file, metric_log_file, metric_groups, metric_states, metric_adfs_groups):
	"""Function called after form submit in the main page.
	1. Removing site from sites' list
	2. Removing old reason
	3. Adding updated site to sites' list
	4. Adding new reason to reasons' list
	5. Writintg new event in log
	"""
        metric_name = Sites(metric_file, original_metric_file)
        user = User(adfs_login, metric_name.sites, metric_groups, adfs_groups, metric_adfs_groups, metric)
        reasons = Reason(metric_reasons_file) 
	if site_name in user.managed_sites:
		for site in metric_name.sites:
			if site[1] == site_name and site[2] == form.getvalue("old-status") and form.getvalue("new-status") in metric_states:
				metric_name.sites.remove(site)
				#color = find_color(metric, form.getvalue('new-status'))
				#updated_site = [
					#datetime.now().strftime("%Y-%m-%d %H:%M:%S"), 
					#site_name, 
					#form.getvalue("new-status"), 
					#color, 
					#form.getvalue("url")
					#]
				for site in reasons.sites:
					if site[0] == site_name:
						reasons.sites.remove(site)
				if form.getvalue('new-status') != "no_override":
					color = find_color(metric, form.getvalue('new-status'))
                               		updated_site = [
						datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
						site_name,
						form.getvalue("new-status"),
						color,
						form.getvalue("url")
						]
					metric_name.sites.append(updated_site)
					reasons.sites.append([site_name, re.sub('[\s+]', ' ', form.getvalue("reason"))])
				reasons.write_changes(reasons.sites)
				metric_name.write_changes(metric_name.sites)
				log = Log(metric_log_file)
				new_log = [datetime.now().strftime("%Y-%m-%d %H:%M:%S"), adfs_login, site_name, form.getvalue('new-status'), form.getvalue('reason')]
				log.write_changes(new_log)
				url = "https://cmssst.web.cern.ch/cmssst/man_override/cgi/manualOverride.py/%s" %metric
				print "Status: 302 Moved"
				print "Location: %s" % url
				print 

def find_color(metric, new_status):
	if metric == 'lifestatus':
		if new_status == 'enabled':
			color = 'green'
		elif new_status == 'waiting_room':
			color = 'yellow'
		elif new_status == 'morgue':
			color = 'red'
	if metric == 'prodstatus':
		if new_status == 'enabled':
			color = 'green'
		elif new_status == 'disabled':
			color = 'yellow'
		elif new_status == 'drain':
			color = 'yellow'
		elif new_status == 'test':
			color = 'yellow'
	if metric == 'crabstatus':
		if new_status == 'enabled':
			color = 'green'
		elif new_status == 'disabled':
			color = 'red'
	return color

def print_header():
	print "Content-Type: text/html"
	print

def error():
	print_header()
	print "Sorry, something went wrong. Please refresh your browser"


if path == '/crabstatus':
	print_header()
	metric = 'crabstatus'
	index(metric, crabstatus_original_file, crabstatus_file, crabstatus_reasons_file, crabstatus_groups, crabstatus_adfs_groups)
elif path == '/lifestatus':
	print_header()
	metric = 'lifestatus' 
	index(metric, lifeStatus_original_file, lifeStatus_file, lifeStatus_reasons_file, lifeStatus_groups, lifeStatus_adfs_groups)
elif path == '/prodstatus':
        print_header()
        metric = 'prodstatus'
        index(metric, prodStatus_original_file, prodStatus_file, prodStatus_reasons_file, prodStatus_groups, prod_adfs_groups)

match_analysis = re.search('^\/crabstatus\/T[0-3]_[A-Z]{2}_.[a-zA-Z].+', path)
match_lifeStatus = re.search('^\/lifestatus\/T[0-3]_[A-Z]{2}_.[a-zA-Z].+', path)
match_productionStatus = re.search('^\/prodstatus\/T[0-3]_[A-Z]{2}_.[a-zA-Z].+', path)
if match_analysis:
	if os.environ['REQUEST_METHOD'] == 'POST':
		site_name = path[12:]
		metric = 'crabstatus'
		form = cgi.FieldStorage()
		if all (key in form for key in ('old-status', 'new-status', 'url')):
			update_site(site_name, metric, form, crabstatus_original_file, crabstatus_file, crabstatus_reasons_file, crabstatus_log_file, crabstatus_groups, crabstatus_states, crabstatus_adfs_groups)
		else:
			error()
if match_lifeStatus:
	if os.environ['REQUEST_METHOD'] == 'POST':
                site_name = path[12:]
                metric = 'lifestatus'
                form = cgi.FieldStorage()
                if all (key in form for key in ('old-status', 'new-status', 'url', 'reason')):
			if len(form.getvalue('reason')) < 251:
				update_site(site_name, metric, form, lifeStatus_original_file, lifeStatus_file, lifeStatus_reasons_file, lifeStatus_log_file, lifeStatus_groups, lifeStatus_states, lifeStatus_adfs_groups)
                else:
                        error()
if match_productionStatus:
        if os.environ['REQUEST_METHOD'] == 'POST':
                site_name = path[12:]
                metric = 'prodstatus'
                form = cgi.FieldStorage()
                if all (key in form for key in ('old-status', 'new-status', 'url', 'reason')):
                        if len(form.getvalue('reason')) < 251:
                                update_site(site_name, metric, form, prodStatus_original_file, prodStatus_file, prodStatus_reasons_file, prodStatus_log_file, prodStatus_groups, prodStatus_states, prod_adfs_groups)
                else:
                        error()
