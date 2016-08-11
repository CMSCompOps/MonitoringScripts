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



# apply manual override to primal Life Status:
# ============================================
PRIMAL_FILE=${DASHB_STEM}/lifestatus/primalLifeStatus.txt
MANUAL_FILE=${DASHB_STEM}/man_override/lifestatus/manualLifeStatus.txt
DASHB_FILE=${DASHB_STEM}/lifestatus/LifeStatus.txt


# check if an update is required:
# -------------------------------
if [ ! -f ${DASHB_FILE} -o ${PRIMAL_FILE} -nt ${DASHB_FILE} \
                        -o ${MANUAL_FILE} -nt ${DASHB_FILE} ]; then
   echo "Life Status update required:"

   # write metric text file header:
   # ------------------------------
   /bin/cp /dev/null ${DASHB_FILE}_new 2> ${ERR_FILE}
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
   echo "# Site Support Team, Life Status Metric" 1>> ${DASHB_FILE}_new
   echo "#    written at `/bin/date -u '+%Y-%b-%d %H:%M:%S UTC'` by $0" 1>> ${DASHB_FILE}_new
   echo "#    in account `/usr/bin/whoami` on node `/bin/hostname`" 1>> ${DASHB_FILE}_new
   echo "#    maintained by cms-comp-ops-site-support-team@cern.ch" 1>> ${DASHB_FILE}_new
   echo "#    https://twiki.cern.ch/twiki/bin/view/CMS/SiteSupportSiteStatusSiteReadiness" 1>> ${DASHB_FILE}_new
   echo "# =======================================================" 1>> ${DASHB_FILE}_new
   echo "#" 1>> ${DASHB_FILE}_new
   TODAY=`/bin/date -u '+%Y-%m-%d %H:%M:%S'`
   URL_M='https://twiki.cern.ch/twiki/bin/view/CMSPublic/ManualOverride'
   URL_P='https://twiki.cern.ch/twiki/bin/view/CMS/SiteSupportSiteStatusSiteReadiness'


   # get list of sites in manual override and primal file:
   # -----------------------------------------------------
   SITE_LIST=`(/usr/bin/awk '{i=index($0,"#");if(i>0){s=substr($0,1,i-1)}else{s=$0};n=split(s,a,"\t");if(n>=4)print a[2]}' ${MANUAL_FILE} ${PRIMAL_FILE} | /bin/sort -u) 2>/dev/null`


   # loop over sites and set Life Status based on manual override or primal:
   # -----------------------------------------------------------------------
   for SITE in ${SITE_LIST}; do
      # check for override entry:
      MANUAL=`/usr/bin/awk -v site="${SITE}" '{i=index($0,"#");if(i>0){s=substr($0,1,i-1)}else{s=$0};n=split(s,a,"\t");if(a[2]==site)print a[3]}' ${MANUAL_FILE} 2>/dev/null`
      #
      if [ "${MANUAL}" = "enabled" -o "${MANUAL}" = "OK" ]; then
         # site Life Status manually overridden to "enabled"
         echo -e "${TODAY}\t${SITE}\tenabled\tgreen\t${URL_M}" >> ${DASHB_FILE}_new
         #
      elif [ "${MANUAL}" = "waiting_room" -o "${MANUAL}" = "Waiting_Room" ]; then
         # site Life Status manually overridden to "waiting_room"
         echo -e "${TODAY}\t${SITE}\twaiting_room\tyellow\t${URL_M}" >> ${DASHB_FILE}_new
         #
      elif [ "${MANUAL}" = "morgue" -o "${MANUAL}" = "Morgue" ]; then
         # site Life Status manually overridden to "morgue"
         echo -e "${TODAY}\t${SITE}\tmorgue\tred\t${URL_M}" >> ${DASHB_FILE}_new
         #
      else
         # no or unknown manual override status, use primal status:
         PRIMAL=`/usr/bin/awk -v site="${SITE}" '{i=index($0,"#");if(i>0){s=substr($0,1,i-1)}else{s=$0};n=split(s,a,"\t");if(a[2]==site)print a[3]}' ${PRIMAL_FILE} 2>/dev/null`
         #
         if [ "${PRIMAL}" = "enabled" -o "${PRIMAL}" = "OK" ]; then
            echo -e "${TODAY}\t${SITE}\tenabled\tgreen\t${URL_P}" >> ${DASHB_FILE}_new
            #
         elif [ "${PRIMAL}" = "waiting_room" -o "${PRIMAL}" = "Waiting_Room" ]; then
            echo -e "${TODAY}\t${SITE}\twaiting_room\tyellow\t${URL_P}" >> ${DASHB_FILE}_new
            #
         elif [ "${PRIMAL}" = "morgue" -o "${PRIMAL}" = "Morgue" ]; then
            echo -e "${TODAY}\t${SITE}\tmorgue\tred\t${URL_P}" >> ${DASHB_FILE}_new
            #
         else
            MSG="illegal status \"${PRIMAL}\" in primal LifeStatus for ${SITE}"
            echo "   ${MSG}"
            if [ ! -t 0 ]; then
               /usr/bin/Mail -s "$0 ${MSG}" ${EMAIL_ADDR} < ${PRIMAL_FILE}
            fi
         fi
      fi
   done
   
   
   # update metric text file:
   # ------------------------
   /bin/chmod a+r ${DASHB_FILE}_new
   /bin/mv ${DASHB_FILE}_new ${DASHB_FILE}


   INPUT_FILE=${DASHB_FILE}
   #
   #
   # write a revised active Tier-2 metric file:
   # ------------------------------------------
   DASHB_FILE=${DASHB_STEM}/lifestatus/activeT2s.txt
   /bin/cp /dev/null ${DASHB_FILE}_new 2> ${ERR_FILE}
   RC=$?
   if [ ${RC} -ne 0 ]; then
      MSG="failed to create new activeT2s metric file, cp=${RC}"
      echo "   ${MSG}"
      if [ ! -t 0 ]; then
         /usr/bin/Mail -s "$0 ${MSG}" ${EMAIL_ADDR} < ${ERR_FILE}
      fi
      exit ${RC}
   fi
   echo "#txt" 1>> ${DASHB_FILE}_new
   echo "#" 1>> ${DASHB_FILE}_new
   echo "# Site Support Team, Active Tier-2s Metric" 1>> ${DASHB_FILE}_new
   echo "#    written at `/bin/date -u '+%Y-%b-%d %H:%M:%S UTC'` by $0" 1>> ${DASHB_FILE}_new
   echo "#    in account `/usr/bin/whoami` on node `/bin/hostname`" 1>> ${DASHB_FILE}_new
   echo "#    maintained by cms-comp-ops-site-support-team@cern.ch" 1>> ${DASHB_FILE}_new
   echo "#    https://twiki.cern.ch/twiki/bin/view/CMS/SiteSupportSiteStatusSiteReadiness" 1>> ${DASHB_FILE}_new
   echo "# =======================================================" 1>> ${DASHB_FILE}_new
   echo "#" 1>> ${DASHB_FILE}_new
   #
   # get list of enabled Tier-2 sites in Life Status:
   SITE_LIST=`/usr/bin/awk '{i=index($0,"#");if(i>0){s=substr($0,1,i-1)}else{s=$0};n=split(s,a,"\t");if(n>=4){if((index(a[2],"T2_")==1)&&(a[3]=="enabled"))print a[2]}}' ${INPUT_FILE} 2>/dev/null`
   for SITE in ${SITE_LIST}; do
      echo -e "${TODAY}\t${SITE}\t1\tgreen\thttps://twiki.cern.ch/twiki/bin/view/CMSPublic/CurrentWaitingRoomAndMorgue" >> ${DASHB_FILE}_new
   done
   #
   /bin/chmod a+r ${DASHB_FILE}_new
   /bin/mv ${DASHB_FILE}_new ${DASHB_FILE}
   #
   #
   # write a revised Waiting Room metric file:
   # ------------------------------------------
   DASHB_FILE=${DASHB_STEM}/lifestatus/waitingRoom.txt
   /bin/cp /dev/null ${DASHB_FILE}_new 2> ${ERR_FILE}
   RC=$?
   if [ ${RC} -ne 0 ]; then
      MSG="failed to create new Waiting Room metric file, cp=${RC}"
      echo "   ${MSG}"
      if [ ! -t 0 ]; then
         /usr/bin/Mail -s "$0 ${MSG}" ${EMAIL_ADDR} < ${ERR_FILE}
      fi
      exit ${RC}
   fi
   echo "#txt" 1>> ${DASHB_FILE}_new
   echo "#" 1>> ${DASHB_FILE}_new
   echo "# Site Support Team, Waiting Room Metric" 1>> ${DASHB_FILE}_new
   echo "#    written at `/bin/date -u '+%Y-%b-%d %H:%M:%S UTC'` by $0" 1>> ${DASHB_FILE}_new
   echo "#    in account `/usr/bin/whoami` on node `/bin/hostname`" 1>> ${DASHB_FILE}_new
   echo "#    maintained by cms-comp-ops-site-support-team@cern.ch" 1>> ${DASHB_FILE}_new
   echo "#    https://twiki.cern.ch/twiki/bin/view/CMS/SiteSupportSiteStatusSiteReadiness" 1>> ${DASHB_FILE}_new
   echo "# =======================================================" 1>> ${DASHB_FILE}_new
   echo "#" 1>> ${DASHB_FILE}_new
   #
   # get list of Waiting Room sites in Life Status:
   SITE_LIST=`/usr/bin/awk '{i=index($0,"#");if(i>0){s=substr($0,1,i-1)}else{s=$0};n=split(s,a,"\t");if(n>=4)print a[2]}' ${INPUT_FILE} 2>/dev/null`
   for SITE in ${SITE_LIST}; do
      STATUS=`/usr/bin/awk -v site="${SITE}" '{i=index($0,"#");if(i>0){s=substr($0,1,i-1)}else{s=$0};n=split(s,a,"\t");if(a[2]==site)print a[3]}' ${INPUT_FILE} 2>/dev/null`
      if [ "${STATUS}" = "enabled" ]; then
         echo -e "${TODAY}\t${SITE}\tout\tgreen\thttps://twiki.cern.ch/twiki/bin/view/CMSPublic/CurrentWaitingRoomAndMorgue" >> ${DASHB_FILE}_new
      else
         echo -e "${TODAY}\t${SITE}\tin\tred\thttps://twiki.cern.ch/twiki/bin/view/CMSPublic/CurrentWaitingRoomAndMorgue" >> ${DASHB_FILE}_new
      fi
   done
   #
   /bin/chmod a+r ${DASHB_FILE}_new
   /bin/mv ${DASHB_FILE}_new ${DASHB_FILE}
   #
   #
   # write a revised Morgue metric file:
   # ------------------------------------------
   DASHB_FILE=${DASHB_STEM}/lifestatus/morgue.txt
   /bin/cp /dev/null ${DASHB_FILE}_new 2> ${ERR_FILE}
   RC=$?
   if [ ${RC} -ne 0 ]; then
      MSG="failed to create new Morgue metric file, cp=${RC}"
      echo "   ${MSG}"
      if [ ! -t 0 ]; then
         /usr/bin/Mail -s "$0 ${MSG}" ${EMAIL_ADDR} < ${ERR_FILE}
      fi
      exit ${RC}
   fi
   echo "#txt" 1>> ${DASHB_FILE}_new
   echo "#" 1>> ${DASHB_FILE}_new
   echo "# Site Support Team, Morgue Metric" 1>> ${DASHB_FILE}_new
   echo "#    written at `/bin/date -u '+%Y-%b-%d %H:%M:%S UTC'` by $0" 1>> ${DASHB_FILE}_new
   echo "#    in account `/usr/bin/whoami` on node `/bin/hostname`" 1>> ${DASHB_FILE}_new
   echo "#    maintained by cms-comp-ops-site-support-team@cern.ch" 1>> ${DASHB_FILE}_new
   echo "#    https://twiki.cern.ch/twiki/bin/view/CMS/SiteSupportSiteStatusSiteReadiness" 1>> ${DASHB_FILE}_new
   echo "# =======================================================" 1>> ${DASHB_FILE}_new
   echo "#" 1>> ${DASHB_FILE}_new
   #
   # get list of Morgue sites in Life Status:
   SITE_LIST=`/usr/bin/awk '{i=index($0,"#");if(i>0){s=substr($0,1,i-1)}else{s=$0};n=split(s,a,"\t");if(n>=4)print a[2]}' ${INPUT_FILE} 2>/dev/null`
   for SITE in ${SITE_LIST}; do
      STATUS=`/usr/bin/awk -v site="${SITE}" '{i=index($0,"#");if(i>0){s=substr($0,1,i-1)}else{s=$0};n=split(s,a,"\t");if(a[2]==site)print a[3]}' ${INPUT_FILE} 2>/dev/null`
      if [ "${STATUS}" = "morgue" ]; then
         echo -e "${TODAY}\t${SITE}\tin\tred\thttps://twiki.cern.ch/twiki/bin/view/CMSPublic/CurrentWaitingRoomAndMorgue" >> ${DASHB_FILE}_new
      else
         echo -e "${TODAY}\t${SITE}\tout\tgreen\thttps://twiki.cern.ch/twiki/bin/view/CMSPublic/CurrentWaitingRoomAndMorgue" >> ${DASHB_FILE}_new
      fi
   done
   #
   /bin/chmod a+r ${DASHB_FILE}_new
   /bin/mv ${DASHB_FILE}_new ${DASHB_FILE}

fi
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
   echo "Prod Status update required:"

   # write metric text file header:
   # ------------------------------
   /bin/cp /dev/null ${DASHB_FILE}_new 2> ${ERR_FILE}
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
   echo "#    written at `/bin/date -u '+%Y-%b-%d %H:%M:%S UTC'` by $0" 1>> ${DASHB_FILE}_new
   echo "#    in account `/usr/bin/whoami` on node `/bin/hostname`" 1>> ${DASHB_FILE}_new
   echo "#    maintained by cms-comp-ops-site-support-team@cern.ch" 1>> ${DASHB_FILE}_new
   echo "#    https://twiki.cern.ch/twiki/bin/view/CMS/SiteSupportSiteStatusSiteReadiness" 1>> ${DASHB_FILE}_new
   echo "# =======================================================" 1>> ${DASHB_FILE}_new
   echo "#" 1>> ${DASHB_FILE}_new
   TODAY=`/bin/date -u '+%Y-%m-%d %H:%M:%S'`
   URL_M='https://twiki.cern.ch/twiki/bin/view/CMSPublic/ManualOverride'
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
         # no or unknown manual override status, use primal status:
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
               /usr/bin/Mail -s "$0 ${MSG}" ${EMAIL_ADDR} < ${PRIMAL_FILE}
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



# apply manual override to primal Crab Status:
# ============================================
PRIMAL_FILE=${DASHB_STEM}/crabstatus/primalCrabStatus.txt
MANUAL_FILE=${DASHB_STEM}/man_override/crabstatus/manualCrabStatus.txt
DASHB_FILE=${DASHB_STEM}/crabstatus/CrabStatus.txt


# check if an update is required:
# -------------------------------
if [ ! -f ${DASHB_FILE} -o ${PRIMAL_FILE} -nt ${DASHB_FILE} \
                        -o ${MANUAL_FILE} -nt ${DASHB_FILE} ]; then
   echo "Crab Status update required:"

   # write metric text file header:
   # ------------------------------
   /bin/cp /dev/null ${DASHB_FILE}_new 2> ${ERR_FILE}
   RC=$?
   if [ ${RC} -ne 0 ]; then
      MSG="failed to create new Crab Status metric file, cp=${RC}"
      echo "   ${MSG}"
      if [ ! -t 0 ]; then
         /usr/bin/Mail -s "$0 ${MSG}" ${EMAIL_ADDR} < ${ERR_FILE}
      fi
      exit ${RC}
   fi
   echo "#txt" 1>> ${DASHB_FILE}_new
   echo "#" 1>> ${DASHB_FILE}_new
   echo "# Site Support Team, Crab Status Metric" 1>> ${DASHB_FILE}_new
   echo "#    written at `/bin/date -u '+%Y-%b-%d %H:%M:%S UTC'` by $0" 1>> ${DASHB_FILE}_new
   echo "#    in account `/usr/bin/whoami` on node `/bin/hostname`" 1>> ${DASHB_FILE}_new
   echo "#    maintained by cms-comp-ops-site-support-team@cern.ch" 1>> ${DASHB_FILE}_new
   echo "#    https://twiki.cern.ch/twiki/bin/view/CMS/SiteSupportSiteStatusSiteReadiness" 1>> ${DASHB_FILE}_new
   echo "# =======================================================" 1>> ${DASHB_FILE}_new
   echo "#" 1>> ${DASHB_FILE}_new
   TODAY=`/bin/date -u '+%Y-%m-%d %H:%M:%S'`
   URL_M='https://twiki.cern.ch/twiki/bin/view/CMSPublic/ManualOverride'
   URL_P='https://twiki.cern.ch/twiki/bin/view/CMS/SiteSupportSiteStatusSiteReadiness'


   # get list of sites in manual override and primal file:
   # -----------------------------------------------------
   SITE_LIST=`(/usr/bin/awk '{i=index($0,"#");if(i>0){s=substr($0,1,i-1)}else{s=$0};n=split(s,a,"\t");if(n>=4)print a[2]}' ${MANUAL_FILE} ${PRIMAL_FILE} | /bin/sort -u) 2>/dev/null`


   # loop over sites and set Crab Status based on manual override or primal:
   # -----------------------------------------------------------------------
   for SITE in ${SITE_LIST}; do
      # check for override entry:
      MANUAL=`/usr/bin/awk -v site="${SITE}" '{i=index($0,"#");if(i>0){s=substr($0,1,i-1)}else{s=$0};n=split(s,a,"\t");if(a[2]==site)print a[3]}' ${MANUAL_FILE} 2>/dev/null`
      #
      if [ "${MANUAL}" = "enabled" ]; then
         # site Crab Status manually overridden to "enabled"
         echo -e "${TODAY}\t${SITE}\tenabled\tgreen\t${URL_M}" >> ${DASHB_FILE}_new
         #
      elif [ "${MANUAL}" = "disabled" ]; then
         # site Crab Status manually overridden to "disabled"
         echo -e "${TODAY}\t${SITE}\tdisabled\tred\t${URL_M}" >> ${DASHB_FILE}_new
         #
      else
         # no or unknown manual override status, use primal status:
         PRIMAL=`/usr/bin/awk -v site="${SITE}" '{i=index($0,"#");if(i>0){s=substr($0,1,i-1)}else{s=$0};n=split(s,a,"\t");if(a[2]==site)print a[3]}' ${PRIMAL_FILE} 2>/dev/null`
         #
         if [ "${PRIMAL}" = "enabled" ]; then
            echo -e "${TODAY}\t${SITE}\tenabled\tgreen\t${URL_P}" >> ${DASHB_FILE}_new
            #
         elif [ "${PRIMAL}" = "disabled" ]; then
            echo -e "${TODAY}\t${SITE}\tdisabled\tred\t${URL_P}" >> ${DASHB_FILE}_new
            #
         else
            MSG="illegal status \"${PRIMAL}\" in primal CrabStatus for ${SITE}"
            echo "   ${MSG}"
            if [ ! -t 0 ]; then
               /usr/bin/Mail -s "$0 ${MSG}" ${EMAIL_ADDR} < ${PRIMAL_FILE}
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



# write backward compatibility analysis metric and JSON file:
# ===========================================================
DASHB_FILE=${DASHB_STEM}/crabstatus/CrabStatus.txt
ANALYSIS_JSON=${DASHB_STEM}/analysis/usableSites.json


# check if an update is required:
# -------------------------------
if [ ! -f ${ANALYSIS_JSON} -o ${DASHB_FILE} -nt ${ANALYSIS_JSON} ]; then
   echo "Analysis JSON update required:"

   # write JSON file:
   # ------------------------------
   /bin/cp /dev/null ${ANALYSIS_JSON}_new 2> ${ERR_FILE}
   RC=$?
   if [ ${RC} -ne 0 ]; then
      MSG="failed to create new Analysis metric JSON file, cp=${RC}"
      echo "   ${MSG}"
      if [ ! -t 0 ]; then
         /usr/bin/Mail -s "$0 ${MSG}" ${EMAIL_ADDR} < ${ERR_FILE}
      fi
      exit ${RC}
   fi
   TODAY=`/bin/date '+%s'`
   URL_M='https://cmssst.web.cern.ch/cmssst/analysis/usableSites.txt'


   # get list of sites in Crab Status metric file:
   # ---------------------------------------------
   SITE_LIST=`(/usr/bin/awk '{i=index($0,"#");if(i>0){s=substr($0,1,i-1)}else{s=$0};n=split(s,a,"\t");if(n>=4)print a[2]}' ${DASHB_FILE} | /bin/sort -u) 2>/dev/null`


   # loop over sites and set Analysis status based on Crab status:
   # -------------------------------------------------------------
   SEPARATOR="[\n";
   for SITE in ${SITE_LIST}; do
      # get site CRAB status:
      MANUAL=`/usr/bin/awk -v site="${SITE}" '{i=index($0,"#");if(i>0){s=substr($0,1,i-1)}else{s=$0};n=split(s,a,"\t");if(a[2]==site)print a[3]}' ${DASHB_FILE} 2>/dev/null`
      #
      if [ "${MANUAL}" = "enabled" ]; then
         # analysis status is "usable"
         echo -e "${SEPARATOR}  {\n    \"name\": \"${SITE}\",\n    \"nvalue\": null,\n    \"color\": \"green\",\n    \"value\": \"usable\",\n    \"url\": \"${URL_M}\",\n    \"date\": ${TODAY}" >> ${ANALYSIS_JSON}_new
         SEPARATOR="  },\n"
         #
      elif [ "${MANUAL}" = "disabled" ]; then
         # analysis status is "not_usable"
         echo -e "${SEPARATOR}  {\n    \"name\": \"${SITE}\",\n    \"nvalue\": null,\n    \"color\": \"red\",\n    \"value\": \"not_usable\",\n    \"url\": \"${URL_M}\",\n    \"date\": ${TODAY}" >> ${ANALYSIS_JSON}_new
         SEPARATOR="  },\n"
         #
      else
         MSG="illegal status \"${MANUAL}\" in CrabStatus for ${SITE}"
         echo "   ${MSG}"
         if [ ! -t 0 ]; then
            /usr/bin/Mail -s "$0 ${MSG}" ${EMAIL_ADDR} < ${DASHB_FILE}
         fi
      fi
   done
   echo -en "  }\n]" >> ${ANALYSIS_JSON}_new
   
   
   # update Analysis metric JSON file:
   # ---------------------------------
   /bin/chmod a+r ${ANALYSIS_JSON}_new
   /bin/mv ${ANALYSIS_JSON}_new ${ANALYSIS_JSON}
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
