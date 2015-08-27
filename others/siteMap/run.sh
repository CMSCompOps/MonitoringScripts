#!/bin/bash

# go to the path that contains this script
cd $(dirname $(readlink -f "${BASH_SOURCE[0]}"))

source ../../init.sh

# output directory for this script
OUT=$SSTBASE/output/others/siteMap

if [ ! -d "$OUT" ]; then
    mkdir -p $OUT
fi

python siteMap.py $SSTDATA/siteMap/config.json $SSTDATA/siteMap/template.html $OUT/out.html
