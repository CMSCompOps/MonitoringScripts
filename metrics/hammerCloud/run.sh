#!/bin/bash

# go to the path that contain this script
cd $(dirname $(readlink -f "${BASH_SOURCE[0]}"))

source ../../init.sh

# output & temp directory for this script
OUT=$SSTBASE/output/metrics/hammerCloud
TMP=$SSTBASE/tmp/metrics/hammerCloud

if [ ! -d "$OUT" ]; then
    mkdir -p $OUT
fi

if [ ! -d "$TMP" ]; then
    mkdir -p $TMP
fi

python hammerCloud.py hctest $OUT/hctest.txt
