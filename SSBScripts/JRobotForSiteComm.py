#!/usr/bin/python

import os, sys, urllib2
import datetime

#_______________________________________________________________________________
# Function that extracts the information stored in the day's html summary page.
# It returns a list containing elements with the following information:
#   [site, no. submitted jobs, no. aborted jobs, no. jobs with errors, no.
#    successful jobs]
 
def summary_info(date, option):
# option =  Procedure for finding the info files: 0 for using the local ones.
#                     1 for finding them in the internet
    
    if (option == 0):
        filename = '/afs/cern.ch/user/b/belforte/www/JobRobot/summary_' + date + '.html'       
        if (not os.path.isfile(filename)):    # Forget about extracting info from the file if it doesn't exist.
            print filename, ': Not Found'
            return []
        file = open(filename, 'r')    
    else:
        filename = 'http://cern.ch/JobRobot/summary_' + date + '.html'
        try:
            file = urllib2.urlopen(filename)
        except IOError, detail:               # Forget the info if the page doesn't exist. 
            return []
    
    file_lines = []
    n = 0
    ini = -1
    end = -1
    for line in file.readlines():
        file_lines.append(line)
        if '<td align=center><b> SUCCESS </b></td> \n' in line:
            if ini == -1:
                ini = n + 2
                step = 7
        if '<td align=center><b>EFFICIENCY</b></td> \n' in line:
            ini = n + 2
            step = 8
        if '<td align=center><b> TOTAL ' in line:
            end = n - 1
        if '</table></center> \n' in line:
            if end == -1:
                end = n - 1
        n += 1      
    if (ini == -1 or end == -1):
        return []
    
    info_list = []
    for n in range(ini, end, step):
        site = ((file_lines[n+1].split('>')[2]).split('<')[0])[1:-1]
        subm = int(((file_lines[n+2].split('>')[1]).split('<')[0])[1:-1])
        
        isit = wordInStr('</a>',file_lines[n+3])
        if isit == 1:
            abor = int(((file_lines[n+3].split('>')[2]).split('<')[0])[1:-1])
        else:
            abor = int(((file_lines[n+3].split('>')[1]).split('<')[0])[1:-1])
        
        isit = wordInStr('</a>',file_lines[n+4])
        if isit == 1:
            erro = int(((file_lines[n+4].split('>')[2]).split('<')[0])[1:-1])
        else:
            erro = int(((file_lines[n+4].split('>')[1]).split('<')[0])[1:-1])
        succ = int(((file_lines[n+5].split('>')[1]).split('<')[0])[1:-1])
         
        info_list.append([site,subm,abor,erro,succ])
    
    info_list.sort()
    if (option == 0):
        file.close()
    return info_list

#_______________________________________________________________________________
# Function that builds the object that has to be passed to the QualityMap module.
# It returns a dictionary containing elements with the following information:
# {site : {datetime.datetime(year, month, day, 0, 0): quality value, datetime(...)}}


def build_info(sitelist):

    # option =  Procedure for finding the info files: 0 for using the local ones.
    #                     1 for finding them in the internet

    # read file with list of sites
    sites = []
    f = open(sitelist)
    for line in f.readlines():
        sites.append(line.strip())
    f.close()

    output=[]
    today=datetime.datetime.utcnow()
    yesterday=today-datetime.timedelta(1)
    todayString=today.strftime("%y%m%d")
    yesterdayString=yesterday.strftime("%y%m%d")
    
    timestamp=today.strftime("%Y-%m-%d %H:%M:%S")
    link='http://jobrobot.web.cern.ch/JobRobot/summary_' + todayString + '.html'

    
    tSummary = summary_info(todayString, 0)
    ySummary = summary_info(yesterdayString,0)

    for i in range(0,len(tSummary)):
        site=tSummary[i][0]
        jsub=tSummary[i][1]
        jabo=tSummary[i][2]
        jerr=tSummary[i][3]
        jsuc=tSummary[i][4]
        if site[0:2] == "T0" or site[0:2] == "T1": thrs = 90
        if site[0:2] == "T2": thrs = 80
        if site[0:2] == "T3": thrs = 0
        if jsub < 100:
            for yi in range (0,len(ySummary)):
                ysite=ySummary[yi][0]
                if ysite==site:
                    jsub+=ySummary[yi][1]
                    jabo+=ySummary[yi][2]
                    jerr+=ySummary[yi][3]
                    jsuc+=ySummary[yi][4]
        if (jabo+jerr+jsuc) > 0:   # some jobs completed
            effic= jsuc *100 / (jabo+jerr+jsuc)
            value=str(effic) + '%' + '(' + str(jabo+jerr+jsuc) + ')'
            if effic>=thrs: status="ok"
            else:
                status="err"
        else:                      # no jobs completed
            if jsub>0:
                value="pend"
                status="warn"
            else :                 # all submissions fail
                value="SubFail"
                status="err"

        #PATCH until JR runs with production role, T1's are forced to OK
#        if site[1:2] == "1":  status="ok"
        #\PATCH

        if status=="ok": color="green"
        if status=="err": color="red"
        if status=="warn":color="green"
        output.append(("%s\t%s\t%s\t%s\t%s") % (timestamp, site, value, color, link))
        sites.remove(site)

    for site in sites:
        output.append(("%s\t%s\t%s\t%s\t%s") % (timestamp, site, 'n/a', 'white', link))        
    
    return output

#_______________________________________________________________________________
# Function that looks for the ocurrence of a word in a character string (it is
# not needed when using Python 2.5)
                                                                                                                                                                                                    
def wordInStr(word, string):
                                                                                                                                                                                                    
    len_word = len(word)
                                                                                                                                                                                                    
    for n in range(0,len(string)):
        if string[n] == word[0]:
            if word == string[n:n+len_word]:
                return 1
                                                                                                                                                                                                    
    return 0
                                                                                                                                                                                                    

#_______________________________________________________________________________
#                             PRINCIPAL PROGRAM


def main(argv) :

    """
    """

    header = """
# JobRobot efficiency by site computed from JR summary of
# current day, plus previous day if there are less than
# 100 submitted jobs.
# JR summaries are at http://cmsweb.cern.ch/JobRobot/
# efficiency = Nok/(Nok+Nabo+Nerr)
# site is OK if efficiency >= 90% (tier 0/1), 80% (tier 2),
# 0% (tier 3)
# if Nsub=0 consider it error (sites who can not get JR jobs
# for good reason must be removed from JR list).
# If Nsub>0 but no ok/err/abo call it pending and warn
#
# for each site efficiency is reported
#
"""

    sites = argv[1]
    now = datetime.datetime.utcnow()
    print 'START: ' + now.ctime()
    
    status = build_info(sites)

    if status:
        print 'Site status retrieved!'
        outfile = argv[0]
        file = open(outfile, 'w')
        file.write(header)
        
        for line in status:
            file.write(line+'\n')
            print line

        file.close()
            
    else:
        print 'ERROR: Site status not retrieved!'

    print
    
if __name__ == '__main__' :

    main(sys.argv[1:])
