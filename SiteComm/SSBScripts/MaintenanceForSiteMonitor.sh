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
gocBaseUrlBegin="https://next.gocdb.eu/portal/index.php?Page_Type=View_Object&object_id="
gocBaseUrlEnd="&grid_id=0"

#
#
cmsSites=`/usr/bin/curl -ks https://cmsweb.cern.ch/sitedb/sitedb/json/index/SitetoCMSName?name= | tr "," "\n"|cut -d"'" -f6|grep -v "T1_CH_CERN"|grep -v "T2_CH_CAF"|sort -u`

for s in $cmsSites
do
  sam=`/usr/bin/curl -ks https://cmsweb.cern.ch/sitedb/sitedb/json/index/CMStoSAMName?name=$s | tr "," "\n"|cut -d"'" -f6 | head -1`
  echo $s $sam
  goc=`/usr/bin/curl -ks "https://goc.gridops.org/gocdbpi/public/?method=get_site_list&sitename=$sam"|tr ' ' '\n'|grep PRIMARY_KEY|cut -d'"' -f2|sed s/G0//`
  gocUrl=$gocBaseUrlBegin$goc$gocBaseUrlEnd

#  if [ "$s" == "T1_US_FNAL" ]
#  then
#    goc=""
#  fi

  if [ "$goc" != "" ]
  then
      value="GOCDB"
      link=$gocUrl
  else
      value="OIM"
      link="http://tinyurl.com/nv66gk"
      link="http://myosg.grid.iu.edu/wizarddowntime/index?datasource=downtime&summary_attrs_showservice=on&summary_attrs_showrsvstatus=on&summary_attrs_showfqdn=on&gip_status_attrs_showtestresults=on&gip_status_attrs_showfqdn=on&account_type=cumulative_hours&ce_account_type=gip_vo&se_account_type=vo_transfer_volume&start_type=7daysago&start_date=06%2F23%2F2009&end_type=now&end_date=06%2F23%2F2009&all_resources=on&gridtype=on&gridtype_1=on&vosup=on&vosup_3=on&active=on&active_value=1&disable_value=1&has_wlcg=on"
      #link="http://oim.grid.iu.edu/pub/maintenance/show.php"
  fi

#  if [ "$s" == "T2_FI_HIP" ]
#  then
#      value="GOCDB"
#      link="https://goc.gridops.org/site/list?id=322#downtimes"
#  fi

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
