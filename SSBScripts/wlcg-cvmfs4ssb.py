#! /bin/env python

import urllib, json, datetime
from xml.parsers import expat

class c4s :

  def __init__(self):
    self.baseDir = '/afs/cern.ch/cms/LCG/SiteComm/'
    self.cvmfsBaseVersionFile = self.baseDir+'cvmfsVersion.txt'
    self.requestedVersion = ''
    self.myVO = 'CMS'
    self.cvmfsColumnNo = 226
    self.wlcgTopoColumnNo = 135
    self.topoDict = {'WLCG':{}, self.myVO:{}}
    self.ssbTimePat = '%Y-%m-%dT%H:%M:%S'
    self.dontpanic = 'http://www.adluge.com/wp-content/uploads/2013/09/homer-simpson-doh.gif'
    self.topologyURL = 'http://dashb-cms-vo-feed.cern.ch/dashboard/request.py/cmssitemapbdii'
    self.wlcgBaseUrl = 'http://wlcg-mon.cern.ch/dashboard/request.py/'
    self.wlcgGetUrl = self.wlcgBaseUrl+'getplotdata?columnid=%d&time=24&sites=all&batch=1'
    self.wlcgExpBaseUrl = 'http://wlcg-sam-cms.cern.ch/dashboard/request.py/'
    self.ssbMetrics = ['CvmfsVersion','CvmfsRepoRevision','CvmfsMountPoint','CvmfsProbeTime', 'CvmfsStratumOnes', 'CvmfsNumSquids', 'CvmfsProbeNoInfo', 'CvmfsProbeLink']
    self.ssbData = {}
    for k in self.ssbMetrics : self.ssbData[k] = {}


  ### start probe functions ###
  ### eval functions ###

  def evalCvmfsProbeLink(self, val, site):
    return (val, 'green')

  def evalCvmfsProbeNoInfo(self, val, site) :
    if self.ssbData['CvmfsProbeTime'][site] == 'no probe' : return ('n/a (no probe)', 'grey')
    if self.ssbData['CvmfsVersion'][site] == 'not installed' : return ('n/a (not installed)', 'grey')
    we = val.split(':')[0]
    if we == 'WARNING' : return (val, 'orange')
    if we == 'ERROR' : return (val, 'red')
    return (val, 'green')

  def evalCvmfsVersion(self, val, site): 
    if self.ssbData['CvmfsProbeTime'][site] == 'no probe' : return ('n/a (no probe)', 'grey')
    if val == 'nfs' : return (val, 'green')
    if val in ('n/a', 'not installed') : return (val, 'red')
    x = 2
    maxDiff = range(x+1)
    deplV = map(lambda x: int(x), val.split('.'))
    reqV = map(lambda x: int(x), self.requestedVersion.split('.'))
    if deplV[1] == reqV[1] and deplV[0] == reqV[0] : 
      if (deplV[2] - reqV[2]) >= 0 : return (val, 'green')
      else : return (val, 'orange')
    else : return (val, 'red')

  def evalCvmfsRepoRevision(self, val, site):
    if self.ssbData['CvmfsProbeTime'][site] == 'no probe' : return ('n/a (no probe)', 'grey')
    vers = self.ssbData['CvmfsVersion'][site]
    if  vers in ('nfs', 'not installed') : return ('n/a (%s)'%vers, 'grey')
    return (val, 'green')

  def evalCvmfsMountPoint(self, val, site):
    if self.ssbData['CvmfsProbeTime'][site] == 'no probe' : return ('n/a (no probe)', 'grey')
    vers = self.ssbData['CvmfsVersion'][site]
    if  vers in ('not installed') : return ('n/a (%s)'%vers, 'grey')
    if val and val == '/cvmfs/cms.cern.ch' : return (val, 'green')
    else : return (val, 'orange')

  def evalCvmfsCondDBMountPoint(self, val, site):
    if self.ssbData['CvmfsProbeTime'][site] == 'no probe' : return ('n/a (no probe)', 'grey')
    if  self.ssbData['CvmfsVersion'][site] == 'not installed' : return ('n/a (not installed)', 'grey')
    if val == 'yes' : return (val, 'orange')
    else : return (val, 'green')

  def evalCvmfsProbeTime(self, val, site):
    if val == 'no probe' : return (val, 'red')
    pTime = datetime.datetime.strptime(val,self.ssbTimePat)
    curTime = datetime.datetime.now()
    delta = (curTime - pTime).seconds
    if delta < 21600 : return (val, 'green')
    elif delta < 43200 : return (val, 'orange')
    else : return (val, 'red')

  def evalCvmfsStratumOnes(self, val, site) :
    if self.ssbData['CvmfsProbeTime'][site] == 'no probe' : return ('n/a (no probe)', 'grey')
    vers = self.ssbData['CvmfsVersion'][site]
    if  vers in ('nfs', 'not installed') : return ('n/a (%s)'%vers, 'grey')
    if val : return (val, 'green')
    else: return ('none', 'red')

  def evalCvmfsNumSquids(self, val, site):
    if self.ssbData['CvmfsProbeTime'][site] == 'no probe' : return ('n/a (no probe)', 'grey')
    vers = self.ssbData['CvmfsVersion'][site]
    if  vers in ('nfs', 'not installed') : return ('n/a (%s)'%vers, 'grey')
    if val :
      if int(val) > 1 : return (val, 'green')
      else : return (val, 'orange')
    else: return (val , 'red')

  ### retrieval functions ###

  def getValCvmfsProbeLink(self, site, probe, metric):
    self.ssbData['CvmfsProbeLink'][site]=metric['URL']

  def getValCvmfsProbeNoInfo(self, site, probe, metric): 
    val = 'none'
    pat = 'INFO: Mandatory tests exectuted successfully, now continuing with testing optional repositories'
    for line in probe :
      we = line.split(':')[0]
      if line[:len(pat)] == pat : break
      elif we == 'WARNING' and val.split(':')[0] != 'ERROR' : val = line
      elif we == 'ERROR' : val = line
    self.ssbData['CvmfsProbeNoInfo'][site] = val[:60]

  def getValCvmfsVersion(self, site, probe, metric):
    pat1 = 'INFO: CVMFS version installed '
    pat2 = 'INFO: Mandatory mount point /cvmfs/cms.cern.ch is nfs mount point'
    pat3 = 'INFO: No cvmfs rpms found on WN, checking if this WN uses nfs mounting of CVMFS repositories'
    ver = 'n/a'
    noCVMFS = False
    cvmfsViaNFS = False
    for line in probe :
      if line[:len(pat1)] == pat1 :
        ver = line[len(pat1):]
      elif line[:len(pat2)] == pat2 :
        ver = 'nfs'
        cvmfsViaNFS = True
      elif line[:len(pat3)] == pat3 : 
        noCVMFS = True
    if noCVMFS and not cvmfsViaNFS : ver = 'not installed'
    self.ssbData['CvmfsVersion'][site] = ver
    
  def getValCvmfsRepoRevision(self, site, probe, metric):
    pat = 'INFO: repository revision '
    rev = 'n/a'
    for line in probe :
      if line[:len(pat)] == pat :
        rev = line[len(pat):]
        break 
    self.ssbData['CvmfsRepoRevision'][site] = rev

  def getValCvmfsMountPoint(self, site, probe, metric):
    pat1 = 'INFO: Variable VO_CMS_SW_DIR points to CVMFS mount point '
    pat2 = 'INFO: Variable OSG_APP points to CVMFS mount point '
    pat3 = 'INFO: Mandatory mount point /cvmfs/cms.cern.ch is nfs mount point'
    mp = 'n/a'
    for line in probe :
      if line[:len(pat1)] == pat1 :
        mp = line[len(pat1):]
      elif line[:len(pat2)] == pat2 :
        mp = line[len(pat2):]
      elif line[:len(pat3)] == pat3 :
        mp = '/cvmfs/cms.cern.ch'
    self.ssbData['CvmfsMountPoint'][site] = mp

  def getValCvmfsProbeTime(self, site, probe, metric):
    self.ssbData['CvmfsProbeTime'][site] = metric['URL'].split('&')[1].split('=')[1][:-1]
#    self.ssbData['CvmfsProbeTime'][site] = metric['EndTime']

  def getValCvmfsStratumOnes(self, site, probe, metric) :
    strats = []
    pat = 'INFO: Servers: '
    for line in probe :
      if line[:len(pat)] == pat :
        stratumL = line[len(pat):]
        for serv in stratumL.split() :
          strats.append('.'.join(serv.split('/')[2].split(':')[0].split('.')[-2:]))
        break
    self.ssbData['CvmfsStratumOnes'][site] = ' '.join(strats)

  def getValCvmfsNumSquids(self, site, probe, metric) :
    numSq = 0
    pat = 'INFO: Proxies: '
    for line in probe :
      if line[:len(pat)] == pat :
        numSq = len(line[len(pat):].split())
        break
    self.ssbData['CvmfsNumSquids'][site] = numSq

  ### end probe functions ####

  def xmlStartElement(self, name, attrs):
    if name == 'atp_site' : self.currWLCGSite = attrs['name']
    if name == 'group' and attrs['type'] == 'CMS_Site' : 
      self.topoDict['WLCG'][attrs['name']] = self.currWLCGSite

  def bootstrap(self):
    # get WLCG Mon mapping VO site name <-> site ID
    topo = json.loads(urllib.urlopen(self.wlcgGetUrl%self.wlcgTopoColumnNo).read())
    for ent in topo['csvdata'] : self.topoDict[self.myVO][ent['SiteId']] = ent['Status']
    # read CVMFS base line version number
    f = open(self.cvmfsBaseVersionFile, 'r')
    self.requestedVersion = f.read()
    f.close()
    # read topology file and create mapping VO site name <-> WLCG site name
    topo = urllib.urlopen(self.topologyURL).read()
    p = expat.ParserCreate()
    p.StartElementHandler = self.xmlStartElement
    p.Parse(topo)

  def clearSsbData(self, site):
    for metric in self.ssbMetrics : 
      self.ssbData[metric][site] = ''

  def collectInfo(self):
    info = json.loads(urllib.urlopen(self.wlcgGetUrl%self.cvmfsColumnNo).read())
    for metricInf in info['csvdata'] :
      site = self.topoDict[self.myVO][metricInf['SiteId']]
      tTime = datetime.datetime.strptime(metricInf['Time'], self.ssbTimePat)
      dTime = self.ssbData['CvmfsProbeTime'].get(site)
      if ( not dTime ) or ( datetime.datetime.strptime(dTime, self.ssbTimePat) < tTime ) :  
        if dTime : self.clearSsbData(site)
        tl = urllib.urlopen(self.wlcgExpBaseUrl+metricInf['URL']).read().split('\n')
        for metr in self.ssbMetrics : eval('self.getVal'+metr)(site, tl, metricInf)
    for site in self.topoDict['WLCG'].keys() : 
      if not self.ssbData['CvmfsProbeTime'].get(site) : 
        for metric in self.ssbMetrics : self.ssbData[metric][site] = ''
        self.ssbData['CvmfsProbeTime'][site] = 'no probe'
              
  def writeSSBColumns(self):
    for k in self.ssbMetrics :
      fun = 'self.eval'+k
      colData = self.ssbData[k]
      f = open(self.baseDir+k+'.ssb.txt', 'w')
      for site in colData.keys() :
        now = str(datetime.datetime.now())
        (val, color) = eval(fun)(colData[site], site)
        url = self.dontpanic
        if self.ssbData['CvmfsProbeLink'].get(site): url = self.wlcgExpBaseUrl+self.ssbData['CvmfsProbeLink'][site]
        f.write('%s\t%s\t%s\t%s\t%s\n' % (now, site, val, color, url))
      f.close()

  def run(self):
    self.bootstrap()
    self.collectInfo()
    self.writeSSBColumns()

if __name__ == '__main__' :
  c4s().run()
