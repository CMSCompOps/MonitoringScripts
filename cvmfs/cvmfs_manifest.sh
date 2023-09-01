#!/bin/sh
# #############################################################################
# Bourne shell script to fetch .cvmfspublished of cms.cern.ch from the        #
#    CVMFS Stratum-0 at CERN and publish on CMSWeb with a double TTL delay.   #
#    The revision information will be used by the SAM worker node CVMFS probe #
#    to decide if the local filesystem mount is current or out-dated.         #
#                                                                             #
# 2022-Aug-30 Stephan Lammel                                                  #
# #############################################################################
MY_URLS="http://cvmfs-stratum-zero.cern.ch/cvmfs/cms.cern.ch/.cvmfspublished http://oasis.opensciencegrid.org:8000/cvmfs/oasis.opensciencegrid.org/.cvmfspublished http://oasis-replica.opensciencegrid.org:8000/cvmfs/singularity.opensciencegrid.org/.cvmfspublished http://cvmfs-stratum-zero.cern.ch/cvmfs/grid.cern.ch/.cvmfspublished"
MY_OUT_STEM="/eos/user/c/cmssst/www/cvmfs"
MY_VERSION="v1.2.0"
#
umask 022
EXITCODE=0



null_cvmfspublished()
{
   THIS_OUT_DIR=$1
   if [ ${THIS_OUT_DIR} = "" -o [ ${THIS_OUT_DIR} = *" "* ]]; then
      return
   fi
   THIS_AREA=`echo "${THIS_OUT_DIR}" | /usr/bin/awk -F/ '{print $NF;exit}'`
   ERROR_MSG=$2
   /bin/rm -f ${THIS_OUT_DIR}/new.cvmfspublished
   echo -e -n "C0000000000000000000000000000000000000000\nB0\nRd41d8cd98f00b204e9800998ecf8427e\nD0\nS0\nGno\nAno\nN${THIS_AREA}\nX0000000000000000000000000000000000000000\nH0000000000000000000000000000000000000000\nT0\nM0000000000000000000000000000000000000000\nY0000000000000000000000000000000000000000\n--\n00000000deadbeef00000000deadbeef00000000\n${ERROR_MSG} !!!" 1>${THIS_OUT_DIR}/new.cvmfspublished 2>/dev/null
   /bin/mv ${THIS_OUT_DIR}/new.cvmfspublished ${THIS_OUT_DIR}/.cvmfspublished
}



if [ ! -x /usr/bin/eosfusebind ] || \
   [ ! -x /usr/bin/timeout ] || \
   [ ! -x /usr/bin/wget ] || \
   [ ! -x /usr/bin/date ] || \
   [ ! -x /usr/bin/awk ] || \
   [ ! -x /usr/bin/sort ]; then
   null_cvmfspublished "missing UNIX commands"
   exit 1
fi

/usr/bin/eosfusebind -g
MY_START=`/usr/bin/date -u +"%s"`



# start new revisions summary file:
# =================================
/bin/rm -f ${MY_OUT_STEM}/revisions.txt_new 1>/dev/null 2>&1
MY_TMP=`/bin/date -u +'%Y-%b-%d %H:%M:%S' 2>/dev/null`
echo -e "#txt\n#\n# CMS Site Support, CVMFS revisions summary, ${MY_VERSION} of ${MY_TMP} UTC" 1> ${MY_OUT_STEM}/revisions.txt_new
echo "# =============================================================================" 1>> ${MY_OUT_STEM}/revisions.txt_new
echo "cvmfs_manifest.sh:${MY_VERSION}:${MY_START}" 1>> ${MY_OUT_STEM}/revisions.txt_new



# loop over Stratum-0 URLs of CVMFS areas of interest:
# ====================================================
for MY_URL in ${MY_URLS}; do
   MY_AREA=`echo "${MY_URL}" | /usr/bin/awk -F/ '{print $(NF-1);exit}'`
   MY_AREA="${MY_AREA# *}"
   MY_AREA="${MY_AREA%% *}"
   echo "[I] CVMFS area ${MY_AREA}:"
   #
   MY_OUT_DIR=${MY_OUT_STEM}/${MY_AREA}
   if [ ! -e ${MY_OUT_DIR} ]; then
      /bin/mkdir ${MY_OUT_DIR}
      /bin/touch ${MY_OUT_DIR}/revisions.txt
   fi
   /bin/rm -f ${MY_OUT_DIR}/revisions.txt_new 1>/dev/null 2>&1

   # fetch .cvmfspublished file of Stratum-0:
   # ----------------------------------------
   /bin/rm -f ${MY_OUT_DIR}/new.cvmfspublished 1>/dev/null 2>&1
   /usr/bin/timeout 90 /usr/bin/wget -O ${MY_OUT_DIR}/new.cvmfspublished -T 60 ${MY_URL}
   RC=$?
   if [ ${RC} -eq 124 ]; then
      echo "[E] timeout contacting Stratum-0"
      null_cvmfspublished "${MY_OUT_DIR}" "timeout contacting Stratum-0"
      if [ ${EXITCODE} -eq 0 ]; then
         EXITCODE=1
      fi
   elif [ ${RC} -ne 0 ]; then
      echo "[E] failed to fetch Stratum-0 manifest"
      null_cvmfspublished "${MY_OUT_DIR}" "failed to fetch Stratum-0 manifest"
      if [ ${EXITCODE} -eq 0 ]; then
         EXITCODE=1
      fi
   else

      # get current filesystem revision and release date or area:
      MY_REVN=`/usr/bin/awk '$0 ~ /^S/ {print substr($0,2);exit}' ${MY_OUT_DIR}/new.cvmfspublished`
      MY_REVT=`/usr/bin/awk '$0 ~ /^T/ {print int(substr($0,2));exit}' ${MY_OUT_DIR}/new.cvmfspublished`
      if [ -z "${MY_REVN}" -o -z "${MY_REVT}" ]; then
         echo "[E] no revision and/or release date information"
      else

         MY_48H=`echo "${MY_START} - (48*60*60)" | /usr/bin/bc`
         #
         echo "${MY_REVN}:${MY_REVT}" 1> ${MY_OUT_DIR}/revisions.tmp
         /bin/cat ${MY_OUT_DIR}/revisions.txt 1>> ${MY_OUT_DIR}/revisions.tmp
         #
         /bin/cat ${MY_OUT_DIR}/revisions.tmp | /usr/bin/sort -t: -n -r -u | /usr/bin/awk -F: -vc=${MY_48H} 'BEGIN{d=0}{if($2<c){if(d==0){print $0;d=1}}else{print $0}}' 1> ${MY_OUT_DIR}/revisions.txt_new
         if [ $? -ne 0 ]; then
            echo "[E] update of new revisions.txt of ${MY_AREA} failed"
         else

            /bin/mv ${MY_OUT_DIR}/new.cvmfspublished ${MY_OUT_DIR}/.cvmfspublished
            /bin/mv ${MY_OUT_DIR}/revisions.txt_new ${MY_OUT_DIR}/revisions.txt
            if [ ! -e ${MY_OUT_DIR}/.htaccess ]; then
               echo -e "<FilesMatch \"^(.cvmfspublished|revisions.txt)\$\">\n   Header set Cache-Control \"public, max-age=3600\"\n   Header set Access-Control-Max-Age 3600\n</Files>" 1> ${MY_OUT_DIR}/.htaccess 2>/dev/null
            fi
            echo "   new .cvmfspublished/revisions.txt with ${MY_REVN} revision"
         fi
         /bin/rm ${MY_OUT_DIR}/revisions.tmp
      fi
   fi

   echo "#" 1>> ${MY_OUT_STEM}/revisions.txt_new
   /usr/bin/awk -F: -va=${MY_AREA} '{if(NF==2){printf "%s:%s:%s\n",a,$1,$2}}' ${MY_OUT_DIR}/revisions.txt 1>> ${MY_OUT_STEM}/revisions.txt_new
   echo ""
done



# mv new revisions summary file into place:
# =========================================
/bin/mv ${MY_OUT_STEM}/revisions.txt_new ${MY_OUT_STEM}/revisions.txt
RC=$?
if [ ${EXITCODE} -eq 0 ]; then
   EXITCODE=${RC}
fi
if [ ! -e ${MY_OUT_STEM}/.htaccess ]; then
   echo -e "<Files \"revisions.txt\">\n   ForceType 'text/plain; charset=UTF-8'\n   Header set Cache-Control \"public, max-age=3600\"\n   Header set Access-Control-Max-Age 3600\n</Files>" 1> ${MY_OUT_STEM}/.htaccess 2>/dev/null
fi


exit ${EXITCODE}
