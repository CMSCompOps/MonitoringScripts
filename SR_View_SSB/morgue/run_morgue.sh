#!/bin/bash
# Script finds which site should be in morgue and creates 1 file which is morgue.txt
python /afs/cern.ch/user/c/cmst1/scratch0/MonitoringScripts/SR_View_SSB/morgue/morgue.py &> /afs/cern.ch/user/c/cmst1/scratch0/MonitoringScripts/SR_View_SSB/morgue/morgue.log
cp /afs/cern.ch/user/c/cmst1/scratch0/MonitoringScripts/SR_View_SSB/morgue/morgue.txt /afs/cern.ch/user/c/cmst1/www/SST/