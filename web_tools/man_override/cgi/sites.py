import fcntl
import json
from datetime import datetime
import csv

class Sites(object):
	def __init__(self, input_file, original_metric_file):
		self.file = input_file
		self.header = []
		self.original_metric_file = original_metric_file
		self.sites = self.read_input()

	def read_input(self):
		sites = []
		all_sites = set()
		fake_sites = ['T1_RU_JINR_Disk','T1_UK_RAL_Disk','T1_US_FNAL_Disk','T2_CH_CERN_Wigner']
		with open(self.file, 'r') as input_file:
                        sites = [item for item in csv.reader(input_file, delimiter='\t') if '#' not in item[0]]
                input_file.close()
		overriden_sites = zip(*sites)[1] if len(sites) > 0 else []
		#mergin sites from manual override metric and sitedb
		site_db_info = '/afs/cern.ch/user/c/cmssst/www/siteDbInfo/site_names.json'
		with open(site_db_info, 'r') as site_db_file:
			cms_sites = json.load(site_db_file)
			all_sites = [item[2] for item in cms_sites['result'] if item[0] == 'cms']
		site_db_file.close()
		for site in all_sites:
			if site not in overriden_sites and site not in fake_sites:
				site = [datetime.now().strftime("%Y-%m-%d %H:%M:%S"), site, 'no_override', 'no_color', 'url']
				sites.append(site)
		return sites
			
	def write_changes(self, updated_sites):
		with open(self.file, 'w') as output_file:
			fcntl.flock(output_file, fcntl.LOCK_EX | fcntl.LOCK_NB)
			for item in self.header:	
				output_file.writelines(item)
			for row in updated_sites:
				if row[2] != 'no_override':
					output_file.write(datetime.now().strftime("%Y-%m-%d %H:%M:%S")+"\t"+row[1]+"\t"+row[2]+"\t"+row[3]+"\t"+row[4]+"\n")
			fcntl.flock(output_file, fcntl.LOCK_UN)
		output_file.close()

