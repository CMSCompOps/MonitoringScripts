#!/bin/bash
# Sten Luyckx
# Script for Dashboard metric 154, 155, 156

cd /afs/cern.ch/user/c/cmst1/scratch0/Waitingroom_Dashboard/Waitingroom_SummedMetric/

echo "exporting KEY and CERT"

#fixing access
export X509_USER_CERT=/data/certs/servicecert.pem
export X509_USER_KEY=/data/certs/servicekey.pem


# Email if things are running slowly

if [ -f scriptRunning.run ];
then
   echo "run_WaitingRoom_SumMetrics.sh is already running. Will send an email to the admin."
   # script to send simple email
   # email subject
   SUBJECT="[Monitoring] load WaitingRoom sites (sums)"
   # Email To ?
   EMAIL="sten.luyckx@cern.ch"
   # Email text/message
   if [ -f emailmessage.txt ];
   then
      rm emailmessage.txt
   fi
   touch emailmessage.txt
   EMAILMESSAGE="/tmp/emailmessage.txt"
   echo "run_WaitingRoom_SumMetrics.sh  is running to slowly. See: /afs/cern.ch/user/c/cmst1/scratch0/Waitingroom_Dashboard/Waitingroom_SummedMetric/"> $EMAILMESSAGE
   echo "/afs/cern.ch/user/c/cmst1/scratch0/Waitingroom_Dashboard/Waitingroom_SummedMetric/" >>$EMAILMESSAGE
   # send an email using /bin/mail
   /bin/mail -s "$SUBJECT" "$EMAIL" < $EMAILMESSAGE

else
     echo "bash run_WaitingRoom_SumMetrics.sh succesfully"
     touch scriptRunning.run
fi


#Run the script
txt="WaitingRoom_"  #postfix in code itself
echo "python waitingRoom_SummedMetrics.py $txt1"
python waitingRoom_SummedMetrics.py $txt &> sites_WaitingRoom_SummedMetrics.log
cat sites_WaitingRoom_SummedMetrics.log

problem="$?"
echo "problem: $problem"

cp $txt*.txt /afs/cern.ch/user/c/cmst1/www/WFMon/
echo "files copied to: /afs/cern.ch/user/c/cmst1/www/WFMon/ "
rm scriptRunning.run

