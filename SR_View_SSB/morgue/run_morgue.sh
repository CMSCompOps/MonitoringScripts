#!/bin/bash
# Script in cmst1 acrontab 
# 5,20,35,50 * * * * lxplus ssh vocms202 /afs/cern.ch/user/c/cmst1/scratch0/MonitoringScripts/morgue/run_morgue.sh &> /dev/null
# Script for Dashboard metric 
# outputfile morgue.txt
# Script finds which site should be in morgue and creates 1 file which is morgue.txt
python /afs/cern.ch/user/c/cmst1/scratch0/MonitoringScripts/SR_View_SSB/morgue/morgue.py &> /afs/cern.ch/user/c/cmst1/scratch0/MonitoringScripts/SR_View_SSB/morgue/morgue.log
cp /afs/cern.ch/user/c/cmst1/scratch0/MonitoringScripts/SR_View_SSB/morgue/morgue.txt /afs/cern.ch/user/c/cmst1/www/SST/
