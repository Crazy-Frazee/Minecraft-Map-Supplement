import media_dissected as media

class Background:
    def __init__(self):
        self.x_min = 0
        self.x_max = 0
        self.z_min = 0
        self.z_max = 0
        self.reach = 0
        self.height = 0
        self.pict = None
        self.xaxis = 0
        self.zaxis = 0
        self.xcoor = 0
        self.zcoor = 0
    
    def setup(self, l_edge, r_edge, u_edge, d_edge):
        self.x_min = l_edge
        self.x_max = r_edge
        self.z_min = u_edge
        self.z_max = d_edge
        if l_edge > -220:
            self.reach = (r_edge + 220)
        else:
            self.reach = (r_edge - l_edge)
        if u_edge > -120:
            self.height = (d_edge + 120)
        else:
            self.height = (d_edge - u_edge)
        self.pict = media.makeEmptyPicture(self.reach, self.height, media.gray)
        self.xaxis = (-1 * l_edge)
        self.zaxis = (-1 * u_edge)
        self.xcoor = (self.xaxis - 64)
        self.zcoor = (self.zaxis - 64)
    
    def calcx(self, xin, code):
        if code == 0:
            xout = (self.xaxis + (xin - 8))
        if code == 1:
            xout = (self.xaxis + (xin + 14))
        if code == 2:
            xout = (self.xaxis + (xin - 4))
        return xout
    
    def calcz(self, zin, code):
        if code == 0:
            zout = (self.zaxis + (zin - 8))
        if code == 1:
            zout = (self.zaxis + (zin + 8))
        if code == 2:
            zout = (self.zaxis + (zin - 4))
        return zout
    
    def gridlines(self, zoom):
        rep = 0
        if zoom == 4:
            spacing = 2048
            coll = media.makeColor(media.white)
        if zoom == 3:
            spacing = 1024
            coll = media.makeColor(media.green)
        if zoom == 2:
            spacing = 512
            coll = media.makeColor(media.blue)
        if zoom == 1:
            spacing = 256
            coll = media.makeColor(media.red)
        if zoom == 0:
            spacing = 128
            coll = media.makeColor(media.black)
        curverline = self.zcoor
        curhorline = self.xcoor
        while curhorline > 0:
            self.pict.addLine(coll,curhorline,0,curhorline,self.pict.getHeight())
            rep = rep - 1
            curhorline = self.xcoor + (spacing * rep)
        curhorline = self.xcoor
        rep = 0
        while curhorline < self.pict.getWidth():
            self.pict.addLine(coll,curhorline,0,curhorline,self.pict.getHeight())
            rep = rep + 1
            curhorline = self.xcoor + (spacing * rep)
        rep = 0
        while curverline > 0:
            self.pict.addLine(coll,0,curverline,self.pict.getWidth(),curverline)
            rep = rep - 1
            curverline = self.zcoor + (spacing * rep)
        curverline = self.zcoor
        rep = 0
        while curverline < self.pict.getHeight():
            self.pict.addLine(coll,0,curverline,self.pict.getWidth(),curverline)
            rep = rep + 1
            curverline = self.zcoor + (spacing * rep)
        rep = 0
