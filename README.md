This program is a supplement to the mapping and bannering system in Minecraft: Java Edition.
It takes an associated text file of points of interest, structured in the following way:
    The first line of the text file is the seed of the Minecraft world.
    After that, each line represents one POI (Point Of Interest), structered as follows:
        - the color code of the banner used to mark it (see below)
        - the POI's x-coordinate
        - the POI's z-coordinate
        - the status of bannering the POI (one of the following options:)
            - you know the POI is there, but you've never actually REACHED it (known)
            - you've actually discovered the POI (discovered)
            - you've placed a banner at the POI (bannered)
            - you have the banner appear on a map (mapped)
        - the status of looting the POI (one of the following options:)
            - the POI has not been fully looted yet (no)
            - the POI has been fully looted (yes)
            - the POI cannot be fully looted (NA)
        - any additional information you want to make about the POI
            - If you have no such extra information, end the line with an "X", or the program will have issues with you >:(
The program takes this text file and generates a picture displaying:
    - the relative location of each POI, designated with its own sprite
    - the x-axis and z-axis of the Minecraft world (the yellow lines)
    - the borders of each zoom level of map:
        - black for Zoom Level 0
        - red for Zoom Level 1
        - blue for Zoom Level 2
        - green for Zoom Level 3
        - white for Zoom Level 4
In the picture, one pixel equals one block in Minecraft - so obviously, there will be some loss of precision given that the banner sprites are anywhere from 17x17 pixels to 27x27 pixels.


Here is the key of banner colors to codes - if you want to change these codes, you'll have to hardcode that yourself:
    - red: PV (Plundered Village)
    - orange: AM (Abandoned Mineshaft)
    - yellow: HV (Home Village)
    - lime: SP (Spawn Point)
    - green: D (Dungeon or Trial Chamber)
    - cyan: SC (Skulk City)
    - light blue: WM (Woodland Mansion)
    - blue: US (Underwater Structure)
    - purple: B (Base)
    - pink: WH (Witch Hut)
    - magenta: SH (StrongHold)
    - brown: SR (Surface Ruin)
    - white: I (Igloo)
    - light gray: RRA (Resource-Rich Area)
    - gray: PO (Pillager Outpost)
    - black: NP (abandoned Nether Portal)
The shape of the sprite denotes the mapping status:
    - blob: known
    - circle: discovered
    - square: bannered
    - banner: mapped
Finally, the markings on the sprite (in the banner's inverse color) denote its looting status:
    - no markings: no
    - check mark: yes
    - X: NA