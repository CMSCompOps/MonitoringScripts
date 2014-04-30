Generic File Monitoring
CMSSW-based file-opening popularity reporting in TFC
https://cmsweb.cern.ch/gitweb/?p=siteconf/.git;a=tree
- this script checks how many sites have implemented this TFC change
- https://twiki.cern.ch/twiki/bin/view/Main/GenericFileMonitoring 
- Edit the site-local-config.xml to enable it and set the destination
- The additional line goes in the source-config stanza:
     statistics-destination name="cms-udpmon-collector.cern.ch:9331"

--INFO--
Script for Dashboard metric 189: file monitoring - reads from site-local-config.xml
Script responsible: John Artieda (artiedaj@fnal.gov)
output dir 	/afs/cern.ch/user/c/cmst1/www/SST/
output file 	gfm.txt
web		https://cmst1.web.cern.ch/CMST1/SST/gfm.txt

—-
To run script:
set up a proxy before running run_site_local_config.sh script
	lxplus
	source /afs/cern.ch/cms/LCG/LCG-2/UI/cms_ui_env.sh
	voms-proxy-init -voms cms