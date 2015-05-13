--INFO--
Script for Dashboard metric 145: Pledge [cores] - obtains official pledge from SiteDB
Script responsible: John Artieda (artiedaj@fnal.gov)
output dir 	/afs/cern.ch/user/c/cmst1/www/SST/
output file 	pledges.txt
web		https://cmst1.web.cern.ch/CMST1/SST/pledges.txt

—-
not running in a cronjob
Run script manually when needed to update:
set up a proxy before running run_pledges.sh script
	lxplus
	source /afs/cern.ch/cms/LCG/LCG-2/UI/cms_ui_env.sh
	voms-proxy-init -voms cms
	X509_USER_PROXY=/tmp/x509up_u47967;export X509_USER_PROXY