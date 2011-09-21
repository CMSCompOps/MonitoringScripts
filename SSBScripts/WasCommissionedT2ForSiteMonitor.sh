#!/bin/sh
#
#
outFile="./WasCommissionedT2ForSiteMonitor.txt"

cat <<EOF > $outFile
# list WasCommissionedT2 sites for  Site Status Board
# A T2 site goes here it it was commissioned at least once
# and it is in some "active" status so it deserves being watched
# in the top page.
# Other T2's are in the "wating room" to avoid cluttering
# the main view with sites that are mostly in error status
#
# This table is maintained by hand by the Commissioning Coordinators
#
# Is initially seeded on July 17 2008 by picking sites
# that did at least 40% OK in both SAM and JobRobot in last 30days
#
# updates:
# Sep 11 2008: enable Warsaw and Sprace based on good record in last month
# Jun 10 2009: enable SINP on req. of admins, enable METU based on good record
# Aug 10 2009: enable UA_KIPT and move to CVS (will have history there)
#
# this page is located at
# /afs/cern.ch/cms/LCG/SiteComm/T2WaitingList/WasCommissionedT2ForSiteMonitor.txt
# and is created by running the script
# /afs/cern.ch/cms/LCG/SiteComm/SSBScripts/WasCommissionedT2ForSiteMonitor.sh
# which is maintained in CVS at
# http://cmssw.cvs.cern.ch/cgi-bin/cmssw.cgi/COMP/SITECOMM/SSBScripts/WasCommissionedT2ForSiteMonitor.sh?view=log
#
EOF

timestamp=`date +"%Y-%m-%d %H:%M:%S"`

#
WasCommissionedT2List="
AT_Vienna \
BE_IIHE \
BE_UCL \
BR_UERJ \
BR_SPRACE \
CH_CSCS \
CN_Beijing \
DE_DESY \
DE_RWTH \
EE_Estonia \
ES_CIEMAT \
ES_IFCA \
FI_HIP \
FR_CCIN2P3 \
FR_GRIF_IRFU \
FR_IPHC \
FR_GRIF_LLR \
HU_Budapest \
IN_TIFR \
IT_Bari \
IT_Legnaro \
IT_Pisa \
IT_Rome \
KR_KNU \
PL_Warsaw \
PT_LIP_Lisbon \
PT_NCG_Lisbon \
RU_IHEP \
RU_INR \
RU_ITEP \
RU_JINR \
RU_PNPI \
RU_RRC_KI \
RU_SINP \
TR_METU \
TW_Taiwan \
UA_KIPT \
UK_London_Brunel \
UK_London_IC \
UK_SGrid_RALPP \
US_Caltech \
US_Florida \
US_MIT \
US_Nebraska \
US_Purdue \
US_UCSD \
US_Wisconsin \
"
#

for site in $WasCommissionedT2List
do
  echo -e $timestamp'\t'T2_${site}'\t'1'\t'"white"'\t'n/a'\t'"n/a" >> $outFile
done


#


cp /afs/cern.ch/cms/LCG/SiteComm/T2WaitingList/WasCommissionedT2ForSiteMonitor.txt /afs/cern.ch/cms/LCG/SiteComm/T2WaitingList/WasCommissionedT2ForSiteMonitor.txt.OLD
cp $outFile /afs/cern.ch/cms/LCG/SiteComm/T2WaitingList/WasCommissionedT2ForSiteMonitor.txt
