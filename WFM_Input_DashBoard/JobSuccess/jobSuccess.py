import os, sys, errno
#import urllib, json
import urllib, simplejson
from datetime import datetime
from datetime import timedelta
import time
from pprint import pprint
import string

def run(grid_proc_out_txt,app_proc_out_txt):
 ################################################################################
        # interactive view (success rates)
        print "Retrieve Dashboard infomration via json"
        template4a=string.Template("http://dashb-cms-job.cern.ch/dashboard/request.py/jobsummary-plot-or-table2?user=&site=&submissiontool=&application=&activity=reprocessing&status=&check=submitted&tier=&sortby=site&ce=&rb=&grid=&jobtype=&submissionui=&dataset=&submissiontype=&task=&subtoolver=&genactivity=&outputse=&appexitcode=&accesstype=&date1=$date1&date2=$date2&prettyprint")
        template4b=string.Template("http://dashb-cms-job.cern.ch/dashboard/request.py/jobsummary-plot-or-table2?user=&site=&submissiontool=&application=&activity=production&status=&check=submitted&tier=&sortby=site&ce=&rb=&grid=&jobtype=&submissionui=&dataset=&submissiontype=&task=&subtoolver=&genactivity=&outputse=&appexitcode=&accesstype=&date1=$date1&date2=$date2&prettyprint")
        now=(datetime.utcnow()).strftime("%Y-%m-%d+%H%%3A%M")
        nowyest=(datetime.utcnow()-timedelta(1)).strftime("%Y-%m-%d+%H%%3A%M")
        link4a=template4a.safe_substitute(date1=nowyest,date2=now)
        link4b=template4b.safe_substitute(date1=nowyest,date2=now)
        name4a="tmp4a.json"
        name4b="tmp4b.json"
        os.system("curl '%s' -o %s"%(link4a,name4a))
        os.system("curl '%s' -o %s"%(link4b,name4b))
        # get input
        file4a=open(name4a,'r+')
        input4a=file4a.read()
        file4a.close()
        file4b=open(name4b,'r+')
        input4b=file4b.read()
        file4b.close()
        # fill
        print "Filling intermediate json"
        json4a=simplejson.loads(input4a)
        json4b=simplejson.loads(input4b)
        dict4 = {}
        for k in json4a['summaries']+json4b['summaries']:
                dict4[k['name']] = k
                if ((k['app-succeeded']+k['app-failed']) == 0) or ((k['aborted']+k['done']) == 0):
                        dict4[k['name']]['grid-proc'] = -1
                        dict4[k['name']]['app-proc'] = -1
                else:
                        dict4[k['name']]['grid-proc'] = float(k['done'])*100.0/(k['aborted']+k['done'])
                        dict4[k['name']]['app-proc'] = float(k['app-succeeded'])*100.0/(k['app-succeeded']+k['app-failed'])

        
        #and write away
        f1=open('./'+grid_proc_out_txt, 'w+')
        f2=open('./'+app_proc_out_txt, 'w+')
        f1.write('# grid proc: done*100.0/(aborted+done)  \n')
        f1.write('# watchout, you have to replace $date1 and $date2 below with the current time and the time-24h\n')
        f1.write('# reprocessing: http://dashb-cms-job.cern.ch/dashboard/request.py/jobsummary-plot-or-table2?user=&site=&submissiontool=&application=&activity=reprocessing&status=&check=submitted&tier=&sortby=site&ce=&rb=&grid=&jobtype=&submissionui=&dataset=&submissiontype=&task=&subtoolver=&genactivity=&outputse=&appexitcode=&accesstype=&date1=$date1&date2=$date2&prettyprint\n')
        f1.write('# production: http://dashb-cms-job.cern.ch/dashboard/request.py/jobsummary-plot-or-table2?user=&site=&submissiontool=&application=&activity=production&status=&check=submitted&tier=&sortby=site&ce=&rb=&grid=&jobtype=&submissionui=&dataset=&submissiontype=&task=&subtoolver=&genactivity=&outputse=&appexitcode=&accesstype=&date1=$date1&date2=$date2&prettyprint\n')
        f2.write('# app proc: app-succeeded*100.0/(app-succeeded+app-failed) \n')
        f2.write('# watchout, you have to replace $date1 and $date2 below with the current time and the time-24h\n')
        f2.write('# reprocessing: http://dashb-cms-job.cern.ch/dashboard/request.py/jobsummary-plot-or-table2?user=&site=&submissiontool=&application=&activity=reprocessing&status=&check=submitted&tier=&sortby=site&ce=&rb=&grid=&jobtype=&submissionui=&dataset=&submissiontype=&task=&subtoolver=&genactivity=&outputse=&appexitcode=&accesstype=&date1=$date1&date2=$date2&prettyprint\n')
        f2.write('# production: http://dashb-cms-job.cern.ch/dashboard/request.py/jobsummary-plot-or-table2?user=&site=&submissiontool=&application=&activity=production&status=&check=submitted&tier=&sortby=site&ce=&rb=&grid=&jobtype=&submissionui=&dataset=&submissiontype=&task=&subtoolver=&genactivity=&outputse=&appexitcode=&accesstype=&date1=$date1&date2=$date2&prettyprint\n')
        
        #time to write
        now_write=(datetime.utcnow()).strftime("%Y-%m-%d %H:%M:%S") 
        print "Local current time :", now
        for k in json4a['summaries']+json4b['summaries']:
                color_app='green'
                color_grid='green'

                if((dict4[k['name']]['grid-proc']) <= 75 ):
                   color_grid='yellow'
                if((dict4[k['name']]['app-proc']) <= 75 ):
                   color_app='yellow'

                if((dict4[k['name']]['grid-proc']) <= 25 ):
                   color_grid='red'
                if((dict4[k['name']]['app-proc']) <= 25 ):
                   color_app='red'

                if((dict4[k['name']]['grid-proc']) == -1 ):
                   color_grid='green'
                if((dict4[k['name']]['app-proc']) == -1 ):
                   color_app='green'
                print k['name'],trunc(dict4[k['name']]['grid-proc'],0),trunc(dict4[k['name']]['app-proc'],0), color_grid, color_app
                f1.write(now_write+' '+k['name']+' '+str(trunc(dict4[k['name']]['grid-proc'],0))+' '+color_grid+' http://dashb-cms-job.cern.ch/dashboard/request.py/jobsummary-plot-or-table2\n')
                f2.write(now_write+' '+k['name']+' '+str(trunc(dict4[k['name']]['app-proc'],0))+' '+color_app+' http://dashb-cms-job.cern.ch/dashboard/request.py/jobsummary-plot-or-table2\n')
 

#######################################

def trunc(f, n):
    '''Truncates/pads a float f to n decimal places without rounding'''
    return ('%.*f' % (n + 1, f))[:-1]

#######################################

if __name__ == '__main__':
  grid_proc_out_txt=sys.argv[1]
  app_proc_out_txt=sys.argv[2]
  #grid_proc_out_txt="grid_proc_out.txt"
  #app_proc_out_txt="app_proc_out.txt"
  run(grid_proc_out_txt,app_proc_out_txt)
