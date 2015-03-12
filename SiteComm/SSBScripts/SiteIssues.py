#!/usr/bin/python
import string, os, datetime
import xml.dom.minidom
from xml import xpath

def getChildValue(element, child):
  child = element.getElementsByTagName(child)[0].firstChild
  if child is not None:
    return str(child.nodeValue)
  return None

countryToROC={
    'AT':'ROC_CE',
    'BE':'ROC_North',
    'BR':'ROC_CERN',
    'CH':'ROC_DECH',
    'CN':'ROC_Asia/Pacific',
    'CO':'ROC_CERN',
    'DE':'ROC_DECH',
    'EE':'ROC_North',
    'ES':'ROC_SW',
    'FI':'ROC_North',
    'FR':'ROC_France',
    'GR':'ROC_SE',
    'HU':'ROC_CE',
    'IN':'ROC_Asia/Pacific',
    'IT':'ROC_Italy',
    'KR':'ROC_Asia/Pacific',
    'MX':'ROC_CERN',
    'PK':'ROC_Asia/Pacific',
    'PL':'ROC_CE',
    'PT':'ROC_SW',
    'RU':'ROC_Russia',
    'TR':'ROC_SE',
    'TW':'ROC_Asia/Pacific',
    'UA':'ROC_Russia',
    'UK':'ROC_UK/Ireland',
    'US':'ROC_CERN'
    }

today=datetime.datetime.utcnow()
oneweekago=today-datetime.timedelta(7)
timestamp=today.strftime("%Y-%m-%d %H:%M:%S")


ggusBaseUrl="https://gus.fzk.de/pages/ticket_search.php?ticket=&supportunit=%s&vo=all&user=&keyword=&involvedsupporter=&assignto=&specattrib=0&status=all&priority=all&typeofproblem=all&radiotf=1&timeframe=lastweek&orderticketsby=GHD_EXPERIMENT&orderhow=desc"

ggusBaseUrlBySite="https://gus.fzk.de/ws/ticket_search.php?ticket=&affectedsite=%s&vo=all&user=&keyword=&involvedsupporter=&assignto=&specattrib=0&status=all&priority=all&typeofproblem=all&radiotf=1&timeframe=lastweek&orderticketsby=GHD_EXPERIMENT&orderhow=desc"



savannahBaseUrl="https://savannah.cern.ch/support/index.php?go_report=Apply&group=cmscompinfrasup&func=browse&set=custom&msort=0&report_id=187&advsrch=0&details=%s&summary=%s&category_id=0&status_id=0&sumORdet=1&history_search=0&history_field=0&history_event=modified&chunksz=50&spamscore=5&boxoptionwanted=1#options"


hnBaseUrl_1="https://hypernews.cern.ch/HyperNews/CMS/search?query=%s+and+(forum=sc4+or+forum=dataops)&submit=Search!&metaname=swishdefault&sort=swishrank"

hnBaseUrl_2="&dr_s_mon=%d&dr_s_day=%d&dr_s_year=%d&dr_e_mon=%d&dr_e_day=%d&dr_e_year=%d" % (oneweekago.month, oneweekago.day, oneweekago.year, today.month, today.day, today.year)

hnBaseUrl=hnBaseUrl_1 + hnBaseUrl_2

ssbTktBaseUrl="http://dashb-ssb-devel.cern.ch/dashboard/request.py/ticketsform?site=%s"

sitePageBaseUrl="http://cmsdoc.cern.ch/cms/LCG/SiteComm/SiteIssues/%s.html"

sitePageBase='<html><body>\n'
sitePageBase='<h2>Open Issues for site %s</h2>\n'
sitePageBase+='<p>Known issues that may involve this site\n'
sitePageBase+='<ul>\n'
sitePageBase+='<li>Tickets associated to this site in CMS Site Status Board : '
sitePageBase+='<a href="%s">link</a>\n'
sitePageBase+='<li>Computing Infrastructure Savannah (all) : '
sitePageBase+='<a href="%s">link</a>\n'
sitePageBase+='<li>GGUS for this site (last week) : '
sitePageBase+='<a href="%s">link</a>\n'
sitePageBase+='<li>GGUS for the ROC this site belons to (last week) : '
sitePageBase+='<a href="%s">link</a>\n'
sitePageBase+='<li>CMS HyperNews (last week) (limited to Facilities Operations and Data Operations fora) : '
sitePageBase+='<a href="%s">link</a>\n'

sitePageBase+='</ul>\n'
sitePageBase+="<p>Link to site's own information/news page:"
sitePageBase+='<a href="undefined">NotYet</a>\n'
sitePageBase+='<p>\n'
sitePageBase+='<p>\n'
sitePageBase+='</body></html>\n'

fileNameForSSB="SiteIssues.txt"

# get list of sites from SiteDB naming_convention report

pid=os.getpid()
namesUrl= 'https://cmsweb.cern.ch/sitedb/sitedb/reports/showXMLReport/?reportid=naming_convention.ini'
fileN="/tmp/sitelist.%i" % pid
#fileN="/home/belforte/cms/SM/test/sitelist"
os.system('wget -q --no-check-certificate -O  %s %s' % (fileN, namesUrl))
f=file(fileN,'r')

t= xml.dom.minidom.parse(f)
f.close()
siteList={}
for url in xpath.Evaluate('report/result/item', t):
  samName=getChildValue(url, 'sam')
  cmsName=getChildValue(url, 'cms')
  if cmsName not in siteList.keys():
    siteList[cmsName]=samName

siteNames=siteList.keys()
siteNames.sort()

#print siteNames


ssbFile=file(fileNameForSSB,'w')

for site in siteNames:
    if site == "T1_CH_CERN": continue
    if site == "T2_CH_CAF": continue
    if site == "T2_FR_GRIF_LAL": continue
    if site == "T2_FR_GRIF_LPNHE": continue
    strings=site.split('_')
    tier=int(strings[0][1])
    countryCode=strings[1]
    roc=countryToROC[countryCode]
    if site.find('CERN') != -1:
        roc='ROC_CERN'
    siteString=strings[2]
    sitename='_'.join(strings[2:])
    bdiiSite=siteList[site]

    ggusUrl=ggusBaseUrl % roc
    ggusUrlBySite=ggusBaseUrlBySite % bdiiSite
    savannahUrl=savannahBaseUrl % (siteString, siteString)
    hnUrl=hnBaseUrl % (siteString)
    ssbTktUrl=ssbTktBaseUrl % (site)
    sitePageUrl=sitePageBaseUrl % (site)
    sitePage=sitePageBase % (site, ssbTktUrl, savannahUrl,
                             ggusUrlBySite, ggusUrl,
                             hnUrl)

    ssbFile.write('%s\t%s\t%s\t%s\t%s\t%s\n'% (timestamp, site, "info", "white", sitePageUrl, "ok") )
    siteFileName="%s.html" % site
    siteFile=file(siteFileName, 'w')
    siteFile.write(sitePage)
    siteFile.close()
    
ssbFile.close()
