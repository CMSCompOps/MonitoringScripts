#!/usr/bin/python

import json
import subprocess
import urllib2
import httplib
import os
import ssl

site_db_url = 'cmsweb.cern.ch'
sites_admins_api = '/sitedb/data/prod/site-responsibilities'
site_names_api = '/sitedb/data/prod/site-names'
gitlab_token = "****************"
admin_roles = ['Site Executive', 'Site Admin', 'Admin']
group_url = 'https://gitlab.cern.ch/api/v3/groups/4099/projects?per_page=100&page=%s&private_token=%s'
user_url = 'https://gitlab.cern.ch/api/v3/users?username=%s&private_token=%s'
project_members_url = 'https://gitlab.cern.ch/api/v3/projects/%s/members?private_token=%s'
headers = {"Accept": "application/json"}


def parse_data(url, api = None):
	if api:  
		data = parse_data_cert(url, api)
	else:
		data = urllib2.urlopen(url).read()
	data = json.loads(data)
	return data

def parse_data_cert(url, api):
	conn = httplib.HTTPSConnection(
		url,
		cert_file = X509_USER_PROXY,
		key_file = X509_USER_PROXY, 
	)
	r1 = conn.request("GET", api, None, headers)
	r2 = conn.getresponse()
	request = r2.read()
	return request

proxy_files = [filename for filename in os.listdir('/tmp/') if filename.startswith("x509up_u")]
for proxy_file in proxy_files:
	try:
		X509_USER_PROXY = "/tmp/" + proxy_file
		parse_data(site_db_url, sites_admins_api)
	except ssl.SSLError:
		print "Proxy problem, let's try other"
	else:
		print X509_USER_PROXY + " will be used"

site_admins = parse_data(site_db_url, sites_admins_api)
site_admins = site_admins['result']
site_names = parse_data(site_db_url, site_names_api)
site_names = site_names['result']

for admin in site_admins:
	for site in site_names:
		if admin[1] == site[1]: admin[1] = site[2]

group_projects = parse_data(group_url %('1', gitlab_token)) + parse_data(group_url %('2',gitlab_token))
for project in group_projects:
	project_members = parse_data(project_members_url %(project['id'], gitlab_token))
	project_members = [member['username'] for member in project_members]
	for admin in site_admins:
		if project['name'] == admin[1] and admin[2] in admin_roles and admin[0] not in project_members:
			user = parse_data(user_url %(admin[0], gitlab_token))
			if user:
				print user
				subprocess.call('curl --header "PRIVATE-TOKEN: %s" -X POST "https://gitlab.cern.ch/api/v3/projects/%s/members?user_id=%s&access_level=30"' 
					%(gitlab_token, project['id'], str(user[0]["id"])), shell=True)
