import re

alter = { \
    # 'PIC' : 'T1_ES_PIC_Buffer',
    #'CERN' : 'T1_CH_CERN_Buffer',
}

def rename(name):
    for key, val in alter.items():
         if name.find(key) >= 0:
             return val
    return name

class Node:
    """ @todo COMMENT """

    class Tier:
        T0 = 'T1'
        T1 = 'T1'
        T2 = 'T2'
        T3 = 'T3'

    # Short-name regexp
    short_name_regexp = re.compile('T._(.*?)(_(Buffer|Disk|MSS))*$')
    tier_regexp = re.compile('(T.)')

    def __init__(self, name):
        name = rename(name)
        self.name = name
        try:
            self.shortname = self.short_name_regexp.match(self.name).groups()[0]
        except Exception, e:
            print e
            self.shortname = 'Unknown'
        try:
            self.tier = self.tier_regexp.match(self.name).groups()[0]
        except:
            print e
            self.tier = 'TX'
        
    def find_tier(self):
        return self.tier

    def __str__(self):
        return self.name

    #def __cmp__(self, other):
    #    return cmp(self.name, other.name)

