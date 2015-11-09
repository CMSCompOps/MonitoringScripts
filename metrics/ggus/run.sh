#!/bin/bash

# go to the path that contain this script
cd $(dirname $(readlink -f "${BASH_SOURCE[0]}"))

source ../../init.sh

# output & temp directory for this script
OUT=$SSTBASE/output/metrics/ggus
TMP=$SSTBASE/tmp/metrics/ggus

if [ ! -d "$OUT" ]; then
    mkdir -p $OUT
fi

if [ ! -d "$TMP" ]; then
    mkdir -p $TMP
fi

# URL of the GGUS xml interface
URL="https://ggus.eu/?mode=ticket_search&show_columns_check%5B%5D=TICKET_TYPE&show_columns_check%5B%5D=AFFECTED_VO&show_columns_check%5B%5D=AFFECTED_SITE&show_columns_check%5B%5D=CMS_SITE&show_columns_check%5B%5D=PRIORITY&show_columns_check%5B%5D=RESPONSIBLE_UNIT&show_columns_check%5B%5D=CMS_SU&show_columns_check%5B%5D=STATUS&show_columns_check%5B%5D=DATE_OF_CHANGE&show_columns_check%5B%5D=SHORT_DESCRIPTION&ticket_id=&supportunit=&su_hierarchy=0&vo=cms&cms_su=&user=&keyword=&involvedsupporter=&assignedto=&affectedsite=&cms_site=&specattrib=none&status=open&priority=&typeofproblem=all&ticket_category=all&mouarea=&date_type=creation+date&tf_radio=1&timeframe=any&from_date=17+Feb+2015&to_date=18+Feb+2015&untouched_date=&orderticketsby=REQUEST_ID&orderhow=desc&search_submit=GO%21&writeFormat=XML"

# download the xml file
certFile=`/usr/bin/grid-proxy-info -path 2> /dev/null`
wgetOpt="--certificate=${certFile} --private-key=${certFile} --ca-certificate=${certFile}"
/usr/bin/wget ${wgetOpt} -O $TMP/xml_input.xml $URL

# parse the xml file and generate output files
python ggus.py $TMP/xml_input.xml $OUT/ggusticketmeeting.txt $OUT/ggusticketmetrics.txt

cp $OUT/* /afs/cern.ch/user/c/cmssst/www/ggus
