#!/bin/bash
# Script in acrontab t1
# Script for Dashboard metric 153
# outputfile WaitingRoom_1MonthSum.txt
# outputfile WaitingRoom_2MonthSum.txt
# outputfile WaitingRoom_3MonthSum.txt
# usercert and userkey files must be in folder "data"
# this script read all of data from http://dashb-ssb.cern.ch/dashboard/ according to column, dateFrom, dateTo, sites and it calculates How many days Sites are in WaitingRoom as last 1 month, last 2 months, last 3 months. 
clear
echo "exporting KEY and CERT"

#fixing access
export X509_USER_CERT=./data/usercert.pem
export X509_USER_KEY=./data/userkey.pem

# Email if things are running slowly

if [ -f scriptRunning.run ];
then
   echo "run_WaitingRoom_SumMetrics.sh is already running. Will send an email to the admin."
   # script to send simple email
   # email subject
   SUBJECT="[Monitoring] load WaitingRoom sites (sums)"
   # Email To ?
   EMAIL="gokhan.kandemir@cern.ch"
   # Email text/message
   if [ -f emailmessage.txt ];
   then
      rm emailmessage.txt
   fi
   touch emailmessage.txt
   EMAILMESSAGE="/tmp/emailmessage.txt"
   echo "run_WaitingRoom_SumMetrics.sh  is running to slowly. See: /afs/cern.ch//user/g/gkandemi/Desktop/CMS_Work/wRDashBoard/Waitingroom_Dashboard/Waitingroom_SummedMetric/"> $EMAILMESSAGE
   echo "/afs/cern.ch/user/g/gkandemi/Desktop/CMS_Work/wRDashBoard/Waitingroom_Dashboard/Waitingroom_SummedMetric/" >>$EMAILMESSAGE
   # send an email using /bin/mail
   /bin/mail -s "$SUBJECT" "$EMAIL" < $EMAILMESSAGE

else
     echo "bash run_WaitingRoom_SumMetrics.sh succesfully"
     touch scriptRunning.run
fi


#Run the script
txt="WaitingRoom_"  #postfix in code itself
echo "python waitingRoom_SummedMetrics.py $txt1"
python WaitingRoom_SummedMetrics.py $txt &> sites_WaitingRoom_SummedMetrics.log
cat sites_WaitingRoom_SummedMetrics.log

problem="$?"
echo "problem: $problem"

#cp $txt*.txt /afs/cern.ch/user/g/gkandemi/www/WFMon/
cp $txt.txt ./
echo "files copied to: Script Directory "
rm scriptRunning.run

