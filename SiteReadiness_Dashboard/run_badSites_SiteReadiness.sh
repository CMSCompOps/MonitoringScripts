#!/bin/sh
#
# Sten Luyckx
# Script in acrontab t1
# 5,20,35,50 * * * * lxplus ssh vocms202 /afs/cern.ch/user/c/cmst1/scratch0/SiteReadiness_Dashboard/run_badSites_SiteReadiness.sh &> /dev/null 
# Script for Dashboard metric 152: SiteReadiness 1W&3M (>60%) 
# outputfile BadSites_SiteReadiness.txt
# outputdir /afs/cern.ch/user/c/cmst1/www/WFMon/


cd /afs/cern.ch/user/c/cmst1/scratch0/SiteReadiness_Dashboard

# Email if things are running slowly
if [ -f scriptRunning.run ];
then
   echo "bash run_badSites_SiteReadiness.sh is already running. Will send an email to the admin."
   # script to send simple email
   # email subject
   SUBJECT="[Monitoring] load SiteReadiness of sites"
   # Email To ?
   EMAIL="sten.luyckx@cern.ch"
   # Email text/message
   if [ -f emailmessage.txt ];
   then
      rm emailmessage.txt
   fi
   touch emailmessage.txt
   EMAILMESSAGE="/tmp/emailmessage.txt"
   echo "Run_badSites_SiteReadiness.sh  is running to slowly. See: /afs/cern.ch/user/c/cmst1/scratch0/SiteReadiness_Dashboard"> $EMAILMESSAGE
   echo "/afs/cern.ch/user/c/cmst1/scratch0/SiteReadiness_Dashboard" >>$EMAILMESSAGE
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

cp $txt /afs/cern.ch/user/c/cmst1/www/WFMon/
echo "files copied to: /afs/cern.ch/user/c/cmst1/www/WFMon/ "
rm scriptRunning.run

