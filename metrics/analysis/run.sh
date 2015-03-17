#!/bin/bash

# go to the path that contain this script
cd $(dirname $(readlink -f "${BASH_SOURCE[0]}"))

source ../../init.sh

# output directory for this script
OUT=$SSTBASE/output/metrics/analysis

if [ ! -d "$OUT" ]; then
    mkdir -p $OUT
fi

usableSitesManualChangesMetricUrl="http://dashb-ssb.cern.ch/dashboard/request.py/getplotdata?columnid=211&time=24&dateFrom=&dateTo=&sites=all&clouds=undefined&batch=1"

python usableSitesManualChanges.py $usableSitesManualChangesMetricUrl= $OUT/usableSitesManualChanges.txt

cp $OUT/* /afs/cern.ch/user/c/cmst1/www/SST/analysis
