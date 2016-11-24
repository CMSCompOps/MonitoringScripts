#!/bin/sh

#get the glidein configuration file name
#must use glidein_config, it is used as global variable
glidein_config="$1"

PARROT_RUN_WORKS=`grep -i "^PARROT_RUN_WORKS " $glidein_config | awk '{print $2}'`

# Look for CMSSW in CVMFS, then the older places:

if [ -f "$CVMFS/cms.cern.ch/cmsset_default.sh" ]; then
   echo "Found CMS SW in $CVMFS/cms.cern.ch" 
   source "$CVMFS/cms.cern.ch/cmsset_default.sh"
elif [ -f "/cvmfs/cms.cern.ch/cmsset_default.sh" ]; then
   echo "Found CMS SW in /cvmfs/cms.cern.ch" 
   source "/cvmfs/cms.cern.ch/cmsset_default.sh"
elif [ -f "$VO_CMS_SW_DIR/cmsset_default.sh" ]; then
   echo "Found CMS SW in $VO_CMS_SW_DIR" 
   source "$VO_CMS_SW_DIR/cmsset_default.sh"
elif [ -f "$OSG_APP/cmssoft/cms/cmsset_default.sh" ]; then
   echo "Found CMS SW in $OSG_APP/cmssoft/cms" 
   source "$OSG_APP/cmssoft/cms/cmsset_default.sh"
elif [ "X$PARROT_RUN_WORKS" = "XTRUE" ]; then
   echo "Pilot will use parrot for CVMFS." 
   echo 0 1>&2
   exit 0
else
   echo "cmsset_default.sh not found!\n" 
   echo "Looked in $CVMFS/cms.cern.ch/cmsset_default.sh" 
   echo "and /cvmfs/cms.cern.ch/cmsset_default.sh" 
   echo "and $VO_CMS_SW_DIR/cmsset_default.sh" 
   echo "and $OSG_APP/cmssoft/cms/cmsset_default.sh" 
   echo "and \$PARROT_RUN_WORKS is set to $PARROT_RUN_WORKS" 
   echo $ERROR_NO_CMSSW 1>&2
   exit 1 
fi

if [ -z "$glidein_config" ]; then
  archs="slc6_amd64_gcc481"
else
  archs=`grep '^CMS_SCRAM_ARCHES ' $glidein_config | awk '{print $2}'`
  if [ -z "$archs" ]; then
    archs="slc6_amd64_gcc481"
  fi
fi
echo "Looking for CMS SW on $archs" 

tmpname=`mktemp --tmpdir=$PWD installed_cms_software.XXXXXX`
for arch in $archs
do
   echo "Analyzing $arch" 
   export SCRAM_ARCH=$arch
   scramv1 list -c CMSSW | grep CMSSW | awk '{print $2}' | sort | uniq | grep ^CMSSW >> $tmpname
done

# Format the CMSSW list

sw_list=`cat $tmpname | awk '{if (length(a)!=0) {a=a "," $0} else {a=$0}}END{print a}'`
rm $tmpname

if [ -z "$sw_list" ]; then
  echo "No CMS SW found!" 
  echo $ERROR_NO_CMSSW 1>&2
  exit 81
fi
echo "CMS SW list found and not empty" 

# Export the data - DISABLED to save ClassAd space

#echo "############ CMS software ##############" >> "$glidein_config"
#echo "GLIDEIN_CMSSW_LIST $sw_list" >> "$glidein_config"
#echo "########## end CMS software ############" >> "$glidein_config"

# One has to tell the condor_startup to publish the data
#condor_vars_file=`grep -i "^CONDOR_VARS_FILE " $glidein_config | awk '{print $2}'`
#echo "############ CMS software ##############" >> "$condor_vars_file"
#echo "GLIDEIN_CMSSW_LIST S - + Y Y +" >> "$condor_vars_file"
#echo "########## end CMS software ############" >> "$condor_vars_file"
echo 0 1>&2
exit 0
