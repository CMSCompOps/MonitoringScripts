from sets import Set
import json
from sites import Sites

class User(object):
	def __init__(self, adfs_login, cms_sites, allowed_groups, adfs_groups, allowed_adfs_groups, metric=None):
		self.cms_sites = cms_sites
		self.adfs_login = adfs_login
		self.allowed_groups = allowed_groups
		cms_site_admins = open('/afs/cern.ch/user/c/cmssst/www/siteDbInfo/cms_site_admins.json', 'r')
		cms_site_admins = cms_site_admins.read()
		self.cms_site_admins = json.loads(cms_site_admins)
		self.adfs_groups = adfs_groups.split(';')
		self.allowed_adfs_groups = allowed_adfs_groups
		self.metric = metric
		self.user_info = self.__determine_responsibilities()		

	def __determine_responsibilities(self):
		team_member = any(adfs_group in self.allowed_adfs_groups for adfs_group in self.adfs_groups)
		user_groups = set()
		user_roles = set()
		self.managed_sites = set()
		if team_member:
			if "cms-tier0-operations" in self.adfs_groups and self.metric == 'prodstatus':
				self.managed_sites.add('T0_CH_CERN')
			else:
				for site in self.cms_sites:
					self.managed_sites.add(site[1])
				#self.managed_sites = [site[1] for site in self.cms_sites]	
		#else:
		for item in self.cms_site_admins:
			if item[0] == self.adfs_login:	
				if item[1] in self.allowed_groups:
					user_groups.add(item[1])
					user_roles.add(item[2])
					for site in self.cms_sites:
						self.managed_sites.add(site[1])
				self.managed_sites.add(item[1])
		user_info = {
			"groups_roles": zip(user_groups, user_roles),
			"sites": self.managed_sites 
		}
			
		return user_info
