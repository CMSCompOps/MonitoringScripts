# --Waiting Room Criteria--
# A site is moved into the WR if site readiness percentage is <80% for both: last week AND last 3 months

# --INFO--
# Script for Dashboard metric 152: SiteReadiness 1W&3M (>80%, yes=green, no=red) 
# Script responsible: John Artieda (artiedaj@fnal.gov)
# output dir:  /afs/cern.ch/user/c/cmst1/www/WFMon/
# output file: BadSites_SiteReadiness.txt
# web	https://cmst1.web.cern.ch/CMST1/WFMon/BadSites_SiteReadiness.txt
# Script in acrontab t1
# 5,20,35,50 * * * * => Every 15 minutes every day (starting at 00:05)
# 5,20,35,50 * * * * lxplus ssh vocms202 /afs/cern.ch/user/c/cmst1/scratch0/MonitoringScripts/SR_View_SSB/WRCriteria/run_badSites_SiteReadiness.sh &> /dev/null 