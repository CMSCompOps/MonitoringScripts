# aaltunda - ali.mehmet.altundag@cern.ch

import time

green  = 'green'
yellow = 'yellow'
red    = 'red'
saddlebrown = 'saddlebrown'
cyan   = 'cyan'
grey   = 'grey'
white  = 'white'

# dashboard entry structure
class entry:
    def __init__(self, date = None, name = None, value = None, color = None, url = None):
        if date == None:
            self.date = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
        else:
            self.date  = date
        self.name  = name
        self.value = value
        self.color = color
        if url == None:
            self.url = '#'
        else:
            self.url = url

    def __str__(self):
        return "%s\t%s\t%s\t%s\t%s" % (self.date, self.name, self.value, self.color, self.url)
