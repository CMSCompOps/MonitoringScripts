#!/bin/bash
# Script finds which site should be production status = drain, down, on and creates 1 file which is drain.txt
python /afs/cern.ch/user/c/cmst1/scratch0/MonitoringScripts/SR_View_SSB/drain/drain.py &> /afs/cern.ch/user/c/cmst1/scratch0/MonitoringScripts/SR_View_SSB/drain/drain.log
cp /afs/cern.ch/user/c/cmst1/scratch0/MonitoringScripts/SR_View_SSB/drain/drain.txt /afs/cern.ch/user/c/cmst1/www/SST/
