#!/bin/bash

work_dir="$1"
cpus="$2"

if [ "x$cpus" = "x" ]; then
	cpus=1
fi

required_space=$((20000 * $cpus))
echo "Required scratch space: "$required_space

if [ -n "$work_dir" ]; then
	if [ ! -d "$work_dir" ]; then
		echo $ERROR_SCRATCH_DIR_NOT_FOUND_MSG ${work_dir}
		exit $ERROR_SCRATCH_DIR_NOT_FOUND
	fi
else
	echo $ERROR_SCRATCH_DIR_NOT_FOUND_MSG ${work_dir}
	exit $ERROR_SCRATCH_DIR_NOT_FOUND
fi

free_space=`df -P -B1MB ${work_dir} | awk '{if (NR==2) print $4}'`
echo "Scratch space in ${work_dir}: ${free_space} MB"

if [ $free_space -lt $required_space ] ; then
	echo $ERROR_LOW_SCRATCH_SPACE_MSG ${work_dir}
	exit $ERROR_LOW_SCRATCH_SPACE
fi

exit 0