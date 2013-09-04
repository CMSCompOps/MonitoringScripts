#!/bin/bash

# by Luyckx S.


args=("$@")

filename=${args[0]}
voBox=${args[1]}

# check number of arguments
EXPECTED_ARGS=2
if [ $# -ne $EXPECTED_ARGS ];
then
    echo "Wrong number of arguments. Expecting $EXPECTED_ARGS arguments."
    exit 65
fi

voBox_in_file=$(cat $filename | grep "$voBox" | awk '{print $1}' )

#changing _ to . in filename
voBoxDots=$(echo $voBox|sed 's/_/./g')
uptimeArray=$( grep "$voBoxDots" $filename )  #array of [voBox uptimestatus]
   if [ "$uptimeArray" == "" ];
   then
      uptime='up'
   else
      echo $uptimeArray > upAr.tmp
      uptime=$( awk '{print $2}' upAr.tmp  )
      rm upAr.tmp
   fi

# will be picked up by python script
echo "output $uptime" 



