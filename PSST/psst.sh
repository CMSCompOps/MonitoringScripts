#!/usr/bin/env bash

#function for ending validation script if one of the test fails (returns not 0)
test_result() {	
	if [ "$exit_code" != "0" ]; then
		send_dashboard_report
		exit $exit_code
	fi
}

send_dashboard_report() { 
	#Generating taskId and jobRange for dashboard
	MAXJOB=1000
	TIMENOW=`/bin/date '+%s'`
	TIMEMOD=`echo "${TIMENOW} % 900" | /usr/bin/bc`
	TIME15M=`echo "${TIMENOW} - ${TIMEMOD}" | /usr/bin/bc`

	TASK="PSST_${site_name}_${TIME15M}"

	network_interface=`/sbin/route | grep '^default' | grep -o '[^ ]*$'`
	ip=`/sbin/ip addr show ${network_interface} | grep -m 1 "inet" | awk '{print $2}' | sed 's/[^0-9]*//g'`
	mac=`/sbin/ifconfig -a ${network_interface} | grep -m 1 -o -E '([[:xdigit:]]{1,2}:){5}[[:xdigit:]]{1,2}' | sed 's/://g'`

	if [ -z "$mac" ]; then
		MAC10=`echo "ibase=16; ${mac}" | /usr/bin/bc`
		MACMOD=`echo "${MAC10} + ${TIMEMOD}" | /usr/bin/bc`
		JOB=`echo "${MACMOD} % ${MAXJOB}" | /usr/bin/bc`
	else
		JOB=`echo "${ip} % ${MAXJOB}" | /usr/bin/bc`
	fi

	#Check job status that will be reported to the dashboard
	if [ "$exit_code" = "0" ]; then
		grid_status="succeeded"
	else
		grid_status="failed"
	fi

	echo "Sending post job info to the dashboard"
	echo $site_name $exit_code $grid_status $TASK $JOB
	# /usr/bin/python ${my_tar_dir}/DashboardAPI.py $site_name $exit_code $grid_status $TASK $JOB
}

glidein_config="$1"
echo "Pilot Startup Site Test"
echo "More information - https://twiki.cern.ch/twiki/bin/view/CMSPublic/PilotStartupSiteTest"

echo "Printing current glidein_config"
echo "$(cat glidein_config)"

echo "Find directory of sub-scripts"
my_tar_dir=`grep -m1 -i '^GLIDECLIENT_CMS_PSST ' $glidein_config | awk '{print $2}'`
echo $my_tar_dir

echo "Grep site_name from glidein_config"
site_name=`grep -m1 -i '^GLIDEIN_CMSSite' $glidein_config| awk '{print $2}'`
echo $site_name

echo "Export error codes"
source ${my_tar_dir}/exit_codes.txt
export $(cut -f1 ${my_tar_dir}/exit_codes.txt)

echo "Check proxy"
exit_code=$(${my_tar_dir}/check_proxy.sh 2>&1 >/dev/null)
echo "Exit code:" $exit_code
test_result

echo "Check software area"
exit_code=$(${my_tar_dir}/check_software_area.sh 2>&1 >/dev/null)
echo "Exit code:" $exit_code
test_result

echo "Discover CMSSSW"
exit_code=$(${my_tar_dir}/discover_CMSSW.sh $glidein_config 2>&1 >/dev/null)
echo "Exit code:" $exit_code
test_result

echo "siteconf validation"
exit_code=$(/usr/bin/python ${my_tar_dir}/export_siteconf_info.py 2>&1 >/dev/null)
echo "Exit code:" $exit_code

# echo "test squid"
# exit_code=$(/usr/bin/python ${my_tar_dir}/test_squid.py 2>&1 >/dev/null)
# echo "Exit code:" $exit_code

send_dashboard_report
exit $exit_code
