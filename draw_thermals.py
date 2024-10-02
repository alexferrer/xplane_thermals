import world
import thermal
from thermal_model import convert_lat_lon2meters, calc_dist, calc_drift
import xp

LIB_VERSION = "Version ----------------------------   draw_thermals.py v2.0"
print(LIB_VERSION)

THERMAL_COLUMN = 'Resources/plugins/PythonPlugins/cloudmade.obj'

# thermal image
thermal_column = xp.loadObject(THERMAL_COLUMN)

#for debug purposes only
#huge_cloud = xp.loadObject(
#    'Custom Scenery/X-Plane Airports - TNCS Juancho E Yrausquin/objects/mt_scenery.obj')

huge_cloud = xp.loadObject('Resources/plugins/PythonPlugins/mt_scenery.obj')


def draw_thermal(lat, lon):  # min_alt,max_alt
    ''' Draw thermal images along the raising thermal, accounting
        for wind drift along the climb. end at almost the thermal top
    '''
    if world.DEBUG > 6: print("draw a thermal column of clouds") 
    base = 1
    _dew, _dud, _dns = xp.worldToLocal(
        lat, lon, 0)  # Dew=E/W,Dud=Up/Down,Dns=N/S
    # from 100 to almost thermal top steps of 200
    for alt in range(base, world.thermal_tops-200, 200):
        _dx, _dy = calc_drift(alt)
        #AlX disabled for testing 2021-09-26
        #instance = xp.createInstance(thermal_column)
        #xp.instanceSetPosition(
        #    instance, [_dew + _dx, _dud + alt, _dns + _dy, 0, 0, 0])
        #world.instance_list.append(instance)


def draw_cloud(lat, lon):
    ''' Return the location for a cloud at the top of the raising thermal, accounting
        for wind drift along the climb.
    '''
    if world.DEBUG == 6 : print("Cloud-", end='') 

    # Dew=E/W,Dud=Up/Down,Dns=N/S
    _dew, _dud, _dns = xp.worldToLocal(lat, lon, 0)
    _alt = world.thermal_tops
    _dx, _dy = calc_drift(_alt)
    instance = xp.createInstance(huge_cloud)
    xp.instanceSetPosition(
        instance, [_dew + _dx, _dud + _alt, _dns + _dy, 0, 0, 0])
    world.instance_list.append(instance)


def draw_thermal_columns(lat, lon):
    ''' return a list of thermal location tuples, if the distance not exceeds max display
        draw the thermal column of rising air
    '''
    _p1x, _p1y = convert_lat_lon2meters(lat, lon)

    for athermal in world.thermal_dict:
        p2x, p2y = athermal.p_x, athermal.p_y
        if calc_dist(_p1x, _p1y, p2x, p2y) < world.max_draw_distance:
            draw_thermal(athermal.lat, athermal.lon)


def draw_clouds(lat, lon):
    ''' return a list of thermal location tuples, if the distance not exceeds max display
    Just the thermals at cloudbase
    '''
    if world.DEBUG == 6: print("draw_clouds") 
    p1x, p1y = convert_lat_lon2meters(lat, lon)

    for athermal in world.thermal_dict:
        p2x, p2y = athermal.p_x, athermal.p_y
        if calc_dist(p1x, p1y, p2x, p2y) < world.max_draw_distance:
            draw_cloud(athermal.lat, athermal.lon)


def eraseThermalsOnScreen():
    if world.DEBUG > 0: print("loop: Delete old instances #", len(world.instance_list))
    for i in world.instance_list:
        if world.DEBUG == 6 : print("loop: delete instance,", i)
        if i:
            try:
                xp.destroyInstance(i)
                world.instance_list.remove(i)
            except Exception as e:
                if world.DEBUG > 0: print(f"Exception destroying instance {i}: {e}")

def drawThermalsOnScreen(lat, lon):
    # if visibility is off, only draw clouds at cloudbase (no visible columns)

    if world.DEBUG == 6: print(" eraseThermalsOnScreen")
    eraseThermalsOnScreen()

    draw_clouds(lat, lon)

    if world.THERMAL_COLUMN_VISIBLE:
        draw_thermal_columns(lat, lon)

    if world.DEBUG == 6: print("set world_update = False")
    world.world_update = False
    return 1
