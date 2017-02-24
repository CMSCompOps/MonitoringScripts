from datetime import datetime, date, timedelta
from lib import dashboard, sites, url

from ggus import Ticket

# Reads a metric from SSB
def getJSONMetric(metricNumber, hoursToRead, sitesStr, sitesVar, dateStart="2000-01-01", dateEnd=datetime.now().strftime('%Y-%m-%d')):
	urlstr = "http://dashb-ssb.cern.ch/dashboard/request.py/getplotdata?columnid=" + str(metricNumber) + "&time=" + str(hoursToRead) + "&dateFrom=" + dateStart + "&dateTo=" + dateEnd + "&site=" + sitesStr + "&sites=" + sitesVar + "&clouds=all&batch=1"
	print urlstr
	try:
		metricData = url.read(urlstr)
		return dashboard.parseJSONMetric(metricData)
	except:
		return None


def getJSONMetricforAllSitesForDate(metricNumber, dateStart, dateEnd):
	return getJSONMetric(metricNumber, "custom", "", "all", dateStart, dateEnd)


waiting_room_subject = '%s was moved to the waiting room'
waiting_room_description = '''
	Dear site admin,

	%s was moved to the waiting room because of %s problems. Could you take a look?

	https://cms-site-readiness.web.cern.ch/cms-site-readiness/SiteReadiness/HTML/SiteReadinessReport.html#%s
	
	'''

#date_today = date.today()
date_today=date(2017,02,17)
print "NOW: %s" %date_today

date_yesterday = date_today + timedelta(days=-1)
print "YESTERDAY: %s" %date_yesterday

date_tomorrow = date_today + timedelta(days=1)
print "TOMORROW: %s" %date_tomorrow

life_status_metric=235
hc_metric=135
sam_metric=126
T1_T2_links_metric=78
T2_T1_links_metric=79  

sam_results='http://wlcg-sam-cms.cern.ch/templates/ember/#/historicalsmry/heatMap?profile=CMS_CRITICAL_FULL&site=%s&time=24h&view=Test%%20History \n \n'
hc_results='http://dashb-cms-job.cern.ch/dashboard/templates/web-job2/#user=&refresh=0&table=Jobs&p=1&records=25&activemenu=1&usr=&site=%s&submissiontool=&application=&activity=hctest&status=&check=submitted&tier=&date1='+ str(date_yesterday) +'&date2='+ str(date_today) +'33&sortby=activity&scale=linear&bars=20&ce=&rb=&grid=&jobtype=&submissionui=&dataset=&submissiontype=&task=&subtoolver=&genactivity=&outputse=&appexitcode=&accesstype=&inputse=&cores= \n \n'
t1_t2_results='https://cmsweb.cern.ch/phedex/graphs/quality_all?link=link&no_mss=true&to_node=%s&from_node=T[01]&starttime='+ date_yesterday.strftime("%s") +'&span=3600&endtime='+ date_today.strftime("%s") +' \n \n'
t2_t1_results='https://cmsweb.cern.ch/phedex/graphs/quality_all?link=link&no_mss=true&to_node=T[01]&from_node=%s&starttime='+ date_yesterday.strftime("%s") +'&span=3600&endtime='+ date_today.strftime("%s") +' \n \n'
phedex_erros='https://cmsweb.cern.ch/phedex/prod/Activity::ErrorInfo?tofilter=%s&fromfilter=.*&report_code=.*&xfer_code=.*&to_pfn=.*&from_pfn=.*&log_detail=.*&log_validate=.*&.submit=Update \n \n'
sr_twiki='https://twiki.cern.ch/twiki/bin/view/CMS/SiteSupportSiteStatusSiteReadiness#Life_Status'

lifeStatus_metric_today = getJSONMetricforAllSitesForDate(life_status_metric, str(date_today), str(date_tomorrow))
lifeStatus_metric_yesterday = getJSONMetricforAllSitesForDate(life_status_metric, str(date_yesterday), str(date_today))
hc = getJSONMetricforAllSitesForDate(hc_metric, str(date_today), str(date_tomorrow))
sam = getJSONMetricforAllSitesForDate(sam_metric, str(date_today), str(date_tomorrow))
T2_T1_links = getJSONMetricforAllSitesForDate(T2_T1_links_metric, str(date_today), str(date_tomorrow))
T1_T2_links = getJSONMetricforAllSitesForDate(T1_T2_links_metric, str(date_today), str(date_tomorrow))


new_state_sites = []
for site in lifeStatus_metric_today.getSites():
	if lifeStatus_metric_today.getLatestEntry(site).value != lifeStatus_metric_yesterday.getLatestEntry(site).value:
		problems=[]
		if hc.getLatestEntry(site):
			if hc.getLatestEntry(site).color == 'red': problems.append("HammerCloud")
		if sam.getLatestEntry(site):
			if sam.getLatestEntry(site).color == 'red': problems.append("SAM")
		if T2_T1_links.getLatestEntry(site):
			if T2_T1_links.getLatestEntry(site).color == 'red': problems.append("T2_T1_links")
		if T1_T2_links.getLatestEntry(site): 
			if T1_T2_links.getLatestEntry(site).color == 'red': problems.append("T1_T2_links")
		item = {
			"cms_name": site,
			"name": sites.getSites()[site]['name'],
			"new_status": lifeStatus_metric_today.getLatestEntry(site).value,
			"old_status": lifeStatus_metric_yesterday.getLatestEntry(site).value,
			"problems": ', '.join(problems)
		}
		new_state_sites.append(item)

for site in new_state_sites:
	if site['new_status'] == "waiting_room":
		subject = waiting_room_subject %(site['cms_name'])
		description = waiting_room_description %(site['cms_name'], site['problems'], site['cms_name'])
		if 'HammerCloud' in site['problems']:
			description = description + hc_results % site['cms_name']
		if 'SAM' in site['problems']:
			description = description + sam_results % site['cms_name']
		if "T2_T1_links" in site['problems']: 
			description = description + t2_t1_results % site['cms_name'] + phedex_erros % site['cms_name']
		if "T1_T2_links" in site['problems']:
			description = description + t1_t2_results % site['cms_name'] + phedex_erros % site['cms_name']
		description = description + sr_twiki
		print "SUBJECT: " + subject
		print "TICKET DESCRIPTION: " + description
		var = raw_input("If you want to create a ticket press - y, if not - n: \n")
		if var == 'y':
			ticket = Ticket(site['name'], subject, description)
			ticket.create()
