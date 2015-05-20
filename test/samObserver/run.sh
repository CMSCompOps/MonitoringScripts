#!/bin/bash

# go to the path that contain this script
cd $(dirname $(readlink -f "${BASH_SOURCE[0]}"))

source ../../init.sh

# output & temp directory for this script
OUT=$SSTBASE/output/test/samObserver

if [ ! -d "$OUT" ]; then
    mkdir -p $OUT
fi

samURL="http://wlcg-sam-cms.cern.ch/dashboard/request.py/getstatsresultsmin?profile_name=CMS_CRITICAL_FULL&plot_type=quality&start_time={0}&end_time={1}&granularity=single&group_name={2}&view=siteavl"
# SAM test date:
date="2015-05-20{0}"

python observer.py $OUT $samURL $date
