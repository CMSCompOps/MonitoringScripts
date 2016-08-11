#!/bin/sh
# #############################################################################
# Bourne shell script to query the Data and Workload Management, DMWM,
#                     monitoring web service and extract the last update
#                     time stamp for each site.
# #############################################################################
EXC_LOCK=""
TMP_FILE="/tmp/cmssst_spacemon_$$.txt"
ERR_FILE="/tmp/cmssst_spacemon_$$.err"
SDB_FILE="/tmp/cmssst_spacemon_$$.sdb"
PDX_FILE="/tmp/cmssst_spacemon_$$.pdx"
trap 'exit 1' 1 2 3 15
trap '(/bin/rm -f ${EXC_LOCK} ${TMP_FILE} ${ERR_FILE} ${SDB_FILE} ${PDX_FILE}) 1> /dev/null 2>&1' 0



SITES_URL="https://cmsweb.cern.ch/sitedb/data/prod/site-names"
NODES_URL="https://cmsweb.cern.ch/phedex/datasvc/perl/prod/nodes"
SPACE_URL="https://cmsweb.cern.ch/dmwmmon/datasvc/perl/storageusage"
DASHB_FILE="/afs/cern.ch/user/c/cmssst/www/space_mon/space_check.txt"
FILE_URL="http://cmssst.web.cern.ch/cmssst/space_mon/space_check.txt"
EMAIL_ADDR="lammel@fnal.gov"
# #############################################################################



# get cmssst/space_mon lock:
# --------------------------
echo "Acquiring lock for cmssst/space_mon"
if [ ! -d /var/tmp/cmssst ]; then
   /bin/rm -f /var/tmp/cmssst 1>/dev/null 2>&1
   /bin/mkdir /var/tmp/cmssst 1>/dev/null 2>&1
fi
/bin/ln -s $$ /var/tmp/cmssst/space_mon.lock
if [ $? -ne 0 ]; then
   # locking failed, get lock information
   LKINFO=`/bin/ls -il /var/tmp/cmssst/space_mon.lock 2>/dev/null`
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
   /bin/ln -s $$ /var/tmp/cmssst/space_mon.lock
   if [ $? -ne 0 ]; then
      echo "   failed to acquire lock, exiting"
      exit 1
   fi
fi
#
# double check we have the lock
LKPID=`(/bin/ls -l /var/tmp/cmssst/space_mon.lock | /usr/bin/awk '{if($(NF-1)=="->")print $NF;else print "";exit}') 2>/dev/null`
if [ "${LKPID}" != "$$" ]; then
   echo "   lost lock to process ${LKPID}, exiting"
   exit 1
fi
LKPID=""
EXC_LOCK="/var/tmp/cmssst/space_mon.lock"
# #############################################################################



# check Kerberos ticket and AFS token:
# ------------------------------------
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
/bin/rm ${ERR_FILE} 1>/dev/null 2>&1
/usr/bin/aklog 2> ${ERR_FILE}
RC=$?
if [ ${RC} -ne 0 ]; then
   MSG="unable to acquire AFS token, aklog=${RC}"
   echo "   ${MSG}"
   /usr/bin/Mail -s "$0 ${MSG}" ${EMAIL_ADDR} < ${ERR_FILE}
   exit ${RC}
fi


# check for certificate, needed to access the DMWM monitoring web service:
# ------------------------------------------------------------------------
echo "Checking certificate:"
/bin/rm ${ERR_FILE} 1>/dev/null 2>&1
/usr/bin/grid-proxy-info -identity -exists -valid 0:15 2> ${ERR_FILE}
RC=$?
if [ ${RC} -ne 0 ]; then
   MSG="no valid certificate, grid-proxy-info=${RC}"
   echo "   ${MSG}"
   if [ -t 0 ]; then
      # attached terminal, prompt user to grid-proxy-init for 30 days
      /usr/bin/grid-proxy-init -valid 744:0
      /usr/bin/grid-proxy-info -identity -exists -valid 0:15 2> /dev/null
      if [ $? -ne 0 ]; then
         exit ${RC}
      fi
   else
      /usr/bin/Mail -s "$0 ${MSG}" ${EMAIL_ADDR} < ${ERR_FILE}
      exit ${RC}
   fi
fi
/bin/rm ${ERR_FILE} 1>/dev/null 2>&1
CRT_FILE=`/usr/bin/grid-proxy-info -path 2> /dev/null`
WGET_OPT="--certificate=${CRT_FILE} --private-key=${CRT_FILE} --ca-certificate=${CRT_FILE}"
# #############################################################################



# write metric text file header:
# ------------------------------
/bin/cp /dev/null ${DASHB_FILE}_new
echo "#txt" 1>> ${DASHB_FILE}_new
echo "#" 1>> ${DASHB_FILE}_new
echo "# Site Support Team, Space Monitoring Metric" 1>> ${DASHB_FILE}_new
echo "#    written at `/bin/date -u '+%Y-%b-%d %H:%M:%S UTC'` by $0" 1>> ${DASHB_FILE}_new
echo "#    in account `/usr/bin/whoami` on node `/bin/hostname`" 1>> ${DASHB_FILE}_new
echo "#    maintained by cms-comp-ops-site-support-team@cern.ch" 1>> ${DASHB_FILE}_new
echo "#    https://twiki.cern.ch/twiki/bin/view/CMSPublic/CompProjSpaceMon" 1>> ${DASHB_FILE}_new
echo "# =======================================================" 1>> ${DASHB_FILE}_new
echo "#" 1>> ${DASHB_FILE}_new
TODAY=`/bin/date -u '+%Y-%m-%d %H:%M:%S'`
NOW75=`/bin/date '+%s + 4500' | /usr/bin/bc`
#echo "Using timestamp ${NOW75} for past-future boundary"
#
/bin/rm -f ${TMP_FILE} 1>/dev/null 2>&1



# get list of CMS Tier-1,2,3 sites:
# ---------------------------------
echo "Getting list of CMS sites:"
/usr/bin/wget ${WGET_OPT} -O ${TMP_FILE} ${SITES_URL} 1> ${ERR_FILE} 2>&1
RC=$?
if [ ${RC} -ne 0 ]; then
   MSG="failed to query SiteDB(site-names), wget=${RC}"
   echo "   ${MSG}"
   if [ ! -t 0 ]; then
      /usr/bin/Mail -s "$0 ${MSG}" ${EMAIL_ADDR} < ${ERR_FILE}
   fi
   exit ${RC}
fi
/bin/rm ${ERR_FILE} 1>/dev/null 2>&1
# filter out SiteName, CMS, and PhEDEx alias for Tier-1,2,3 sites:
/bin/rm ${SDB_FILE} 1>/dev/null 2>&1
/usr/bin/awk -F\" '/"cms"|"phedex"/ {if(index($6,"T3_")!=1){print $0}}' ${TMP_FILE} | /bin/sort -t\" -k 2,2 -k6,6 -u > ${SDB_FILE}
/bin/rm ${TMP_FILE}



# get PhEDEx node information:
# ----------------------------
echo "Getting PhEDEx node information:"
/usr/bin/wget ${WGET_OPT} -O ${TMP_FILE} ${NODES_URL} 1> ${ERR_FILE} 2>&1
RC=$?
if [ ${RC} -ne 0 ]; then
   echo "failed to get PhEDEx node information, wget=${RC}"
   if [ ! -t 0 ]; then
      /usr/bin/Mail -s "$0 failed with wget=${RC}" ${EMAIL_ADDR} < ${ERR_FILE}
   fi
   exit ${RC}
fi
/bin/rm ${ERR_FILE} 1>/dev/null 2>&1
# extract PhEDEx node name and type and save compact information:
/bin/rm ${PDX_FILE} 1>/dev/null 2>&1
/usr/bin/awk -F\' 'BEGIN{b=0}{for(i=1;i<=NF;i++){if(index($i,"[")>0){b+=1};if(b>0){if(index($i,"{")>0){n="";k=""};if($i=="NAME"){n=$(i+2)};if($i=="KIND"){k=$(i+2)};if(index($i,"}")>0){if(index(n,"T3_")!=1)printf "%s:%s\n",n,k};if(index($i,"]")>0){b-=1}}}}' ${TMP_FILE} > ${PDX_FILE}
/bin/rm ${TMP_FILE}



# loop over the sites and get last record for each PhEDEx node of the site:
# -------------------------------------------------------------------------
ERR_CNT=0
/bin/touch ${ERR_FILE}
SITE_LIST=`/usr/bin/awk -F\" '{if($2=="cms"){print $6}}' ${SDB_FILE}`
for SITE in ${SITE_LIST}; do
   echo "Checking PhEDEx nodes for site ${SITE}:"
   DATE_TIS=-2

   # get PhEDEx nodes of the site and loop over them to query DM/WM:
   # ---------------------------------------------------------------
   NODE_LIST=`/usr/bin/awk -F\" -vs=${SITE} 'BEGIN{n=s}{if(($2=="cms")&&($6==s)){n=$4};if(($2=="phedex")&&($4==n)){print $6}}' ${SDB_FILE}`
   for NODE in ${NODE_LIST}; do
      # check what kind of PhEDEx node it is:
      NODE_TYPE=`/usr/bin/awk -F: -vn=${NODE} 'BEGIN{k="???"}{if($1==n){k=$2}}END{print k}' ${PDX_FILE}`
      if [ "${NODE_TYPE}" = "MSS" -o "${NODE_TYPE}" = "Buffer" ]; then
         echo "   skipping ${NODE_TYPE} node ${NODE}"
         continue
      fi

      echo -n "   Checking last record for ${NODE_TYPE} node ${NODE}:"

      # get last non-future record for the PhEDEx node and extract time stamp:
      # ----------------------------------------------------------------------
      #/usr/bin/wget -O ${TMP_FILE} ${SPACE_URL}?node=${NODE}\&time_until=${NOW75} 1>> ${ERR_FILE} 2>&1
      /usr/bin/wget -O ${TMP_FILE} ${SPACE_URL}?node=${NODE} 1>> ${ERR_FILE} 2>&1
      RC=$?
      if [ ${RC} -eq 0 ]; then
         DATE_TMP=`/usr/bin/awk -F\' 'BEGIN{t=0} {if($2=="TIMESTAMP"){if($4>t)t=$4}} END{print t}' ${TMP_FILE}`
      elif [ ${RC} -eq 8 ]; then
         DATE_TMP=0
      else
         DATE_TMP=-1
         ERR_CNT=`echo "${ERR_CNT} + 1" | /usr/bin/bc`
      fi
      echo " ${DATE_TMP}"
      /bin/rm ${TMP_FILE} 1>/dev/null 2>&1
      # take the most recent date of any PhEDEx nodes of the site:
      if [ ${DATE_TMP} -gt ${DATE_TIS} ]; then
         DATE_TIS=${DATE_TMP}
         NODE_TIS=${NODE}
      fi
   done

   # evaluate time information and add site entry to metric text file:
   # -----------------------------------------------------------------
   DATE_STR=`echo "${DATE_TIS}" | /usr/bin/awk '{if($1>0){print strftime("%Y-%m-%d", int($1))}else{if($1==0){print "never"}else{if($1==-1){print "error"}else{print "N/A"}}}}'`
   DATE_CLR=`echo "${DATE_TIS}" | /usr/bin/awk '{if($1>=0){t=(systime()-$1)/86400;if(t<=31){print "green"}else{if(t<=92){print "yellow"}else{print "red"}}}else{print "white"}}'`
   #
   if [ ${DATE_TIS} -gt 0 ]; then
      echo -e "${TODAY}\t${SITE}\t${DATE_STR}\t${DATE_CLR}\t${SPACE_URL}?node=${NODE_TIS}" 1>> ${DASHB_FILE}_new
   else
      echo -e "${TODAY}\t${SITE}\t${DATE_STR}\t${DATE_CLR}\t${FILE_URL}" 1>> ${DASHB_FILE}_new
   fi
done
/bin/rm ${PDX_FILE} 1>/dev/null 2>&1
/bin/rm ${SDB_FILE} 1>/dev/null 2>&1

if [ ${ERR_CNT} -ge 3 ]; then
   MSG="many failed DM/WM-Mon(storageusage) queries"
   echo "   ${MSG}"
   if [ ! -t 0 ]; then
      /usr/bin/Mail -s "$0 ${MSG}" ${EMAIL_ADDR} < ${ERR_FILE}
   fi
fi
/bin/rm ${ERR_FILE} 1>/dev/null 2>&1



# update metric text file:
# ------------------------
/bin/chmod a+r ${DASHB_FILE}_new
/bin/mv ${DASHB_FILE}_new ${DASHB_FILE}
RC=$?
# #############################################################################



# release space_mon lock:
# -----------------------
echo "Releasing lock for cmssst/space_mon"
/bin/rm ${EXC_LOCK}
EXC_LOCK=""
# #############################################################################


exit ${RC}
