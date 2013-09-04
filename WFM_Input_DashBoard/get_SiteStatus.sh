#!/bin/bash

# by Luyckx S.

# this code will write information to the database and is called by the python script. (Python on vocms201 only has v 1.1.7, while in bash we have v3

args=("$@")

filename=${args[0]}
site=${args[1]}

# check number of arguments
EXPECTED_ARGS=2
if [ $# -ne $EXPECTED_ARGS ];
then
    echo "Wrong number of arguments. Expecting $EXPECTED_ARGS arguments."
    exit 65
fi

site_in_file=$(cat $filename | grep "$site" | awk '{print $1}' )


uptimeArray=$( grep "$site " $filename )  #array of [site pledge uptimestatus]
   if [ "$uptimeArray" == "" ];
   then
      pledge='0'
      s_status='on'
   else
      echo $uptimeArray > upAr.tmp
      pledge=$( awk '{print $2}' upAr.tmp  )
      s_status=$( awk '{print $3}' upAr.tmp  )
      rm upAr.tmp
   fi

#if [ "$site_in_file" != "$site" ];
#   then
#      echo "the site is not included in the textfile: $filename"
#      exit
#fi

#pledge=$(cat $filename | grep "$site" | awk '{print $2}' )
#s_status=$(cat $filename | grep "$site" | awk '{print $3}')

# check if s_status is empty. If this is true, the status is "on"
if [ -z "$s_status" ]; then
    s_status="on"
fi

# will be picked up by python script
echo "output $pledge $s_status" 



