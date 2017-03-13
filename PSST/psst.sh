#!/bin/bash

# ###################################
# Pilot Startup Site Test main script
# ###################################

EMAIL_ADDR="rokas.maciulaitis@cern.ch"

#function for ending PSST validation script if one of the test fails (returns not 0).
#Exit codes in range [30;40] are treated as warning. It means that exit code is reported
#to the job Dashboard and PSST continues to run.
test_result() {	
	if [ "$exit_code" -ne 0 ]; then
		if [ "$exit_code" -ge 30 ] && [ "$exit_code" -le 40 ]; then
			send_dashboard_report
		else
			send_dashboard_report
			exit $exit_code
		fi
	fi
}

send_dashboard_report() { 
	#Generating taskId and jobRange for dashboard
	maxjob=1000
	#Range(10000 - 19999) Failures related to the environment setup
	#https://twiki.cern.ch/twiki/bin/view/CMSPublic/JobExitCodes
	exit_code_range=10000
	timenow=`/bin/date '+%s'`
	timemod=`echo "${timenow} % 900" | /usr/bin/bc`
	time15=`echo "${timenow} - ${timemod}" | /usr/bin/bc`

	task="PSST_${site_name}_${time15}"

	network_interface=`/sbin/route | grep '^default' | grep -o '[^ ]*$'`
	ip=`/sbin/ip addr show ${network_interface} | grep -m 1 "inet" | awk '{print $2}' | sed 's/[^0-9]*//g'`
	mac=`/sbin/ifconfig -a ${network_interface} | grep -o  -E '([0-9A-Fa-f]{2}[:-]){5,}([0-9A-Fa-f]{2})' | sed 's/[:-]//g'`

	if [ ! -z "$mac" ]; then
		mac10=`echo $((16#${mac}))`
		macmod=`echo "${mac10} + ${timemod}" | /usr/bin/bc`
		job=`echo "${macmod} % ${maxjob}" | /usr/bin/bc`
	else
		job=`echo "${ip} % ${maxjob}" | /usr/bin/bc`
	fi

	#Check job status that will be reported to the dashboard
	if [ "$exit_code" = 0 ]; then
		grid_status="succeeded"
	else
		grid_status="failed"
		exit_code=$((exit_code + exit_code_range))
	fi
	echo "Sending post job info to the dashboard"
	echo $site_name $target_ce $exit_code $grid_status $task $job
	/usr/bin/python ${my_tar_dir}/reporting/DashboardAPI.py $site_name $target_ce $exit_code $grid_status $task $job
	checkError "Reporting to dashboard failed. Example of report: ${site_name} ${target_ce} ${exit_code} ${grid_status} ${task} ${job}"
}

function checkError(){
	if [ $(echo $?) -ne 0 ]; then
		hostname=`hostname`
		MSG="PSST ERROR: ${1}; hostname: ${hostname}"
		echo $MSG
		/usr/bin/Mail -s "${MSG}" ${EMAIL_ADDR} < /dev/null
		exit 0
	fi
}

glidein_config="$1"
echo "Pilot Startup Site Test"
echo "Author Rokas Maciulaitis"
echo "rokas.maciulaitis(nospam)cern.ch"
echo "More information - https://twiki.cern.ch/twiki/bin/view/CMSPublic/PilotStartupSiteTest"

echo "Find directory of sub-scripts"
my_tar_dir=`grep -m1 -i '^GLIDECLIENT_CMS_PSST ' $glidein_config | awk 'END { if (NR==0 || $2=="")  exit 1; else print $2;}'`
checkError "Can't find directory of sub-scripts"
echo $my_tar_dir

echo "Grep site_name from glidein_config"
site_name=`grep -m1 -i '^GLIDEIN_CMSSite' $glidein_config| awk 'END { if (NR==0 || $2=="")  exit 1; else print $2;}'`
checkError "Can't find site_name"
echo $site_name

echo "Grep workdir from glidein_config"
work_dir=`grep -m1 -i '^GLIDEIN_WORK_DIR' $glidein_config|awk 'END { if (NR==0 || $2=="")  exit 1; else print $2;}'`
checkError "Can't find work directory"
echo $work_dir

echo "Grep CE from glidein_config"
target_ce=`grep -m1 -i '^GLIDEIN_Gatekeeper' $glidein_config| awk 'END { if (NR==0 || $2=="")  exit 1; else print $2;}' | cut -f1 -d":"`
checkError "Can't find CE name"
echo $target_ce

echo "Grep number of CPUs"
cpus=`grep -m1 -i '^GLIDEIN_CPUS' $glidein_config| awk 'END { if (NR==0 || $2=="")  exit 1; else print $2;}'`
checkError "Can't number of CPUs"
echo $cpus

echo "Source error codes"
source ${my_tar_dir}/exit_codes.txt
export $(cut -d= -f1 ${my_tar_dir}/exit_codes.txt)

echo "Check OS"
${my_tar_dir}/tests/check_os.sh
exit_code=$?
echo "Exit code:" $exit_code
test_result

echo "Check connection"
${my_tar_dir}/tests/check_connection.sh
exit_code=$?
echo "Exit code:" $exit_code
test_result

echo "Check software area"
${my_tar_dir}/tests/check_software_area.sh $cpus
exit_code=$?
echo "Exit code:" $exit_code
test_result

echo "Check RPMs"
${my_tar_dir}/tests/check_RPMs.sh $my_tar_dir
exit_code=$?
echo "Exit code:" $exit_code
test_result

echo "Check scratch space"
${my_tar_dir}/tests/check_scratch_space.sh $work_dir $cpus
exit_code=$?
echo "Exit code:" $exit_code
test_result

echo "Check proxy"
${my_tar_dir}/tests/check_proxy.sh
exit_code=$?
echo "Exit code:" $exit_code
test_result

# echo "test squid"
# exit_code=$(/usr/bin/python ${my_tar_dir}/tests/test_squid.py 2>&1 >/dev/null)
# echo "Exit code:" $exit_code

echo "Siteconf validation"
/usr/bin/python ${my_tar_dir}/tests/check_siteconf.py
exit_code=$?
echo "Exit code:" $exit_code
test_result

echo "Check cpu load"
${my_tar_dir}/tests/check_cpu_load.sh $cpus
exit_code=$?
echo "Exit code:" $exit_code

send_dashboard_report
exit $exit_code