#!/bin/bash

#th that contain this script
cd $(dirname $(readlink -f "${BASH_SOURCE[0]}"))
source ../../init.sh

OUT=$SSTBASE/output/metrics/lifestatus

if [ ! -d "$OUT" ]; then
    mkdir -p $OUT
fi

date=$(date -I --utc -d "yesterday")

python	lifestatus.py $date $OUT
cp $OUT/* /afs/cern.ch/user/c/cmssst/www/lifestatus/
