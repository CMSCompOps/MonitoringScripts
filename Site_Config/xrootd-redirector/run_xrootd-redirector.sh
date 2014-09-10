#!/bin/bash
# written by John Artieda

# set up a proxy to read site names from SiteDB
#source /afs/cern.ch/project/gd/LCG-share/new_3.2/etc/profile.d/grid_env.sh
#voms-proxy-init -voms cms

#Run the script
path="/afs/cern.ch/user/j/jartieda/MonitoringScripts/Site_Config/xrootd-redirector"
fileName="xrootd-redirector"
txt=$path"/"$fileName
findText1="root://xrootd-cms.infn.it"
findText2="root://cmsxrootd.fnal.gov"

echo "python $fileName.py > $txt.txt"
python $txt".py" $txt $findText1 $findText2 &> $txt".log"

problem="$?"
echo "problem: $problem"

cp $txt".txt" /afs/cern.ch/user/c/cmst1/www/SST/
echo "The files were created succesfully."