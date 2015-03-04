# aaltunda - ali.mehmet.altundag@cern.ch

def read(fileName, printFlag = True, binary = False):
    if binary: fh = open(fileName, 'rb')
    else: fh = open(fileName)
    data = fh.read()
    fh.close()
    if printFlag: print "Read:", fileName
    return data

def write(fileName, data, printFlag = True, binary = False):
    if binary: fh = open(fileName, 'wb')
    else: fh = open(fileName, 'w')
    fh.write(data)
    fh.close()
    if printFlag: print "Write:", fileName
