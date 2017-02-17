import urllib
import sys
import re
import xml.etree.ElementTree as ET

try: import yum
except ImportError: sys.exit(0)

if len(sys.argv) < 3:
	sys.stderr.write('not enough parameters! \n')
	sys.exit(1)

yb = yum.YumBase()

package_url = sys.argv[2]
cms_os = re.match("slc[5-7]_[0-9a-zA-Z]+", sys.argv[1]).group(0)
print cms_os

releases_url = "https://cmssdt.cern.ch/SDT/cgi-bin/ReleasesXML?anytype=1"
response = urllib.urlopen(releases_url)
realeses_file = response.read()

cms_archs = []
root = ET.fromstring(realeses_file)
for child in root:
	if cms_os in child.attrib['name'] and child.attrib['name'] not in cms_archs:
		cms_archs.append(child.attrib['name'])

required_packages = set()
for arch in cms_archs:
	response = urllib.urlopen(package_url + arch)
	package_file = response.read()
	regex_expression = '%s_platformSeeds="(.*?)"' % cms_os
	packages = re.findall(regex_expression, package_file, re.DOTALL)
	packages = packages[0].rstrip('\n')
	for package in packages.split():
		required_packages.add(package)

for package in required_packages:
	if yb.rpmdb.searchNevra(name=package):
		print "%s is installed" %package
	else:
		print "%s not installed" %package
		sys.exit(1)

sys.exit(0)