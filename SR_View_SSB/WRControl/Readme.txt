# --INFO--
# Script for Dashboard metric 153: Waiting Room (in=red, out=green)
# Reads from: SR Status, SR Ranking, WR manual, Morgue.
# Script responsible: John Artieda (artiedaj@fnal.gov)
# output dir /afs/cern.ch/user/c/cmst1/www/WFMon/
# output file WaitingRoom_Sites.txt
# web	https://cmst1.web.cern.ch/CMST1/WFMon/WaitingRoom_Sites.txt
# Script in acrontab cmst1
# */15 * * * * => Every 15 minutes every day
# */15 * * * * lxplus ssh vocms077 /afs/cern.ch/user/c/cmst1/scratch0/MonitoringScripts/SR_View_SSB/WRControl/run_WaitingRoom_Sites.sh &> /dev/null
