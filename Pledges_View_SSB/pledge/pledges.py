#!/usr/bin/python
import os, sys
import simplejson
import json
import time
import urllib, httplib, urllib2
import string
#_____________________________________________________________________________

# function needed to fetch a list of all pledges values from siteDB
def fetch_all_pledges(url,api):
  headers = {"Accept": "application/json"}
  if 'X509_USER_PROXY' in os.environ:
      print 'X509_USER_PROXY found'
      conn = httplib.HTTPSConnection(url, cert_file = os.getenv('X509_USER_PROXY'), key_file = os.getenv('X509_USER_PROXY'))
  elif 'X509_USER_CERT' in os.environ and 'X509_USER_KEY' in os.environ:
      print 'X509_USER_CERT and X509_USER_KEY found'
      conn = httplib.HTTPSConnection(url, cert_file = os.getenv('X509_USER_CERT'), key_file = os.getenv('X509_USER_KEY'))
  else:
      print 'You need a valid proxy or cert/key files'
      sys.exit()
  print 'conn found in if else structure'
  r1=conn.request("GET",api, None, headers)
  print 'r1 passed'
  r2=conn.getresponse()
  print 'r2 passed'
  inputjson=r2.read()
  print '-------------------------------------------------------------'
  jsn = simplejson.loads(inputjson)
  pledges= {}
  pledgesSites = {}
  count = 0
  for i in jsn['result']:
    #_____________________________
    pledgeDate     = i[2]
    pledgeTime     = i[1]
    pledgeSiteName = i[0]
    #pledgeCpuValue = i[3]
    #_____________________________
    if pledgeDate == 2014:
      current = time.time()
      diff = current - pledgeTime
      if pledges.has_key(pledgeSiteName):
        pledges[pledgeSiteName][diff] = {"time":i[1], "cpu":i[3] * 100}
      else:
        pledges[pledgeSiteName] = {diff:{"time":i[1], "cpu":i[3] * 100}}
  for site in pledges.keys():
    min_site = min(pledges[site].keys())
    pledgesSites[site] = pledges[site][min_site]['cpu']
  return pledgesSites
#_____________________________________________________________________________

# function matchs pledges values gets from siteDB with SiteName

def matchPledges(pledgeList):
  pledges = {}
  #sitesList =  ['T1_TW_ASGC','T1_FR_CCIN2P3','T1_CH_CERN','T1_IT_CNAF','T1_US_FNAL','T1_US_FNAL_Disk','T1_RU_JINR','T1_RU_JINR_Disk','T1_DE_KIT','T1_ES_PIC','T1_UK_RAL','T1_UK_RAL_Disk','T2_IT_Bari','T2_CN_Beijing','T2_K_SGrid_Bristol','T2_K_London_Brunel','T2_FR_CCIN2P3','T2_CH_CERN','T2_CH_CERN_AI','T2_CH_CERN_HLT','T2_CH_CERN_T0','T2_ES_CIEMAT','T2_CH_CSCS','T2_TH_CUNSTDA','T2_S_Caltech','T2_DE_DESY','T2_EE_Estonia','T2_S_Florida','T2_FR_GRIF_IRFU','T2_FR_GRIF_LLR','T2_BR_UERJ','T2_FI_HIP','T2_AT_Vienna','T2_HU_Budapest','T2_UK_London_IC','T2_ES_IFCA','T2_RU_IHEP','T2_BE_IIHE','T2_RU_INR', 'T2_FR_IPHC','T2_RU_ITEP','T2_GR_Ioannina','T2_RU_JINR','T2_UA_KIPT','T2_KR_KNU','T2_IT_Legnaro','T2_BE_UCL','T2_TR_METU','T2_US_MIT','T2_PT_NCG_Lisbon','T2_PK_NCP','T2_US_Nebraska','T2_RU_PNPI','T2_IT_Pisa','T2_US_Purde', 'T2_RU_RRC_KI','T2_DE_RWTH','T2_IT_Rome','T2_UK_SGrid_RALPP','T2_RU_SINP','T2_BR_SPRACE','T2_IN_TIFR','T2_TW_Taiwan','T2_US_UCSD','T2_MY_UPM_BIRUNI', 'T2_US_Vanderbilt','T2_PL_Warsaw','T2_US_Wisconsin']
  sitesList =  ['T1_TW_ASGC','T1_FR_CCIN2P3','T1_CH_CERN','T1_IT_CNAF','T1_US_FNAL','T1_US_FNAL_Disk','T1_RU_JINR','T1_RU_JINR_Disk','T1_DE_KIT','T1_ES_PIC','T1_UK_RAL','T1_UK_RAL_Disk','T2_IT_Bari','T2_CN_Beijing','T2_UK_SGrid_Bristol','T2_UK_London_Brunel','T2_FR_CCIN2P3','T2_CH_CERN','T2_CH_CERN_AI','T2_CH_CERN_HLT','T2_CH_CERN_T0','T2_ES_CIEMAT','T2_CH_CSCS','T2_TH_CUNSTDA','T2_US_Caltech','T2_DE_DESY','T2_EE_Estonia','T2_US_Florida','T2_FR_GRIF_IRFU','T2_FR_GRIF_LLR','T2_BR_UERJ','T2_FI_HIP','T2_AT_Vienna','T2_HU_Budapest','T2_UK_London_IC','T2_ES_IFCA','T2_RU_IHEP','T2_BE_IIHE','T2_RU_INR', 'T2_FR_IPHC','T2_RU_ITEP','T2_GR_Ioannina','T2_RU_JINR','T2_UA_KIPT','T2_KR_KNU','T2_IT_Legnaro','T2_BE_UCL','T2_TR_METU','T2_US_MIT','T2_PT_NCG_Lisbon','T2_PK_NCP','T2_US_Nebraska','T2_RU_PNPI','T2_IT_Pisa','T2_US_Purdue', 'T2_RU_RRC_KI','T2_DE_RWTH','T2_IT_Rome','T2_UK_SGrid_RALPP','T2_RU_SINP','T2_BR_SPRACE','T2_IN_TIFR','T2_TW_Taiwan','T2_US_UCSD','T2_MY_UPM_BIRUNI', 'T2_US_Vanderbilt','T2_PL_Warsaw','T2_US_Wisconsin']
  #reportRoot = GetXMLFromURL( "https://cmsweb.cern.ch/sitedb/reports/showXMLReport?reportid=naming_convention.ini")
  #result   = reportRoot.find('result')
  #matchList = {'T3_US_PuertoRico': 'UPRM', 'T2_FI_HIP': 'Helsinki Institute of Physics', 'T2_UK_SGrid_RALPP': 'Rutherford PPD', 'T2_FR_GRIF_LLR': 'GRIF_LLR', 'T2_UK_London_IC': 'IC', 'T3_UK_London_QMUL': 'QMUL', 'T3_TW_NTU_HEP': 'NTU_HEP', 'T3_US_Omaha': 'Firefly', 'T2_KR_KNU': 'KNU', 'T2_RU_SINP': 'SINP', 'T3_US_UMD': 'UMD', 'T2_CH_CERN_AI': 'CERN Tier-2 AI', 'T1_TW_ASGC': 'ASGC', 'T3_US_Colorado': 'Colorado', 'T3_US_UB': 'SUNY_BUFFALO', 'T1_UK_RAL_Disk': 'RALDISK', 'T3_IT_Napoli': 'INFN-NAPOLI-CMS', 'T3_NZ_UOA': 'NZ-UOA', 'T2_TH_CUNSTDA': 'CUNSTDA', 'T3_US_Kansas': 'Kansas', 'T3_US_ParrotTest': 'T3 US ParrotTest', 'T3_GR_IASA': 'IASA', 'T3_US_Parrot': 'T3 US Parrot', 'T2_IT_Bari': 'Bari', 'T2_US_UCSD': 'UCSD', 'T2_RU_IHEP': 'IHEP', 'T3_US_Vanderbilt_EC2': 'Vanderbilt_EC2', 'T1_RU_JINR': 'JINR-T1', 'T2_RU_RRC_KI': 'RRC_KI', 'T2_CH_CERN': 'CERN Tier-2', 'T3_BY_NCPHEP': 'BY-NCPHEP', 'T2_US_Vanderbilt': 'Vanderbilt', 'T3_GR_Demokritos': 'Demokritos', 'T3_US_UTENN': 'UTenn', 'T3_US_UCR': 'UC Riverside', 'T3_TW_NCU': 'NCU', 'T2_CH_CSCS': 'CSCS', 'T2_UA_KIPT': 'KIPT', 'T2_PK_NCP': 'NCP-LCG2', 'T2_RU_PNPI': 'PNPI', 'T2_IN_TIFR': 'TIFR', 'T3_UK_London_UCL': 'University College London', 'T3_US_Brown': 'Brown-CMS', 'T3_US_UCD': 'UCD', 'T3_CO_Uniandes': 'UNIANDES', 'T3_KR_KNU': 'KR_KNU', 'T2_FR_IPHC': 'IPHC', 'T3_US_OSU': 'OSU', 'T3_US_TAMU': 'TAMU', 'T1_US_FNAL': 'FNAL', 'T3_IT_Trieste': 'Trieste', 'T2_IT_Rome': 'Rome', 'T2_UK_London_Brunel': 'Brunel', 'T3_IN_PUHEP': 'PUHEP', 'T3_IT_Firenze': 'Firenze', 'T1_US_FNAL_Disk': 'FNALDISK', 'T2_EE_Estonia': 'Estonia', 'T3_UK_ScotGrid_ECDF': 'ECDF', 'T2_CN_Beijing': 'Beijing', 'T2_US_Florida': 'Florida', 'T3_US_Princeton_ICSE': 'Princeton ICSE ', 'T3_IT_MIB': 'INFN-MIB', 'T3_US_FNALXEN': 'FNALXEN', 'T3_US_Rutgers': 'Rutgers', 'T1_DE_KIT': 'KIT', 'T3_IR_IPM': 'IPM', 'T2_US_Wisconsin': 'Wisconsin', 'T2_HU_Budapest': 'Hungary', 'T2_DE_RWTH': 'RWTH', 'T3_IT_Perugia': 'Perugia', 'T3_UK_SGrid_Oxford': 'Oxford', 'T3_US_NU': 'Northwestern', 'T2_BR_UERJ': 'HEPGRID_UERJ', 'T3_MX_Cinvestav': 'cinvestav', 'T3_US_FNALLPC': 'FNALLPC', 'T3_US_UIowa': 'UIowa', 'T3_RU_FIAN': 'FIAN', 'T3_US_Cornell': 'Cornell', 'T2_ES_IFCA': 'IFCA', 'T3_US_UVA': 'UVA', 'T3_ES_Oviedo': 'Oviedo', 'T3_US_NotreDame': 'NWICG_NDCMS', 'T2_DE_DESY': 'DESY', 'T1_UK_RAL': 'RAL', 'T2_US_Caltech': 'Caltech', 'T3_FR_IPNL': 'IN2P3-IPNL', 'T2_TW_Taiwan': 'Taiwan', 'T3_US_NEU': 'Northeastern', 'T3_UK_London_RHUL': 'RHUL', 'T0_CH_CERN': 'CERN Tier-0', 'T1_RU_JINR_Disk': 'JINR-T1DISK', 'T3_CN_PKU': 'CN_PKU', 'T3_US_Baylor': 'Baylor University Tier3', 'T2_US_Nebraska': 'Nebraska', 'T2_ES_CIEMAT': 'CIEMAT', 'T3_US_Princeton': 'Princeton', 'T3_UK_ScotGrid_GLA': 'UKI-SCOTGRID-GLASGOW', 'T2_CH_CERN_T0': 'CERN Tier-2 T0', 'T3_US_TTU': 'TTU', 'T3_US_FSU': 'T3_US_FSU', 'T3_KR_UOS': 'UOS', 'T2_BR_SPRACE': 'SPRACE', 'T1_IT_CNAF': 'CNAF', 'T3_US_Minnesota': 'Minnesota', 'T2_TR_METU': 'METU', 'T2_AT_Vienna': 'Hephy-Vienna', 'T2_US_Purdue': 'Purdue', 'T3_US_Rice': 'Rice', 'T3_HR_IRB': 'IRB', 'T2_BE_UCL': 'Louvain', 'T3_US_FIT': 'FLTECH', 'T2_UK_SGrid_Bristol': 'Bristol', 'T2_PT_NCG_Lisbon': 'NCG-INGRID-PT', 'T1_ES_PIC': 'PIC', 'T3_US_JHU': 'JHU', 'T2_IT_Legnaro': 'Legnaro', 'T2_RU_INR': 'INR', 'T3_US_FIU': 'T3_US_FIU', 'T3_EU_Parrot': 'T3 EU Parrot', 'T2_RU_JINR': 'JINR', 'T2_IT_Pisa': 'Pisa', 'T2_GR_Ioannina': 'Ioannina', 'T3_US_MIT': 'T3 US MIT', 'T2_CH_CERN_HLT': 'CERN Tier-2 HLT', 'T2_MY_UPM_BIRUNI': 'UPM Biruni', 'T1_FR_CCIN2P3': 'CC-IN2P3', 'T2_FR_GRIF_IRFU': 'GRIF_IRFU', 'T3_US_UMiss': 'UMissHEP', 'T2_FR_CCIN2P3': 'CC-IN2P3 AF', 'T2_PL_Warsaw': 'Warsaw', 'T3_AS_Parrot': 'T3 AS Parrot', 'T2_US_MIT': 'MIT', 'T2_BE_IIHE': 'IIHE', 'T2_RU_ITEP': 'ITEP', 'T1_CH_CERN': 'CERN', 'T3_CH_PSI': 'PSI', 'T3_IT_Bologna': 'Bologna-T3'}
  matchList = {'T2_FI_HIP': 'Helsinki Institute of Physics', 'T2_UK_SGrid_RALPP': 'Rutherford PPD', 'T2_FR_GRIF_LLR': 'GRIF_LLR', 'T2_UK_London_IC': 'IC', 'T3_US_Omaha': 'Firefly', 'T2_KR_KNU': 'KNU', 'T2_RU_SINP': 'SINP', 'T2_CH_CERN_AI': 'CERN Tier-2 AI', 'T1_TW_ASGC': 'ASGC', 'T3_US_Colorado': 'Colorado', 'T1_UK_RAL_Disk': 'RALDISK', 'T2_TH_CUNSTDA': 'CUNSTDA', 'T2_IT_Bari': 'Bari', 'T2_US_UCSD': 'UCSD', 'T2_RU_IHEP': 'IHEP', 'T1_RU_JINR': 'JINR-T1', 'T2_RU_RRC_KI': 'RRC_KI', 'T2_CH_CERN': 'CERN Tier-2', 'T2_US_Vanderbilt': 'Vanderbilt', 'T2_CH_CSCS': 'CSCS', 'T2_UA_KIPT': 'KIPT', 'T2_PK_NCP': 'NCP-LCG2', 'T2_RU_PNPI': 'PNPI', 'T2_IN_TIFR': 'TIFR', 'T2_FR_IPHC': 'IPHC', 'T1_US_FNAL': 'FNAL', 'T2_IT_Rome': 'Rome', 'T2_UK_London_Brunel': 'Brunel', 'T1_US_FNAL_Disk': 'FNALDISK', 'T2_EE_Estonia': 'Estonia', 'T2_CN_Beijing': 'Beijing', 'T2_US_Florida': 'Florida', 'T1_DE_KIT': 'KIT', 'T2_US_Wisconsin': 'Wisconsin', 'T2_HU_Budapest': 'Hungary', 'T2_DE_RWTH': 'RWTH', 'T2_BR_UERJ': 'HEPGRID_UERJ', 'T2_ES_IFCA': 'IFCA', 'T2_DE_DESY': 'DESY', 'T1_UK_RAL': 'RAL', 'T2_US_Caltech': 'Caltech', 'T2_TW_Taiwan': 'Taiwan', 'T0_CH_CERN': 'CERN Tier-0', 'T1_RU_JINR_Disk': 'JINR-T1DISK', 'T2_US_Nebraska': 'Nebraska', 'T2_ES_CIEMAT': 'CIEMAT', 'T2_CH_CERN_T0': 'CERN Tier-2 T0', 'T2_BR_SPRACE': 'SPRACE', 'T1_IT_CNAF': 'CNAF', 'T2_TR_METU': 'METU', 'T2_AT_Vienna': 'Hephy-Vienna', 'T2_US_Purdue': 'Purdue', 'T2_BE_UCL': 'Louvain', 'T2_UK_SGrid_Bristol': 'Bristol', 'T2_PT_NCG_Lisbon': 'NCG-INGRID-PT', 'T1_ES_PIC': 'PIC', 'T2_IT_Legnaro': 'Legnaro', 'T2_RU_INR': 'INR', 'T2_RU_JINR': 'JINR', 'T2_IT_Pisa': 'Pisa', 'T2_GR_Ioannina': 'Ioannina', 'T2_CH_CERN_HLT': 'CERN Tier-2 HLT', 'T2_MY_UPM_BIRUNI': 'UPM Biruni', 'T1_FR_CCIN2P3': 'CC-IN2P3', 'T2_FR_GRIF_IRFU': 'GRIF_IRFU', 'T2_FR_CCIN2P3': 'CC-IN2P3 AF', 'T2_PL_Warsaw': 'Warsaw', 'T2_US_MIT': 'MIT', 'T2_BE_IIHE': 'IIHE', 'T2_RU_ITEP': 'ITEP', 'T1_CH_CERN': 'CERN'}
#_____________________________________________________________________________
  for site in matchList:
    if pledgeList.has_key(matchList[site]):
    	valPos = str(pledgeList[matchList[site]]).find('.') 
    	pledges[site] = int(str(pledgeList[matchList[site]])[0:valPos])
    else:
      	pledges[site] = "n/a"
  return pledges
#____________________function creates JSON TXT file________________
def savetoFile(pledges, year,outputfile_txt):
  saveTime = time.strftime('%Y-%m-%d %H:%M:%S')
  url = "https://cmsweb.cern.ch/sitedb/prod/pledges "
  #_______________JSON__________________________________________________
  filename = outputfile_txt + ".json"
  fileOp = open(filename, "w")
  fileOp.write(unicode(simplejson.dumps(pledges, ensure_ascii=False)))
  fileOp.close()

  #_______________the List_____________________________________________
  filename = outputfile_txt + ".txt"
  fileOp = open(filename, "w")
  for tmpPledges in pledges:
      if (pledges[tmpPledges]      == 0)     : color = 'yellow'
      if (pledges[tmpPledges]      > 0)      : color = 'green'
      if (str(pledges[tmpPledges]) == 'n/a') : color = 'white'
      fileOp.write(saveTime + "\t" + tmpPledges + "\t" + str(pledges[tmpPledges]) + "\t" + color + "\t" +  url + "\n" )

  fileOp.close()

if __name__ == '__main__':
  outputfile_txt=sys.argv[1]
  year = sys.argv[2]
  print 'starting to fetch all pledges from siteDB'
  allPledgeList = fetch_all_pledges('cmsweb.cern.ch','/sitedb/data/prod/resource-pledges')
  pledges       = matchPledges(allPledgeList)
  savetoFile(pledges, year, outputfile_txt)
