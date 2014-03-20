README.TXT
--------------------
To fill the Pledges View metrics in SSB like a regular SSB metric, i.e. provide a source txt file for it. 
Example txt file (for SR metric) is 
http://cms-site-readiness.web.cern.ch/cms-site-readiness/SiteReadiness/toSSB/SiteReadiness_SSBfeed.txt

For the 159 metric (MC Thresholds), you need to set timestamp to lets say yesterday, for color you can put 'green' and for url 'n/a'.
 
First set "ColumnFrequency" to something small (600 seconds) so we are sure that the collector feeds the metric at least once. After that set "ColumnFrequency" to 315360000 and "ColumnSource" to null to assure that the collector will never feed this metric again. Now it can be modified only manually. 

Please set ColumnValidity and ColumnFrequency to something huge, let say 315360000 (10 years in seconds), so that we assure that the collector will get the info from the source file only once and will insert big intervals of data. 

After that you will be able to update the values manually. 

This is the recipe for filling any other metric that will be edited by hand. 

Reference:
https://savannah.cern.ch/support/?141661

INSTRUCTIONS TO PUBLISH TO WEB.CERN.CH:
https://twiki.cern.ch/twiki/bin/view/CMSPublic/PublishToWEBCERNCH