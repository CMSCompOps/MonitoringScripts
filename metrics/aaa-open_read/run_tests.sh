#!/bin/bash

cd /afs/cern.ch/user/e/eeren/www/MonitoringScripts/metrics/aaa-open_read
python aaa-tests.py > aaa-"$(date)".log

exit 0 
