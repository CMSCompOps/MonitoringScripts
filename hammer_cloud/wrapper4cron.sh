#!/bin/sh
# #############################################################################
# Bourne shell script to wrapper the eval_hc.py python script. It acquires an
#    execution lock, checks there is a valid Kerberos ticket, AFS token and
#    then launches the Python script.
# #############################################################################
EXC_LOCK=""
ERR_FILE="/tmp/cmssst_evalHC_$$.err"
trap 'exit 1' 1 2 3 15
trap '(/bin/rm -f ${EXC_LOCK} ${ERR_FILE}) 1> /dev/null 2>&1' 0



EMAIL_ADDR="lammel@fnal.gov"
HC15MIN_SSB_FILE="/afs/cern.ch/user/c/cmssst/www/hammercloud/hc15min.txt"
#
#
/bin/rm -f ${ERR_FILE} 1>/dev/null 2>&1
# #############################################################################



# get cmssst/evalHC_wrapper lock:
# ===================================
echo "Acquiring lock for cmssst/evalHC_wrapper"
if [ ! -d /var/tmp/cmssst ]; then
   /bin/rm -f /var/tmp/cmssst 1>/dev/null 2>&1
   /bin/mkdir /var/tmp/cmssst 1>/dev/null 2>&1
fi
/bin/ln -s $$ /var/tmp/cmssst/evalHC_wrapper.lock
if [ $? -ne 0 ]; then
   # locking failed, get lock information
   LKINFO=`/bin/ls -il /var/tmp/cmssst/evalHC_wrapper.lock 2>/dev/null`
   LKFID=`echo ${LKINFO} | /usr/bin/awk '{print $1; exit}' 2>/dev/null`
   LKPID=`echo ${LKINFO} | /usr/bin/awk '{print $NF;exit}' 2>/dev/null`
   # check process holding lock is still active
   /bin/ps -fp ${LKPID} 1>/dev/null 2>&1
   if [ $? -eq 0 ]; then
      # check data are not expired (6 hours):
      NOW=`/bin/date '+%s'`
      ALRT=`/usr/bin/stat -c %Y ${HC15MIN_SSB_FILE} | awk -v n=${NOW} '{a=int((n-$1)/900);if((a>24)&&(a%24==1)){print 1}else{print 0}}'`
      if [ ${ALRT} -ne 0 ]; then
         /bin/touch ${ERR_FILE}
         echo "" 1>> ${ERR_FILE}
         echo "data expired:" 1>> ${ERR_FILE}
         /bin/ls -l `/usr/bin/dirname ${SMMRY_FILE}` 1>> ${ERR_FILE}
         /bin/cat ${ERR_FILE}
         if [ ! -t 0 ]; then
            /usr/bin/Mail -s "$0 expired data" ${EMAIL_ADDR} < ${ERR_FILE}
         fi
      fi
      /bin/rm ${ERR_FILE} 1>/dev/null 2>&1
      #
      echo "   active process ${LKPID} holds lock, exiting"
      exit 1
   fi
   echo "   removing leftover lock: ${LKINFO}"
   /usr/bin/find /var/tmp/cmssst -inum ${LKFID} -exec /bin/rm -f {} \;
   LKPID=""
   LKFID=""
   LKINFO=""
   #
   /bin/ln -s $$ /var/tmp/cmssst/evalHC_wrapper.lock
   if [ $? -ne 0 ]; then
      echo "   failed to acquire lock, exiting"
      exit 1
   fi
fi
#
# double check we have the lock
LKPID=`(/bin/ls -l /var/tmp/cmssst/evalHC_wrapper.lock | /usr/bin/awk '{if($(NF-1)=="->")print $NF;else print "";exit}') 2>/dev/null`
if [ "${LKPID}" != "$$" ]; then
   echo "   lost lock to process ${LKPID}, exiting"
   exit 1
fi
LKPID=""
EXC_LOCK="/var/tmp/cmssst/evalHC_wrapper.lock"
# #############################################################################



# check Kerberos ticket and AFS token:
# ====================================
echo "Checking Kerberos ticket/AFS token:"
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
/bin/rm ${ERR_FILE} 1>/dev/null 2>&1
#
/usr/bin/aklog 2> ${ERR_FILE}
RC=$?
if [ ${RC} -ne 0 ]; then
   MSG="unable to acquire AFS token, aklog=${RC}"
   echo "   ${MSG}"
   /usr/bin/Mail -s "$0 ${MSG}" ${EMAIL_ADDR} < ${ERR_FILE}
   exit ${RC}
fi
/bin/rm ${ERR_FILE} 1>/dev/null 2>&1
# #############################################################################



# evaluate Hammer Cloud results, post SSB file(s) and JSON:
# =========================================================
`dirname $0`/eval_hc.py
# #############################################################################



# release cmssst/evalHC_wrapper lock:
# =======================================
echo "Releasing lock for cmssst/evalHC_wrapper"
/bin/rm ${EXC_LOCK}
EXC_LOCK=""
# #############################################################################


exit ${RC}
