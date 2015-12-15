#!/bin/bash
## Script finds which site should be production status = drain, down, on
##cd /afs/cern.ch/user/c/cmst1/scratch0/MonitoringScripts/SR_View_SSB/drain

# go to the path that contains this script
cd $(dirname $(readlink -f "${BASH_SOURCE[0]}"))

source ../../init.sh

python drain.py &> drain_log.txt
cp drain.txt /afs/cern.ch/user/c/cmssst/www/others/ 
cp drain_log.txt /afs/cern.ch/user/c/cmssst/www/others/ 
