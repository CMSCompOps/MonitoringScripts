
THIS LIST IS THE BASIS FOR  ALL THE OTHER “Waiting Room” RELATED METRICS 
in the SiteReadiness View in SSB

Sites that appear in this list are the sites that have been commissioned
and that presently are in "active" status.

--- ACTIVE sites for  SSB ---
SSB metric: 		39 - Active T2s
Active Sites:		SR >=80% last 1 week OR last 3 months

--- WAITING ROOM LIST for SSB ---
Any site that is not in this list will be automatically moved to the Waiting Room.

--- INFO ---
# acronjob in acrontab cmst1
# 00 08 * * 1 => Every monday at 8AM
# 00 08 * * 1 lxplus /afs/cern.ch/user/c/cmst1/scratch0/MonitoringScripts/SR_View_SSB/ActiveSites/sActiveSites.sh &> /dev/null

Script name:
	sActiveSites.sh

Script Location:
	/afs/cern.ch/user/c/cmst1/scratch0/MonitoringScripts/SR_View_SSB/ActiveSites

Github repository:
	https://github.com/CMSCompOps/MonitoringScripts/SR_View_SSB/ActiveSites/

Output copy used by SSB:
	File: WasCommissionedT2ForSiteMonitor.txt
	Location: /afs/cern.ch/cms/LCG/SiteComm/T2WaitingList/ 
	Web: https://cmsdoc.cern.ch/cms/LCG/SiteComm/T2WaitingList/WasCommissionedT2ForSiteMonitor.txt
	Every time the script runs, it saves an old copy (.OLD) of the previous list here:
	/afs/cern.ch/cms/LCG/SiteComm/T2WaitingList/

--- PROCEDURE TO CHANGE THE LIST---
1. make sure you are in AFS group zh:lcg_writers
	using e.g. the command:  pts membership zh:lcg_writers
	if not, ask CMS AFS admins

2. vim /afs/cern.ch/cms/LCG/SiteComm/T2WaitingList/WasCommissionedT2ForSiteMonitor.txt

3. To move a site IN the WR
comment (#) the line with the name of the site in the file: 
	Output copy used by SSB

4. To move a site OUT of the WR
add a new line with the name of the site in the file: 
	Output copy used by SSB.
	* IMPORTANT: 
		a. values must be the same as for the other sites
		b. values MUST be TAB separated

--- PROCEDURE TO TEST CHANGES IN THE SCRIPT ---
1. make sure you are in AFS group zh:lcg_writers
	using e.g. the command:  pts membership zh:lcg_writers
	if not, ask CMS AFS admins
2. cd Script location
3. update from the github repository
	git pull
4. edit sActiveSites.sh as proper
	cd MonitoringScripts/SR_View_SSB/ActiveSites/
	vim sActiveSites.sh
5. run with ./sActiveSites.sh
	that will create a new file in /afs/cern.ch/cms/LCG/SiteComm/T2WaitingList/
	and save previous one in <...>.OLD so you
	can x-check what you have done
6. IMPORTANT: push your changes to github (create a pull request)
	git commit -a
	(include "some decent comment")
	git push