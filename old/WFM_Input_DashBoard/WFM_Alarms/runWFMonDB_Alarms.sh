#!/bin/sh
#
# Sten Luyckx
# Script in acrontab t1
# 0,15,30,45 * * * * vocms174 /afs/cern.ch/user/c/cmst1/scratch0/WFM_Input_DashBoard/WFM_Alarms/runWFMonDB_Alarms.sh  &> /dev/null
# This script is a bit slow 10-14min runtime
# json files are fetched by Dashboardteam, via a special way. Cant be changed by myself
# Script for Dashboard metric : 141, 142, 143, 144 :  GlideIn, 8h, Instant, 24h alarms  
# outputfile SSB_alarms.json 
# outputdir /afs/cern.ch/user/c/cmst1/www/WFMon/


#Initialize
cd /afs/cern.ch/user/c/cmst1/scratch0/WFM_Input_DashBoard/WFM_Alarms_python 

# Email if things are running slowly
if [ -f scriptRunning.run ];
then
   echo "bash runWFMonDB.sh is already running. Will send an email to the admin."
   # script to send simple email
   # email subject
   SUBJECT="[Monitoring] Condor History load"
   # Email To ?
   #EMAIL="sten.luyckx@cern.ch"
   EMAIL="xavier.janssen@cern.ch" 
   # Email text/message
   if [ -f emailmessage.txt ];
   then
      rm emailmessage.txt
   fi
   touch emailmessage.txt
   EMAILMESSAGE="/tmp/emailmessage.txt"
   echo "The alarmscript is running slowly See: /afs/cern.ch/user/c/cmst1/scratch0/WFM_Input_DashBoard/WFM_Alarms_python"> $EMAILMESSAGE
   echo "https://cmst1.web.cern.ch/CMST1/WFMon/" >>$EMAILMESSAGE
   # send an email using /bin/mail
   /bin/mail -s "$SUBJECT" "$EMAIL" < $EMAILMESSAGE
   #exit
else
     echo "bash runWFMonDB.sh started succesfully"
     touch scriptRunning.run
fi

#Run the script
python26 make_WFMalarms.py &> WFMonDB_alarms_cron.log

problem="$?"
echo "problem: $problem"

#cp SSB_alarms.json /afs/cern.ch/user/c/cmst1/www/WFMon/
cp WFMonDB_alarms_cron.log  WFMonDB_alarms_cron_prevlog.log
rm scriptRunning.run
