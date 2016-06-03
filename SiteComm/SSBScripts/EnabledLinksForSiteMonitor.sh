#!/bin/sh
pushd . > /dev/null
cd /tmp
$HOME/COMP/SITECOMM/SSBScripts/EnabledLinksForSiteMonitor.py
mv EnabledLinksForSiteMonitor.txt  /afs/cern.ch/cms/LCG/SiteComm/
mv EnabledLinksStatus.html   /afs/cern.ch/cms/LCG/SiteComm/
popd > /dev/null

