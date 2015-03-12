

class Data:
    """ Data Item """

    LT_5MBS = "lt_5mbs"
    GT_5_LT_20MBS = "gt_5_lt_20mbs"
    GT_20MBS = "gt_20mbs"
    
    LT_18GB = "lt_18gb"
    GT_18_LT_72GB = "gt_18_lt_72gb"
    GT_72GB = "gt_72gb"
    
    def __init__( self, data=None ):
        self.data = data

    def to_str( self ):
        if self.data:
            gigs = int(self.data * 1024)
            megs = (self.data * 1024 * 1024)
            megspersec = int(megs/3600.)
            #link's hourly status classifications
            if megspersec < 5:
                css_class = self.LT_5MBS
            elif megspersec < 20:
                css_class = self.GT_5_LT_20MBS
            else:
                css_class = self.GT_20MBS
            return "<span class='%s'>%s</span>" % (css_class, str(gigs))
        else:
            return "<span>?</span>"

    def __str__( self ):
        if self.data:
            return str(self.data)
        else:
            return "?"

    def __float__( self ):
        if self.data == None:
            return 0.0
        return float(self.data)

