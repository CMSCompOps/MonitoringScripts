#!/bin/sh
# before copying files please do a git pull at:
base="/afs/cern.ch/cms/LCG/SiteComm/MonitoringScripts/"
cd $base
git pull

location=$base"SR_View_SSB/"

#ActiveSites
# Already in the right location: $location/ActiveSites/

#WRControl
cp -a $location/WRControl/. /afs/cern.ch/user/c/cmst1/scratch0/Waitingroom_Dashboard/

#WRCriteria
cp -a $location/WRCriteria/. /afs/cern.ch/user/c/cmst1/scratch0/SiteReadiness_Dashboard/

#WRDays
cp -a $location/WRDays/. /afs/cern.ch/user/c/cmst1/scratch0/Waitingroom_Dashboard/Waitingroom_SummedMetric/
