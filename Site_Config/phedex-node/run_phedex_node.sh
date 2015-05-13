#!/bin/bash
# written by John Artieda

# set up a proxy to read site config files
#source /afs/cern.ch/project/gd/LCG-share/new_3.2/etc/profile.d/grid_env.sh
#voms-proxy-init -voms cms
#X509_USER_PROXY=/tmp/x509up_u47967;export X509_USER_PROXY

#Run the script
path="/afs/cern.ch/user/j/jartieda/MonitoringScripts/Site_Config/phedex-node"
txt=$path"/phedex_node"
findText="phedex-node"

echo "python phedex_node.py > $txt.txt and $txt.json"
python $path"/"phedex_node.py $txt $findText &> $path"/"phedex_node.log

problem="$?"
echo "problem: $problem"

cp $txt".txt" /afs/cern.ch/user/c/cmst1/www/SST/
echo "The files were created succesfully."