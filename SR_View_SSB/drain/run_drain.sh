#!/bin/bash
# Script finds which site should be production status = drain, down, on and creates 1 file which is drain.txt
python drain.py &> drain_log.txt
cp drain.txt /afs/cern.ch/user/c/cmst1/www/SST/
cp drain_log.txt /afs/cern.ch/user/c/cmst1/www/SST/