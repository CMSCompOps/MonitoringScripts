import urllib2, time, datetime

class dashboardEntry:
    def __init__(self, row = (None, None, None, None, None)):
        self.date  = row[0]
        self.name  = row[1]
        self.value = row[2]
        self.color = row[3]
        self.url   = row[4]

    def getHumanReadableDate(self):
        """return the date as human readable date"""
        pass

def getContentFromURL(url):
    """return the content of given URL"""
    pass

def main():
    pass

if __name__ == "__main__":
    main()
