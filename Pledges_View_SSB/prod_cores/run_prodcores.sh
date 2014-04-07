#!/bin/bash
clear
location="/afs/cern.ch/user/j/jartieda/MonitoringScripts/Pledges_View_SSB/prod_cores"
cd $location
# Email if things are running slowly
if [ -f scriptRunning.run ];
then
   echo "run_prodcores.sh is already running. Will send an email to the admin."
   # script to send simple email
   # email subject
   SUBJECT="[Prod[Cores]] load Prod[Cores]"
   # Email To ?
   EMAIL="artiedaj@fnal.gov, gokhan.kandemir@cern.ch"
   # Email text/message
   if [ -f emailmessage.txt ];
   then
      rm emailmessage.txt
   fi
   touch emailmessage.txt
   EMAILMESSAGE="/tmp/emailmessage.txt"
   echo "run_prodcores.sh  is running to slowly."
   # send an email using /bin/mail
   /bin/mail -s "$SUBJECT" "$EMAIL" < $EMAILMESSAGE

else
     echo "bash run_prodcores.sh succesfully"
     touch scriptRunning.run
fi


#Run the script
txt="prod"
echo "python prodcores.py"
python2.6 prodcores.py &> prod.log

problem="$?"
echo "problem: $problem"
echo "The files were created succesfully."

cp $txt".txt"  /afs/cern.ch/user/c/cmst1/www/SST
cp $txt".json"  /afs/cern.ch/user/c/cmst1/www/SST

rm scriptRunning.run
