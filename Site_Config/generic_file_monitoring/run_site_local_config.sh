#!/bin/bash

#clear
#source /afs/cern.ch/project/gd/LCG-share/new_3.2/etc/profile.d/grid_env.sh
#voms-proxy-init -voms cms

# Email if things are running slowly

if [ -f scriptRunning.run ];
then
   echo "run_site_local_config.sh is already running. Will send an email to the admin."
   # script to send simple email
   # email subject
   SUBJECT="[TFC] load site-local-config"
   # Email To ?
   EMAIL="gokhan.kandemir@cern.ch"
   # Email text/message
   if [ -f emailmessage.txt ];
   then
      rm emailmessage.txt
   fi
   touch emailmessage.txt
   EMAILMESSAGE="/tmp/emailmessage.txt"
   echo "run_site_local_config.sh  is running to slowly."
   # send an email using /bin/mail
   /bin/mail -s "$SUBJECT" "$EMAIL" < $EMAILMESSAGE

else
     echo "bash run_site_local_config.sh succesfully"
     touch scriptRunning.run
fi


#Run the script
cd /afs/cern.ch/user/j/jartieda/MonitoringScripts/Site_Config/generic_file_monitoring
txt="gfm"
echo "python site_local_config.py > $txt.txt and $txt.json"

findText="statistics-destination"
python site_local_config.py $txt $findText &> site_local_config.log

problem="$?"
echo "problem: $problem"
echo "The files were created succesfully."

cp $txt".txt" /afs/cern.ch/user/c/cmst1/www/SST

rm scriptRunning.run