#!/bin/sh
# #############################################################################
# Bourne shell script to wrapper the eval_downtime.py python script. It
#    acquires an execution lock, checks there is a valid Kerberos ticket,
#    AFS token, sets up the environment for pydoop, and then launches the
#    Python script.
# #############################################################################
EXC_LOCK=""
ERR_FILE="/tmp/cmssst_evalDownTime_$$.err"
trap 'exit 1' 1 2 3 15
trap '(/bin/rm -f ${EXC_LOCK} ${ERR_FILE}) 1> /dev/null 2>&1' 0



EMAIL_ADDR="lammel@cern.ch"
#
#
/bin/rm -f ${ERR_FILE} 1>/dev/null 2>&1
# #############################################################################



# get cmssst/evalDownTime_wrapper lock:
# ===================================
echo "Acquiring lock for cmssst/evalDownTime_wrapper"
if [ ! -d /var/tmp/cmssst ]; then
   /bin/rm -f /var/tmp/cmssst 1>/dev/null 2>&1
   /bin/mkdir /var/tmp/cmssst 1>/dev/null 2>&1
fi
/bin/ln -s $$ /var/tmp/cmssst/evalDownTime_wrapper.lock
if [ $? -ne 0 ]; then
   # locking failed, get lock information
   LKINFO=`/bin/ls -il /var/tmp/cmssst/evalDownTime_wrapper.lock 2>/dev/null`
   LKFID=`echo ${LKINFO} | /usr/bin/awk '{print $1; exit}' 2>/dev/null`
   LKPID=`echo ${LKINFO} | /usr/bin/awk '{print $NF;exit}' 2>/dev/null`
   # check process holding lock is still active
   /bin/ps -fp ${LKPID} 1>/dev/null 2>&1
   if [ $? -eq 0 ]; then
      # check data are not expired (1 hour):
      NOW=`/bin/date '+%s'`
      ALRT=`/usr/bin/stat -c %Y /data/cmssst/MonitoringScripts/downtime/cache/vofeed.xml | /usr/bin/awk -v n=${NOW} '{a=int((n-$1)/900);if((a>=4)&&(a==4)||(a%48==0))){print 1}else{print 0}}'`
      if [ ${ALRT} -ne 0 ]; then
         /bin/touch ${ERR_FILE}
         echo "" 1>> ${ERR_FILE}
         echo "data expired:" 1>> ${ERR_FILE}
         /bin/ls -l /data/cmssst/MonitoringScripts/downtime/cache 1>> ${ERR_FILE}
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
   /bin/ln -s $$ /var/tmp/cmssst/evalDownTime_wrapper.lock
   if [ $? -ne 0 ]; then
      echo "   failed to acquire lock, exiting"
      exit 1
   fi
fi
#
# double check we have the lock
LKPID=`(/bin/ls -l /var/tmp/cmssst/evalDownTime_wrapper.lock | /usr/bin/awk '{if($(NF-1)=="->")print $NF;else print "";exit}') 2>/dev/null`
if [ "${LKPID}" != "$$" ]; then
   echo "   lost lock to process ${LKPID}, exiting"
   exit 1
fi
LKPID=""
EXC_LOCK="/var/tmp/cmssst/evalDownTime_wrapper.lock"
# #############################################################################



# check Kerberos ticket and AFS token:
# ====================================
echo "Checking Kerberos ticket/AFS token lifetime:"
KRB5_LIFE=`/usr/bin/klist -c ${KRB5_FILE} | /usr/bin/awk 'BEGIN{tgt=0;afs=0} {if(index($5,"krbtgt/")==1){split($3,d,"/");if(length(d[3])<3)d[3]="20"d[3];split($4,t,":");dts=d[3]" "d[1]" "d[2]" "t[1]" "t[2]" "t[3];tgt=mktime(dts)-systime()}else{if(index($5,"afs/")==1){split($3,d,"/");if(length(d[3])<3)d[3]="20"d[3];split($4,t,":");dts=d[3]" "d[1]" "d[2]" "t[1]" "t[2]" "t[3];afs=mktime(dts)-systime()}}} END{if(afs<tgt)tgt=afs;print tgt}' 2>> ${ERR_FILE}`
RC=$?
if [ ${RC} -ne 0 ]; then
   MSG="check of Kerberos/AFS ticket lifetime failed, klist=${RC}"
   echo "   ${MSG}"
   if [ ! -t 0 ]; then
      /usr/bin/Mail -s "`/bin/basename $0` ${MSG}" ${EMAIL_ADDR} < ${ERR_FILE}
   fi
   exit ${RC}
fi
if [ ${KRB5_LIFE} -lt 7200 ]; then
   MSG="Short Kerberos ticket/AFS token lifetime, ${KRB5_LIFE} sec"
   echo "   ${MSG}"
   if [ -t 0 ]; then
      # attached terminal, prompt user to kinit for 25 hours
      /usr/bin/kinit -l 25h cmssst@CERN.CH
      if [ $? -ne 0 ]; then
         exit 1
      fi
      /usr/bin/aklog
KRB5_LIFE=`/usr/bin/klist -c ${KRB5_FILE} | /usr/bin/awk 'BEGIN{tgt=0;afs=0} {if(index($5,"krbtgt/")==1){split($3,d,"/");if(length(d[3])<3)d[3]="20"d[3];split($4,t,":");dts=d[3]" "d[1]" "d[2]" "t[1]" "t[2]" "t[3];tgt=mktime(dts)-systime()}else{if(index($5,"afs/")==1){split($3,d,"/");if(length(d[3])<3)d[3]="20"d[3];split($4,t,":");dts=d[3]" "d[1]" "d[2]" "t[1]" "t[2]" "t[3];afs=mktime(dts)-systime()}}} END{if(afs<tgt)tgt=afs;print tgt}' 2>> ${ERR_FILE}`
   else
      echo "" >> ${ERR_FILE}
      /usr/bin/klist -c ${KRB5_FILE} >> ${ERR_FILE}
      /usr/bin/Mail -s "`/bin/basename $0` ${MSG}" ${EMAIL_ADDR} < ${ERR_FILE}
      exit 1
   fi
fi
/bin/rm ${ERR_FILE} 1>/dev/null 2>&1
# #############################################################################



# evaluate downtime status and upload downtime JSON to MonIT:
# ===========================================================
`dirname $0`/eval_downtime.py -v
# #############################################################################



# release cmssst/evalHC_wrapper lock:
# =======================================
echo "Releasing lock for cmssst/evalDownTime_wrapper"
/bin/rm ${EXC_LOCK}
EXC_LOCK=""
# #############################################################################


exit ${RC}
