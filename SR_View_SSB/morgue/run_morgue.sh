#!/bin/bash

BASE=$(dirname $(readlink -f "${BASH_SOURCE[0]}"))
source $BASE/../../init.sh
OUT="$SSTOUT/metrics/morgue/"

if [ ! -d "$OUT" ]; then
    mkdir $OUT
fi

python morgue.py $OUT/morgue.txt &> $OUT/morgue.log

cp $OUT/morgue.txt /afs/cern.ch/user/c/cmssst/www/others/
