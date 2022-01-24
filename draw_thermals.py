import world
import thermal
from thermal_model import convertLatLon2Meters, calcDist, calcDrift
import xp

def DrawThermal(lat, lon):  # min_alt,max_alt
    ''' make a location list of thermal images along the raising thermal, accounting
        for wind drift along the climb. end at thermal tops
    '''
    base = 1
    Dew, Dud, Dns = xp.worldToLocal(lat, lon, 0)  # Dew=E/W,Dud=Up/Down,Dns=N/S
    locs = []  # locations
    for alt in range(base, world.thermal_tops, 200):  # from 100 to thermal top steps of  200
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
            locations.extend(DrawThermal(athermal.lat, athermal.lon) ) 

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
            locations.extend( DrawCloud(athermal.lat, athermal.lon) )

    return locations

def eraseThermalsOnScreen():
    if world.DEBUG:
        print("loop: Delete old instances")
    for i in world.instance_list:
        if world.DEBUG :
            print("loop: delete instance,", i )
        if i:
           xp.destroyInstance(i)


def drawThermalsOnScreen( lat, lon ) :
    if world.DEBUG :
        print("DrawThermalsOnScreen:start")

    locations = []

    # if visibility is off, only draw clouds at cloudbase (no visible columns)
    
    if world.thermals_visible :  
       if world.thermals_show_column :
           locs =  DrawThermalMap(lat,lon) 
       else:
           locs =  DrawCloudMap(lat,lon) 

    if world.DEBUG :
        print("plane ( lat, lon ) " ,lat,lon)
        print("plane local", xp.worldToLocal(lat, lon, 0))
        #print("thermal location = ",loc[0])


    paths = []
    xp.lookupObjects('lib/dynamic/balloon.obj', 0, 0, lambda path, refCon: paths.append(path), None)
    #print(paths) 
    obj = xp.loadObject(paths[0])

    '''
        # For testingonly 
        # get current aircraft position
        x = xp.getDatad(xp.findDataRef('sim/flightmodel/position/local_x'))
        y = xp.getDatad(xp.findDataRef('sim/flightmodel/position/local_y'))
        z = xp.getDatad(xp.findDataRef('sim/flightmodel/position/local_z'))
        pitch, heading, roll = (0, 0, 0)
        print("-------------------local x,y,z",x,y,z)
        position = x+30, y+30, z + 380, pitch, heading, roll
        instance1 = xp.createInstance(obj)
        xp.instanceSetPosition(instance1, position )
    '''

    eraseThermalsOnScreen()

    if world.DEBUG:
        print("loop: create instances and position")
    for loc in locs:
        instance = xp.createInstance(obj)
        if world.DEBUG:
            print("loop: xp.instanceSetPosition(instance,", instance, loc )
        xp.instanceSetPosition(instance, loc )
        world.instance_list.append(instance)

    world.world_update = False
    return 1

