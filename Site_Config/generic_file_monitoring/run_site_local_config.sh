#!/bin/bash
# written by Gökhan Kandemir => gokhan.kandemir@cern.ch
# usercert and userkey files must be in folder .globus
# this script calculates the number of T1s and T2s counts and writes results to console and file.
clear
echo "To Prevent ask typing password constantly, Registering your KEY and CERT to Grid Environment"
source /afs/cern.ch/project/gd/LCG-share/new_3.2/etc/profile.d/grid_env.sh
voms-proxy-init -voms cms
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
txt="gfm"
echo "python site_local_config.py > $txt.txt and $txt.json"
python site_local_config.py $txt &> site_local_config.log

problem="$?"
echo "problem: $problem"
echo "The files were created succesfully."

cp $txt".txt" /afs/cern.ch/user/c/cmst1/www/SST
cp $txt".json"  /afs/cern.ch/user/c/cmst1/www/SST

rm scriptRunning.run

