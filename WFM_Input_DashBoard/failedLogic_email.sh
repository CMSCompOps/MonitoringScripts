jobs=$1

   SUBJECT="[Monitoring] Failed task type logic problem"
   # Email to workflow team
   EMAIL="jbadillo@cern.ch"
   EMAILMESSAGE="/tmp/emailmessage.txt"
   echo "There is a problem with the logic to deduce job type from the condor data."> $EMAILMESSAGE
   echo "Please have a look to the following jobs:" >>$EMAILMESSAGE
   echo ${jobs} >> $EMAILMESSAGE
   # send an email using /bin/mail
   /bin/mail -s "$SUBJECT" "$EMAIL" < $EMAILMESSAGE

