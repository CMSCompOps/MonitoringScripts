# Script Responsible: Site Support Team
# Script location: /afs/cern.ch/user/c/cmst1/scratch0/MonitoringScripts/SR_View_SSB/drain
# Output: /afs/cern.ch/user/c/cmst1/www/SST/drain.txt (https://cmst1.web.cern.ch/CMST1/SST/drain.txt

# The script is being run by an acronjob
# The acronjob is in the acrontab of the user: cmst1
# 5,20,35,50 * * * * lxplus ssh vocms202 /afs/cern.ch/user/c/cmst1/scratch0/MonitoringScripts/SR_View_SSB/drain/run_drain.sh &> /dev/null
# Description : # Script finds which site should be production status = drain, down, on and creates 1 file which is drain.txt [1]

[1] https://cmst1.web.cern.ch/CMST1/SST/drain.txt