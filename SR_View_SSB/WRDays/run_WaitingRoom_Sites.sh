#!/bin/bash
# Script in acrontab t1
# 5,20,35,50 * * * * lxplus ssh vocms202 /afs/cern.ch/user/c/cmst1/scratch0/Waitingroom_Dashboard/Waitingroom_SummedMetric/run_WaitingRoom_Sites.sh &> /dev/null
# Script for Dashboard metric 154, 155, 156
# outputfile WaitingRoom_1MonthSum.txt
# outputfile WaitingRoom_2MonthSum.txt
# outputfile WaitingRoom_3MonthSum.txt
# this script read all of data from http://dashb-ssb.cern.ch/dashboard/ according to column, dateFrom, dateTo, sites and it calculates How many days Sites are in WaitingRoom as last 1 month, last 2 months, last 3 months. 
clear
#fixing access
#source /afs/cern.ch/project/gd/LCG-share/new_3.2/etc/profile.d/grid_env.sh
#voms-proxy-init -voms cms
# Email if things are running slowly

if [ -f scriptRunning.run ];
then
   echo "run_WaitingRoom_SumMetrics.sh is already running. Will send an email to the admin."
   # script to send simple email
   # email subject
   SUBJECT="[MonitoringScripts] WRDays running slow"
   # Email To ?
   EMAIL="artiedaj@fnal.gov"
   # Email text/message
   if [ -f emailmessage.txt ];
   then
      rm emailmessage.txt
   fi
   touch emailmessage.txt
   EMAILMESSAGE="/tmp/emailmessage.txt"
   echo "run_WaitingRoom_SumMetrics.sh  is running to slowly. See: /afs/cern.ch/user/c/cmst1/scratch0/Waitingroom_Dashboard/Waitingroom_SummedMetric/"> $EMAILMESSAGE
   echo "/afs/cern.ch/user/c/cmst1/scratch0/Waitingroom_Dashboard/Waitingroom_SummedMetric/" >>$EMAILMESSAGE
   # send an email using /bin/mail
   /bin/mail -s "$SUBJECT" "$EMAIL" < $EMAILMESSAGE

else
     echo "bash run_WaitingRoom_SumMetrics.sh succesfully"
     touch scriptRunning.run
fi


#Run the script
txt="WaitingRoom_"  #postfix in code itself
echo "python waitingRoom_SummedMetrics.py $txt1"
python waitingRoom_SummedMetrics.py $txt &> sites_WaitingRoom_SummedMetrics.log
cat sites_WaitingRoom_SummedMetrics.log

problem="$?"
echo "problem: $problem"

cp $txt*.txt /afs/cern.ch/user/c/cmst1/www/WFMon/
echo "WaitingRoom_XMonthSum.txt files copied to: /afs/cern.ch/user/c/cmst1/www/WFMon/ "
rm scriptRunning.run
