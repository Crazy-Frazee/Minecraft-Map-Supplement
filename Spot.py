import media_dissected as media
import Background

class Spot:
    def __init__(self):
        self.banner = "I"
        self.x_coor = 0
        self.z_coor = 0
        self.status = "known"
        self.plunder = "no"
        self.description = None
        self.sprite_name = "./sprites/sprite_"
        self.sprite = media.Picture(27,27)
    
    
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
        self.find_sprite()
    
    def find_sprite(self):
        self.sprite_name = self.sprite_name + self.banner
        if self.status == "mapped":
            self.sprite_name = self.sprite_name + "_m_"
        elif self.status == "bannered":
            self.sprite_name = self.sprite_name + "_b_"
        elif self.status == "discovered":
            self.sprite_name = self.sprite_name + "_d_"
        elif self.status == "known":
            self.sprite_name = self.sprite_name + "_k"
        else:
            if self.description == None:
                print('Whoa, we got an error with the status of ' + self.banner)
            else:
                print('Whoa, we got an error with the status of ' + self.banner + self.description)
            exit()
        if self.status != "known":
            if self.plunder == "no":
                self.sprite_name = self.sprite_name + "n"
            elif self.plunder == "yes":
                self.sprite_name = self.sprite_name + "y"
            elif self.plunder == "NA":
                self.sprite_name = self.sprite_name + "x"
            else:
                if self.description == None:
                    print('Whoa, we got an error with the status of ' + self.banner)
                else:
                    print('Whoa, we got an error with the status of ' + self.banner + self.description)
                exit()
        self.sprite_name = self.sprite_name + ".png"
        self.sprite = media.makePicture(self.sprite_name)
        
    def tack(self, canvas):
        canvas.pict.copyInto(self.sprite, canvas.calcx(self.x_coor, 0), canvas.calcz(self.z_coor, 0))
        if self.description != None:
            canvas.pict.addText(media.black, canvas.calcx(self.x_coor, 1), canvas.calcz(self.z_coor, 1), self.description)
