#!/bin/bash
# Script finds which site should be production status = drain, down, on
cd /afs/cern.ch/user/c/cmst1/scratch0/MonitoringScripts/SR_View_SSB/drain
python drain.py &> drain_log.txt
cp drain.txt /afs/cern.ch/user/c/cmst1/www/SST/
cp drain_log.txt /afs/cern.ch/user/c/cmst1/www/SST/