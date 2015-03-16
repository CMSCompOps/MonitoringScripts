#!/bin/bash

# go to the path that contain this script
cd $(dirname $(readlink -f "${BASH_SOURCE[0]}"))

source ../../init.sh

# output directory for this script
OUT=$SSTBASE/output/metrics/analysis

if [ ! -d "$OUT" ]; then
    mkdir -p $OUT
fi

python usableSitesManualChanges.py 'https://cmst1.web.cern.ch/CMST1/SST/analysis/usableSitesManualChanges.txt' $OUT/usableSitesManualChanges.txt

cp $OUT/* /afs/cern.ch/user/c/cmst1/www/SST/analysis
