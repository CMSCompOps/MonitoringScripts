#!/bin/bash
#
# Pilot Startup Site Test wrapper script


glidein_config="$1"
time_limit=300
email_addr="rokas.maciulaitis@cern.ch"

my_tar_dir=`grep -m1 -i '^GLIDECLIENT_CMS_PSST' $glidein_config | awk '{print $2}'`

timeout $time_limit ${my_tar_dir}/psst.sh $glidein_config

exit_code=$?

if [ "$exit_code" -ge 124 -a "$exit_code" -le 137 ];then
  echo "PSST reached time limit - ${time_limit} s"
  site_name=`grep -m1 -i '^GLIDEIN_CMSSite' $glidein_config | awk '{print $2}'`
  hostname | /usr/bin/Mail -s "PSST reached time limit - ${time_limit} s at ${site_name}" $email_addr
  exit 0
else
  exit $exit_code
fi
