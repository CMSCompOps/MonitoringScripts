#!/bin/sh
# #############################################################################
# Bourne shell script to apply the manual overrides to the Primal metric
#                     file and write an updated metric file.
# #############################################################################
EXC_LOCK=""
TMP_FILE="/tmp/cmssst_applvrrd_$$.txt"
ERR_FILE="/tmp/cmssst_applvrrd_$$.err"
trap 'exit 1' 1 2 3 15
trap '(/bin/rm -f ${EXC_LOCK} ${TMP_FILE} ${ERR_FILE}) 1> /dev/null 2>&1' 0



DASHB_STEM="/afs/cern.ch/user/c/cmssst/www"
EMAIL_ADDR="lammel@fnal.gov"
#
#
/bin/rm -f ${ERR_FILE} 1>/dev/null 2>&1
# #############################################################################



# get cmssst/override_apply lock:
# ===============================
echo "Acquiring lock for cmssst/apply_override"
if [ ! -d /var/tmp/cmssst ]; then
   /bin/rm -f /var/tmp/cmssst 1>/dev/null 2>&1
   /bin/mkdir /var/tmp/cmssst 1>/dev/null 2>&1
fi
/bin/ln -s $$ /var/tmp/cmssst/apply_override.lock
if [ $? -ne 0 ]; then
   # locking failed, get lock information
   LKINFO=`/bin/ls -il /var/tmp/cmssst/apply_override.lock 2>/dev/null`
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
   /bin/ln -s $$ /var/tmp/cmssst/apply_override.lock
   if [ $? -ne 0 ]; then
      echo "   failed to acquire lock, exiting"
      exit 1
   fi
fi
#
# double check we have the lock
LKPID=`(/bin/ls -l /var/tmp/cmssst/apply_override.lock | /usr/bin/awk '{if($(NF-1)=="->")print $NF;else print "";exit}') 2>/dev/null`
if [ "${LKPID}" != "$$" ]; then
   echo "   lost lock to process ${LKPID}, exiting"
   exit 1
fi
LKPID=""
EXC_LOCK="/var/tmp/cmssst/apply_override.lock"
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



# apply manual override to primal Prod Status:
# ============================================
PRIMAL_FILE=${DASHB_STEM}/prodstatus/primalProdStatus.txt
MANUAL_FILE=${DASHB_STEM}/man_override/prodstatus/manualProdStatus.txt
DASHB_FILE=${DASHB_STEM}/prodstatus/ProdStatus.txt


# check if an update is required:
# -------------------------------
if [ ! -f ${DASHB_FILE} -o ${PRIMAL_FILE} -nt ${DASHB_FILE} \
                        -o ${MANUAL_FILE} -nt ${DASHB_FILE} ]; then

   # write metric text file header:
   # ------------------------------
   /bin/cp /dev/null ${DASHB_FILE}_new
   RC=$?
   if [ ${RC} -ne 0 ]; then
      MSG="failed to create new Prod Status metric file, cp=${RC}"
      echo "   ${MSG}"
      if [ ! -t 0 ]; then
         /usr/bin/Mail -s "$0 ${MSG}" ${EMAIL_ADDR} < ${ERR_FILE}
      fi
      exit ${RC}
   fi
   echo "#txt" 1>> ${DASHB_FILE}_new
   echo "#" 1>> ${DASHB_FILE}_new
   echo "# Site Support Team, Prod Status Metric" 1>> ${DASHB_FILE}_new
   echo "#    written at `/bin/date '+%Y-%b-%d %H:%M:%S'` by $0" 1>> ${DASHB_FILE}_new
   echo "#    in account `/usr/bin/whoami` on node `/bin/hostname`" 1>> ${DASHB_FILE}_new
   echo "#    maintained by cms-comp-ops-site-support-team@cern.ch" 1>> ${DASHB_FILE}_new
   echo "#    https://twiki.cern.ch/twiki/bin/view/CMSPublic/WaitingRoomMorgueAndSiteReadiness" 1>> ${DASHB_FILE}_new
   echo "# =======================================================" 1>> ${DASHB_FILE}_new
   echo "#" 1>> ${DASHB_FILE}_new
   TODAY=`/bin/date '+%Y-%m-%d %H:%M:%S'`
   URL_M='https://twiki.cern.ch/twiki/bin/view/CMS/SiteSupportSiteStatusSiteReadiness'
   URL_P='https://twiki.cern.ch/twiki/bin/view/CMS/SiteSupportSiteStatusSiteReadiness'


   # get list of sites in manual override and primal file:
   # -----------------------------------------------------
   SITE_LIST=`(/usr/bin/awk '{i=index($0,"#");if(i>0){s=substr($0,1,i-1)}else{s=$0};n=split(s,a,"\t");if(n>=4)print a[2]}' ${MANUAL_FILE} ${PRIMAL_FILE} | /bin/sort -u) 2>/dev/null`


   # loop over sites and set Prod Status based on manual override or primal:
   # -----------------------------------------------------------------------
   for SITE in ${SITE_LIST}; do
      # check for override entry:
      MANUAL=`/usr/bin/awk -v site="${SITE}" '{i=index($0,"#");if(i>0){s=substr($0,1,i-1)}else{s=$0};n=split(s,a,"\t");if(a[2]==site)print a[3]}' ${MANUAL_FILE} 2>/dev/null`
      #
      if [ "${MANUAL}" = "enabled" ]; then
         # site Prod Status manually overridden to "enabled"
         echo -e "${TODAY}\t${SITE}\tenabled\tgreen\t${URL_M}" >> ${DASHB_FILE}_new
         #
      elif [ "${MANUAL}" = "disabled" ]; then
         # site Prod Status manually overridden to "disabled"
         echo -e "${TODAY}\t${SITE}\tdisabled\tred\t${URL_M}" >> ${DASHB_FILE}_new
         #
      elif [ "${MANUAL}" = "drain" ]; then
         # site Prod Status manually overridden to "drain"
         echo -e "${TODAY}\t${SITE}\tdrain\tyellow\t${URL_M}" >> ${DASHB_FILE}_new
         #
      elif [ "${MANUAL}" = "test" ]; then
         # site Prod Status manually overridden to "test"
         echo -e "${TODAY}\t${SITE}\ttest\tyellow\t${URL_M}" >> ${DASHB_FILE}_new
         #
      else
         # no or unknown manual override ststus, use primal status:
         PRIMAL=`/usr/bin/awk -v site="${SITE}" '{i=index($0,"#");if(i>0){s=substr($0,1,i-1)}else{s=$0};n=split(s,a,"\t");if(a[2]==site)print a[3]}' ${PRIMAL_FILE} 2>/dev/null`
         #
         if [ "${PRIMAL}" = "enabled" -o "${PRIMAL}" = "on" ]; then
            echo -e "${TODAY}\t${SITE}\tenabled\tgreen\t${URL_P}" >> ${DASHB_FILE}_new
            #
         elif [ "${PRIMAL}" = "disabled" -o "${PRIMAL}" = "down" ]; then
            echo -e "${TODAY}\t${SITE}\tdisabled\tred\t${URL_P}" >> ${DASHB_FILE}_new
            #
         elif [ "${PRIMAL}" = "drain" ]; then
            echo -e "${TODAY}\t${SITE}\tdrain\tyellow\t${URL_P}" >> ${DASHB_FILE}_new
            #
         elif [ "${PRIMAL}" = "test" -o "${PRIMAL}" = "tier0" ]; then
            echo -e "${TODAY}\t${SITE}\ttest\tyellow\t${URL_P}" >> ${DASHB_FILE}_new
         else
            MSG="illegal status \"${PRIMAL}\" in primal ProdStatus for ${SITE}"
            echo "   ${MSG}"
            if [ ! -t 0 ]; then
               /usr/bin/Mail -s "$0 ${MSG}" ${EMAIL_ADDR} < ${ERR_FILE}
            fi
         fi
      fi
   done
   
   
   # update metric text file:
   # ------------------------
   /bin/chmod a+r ${DASHB_FILE}_new
   /bin/mv ${DASHB_FILE}_new ${DASHB_FILE}
   RC=$?
fi
# #############################################################################



# release space_mon lock:
# -----------------------
echo "Releasing lock for cmssst/apply_override"
/bin/rm ${EXC_LOCK}
EXC_LOCK=""
# #############################################################################


exit ${RC}
