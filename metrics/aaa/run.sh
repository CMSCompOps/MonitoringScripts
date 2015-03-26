#!/bin/bash

# go to the path that contain this script
cd $(dirname $(readlink -f "${BASH_SOURCE[0]}"))

source ../../init.sh

# output & temp directory for this script
OUT=$SSTBASE/output/metrics/aaa

if [ ! -d "$OUT" ]; then
    mkdir -p $OUT
fi

# you just need to put host name into this SAM url
samURL="http://wlcg-sam-cms.cern.ch/dashboard/request.py/getTestResults?profile_name=CMS_CRITICAL&metrics=org.cms.WN-xrootd-access%20(/cms/Role_lcgadmin)&hostname={0}&flavours=CREAM-CE,OSG-CE,ARC-CE,SRMv2&time_range=last2Weeks"

# notice parameters in the following url
hcURL="http://dashb-cms-job.cern.ch/dashboard/request.py/jobsummary-plot-or-table?activity=hcxrootd&date1={0}&date2={1}&sortby=inputse&scale=linear&check=terminated"

python aaa.py $samURL $hcURL $OUT/aaa.txt
