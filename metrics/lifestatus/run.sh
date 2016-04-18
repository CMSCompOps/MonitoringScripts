#!/bin/bash

# go to the path that contain this script
cd $(dirname $(readlink -f "${BASH_SOURCE[0]}"))
source ../../init.sh
OUT=$SSTBASE/output/metrics/newLifeStatus

if [ ! -d "$OUT" ]; then
    mkdir -p $OUT
fi

date=$(date -I --utc -d "yesterday")

python	lifestatus.py $date $OUT
cp $OUT/* /afs/cern.ch/user/c/cmssst/www/newLifeStatus/
cp $OUT/* /afs/cern.ch/user/c/cmssst/www/lifestatus/
