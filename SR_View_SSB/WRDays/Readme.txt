# --INFO--
# Script for Dashboard metric 154, 155, 156: WR days/last x months
# Script responsible: John Artieda (artiedaj@fnal.gov)
# output dir /afs/cern.ch/user/c/cmst1/www/SST/
# output file WaitingRoom_1MonthSum.txt
# output file WaitingRoom_2MonthSum.txt
# output file WaitingRoom_3MonthSum.txt
# web	https://cmst1.web.cern.ch/CMST1/WFMon/WaitingRoom_1MonthSum.txt
# Script in acrontab t1
# 5,20,35,50 * * * * => Every 15 minutes every day (starting at 00:05)
# 5,20,35,50 * * * * lxplus ssh vocms202 /afs/cern.ch/user/c/cmst1/scratch0/MonitoringScripts/SR_View_SSB/WRDays/run_WaitingRoom_Sites.sh &> /dev/null