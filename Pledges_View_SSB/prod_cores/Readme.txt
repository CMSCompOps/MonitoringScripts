--INFO--
Script for Dashboard metric 159: Prod [cores]
Script responsible: John Artieda (artiedaj@fnal.gov)
output dir 	/afs/cern.ch/user/c/cmst1/www/SST/
output file 	prod.txt
web		https://cmst1.web.cern.ch/CMST1/SST/prod.txt

—-
Script in acrontab cmst1
*/05 * * * * lxplus /afs/cern.ch/user/c/cmst1/scratch0/MonitoringScripts/Pledges_View_SSB/prod_cores/run_prodcores.sh &> /dev/null