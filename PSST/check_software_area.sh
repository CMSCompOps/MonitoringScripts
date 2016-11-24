#!/usr/bin/env bash

# Software area definition and existence
isEGEE=0
if [ -n "$OSG_GRID" ] ; then
	[ -f $OSG_GRID/setup.sh ] && source $OSG_GRID/setup.sh
	if [ -d $OSG_APP/cmssoft/cms ] ;then
		SW_DIR=$OSG_APP/cmssoft/cms
	elif [ -d $CVMFS/cms.cern.ch ] ; then
		SW_DIR=$CVMFS/cms.cern.ch
	elif [ -d /cvmfs/cms.cern.ch ] ; then
		SW_DIR=/cvmfs/cms.cern.ch
	else
		echo "ERROR: Cannot find CMS software in OSG node"
		echo "summary: SW_DIR_UNDEF"
		echo $ERROR_NO_CMS_SW_DIR 1>&2
		exit 1
	fi
	echo "SwArea: $SW_DIR"
elif [ -n "$VO_CMS_SW_DIR" ] ; then
	isEGEE=1
	SW_DIR=$VO_CMS_SW_DIR
	echo "SwArea: $SW_DIR"
else
	echo "ERROR: Neither VO_CMS_SW_DIR nor OSG_GRID defined"
	echo "summary: SW_DIR_UNDEF"
	echo $ERROR_NO_CMS_SW_DIR 1>&2
	exit 1
fi
if [ ! -d $SW_DIR -o ! -r $SW_DIR ] ; then
	echo "ERROR: software directory non existent or non readable"
	echo "summary: SW_DIR_NOT_READABLE"
	echo $ERROR_NO_CMS_SW_DIR 1>&2
	exit 1
fi

# Software area space
hasCVMFS=0
if [ -d $SW_DIR ] ; then
  if [ "`echo $SW_DIR | cut -d / -f 2`" == "afs" ]; then
	SPACE=`fs lq $SW_DIR | tail -1 | awk '{print (\$2-\$3)/1000000 }'`
  elif [ "`echo $SW_DIR | cut -d / -f 2`" == "cvmfs" ]; then
	hasCVMFS=1
  else
	SPACE=`df -k -P $SW_DIR | tail -1 | awk '{print \$4/1000000}'`
  fi
  if [ $hasCVMFS == 0  ]; then
	echo "FreeSWAreaSpace: $SPACE GB"
  fi

# Test if we are at CERN
  atCERN=0
  atCERN=`echo $SW_DIR | grep -c '/afs/cern.ch' 2>/dev/null`

# Test if can write on SwArea (for EGI, non-CVMFS sites excluding CERN)
  cantwrite=0
  if [ $isEGEE == 1 ] && [ $hasCVMFS == 0 ] && [ $atCERN == 0 ]
  then
	touch $SW_DIR/.sametest
	result=$?
	if [ $result != 0 ]
	then
	  cantwrite=1
	  echo "ERROR: cannot write to software area"
	  echo "summary: SW_DIR_NOT_WRITABLE"
	  echo $ERROR_NOT_WRITABLE_SW_DIR 1>&2
	  exit 1
	fi
  fi
fi

# Check for free space on current directory and /tmp
# space=`check_df .`
# echo "WorkDirSpace: $space MB" &>/dev/null
# if [ $space -lt 10000 ] ; then
# 	echo "WARNING: less than 10 GB of free space in working directory"
# 	summary="summary: WORKDIR_LOW_SPACE"
# 	warn=1
# fi

# space=`check_df /tmp` &>/dev/null
# echo "TmpSpace: $space MB"
# if [ $space -lt 10 ] ; then
# 	echo "WARNING: less than 10 MB of free space in /tmp"
# 	summary="summary: TMP_LOW_SPACE"
# 	warn=1
# fi

# # Check quota, if any
# space=`check_quota .` &>/dev/null
# if [ $space -ne -1 ] ; then
# 	echo "Quota: $space MB"
# 	if [ $space -lt 10000 ] ; then
# 	echo "WARNING: too little quota"
# 	summary="summary: TMP_LOW_QUOTA"
# 	warn=1
# 	fi
# fi
echo 0 1>&2
exit 0