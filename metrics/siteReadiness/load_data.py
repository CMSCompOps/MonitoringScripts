#!/bin/bash

# go to the path that contain this script
cd $(dirname $(readlink -f "${BASH_SOURCE[0]}"))
source ./init.sh
OUT=$SSTBASE/output/metrics/siteReadiness

if [ ! -d "$OUT" ]; then
    mkdir -p $OUT
fi

d=$(<lastdate.txt)
enddate=$(date -I --utc)
echo "Deleting old file"
rm -rf /afs/cern.ch/user/c/cmssst/www/siteReadiness/siteReadiness.txt
while [ "$d" != "$enddate" ]; do 
  echo "Starting $d"
  d=$(date -I --utc -d "$d + 1 day")
  echo $d > lastdate.txt
  python dailyMetric.py $d $OUT
  echo "Sleeping 30 minutes"
  cp $OUT/* /afs/cern.ch/user/c/cmssst/www/siteReadiness/
  #sleep 1200
done
