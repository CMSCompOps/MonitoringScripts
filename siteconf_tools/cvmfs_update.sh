#!/bin/sh
# #############################################################################
# cvmfs_update.sh   Simple script to keep a SYNC_DIR area up-to-date with
#                   config files for jobs from the SITECONF repository.
#                   Script aquires a lock to prevent multiple, simultaneous
#                   executions; queries SiteDB for a list of CMS sites; fetches
#                   the commit information from the SITECONF GitLab repository;
#                   removes sites in SYNC_DIR no longer in SiteDB; updates job
#                   config files for sites where the files got updated;
#
#                   Please configure the SYNC_DIR, TMP_AREA (for temporary
#                   files during script execution), AUTH_CRT, AUTH_KEY (pem
#                   files with your cert/key), AUTH_TKN (your token in GitLab),
#                   and EMAIL_ADDR (in case of errors) before execution.
# #############################################################################
EXC_LOCK=""
TMP_AREA="/usr/scratch/???????????????????????/cvmfs_tmp"
ERR_FILE="/tmp/stcnf_$$.err"
trap 'exit 1' 1 2 3 15
trap '(/bin/rm -rf ${EXC_LOCK} ${TMP_AREA} ${ERR_FILE}) 1> /dev/null 2>&1' 0



SYNC_DIR="/usr/cvmfs/????????????????????????????????????"
AUTH_CRT="/usr/?????????????????????/.globus/usercert.pem"
AUTH_KEY="/usr/??????????????????????/.globus/userkey.pem"
AUTH_TKN="PRIVATE-TOKEN: ????????????????????"
EMAIL_ADDR="???????????????????????????@?????????????.???"
# #############################################################################



# get cvmfs/stcnf_updt lock:
# --------------------------
echo "Acquiring lock for cvmfs/stcnf_updt"
if [ ! -d /var/tmp/cmssst ]; then
   /bin/rm -f /var/tmp/cvmfs 1>/dev/null 2>&1
   /bin/mkdir /var/tmp/cvmfs 1>/dev/null 2>&1
fi
/bin/ln -s $$ /var/tmp/cvmfs/stcnf_updt.lock
if [ $? -ne 0 ]; then
   # locking failed, get lock information
   LKINFO=`/bin/ls -il /var/tmp/cvmfs/stcnf_updt.lock 2>/dev/null`
   LKFID=`echo ${LKINFO} | /usr/bin/awk '{print $1; exit}' 2>/dev/null`
   LKPID=`echo ${LKINFO} | /usr/bin/awk '{print $NF;exit}' 2>/dev/null`
   # check process holding lock is still active
   /bin/ps -fp ${LKPID} 1>/dev/null 2>&1
   if [ $? -eq 0 ]; then
      echo "   active process ${LKPID} holds lock, exiting"
      exit 1
   fi
   echo "   removing leftover lock: ${LKINFO}"
   /usr/bin/find /var/tmp/cvmfs -inum ${LKFID} -exec /bin/rm -f {} \;
   LKPID=""
   LKFID=""
   LKINFO=""
   #
   /bin/ln -s $$ /var/tmp/cvmfs/stcnf_updt.lock
   if [ $? -ne 0 ]; then
      echo "   failed to acquire lock, exiting"
      exit 1
   fi
fi
#
# double check we have the lock
LKPID=`(/bin/ls -l /var/tmp/cvmfs/stcnf_updt.lock | /usr/bin/awk '{if($(NF-1)=="->")print $NF;else print "";exit}') 2>/dev/null`
if [ "${LKPID}" != "$$" ]; then
   echo "   lost lock to process ${LKPID}, exiting"
   exit 1
fi
LKPID=""
EXC_LOCK="/var/tmp/cvmfs/stcnf_updt.lock"
# #############################################################################



/bin/rm -f ${ERR_FILE} 1>/dev/null 2>&1
#
/bin/rm -rf ${TMP_AREA} 1>/dev/null 2>&1
/bin/mkdir ${TMP_AREA} 1>${ERR_FILE} 2>&1
RC=$?
if [ ${RC} -ne 0 ]; then
   MSG="failed to create TMP_AREA, mkdir=${RC}"
   /bin/cat ${ERR_FILE}
   echo "   ${MSG}"
   if [ ! -t 0 ]; then
      /usr/bin/Mail -s "$0 ${MSG}" ${EMAIL_ADDR} < ${ERR_FILE}
   fi
   exit ${RC}
fi
/bin/rm -f ${ERR_FILE} 1>/dev/null 2>&1
#
if [ ! -d ${SYNC_DIR} ]; then
   /bin/mkdir ${SYNC_DIR} 1>${ERR_FILE} 2>&1
   RC=$?
   if [ ${RC} -ne 0 ]; then
      MSG="failed to create SYNC_DIR, mkdir=${RC}"
      /bin/cat ${ERR_FILE}
      echo "   ${MSG}"
      if [ ! -t 0 ]; then
         /usr/bin/Mail -s "$0 ${MSG}" ${EMAIL_ADDR} < ${ERR_FILE}
      fi
      exit ${RC}
   fi
fi
/bin/rm -f ${ERR_FILE} 1>/dev/null 2>&1
if [ ! -d ${SYNC_DIR}/SITECONF ]; then
   /bin/mkdir ${SYNC_DIR}/SITECONF 1>${ERR_FILE} 2>&1
   RC=$?
   if [ ${RC} -ne 0 ]; then
      MSG="failed to create SYNC_DIR/SITECONF, mkdir=${RC}"
      /bin/cat ${ERR_FILE}
      echo "   ${MSG}"
      if [ ! -t 0 ]; then
         /usr/bin/Mail -s "$0 ${MSG}" ${EMAIL_ADDR} < ${ERR_FILE}
      fi
      exit ${RC}
   fi
fi
/bin/rm -f ${ERR_FILE} 1>/dev/null 2>&1
# #############################################################################



# extract awk script:
# ===================
/bin/rm -f ${TMP_AREA}/sitedb.awk 1> /dev/null 2>&1
/bin/cat 1>${TMP_AREA}/sitedb.awk 2>${ERR_FILE} << 'EOF_sitedb.awk'
#!/bin/awk -f
BEGIN{brck=0}
{
   todo=$0
   while(length(todo)>=1){
      ob=index(todo,"[")
      cb=index(todo,"]")
      if((ob!=0)&&((cb==0)||(ob<cb))){
         brck+=1
         if(brck==2)line=substr(todo,ob+1)
         todo=substr(todo,ob+1)
      }else{
         if(cb!=0){
            todo=substr(todo,cb+1);
            if(brck==2){
               len=length(line)-length(todo)-1
               line=substr(line,0,len)
               nk=split(line,a,",")
               if(a[1]=="\"cms\""){
                  gsub(" ","",a[3]);gsub("\"","",a[3])
                  print a[3]
               }
            }
            brck-=1
         }else{
            break
         }
      }
   }
}
EOF_sitedb.awk
RC=$?
if [ ${RC} -ne 0 ]; then
   MSG="failed to write sitedb.awk, cat=${RC}"
   /bin/cat ${ERR_FILE}
   echo "   ${MSG}"
   if [ ! -t 0 ]; then
      /usr/bin/Mail -s "$0 ${MSG}" ${EMAIL_ADDR} < ${ERR_FILE}
   fi
   exit ${RC}
fi
/bin/rm ${ERR_FILE} 1>/dev/null 2>&1
#
/bin/rm -f ${TMP_AREA}/gitlab.awk 1> /dev/null 2>&1
/bin/cat 1>${TMP_AREA}/gitlab.awk 2>${ERR_FILE} << 'EOF_gitlab.awk'
#!/bin/awk -f
BEGIN{now=systime();brcs=0}
{
   todo=$0
   while(length(todo)>=1){
      ob=index(todo,"{")
      cb=index(todo,"}")
      if((ob!=0)&&((cb==0)||(ob<cb))){
         brcs+=1
         if(brcs==1){site="";last=now;keys=substr(todo,ob+1);sobj=0}
         if(brcs==2)sobj=ob
         todo=substr(todo,ob+1)
      }else{
         if(cb!=0){
            todo=substr(todo,cb+1);
            if(brcs==1){
               len=length(keys)-length(todo)-1
               if(sobj==0){
                  keys=substr(keys,0,len)
               }else{
                  key1=substr(keys,0,sobj)
                  key2=substr(keys,eobj,len-eobj+1)
                  keys=(key1 key2)
               }
               nk=split(keys,a,",")
               for(i=nk;i>0;i-=1){
                  if(index(a[i],"\"name\":")>0){
                     site=substr(a[i],8)
                     gsub("\"","",site)
                  }
                  if(index(a[i],"\"last_activity_at\":")>0){
                     ts=substr(a[i],21,19)
                     gsub("-"," ",ts);gsub("T"," ",ts);gsub(":"," ",ts)
                     tzn=substr(a[i],44,3)
                     last=mktime(ts)-3600*tzn
                  }
               }
               if(site!="")printf "%s:%s\n",site,last
            }
            if(brcs==2)eobj=length(keys)-length(todo)
            brcs-=1
         }else{
            break
         }
      }
   }
}
EOF_gitlab.awk
RC=$?
if [ ${RC} -ne 0 ]; then
   MSG="failed to write gitlab.awk, cat=${RC}"
   /bin/cat ${ERR_FILE}
   echo "   ${MSG}"
   if [ ! -t 0 ]; then
      /usr/bin/Mail -s "$0 ${MSG}" ${EMAIL_ADDR} < ${ERR_FILE}
   fi
   exit ${RC}
fi
/bin/rm ${ERR_FILE} 1>/dev/null 2>&1
# #############################################################################



# get list of CMS sites:
# ======================
echo "Fetching list of CMS sites..."
SITES_URL="https://cmsweb.cern.ch/sitedb/data/prod/site-names"
/bin/rm -f ${TMP_AREA}/sitedb.json 1>/dev/null 2>&1
/usr/bin/wget --certificate=${AUTH_CRT} --private-key=${AUTH_KEY} -O ${TMP_AREA}/sitedb.json ${SITES_URL} 1>${ERR_FILE} 2>&1
RC=$?
if [ ${RC} -ne 0 ]; then
   MSG="failed to query SiteDB to get site-names, wget=${RC}"
   /bin/cat ${ERR_FILE}
   echo "   ${MSG}"
   if [ ! -t 0 ]; then
      /usr/bin/Mail -s "$0 ${MSG}" ${EMAIL_ADDR} < ${ERR_FILE}
   fi
   exit ${RC}
fi
/bin/rm ${ERR_FILE} 1>/dev/null 2>&1
#
# make list of CMS site names:
/bin/rm -f ${TMP_AREA}/sitedb.list
/usr/bin/awk -f ${TMP_AREA}/sitedb.awk ${TMP_AREA}/sitedb.json 1>${TMP_AREA}/sitedb.list
/bin/rm ${TMP_AREA}/sitedb.json
#
# sanity check of SiteDB sites:
if [ `/usr/bin/awk 'BEGIN{nl=0}{nl+=1}END{print nl}' ${TMP_AREA}/sitedb.list 2>/dev/null` -lt 100 ]; then
   MSG="sanity check of SiteDB sites failed, exiting"
   echo "   ${MSG}"
   if [ ! -t 0 ]; then
      echo "${SDB_LIST}" | /usr/bin/Mail -s "$0 ${MSG}" ${EMAIL_ADDR}
   fi
   exit 1
fi
if [ `(/bin/grep '^T0_' ${TMP_AREA}/sitedb.list | /usr/bin/wc -l) 2>/dev/null` -lt 1 ]; then
   MSG="sanity check of SiteDB Tier-0 count failed, exiting"
   echo "   ${MSG}"
   if [ ! -t 0 ]; then
      echo "${SDB_LIST}" | /usr/bin/Mail -s "$0 ${MSG}" ${EMAIL_ADDR}
   fi
   exit 1
fi
if [ `(/bin/grep '^T1_' ${TMP_AREA}/sitedb.list | /usr/bin/wc -l) 2>/dev/null` -lt 5 ]; then
   MSG="sanity check of SiteDB Tier-1 count failed, exiting"
   echo "   ${MSG}"
   if [ ! -t 0 ]; then
      echo "${SDB_LIST}" | /usr/bin/Mail -s "$0 ${MSG}" ${EMAIL_ADDR}
   fi
   exit 1
fi
if [ `(/bin/grep '^T2_' ${TMP_AREA}/sitedb.list | /usr/bin/wc -l) 2>/dev/null` -lt 40 ]; then
   MSG="sanity check of SiteDB Tier-2 count failed, exiting"
   echo "   ${MSG}"
   if [ ! -t 0 ]; then
      echo "${SDB_LIST}" | /usr/bin/Mail -s "$0 ${MSG}" ${EMAIL_ADDR}
   fi
   exit 1
fi
if [ `(/bin/grep '^T3_' ${TMP_AREA}/sitedb.list | /usr/bin/wc -l) 2>/dev/null` -lt 50 ]; then
   MSG="sanity check of SiteDB Tier-3 count failed, exiting"
   echo "   ${MSG}"
   if [ ! -t 0 ]; then
      echo "${SDB_LIST}" | /usr/bin/Mail -s "$0 ${MSG}" ${EMAIL_ADDR}
   fi
   exit 1
fi
# #############################################################################



# get list of GitLab projects (CMS sites) with last update time:
# ==============================================================
echo "Fetching list of GitLab projects/sites..."
/bin/cp /dev/null ${ERR_FILE} 1>/dev/null 2>&1
SUCC=0
FAIL=0
for PAGE in 1 2 3 4 5 6 7 8 9; do
   /usr/bin/wget --header="${AUTH_TKN}" --read-timeout=90 -O ${TMP_AREA}/gitlab_${PAGE}.json 'https://gitlab.cern.ch/api/v3/groups/SITECONF/projects?per_page=100&page='${PAGE} 1>>${ERR_FILE} 2>&1
   RC=$?
   if [ ${RC} -eq 0 ]; then
      SUCC=1
      /bin/grep name ${TMP_AREA}/gitlab_${PAGE}.json 1>/dev/null 2>&1
      if [ $? -ne 0 ]; then
         break
      fi
   else
      FAIL=1
      MSG="failed to query GitLab projects, page ${PAGE}, wget=${RC}"
      echo "   ${MSG}"
      if [ ! -t 0 ]; then
         echo "${MSG}" >> ${ERR_FILE}
         echo "" >> ${ERR_FILE}
      fi
   fi
done
if [ ${FAIL} -ne 0 ]; then
   MSG="failed to query GitLab projects"
   echo ""
   /bin/cat ${ERR_FILE}
   echo "   ${MSG}"
   if [ ! -t 0 ]; then
      /usr/bin/Mail -s "$0 ${MSG}" ${EMAIL_ADDR} < ${ERR_FILE}
   fi
fi
if [ ${SUCC} -eq 0 ]; then
   exit 1
fi
/bin/rm ${ERR_FILE} 1>/dev/null 2>&1
#
/bin/rm -f ${TMP_AREA}/.timestamp
/usr/bin/awk -f ${TMP_AREA}/gitlab.awk ${TMP_AREA}/gitlab_*.json 1>${TMP_AREA}/.timestamp
/bin/rm ${TMP_AREA}/gitlab_*.json
# #############################################################################



# loop over SYNC_DIR CMS sites and remove sites no longer in SiteDB:
# ==================================================================
/bin/cp /dev/null ${ERR_FILE} 1>/dev/null 2>&1
FAIL=0
SYC_LIST=`(cd ${SYNC_DIR}/SITECONF; /bin/ls -d1 T?_??_*) 2>/dev/null`
for SITE in ${SYC_LIST}; do
   /bin/grep "^${SITE}\$" ${TMP_AREA}/sitedb.list 1>/dev/null 2>&1
   if [ $? -ne 0 ]; then
      echo "Site \"${SITE}\" no longer in SiteDB, removing site area"
      /bin/rm -rf ${SYNC_DIR}/SITECONF/${SITE} 1>>${ERR_FILE} 2>&1
      RC=$?
      if [ ${RC} -ne 0 ]; then
         FAIL=1
         MSG="failed to remove area of ${SITE} not in SiteDB, rm=${RC}"
         echo "   ${MSG}"
         if [ ! -t 0 ]; then
            echo "${MSG}" >> ${ERR_FILE}
            echo "" >> ${ERR_FILE}
         fi
      fi
      /bin/rm ${ERR_FILE} 1>/dev/null 2>&1
      #
      /bin/touch ${SYNC_DIR}/SITECONF/.timestamp
      /bin/sed -i "/^${SITE}:/d" ${SYNC_DIR}/SITECONF/.timestamp
   fi
done
if [ ${FAIL} -ne 0 ]; then
   MSG="failed to remove areas not in SiteDB"
   echo ""
   /bin/cat ${ERR_FILE}
   echo "   ${MSG}"
   if [ ! -t 0 ]; then
      /usr/bin/Mail -s "$0 ${MSG}" ${EMAIL_ADDR} < ${ERR_FILE}
   fi
   exit 1
fi
/bin/rm ${ERR_FILE} 1>/dev/null 2>&1
# #############################################################################



# loop over SiteDB sites and update SYNC_DIR as needed:
# =====================================================
/bin/cp /dev/null ${ERR_FILE} 1>/dev/null 2>&1
FAIL=0
for SITE in `/bin/cat ${TMP_AREA}/sitedb.list`; do
   NEWT=`/usr/bin/awk -F: '{if($1=="'${SITE}'"){print $2}}' ${TMP_AREA}/.timestamp 2>/dev/null`
   if [ -z "${NEWT}" ]; then
      # no repository for this SiteDB site
      continue
   fi
   if [ -f ${SYNC_DIR}/SITECONF/.timestamp ]; then
      OLDT=`/usr/bin/awk -F: '{if($1=="'${SITE}'"){print $2}}' ${SYNC_DIR}/SITECONF/.timestamp 2>/dev/null`
      if [ "${NEWT}" = "${OLDT}" ]; then
         # SYNC_DIR up-to-date
         continue
      fi
   fi
   #
   # need to update SITECONF:
   # ------------------------
   echo "Updating area of site \"${SITE}\":"
   UPPER=`echo ${SITE} | /usr/bin/tr '[:lower:]' '[:upper:]'`
   /usr/bin/wget --header="${AUTH_TKN}" --read-timeout=180 -O ${TMP_AREA}/archive_${SITE}.tgz 'https://gitlab.cern.ch/SITECONF/'${UPPER}'/repository/archive.tar.gz?ref=master' 1>>${ERR_FILE} 2>&1
   RC=$?
   if [ ${RC} -ne 0 ]; then
      FAIL=1
      MSG="failed to fetch GitLab archive of ${SITE}, wget=${RC}"
      echo "   ${MSG}"
      if [ ! -t 0 ]; then
         echo "${MSG}" >> ${ERR_FILE}
         echo "" >> ${ERR_FILE}
      fi
      continue
   fi
   #
   TAR_DIR=`(/bin/tar -tzf ${TMP_AREA}/archive_${SITE}.tgz | /usr/bin/awk -F/ '{print $1;exit}') 2>/dev/null`
   TAR_LST=`(/bin/tar -tzf ${TMP_AREA}/archive_${SITE}.tgz | /usr/bin/awk -F/ '{if((($2=="JobConfig")&&(match($3,".*site-local-config.*\\.xml$")!=0))||(($2=="JobConfig")&&(match($3,"^cmsset_.*\\.c?sh$")!=0))||(($2=="PhEDEx")&&(match($3,".*storage.*\\.xml$")!=0))||(($2=="Tier0")&&($3=="override_catalog.xml"))||(($2=="GlideinConfig")&&($3=="")))print $0}') 2>/dev/null`
   #
   if [ -n "${TAR_LST}" ]; then
      echo "   extracting tar archive"
      (cd ${SYNC_DIR}/SITECONF; /bin/tar -xzf ${TMP_AREA}/archive_${SITE}.tgz ${TAR_LST}) 1>>${ERR_FILE} 2>&1
   else
      /bin/mkdir ${SYNC_DIR}/SITECONF/${TAR_DIR}
      /bin/mkdir ${SYNC_DIR}/SITECONF/${TAR_DIR}/JobConfig
   fi
   RC=$?
   if [ ${RC} -ne 0 ]; then
      FAIL=1
      MSG="failed to extract tar archive of ${SITE}, tar=${RC}"
      echo "   ${MSG}"
      if [ ! -t 0 ]; then
         echo "${MSG}" >> ${ERR_FILE}
         echo "" >> ${ERR_FILE}
         /bin/rm ${TMP_AREA}/archive_${SITE}.tgz
      fi
      continue
   fi
   /bin/rm ${TMP_AREA}/archive_${SITE}.tgz
   #
   # avoid directory file update in case extracted files did not change
   /usr/bin/diff -r ${SYNC_DIR}/SITECONF/${SITE} ${SYNC_DIR}/SITECONF/${TAR_DIR} 1>/dev/null 2>&1
   if [ $? -eq 0 ]; then
      # no file difference, keep old area
      echo "   no change to CVMFS files, keeping old area"
      /bin/rm -rf ${SYNC_DIR}/SITECONF/${TAR_DIR} 1>>${ERR_FILE} 2>&1
      RC=$?
      if [ ${RC} -ne 0 ]; then
         FAIL=1
         MSG="failed to remove new area of ${SITE}, rm=${RC}"
         echo "   ${MSG}"
         if [ ! -t 0 ]; then
            echo "${MSG}" >> ${ERR_FILE}
            echo "" >> ${ERR_FILE}
         fi
      fi
   else
      #
      if [ -e ${SYNC_DIR}/SITECONF/${SITE} ]; then
         echo "   removing old CVMFS area"
         /bin/rm -rf ${SYNC_DIR}/SITECONF/${SITE} 1>>${ERR_FILE} 2>&1
         RC=$?
         if [ ${RC} -ne 0 ]; then
            FAIL=1
            MSG="failed to remove old area of ${SITE}, rm=${RC}"
            echo "   ${MSG}"
            if [ ! -t 0 ]; then
               echo "${MSG}" >> ${ERR_FILE}
               echo "" >> ${ERR_FILE}
               /bin/rm -rf ${SYNC_DIR}/SITECONF/${TAR_DIR}
            fi
            continue
         fi
         /bin/touch ${SYNC_DIR}/SITECONF/.timestamp
         /bin/sed -i "/^${SITE}:/d" ${SYNC_DIR}/SITECONF/.timestamp
      fi
      #
      echo "   moving tar area into place"
      /bin/mv ${SYNC_DIR}/SITECONF/${TAR_DIR} ${SYNC_DIR}/SITECONF/${SITE} 1>>${ERR_FILE} 2>&1
      if [ $? -ne 0 ]; then
         # this is bad, so we better re-try:
         /bin/sync
         /bin/sleep 3
         echo "   re-trying move of ${SITE} area" >> ${ERR_FILE}
         /bin/mv ${SYNC_DIR}/SITECONF/${TAR_DIR} ${SYNC_DIR}/SITECONF/${SITE} 1>>${ERR_FILE} 2>&1
      fi
      RC=$?
      if [ ${RC} -ne 0 ]; then
         FAIL=1
         MSG="failed to move area of ${SITE}, mv=${RC}"
         echo "   ${MSG}"
         if [ ! -t 0 ]; then
            echo "${MSG}" >> ${ERR_FILE}
            echo "" >> ${ERR_FILE}
            /bin/rm -rf ${SYNC_DIR}/SITECONF/${TAR_DIR}
         fi
         continue
      fi
   fi
   #
   echo "   updating CVMFS timestamp of site"
   /bin/touch ${SYNC_DIR}/SITECONF/.timestamp
   /bin/sed -i "/^${SITE}:/d" ${SYNC_DIR}/SITECONF/.timestamp 1>/dev/null 2>&1
   /usr/bin/awk -F: '{if($1=="'${SITE}'"){print $0}}' ${TMP_AREA}/.timestamp >> ${SYNC_DIR}/SITECONF/.timestamp
done
if [ ${FAIL} -ne 0 ]; then
   MSG="failed to update SITECONF in SYNC_DIR"
   echo ""
   /bin/cat ${ERR_FILE}
   echo "   ${MSG}"
   if [ ! -t 0 ]; then
      /usr/bin/Mail -s "$0 ${MSG}" ${EMAIL_ADDR} < ${ERR_FILE}
   fi
   exit 1
fi
/bin/rm ${ERR_FILE} 1>/dev/null 2>&1
# #############################################################################



# release space_mon lock:
# -----------------------
echo "Releasing lock for cvmfs/stcnf_updt"
/bin/rm ${EXC_LOCK}
EXC_LOCK=""
# #############################################################################



exit 0
