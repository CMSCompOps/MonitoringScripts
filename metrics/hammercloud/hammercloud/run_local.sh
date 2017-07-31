#!/bin/bash

# go to the path that contain this script
cd $(dirname $(readlink -f "${BASH_SOURCE[0]}"))
source init.sh
OUT=$SSTBASE/output/metrics/hammercloud

if [ ! -d "$OUT" ]; then
    mkdir -p $OUT
fi

date=$(date "+%Y-%m-%dT%H:%M:%SZ" --utc -d "15 minutes ago")

python hammercloud.py --date=$date --outputDir=$OUT	
cp $OUT/* /afs/cern.ch/user/c/cmssst/www/hammercloud/
echo "Output copied to /afs/cern.ch/user/c/cmssst/www/hammercloud/"
