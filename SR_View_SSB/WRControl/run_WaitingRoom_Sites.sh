#!/bin/bash

cd /afs/cern.ch/user/c/cmst1/scratch0/Waitingroom_Dashboard

echo "exporting KEY and CERT"

#fixing access
export X509_USER_CERT=/data/certs/servicecert.pem
export X509_USER_KEY=/data/certs/servicekey.pem


# Email if things are running slowly
if [ -f scriptRunning.run ];
then
   echo "run_WaitingRoom_Sites.sh is already running. Will send an email to the admin."
   # script to send simple email
   # email subject
   SUBJECT="[MonitoringScripts] WRControl running slow"
   # Email To ?
   EMAIL="artiedaj@fnal.gov"
   # Email text/message
   if [ -f emailmessage.txt ];
   then
      rm emailmessage.txt
   fi
   touch emailmessage.txt
   EMAILMESSAGE="/tmp/emailmessage.txt"
   echo "run_WaitingRoom_Sites.sh  is running to slowly. See: /afs/cern.ch/user/c/cmst1/scratch0/Waitingroom_Dashboard/"> $EMAILMESSAGE
   echo "/afs/cern.ch/user/c/cmst1/scratch0/Waitingroom_Dashboard/" >>$EMAILMESSAGE
   # send an email using /bin/mail
   /bin/mail -s "$SUBJECT" "$EMAIL" < $EMAILMESSAGE

else
     echo "bash run_WaitingRoom_Sites.sh succesfully"
     touch scriptRunning.run
fi


#Run the script
txt="WaitingRoom_Sites.txt"
echo "python WaitingRoom_Sites.py $txt1"
python WaitingRoom_Sites.py $txt &> sites_WaitingRoom.log
cat sites_WaitingRoom.log

problem="$?"
echo "problem: $problem"

cp $txt /afs/cern.ch/user/c/cmst1/www/WFMon/
echo "WaitingRoom_Sites.txt copied to: /afs/cern.ch/user/c/cmst1/www/WFMon/ "
rm scriptRunning.run