#!/bin/bash

# go to the path that contains this script
cd $(dirname $(readlink -f "${BASH_SOURCE[0]}"))

source ../../init.sh

# output & temp directory for this script
OUT=$SSTBASE/output/metrics/aaa
TMP=$SSTBASE/tmp/metrics/aaa
DATA=$SSTBASE/data/metrics/aaa/

echo $DATA

if [ ! -d "$OUT" ]; then
    mkdir -p $OUT
fi

if [ ! -d "$TMP" ]; then
    mkdir -p $TMP
fi

# report url
reportURL="https://cmssst.web.cern.ch/cmssst/aaa/%s_report.html"

# federation source
federations="http://vocms037.cern.ch/fedinfo/federations.json"

# you just need to put host name into this SAM url
samURL="http://wlcg-sam-cms.cern.ch/dashboard/request.py/getTestResults?profile_name=CMS_CRITICAL&metrics=org.cms.WN-xrootd-access%20(/cms/Role_lcgadmin)&hostname={0}&flavours=CREAM-CE,OSG-CE,ARC-CE,SRMv2&time_range=last2Weeks"

# notice parameters in the following url
hcURL="http://dashb-cms-job.cern.ch/dashboard/request.py/jobsummary-plot-or-table?activity=hcxrootd&date1={0}&date2={1}&sortby=inputse&scale=linear&check=terminated"

downTimesURL="http://dashb-ssb.cern.ch/dashboard/request.py/getplotdata?columnid=121&time=24&dateFrom=&dateTo=&site=T0_CH_CERN&sites=all&clouds=undefined&batch=1"

# notice the ebedded time frame parameters
ggusEnd=`date +%d+%b+%Y`
ggusStart=$(date  --date="2 weeks ago" +%d+%b+%Y)
ggusURL="https://ggus.eu/?mode=ticket_search&show_columns_check%5B%5D=TICKET_TYPE&show_columns_check%5B%5D=AFFECTED_VO&show_columns_check%5B%5D=AFFECTED_SITE&show_columns_check%5B%5D=CMS_SITE&show_columns_check%5B%5D=PRIORITY&show_columns_check%5B%5D=RESPONSIBLE_UNIT&show_columns_check%5B%5D=CMS_SU&show_columns_check%5B%5D=STATUS&show_columns_check%5B%5D=DATE_OF_CHANGE&show_columns_check%5B%5D=TYPE_OF_PROBLEM&show_columns_check%5B%5D=SHORT_DESCRIPTION&ticket_id=&supportunit=&su_hierarchy=0&vo=cms&cms_su=&user=&keyword=&involvedsupporter=&assignedto=&affectedsite=&cms_site=&specattrib=none&status=open&priority=&typeofproblem=CMS_AAA+WAN+Access&ticket_category=all&mouarea=&date_type=creation+date&timeframe=lastweek&tf_radio=2&from_date=$ggusStart&to_date=$ggusEnd&untouched_date=&orderticketsby=REQUEST_ID&orderhow=desc&search_submit=GO%21&writeFormat=XML"

# download the xml file
certFile=`/usr/bin/grid-proxy-info -path 2> /dev/null`
wgetOpt="--certificate=${certFile} --private-key=${certFile} --ca-certificate=${certFile}"
/usr/bin/wget ${wgetOpt} -O $TMP/ggus.xml $ggusURL

python federations.py $federations $OUT/federations.txt
python aaa.py $TMP/ggus.xml $samURL $hcURL $downTimesURL $federations $TMP/report.json $reportURL $OUT
python report.py $TMP/report.json $DATA/template.html $OUT/report_2weeks.json $OUT

cp $OUT/* /afs/cern.ch/user/c/cmssst/www/aaa
