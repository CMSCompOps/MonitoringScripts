# Author : Gökhan Kandemir
# E-mail : gokhan.kandemir@cern.ch
# Script Responsible : Site Support Team
# Script is located  : /afs/cern.ch/user/c/cmst1/scratch0/MonitoringScripts/GGUS
# Outputs : 
   # /afs/cern.ch/user/c/cmst1/www/SST/ggusticketmeeting.txt (https://cmst1.web.cern.ch/CMST1/SST/ggusticketmeeting.txt)
   # /afs/cern.ch/user/c/cmst1/www/SST/ggusticketmetrics.txt (https://cmst1.web.cern.ch/CMST1/SST/ggusticketmetrics.txt)
# The script is being run by an acronjob
# The acronojb is in the acrontab of the user: cmst1
# 5,20,35,50 * * * * lxplus ssh vocms202 /afs/cern.ch/user/c/cmst1/scratch0/MonitoringScripts/GGUS/run_ggus.sh &> /dev/null
# Description : The script is used for getting ggus ticket information for each site. Also it calcultes how many tickets the site has and it creates 2 files. One of them is for metric 198 [1], the other one is for twiki table.

[1] https://dashb-ssb.cern.ch/dashboard/request.py/siteviewhistory?columnid=198&view=Site%20Readiness
[2] https://cmst1.web.cern.ch/CMST1/SST/ggusticketmeeting.txt
