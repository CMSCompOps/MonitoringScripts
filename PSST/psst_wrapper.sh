#!/bin/bash

# ###################################
# Pilot Startup Site Test wrapper script
# ###################################

glidein_config="$1"
time_limit=300

timeout $time_limit ./psst.sh $glidein_config

exit_code=$?

site_name=`grep -m1 -i '^GLIDEIN_CMSSite' $glidein_config`

if [ $exit_code = 124 ];then
    echo "PSST reached time limit - ${time_limit} s"
    hostname | /usr/bin/Mail -s "PSST reached time limit - ${time_limit} s at ${site_name}" rokas.maciulaitis@cern.ch
    exit $exit_code
else
    exit $exit_code
fi