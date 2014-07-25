#!/bin/bash
# written by John Artieda

# set up a proxy to read site config files
#source /afs/cern.ch/project/gd/LCG-share/new_3.2/etc/profile.d/grid_env.sh
#voms-proxy-init -voms cms

#Run the script
path="/afs/cern.ch/user/j/jartieda/MonitoringScripts/Site_Config/generic_file_monitoring"
txt=$path"/gfm"
findText="statistics-destination"

echo "python site_local_config.py > $txt.txt and $txt.json"
python $path"/"site_local_config.py $txt $findText &> $path"/"site_local_config.log

problem="$?"
echo "problem: $problem"

cp $txt".txt" /afs/cern.ch/user/c/cmst1/www/SST
echo "The files were created succesfully."