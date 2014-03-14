#!/bin/sh
Read="Readme:       https://cmsdoc.cern.ch/cms/LCG/SiteComm/MonitoringScripts/SR_View_SSB/ActiveSites/README.txt"
outFile="./WasCommissionedT2ForSiteMonitor.txt"
cat <<EOF > $outFile
# SSB:          metric 39 - Active T2s
# Criteria:     ActiveSite = SR>60% last 1 week OR last 3 months
# Written by:   John Artieda <artiedaj@fnal.gov>
# $Read
EOF

# Script in acrontab t1
# 00 08 * * 1 => Every monday at 8AM
# 00 08 * * 1 lxplus ssh vocms202 /afs/cern.ch/user/c/cmst1/scratch0/MonitoringScripts/SR_View_SSB/ActiveSites/sActiveSites.sh &> /dev/null
cd /afs/cern.ch/user/c/cmst1/scratch0/MonitoringScripts/SR_View_SSB/ActiveSites/

# Fixing access
echo "exporting KEY and CERT"
export X509_USER_CERT=/data/certs/servicecert.pem
export X509_USER_KEY=/data/certs/servicekey.pem

# Email if script is stuck
if [ -f scriptRunning.run ];
then
    echo "sActiveSites.sh is stuck. Email is being sent to the admin."
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
    echo "previous bash sActiveSites.sh run succesfully"
    touch scriptRunning.run
fi

# Appending Sites that can't be calculated with the python script (disk and T3s)
ActiveSitesList="
T0_CH_CERN
T1_CH_CERN
T1_DE_KIT_Disk
T1_FR_CCIN2P3_Disk
T1_RU_JINR_Disk
T1_UK_RAL_Disk
T1_US_FNAL_Disk
T3_US_Colorado
T3_US_Omaha
"
# creating output in the SSB feed format
echo "T1 Disks and Used T3s added to the list:"
timestamp=`date +"%Y-%m-%d %H:%M:%S"`
for site in $ActiveSitesList
do
  echo -e $timestamp'\t'${site}'\t'1'\t'"green"'\t'"n/a" >> $outFile
  echo ${site}
done

#Run the python script
python ActiveSites.py &> ActiveSites.log
cat ActiveSites.log
# checking if any errors occurred
if [ $? = 0 ]
then
    echo "ActiveSites.py completed"
else
    echo "problem running the python script"
fi

# creating a copy of the previous fed to SSB as .OLD file
cp /afs/cern.ch/cms/LCG/SiteComm/T2WaitingList/WasCommissionedT2ForSiteMonitor.txt /afs/cern.ch/cms/LCG/SiteComm/T2WaitingList/WasCommissionedT2ForSiteMonitor.txt.OLD
if [ $? = 0 ]
then
    echo "previous fed to SSB copied as .OLD file"
else
    echo "problem copying previous fed to SSB as .OLD file"
fi
# copying output to web location to feed SSB
cp $outFile /afs/cern.ch/cms/LCG/SiteComm/T2WaitingList/WasCommissionedT2ForSiteMonitor.txt
# checking if any errors occurred
if [ $? = 0 ]
then
    echo "new file copied to web location to feed SSB"
    echo "SCRIPT COMPLETED SUCCESFULLY"
    echo "Email is being sent to the admin."
    # email subject
    SUBJECT="[MonitoringScripts] sActiveSites.sh completed successfully!"
    # Email To ?
    EMAIL="artiedaj@fnal.gov"
    # Email text/message
    if [ -f emailmessage.txt ];
    then
        rm emailmessage.txt
    fi
    touch emailmessage.txt
    EMAILMESSAGE="/tmp/emailmessage.txt"
    echo "sActiveSites.sh  completed successfully!"> $EMAILMESSAGE
    echo $Read >>$EMAILMESSAGE
    # send an email using /bin/mail
    /bin/mail -s "$SUBJECT" "$EMAIL" < $EMAILMESSAGE
else
    echo "problem copying output to web location to feed SSB"
fi

rm scriptRunning.run