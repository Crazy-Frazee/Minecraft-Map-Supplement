import media_original as media
import Spot
import Background


def find_edge(points, coor, pol):
    if coor == 0:
        output = points[0].x_coor
        if pol == 0:
            for line in points:
                if line.x_coor > output:
                    output = line.x_coor
            return output + 64
        if pol == 1:
            for line in points:
                if line.x_coor < output:
                    output = line.x_coor
            return output - 32
    if coor == 1:
        output = points[0].z_coor
        if pol == 0:
            for line in points:
                if line.z_coor > output:
                    output = line.z_coor
            return output + 32
        if pol == 1:
            for line in points:
                if line.z_coor < output:
                    output = line.z_coor
            return output - 32

def establish_colors():
    mc_colors = []
    mc_red = media.makeColor(176,46,38)
    mc_colors.append(mc_red)
    mc_orange = media.makeColor(249,128,29)
    mc_colors.append(mc_orange)
    mc_yellow = media.makeColor(254,216,61)
    mc_colors.append(mc_yellow)
    mc_lime = media.makeColor(128,199,31)
    mc_colors.append(mc_lime)
    mc_green = media.makeColor(94,124,22)
    mc_colors.append(mc_green)
    mc_cyan = media.makeColor(22,156,156)
    mc_colors.append(mc_cyan)
    mc_light_blue = media.makeColor(58,179,218)
    mc_colors.append(mc_light_blue)
    mc_blue = media.makeColor(60,68,170)
    mc_colors.append(mc_blue)
    mc_purple = media.makeColor(137,50,184)
    mc_colors.append(mc_purple)
    mc_magenta = media.makeColor(199,78,189)
    mc_colors.append(mc_magenta)
    mc_pink = media.makeColor(243,139,170)
    mc_colors.append(mc_pink)
    mc_brown = media.makeColor(131,84,50)
    mc_colors.append(mc_brown)
    mc_white = media.makeColor(249,255,254)
    mc_colors.append(mc_white)
    mc_light_gray = media.makeColor(157,157,151)
    mc_colors.append(mc_light_gray)
    mc_gray = media.makeColor(71,79,82)
    mc_colors.append(mc_gray)
    mc_black = media.makeColor(29,29,33)
    mc_colors.append(mc_black)
    return mc_colors
    

def color_switcher(banner_type, color_options):
    color_code = {
        "PV": 0,
        "AM": 1,
        "HV": 2,
        "SP": 3,
        "D": 4,
        "SC": 5,
        "WM": 6,
        "US": 7,
        "B": 8,
        "SH": 9,
        "WH": 10,
        "SR": 11,
        "I": 12,
        "RRA": 13,
        "PO": 14,
        "NP": 15,
        "V": 0
    }
    numb = color_code.get(banner_type)
    return color_options[numb]

def main():
    color_arr = establish_colors()
    
    which_seed = input("Which world are you calculating?\n")
    chosen_file = (which_seed + "coor.txt")
    experiment = open(chosen_file, "r")
    inputs = experiment.readlines()
    seed = inputs.pop(0)
    database = []
    for point in inputs:
        p = Spot.Spot()
        p.make_point(point)
        p.import_color(color_switcher(p.banner, color_arr))
        database.append(p)
    experiment.close()
    l_limit = find_edge(database, 0, 1)
    r_limit = find_edge(database, 0, 0)
    u_limit = find_edge(database, 1, 1)
    d_limit = find_edge(database, 1, 0)
    
    drop = Background.Background()
    drop.setup(l_limit, r_limit, u_limit, d_limit)
    
    drop.pict.addText(media.makeColor(media.black),drop.calcx(-90,0),drop.calcz(-64,0), "Z0") # Z0
    drop.gridlines(0)
    drop.pict.addText(media.makeColor(media.red),drop.calcx(-122,0),drop.calcz(-64,0), "Z1") # Z1
    drop.gridlines(1)
    drop.pict.addText(media.makeColor(media.blue),drop.calcx(-154,0),drop.calcz(-64,0), "Z2") # Z2
    drop.gridlines(2)
    drop.pict.addText(media.makeColor(media.green),drop.calcx(-186,0),drop.calcz(-64,0), "Z3") # Z3
    drop.gridlines(3)
    drop.pict.addText(media.makeColor(media.white),drop.calcx(-218,0),drop.calcz(-64,0), "Z4") # Z4
    drop.gridlines(4)
    drop.pict.addText(media.makeColor(media.black),drop.calcx(-218,0),drop.calcz(-90,0), seed) # seed
    drop.pict.addLine(media.makeColor(media.yellow),0,drop.zaxis,drop.pict.getWidth(),drop.zaxis) # x
    drop.pict.addLine(media.makeColor(media.yellow),drop.xaxis,0,drop.xaxis,drop.pict.getHeight()) # z
    
    for poi in database:
        poi.tack(drop)
    
    media.writePictureTo(drop.pict, which_seed + "map.png")
    print('Ready to view')


if __name__ == '__main__':
    main()