import world
import thermal
from thermal_model import calc_dist, calc_drift
import xp # type: ignore

LIB_VERSION = "Version ----------------------------   draw_thermals.py v2.0"
print(LIB_VERSION)

THERMAL_COLUMN_sm = 'Resources/plugins/PythonPlugins/t_ring_50.obj'
THERMAL_COLUMN_m  = 'Resources/plugins/PythonPlugins/t_ring_200.obj'
THERMAL_COLUMN_lg = 'Resources/plugins/PythonPlugins/t_ring_800.obj'
thermal_column_sm = None
thermal_column_m = None
thermal_column_lg = None
huge_cloud = None


# thermal column and cloud images
def load_image_objects():
   global huge_cloud 
   global thermal_column_sm 
   global thermal_column_m 
   global thermal_column_lg 

   thermal_column_sm = xp.loadObject(THERMAL_COLUMN_sm)
   thermal_column_m = xp.loadObject(THERMAL_COLUMN_m)
   thermal_column_lg = xp.loadObject(THERMAL_COLUMN_lg)
   huge_cloud = xp.loadObject('Resources/plugins/PythonPlugins/mt_scenery.obj')
   # huge_cloud = xp.loadObject('Custom Scenery/X-Plane Airports - TNCS Juancho E Yrausquin/objects/mt_scenery.obj')



def draw_thermal_column(lat, lon, radius):  # min_alt,max_alt
    ''' Draw thermal images ( Rings ) along the raising thermal, accounting
        for wind drift along the climb. end at almost the thermal top
    '''
    if world.DEBUG > 4 : print("B ", end='') 

    base = 1
    _dew, _dud, _dns = xp.worldToLocal(
        lat, lon, 0)  # Dew=E/W,Dud=Up/Down,Dns=N/S
    # from 100 to almost thermal top steps of 300
    for alt in range(base, world.thermal_tops-200, 300):
        _dx, _dy = calc_drift(alt)
        if radius < 100:
            ring_instance = xp.createInstance(thermal_column_sm)
        elif radius >= 100 and radius < 500:
            ring_instance = xp.createInstance(thermal_column_m)  
        else:       
            ring_instance = xp.createInstance(thermal_column_lg)

        xp.instanceSetPosition(
            ring_instance, [_dew + _dx, _dud + alt, _dns + _dy, 0, 0, 0])
        world.thermal_rings_instance_list.append(ring_instance)


def draw_cloud(lat, lon):
    ''' Return the location for a cloud at the top of the raising thermal, accounting
        for wind drift along the climb.
    '''
    if world.DEBUG > 5 : print("Cloud-", end='') 

    # Dew=E/W,Dud=Up/Down,Dns=N/S
    _dew, _dud, _dns = xp.worldToLocal(lat, lon, 0)
    _alt = world.thermal_tops
    _dx, _dy = calc_drift(_alt)
    cloud_instance = xp.createInstance(huge_cloud)
    xp.instanceSetPosition(
        cloud_instance, [_dew + _dx, _dud + _alt, _dns + _dy, 0, 0, 0])
    world.cloud_instance_list.append(cloud_instance)


def draw_thermal_columns(lat, lon):
    ''' return a list of thermal location tuples, if the distance not exceeds max display
        draw the thermal column of rising air
    '''
    _p1x, alt, _p1y  = xp.worldToLocal(lat, lon,0)

    for athermal in world.thermal_list:
        p2x, p2y , radius = athermal.p_x, athermal.p_y, athermal.radius 
        if calc_dist(_p1x, _p1y, p2x, p2y) < world.max_draw_distance:
            draw_thermal_column(athermal.lat, athermal.lon, radius)


def draw_clouds(lat, lon):
    ''' return a list of thermal location tuples, if the distance not exceeds max display
    Just the thermals at cloudbase
    '''
    if world.DEBUG > 4: print("draw_clouds") 
    p1x,alt, p1y = xp.worldToLocal(lat, lon,0)

    for athermal in world.thermal_list:
        p2x, p2y = athermal.p_x, athermal.p_y
        if calc_dist(p1x, p1y, p2x, p2y) < world.max_draw_distance:
            draw_cloud(athermal.lat, athermal.lon)


def eraseThermalsCloudsOnScreen():
    if world.DEBUG > 3: print("Delete old cloud instances #", len(world.cloud_instance_list))
    csize = len(world.cloud_instance_list)
    for x in range(csize):
       i = world.cloud_instance_list[x]
       xp.destroyInstance(i)

    world.cloud_instance_list = []

def eraseThermalsRingsOnScreen():
    tsize = len(world.thermal_rings_instance_list)
    print("Delete old thermal instances #", tsize)
    for x in range(tsize):
       i = world.thermal_rings_instance_list[x]
       xp.destroyInstance(i)

    world.thermal_rings_instance_list = []


def drawThermalsOnScreen(lat, lon):
    # if visibility is off, only draw clouds at cloudbase (no visible columns)

    if world.DEBUG > 5: print(" eraseThermalsRingsOnScreen, draw_clouds, reset update")

    eraseThermalsRingsOnScreen()
    eraseThermalsCloudsOnScreen()
    draw_clouds(lat, lon)

    if world.THERMAL_COLUMN_VISIBLE:
        draw_thermal_columns(lat, lon)

    if world.DEBUG > 5: print("set world_update = False")
    world.world_update = False
    return 1
