#!/bin/sh
#
#
#outFile="/afs/cern.ch/user/b/belforte/www/misc/MaintenanceForSiteMonitor.txt"
outFile="./MaintenanceForSiteMonitor.txt"

cat <<EOF > $outFile
# list of maintenance information links for Site Status Board
# for EGEE sites point to their GOC site
# for OSG sites point to OSG GOC downtime page
# something still needed for Helsinki(NorduGrid)
# 
# some inforamtion is also available in CMS HN forum
# https://hypernews.cern.ch/HyperNews/CMS/get/gridAnnounce.html

# this page is created by an acrontab script running on lxplus.cern.ch
# which runs the script
# /afs/cern.ch/user/b/belforte/SiteMonitor/MaintenanceForSiteMonitor.sh
# directely linked at
# http://belforte.home.cern.ch/belforte/misc/MaintenanceForSiteMonitor.sh
#
EOF

timestamp=`date +"%Y-%m-%d %H:%M:%S"`

#
#
cmsSites=`curl -ks https://cmsweb.cern.ch/sitedb/sitedb/json/index/SitetoCMSName?name= | tr "," "\n"|cut -d"'" -f6|grep -v "T1_CH_CERN"|grep -v "T2_CH_CAF"|sort -u`

for s in $cmsSites
do
  sam=`curl -ks https://cmsweb.cern.ch/sitedb/sitedb/json/index/CMStoSAMName?name=$s | tr "," "\n"|cut -d"'" -f6 | head -1`
  goc=`curl -s http://goc.grid.sinica.edu.tw/gstat/$sam/|grep "goc.gridops.org"| cut -d= -f3,4|cut -d">" -f1|tr -d '"'`

  if [ "$goc" != "" ]
  then
      value="GOCDB"
      link=$goc"#downtimes"
  else
      value="OIM"
      link="http://oim.grid.iu.edu/pub/maintenance/show.php"
  fi

  if [ "$s" == "T2_FI_HIP" ]
  then
      value="GOCDB"
      link="https://goc.gridops.org/site/list?id=322#downtimes"
  fi

  if [ "$s" != "T2_FR_GRIF_LAL" ]
  then
   if [ "$s" != "T2_FR_GRIF_LPNHE" ]
   then
    echo -e $timestamp'\t'$s'\t'$value'\t'"white"'\t'$link'\t'"n/a" >> $outFile
   fi
  fi
done

cp /afs/cern.ch/user/b/belforte/www/misc/MaintenanceForSiteMonitor.txt /afs/cern.ch/user/b/belforte/www/misc/MaintenanceForSiteMonitor.txt.OLD
cp $outFile /afs/cern.ch/user/b/belforte/www/misc/MaintenanceForSiteMonitor.txt
