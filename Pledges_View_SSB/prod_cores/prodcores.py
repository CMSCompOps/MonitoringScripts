import urllib2
import json, time, string
#______________________get all datas from SSB___________________________
def getDatafromURL():
	url='http://dashb-ssb.cern.ch/dashboard/request.py/getplotdata?columnid=136&time=720&dateFrom=&dateTo=&site=T0_CH_CERN&sites=all&clouds=undefined&batch=1';
	print "Getting the url %s" % url
	obj = urllib2.urlopen(url)
	data = obj.read()
	rows = json.loads(data)
	return rows
#_______________________________________________________________________
#______________________function calculates T1, T2, T3 prod[Cores] values.__________________________________
def calculateProdCore(json):
	saveTime = time.strftime('%Y-%m-%d %H:%M:%S')
	urll = "https://cmst1.web.cern.ch/CMST1/SST/prod.txt"
	filename = "prod"
	jsonCode = '{ "prodCores":['
	jsonCodeEnd = ']}'
	f = open(filename + ".txt", "w")
	j = open(filename + ".json", "w")
        sites = []
        for row in json['csvdata']:
                siteName = row['VOName']
                sites.append(siteName)
        sites = list(set(sites))
        print sites
        for row in json['csvdata']:
		tierName = row['VOName'][0:2]
		siteName = row['VOName']
                if siteName in sites:
                    sites.remove(siteName)
                else:
                    continue
		value = row['Value']
		status = row['Status']
		color = row['COLORNAME']
		#_______________Calculate Prod[Cores]____________________________
		prodCore = 0 if value is None else value
		if (tierName == 'T1'):
			prodCore = int(int(prodCore + 2) * 0.9)
		elif (tierName == 'T3' or siteName == 'T2_CH_CERN_AI' or siteName == 'T2_CH_CERN_HLT' or siteName == 'T2_CH_CERN_T0'):
			prodCore = int(int(prodCore +1 ) * 1)
		elif (tierName == 'T2'):
			prodCore = int(int(prodCore + 2) * 0.5)
		if color == 'white':
			prodCore = 'n/a'
		jsonCode = jsonCode + "{" + '"siteName":"' + siteName + '", "prodCore":' + str(prodCore) + ',' + '"color":"' + color + '",' + '"url":"' + urll + '"},'
		f.write(saveTime + "\t" + siteName + "\t" + str(prodCore) + "\t" + color + "\t" + urll + "\n")
		print saveTime, siteName, prodCore, color, urll
	#____________________save to JSON file______________________________
	jsonCode = (jsonCode + jsonCodeEnd).replace("},]}", "}]}")
	j.write(jsonCode)
	#___________________________________________________________________
	#_______________________________________________________________
#__________________________________________________________________________________________________________
if __name__ == '__main__':
	rows = getDatafromURL() #get all pledge from dashBoard SSB metric 136 (json)
	calculateProdCore(rows)
