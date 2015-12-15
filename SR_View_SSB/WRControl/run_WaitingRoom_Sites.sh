#!/bin/bash
location=$(dirname $(readlink -f "${BASH_SOURCE[0]}"))
outputdir="/afs/cern.ch/user/c/cmssst/www/others/"
outputdir2="/afs/cern.ch/user/c/cmssst/www/others/"

source $location/../../init.sh

cd $location

# Email if things are running slowly
if [ -f scriptRunning.run ];
then
   echo "run_WaitingRoom_Sites.sh is already running. Will send an email to the admin."
   # script to send simple email
   # email subject
   SUBJECT="[MonitoringScripts] WRControl running slowly."
   # Email To ?
   # Email text/message
   if [ -f emailmessage.txt ];
   then
      rm emailmessage.txt
   fi
   touch emailmessage.txt
   EMAILMESSAGE="/tmp/emailmessage.txt"
   echo "run_WaitingRoom_Sites.sh  is running slowly." > $EMAILMESSAGE
   echo $location >> $EMAILMESSAGE
   # send an email using /bin/mail
   /bin/mail -s "$SUBJECT" "$SSTMAIL" < $EMAILMESSAGE

else
     echo "bash run_WaitingRoom_Sites.sh started succesfully"
     touch scriptRunning.run
fi

#Run the script
txt="WaitingRoom_Sites.txt"
echo "python WaitingRoom_Sites.py $txt1"
python WaitingRoom_Sites.py $txt &> wr_log.txt
cat wr_log.txt

problem="$?"
echo "problems: $problem"

cp $txt $outputdir
cp wr_log.txt $outputdir2
echo "WaitingRoom_Sites.txt copied to: " $outputdir
rm scriptRunning.run
