#!/bin/sh

# Script and files location
location="/afs/cern.ch/user/c/cmst1/scratch0/MonitoringScripts/SR_View_SSB/ActiveSites"
githublocation="https://raw.github.com/CMSCompOps/MonitoringScripts/master/SR_View_SSB/ActiveSites/"
outFile="./WasCommissionedT2ForSiteMonitor.txt"
ssbfeed="/afs/cern.ch/cms/LCG/SiteComm/T2WaitingList/WasCommissionedT2ForSiteMonitor.txt"
ssbfeedweb="https://cmsdoc.cern.ch/cms/LCG/SiteComm/T2WaitingList/WasCommissionedT2ForSiteMonitor.txt"
Read="https://raw.githubusercontent.com/CMSCompOps/MonitoringScripts/master/SR_View_SSB/ActiveSites/Readme.txt"

echo "*** sActiveSites.sh SCRIPT STARTED ***"
cd $location

# Email if script is stuck
if [ -f scriptRunning.run ];
then
    echo "** sActiveSites.sh is stuck. Email is being sent to the admin."
    # email subject
    SUBJECT="[MonitoringScripts] sActiveSites.sh is stuck!!"
    # Email To ?
    EMAIL="artiedaj@fnal.gov"
    # Email text/message
    if [ -f emailmessage.txt ];
    then
        rm emailmessage.txt
    fi
    touch emailmessage.txt
    EMAILMESSAGE="/tmp/emailmessage.txt"
    echo "sActiveSites.sh is stuck!!"> $EMAILMESSAGE
    echo $Read >>$EMAILMESSAGE
    # send an email using /bin/mail
    /bin/mail -s "$SUBJECT" "$EMAIL" < $EMAILMESSAGE
else
    echo "* previous bash sActiveSites.sh ran succesfully"
    touch scriptRunning.run
fi

# updating files from github
# echo "* updating ActiveSites.py script from github"
# curl $githublocation/ActiveSites.py > ActiveSites.py
# echo "* updating README file from github"
# curl $githublocation/README.txt > README.txt

# creating output file
cat <<EOF > $outFile
# SSB:          metric 39 - Active T2s
# Criteria:     ActiveSite = SR>=80% last 1 week OR last 3 months
# Written by:   John Artieda <artiedaj@fnal.gov>
# Readme:
# $Read
EOF

# Appending Sites that are not included in the python script feeder (IMPORTANT: do not include T1s or T3s)
ActiveSitesList="
T2_CH_CERN
T2_CH_CERN_AI
T2_CH_CERN_HLT
"

# creating output in the SSB feed format
echo "* Appended sites that are not included in the python script feeder:"
timestamp=`date +"%Y-%m-%d %H:%M:%S"`
for site in $ActiveSitesList
do
  echo -e $timestamp'\t'${site}'\t'1'\t'"green"'\t'$ssbfeedweb >> $outFile
  echo ${site}
done

#Run the python script
python2.6 ActiveSites.py &> ActiveSites.log
cat ActiveSites.log
# checking if any errors occurred
if [ $? = 0 ]
then
    echo "* ActiveSites.py completed"
else
    echo "** problem running the python script"
fi

# creating a copy of the previous fed to SSB as .OLD file
cp $ssbfeed $ssbfeed.OLD
if [ $? = 0 ]
then
    echo "* previous fed to SSB copied as .OLD file"
else
    echo "** problem copying previous fed to SSB as .OLD file"
fi
# copying output to web location to feed SSB
cp $outFile $ssbfeed

# checking if any errors occurred
if [ $? = 0 ]
then
    echo "* new file copied to web location to feed SSB"
    echo "*** sActiveSites.sh SCRIPT COMPLETED SUCCESFULLY ***"
    # email subject
    SUBJECT="[MonitoringScripts] sActiveSites.sh completed successfully: WR List updated!"
    # Email To ?
    EMAIL="artiedaj@fnal.gov, ali.mehmet.altundag@cern.ch"
    # Email text/message
    if [ -f emailmessage.txt ];
    then
        rm emailmessage.txt
    fi
    touch emailmessage.txt
    EMAILMESSAGE="/tmp/emailmessage.txt"
    echo "sActiveSites.sh completed successfully: WR List updated!"> $EMAILMESSAGE
    echo $ssbfeedweb >>$EMAILMESSAGE
    echo $Read >>$EMAILMESSAGE
    # send an email using /bin/mail
    /bin/mail -s "$SUBJECT" "$EMAIL" < $EMAILMESSAGE
else
    echo "** problem copying output to web location to feed SSB"
fi

rm scriptRunning.run
