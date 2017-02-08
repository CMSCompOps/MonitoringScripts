#!/usr/bin/env bash

# Software area definition and existence
isEGEE=false
isOSG=false
hasCVMFS=false

if [ -n "$OSG_GRID" ] ; then
	isOSG=true
	[ -f $OSG_GRID/setup.sh ] && source $OSG_GRID/setup.sh
	if [ -d $OSG_APP/cmssoft/cms ] ;then
		SW_DIR=$OSG_APP/cmssoft/cms
	elif [ -d $CVMFS/cms.cern.ch ] ; then
		SW_DIR=$CVMFS/cms.cern.ch
	elif [ -d /cvmfs/cms.cern.ch ] ; then
		SW_DIR=/cvmfs/cms.cern.ch
	else
		echo $ERROR_NO_CMS_SW_DIR_MSG
		exit $ERROR_NO_CMS_SW_DIR
	fi
	echo "SwArea: $SW_DIR"

elif [ -n "$VO_CMS_SW_DIR" ] ; then
	isEGEE=true
	SW_DIR=$VO_CMS_SW_DIR
	echo "SwArea: $SW_DIR"

elif [ -n "$CMS_PATH" ] && [ -d "/cvmfs/cms.cern.ch" ] ; then
	SW_DIR=$CMS_PATH
	hasCVMFS=true
	echo "SwArea: $SW_DIR"
else
	echo $ERROR_NO_CMS_SW_DIR_MSG
	exit $ERROR_NO_CMS_SW_DIR
fi

if [ ! -d $SW_DIR -o ! -r $SW_DIR ] ; then
	echo $ERROR_NO_CMS_SW_DIR_MSG
	exit $ERROR_NO_CMS_SW_DIR
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
	exit $ERROR_CMSSET_DEFAULT_FAILED
fi
rm -f $tmpfile

echo "Default SCRAM_ARCH: $SCRAM_ARCH"

if [ -z $CMS_PATH ]; then
	echo $ERROR_CMS_PATH_UNDEFINED_MSG
	exit $ERROR_CMS_PATH_UNDEFINED
fi

if [ ! -d $CMS_PATH ] ; then
	echo $ERROR_CMS_PATH_DIR_MISSING_MSG $CMS_PATH
	exit $ERROR_CMS_PATH_DIR_MISSING
fi

echo -n "scramv1_version: "
scramv1 version
result=$?
if [ $result != 0 ]
then
	echo $ERROR_SCRAM_NOT_FOUND_MSG
	exit $ERROR_SCRAM_NOT_FOUND
fi

echo "Retrieving list of CMSSW versions installed..."
# cmsos_defined='slc5_amd64 slc6_amd64'
# cmssw_installed_version_list=''
# for cmsos in $cmsos_defined
# do
# 	cmssw_installed_version_list=$cmssw_installed_version_list`scram -a ${cmsos} l -a -c CMSSW | tr -s " " | cut -d " " -f2 | sort -u`
# done

#get all available cmssw realeases of any architecture
cmssw_installed_version_list=`scram -a slc* l -a -c CMSSW | tr -s " " | cut -d " " -f2 | sort -u`

cmssw_required_version_list='CMSSW_5_3_11 CMSSW_8_0_21'
for cmssw_ver in $cmssw_required_version_list
do
	echo $cmssw_installed_version_list | grep -i $cmssw_ver >& /dev/null
	result=$?
	if [ $result != 0 ]; then
		echo "ERROR: Required CMSSW version $cmssw_ver not installed"
		exit 1
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
				exit $ERORR_CORRUPTED_CMSSW_FILES
			else
				echo "${file}: ls_byte_count=${ls_byte_count}; wc_byte_count=${wc_byte_count}"
			fi
		done
		# echo "Checking version $cmssw_ver installation..."
		# scramv1 project CMSSW $cmssw_ver
		# TestResult=$?
		# if [ $TestResult != 0 ]; then
		# 	error=1
		# 	echo "ERROR: Some of the required CMSSW versions not working"
		# 	errorSummary="summary: REQ_CMSSW_NOT_WORKING"
		# fi
	fi
done
# 	result=$?


# archs_defined='slc5_amd64_gcc434 slc5_amd64_gcc462 slc5_amd64_gcc472 slc6_amd64_gcc530 slc6_amd64_gcc472 slc6_amd64_gcc481 slc6_amd64_gcc493 slc6_amd64_gcc491'
# for arch in $archs_defined
# do
# 	export SCRAM_ARCH=$arch
# 	export BUILD_ARCH=$arch
# 	echo "SCRAM_ARCH: $arch"
# 	#scramv1 list -c CMSSW > scramv1_list_output.txt
# 	listerror=$?
# 	if [ $listerror != 0 ]; then
# 		echo "WARNING: could not list CMSSW versions with scramv1"
# 	fi
# 	touch scramv1_list_output.txt
# 	cat scramv1_list_output.txt | tr -s " " | cut -d " " -f2 | sort -u > cmssw_installed_${arch}.txt
# 	rm -f scramv1_list_output.txt
# 	cat cmssw_installed_${arch}.txt >> cmssw_installed_version_list.txt
# 	# if [ -d $CMS_PATH/${arch}/cms/cms-common/1.0 ]; then
# 	# 	echo "Recent cms-common RPM already installed:"
# 	# 	ls -d $CMS_PATH/${arch}/cms/cms-common/1.0/* | grep -v etc
# 	# else
# 	# 	echo "Old style cms-common RPM installed."
# 	# fi
# done
# scram l -a -c CMSSW

# missing=0
# failproject=0
# for cmsver in `cat cmssw_required_version_list.txt`
# do
# 	grep -x $cmsver cmssw_installed_version_list.txt >& /dev/null
# 	result=$?
# 	if [ $result != 0 ]; then
# 		echo "ERROR: Required CMSSW version $cmsver not installed"
# 		error=1
# 		errorSummary="REQ_CMSSW_NOT_FOUND"
# 	else
# 		echo "Checking version $cmsver installation..."
# 	   	# execute in a subprocess commands that require scram 
# 	   	echo $SAME_SENSOR_HOME
# 		$SAME_SENSOR_HOME/tests/TestCmsswVersion.sh $cmsver
# 		TestResult=$?
# 		if [ $TestResult != 0 ]; then
# 			error=1
# 			echo "ERROR: Some of the required CMSSW versions not working"
# 			errorSummary="summary: REQ_CMSSW_NOT_WORKING"
# 		fi
# 	fi
# done


exit 0