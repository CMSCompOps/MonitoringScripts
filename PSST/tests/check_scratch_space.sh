#!/bin/bash

work_dir="$1"
cpus="$2"

if [ "x$cpus" = "x" ]; then
	cpus=1
fi

#20 GB of scratch sapce per code, defined in VO card
required_space=$((20000 * $cpus))
#if site has lower than 10 GB of scratch space, validation will fail
critical_space=$((5000 * $cpus))
echo "Required scratch space: ${required_space} MB"
#Required 10MB in /TMP
required_space_tmp=10

if [ -n "$work_dir" ]; then
	if [ ! -d "$work_dir" ]; then
		echo $ERROR_SCRATCH_DIR_NOT_FOUND_MSG ${work_dir}
		return $ERROR_SCRATCH_DIR_NOT_FOUND
	fi
else
	echo $ERROR_SCRATCH_DIR_NOT_FOUND_MSG ${work_dir}
	return $ERROR_SCRATCH_DIR_NOT_FOUND
fi

free_space=`df -P -B1MB ${work_dir} | awk '{if (NR==2) print $4}'`
echo "Scratch space in ${work_dir}: ${free_space} MB"

fs=`df -kP ${work_dir} | awk '{if (NR==2) print $1}'`
quota_str=`quota 2>/dev/null | awk '{if (NR>2) {if (NF==1) {n=$1; getline; print n " " $2-$1} else {print $1 " " $3-$2}}}' |grep $fs`
if [ $? -eq 0 ]; then
	myquota=`echo $myquotastr|awk '{print $2}'`
	let "quotagb=$myquota / (2 * 1000)"
	echo "Disk quota: ${quotagb}"
	metrics+=" disk_quota ${quotagb}"
fi

metrics+=" free_scratch_space ${free_space}"

free_space_tmp=`df -P -B1MB /tmp | awk '{if (NR==2) print $4}'`
echo "Free space in /tmp ${free_space_tmp} MB"
if [ $free_space_tmp -lt $required_space_tmp ]; then
	echo $WARNING_LOW_TMP_SPACE_MSG
	metrics+=" status WARNING"
fi

if [ $free_space -lt $required_space ]; then
	if [ $free_space -lt $critical_space ]; then
		echo $ERROR_LOW_SCRATCH_SPACE_MSG ${work_dir}
		return $ERROR_LOW_SCRATCH_SPACE
	else
		echo $WARNING_LOW_SCRATCH_SPACE_MSG ${work_dir}
		metrics+=" status WARNING"
		# return $WARNING_LOW_SCRATCH_SPACE
	fi
fi
