#!/bin/sh
location="/afs/cern.ch/user/c/cmst1/scratch0/MonitoringScripts/WFM_Input_DashBoard"
outputdir="/afs/cern.ch/user/c/cmst1/www/WFMon/"

#Initialize
source ~cmst1/.bashrc
agentenv
source /data/srv/wmagent/current/apps/wmagent/etc/profile.d/init.sh
cd $location

# Email if things are running slowly
if [ -f scriptRunning.run ];
then
   echo "bash runWFMonDB.sh is already running. Will send an email to the admin."
   # script to send simple email
   # email subject
   SUBJECT="[Monitoring] Condor History load"
   # Email To workflow team
   EMAIL="jbadillo@cern.ch"
   # Email text/message
   if [ -f emailmessage.txt ];
   then
      rm emailmessage.txt
   fi
   touch emailmessage.txt
   EMAILMESSAGE="/tmp/emailmessage.txt"
   echo "Condor history is running slowly." > $EMAILMESSAGE
   echo $location >>$EMAILMESSAGE
   # send an email using /bin/mail
   /bin/mail -s "$SUBJECT" "$EMAIL" < $EMAILMESSAGE

else
     echo "bash runWFMonDB.sh started succesfully"
     touch scriptRunning.run
fi

#Run the script
python WFMonDBShort.py &> WFMonDBcron.log

problem="$?"
echo "problem: $problem"

cp *.json $outputdir
cp *.txt $outputdir
cp WFMonDBcron_prevlog.log WFMonDBcron_prevlog2.log
cp WFMonDBcron.log WFMonDBcron_prevlog.log
rm scriptRunning.run