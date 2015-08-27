#!/bin/sh

export SSTBASE=$(dirname $(readlink -f "${BASH_SOURCE[0]}"))
export CERTS=$SSTBASE/certs
export PYTHONPATH="$PYTHONPATH:$SSTBASE"
export SSTOUT="$SSTBASE/output"
export SSTLOG="$SSTBASE/log"
export SSTDATA="$SSTBASE/data"
export SSTMAIL="cms-comp-ops-site-support-team@cern.ch"
SSTINITERR="$SSTLOG/sstInit.log"

if [ ! -d "$SSTOUT" ]; then
    mkdir $SSTOUT
fi

if [ ! -d "$SSTLOG" ]; then
    mkdir $SSTLOG
fi

# check Kerberos ticket and AFS token (author: slammel):
# ------------------------------------
echo "Checking Kerberos ticket/AFS token:"
/bin/rm ${SSTINITERR} 1>/dev/null 2>&1
/usr/bin/klist 2> ${SSTINITERR}
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
      /usr/bin/Mail -s "$0 ${MSG}" ${SSTMAIL} < ${SSTINITERR}
      exit ${RC}
   fi
fi
/bin/rm ${SSTINITERR} 1>/dev/null 2>&1
/usr/bin/aklog 2> ${SSTINITERR}
RC=$?
if [ ${RC} -ne 0 ]; then
   MSG="unable to acquire AFS token, aklog=${RC}"
   echo "   ${MSG}"
   /usr/bin/Mail -s "$0 ${MSG}" ${SSTMAIL} < ${SSTINITERR}
   exit ${RC}
fi
