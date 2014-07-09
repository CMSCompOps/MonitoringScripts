# Author : Gökhan Kandemir
# E-mail : gokhan.kandemir@cern.ch
# Script Responsible : Site Support Team
# Script is located : /afs/cern.ch/user/c/cmst1/scratch0/MonitoringScripts/SR_View_SSB/morgue
# Outputs : 
   # /afs/cern.ch/user/c/cmst1/www/SST/morgue.txt (https://cmst1.web.cern.ch/CMST1/SST/morgue.txt)
# The script is being run by an acronjob
# The acronojb is in the acrontab of the user: cmst1
# 5,20,35,50 * * * * lxplus ssh vocms202 /afs/cern.ch/user/c/cmst1/scratch0/MonitoringScripts/SR_View_SSB/morgue/run_morgue.sh &> /dev/null
# Description : # Script finds which site should be in morgue and creates 1 file which is morgue.txt [1]

[1] https://cmst1.web.cern.ch/CMST1/SST/morgue.txt
