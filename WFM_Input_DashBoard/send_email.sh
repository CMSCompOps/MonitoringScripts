col=$1

   SUBJECT="[Monitoring] Condor Collector "${col}" Error"
   # Email to workflow team
   EMAIL="jbadillo@cern.ch"
   EMAILMESSAGE="/tmp/emailmessage.txt"
   echo "There is a problem with one of the collectors!  The monitoring scripts will give false information."> $EMAILMESSAGE
   echo "/afs/cern.ch/user/c/cmst1/scratch0/WFM_Input_DashBoard/WFMonDBShort.py" >>$EMAILMESSAGE
   echo "See the log file in the same directory for the error output " >> $EMAILMESSAGE
   # send an email using /bin/mail
   /bin/mail -s "$SUBJECT" "$EMAIL" < $EMAILMESSAGE

