#!/bin/bash

# go to the path that contain this script
cd $(dirname $(readlink -f "${BASH_SOURCE[0]}"))

source ../../init.sh

# output directory for this script
OUT=$SSTBASE/output/metrics/analysis

if [ ! -d "$OUT" ]; then
    mkdir -p $OUT
fi

# usable sites manual changes URL
usableSitesMCJSON="http://dashb-ssb.cern.ch/dashboard/request.py/getplotdata?columnid=211&time=24&dateFrom=&dateTo=&sites=all&clouds=undefined&batch=1"
python usableSitesManualChanges.py $usableSitesMCJSON $OUT/usableSitesManualChanges.txt

# usable sites manual changes JSON URL
usableSitesMCTEXT="https://cmst1.web.cern.ch/CMST1/SST/analysis/usableSitesManualChanges.txt"
morgueTEXT="https://cmst1.web.cern.ch/CMST1/SST/morgue.txt"
# notice the time '%s' stamps for the start and 
hammerCloudJSON="http://dashb-ssb.cern.ch/dashboard/request.py/getplotdata?columnid=135&time=custom&dateFrom=%s&dateTo=%s&sites=all&clouds=undefined&debug=1&batch=1"
dashboardURLStamp="https://cmst1.web.cern.ch/CMST1/SST/analysis/usableSites.txt"
python usableSites.py $usableSitesMCTEXT $morgueTEXT $hammerCloudJSON $dashboardURLStamp $OUT/usableSites.txt $OUT/usableSites.json

cp $OUT/* /afs/cern.ch/user/c/cmst1/www/SST/analysis
