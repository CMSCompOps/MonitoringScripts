#!/bin/bash
# written by John Artieda

# set up a proxy to read site config files
#clear
#source /afs/cern.ch/project/gd/LCG-share/new_3.2/etc/profile.d/grid_env.sh
#voms-proxy-init -voms cms

# Email if things are running slowly
if [ -f scriptRunning.run ];
then
   echo "run_site_local_config.sh is already running. Will send an email to the admin."
   # script to send simple email
   # email subject
   SUBJECT="[TFC] load site-local-config"
   # Email To ?
   EMAIL="cms-comp-ops-site-support-team@cern.ch"
   # Email text/message
   if [ -f emailmessage.txt ];
   then
      rm emailmessage.txt
   fi
   touch emailmessage.txt
   echo "run_site_local_config.sh  is running to slowly." > emailmessage.txt
   # send an email using /bin/mail
   /bin/mail -s "$SUBJECT" "$EMAIL" < emailmessage.txt
else
     echo "bash run_site_local_config.sh succesfully"
     touch scriptRunning.run
fi

#Run the script
path="/afs/cern.ch/user/j/jartieda/MonitoringScripts/Site_Config/generic_file_monitoring"
txt=$path"/gfm"
findText="statistics-destination"

echo "python site_local_config.py > $txt.txt and $txt.json"
python $path"/"site_local_config.py $txt $findText &> $path"/"site_local_config.log

problem="$?"
echo "problem: $problem"
echo "The files were created succesfully."

cp $txt".txt" /afs/cern.ch/user/c/cmst1/www/SST

rm scriptRunning.run