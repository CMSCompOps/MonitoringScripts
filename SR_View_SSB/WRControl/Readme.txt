# --INFO--
# Script for Dashboard metric 153: Waiting Room (in=red, out=green)
# Script responsible: John Artieda (artiedaj@fnal.gov)
# output dir /afs/cern.ch/user/c/cmst1/www/WFMon/
# output file WaitingRoom_Sites.txt
# Script in acrontab t1
# 5,20,35,50 * * * * => Every 15 minutes every day (starting at 00:05)
# 5,20,35,50 * * * * lxplus ssh vocms202 /afs/cern.ch/user/c/cmst1/scratch0/Waitingroom_Dashboard/source_The_Run_File_WaitingRoom_Sites.sh &> /dev/null 