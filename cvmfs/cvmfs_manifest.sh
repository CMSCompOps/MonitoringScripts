#!/bin/sh
# #############################################################################
# Bourne shell script to fetch .cvmfspublished of cms.cern.ch from the        #
#    CVMFS Stratum-0 at CERN and publish on CMSWeb with a double TTL delay.   #
#    The revision information will be used by the SAM worker node CVMFS probe #
#    to decide if the local filesystem mount is current or out-dated.         #
#                                                                             #
# 2022-Aug-30 Stephan Lammel                                                  #
# #############################################################################
URLS="http://cvmfs-stratum-zero.cern.ch/cvmfs/cms.cern.ch/.cvmfspublished http://oasis.opensciencegrid.org:8000/cvmfs/oasis.opensciencegrid.org/.cvmfspublished http://oasis-replica.opensciencegrid.org:8000/cvmfs/singularity.opensciencegrid.org/.cvmfspublished"
DIRS="/eos/user/c/cmssst/www/cvmfs/"
#
umask 022
EXITCODE=0



null_cvmfspublished()
{
   MY_AREA=$1
   if [ ${MY_AREA} = "" -o [ ${MY_AREA} = *" "* ]]; then
      return
   fi
   MY_REPO=`echo "${MY_AREA}" | /usr/bin/awk -F/ '{print $NF;exit}'`
   ERROR_MSG=$2
   /bin/rm -f ${MY_AREA}/new.cvmfspublished
   echo -e -n "C0000000000000000000000000000000000000000\nB0\nRd41d8cd98f00b204e9800998ecf8427e\nD0\nS0\nGno\nAno\nN${MY_REPO}\nX0000000000000000000000000000000000000000\nH0000000000000000000000000000000000000000\nT0\nM0000000000000000000000000000000000000000\nY0000000000000000000000000000000000000000\n--\n00000000deadbeef00000000deadbeef00000000\n${ERROR_MSG} !!!" 1>${MY_AREA}/new.cvmfspublished 2>/dev/null
   /bin/mv ${MY_AREA}/new.cvmfspublished ${MY_AREA}/.cvmfspublished
}



if [ ! -x /usr/bin/eosfusebind ] || \
   [ ! -x /usr/bin/timeout ] || \
   [ ! -x /usr/bin/wget ] || \
   [ ! -x /usr/bin/date ] || \
   [ ! -x /usr/bin/awk ] || \
   [ ! -x /bin/sleep ]; then
   null_cvmfspublished "missing UNIX commands"
   exit 1
fi

/usr/bin/eosfusebind -g



# fetch manifest for repositories:
for URL in ${URLS}; do
   REPO=`echo "${URL}" | /usr/bin/awk -F/ '{print $(NF-1);exit}'`
   AREA=${DIRS}/${REPO}

   /usr/bin/timeout 90 /usr/bin/wget -O ${AREA}/new.cvmfspublished -T 60 ${URL}
   RC=$?
   if [ ${RC} -eq 124 ]; then
      null_cvmfspublished "${AREA}" "timeout contacting Stratum-0"
      if [ ${EXITCODE} -eq 0 ]; then
         EXITCODE=1
      fi
      continue
   elif [ ${RC} -ne 0 ]; then
      null_cvmfspublished "${AREA}" "failed to fetch Stratum-0 manifest"
      if [ ${EXITCODE} -eq 0 ]; then
         EXITCODE=1
      fi
      continue
   fi

   NOW=`/usr/bin/date +"%s"`
   TSP=`/usr/bin/awk -v now=${NOW} 'BEGIN{t=now} $0 ~ /^T/ {t=int(substr($0,2))} END{print int(now-t)}' ${AREA}/new.cvmfspublished`
   TDL=`/usr/bin/awk -v tsp=${TSP} 'BEGIN{t=900} $0 ~ /^D/ {t=2*int(substr($0,2))} END{print int(t-tsp)}' ${AREA}/new.cvmfspublished`
   if [ ${TDL} -gt 0 ]; then
      echo "sleeping ${TDL} seconds before update"
      /bin/sleep ${TDL}
   fi

   /bin/mv ${AREA}/new.cvmfspublished ${AREA}/.cvmfspublished
   RC=$?
   if [ ${EXITCODE} -eq 0 ]; then
      EXITCODE=${RC}
   fi

   if [ ! -e ${AREA}/.htaccess ]; then
      echo -e "<Files \".cvmfspublished\">\n   Header set Cache-Control \"public, max-age=3600\"\n   Header set Access-Control-Max-Age 3600\n</Files>" 1> ${AREA}/.htaccess 2>/dev/null
   fi
done

exit ${EXITCODE}
