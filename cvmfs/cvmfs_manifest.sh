#!/bin/sh
# #############################################################################
# Bourne shell script to fetch .cvmfspublished of cms.cern.ch from the        #
#    CVMFS Stratum-0 at CERN and publish on CMSWeb with a double TTL delay.   #
#    The revision information will be used by the SAM worker node CVMFS probe #
#    to decide if the local filesystem mount is current or out-dated.         #
#                                                                             #
# 2022-Aug-30 Stephan Lammel                                                  #
# #############################################################################
URL="http://cvmfs-stratum-zero.cern.ch/cvmfs/cms.cern.ch/.cvmfspublished"
DIR="/eos/user/c/cmssst/www/cvmfs/cms.cern.ch"
#
umask 022



null_cvmfspublished()
{
   ERROR_MSG=$1
   /bin/rm -f ${DIR}/new.cvmfspublished
   echo -e -n "C0000000000000000000000000000000000000000\nB0\nRd41d8cd98f00b204e9800998ecf8427e\nD0\nS0\nGno\nAno\nNcms.cern.ch\nX0000000000000000000000000000000000000000\nH0000000000000000000000000000000000000000\nT0\nM0000000000000000000000000000000000000000\nY0000000000000000000000000000000000000000\n--\n00000000deadbeef00000000deadbeef00000000\n${ERROR_MSG} !!!" 1>${DIR}/new.cvmfspublished 2>/dev/null
   /bin/mv ${DIR}/new.cvmfspublished ${DIR}/.cvmfspublished
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

/usr/bin/timeout 90 /usr/bin/wget -O ${DIR}/new.cvmfspublished -T 60 ${URL}
RC=$?
if [ ${RC} -eq 124 ]; then
   null_cvmfspublished "timeout contacting Stratum-0"
   exit 1
elif [ ${RC} -ne 0 ]; then
   null_cvmfspublished "failed to fetch Stratum-0 manifest"
   exit 1
fi

NOW=`/usr/bin/date +"%s"`
TSP=`/usr/bin/awk -v now=${NOW} 'BEGIN{t=now} $0 ~ /^T/ {t=int(substr($0,2))} END{print int(now-t)}' ${DIR}/new.cvmfspublished`
TDL=`/usr/bin/awk -v tsp=${TSP} 'BEGIN{t=900} $0 ~ /^D/ {t=2*int(substr($0,2))} END{print int(t-tsp)}' ${DIR}/new.cvmfspublished`
if [ ${TDL} -gt 0 ]; then
   echo "sleeping ${TDL} seconds before update"
   /bin/sleep ${TDL}
fi

/bin/mv ${DIR}/new.cvmfspublished ${DIR}/.cvmfspublished
RC=$?

if [ ! -e ${DIR}/.htaccess ]; then
   echo -e "<Files \".cvmfspublished\">\n   Header set Cache-Control \"public, max-age=3600\"\n   Header set Access-Control-Max-Age 3600\n</Files>" 1> ${DIR}/.htaccess 2>/dev/null
fi

exit ${RC}
