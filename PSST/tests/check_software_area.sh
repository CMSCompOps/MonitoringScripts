#!/bin/bash

cpus="$1"
error_gen="$2"

#if CPUs variable is not set, let's assume that it is single core pilot
if [ "x$cpus" = "x" ]; then
	cpus=1
fi

# Software area definition and existence
hasCVMFS=0
/usr/bin/cvmfs_config stat -v cms.cern.ch > /dev/null 2>&1
if [ $? -eq 0 ]; then
    hasCVMFS=1
fi

if [ -n "$OSG_GRID" ] ; then
	[ -f $OSG_GRID/setup.sh ] && source $OSG_GRID/setup.sh
	if [ -d $OSG_APP/cmssoft/cms ] ;then
		SW_DIR=$OSG_APP/cmssoft/cms
	elif [ -d $CVMFS/cms.cern.ch ] ; then
		SW_DIR=$CVMFS/cms.cern.ch
	elif [ -d /cvmfs/cms.cern.ch ] ; then
		SW_DIR=/cvmfs/cms.cern.ch
	else
		echo $ERROR_NO_CMS_SW_DIR_MSG
		return $ERROR_NO_CMS_SW_DIR
	fi
	echo "SwArea: $SW_DIR"

elif [ -n "$VO_CMS_SW_DIR" ] ; then
	SW_DIR=$VO_CMS_SW_DIR
	echo "SwArea: $SW_DIR"

elif [ -n "$CMS_PATH" ] && [ -d "/cvmfs/cms.cern.ch" ] ; then
	SW_DIR=$CMS_PATH
	echo "SwArea: $SW_DIR"
else
	echo $ERROR_NO_CMS_SW_DIR_MSG
	return $ERROR_NO_CMS_SW_DIR
fi

if [ ! -d $SW_DIR -o ! -r $SW_DIR ] ; then
	echo $ERROR_NO_CMS_SW_DIR_MSG
	return $ERROR_NO_CMS_SW_DIR
fi

echo -n "Software location: "
if [ "`echo $SW_DIR | cut -d / -f 2`" == "afs" ]; then
	echo "AFS"
	SPACE=`fs lq $SW_DIR | tail -1 | awk '{print (\$2-\$3)/1024 }'`
elif [ "`echo $SW_DIR | cut -d / -f 2`" == "cvmfs" ]; then
	hasCVMFS=1
	echo "CVMFS"
else
	echo "local"
	SPACE=`df -k -P $SW_DIR | tail -1 | awk '{print \$4/1024}'`
fi
# Disk space check only for non-CVMFS
if [ $hasCVMFS == 0  ]; then
	echo "FreeSWAreaSpace: $SPACE MB"
fi

tmpfile=`mktemp /tmp/tmp.XXXXXXXXXX`
source $SW_DIR/cmsset_default.sh > $tmpfile 2>&1
result=$?

if [ $result != 0 ] ; then
	cat $tmpfile
	rm -f $tmpfile
	echo "ERROR: CMS software initialisation script cmsset_default.sh failed"
	return $ERROR_CMSSET_DEFAULT_FAILED
fi
rm -f $tmpfile


if [ $hasCVMFS == 1 ]; then
	echo "Checking CVMFS cache"

	#approach from /usr/bin/cvmfs_config
	mount_point="/cvmfs/cms.cern.ch"
	cache_use=`df -P $mount_point | tail -n 1 | awk '{print int($3)"/" 1024}' | bc ` || exit 34
	cache_avail=`df -P $mount_point | tail -n 1 | awk '{print int($4)"/" 1024}' | bc ` || exit 34
  	cache_max=$(($cache_use+$cache_avail))

	echo "Free space in CVMFS cache: ${cache_avail} MB"

	metrics+=" free_cvmfs_cache_space ${cache_avail}"
	metrics+=" cvmfs_cache_quota ${cache_max}"

	#Required cvmfs free cache size 1024MB/core
	# required_cvmfs_free_cache=`echo 1024*${cpus}| bc`
	# echo "Required space for cvmfs cache: ${required_cvmfs_free_cache} MB"

	# # if [ $cvmfs_free_cache -le $required_cvmfs_free_cache ]; then
	# if [ $(echo "$cache_avail >= $required_cvmfs_free_cache" | bc) -eq 0 ]; then
	# 	echo $ERROR_LOW_CVMFS_CACHE_MSG: $cache_avail MB
	# 	return $ERROR_LOW_CVMFS_CACHE
	# fi
fi

echo "Default SCRAM_ARCH: $SCRAM_ARCH"

if [ -z $CMS_PATH ]; then
	echo $ERROR_CMS_PATH_UNDEFINED_MSG
	return $ERROR_CMS_PATH_UNDEFINED
fi

if [ ! -d $CMS_PATH ] ; then
	echo $ERROR_CMS_PATH_DIR_MISSING_MSG $CMS_PATH
	return $ERROR_CMS_PATH_DIR_MISSING
fi

echo -n "scramv1_version: "
scramv1 version
result=$?
if [ $result != 0 ]
then
	echo $ERROR_SCRAM_NOT_FOUND_MSG
	return $ERROR_SCRAM_NOT_FOUND
fi

echo "Retrieving list of CMSSW versions installed..."

#get all available cmssw realeases of any architecture
cmssw_installed_version_list=`scram -a slc* l -a -c CMSSW | tr -s " " | cut -d " " -f2 | sort -u`

#Most popular releases according kibana
#https://twiki.cern.ch/twiki/bin/view/CMSPublic/PilotStartupSiteTest
cmssw_required_version_list='CMSSW_8_0_25 CMSSW_8_0_26_patch1'
for cmssw_ver in $cmssw_required_version_list
do
	echo $cmssw_installed_version_list | grep -i $cmssw_ver >& /dev/null
	result=$?
	if [ $result != 0 ]; then
		echo "ERROR: Required CMSSW version $cmssw_ver not installed"
		return $ERROR_NO_CMSSW
	else
		#Getting path of cmssw_ver in CVMFS
		cmssw_ver_path=`scram -a slc* l -a -c ${cmssw_ver} | tr -s " " | cut -d " " -f3 | sed -n 1p`
		echo "Selecting 10 random files $cmssw_ver_path"
		random_files=`find ${cmssw_ver_path} -type f | shuf -n 10`
		for file in $random_files
		do
			ls_byte_count=`ls -l ${file} | cut -d " " -f5`
			wc_byte_count=`wc -c ${file} | cut -d " " -f1`
			if [ $ls_byte_count != $wc_byte_count ]; then
				echo $ERORR_CORRUPTED_CMSSW_FILES_MSG $file
				return $ERORR_CORRUPTED_CMSSW_FILES
			# else
				# echo "${file}: ls_byte_count=${ls_byte_count}; wc_byte_count=${wc_byte_count}"
			fi
		done
	fi
done
