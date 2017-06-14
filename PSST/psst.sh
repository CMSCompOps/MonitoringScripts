#!/bin/bash
#
# Pilot Startup Site Test main script

#######################################
# Checking exit code of each test
# if exit code is not zero
# report to ES will be sent
# log file will be removed
# PSST will exit
#######################################
test_result() {
if [ "$exit_code" -ne 0 ]; then
  send_dashboard_report
  rm $log_file
  exit $exit_code
fi
}

#######################################
# Generating report file, which is
# passed to reporting script
#######################################
send_dashboard_report() {
  #Range(10000 - 19999) Failures related to the environment setup
  #https://twiki.cern.ch/twiki/bin/view/CMSPublic/JobExitCodes
  exit_code_range=10000
  logs=`cat ${log_file}`
  #timestamp in UTC with miliseconds
  end_timestamp=`date -u +%s%3N`
  metrics+=" timestamp ${end_timestamp}"
  #Check job status that will be reported to the dashboard
  if [ "$exit_code" = 0 ]; then
    if [[ $metrics != *"status"* ]]; then
      metrics+=" status OK"
    else
      #we will report only last status
      last_status=`echo $metrics | grep --only-matching 'status\s*[CRITICAL|WARNING|OK]*' | tail -n 1`
      #deleting all statuses
      metrics=`echo $metrics | sed -e 's/\<status\>\s*[a-zA-Z]*//g'`
      #let's add back latest status
      metrics+=" ${last_status}"
    fi
    #generating otrb_output.xml - http://glideinwms.fnal.gov/doc.prd/factory/custom_scripts.html#xml_output
    "$error_gen" -ok "psst.sh" "exit_code" 0 $metrics "logs" "${logs}"
  else
    metrics=`echo $metrics | sed -e 's/\<status\>\s*[a-zA-Z]*//g'`
    metrics+=" status CRITICAL"
    psst_exit_code=$((exit_code + exit_code_range))
    #generating otrb_output.xml - http://glideinwms.fnal.gov/doc.prd/factory/custom_scripts.html#xml_output
    "$error_gen" -error "psst.sh" "WN_Resource" "${logs}" "exit_code" $psst_exit_code $metrics
  fi
  echo "Sending metrics to ES"
  echo $metrics
  /usr/bin/python ${my_tar_dir}/reporting/es_report.py otrb_output.xml
  checkError "Reporting to job ES failed. Metrics: ${metrics}"
}


#######################################
# In case of unexpected script failure
# email alert will be sent and PSST
# exit with 0
#######################################
function checkError(){
  if [ $(echo $?) -ne 0 ]; then
    hostname=`hostname`
    MSG="PSST ERROR: ${1}; hostname: ${hostname}"
    echo $MSG
    if [ "$debug" != "True" ]; then
      cat $log_file | /usr/bin/Mail -s "${MSG}" ${email_addr}
    fi
    # cat exmple.log | /usr/bin/Mail -s "${MSG}" ${email_addr}
    rm $log_file
    exit 0
  fi
}

start_timestamp=`date -u +%s%3N`

log_file="/tmp/psst_$$.log"

trap "rm $log_file; exit" SIGHUP SIGINT SIGTERM

# Redirect stdout ( > ) into a named pipe ( >() ) running "tee"
exec >  >(tee -ia ${log_file})
exec 2> >(tee -ia ${log_file} >&2)

email_addr="rokas.maciulaitis@cern.ch"

metrics="start_timestamp ${start_timestamp}"
glidein_config="$1"
echo "Pilot Startup Site Test"
echo "Author Rokas Maciulaitis"
echo "rokas.maciulaitis(nospam)cern.ch"
echo "More information - https://twiki.cern.ch/twiki/bin/view/CMSPublic/PilotStartupSiteTest"

echo "Printing preliminary information..."
echo
echo -n "Sysinfo: "
uname -a
/usr/bin/lsb_release -idrc
echo -n "LocalDate: "
date
echo -n "UTCDate: "
date --utc
echo -n "UserId: "
id
cat /proc/meminfo | grep Mem

echo "Find directory of sub-scripts"
my_tar_dir=`grep -m1 -i '^GLIDECLIENT_CMS_PSST ' $glidein_config | awk 'END { if (NR==0 || $2=="")  exit 1; else print $2;}'`
checkError "Can't find directory of sub-scripts"
echo $my_tar_dir

echo "Grep site_name from glidein_config"
site_name=`grep -m1 -i '^GLIDEIN_CMSSite' $glidein_config| awk 'END { if (NR==0 || $2=="")  exit 1; else print $2;}'`
checkError "Can't find site_name"
echo $site_name
metrics+=" site_name ${site_name}"

echo "Grep workdir from glidein_config"
work_dir=`grep -m1 -i '^GLIDEIN_WORK_DIR' $glidein_config|awk 'END { if (NR==0 || $2=="")  exit 1; else print $2;}'`
checkError "Can't find work directory"
echo $work_dir

echo "Grep CE from glidein_config"
target_ce=`grep -m1 -i '^GLIDEIN_Gatekeeper' $glidein_config| awk 'END { if (NR==0 || $2=="")  exit 1; else print $2;}' | cut -f1 -d":"`
checkError "Can't find CE name"
echo $target_ce
metrics+=" target_ce ${target_ce}"

echo "Grep CE flavour"
grid_type=`grep -m1 -i '^GLIDEIN_GridType' $glidein_config|awk 'END { if (NR==0 || $2=="")  exit 1; else print $2;}'`
checkError "Can't find CE type"
echo "GridType: ${grid_type}"
if [ $grid_type = "gt2" ]; then
  ce_flavour="GLOBUS"
elif [ $grid_type = "nordugrid" ]; then
  ce_flavour="ARC-CE"
elif [ $grid_type = "cream" ]; then
  ce_flavour="CREAM-CE"
elif [ $grid_type = "condor" ]; then
  ce_flavour="HTCONDOR-CE"
fi
echo $ce_flavour
metrics+=" service_flavour ${ce_flavour}"

echo "Grep number of glidein CPUs"
cpus=`grep -m1 -i '^GLIDEIN_CPUS' $glidein_config| awk 'END { if (NR==0 || $2=="")  exit 1; else print $2;}'`
#2017-03-20 many factory entries are missing GLIDEIN_CPUS field in glidein
#config, by default it is set to 1
if [ "X$cpus" = X ]; then
  echo "No GLIDEIN_CPUS field in glidein_config, let's set it to 1"
  cpus=1
fi
checkError "Can't find number of CPUs"
echo $cpus

echo "Grep debug level"
debug=`grep -m1 -i '^PSST_DEBUG' $glidein_config | awk 'END { if (NR==0 || $2=="")  exit 1; else print $2;}'`
echo $debug

echo "Source error codes"
source ${my_tar_dir}/exit_codes.txt
export $(cut -d= -f1 ${my_tar_dir}/exit_codes.txt)
export metrics

# find error reporting helper script
error_gen=`grep '^ERROR_GEN_PATH ' $glidein_config | awk '{print $2}'`


echo "Check connection"
${my_tar_dir}/tests/check_connection.sh
exit_code=$?
echo "Exit code:" $exit_code
test_result

echo "Check cpu load"
. ${my_tar_dir}/tests/check_cpu_load.sh $cpus
exit_code=$?
echo "Exit code:" $exit_code

echo "Check software area"
. ${my_tar_dir}/tests/check_software_area.sh $cpus $error_gen
exit_code=$?
echo "Exit code:" $exit_code
test_result

echo "Check scratch space"
. ${my_tar_dir}/tests/check_scratch_space.sh $work_dir $cpus
exit_code=$?
echo "Exit code:" $exit_code
test_result


echo "Check proxy"
${my_tar_dir}/tests/check_proxy.sh
exit_code=$?
echo "Exit code:" $exit_code
test_result

echo "Siteconf validation"
/usr/bin/python ${my_tar_dir}/tests/check_siteconf.py
exit_code=$?
echo "Exit code:" $exit_code
test_result

send_dashboard_report
exit $exit_code
# let's exit with 0, to do not affect CMS activities
# as now we are interested only in results reported to
# job dashboard
# exit 0
