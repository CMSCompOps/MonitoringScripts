#!/bin/bash

# Determine the cpu architecture string.
case `uname -p` in
i*86) 
	cpuarch=ia32 ;;
x86_64) 
	cpuarch=amd64 ;;
*EMT*) 
	cpuarch=amd64 ;;
armv7l) 
	cpuarch=armv7hl ;; # The kernel is armv7l, but we assume system as armv7hl (hard floats)
aarch64) 
	cpuarch=aarch64 ;;
ppc64le) 
	cpuarch=ppc64le ;;
*) 
	cpuarch=`uname -p`
	echo ERROR_NOT_SUPPORTED_ARCH_MSG ${cpuarch}
	exit $ERROR_NOT_SUPPORTED_ARCH
esac

required_os_version=6

if [ -d "/etc/lsb-release.d/" ] || [ -f "/etc/lsb-release" ]; then
	os=`lsb_release -d | awk '{$1= ""; print $0}'`
	version=`lsb_release -r | awk '{$1= ""; print $0}' | cut -f1 -d"."`
	echo $version
	echo $os | egrep -q "Scientific|Red Hat Enterprise|CentOS"
	if [ $? -eq 0 ]; then
		if [ $required_os_version -eq $version ]; then
			echo $os, $version
			exit 0
		else
			echo $ERROR_NOT_SUPPORTED_OS_V_MSG $os, $version
			exit $ERROR_NOT_SUPPORTED_OS_V
		fi
	else
		echo $ERROR_NOT_SUPPORTED_OS_MSG $os
		exit $ERROR_NOT_SUPPORTED_OS
	fi
elif [ -f /etc/SuSE-release ]; then
	os="SuSE"
	version=`grep -i '^version' < /etc/SuSE-release | tr -dc '[0-9]'`
	echo $ERROR_NOT_SUPPORTED_OS_MSG $os
	exit $ERROR_NOT_SUPPORTED_OS
elif [ -f /etc/fedora-release ]; then
	os="FC"
	version=`sed 's/[^0-9]//g' /etc/fedora-release`
	echo $ERROR_NOT_SUPPORTED_OS_MSG $os
	exit $ERROR_NOT_SUPPORTED_OS
elif [ -f /etc/redhat-release ]; then
	os=`cat /etc/redhat-release`
	version=`egrep "Red Hat Enterprise|Scientific|CentOS" /etc/redhat-release | sed 's/.*[rR]elease \([0-9]*\).*/\1/'`
	echo $os, $version
	if [ 1 -eq "$(echo "${version} < 7" | bc)" ] && [ 1 -eq "$(echo "${version} >= 6" | bc)" ]; then
		echo $version
		echo $os, $version
		exit 0
	else
		echo "ERROR: wrong version of ${os}"
		echo $ERROR_NOT_SUPPORTED_OS_V $os, $version
		exit $ERROR_NOT_SUPPORTED_OS_V
	fi
else
	echo "ERROR: not found supported os"
	echo $ERROR_NOT_SUPPORTED_OS_V_MSG $os, $version
	exit $ERROR_NOT_SUPPORTED_OS_V
fi