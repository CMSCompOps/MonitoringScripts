#!/bin/bash

#Initialize
#source ~cmst1/.bashrc
#agentenv

workdir=/afs/cern.ch/user/c/cmst1/scratch0/WFM_Input_DashBoard/WFM_Alarms
cd $workdir

tmpDir=$(mktemp -d)
cd $tmpDir
cp $workdir/*.sh $workdir/*.py $tmpDir

echo $tmpDir
copyto=/afs/cern.ch/user/c/cmst1/www/WFMon/
#copyto=.

cp "/afs/cern.ch/user/c/cmst1/scratch0/WFM_Input_DashBoard/site_list_prev.txt" "sitelist_prev_copy.txt"
sitelist="sitelist_prev_copy.txt"
cat $sitelist
pledgejson="tmp_pledge.json"
statusjson="tmp_status.json"


#UNCOMMENTE
cmd="python db_Initialize.py $pledgejson $statusjson"
echo $cmd
eval $cmd

OUTPUTJSON="SSB_alarms.json"
if [  -f $OUTPUTJSON ]; then rm $OUTPUTJSON; fi
DateTimeSplit=$(sqlite3 fakedatabase "select datetime('now')")
rm fakedatabase
DateTimeSplitwith_h=$(echo $DateTimeSplit | awk '{print $1"T"$2}')
Date=$(echo $DateTimeSplit | awk '{print $1}') 
Time=$(echo $DateTimeSplit | awk '{print $2}') 
echo "{\"UPDATE\":{\"Date\":\"$Date\",\"Time\":\"$Time\"},\"Sites\":[" > $OUTPUTJSON

# thresholds for the alarm state of the normal alarm
thresh_alarm=0.7
thresh_warning=0.9

#for loop over sites
firstSite=1
# #sitelist goes into this loop at the end of the loop
while read site ; do
   echo "=========================================================================================="
   echo  $site

   #don't do this when the site contains "_Long", we don't want info for that
   if [[ "$site" == *"_Long" ]]
   then 
      echo "been here, will skip: site $site"
      continue
   fi

   
   # First 2 letters of the site (T1, T2 or T3)
   siteTier=${site:0:2}

   # fetching the pledge numbers
   pledge=$( python db_ExtractStatusEntry.py $site $DateTimeSplitwith_h $pledgejson )
   echo "pledge: $pledge"
   if [ "$pledge" == "" ] ; then pledge="0" ; fi
   pledge_SafeDivision=$pledge
   if [ $pledge_SafeDivision -eq 0 ] ; then pledge_SafeDivision=1 ; fi
    
   # fetching site information numbers of the last 24 hours 
   tmp_csv_merg="temp_site_RunAndPend.csv"
   #RUNNING
   url_siteinfo="http://dashb-cms-prod.cern.ch/dashboard/request.py/condorjobnumberscsv?sites=REPLACEME&sitesSort=1&jobTypes=&start=null&end=null&timeRange=last24&granularity=15%20Min&sortBy=3&series=All&type=r"
   url_filledwithsite=${url_siteinfo/REPLACEME/$site}
   echo $url_filledwithsite
   tmp_csv_run="temp_site_running.csv"
   wget -q -O $tmp_csv_run $url_filledwithsite
   echo fetched running csv of $site succesfully

  #PENDING
   url_siteinfo="http://dashb-cms-prod.cern.ch/dashboard/request.py/condorjobnumberscsv?sites=REPLACEME&sitesSort=1&jobTypes=&start=null&end=null&timeRange=last24&granularity=15%20Min&sortBy=3&series=All&type=p"
   url_filledwithsite=${url_siteinfo/REPLACEME/$site}
   echo $url_filledwithsite
   tmp_csv_pen="temp_site_pending.csv"
   wget -q -O $tmp_csv_pen $url_filledwithsite
   echo fetched pending csv of $site succesfully

  #MERGE the TWO files togther with paste and put a "," between the two instead of an endline symbol
  paste $tmp_csv_run $tmp_csv_pen  | sed -e 's/\s*\t\s*/,/g' > $tmp_csv_merg 
  echo merged the csv to one csv
  rm $tmp_csv_run 
  rm $tmp_csv_pen
   # now read first line in the csv for RUNNING jobs
   tmp_all="temp_All.dat"
   if [  -f $tmp_all ]; then rm $tmp_all; fi
   nb_Run_Clean="-1"
   nb_Run_Log="-1"
   nb_Run_Merge="-1"
   nb_Run_RelVal="-1"
   nb_Run_Proc="-1"
   nb_Run_Prod="-1"
   nb_Pen_Clean="-1"
   nb_Pen_Log="-1"
   nb_Pen_Merge="-1"
   nb_Pen_RelVal="-1"
   nb_Pen_Proc="-1"
   nb_Pen_Prod="-1"
   while read line ; do
      line=$( echo $line | sed  "s: :,:g")
      #echo $line

      # calculate sumPen and sumRun
      if [[ "$line" == *Clean* ]]
      then
            nb_Run_Clean=$( echo $line | awk 'BEGIN { FS = "," } ;{print $1}' );
            nb_Pen_Clean=$( echo $line | awk 'BEGIN { FS = "," } ;{print $5}' );
      fi
      if [[ "$line" == *Log* ]]
      then
            nb_Run_Log=$( echo $line | awk 'BEGIN { FS = "," } ;{print $1}' );
            nb_Pen_Log=$( echo $line | awk 'BEGIN { FS = "," } ;{print $5}' );
      fi
      if [[ "$line" == *Merge* ]]
      then
            nb_Run_Merge=$( echo $line | awk 'BEGIN { FS = "," } ;{print $1}' );
            nb_Pen_Merge=$( echo $line | awk 'BEGIN { FS = "," } ;{print $5}' );
      fi
      if [[ "$line" == *RelVal* ]]
      then
            nb_Run_RelVal=$( echo $line | awk 'BEGIN { FS = "," } ;{print $1}' );
            nb_Pen_RelVal=$( echo $line | awk 'BEGIN { FS = "," } ;{print $5}' );
      fi
      if [[ "$line" == *Proc* ]]
      then
            nb_Run_Proc=$( echo $line | awk 'BEGIN { FS = "," } ;{print $1}' );
            nb_Pen_Proc=$( echo $line | awk 'BEGIN { FS = "," } ;{print $5}' );
      fi
      if [[ "$line" == *Prod* ]]
      then
            nb_Run_Prod=$( echo $line | awk 'BEGIN { FS = "," } ;{print $1}' );
            nb_Pen_Prod=$( echo $line | awk 'BEGIN { FS = "," } ;{print $5}' );
            #this is also the last of the 5 variables that I have to read, so we write away our set and reset all the others
            #echo  "$nb_Run_Clean $nb_Run_Log $nb_Run_Merge $nb_Run_RelVal $nb_Run_Proc $nb_Run_Prod $nb_Pen_Clean $nb_Pen_Log $nb_Pen_Merge $nb_Pen_RelVal $nb_Pen_Proc $nb_Pen_Prod"
            nb_Sums=$( echo  "$nb_Run_Clean $nb_Run_Log $nb_Run_Merge $nb_Run_RelVal $nb_Run_Proc $nb_Run_Prod $nb_Pen_Clean $nb_Pen_Log $nb_Pen_Merge $nb_Pen_RelVal $nb_Pen_Proc $nb_Pen_Prod" | awk '{SUMRun=$1+$2+$3+$4+$5+$6}{SUMPen=$7+$8+$9+$10+$11+$12}{print SUMRun,SUMPen}'  )
     
            # fetching the time
            time_date=$( echo $line | awk 'BEGIN { FS = "," } ; {print $2}' )
            time_hour=$( echo $line | awk 'BEGIN { FS = "," } ; {print $3}' )
            time_point="${time_date}T${time_hour}" 

            # fetching the status number per time_point
            #need to transform the time first, because the csv has a different time format
            time_csv_converted=$( python db_time_converter.py $time_point)
            status=$( python db_ExtractStatusEntry.py $site $time_csv_converted $statusjson )
            #echo " python db_ExtractStatusEntry.py $site $time_csv_converted $statusjson "
            #echo $status

            echo "$time_point $nb_Sums $status" | awk -v Pledge="$pledge_SafeDivision" -v Status="$status" -v tier="$siteTier" -v th_al="$thresh_alarm" -v th_war="$thresh_warning" '{SUMRun=$2}{SUMPen=$3}{Ratio=(SUMRun)/Pledge}{PerfectRatio=1}{SeventyRatio=0.7}{Condition=((tier=="T1")||($4=="on"))}{GL_AL=Condition&&(SUMPen>=10)&&(SUMRun==0); GL_UNDEF=(!Condition); GL_OK=(GL_AL==0)&&(GL_UNDEF==0)}{A_WARN=Condition&&(Ratio<th_war)&&(Ratio>=th_al)&&(SUMPen>10); A_AL=Condition&&(Ratio<th_al)&&(SUMPen>10); A_UNDEF=(!Condition); A_OK=(A_AL==0)&&(A_WARN==0)&&(A_UNDEF==0)}{SPEC_Cond=Condition&&(SUMPen>=10); SPEC_SUMRun=SUMRun*SPEC_Cond; SPEC_Pledge=Pledge*SPEC_Cond}{print $1,Status,SUMRun,SUMPen,Pledge,Ratio,PerfectRatio,SeventyRatio,A_OK,A_WARN,A_AL,A_UNDEF,GL_OK,GL_AL,GL_UNDEF,SPEC_SUMRun,SPEC_Pledge,SPEC_Cond}' >> $tmp_all
            #format of data.dat: dateTime State SUMRun SUMPen Pledge Ratio 1.0 0.7 ALARM_OK ALARM_WARNING ALARM_ALARM ALARM_UNDEFINED GLIDEIN_OK GLIDEIN_ALARM GLIDEIN_UNDEF SPEC_SUMRun SPEC_Pledge SPEC_CondCanBeRemoved 
            #variable number  :     1       2    3      4        5    6     7   8    9           10            11            12         13             14         15            16          17         18
  	    nb_Run_Clean="-1"
   	    nb_Run_Log="-1"
  	    nb_Run_Merge="-1"
  	    nb_Run_RelVal="-1"
   	    nb_Run_Proc="-1"
   	    nb_Run_Prod="-1"
  	    nb_Pen_Clean="-1"
   	    nb_Pen_Log="-1"
   	    nb_Pen_RelVal="-1"
   	    nb_Pen_Proc="-1"
   	    nb_Pen_Prod="-1"
      fi
   # put tmp_csv for pending and running into the while loop
   done <  $tmp_csv_merg 

   #cat $tmp_all 
   
  # Looping over the 4 alarms: instant, 1h, 8h, 24h
       index=0
       for nb_entries in `echo 1 4 32 96` ; do
          tail -n $nb_entries $tmp_all > part.dat
   
          #GLIDE IN
          if [ $( cat part.dat | awk '{GlideIn_UNDEF += $15} END {print GlideIn_UNDEF}') -ge 1 ] ; then GlideInAlarm[$index]="UNDEF"; # 1 UNDEF is enough
          elif [   $( cat part.dat | awk '{GlideIn_OK += $13} END {print GlideIn_OK}') -ge 1 ] ; then GlideInAlarm[$index]="OK";       # 1 OK is enough 
          elif [ $( cat part.dat | awk '{if(GlideIn_ALARM==""){GlideIn_ALARM=1};GlideIn_ALARM *= $14} END {print GlideIn_ALARM}') -eq 1 ] ; then GlideInAlarm[$index]="ALARM"; # All in alarm
          else GlideInAlarm[$index]="MIS_OPT"                                                                                # 
          fi

          #OLD Alarm
          #if [   $( cat part.dat | awk '{Alarm_UNDEF += $12} END {print Alarm_UNDEF}') -ge 1 ] ; then Alarm[$index]="UNDEF"; # 1 undef is enough
          #elif [ $( cat part.dat | awk '{Alarm_OK += $9} END {print Alarm_OK}') -ge 1 ] ; then Alarm[$index]="OK";          # 1 OK is enough 
          #elif [ $( cat part.dat | awk '{Alarm_UNDEF += $12} END {print Alarm_UNDEF}') -ge 1 ] ; then Alarm[$index]="UNDEF"; # 1 undef is enough
          #elif [ $( cat part.dat | awk '{if(Alarm_WARNING==""){Alarm_WARNING=1};Alarm_WARNING *= $10} END {print Alarm_WARNING}') -eq 1 ] ; then Alarm[$index]="WARNING"; # All in warning
          #elif [ $( cat part.dat | awk '{if(Alarm_ALARM==""){Alarm_ALARM=1};Alarm_ALARM *= $11} END {print Alarm_ALARM}') -eq 1 ] ; then Alarm[$index]="ALARM"; # All in alarm
          #else   # mix of alarm and warning
          #   if [ $( cat part.dat | awk -v nb="$nb_entries" '{Alarm_ALARM += $11} END {Div=Alarm_ALARM/nb;Yes=(Div>=0.50);print Yes}') -eq 1 ] ; then Alarm[$index]="ALARM"                                                                                     # mix + >50% alarm  --> alarm
          #   elif [ $(tail -n 1 part.dat | awk '{print $11}') -eq 1 ] ; then Alarm[$index]="ALARM"                  # mix + last entry alarm --> alarm
          #   else Alarm[$index]="WARNING"                                                                              # mix + opposite of the two above --> warning
          #   fi
          #fi

          # new alarm
          #sum all SPEC_SUMRun  and sum all SPEC_Pledge
          ratioTmp=$( cat part.dat | awk '{nom +=$16; denom +=$17} END {if(denom!=0) {div=nom/denom} else {div=0}; print div} ')
          #if [ $(awk -v Ratio=$ratioTmp ' BEGIN{res=(Ratio==0); print res}') -eq 1 ] ; then NEW_ALARM[$index]="UNDEF"; 
          if [ $(awk -v Ratio=$ratioTmp -v th_al="$thresh_alarm" -v th_war="$thresh_warning" 'BEGIN {res=((Ratio<th_war)&&(Ratio>=th_al)); print res}')  -eq 1 ] ; then NEW_ALARM[$index]="WARNING";
          elif [ $(awk -v Ratio=$ratioTmp -v th_al="$thresh_alarm" 'BEGIN { res=(Ratio<th_al); print res}')  -eq 1 ] ; then NEW_ALARM[$index]="ALARM";
          else NEW_ALARM[$index]="OK";
          fi
          if [ $(cat part.dat | awk '{sum +=$4} END {res=(sum<=10); print res}') -eq 1 ] ; then NEW_ALARM[$index]="OK";
          fi
          if [ $(tail -n 1 part.dat | awk -v tier="$siteTier" '{res=($2=="on" || (tier=="T1") ); print res}') -eq 0 ] ; then NEW_ALARM[$index]="UNDEF";
          fi
#          nom=$( cat part.dat | awk '{nom +=$26} END {print nom}')
#          denom=$( cat part.dat | awk '{denom +=$27} END {print denom}')
#          echo "$site , $nb_entries ; $nom / $denom : $ratioTmp "

          #needed for json
          if [ $nb_entries -eq 1 ] ; then
            Timetmp=$(   cat part.dat | awk '{print $1}'  )
            Ratiotmp=$(  cat part.dat | awk '{print $16}' )
            echo "$Timetmp"
          fi
          index=$(expr $index + 1 )
       done
       rm part.dat

      echo "GLIDE IN : ${GlideInAlarm[0]}  , ${GlideInAlarm[1]}, ${GlideInAlarm[2]}, ${GlideInAlarm[3]}   "  
      echo "NEW ALARM: ${NEW_ALARM[0]}  , ${NEW_ALARM[1]}, ${NEW_ALARM[2]}, ${NEW_ALARM[3]}  "  

      #writing instand data to json + 1h 24h alarms (the 1h alarm is calculated above, but it is not used below 
       if [ $firstSite -eq 1 ] ; then firstSite=0 ;
       else  echo "," >> $OUTPUTJSON;  fi ;
       str="{\"Site\":\"$site\",\"TimeDate\":\"$Timetmp\",\"Ratio\":\"$Ratiotmp\",\"InstantAlarm\":\"${NEW_ALARM[0]}\",\"x8hAlarm\":\"${NEW_ALARM[2]}\",\"x24hAlarm\":\"${NEW_ALARM[3]}\",\"InstantGlideInAlarm\":\"${GlideInAlarm[0]}\",\"x1hGlideInAlarm\":\"${GlideInAlarm[1]}\",\"x8hGlideInAlarm\":\"${GlideInAlarm[2]}\",\"x24hGlideInAlarm\":\"${GlideInAlarm[3]}\"}"
       #str="{\"Site\":\"$site\",\"TimeDate\":\"$Timetmp\",\"InstantAlarm\":\"${NEW_ALARM[0]}\",\"x1hAlarm\":\"${NEW_ALARM[1]}\",\"x24hAlarm\":\"${NEW_ALARM[2]}\",\"InstantGlideInAlarm\":\"${GlideInAlarm[0]}\",\"x1hGlideInAlarm\":\"${GlideInAlarm[1]}\",\"x24hGlideInAlarm\":\"${GlideInAlarm[2]}\"}"
        echo  $str >> $OUTPUTJSON
        echo $str

     #remove site specific tmp_all
     rm $tmp_all

     #exit
# put $sitelist into the while loop
done < $sitelist  # closing while loop over sites

# remove \n in json
mv $OUTPUTJSON tmp.json
tr -d '\n' < tmp.json > $OUTPUTJSON
echo "]}" >> $OUTPUTJSON
rm tmp.json
cp $OUTPUTJSON $workdir
cp $OUTPUTJSON $copyto
cd -
rm -rf $tmpDir
exit

