import calendar
import time
import json
import pprint
import urllib
import ssl
import sys
import os
from datetime import datetime, timedelta
from lib import dashboard, sites, url
import dateutil.parser


perTierVeto ={}
perTierVeto[0] = 0
perTierVeto[1] = 1
perTierVeto[2] = 3
XFERS_COLUMN_NUMBER=16101
def makelink(site, starttime, span, endtime):
    return "https://twiki.cern.ch/twiki/bin/view/CMSPublic/TransferQualityOverview?site=%s&starttime=%s&span=%s&endtime=%s" %(site, starttime, span, endtime)

# Reads a metric from SS1B
def getJSONMetric(metricNumber, hoursToRead, sitesStr, sitesVar, dateStart="2000-01-01", dateEnd=datetime.now().strftime('%Y-%m-%d')):
    urlstr = "http://dashb-ssb.cern.ch/dashboard/request.py/getplotdata?columnid=" + str(metricNumber) + "&time=" + str(hoursToRead) + "&dateFrom=" + dateStart + "&dateTo=" + dateEnd + "&site=" + sitesStr + "&sites=" + sitesVar + "&clouds=all&batch=1"
    try:
        metricData = url.read(urlstr)
        return dashboard.parseJSONMetric(metricData)
    except:
        return None

def getJSONMetricforAllSites(metricNumber, hoursToRead):
    return getJSONMetric(metricNumber, hoursToRead, "custom", "all")

def getJSONMetricforAllSitesForDate(metricNumber, dateStart, dateEnd):
    return getJSONMetric(metricNumber, "custom", "", "all", dateStart, dateEnd)


#@profile
def main():
    #Make a pretty printer
    print "--------------------------\nStarting at " +str(datetime.now()) 
    pp = pprint.PrettyPrinter()
    OUTPUT_FILE_NAME = os.path.join(sys.argv[2],"xfers.txt")
    OUTPUT_FILE_CORRECTIONS = os.path.join(sys.argv[2],"xfers_POSTREQUEST.txt")
    #Get transfer history
    binwidth = 6*60*60
    datetmp = dateutil.parser.parse(sys.argv[1], ignoretz=True)
    print datetmp
    endtime = (int(calendar.timegm(datetmp.timetuple()))/binwidth)*binwidth
    starttime = endtime-binwidth
    starttime_str = (datetime.fromtimestamp(starttime)).strftime("%Y-%m-%d %H:%M:%S")
    endtime_srt =  (datetime.fromtimestamp(endtime)).strftime("%Y-%m-%d %H:%M:%S")
    params = {'binwidth': binwidth, 'starttime': starttime , 'endtime': endtime}
    Morgue_Sites =  []
    lifeStatus = getJSONMetricforAllSites(235, 24)
    sites = lifeStatus.getSites()
    for site in sites:
        site_status = lifeStatus.getLatestEntry(site)
        if site_status.value != "enabled":
            Morgue_Sites.append(site)
    url = 'https://cmsweb.cern.ch/phedex/datasvc/json/%s/TransferHistory'
    print url+"?"+urllib.urlencode(params)
    context = None #ssl._create_unverified_context()
    f_debug = urllib.urlopen(url %'debug',data=urllib.urlencode(params))
    items_debug =json.load(f_debug)
    f_prod = urllib.urlopen(url %'prod',data=urllib.urlencode(params))
    items_prod =json.load(f_prod)
    timeslots = set()
    xferdata = {}
    noTransfersToFrom = {}
    noTransfersToFrom2 = {}
    for item in items_debug["phedex"]["link"] + items_prod["phedex"]["link"]:
        from_site = item['from'] #.replace('_MSS','').replace('_Buffer', '').replace('_Disk','').replace('_Export','')
        to_site= item['to'] #.replace('_MSS','').replace('_Buffer', '').replace('_Disk','').replace('_Export','')
        if to_site == from_site:
            continue 
        to_tier = int(to_site[1])
        from_tier = int(from_site[1])
        to_tier = 1 if to_tier==0 else to_tier
        from_tier = 1 if from_tier==0 else from_tier
        for transferslot in item['transfer']:
            try:
                quality = float(transferslot['quality'])
            except:
                quality = 0.0
            done_files = int(transferslot['done_files'])
            fail_files = int(transferslot['fail_files'])
            done_bytes = int(transferslot['done_bytes'])
            fail_bytes = int(transferslot['fail_bytes'])
            try_files = int(transferslot['try_files'])
            timeslot = int(transferslot['timebin'])
            if from_site not in Morgue_Sites and to_site not in Morgue_Sites and try_files > 0:
                noTransfersToFrom[from_site][timeslot] = noTransfersToFrom.setdefault(from_site,{}).setdefault(timeslot,0) + try_files
                noTransfersToFrom[to_site][timeslot] = noTransfersToFrom.setdefault(to_site,{}).setdefault(timeslot,0) + try_files
                noTransfersToFrom2[from_site][timeslot] = noTransfersToFrom2.setdefault(from_site,{}).setdefault(timeslot,0) + 1
                noTransfersToFrom2[to_site][timeslot] = noTransfersToFrom2.setdefault(to_site,{}).setdefault(timeslot,0) + 1 
 
            timeslots.add(timeslot)
            if to_tier < 3 and from_tier < 3 and (done_bytes > 0 or fail_bytes >0) and try_files > 0 :
                xferdata.setdefault(from_site,{}).setdefault(timeslot,{}).setdefault("to", {}).setdefault(to_tier,[]).append([quality, done_files, fail_files, done_bytes, fail_bytes, to_site])
                xferdata.setdefault(to_site,{}).setdefault(timeslot,{}).setdefault("from", {}).setdefault(from_tier,[]).append([quality, done_files, fail_files, done_bytes, fail_bytes, from_site])
            #xferdate[site][from][tier][site][donefile, failfiles, donebytes, failbytes]
            #pp.pprint([from_site, to_site, quality, done_files, fail_files])
    del items_debug
    siteScores = {}
    
    for site, bincontent in xferdata.iteritems():
        for timeslot, xfers in bincontent.iteritems():
            print site
            for toFrom in ['from', 'to']:
                xfers_tofrom = xfers.get(toFrom, {})
                for tier, xfers_from_tier in xfers_tofrom.iteritems():
                    print "----------"
                    print "Tier" + str(tier)
                    print "Original sorted"
                    xfers_from_tier.sort(key=lambda x: x[2])
                    pp.pprint(len(xfers_from_tier))
                    pp.pprint(xfers_from_tier)
                    # Remove up to [1 for T1, ]
                    for _ in range(0, min(xfers_from_tier, perTierVeto[tier])):
                        xfers_from_tier.sort(key=lambda x: x[2])
                        if len(xfers_from_tier)>0 and xfers_from_tier[-1][2] > 1:
                            #print "  deleted for highest failure files " + str(xfers_from_tier[-1]) 
                            xfers_from_tier.remove(xfers_from_tier[-1])
                        xfers_from_tier.sort(key=lambda x: x[0], reverse=True)
                        if len(xfers_from_tier)>0 and xfers_from_tier[-1][0] < 0.9 :
                            #print "  deleted for highest failure rate " + str(xfers_from_tier[-1])
                            xfers_from_tier.remove(xfers_from_tier[-1])
                    print "After deletion"
                    pp.pprint(len(xfers_from_tier))
                    pp.pprint(xfers_from_tier)
                    print "----------"
                    for xfer in xfers_from_tier:
                        siteScores.setdefault(site,{}).setdefault(timeslot,{}).setdefault(toFrom,{}).setdefault(tier,{}).setdefault('done',0)
                        siteScores[site][timeslot][toFrom][tier]['done'] += xfer[1] 
                        siteScores.setdefault(site,{}).setdefault(timeslot,{}).setdefault(toFrom,{}).setdefault(tier,{}).setdefault('failed',0)
                        siteScores[site][timeslot][toFrom][tier]['failed'] += xfer[2]
    #pp.pprint(timeslots)
    slotList = (list(timeslots))
    slotList.sort()
    emptylist = ['n'] * len(slotList)
    outputFile = open('output.csv', 'w')
    excelDate = lambda x: (float(x) / 86400.0) + 25569.0
    outputFile.write("Site," + ",".join([str(excelDate(x)) for x in slotList])+"\n")
    for site, scoresPerSlot in siteScores.iteritems():
        siteList = list(emptylist)
        for i in range(0, len(slotList)):
            if slotList[i] in scoresPerSlot:                
                scores = scoresPerSlot[slotList[i]]
                score = 10.0
                for tag in ['to','from']:
                        for tier in [0,1,2]:
                            try:
                                score = min(score, float(scores.get(tag,{}).get(tier,{}).get('done',0) )/ float(scores.get(tag,{}).get(tier,{}).get('done',0) + scores.get(tag,{}).get(tier,{}).get('failed',0)))
                            except:
                                    continue
                            #print tag + " " + str(tier) + ", score: " + str(score) 
                siteList[i] = score
        #print site + " " + str(siteList)
        outputFile.write(site+ "," + ",".join([str(x) for x in siteList])+"\n")
    xferMetricEntries = []
    
    for site, timeslotObj in siteScores.iteritems():
        score = 666
        for timeslot, scores in timeslotObj.iteritems():
            for x in slotList:
                print site + "," + str(timeslot) 
                for tag in ['to','from']:
                    for tier in [0,1,2]:
                        try:
                            print "tier: " + str(tier) + "to/from: "+ tag + "score: " + str(float(scores.get(tag,{}).get(tier,{}).get('done',0) )/ float(scores.get(tag,{}).get(tier,{}).get('done',0) + scores.get(tag,{}).get(tier,{}).get('failed',0)))
                            score = min(score, float(scores.get(tag,{}).get(tier,{}).get('done',0) )/ float(scores.get(tag,{}).get(tier,{}).get('done',0) + scores.get(tag,{}).get(tier,{}).get('failed',0)))
                        except:
                                continue
                site_value = "%.1f" % (score*100)
                site_nvalue = score*100
                if score == 666:
                    site_color = "white"
                    site_value = "n/a"
                elif score > 0.6 :
                    site_color = "green"
                else :
                    site_color = "red"
                justSite = site.replace("_Disk","").replace("_Buffer","").replace("_Export","").replace("_MSS","") 
                if site != justSite:
                    addnew = True
                    for entry in xferMetricEntries:
                        if entry.name == justSite and entry.nvalue < site_nvalue:
                           addnew = False
                           break
                        if entry.name == justSite and entry.nvalue > site_nvalue:
                           xferMetricEntries.remove(entry)
                           addnew = True

                    if (addnew):
                        xferMetricEntries.append(dashboard.entry(date = starttime_str, name = justSite, value = site_value, color = site_color, url = makelink(site, starttime, binwidth, endtime), nvalue = site_nvalue))

                xferMetricEntries.append(dashboard.entry(date = starttime_str, name = site, value = site_value, color = site_color, url = makelink(site, starttime, binwidth, endtime), nvalue = site_nvalue))
    if len(xferMetricEntries) > 1:
        outputFile = open(OUTPUT_FILE_NAME, 'w')
        correctionOutputFile = open(OUTPUT_FILE_CORRECTIONS, 'a')
        for site in xferMetricEntries:
            outputFile.write(str(site) + '\n')
            correctionOutputFile.write(("\t".join([starttime_str, endtime_srt, str(XFERS_COLUMN_NUMBER), site.name, site.value, site.color, site.url, "nvalue=0"]))+"\n")
        print "\n--Output written to %s" % OUTPUT_FILE_NAME
        outputFile.close()
        correctionOutputFile.close()
    print "--------------------------\nFinished at " +str(datetime.now()) 

if __name__ == '__main__':
    main()
