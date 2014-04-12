Generic File Monitoring
CMSSW-based file-opening popularity reporting in TFC
- how many sites are doing this
- check site config files - script to count how many
- new metric in SSB - test View (once a day)

* instructions at https://twiki.cern.ch/twiki/bin/view/Main/GenericFileMonitoring 
- Edit the site-local-config.xml to enable it and set the destination
- The additional line goes in the source-config stanza:
     statistics-destination name="cms-udpmon-collector.cern.ch:9331"