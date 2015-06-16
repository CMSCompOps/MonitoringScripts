#!/bin/bash

# go to the path that contain this script
cd $(dirname $(readlink -f "${BASH_SOURCE[0]}"))

source ../../init.sh

# output directory for this script
OUT=$SSTBASE/output/test/samObserver

if [ ! -d "$OUT" ]; then
    mkdir -p $OUT
fi

samURL="http://wlcg-sam-cms.cern.ch/dashboard/request.py/getstatsresultsmin?profile_name=CMS_CRITICAL_FULL&plot_type=quality&start_time={0}&end_time={1}&granularity=single&group_name={2}&view=siteavl"
# SAM test date:
date="2015-05-21{0}"
info="QUERY: get SAM test results, time range: 2015-05-21 00:00:00, 2015-05-21 23:00:00"
if [ "$1" == "getSAM" ]; then
    python observer.py $OUT $samURL $date
fi

reportTemplate=$SSTBASE/data/samObservationReportTemplate.html

if [ "$1" == "html" ]; then
    python html.py $reportTemplate "$info" $OUT
fi
