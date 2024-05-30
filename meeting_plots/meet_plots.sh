#!/bin/sh
# #############################################################################
# Bourne shell script to generate/collect the plots and tables for the
#                     Monday group chat meeting.
# #############################################################################
RC=0
EXC_LOCK=""
TMP_FILE="/tmp/cmssst_meetplots_$$.png"
ERR_FILE="/tmp/cmssst_meetplots_$$.err"
trap 'exit 1' 1 2 3 15
trap '(/bin/rm -f ${EXC_LOCK} ${TMP_FILE} ${ERR_FILE}) 1> /dev/null 2>&1' 0



PLOT_DIR="/eos/home-c/cmssst/www/meet_plots"
EMAIL_ADDR="lammel@cern.ch"
if [ -z "${HOME}" ]; then
   HOME="/afs/cern.ch/user/c/cmssst"
fi
# #############################################################################



# get cmssst/meet_plots lock:
# ---------------------------
echo "Acquiring lock for cmssst/meet_plots"
if [ ! -d /var/tmp/cmssst ]; then
   /bin/rm -f /var/tmp/cmssst 1>/dev/null 2>&1
   /bin/mkdir /var/tmp/cmssst 1>/dev/null 2>&1
fi
/bin/ln -s $$ /var/tmp/cmssst/meet_plots.lock
if [ $? -ne 0 ]; then
   # locking failed, get lock information
   LKINFO=`/bin/ls -il /var/tmp/cmssst/meet_plots.lock 2>/dev/null`
   LKFID=`echo ${LKINFO} | /usr/bin/awk '{print $1; exit}' 2>/dev/null`
   LKPID=`echo ${LKINFO} | /usr/bin/awk '{print $NF;exit}' 2>/dev/null`
   # check process holding lock is still active
   /bin/ps -fp ${LKPID} 1>/dev/null 2>&1
   if [ $? -eq 0 ]; then
      echo "   active process ${LKPID} holds lock, exiting"
      exit 1
   fi
   echo "   removing leftover lock: ${LKINFO}"
   /usr/bin/find /var/tmp/cmssst -inum ${LKFID} -exec /bin/rm -f {} \;
   LKPID=""
   LKFID=""
   LKINFO=""
   #
   /bin/ln -s $$ /var/tmp/cmssst/meet_plots.lock
   if [ $? -ne 0 ]; then
      echo "   failed to acquire lock, exiting"
      exit 1
   fi
fi
#
# double check we have the lock
LKPID=`(/bin/ls -l /var/tmp/cmssst/meet_plots.lock | /usr/bin/awk '{if($(NF-1)=="->")print $NF;else print "";exit}') 2>/dev/null`
if [ "${LKPID}" != "$$" ]; then
   echo "   lost lock to process ${LKPID}, exiting"
   exit 1
fi
LKPID=""
EXC_LOCK="/var/tmp/cmssst/meet_plots.lock"
# #############################################################################



# check Kerberos ticket, AFS token, and EOS-fusebind:
# ---------------------------------------------------
echo "Checking Kerberos ticket/AFS token:"
/bin/rm ${ERR_FILE} 1>/dev/null 2>&1
/usr/bin/klist 2> ${ERR_FILE}
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
#
/bin/rm ${ERR_FILE} 1>/dev/null 2>&1
/usr/bin/aklog 2> ${ERR_FILE}
RC=$?
if [ ${RC} -ne 0 ]; then
   MSG="unable to acquire AFS token, aklog=${RC}"
   echo "   ${MSG}"
   /usr/bin/Mail -s "$0 ${MSG}" ${EMAIL_ADDR} < ${ERR_FILE}
   exit ${RC}
fi
#
/bin/rm ${ERR_FILE} 1>/dev/null 2>&1
/usr/bin/eosfusebind -g 2> ${ERR_FILE}
RC=$?
if [ ${RC} -ne 0 ]; then
   MSG="unable to EOS fuse-bind, eosfusebind=${RC}"
   echo "   ${MSG}"
   /usr/bin/Mail -s "$0 ${MSG}" ${EMAIL_ADDR} < ${ERR_FILE}
   exit ${RC}
fi
# #############################################################################



# check if plots of this week already exist:
# ------------------------------------------
THIS_WEEK=`/bin/date '+%Y.%U'`
if [ -f ${PLOT_DIR}/.timestamp ]; then
   PLOT_WEEK=`/usr/bin/awk '{print $1; exit}' ${PLOT_DIR}/.timestamp`
elif [ -f ${PLOT_DIR}/.timetrial ]; then
   PLOT_WEEK=`/usr/bin/awk '{print $1; exit}' ${PLOT_DIR}/.timetrial`
else
   PLOT_WEEK="0000.99"
fi
#
if [ "${THIS_WEEK}" != "${PLOT_WEEK}" ]; then
   #
   # delete plots (probably of last week):
   # -------------------------------------
   echo "Deleting plots of ${PLOT_WEEK}"
   /bin/rm -f ${PLOT_DIR}/*.png ${PLOT_DIR}/.time*
   #
elif [ -f ${PLOT_DIR}/.timestamp ]; then
   #
   if [ `/bin/date '+%u'` -ge 5 ]; then
      #
      # replace plots of previous week with ones for this week:
      # -------------------------------------------------------
      echo "Replacing plots of previous week with this week ${THIS_WEEK}"
      /bin/rm -f ${PLOT_DIR}/*.png ${PLOT_DIR}/.time*
      #
      #
      /bin/touch ${PLOT_DIR}/.timestamp
      /bin/date '+%Y.%U written %Y-%b-%d %H:%M:%S' >> ${PLOT_DIR}/.timestamp
   else
      #
      # plots for this week exist, nothing to do
      echo "Plots for this week, ${THIS_WEEK}, exist already"
      #
      # release cmssst/meet_plots lock:
      # -------------------------------
      echo "Releasing lock for cmssst/meet_plots"
      /bin/rm ${EXC_LOCK}
      exit 0
   fi
fi
# #############################################################################



# fetch/convert plots for this weeks meeting, i.e. last weeks plots:
# ------------------------------------------------------------------
/bin/rm -f ${PLOT_DIR}/.timestamp 1>/dev/null 2>&1
/bin/touch ${PLOT_DIR}/.timetrial
/bin/date '+%Y.%U written %Y-%b-%d %H:%M:%S' >> ${PLOT_DIR}/.timetrial



# get batch/Grid job plots from the dashboard:
# --------------------------------------------
WE_TIS=`/bin/date +'%s' -u -d "last Wednesday"`
SLOT_STIS=`echo "${WE_TIS} - 172800" | /usr/bin/bc`
SLOT_ETIS=`echo "${WE_TIS} + 432000" | /usr/bin/bc`
SLOT_SITES='T1_DE_KIT T1_ES_PIC T1_IT_CNAF T1_FR_CCIN2P3 T1_UK_RAL T1_US_FNAL T1_RU_JINR T2_CH_CERN T2_.*'
SLOT_URL='https://monit-grafana.cern.ch/render/d-solo/requested-cpu/requested-cpu'
SLOT_QRYR="orgId=11&from=${SLOT_STIS}000&to=${SLOT_ETIS}000&panelId=5&width=1024&height=768&tz=UTC&timeout=900&var-site="
SLOT_QRYP="orgId=11&from=${SLOT_STIS}000&to=${SLOT_ETIS}000&panelId=4&width=1024&height=768&tz=UTC&timeout=900&var-site="
#
for QSITE in ${SLOT_SITES}; do
   SITE="${QSITE//.\*}"
   if [ ! -f ${PLOT_DIR}/${SITE}_running.png ]; then
      /usr/bin/wget -O ${PLOT_DIR}/${SITE}_running.png --timeout=900 --no-check-certificate --header="Authorization: Bearer eyJrIjxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxOjExfQ==" --header="Accept: image/png" ${SLOT_URL}?${SLOT_QRYR}${QSITE}
      if [ $? -ne 0 ]; then
         /bin/sleep 3
         /bin/rm -f ${PLOT_DIR}/${SITE}_running.png 1>/dev/null 2>&1
         echo "failed to get ${SITE} running job plot from dashboard" >> ${ERR_FILE}
         /usr/bin/wget -O ${PLOT_DIR}/${SITE}_running.png --timeout=900 --no-check-certificate --header="Authorization: Bearer eyJrIjxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxOjExfQ==" --header="Accept: image/png" ${SLOT_URL}?${SLOT_QRYR}${QSITE} 1> ${ERR_FILE} 2>&1
         RCX=$?
         if [ ${RCX} -ne 0 ]; then
            echo "wget retry failed too, rc=${RCX}" >> ${ERR_FILE}
            echo "" >> ${ERR_FILE}
            if [ ${RC} -eq 0 ]; then
               RC=${RCX}
            fi
            /bin/rm -f ${PLOT_DIR}/${SITE}_running.png 1>/dev/null 2>&1
         else
            echo "succeeded on second attempt" >> ${ERR_FILE}
            echo "" >> ${ERR_FILE}
         fi
      fi
   else
      echo "${SITE}_running.png exists, skipping"
   fi
   if [ ! -f ${PLOT_DIR}/${SITE}_pending.png ]; then
      /usr/bin/wget -O ${PLOT_DIR}/${SITE}_pending.png --timeout=900 --no-check-certificate --header="Authorization: Bearer eyJrIjxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxOjExfQ==" --header="Accept: image/png" ${SLOT_URL}?${SLOT_QRYP}${QSITE}
      if [ $? -ne 0 ]; then
         /bin/sleep 3
         /bin/rm -f ${PLOT_DIR}/${SITE}_pending.png 1>/dev/null 2>&1
         echo "failed to get ${SITE} pending job plot from dashboard" >> ${ERR_FILE}
         /usr/bin/wget -O ${PLOT_DIR}/${SITE}_pending.png --timeout=900 --no-check-certificate --header="Authorization: Bearer eyJrIjxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxOjExfQ==" --header="Accept: image/png" ${SLOT_URL}?${SLOT_QRYP}${QSITE} 1> ${ERR_FILE} 2>&1
         RCX=$?
         if [ ${RCX} -ne 0 ]; then
            echo "wget retry failed too, rc=${RCX}" >> ${ERR_FILE}
            echo "" >> ${ERR_FILE}
            if [ ${RC} -eq 0 ]; then
               RC=${RCX}
            fi
            /bin/rm -f ${PLOT_DIR}/${SITE}_pending.png 1>/dev/null 2>&1
         else
            echo "succeeded on second attempt" >> ${ERR_FILE}
            echo "" >> ${ERR_FILE}
         fi
      fi
   else
      echo "${SITE}_pending.png exists, skipping"
   fi
done
# #############################################################################



# get Site Readiness Report web page as PNG file:
# -----------------------------------------------
/usr/bin/xvfb-run --server-args="-screen 0, 1600x1200x24" /data/cmssst/CutyCapt/cutycapt-code-r10-CutyCapt/CutyCapt --insecure --url=http://cmssst.web.cern.ch/sitereadiness/report.html --out=${TMP_FILE}
if [ $? -ne 0 ]; then
   /bin/sleep 3
   /bin/rm -f ${TMP_FILE} 1>/dev/null 2>&1
   echo "failed to get site readiness report web page as png" >> ${ERR_FILE}
   /usr/bin/xvfb-run --server-args="-screen 0, 1600x1200x24" /data/cmssst/CutyCapt/cutycapt-code-r10-CutyCapt/CutyCapt --insecure --url=http://cmssst.web.cern.ch/sitereadiness/report.html --out=${TMP_FILE} 1> ${ERR_FILE} 2>&1
   RCX=$?
   if [ ${RCX} -ne 0 ]; then
      echo "CutyCapt retry failed too, rc=${RCX}" >> ${ERR_FILE}
      echo "" >> ${ERR_FILE}
      if [ ${RC} -eq 0 ]; then
         RC=${RCX}
      fi
      /bin/rm -f ${TMP_FILE} 1>/dev/null 2>&1
   else
      echo "succeeded on second attempt" >> ${ERR_FILE}
      echo "" >> ${ERR_FILE}
   fi
fi
#
# now cut out Tier-1 and Tier-2 CERN images:
if [ -f ${TMP_FILE} ]; then
   if [ ! -f ${PLOT_DIR}/T2_CH_CERN_sr.png ]; then
      /usr/bin/convert -crop 1086x448+7+689 ${TMP_FILE} ${PLOT_DIR}/T1_DE_KIT_sr.png
      /usr/bin/convert -crop 1086x448+7+1225 ${TMP_FILE} ${PLOT_DIR}/T1_ES_PIC_sr.png
      /usr/bin/convert -crop 1086x448+7+1761 ${TMP_FILE} ${PLOT_DIR}/T1_FR_CCIN2P3_sr.png
      /usr/bin/convert -crop 1086x448+7+2297 ${TMP_FILE} ${PLOT_DIR}/T1_IT_CNAF_sr.png
      /usr/bin/convert -crop 1086x448+7+2833 ${TMP_FILE} ${PLOT_DIR}/T1_RU_JINR_sr.png
      /usr/bin/convert -crop 1086x448+7+3369 ${TMP_FILE} ${PLOT_DIR}/T1_UK_RAL_sr.png
      /usr/bin/convert -crop 1086x448+7+3905 ${TMP_FILE} ${PLOT_DIR}/T1_US_FNAL_sr.png
      /usr/bin/convert -crop 1086x448+7+7121 ${TMP_FILE} ${PLOT_DIR}/T2_CH_CERN_sr.png
   else
      echo "t1_de_kit/pic/ccin2p3/cnaf/jinr/ral/fnal/cern.png exist, skipping"
   fi
   /bin/rm ${TMP_FILE}
fi

/usr/bin/xvfb-run --server-args="-screen 0, 1600x1200x24" /data/cmssst/CutyCapt/cutycapt-code-r10-CutyCapt/CutyCapt --insecure --url=http://cmssst.web.cern.ch/sitereadiness/sum_report.html --out=${TMP_FILE}
if [ $? -ne 0 ]; then
   /bin/sleep 3
   /bin/rm -f ${TMP_FILE} 1>/dev/null 2>&1
   echo "failed to get site readiness summary report page as png" >> ${ERR_FILE}
   /usr/bin/xvfb-run --server-args="-screen 0, 1600x1200x24" /data/cmssst/CutyCapt/cutycapt-code-r10-CutyCapt/CutyCapt --insecure --url=http://cmssst.web.cern.ch/sitereadiness/sum_report.html --out=${TMP_FILE} 1> ${ERR_FILE} 2>&1
   RCX=$?
   if [ ${RCX} -ne 0 ]; then
      echo "CutyCapt retry failed too, rc=${RCX}" >> ${ERR_FILE}
      echo "" >> ${ERR_FILE}
      if [ ${RC} -eq 0 ]; then
         RC=${RCX}
      fi
      /bin/rm -f ${TMP_FILE} 1>/dev/null 2>&1
   else
      echo "succeeded on second attempt" >> ${ERR_FILE}
      echo "" >> ${ERR_FILE}
   fi
fi
#
# now cut out Tier-2 image:
if [ -f ${TMP_FILE} ]; then
   if [ ! -f ${PLOT_DIR}/T2_sr.png ]; then
      /usr/bin/convert -crop 1150x1314+7+365 ${TMP_FILE} ${PLOT_DIR}/T2_sr.png
   else
      echo "T2_sr.png exist, skipping"
   fi
   /bin/rm ${TMP_FILE}
fi
/usr/bin/chmod go+r ${PLOT_DIR}/*.png ${PLOT_DIR}/.time*
# #############################################################################



if [ ${RC} -ne 0 ]; then
   if [ ! -t 0 ]; then
      /usr/bin/Mail -s "$0 failed" ${EMAIL_ADDR} < ${ERR_FILE}
   else
      echo "error log:"
      echo "=========="
      /bin/cat ${ERR_FILE}
   fi
else
   echo "plots for meeting successfully created"
   /bin/mv ${PLOT_DIR}/.timetrial ${PLOT_DIR}/.timestamp
   #
   # save plots:
   # -----------
   if [ ! -e ${PLOT_DIR}/${THIS_WEEK} ]; then
      echo "Saving plots for this week, ${THIS_WEEK}"
      /bin/mkdir ${PLOT_DIR}/${THIS_WEEK}
      /bin/cp -p ${PLOT_DIR}/*.png ${PLOT_DIR}/.time* ${PLOT_DIR}/${THIS_WEEK}
   fi
fi
/bin/rm ${ERR_FILE} 1>/dev/null 2>&1
# #############################################################################



# delete old plots of previous weeks:
# -----------------------------------
PAST_WEEKS=`/usr/bin/awk 'BEGIN{tis=systime();for(pwk=6;pwk<=10;pwk+=1){wis=tis-pwk*7*24*60*60;print strftime("%Y.%U",wis)}}'`
(cd ${PLOT_DIR}; /bin/rm -r ${PAST_WEEKS} 1>/dev/null 2>&1)
PAST_WEEKS=""
# #############################################################################



# release space_mon lock:
# -----------------------
echo "Releasing lock for cmssst/meet_plots"
/bin/rm ${EXC_LOCK}
EXC_LOCK=""
# #############################################################################


exit ${RC}
