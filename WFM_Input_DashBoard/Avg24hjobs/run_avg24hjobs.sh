#!/bin/sh
#
# Sten Luyckx
# Script in acrontab t1
# 5,20,35,50 * * * * lxplus ssh vocms202 /afs/cern.ch/user/c/cmst1/scratch0/WFM_Input_DashBoard/Avg24hjobs/run_avg24hjobs.sh &> /dev/null
# Script for Dashboard metric : 146, 147 : Avg 24h Pending/Running jobs 
# outputfile avg24hjobs_running.txt
# outputfile avg24hjobs_pending.txt
# outputdir /afs/cern.ch/user/c/cmst1/www/WFMon/

cd /afs/cern.ch/user/c/cmst1/scratch0/WFM_Input_DashBoard/Avg24hjobs

# Email if things are running slowly
if [ -f scriptRunning.run ];
then
   echo "bash run_avg24hjobs.sh is already running. Will send an email to the admin."
   # script to send simple email
   # email subject
   SUBJECT="[Monitoring] Condor History load avg24hjobs"
   # Email To ?
   EMAIL="sten.luyckx@cern.ch"
   # Email text/message
   if [ -f emailmessage.txt ];
   then
      rm emailmessage.txt
   fi
   touch emailmessage.txt
   EMAILMESSAGE="/tmp/emailmessage.txt"
   echo "Condor history, 24hjobs, is running to slowly. See: /afs/cern.ch/user/c/cmst1/scratch0/WFM_Input_DashBoard/Avg24hjobs"> $EMAILMESSAGE
   echo "/afs/cern.ch/user/c/cmst1/scratch0/WFM_Input_DashBoard/Avg24hjobs/" >>$EMAILMESSAGE
   # send an email using /bin/mail
   /bin/mail -s "$SUBJECT" "$EMAIL" < $EMAILMESSAGE

else
     echo "bash run_avg24hjobs.sh started succesfully"
     touch scriptRunning.run
fi


#Run the script
txt_running="avg24hjobs_running.txt"
txt_pending="avg24hjobs_pending.txt"
echo "python avg24hjobs.py $txt_running $txt_pending"
python avg24hjobs.py $txt_running $txt_pending &> avg24hjobs.log

problem="$?"
echo "problem: $problem"

cp $txt_running $txt_pending /afs/cern.ch/user/c/cmst1/www/WFMon/
echo "files copied to: /afs/cern.ch/user/c/cmst1/www/WFMon/ "
rm scriptRunning.run
