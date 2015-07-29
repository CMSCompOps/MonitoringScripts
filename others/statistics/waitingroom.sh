#!/bin/bash

# go to the path that contains this script
cd $(dirname $(readlink -f "${BASH_SOURCE[0]}"))

source ../../init.sh

wrStart=$(date  --date="1 year ago" +%Y-%m-%d)
wrEnd=`date +%Y-%m-%d`
url="http://dashb-ssb.cern.ch/dashboard/request.py/getplotdata?columnid=153&time=custom&dateFrom=$wrStart&dateTo=$wrEnd&sites=all&clouds=undefined&batch=1"
python waitingroom.py $url
