#!/bin/bash
# Script in acrontab t1
# 5,20,35,50 * * * * lxplus ssh vocms202 /afs/cern.ch/user/c/cmst1/scratch0/Waitingroom_Dashboard/source_The_Run_File_WaitingRoom_Sites.sh &> /dev/null
# Script for Dashboard metric 153
# outputfile WaitingRoom_Sites.txt
# outputdir /afs/cern.ch/user/c/cmst1/www/WFMon/

cd /afs/cern.ch/user/c/cmst1/scratch0/Waitingroom_Dashboard
source run_WaitingRoom_Sites.sh
