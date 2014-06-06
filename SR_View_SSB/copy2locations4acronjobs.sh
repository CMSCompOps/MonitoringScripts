#!/bin/sh
location="/afs/cern.ch/user/c/cmst1/scratch0/MonitoringScripts/SR_View_SSB"
cd $location
git pull

#ActiveSites
# Already in the right location: $location/ActiveSites/

#WRControl
#cp -a $location/WRControl/. /afs/cern.ch/user/c/cmst1/scratch0/Waitingroom_Dashboard/

#WRCriteria
#cp -a $location/WRCriteria/. /afs/cern.ch/user/c/cmst1/scratch0/SiteReadiness_Dashboard/

#WRDays
#cp -a $location/WRDays/. /afs/cern.ch/user/c/cmst1/scratch0/Waitingroom_Dashboard/Waitingroom_SummedMetric/

#echo "*** All copies completed ***"