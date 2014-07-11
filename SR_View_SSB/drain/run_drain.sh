#!/bin/bash
# Script in cmst1 acrontab 
# 5,20,35,50 * * * * lxplus ssh vocms202 /afs/cern.ch/user/c/cmst1/scratch0/MonitoringScripts/SR_View_SSB/drain/run_drain.sh &> /dev/null
# Script for Dashboard metric 
# outputfile drain.txt
# Script finds which site should be production status = drain, down, on and creates 1 file which is drain.txt
python /afs/cern.ch/user/c/cmst1/scratch0/MonitoringScripts/SR_View_SSB/drain/drain.py &> /afs/cern.ch/user/c/cmst1/scratch0/MonitoringScripts/SR_View_SSB/drain/drain.log
cp /afs/cern.ch/user/c/cmst1/scratch0/MonitoringScripts/SR_View_SSB/drain/drain.txt /afs/cern.ch/user/c/cmst1/www/SST/
