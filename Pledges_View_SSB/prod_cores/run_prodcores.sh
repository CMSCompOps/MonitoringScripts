#!/bin/bash
clear
location="/afs/cern.ch/user/c/cmst1/scratch0/MonitoringScripts/Pledges_View_SSB/prod_cores"
outputdir="/afs/cern.ch/user/c/cmst1/www/SST"
cd $location
# Email if things are running slowly
if [ -f scriptRunning.run ];
then
	echo "run_prodcores.sh is already running. Will send an email to the admin."
	# script to send simple email
	# email subject
	SUBJECT="Prod[Cores] running slowly"
	# Email To ?
	EMAIL="artiedaj@fnal.gov"
	# Email text/message
    if [ -f emailmessage.txt ];
    then
    	rm emailmessage.txt
    fi
    touch emailmessage.txt
    EMAILMESSAGE="/tmp/emailmessage.txt"
    echo "run_prodcores.sh is stuck!!"> $EMAILMESSAGE
    echo $location >>$EMAILMESSAGE
    # send an email using /bin/mail
    /bin/mail -s "$SUBJECT" "$EMAIL" < $EMAILMESSAGE
else
	echo "bash run_prodcores.sh started succesfully"
	touch scriptRunning.run
fi

#Run the script
txt="prod"
echo "python prodcores.py"
python2.6 prodcores.py &> prod.log

problem="$?"
echo "problem: $problem"
echo "The files were created succesfully."

cp $txt".txt"  $outputdir
cp $txt".json" $outputdir

rm scriptRunning.run