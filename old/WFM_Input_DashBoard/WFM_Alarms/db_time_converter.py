import sys
from datetime import datetime
import time

#all the information from Dashboard, csv file versus the pldege/status JOSN file has a different time format, so this function will convert the format
def transformTime(timetotest):
  #FIX python 2.4 versus 2.6 issue
  if hasattr(datetime, 'strptime'):
     #python 2.6
     strptime = datetime.strptime
  else:
     #python 2.4 equivalent
     strptime = lambda date_string, format: datetime(*(time.strptime(date_string, format)[0:6]))

  inputformat="%d-%b-%yT%H:%M:%S"
  timeTest=strptime(timetotest,inputformat)
  timeformat="%Y-%m-%dT%H:%M:%S"
  res=timeTest.strftime(timeformat)
  print res


########################################

if __name__ == '__main__':
    timetotest = sys.argv[1]
    transformTime(timetotest)
                                                               
