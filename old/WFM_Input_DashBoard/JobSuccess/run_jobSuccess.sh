#!/bin/sh
#
# Sten Luyckx
# Script in acrontab t1
# 5,20,35,50 * * * * lxplus ssh vocms202 /afs/cern.ch/user/c/cmst1/scratch0/WFM_Input_DashBoard/JobSuccess/run_jobSuccess.sh &> /dev/null
# Script for Dashboard metric 148, 149: Avg 24h grid/app proc jobSuccess  
# outputfile JobSuccess_app_proc_out.txt
# outputfile JobSuccess_grid_proc_out.txt
# outputdir /afs/cern.ch/user/c/cmst1/www/WFMon/

cd /afs/cern.ch/user/c/cmst1/scratch0/WFM_Input_DashBoard/JobSuccess

# Email if things are running slowly
if [ -f scriptRunning.run ];
then
   echo "bash run_JobSuccess.sh is already running. Will send an email to the admin."
   # script to send simple email
   # email subject
   SUBJECT="[Monitoring] Condor History load JobSuccess"
   # Email To ?
   EMAIL="sten.luyckx@cern.ch"
   # Email text/message
   if [ -f emailmessage.txt ];
   then
      rm emailmessage.txt
   fi
   touch emailmessage.txt
   EMAILMESSAGE="/tmp/emailmessage.txt"
   echo "Condor history, 24hjobs, is running to slowly. See: /afs/cern.ch/user/c/cmst1/scratch0/WFM_Input_DashBoard/JobSuccess"> $EMAILMESSAGE
   echo "/afs/cern.ch/user/c/cmst1/scratch0/WFM_Input_DashBoard/JobSuccess/" >>$EMAILMESSAGE
   # send an email using /bin/mail
   /bin/mail -s "$SUBJECT" "$EMAIL" < $EMAILMESSAGE

else
     echo "bash run_JobSuccess.sh started succesfully"
     touch scriptRunning.run
fi


#Run the script
txt1="JobSuccess_grid_proc_out.txt"
txt2="JobSuccess_app_proc_out.txt"
echo "python jobSuccess.py $txt1 $txt2"
python jobSuccess.py $txt1 $txt2 &> jobSuccess.log

problem="$?"
echo "problem: $problem"

cp $txt1 $txt2 /afs/cern.ch/user/c/cmst1/www/WFMon/
echo "files copied to: /afs/cern.ch/user/c/cmst1/www/WFMon/ "
rm scriptRunning.run
