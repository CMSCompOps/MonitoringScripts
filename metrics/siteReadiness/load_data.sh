#!/bin/bash

# go to the path that contain this script
cd $(dirname $(readlink -f "${BASH_SOURCE[0]}"))
source ../../init.sh
OUT=$SSTBASE/output/metrics/siteReadiness

if [ ! -d "$OUT" ]; then
    mkdir -p $OUT
fi

d=$(<lastdate.txt)
enddate=$(date -I --utc)
echo "Deleting old file"
rm -rf /afs/cern.ch/user/c/cmssst/www/siteReadiness/siteReadiness.txt
echo "Starting $d"
d=$(date -I --utc -d "$d + 1 day")
echo $d > lastdate.txt
echo "$d - $(date)" > results
python dailyMetric.py $d $OUT
cp $OUT/* /afs/cern.ch/user/c/cmssst/www/siteReadiness/
