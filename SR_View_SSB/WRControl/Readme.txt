# --INFO--
# Script for Dashboard metric 153: Waiting Room (in=red, out=green)
# Script responsible: John Artieda (artiedaj@fnal.gov)
# output dir /afs/cern.ch/user/c/cmst1/www/WFMon/
# output file WaitingRoom_Sites.txt
# web	https://cmst1.web.cern.ch/CMST1/WFMon/WaitingRoom_Sites.txt
# Script in acrontab cmst1
# 5,20,35,50 * * * * => Every 15 minutes every day (starting at 00:05)
# 5,20,35,50 * * * * lxplus ssh vocms202 /afs/cern.ch/user/c/cmst1/scratch0/MonitoringScripts/SR_View_SSB/WRControl/run_WaitingRoom_Sites.sh &> /dev/null