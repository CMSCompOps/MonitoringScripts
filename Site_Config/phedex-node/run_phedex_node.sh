#!/bin/bash
# written by John Artieda

# set up a proxy to read site config files
#clear
#source /afs/cern.ch/project/gd/LCG-share/new_3.2/etc/profile.d/grid_env.sh
#voms-proxy-init -voms cms

# Email if things are running slowly
if [ -f scriptRunning.run ];
then
   echo "run_phedex_node.sh is already running. Will send an email to the admin."
   # script to send simple email
   # email subject
   SUBJECT="[TFC] load phedex_node"
   # Email To ?
   EMAIL="cms-comp-ops-site-support-team@cern.ch"
   # Email text/message
   if [ -f emailmessage.txt ];
   then
      rm emailmessage.txt
   fi
   touch emailmessage.txt
   EMAILMESSAGE="/tmp/emailmessage.txt"
   echo "run_phedex_node.sh  is running slowly."
   # send an email using /bin/mail
   /bin/mail -s "$SUBJECT" "$EMAIL" < $EMAILMESSAGE
else
     echo "bash run_phedex_node.sh completed succesfully"
     touch scriptRunning.run
fi

#Run the script
cd /afs/cern.ch/user/c/cmst1/scratch0/MonitoringScripts/Site_Config/phedex-node
txt="phedex_node"
echo "python phedex_node.py > $txt.txt and $txt.json"

findText="phedex-node"
python phedex_node.py $txt $findText &> phedex_node.log

problem="$?"
echo "problem: $problem"
echo "The files were created succesfully."

cp $txt".txt" /afs/cern.ch/user/c/cmst1/www/SST/

rm scriptRunning.run