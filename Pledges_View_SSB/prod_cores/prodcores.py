import urllib2
import json, time, string
#______________________get all datas from SSB___________________________
def getDatafromURL():
	url='http://dashb-ssb.cern.ch/dashboard/request.py/getplotdata?columnid=136&time=24&dateFrom=&dateTo=&site=T0_CH_CERN&sites=all&clouds=undefined&batch=1';
	print "Getting the url %s" % url
	obj = urllib2.urlopen(url)
	data = obj.read()
	rows = json.loads(data)
	return rows
#_______________________________________________________________________

#______________________function calculates T1, T2, T3 prod[Cores] values.__________________________________
def calculateProdCore(json):
	saveTime = time.strftime('%Y-%m-%d %H:%M:%S')
	urll = "mailto:cms-comp-ops-site-support-team@cern.ch?subject=Pledges_View_SSB"
	filename = "prod"
	jsonCode = '{ "prodCores":['
	jsonCodeEnd = ']}'
	f = open(filename + ".txt", "w")
	j = open(filename + ".json", "w")
	for row in json['csvdata']:
		tierName = row['VOName'][0:2]
		siteName = row['VOName']
		value = row['Value']
		status = row['Status']
		color = row['COLORNAME']
		#_______________Calculate Prod[Core]____________________________
		if tierName != 'T0':
			if (tierName == 'T1') or (tierName == 'T3' or siteName == 'T2_CH_CERN_AI' or siteName == 'T2_CH_CERN_HLT') :
				if color == 'white': # value = n/a ?
					prodCore = 'n/a'
				else:
					if status == value :
						prodCore = value
					else: 
						prodCore = status
			elif(tierName == 'T2'):
				if color == 'white':
					prodCore = 'n/a'
				else:
					if status == value :
						prodCore = value
					else: 
						prodCore = int(status) * 0.5
			if str(prodCore).find('.') >= 0 : prodCore = str(prodCore)[0:str(prodCore).find('.')]
			jsonCode = jsonCode + "{" + '"siteName":"' + siteName + '", "prodCore":' + prodCore + ',' + '"color":"' + color + '",' + '"url":"' + urll + '"},'    
			f.write(saveTime + "\t" + siteName + "\t" + prodCore + "\t" + color + "\t" + urll + "\n")

			print saveTime, siteName, prodCore, color, urll
	#____________________save to JSON file______________________________
	jsonCode = (jsonCode + jsonCodeEnd).replace("},]}", "}]}")
	j.write(jsonCode)
	#___________________________________________________________________
	#_______________________________________________________________
#__________________________________________________________________________________________________________
if __name__ == '__main__':
	rows = getDatafromURL() #get all pledge from dashBoard SSB
	calculateProdCore(rows)