import world
import thermal
from thermal_model import convertLatLon2Meters, calcDist, calcDrift
import xp

HUGE_CLOUD = 'lib/dynamic/balloon.obj'
LARGE_CLOUD = 'lib/airport/Common_Elements/Fuel_Storage/Sing_Tank_Large.obj'
# 'lib/street/various/porta_potty.obj'
SMALL_CLOUD = 'lib/airport/landscape/windsock.obj'
# 'lib/airport/Common_Elements/Markers/Poles/Large_Red_White.obj'
THERMAL_COLUMN = 'lib/dynamic/seagull_glide.obj'


def DrawThermal(lat, lon):  # min_alt,max_alt
    ''' make a location list of thermal images along the raising thermal, accounting
        for wind drift along the climb. end at thermal tops
    '''
    base = 1
    Dew, Dud, Dns = xp.worldToLocal(lat, lon, 0)  # Dew=E/W,Dud=Up/Down,Dns=N/S
    locs = []  # locations
    # from 100 to thermal top steps of  200
    for alt in range(base, world.thermal_tops, 200):
        dX, dY = calcDrift(alt)
        locs.append([Dew + dX, Dud + alt, Dns + dY, 0, 0, 0])
    return locs


def DrawCloud(lat, lon):
    ''' Return the location for a cloud at the top of the raising thermal, accounting
        for wind drift along the climb.
    '''
    Dew, Dud, Dns = xp.worldToLocal(lat, lon, 0)  # Dew=E/W,Dud=Up/Down,Dns=N/S
    locs = []  # locations
    alt = world.thermal_tops
    dX, dY = calcDrift(alt)
    locs.append((Dew + dX, Dud + alt, Dns + dY, 0, 0, 0))

    return locs


''' return a list of thermal location tuples, if the distance not exceeds max display 
    draw the thermal column of rising air
'''


def DrawThermalMap(lat, lon):
    locations = []
    p1x, p1y = convertLatLon2Meters(lat, lon)

    for athermal in world.thermal_dict:
        p2x, p2y = athermal.px, athermal.py
        if calcDist(p1x, p1y, p2x, p2y) < world.max_draw_distance:
            locations.extend(DrawThermal(athermal.lat, athermal.lon))

    return locations


''' return a list of thermal location tuples, if the distance not exceeds max display 
    Just the thermals at cloudbase
'''


def DrawCloudMap(lat, lon):
    locations = []
    p1x, p1y = convertLatLon2Meters(lat, lon)

    for athermal in world.thermal_dict:
        p2x, p2y = athermal.px, athermal.py
        if calcDist(p1x, p1y, p2x, p2y) < world.max_draw_distance:
            locations.extend(DrawCloud(athermal.lat, athermal.lon))

    return locations


def eraseThermalsOnScreen():
    if world.DEBUG:
        print("loop: Delete old instances")
    for i in world.instance_list:
        if world.DEBUG:
            print("loop: delete instance,", i)
        if i:
            xp.destroyInstance(i)


def drawThermalsOnScreen(lat, lon):
    if world.DEBUG:
        print("DrawThermalsOnScreen:start")

    # if visibility is off, only draw clouds at cloudbase (no visible columns)

    if world.thermals_visible:
        locs = DrawThermalMap(lat, lon)
    else:
        locs = DrawCloudMap(lat, lon)

    if world.DEBUG:
        print("plane ( lat, lon ) ", lat, lon)
        print("plane local", xp.worldToLocal(lat, lon, 0))
        #print("thermal location = ",loc[0])

    paths = []
    xp.lookupObjects(HUGE_CLOUD, 0, 0,
                     lambda path, refCon: paths.append(path), None)
    huge_cloud = xp.loadObject(paths[0])

    # print(paths)
    thermal_column = xp.loadObject(
        'Resources/default scenery/sim objects/dynamic/SailBoat.obj')

    #print("object1", huge_cloud)
    #print("object2", thermal_column)

    eraseThermalsOnScreen()

    if world.DEBUG:
        print("loop: create instances and position")
    _p = True
    for loc in locs:
        # select the object to draw
        _p = not _p
        if _p:
            instance = xp.createInstance(huge_cloud)
            #print("huge cloud")
        else:
            instance = xp.createInstance(thermal_column)
            # print("thermal_column")

        if world.DEBUG:
            print("loop: xp.instanceSetPosition(instance,", instance, loc)
        xp.instanceSetPosition(instance, loc)
        world.instance_list.append(instance)

    world.world_update = False
    return 1


def select_cloud_type(_thermal):
    ''' return a cloud type based on the thermal size and power'''
    print(_thermal)
