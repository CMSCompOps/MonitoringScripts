#!/bin/bash

# go to the path that contain this script
cd $(dirname $(readlink -f "${BASH_SOURCE[0]}"))

source ../../init.sh

# URL of the GGUS xml interface
URL="https://ggus.eu/?mode=ticket_search&show_columns_check%5B%5D=TICKET_TYPE&show_columns_check%5B%5D=AFFECTED_VO&show_columns_check%5B%5D=AFFECTED_SITE&show_columns_check%5B%5D=CMS_SITE&show_columns_check$

# download the xml file
certFile=`/usr/bin/grid-proxy-info -path 2> /dev/null`
wgetOpt="--certificate=${certFile} --private-key=${certFile} --ca-certificate=${certFile}"
/usr/bin/wget ${wgetOpt} -O $TMP/xml_input.xml $URL

python phedex_version.py

cp output.txt /afs/cern.ch/user/c/cmssst/www/phedex_version