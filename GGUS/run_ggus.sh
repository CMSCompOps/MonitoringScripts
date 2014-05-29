#!/bin/bash
# Script in cmst1 acrontab 
# 5,20,35,50 * * * * lxplus ssh vocms202 /afs/cern.ch/user/c/cmst1/scratch0/MonitoringScripts/GGUS/run_ggus.sh &> /dev/null
# Script for Dashboard metric 
# outputfile ggusticketmetrics.txt
# outputfile ticketmeeting.txt
# outputfile tickets.xml
# Script obtains ggus ticket information and creates 2 files. One of them is ggusticketmetrics.txt for metric in dashboard, the other one is ticketmeeting for CompOps Meeting
curl -kvv --cert /data/certs/servicecert.pem --key /data/certs/servicekey.pem "https://ggus.eu/index.php?mode=ticket_search&show_columns_check%5B%5D=TICKET_TYPE&show_columns_check%5B%5D=AFFECTED_VO&show_columns_check%5B%5D=AFFECTED_SITE&show_columns_check%5B%5D=PRIORITY&show_columns_check%5B%5D=RESPONSIBLE_UNIT&show_columns_check%5B%5D=STATUS&show_columns_check%5B%5D=DATE_OF_CHANGE&show_columns_check%5B%5D=SHORT_DESCRIPTION&ticket_id=&supportunit=&su_hierarchy=0&vo=cms&cms_su=&user=&keyword=&involvedsupporter=&assignedto=&affectedsite=&specattrib=none&status=open&priority=&typeofproblem=&ticket_category=all&mouarea=&date_type=creation+date&tf_radio=1&timeframe=any&from_date=&to_date=&untouched_date=&orderticketsby=REQUEST_ID&orderhow=desc&search_submit=GO%21&writeFormat=XML" -o /afs/cern.ch/user/c/cmst1/scratch0/MonitoringScripts/GGUS/tickets.xml
python /afs/cern.ch/user/c/cmst1/scratch0/MonitoringScripts/GGUS/ggus.py &> /afs/cern.ch/user/c/cmst1/scratch0/MonitoringScripts/GGUS/ticket.log
cp /afs/cern.ch/user/c/cmst1/scratch0/MonitoringScripts/GGUS/ggusticketmetrics.txt /afs/cern.ch/user/c/cmst1/www/SST/
cp /afs/cern.ch/user/c/cmst1/scratch0/MonitoringScripts/GGUS/ggusticketmeeting.txt /afs/cern.ch/user/c/cmst1/www/SST