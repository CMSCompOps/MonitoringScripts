#!/bin/sh
location="/afs/cern.ch/user/c/cmst1/scratch0/MonitoringScripts/SR_View_SSB/WRCriteria/"
outputdir="/afs/cern.ch/user/c/cmst1/www/WFMon/"
cd $location

# Email if things are running slowly
if [ -f scriptRunning.run ];
then
   echo "bash run_badSites_SiteReadiness.sh is already running. Will send an email to the admin."
   # script to send simple email
   # email subject
   SUBJECT="[MonitoringScripts] WRCriteria is running slowly"
   # Email To ?
   EMAIL="artiedaj@fnal.gov"
   # Email text/message
   if [ -f emailmessage.txt ];
   then
      rm emailmessage.txt
   fi
   touch emailmessage.txt
   EMAILMESSAGE="/tmp/emailmessage.txt"
   echo "Run_badSites_SiteReadiness.sh  is running slowly."> $EMAILMESSAGE
   echo $location >>$EMAILMESSAGE
   # send an email using /bin/mail
   /bin/mail -s "$SUBJECT" "$EMAIL" < $EMAILMESSAGE

else
     echo "bash Run_badSites_SiteReadiness.sh started succesfully"
     touch scriptRunning.run
fi

#Run the script
txt="BadSites_SiteReadiness.txt"
echo "python badsites_SiteReadiness.py $txt1"
python badsites_SiteReadiness.py $txt &> badSites_SiteReadiness.log


problem="$?"
echo "problem: $problem"

cp $txt $outputdir
echo "BadSites_SiteReadiness.txt copied to: " $outputdir
rm scriptRunning.run