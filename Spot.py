import media_dissected as media
import Background

class Spot:
    def __init__(self):
        self.banner = "I"
        self.back_color = media.red
        self.x_coor = 0
        self.z_coor = 0
        self.status = "known"
        self.plunder = "no"
        self.description = None
    
    
    def make_point(self, raw_string):
        cut_strings = raw_string.split(".")
        self.banner = cut_strings[0]
        self.x_coor = int(cut_strings[1])
        self.z_coor = int(cut_strings[2])
        self.status = cut_strings[3]
        self.plunder = cut_strings[4]
        if cut_strings[5] == 'X\n':
            self.description = None
        else:
            self.description = cut_strings[5]
        
        
    def import_color(self, given):
        self.back_color = given


    def tack(self, canvas):
        if self.status == "known":
            canvas.pict.addRect(self.back_color,canvas.calcx(self.x_coor,0),canvas.calcz(self.z_coor,0),17,17,False)
        elif self.status == "discovered":
            canvas.pict.addOval(self.back_color,canvas.calcx(self.x_coor,0),canvas.calcz(self.z_coor,0),17,17,False)
        elif self.status == "bannered":
            canvas.pict.addOval(self.back_color,canvas.calcx(self.x_coor,0),canvas.calcz(self.z_coor,0),17,17,True)
        elif self.status == "mapped":
            canvas.pict.addRect(self.back_color,canvas.calcx(self.x_coor,0),canvas.calcz(self.z_coor,0),17,17,True)
        else:
            if self.description == None:
                print('Whoa, we got an error with the status of ' + self.banner)
            else:
                print('Whoa, we got an error with the status of ' + self.banner + self.description)
            exit()
            
        if self.plunder == "yes" or self.plunder == "NA":
            inverse = media.makeColor((255 - self.back_color.r),(255 - self.back_color.g),(255 - self.back_color.b))
            if self.plunder == "yes":
                canvas.pict.addOval(inverse,canvas.calcx(self.x_coor,2),canvas.calcz(self.z_coor,2),7,7,True)
            elif self.plunder == "NA":
                canvas.pict.addRect(inverse,canvas.calcx(self.x_coor,2),canvas.calcz(self.z_coor,2),7,7,True)
        else:
            if self.plunder != "no":
                if self.description == None:
                    print('Whoa, we got an error with the plunder of ' + self.banner)
                else:
                    print('Whoa, we got an error with the plunder of ' + self.banner + self.description)
                exit()
        if self.description != None:
            canvas.pict.addText(media.black, canvas.calcx(self.x_coor,1), canvas.calcz(self.z_coor,1), self.description)
