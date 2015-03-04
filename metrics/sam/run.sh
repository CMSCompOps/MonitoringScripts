#!/bin/bash

# go to the path that contain this script
cd $(dirname $(readlink -f "${BASH_SOURCE[0]}"))

source ../../init.sh

# output & temp directory for this script
OUT=$SSTBASE/output/metrics/sam
TMP=$SSTBASE/tmp/metrics/sam

if [ ! -d "$OUT" ]; then
    mkdir -p $OUT
fi

if [ ! -d "$TMP" ]; then
    mkdir -p $TMP
fi

# run sum metric script
python sam.py $OUT/sam.txt
