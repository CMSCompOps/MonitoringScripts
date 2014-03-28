#!/bin/bash
# written by Gökhan Kandemir => gokhan.kandemir@cern.ch
# outputfile [year]_pledges.txt
# outputfile [year]_pledges.json
# outputfile [year]_pledges.html
# usercert and userkey files must be in folder "data"
# this script fetchs all pledges values and matchs with siteName from siteDB.
clear
echo "exporting KEY and CERT"

#fixing access
export X509_USER_CERT=./data/usercert.pem
export X509_USER_KEY=./data/userkey.pem

# Email if things are running slowly

if [ -f scriptRunning.run ];
then
   echo "run_pledges.sh is already running. Will send an email to the admin."
   # script to send simple email
   # email subject
   SUBJECT="[Pledges] load Pledges"
   # Email To ?
   EMAIL="gokhan.kandemir@cern.ch"
   # Email text/message
   if [ -f emailmessage.txt ];
   then
      rm emailmessage.txt
   fi
   touch emailmessage.txt
   EMAILMESSAGE="/tmp/emailmessage.txt"
   echo "run_pledges.sh  is running to slowly."
   # send an email using /bin/mail
   /bin/mail -s "$SUBJECT" "$EMAIL" < $EMAILMESSAGE

else
     echo "bash run_pledges.sh succesfully"
     touch scriptRunning.run
fi


#Run the script
year="2014"
txt="pledge"  #postfix in code itself
echo "python pledges.py $txt"
python pledges.py $txt $year &> pledges.log

problem="$?"
echo "problem: $problem"
echo "The files were created succesfully."

cp $txt".txt"  /afs/cern.ch/user/c/cmst1/www/SST
cp $txt".json"  /afs/cern.ch/user/c/cmst1/www/SST

rm scriptRunning.run
