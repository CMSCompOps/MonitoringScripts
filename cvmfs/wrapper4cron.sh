#!/bin/sh
# #############################################################################
# Bourne shell script to wrapper the CVMFS manifest script. It acquires an
#    execution lock, checks there is a valid Kerberos ticket, AFS token, and
#    then launches the Bourne shell script.
# #############################################################################
EXC_LOCK=""
ERR_FILE="/tmp/cmssst_cvmfs_$$.err"
trap 'exit 1' 1 2 3 15
trap '(/bin/rm -f ${EXC_LOCK} ${ERR_FILE}) 1> /dev/null 2>&1' 0



EMAIL_ADDR="lammel@fnal.gov"
#
#
/bin/rm -f ${ERR_FILE} 1>/dev/null 2>&1
# #############################################################################



# get cmssst/cvmfs_wrapper lock:
# ==============================
echo "Acquiring lock for cmssst/cvmfs_wrapper"
if [ ! -d /var/tmp/cmssst ]; then
   /bin/rm -f /var/tmp/cmssst 1>/dev/null 2>&1
   /bin/mkdir /var/tmp/cmssst 1>/dev/null 2>&1
fi
/bin/ln -s $$ /var/tmp/cmssst/cvmfs_wrapper.lock
if [ $? -ne 0 ]; then
   # locking failed, get lock information
   LKINFO=`/bin/ls -il /var/tmp/cmssst/cvmfs_wrapper.lock 2>/dev/null`
   LKFID=`echo ${LKINFO} | /usr/bin/awk '{print $1; exit}' 2>/dev/null`
   LKPID=`echo ${LKINFO} | /usr/bin/awk '{print $NF;exit}' 2>/dev/null`
   # check process holding lock is still active
   /bin/ps -fp ${LKPID} 1>/dev/null 2>&1
   if [ $? -eq 0 ]; then
      # get age of lock:
      MYNOW=`/bin/date +'%s' 2>/dev/null`
      MYLKF=`/bin/date +'%s' -r /var/tmp/cmssst/cvmfs_wrapper.lock 2>/dev/null`
      MYAGE=`echo "(${MYNOW} - ${MYLKF}) / 3600" | /usr/bin/bc`
      MYMSG=`echo "${MYAGE} % 24" | /usr/bin/bc`
      #
      MSG="active process ${LKPID} holds lock since ${MYAGE} hours, exiting"
      if [ -t 0 ]; then
         echo "   ${MSG}"
      elif [ ${MYAGE} -eq 6 ]; then
         /usr/bin/Mail -s "$0 ${MSG}" ${EMAIL_ADDR} < /dev/null
      fi
      exit 1
   fi
   echo "   removing leftover lock: ${LKINFO}"
   /usr/bin/find /var/tmp/cmssst -inum ${LKFID} -exec /bin/rm -f {} \;
   LKPID=""
   LKFID=""
   LKINFO=""
   #
   /bin/ln -s $$ /var/tmp/cmssst/cvmfs_wrapper.lock
   if [ $? -ne 0 ]; then
      echo "   failed to acquire lock, exiting"
      exit 1
   fi
fi
#
# double check we have the lock
LKPID=`(/bin/ls -l /var/tmp/cmssst/cvmfs_wrapper.lock | /usr/bin/awk '{if($(NF-1)=="->")print $NF;else print "";exit}') 2>/dev/null`
if [ "${LKPID}" != "$$" ]; then
   echo "   lost lock to process ${LKPID}, exiting"
   exit 1
fi
LKPID=""
EXC_LOCK="/var/tmp/cmssst/cvmfs_wrapper.lock"
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



# bind EOS fuse session:
# ======================
/usr/bin/eosfusebind -g
# #############################################################################



# fetch .cvmfspublished files and write revisions summary file:
# =============================================================
`/usr/bin/dirname $0`/cvmfs_manifest.sh
# #############################################################################



# release cmssst/cvmfs_wrapper lock:
# ==================================
echo "Releasing lock for cmssst/cvmfs_wrapper"
/bin/rm ${EXC_LOCK}
EXC_LOCK=""
# #############################################################################


exit ${RC}
