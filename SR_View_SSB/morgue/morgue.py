import urllib2
import time

#_________________________________________________________________________
def getMorgue():
  url = "https://cmst1.web.cern.ch/CMST1/SST/WaitingRoom_2MonthSum.txt"
  print "Getting the url %s" % url
  sites_in_morgue = {}
  for line in urllib2.urlopen(url).readlines():
    row = line.split("\t")
    if len(row) == 5 :
        siteName = row[1]
        wrDays    = int(row[2])
        
        if not sites_in_morgue.has_key(siteName):
            state = "out"
            if wrDays > 49 :
                state = "in"
            sites_in_morgue[siteName] = state 
  return sites_in_morgue
#_________________________________________________________________________

def writeFile(morgueList):
    saveTime = time.strftime('%Y-%m-%d %H:%M:%S')
    filename = "morgue"
    path = "/afs/cern.ch/user/c/cmst1/scratch0/MonitoringScripts/SR_View_SSB/morgue/"
    url = "https://cmst1.web.cern.ch/CMST1/SST/WaitingRoom_2MonthSum.txt"
    f = open(path + filename + ".txt", "w")
    for rows in morgueList:
        color = "green"
        if morgueList[rows] == "in" : color = "red"
        f.write(saveTime + "\t" + rows + "\t" + morgueList[rows] + "\t" + color + "\t" + url + "\n")
    print "List has been created successfully"
#_________________________________________________________________________

morgueList =  getMorgue()
writeFile(morgueList)