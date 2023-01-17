#!/bin/sh
# #############################################################################
# Bourne shell script to wrapper the eval_status.py python script. It
#    acquires execution lock and then launches the Python script.
# #############################################################################
EXC_LOCK=""
trap 'exit 1' 1 2 3 15
trap '(/bin/rm -f ${EXC_LOCK}) 1> /dev/null 2>&1' 0
# #############################################################################



# get cmssst/evalSTS_wrapper lock:
# ================================
echo "Acquiring lock for cmssst/evalSTS_wrapper"
if [ ! -d /var/tmp/cmssst ]; then
   /bin/rm -f /var/tmp/cmssst 1>/dev/null 2>&1
   /bin/mkdir /var/tmp/cmssst 1>/dev/null 2>&1
fi
/bin/ln -s $$ /var/tmp/cmssst/evalSTS_wrapper.lock
if [ $? -ne 0 ]; then
   # locking failed, get lock information
   LKINFO=`/bin/ls -il /var/tmp/cmssst/evalSTS_wrapper.lock 2>/dev/null`
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
   /bin/ln -s $$ /var/tmp/cmssst/evalSTS_wrapper.lock
   if [ $? -ne 0 ]; then
      echo "   failed to acquire lock, exiting"
      exit 1
   fi
fi
#
# double check we have the lock
LKPID=`(/bin/ls -l /var/tmp/cmssst/evalSTS_wrapper.lock | /usr/bin/awk '{if($(NF-1)=="->")print $NF;else print "";exit}') 2>/dev/null`
if [ "${LKPID}" != "$$" ]; then
   echo "   lost lock to process ${LKPID}, exiting"
   exit 1
fi
LKPID=""
EXC_LOCK="/var/tmp/cmssst/evalSTS_wrapper.lock"
# #############################################################################



# evaluate Life, Prod, and Crab Status and upload JSON to MonIT:
# ==============================================================
`dirname $0`/eval_status.py -vvv
# #############################################################################



# release cmssst/evalSTS_wrapper lock:
# =======================================
echo "Releasing lock for cmssst/evalSTS_wrapper"
/bin/rm ${EXC_LOCK}
EXC_LOCK=""
# #############################################################################


exit 0
