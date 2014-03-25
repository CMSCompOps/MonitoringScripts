#!/bin/sh
#
# Sten Luyckx
# Script in acrontab t1
# 5,20,35,50 * * * * lxplus ssh vocms202 /afs/cern.ch/user/c/cmst1/scratch0/WFM_Input_DashBoard/WFMperVOBox/runWFMonDBShort_voboxes.sh &> /dev/null
# json files are fetched by Dashboardteam, via a special way. Cant be changed by myself
# Script for Dashboard metric (part of) 137, 138: Running/Pending jobs . This metric is shared with that of the # on site instead of on per schedular/vobox
# outputfile SSBCERN_voBoxInfo.json
# outputfile SSBFNAL_voBoxInfo.json / empty at the moment
# outputdir /afs/cern.ch/user/c/cmst1/www/WFMon/


#Initialize
source ~cmst1/.bashrc
agentenv
source /data/srv/wmagent/current/apps/wmagent/etc/profile.d/init.sh
cd /afs/cern.ch/user/c/cmst1/scratch0/WFM_Input_DashBoard/WFMperVOBox

# Email if things are running slowly
if [ -f scriptRunning.run ];
then
   echo "bash runWFMonDB.sh is already running. Will send an email to the admin."
   # script to send simple email
   # email subject
   SUBJECT="[Monitoring] Condor History load"
   # Email To ?
   EMAIL="sten.luyckx@cern.ch"
   # Email text/message
   if [ -f emailmessage.txt ];
   then
      rm emailmessage.txt
   fi
   touch emailmessage.txt
   EMAILMESSAGE="/tmp/emailmessage.txt"
   echo "Condor history is running to slowly. See: /afs/cern.ch/user/c/cmst1/scratch0/WFM_Input_DashBoard/WFMperVOBox"> $EMAILMESSAGE
   echo "https://cmst1.web.cern.ch/CMST1/WFMon/" >>$EMAILMESSAGE
   # send an email using /bin/mail
   /bin/mail -s "$SUBJECT" "$EMAIL" < $EMAILMESSAGE

else
     echo "bash runWFMonDB.sh started succesfully"
     touch scriptRunning.run
fi

#Run the script
python WFMvoBoxDBShort_voboxes.py &> /afs/cern.ch/user/c/cmst1/scratch0/WFM_Input_DashBoard/WFMperVOBox/WFMonDBcron.log

problem="$?"
echo "problem: $problem"

cp SSBCERN_voBoxInfo.json /afs/cern.ch/user/c/cmst1/www/WFMon/
cp SSBFNAL_voBoxInfo.json /afs/cern.ch/user/c/cmst1/www/WFMon/

rm scriptRunning.run

