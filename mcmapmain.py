import media_dissected as media
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

def main():
    which_seed = input("Which world are you calculating?\n")
    chosen_file = (which_seed + "coor.txt")
    experiment = open(chosen_file, "r")
    inputs = experiment.readlines()
    seed = inputs.pop(0)
    database = []
    for point in inputs:
        p = Spot.Spot()
        p.make_point(point)
        database.append(p)
    experiment.close()
    l_limit = find_edge(database, 0, 1)
    r_limit = find_edge(database, 0, 0)
    u_limit = find_edge(database, 1, 1)
    d_limit = find_edge(database, 1, 0)
    
    drop = Background.Background()
    drop.setup(l_limit, r_limit, u_limit, d_limit)
    
    drop.pict.addText(media.makeColor(media.black),drop.calcx(-90,2),drop.calcz(-64,2), "Z0") # Z0
    drop.gridlines(0)
    drop.pict.addText(media.makeColor(media.red),drop.calcx(-122,2),drop.calcz(-64,2), "Z1") # Z1
    drop.gridlines(1)
    drop.pict.addText(media.makeColor(media.blue),drop.calcx(-154,2),drop.calcz(-64,2), "Z2") # Z2
    drop.gridlines(2)
    drop.pict.addText(media.makeColor(media.green),drop.calcx(-186,2),drop.calcz(-64,2), "Z3") # Z3
    drop.gridlines(3)
    drop.pict.addText(media.makeColor(media.white),drop.calcx(-218,2),drop.calcz(-64,2), "Z4") # Z4
    drop.gridlines(4)
    drop.pict.addText(media.makeColor(media.black),drop.calcx(-218,2),drop.calcz(-90,2), seed) # seed
    drop.pict.addLine(media.makeColor(media.yellow),0,drop.zaxis,drop.pict.getWidth(),drop.zaxis) # x
    drop.pict.addLine(media.makeColor(media.yellow),drop.xaxis,0,drop.xaxis,drop.pict.getHeight()) # z
    
    for poi in database:
        poi.tack(drop)
    
    media.writePictureTo(drop.pict, which_seed + "map.png")
    print('Ready to view')


if __name__ == '__main__':
    main()