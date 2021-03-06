#!/bin/bash

# go to the path that contain this script
cd $(dirname $(readlink -f "${BASH_SOURCE[0]}"))
source ./init.sh
OUT=$SSTBASE/output/metrics/mondayTables

if [ ! -d "$OUT" ]; then
    mkdir -p $OUT
fi

python	mondayTables.py $OUT
cp $OUT/* /afs/cern.ch/user/c/cmssst/www/mondayTables/
