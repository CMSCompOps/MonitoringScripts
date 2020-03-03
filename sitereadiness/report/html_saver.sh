#!/bin/sh
# #############################################################################
# Bourne shell script to wrapper the write_sr_html.py python script. It
#    acquires execution lock and then launches the Python script.
# #############################################################################
ERR_FILE="/tmp/cmssst_htmlsavr_$$.err"
trap 'exit 1' 1 2 3 15
trap '(/bin/rm -f ${ERR_FILE}) 1> /dev/null 2>&1' 0
# #############################################################################



# check Kerberos ticket and AFS token:
# ====================================
echo "Checking Kerberos ticket/AFS token:"
/usr/bin/klist 1>${ERR_FILE} 2>&1
RC=$?
if [ ${RC} -ne 0 ]; then
   MSG="no valid Kerberos ticket, klist=${RC}"
   echo "   ${MSG}"
   if [ -t 0 ]; then
      # attached terminal, prompt user to kinit for 25 hours
      /usr/bin/kinit -l 25h cmssst@CERN.CH
      if [ $? -ne 0 ]; then
         exit ${RC}
      fi
   else
      /usr/bin/Mail -s "$0 ${MSG}" ${EMAIL_ADDR} < ${ERR_FILE}
      exit ${RC}
   fi
fi
/bin/rm ${ERR_FILE} 1>/dev/null 2>&1
#
/usr/bin/aklog 1>${ERR_FILE} 2>&1
RC=$?
if [ ${RC} -ne 0 ]; then
   MSG="unable to acquire AFS token, aklog=${RC}"
   echo "   ${MSG}"
   /usr/bin/Mail -s "$0 ${MSG}" ${EMAIL_ADDR} < ${ERR_FILE}
   exit ${RC}
fi
/bin/rm ${ERR_FILE} 1>/dev/null 2>&1


# fuse-bind EOS so we can write:
# ==============================
if [ -e /usr/bin/eosfusebind ]; then
   /usr/bin/eosfusebind -g 1>${ERR_FILE} 2>&1
   RC=$?
   if [ ${RC} -ne 0 ]; then
      MSG="unable to fuse-bind EOS, eosfusebind=${RC}"
      echo "   ${MSG}"
      /usr/bin/Mail -s "$0 ${MSG}" ${EMAIL_ADDR} < ${ERR_FILE}
      exit ${RC}
   fi
fi
/bin/rm ${ERR_FILE} 1>/dev/null 2>&1
# #############################################################################



# save HTML report on Mondays under week number of Sunday a week ago:
# ===================================================================
SR_HREP_DIR="/eos/home-c/cmssst/www/sitereadiness"

NOW_DOW=`/usr/bin/date +'%w'`
if [ "${NOW_DOW}" != "1" ]; then
   echo "HTML report saving only on Mondays !!!"
   exit 1
fi
YEAR_WEEK=`/usr/bin/awk 'BEGIN{print strftime("%G%V", systime()-691200, 1)}'`
if [ -f ${SR_HREP_DIR}/report.html ]; then
    /bin/cp -p -f ${SR_HREP_DIR}/report.html ${SR_HREP_DIR}/report_${YEAR_WEEK}.html
   /bin/ls -l ${SR_HREP_DIR}/report_${YEAR_WEEK}.html
else
   echo "No HTML report to save !!!"
   exit 1
fi

exit 0
