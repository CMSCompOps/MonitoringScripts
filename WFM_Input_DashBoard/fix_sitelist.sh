#!/bin/bash

# by Luyckx S.

# This code is called by the python script. Do not call this function yourself.
# this code will add all sites to a text file 

site_list=$1

# fetching site list from: http://cmst1.web.cern.ch/CMST1/wmaconfig/slot-limits.conf
cp /afs/cern.ch/user/c/cmst1/www/wmaconfig/slot-limits.conf site_slot_limit_0.txt

if [ ! -s site_slot_limit_0.txt ];
then
    echo "Fetching slot-limits.conf has failed."
    exit
fi
awk '{print $1}' site_slot_limit_0.txt > $site_list
rm site_slot_limit_0.txt
