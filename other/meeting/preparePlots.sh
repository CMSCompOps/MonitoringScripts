#!/bin/bash

echo "type the date (it will be name of the output folder):"
read date

baseUrl=http://dashb-cms-prod.cern.ch/dashboard/request.py/condorjobnumbers_individual
baseOpts="&jobTypes=&start=null&end=null&timeRange=lastWeek&granularity=Hourly&sortBy=3&series=All&type"

tier1s="T1_DE_KIT T1_ES_PIC T1_IT_CNAF T1_FR_CCIN2P3 T1_TW_ASGC T1_UK_RAL T1_US_FNAL T1_RU_JINR"
tier2s="T2_CH_CERN All"

for site in $tier1s $tier2s; do
    if [ "$site" == "All" ]; then
        site="All%20T32"
        sort=4
        fname=T2
    else
        sort=1
        fname=$site
    fi
    curl "$baseUrl?sites=$site&sitesSort=$sort$baseOpts&type=sr" > $date/${fname}_running.png &
    curl "$baseUrl?sites=$site&sitesSort=$sort$baseOpts&type=p" > $date/${fname}_pending.png &
    sleep .1
done
