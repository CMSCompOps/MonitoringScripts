#!/bin/sh
# #############################################################################
# Bourne shell script to wrapper the VO-feed python script. It acquires an
#    execution lock, checks there is a valid grid certificate, Kerberos ticket,
#    AFS token and then launches the Python script.
# #############################################################################
EXC_LOCK=""
ERR_FILE="/tmp/cmssst_vofeed_$$.err"
trap 'exit 1' 1 2 3 15
trap '(/bin/rm -f ${EXC_LOCK} ${ERR_FILE}) 1> /dev/null 2>&1' 0



EMAIL_ADDR="lammel@fnal.gov"
CACHE_DIR="/data/cmssst/MonitoringScripts/vofeed/cache"
#
#
/bin/rm -f ${ERR_FILE} 1>/dev/null 2>&1
# #############################################################################



# get cmssst/vofeed_wrapper lock:
# ===============================
echo "Acquiring lock for cmssst/vofeed_wrapper"
if [ ! -d /var/tmp/cmssst ]; then
   /bin/rm -f /var/tmp/cmssst 1>/dev/null 2>&1
   /bin/mkdir /var/tmp/cmssst 1>/dev/null 2>&1
fi
/bin/ln -s $$ /var/tmp/cmssst/vofeed_wrapper.lock
if [ $? -ne 0 ]; then
   # locking failed, get lock information
   LKINFO=`/bin/ls -il /var/tmp/cmssst/vofeed_wrapper.lock 2>/dev/null`
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
   /bin/ln -s $$ /var/tmp/cmssst/vofeed_wrapper.lock
   if [ $? -ne 0 ]; then
      echo "   failed to acquire lock, exiting"
      exit 1
   fi
fi
#
# double check we have the lock
LKPID=`(/bin/ls -l /var/tmp/cmssst/vofeed_wrapper.lock | /usr/bin/awk '{if($(NF-1)=="->")print $NF;else print "";exit}') 2>/dev/null`
if [ "${LKPID}" != "$$" ]; then
   echo "   lost lock to process ${LKPID}, exiting"
   exit 1
fi
LKPID=""
EXC_LOCK="/var/tmp/cmssst/vofeed_wrapper.lock"
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



# generate VO-feed from SiteDB, PhEDEx and Glide-in WMS factory information:
# ==========================================================================
`dirname $0`/vofeed.py
# #############################################################################



# check for expired caches and email alerts:
# ==========================================
NOW=`/bin/date '+%s'`
for FILE in ${CACHE_DIR}/cache_*.*; do
   ALRT=`/usr/bin/stat -c %Y ${FILE} | awk -v n=${NOW} '{a=int((n-$1)/3600);if((a>24)&&(a%24==1)){print 1}else{print 0}}'`
   if [ ${ALRT} -ne 0 ]; then
       /bin/touch ${ERR_FILE}
       echo "" 1>> ${ERR_FILE}
       echo "cache expired:" 1>> ${ERR_FILE}
       /bin/ls -l ${FILE} 1>> ${ERR_FILE}
   fi
done
if [ -f ${ERR_FILE} ]; then
   /bin/cat ${ERR_FILE}
   if [ ! -t 0 ]; then
      /usr/bin/Mail -s "$0 expired cache" ${EMAIL_ADDR} < ${ERR_FILE}
   fi
fi
/bin/rm ${ERR_FILE} 1>/dev/null 2>&1
# #############################################################################



# release cmssst/vofeed_wrapper lock:
# ===================================
echo "Releasing lock for cmssst/vofeed_wrapper"
/bin/rm ${EXC_LOCK}
EXC_LOCK=""
# #############################################################################


exit ${RC}
