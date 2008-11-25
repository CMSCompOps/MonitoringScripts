#!/bin/sh
OUTDIR=/afs/cern.ch/cms/LCG/SiteComm
LOGDIR=$OUTDIR/log
tmpfile=`mktemp`
dir=`dirname $0`
$dir/sites.pl > $tmpfile
$dir/JRobotForSiteComm.py $OUTDIR/JobRobotForSiteComm.txt $tmpfile >> $LOGDIR/JRobotForSiteComm.log 2>&1
rm -f $tmpfile
