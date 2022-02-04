""" Module to keep all thermal drawing stuff """
import xp
import world
from thermal_model import convert_lat_lon2meters, calc_dist, calc_drift

# cloudbase_image
#paths = []
#print("paths", paths)
# xp.lookupObjects(HUGE_CLOUD, 0, 0, lambda path,
#                 refCon: paths.append(path), None)
#print("paths", paths)
#huge_cloud = xp.loadObject(paths[0])
#print("huge-cloud", huge_cloud)

#HUGE_CLOUD = 'lib/dynamic/balloon.obj'
#LARGE_CLOUD = 'lib/airport/Common_Elements/Fuel_Storage/Sing_Tank_Large.obj'
# 'lib/street/various/porta_potty.obj'
#SMALL_CLOUD = 'lib/airport/landscape/windsock.obj'
# 'lib/airport/Common_Elements/Markers/Poles/Large_Red_White.obj'
#THERMAL_COLUMN = 'lib/dynamic/seagull_glide.obj'

# Images to represent thermals and various clouds
thermal_column = xp.loadObject(
    'Resources/default scenery/sim objects/dynamic/SailBoat.obj')

huge_cloud = xp.loadObject(
    'Resources/default scenery/sim objects/dynamic/Nimitz.obj')  # balloon1.obj')

large_cloud = xp.loadObject(
    'Resources/default scenery/sim objects/dynamic/balloon2.obj')

small_cloud = xp.loadObject(
    'Resources/default scenery/sim objects/dynamic/Perry.obj')  # balloon3.obj')


def draw_thermal(lat, lon):  # min_alt,max_alt
    ''' Draw a images along the raising thermal, accounting
        for wind drift along the climb. end at almost the thermal top
    '''
    base = 1
    _dew, _dud, _dns = xp.worldToLocal(
        lat, lon, 0)  # Dew=E/W,Dud=Up/Down,Dns=N/S
    # from 100 to almost thermal top steps of 200
    for alt in range(base, world.thermal_tops-200, 200):
        _dx, _dy = calc_drift(alt)
        instance = xp.createInstance(thermal_column)
        xp.instanceSetPosition(
            instance, [_dew + _dx, _dud + alt, _dns + _dy, 0, 0, 0])
        world.instance_list.append(instance)


def draw_cloud(athermal):
    ''' Draw a single cloud at the top of the raising thermal, accounting
        for wind drift along the climb.
        Select the image based on thermal size.
    '''

    # Dew=E/W,Dud=Up/Down,Dns=N/S
    _dew, _dud, _dns = xp.worldToLocal(athermal.lat, athermal.lon, 0)
    _alt = world.thermal_tops
    _dx, _dy = calc_drift(_alt)

    # select which cloud to draw based on strength (later radius? )
    print(f"T={athermal.strength}")
    if athermal.strength > 2000:
        instance = xp.createInstance(huge_cloud)

    elif athermal.strength < 400:
        instance = xp.createInstance(small_cloud)

    else:
        instance = xp.createInstance(large_cloud)

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
    p1x, p1y = convert_lat_lon2meters(lat, lon)

    for athermal in world.thermal_dict:
        p2x, p2y = athermal.p_x, athermal.p_y
        if calc_dist(p1x, p1y, p2x, p2y) < world.max_draw_distance:
            draw_cloud(athermal)


def erase_thermals_on_screen():
    """ detroy all image objects = clear screen   """
    if world.DEBUG:
        print("loop: Delete old instances")
    for i in world.instance_list:
        if world.DEBUG:
            print("loop: delete instance,", i)
        if i:
            xp.destroyInstance(i)


def draw_thermals_on_screen(lat, lon):
    """ Draw objects representing clouds and thermals (if needed) """
    # if visibility is off, only draw clouds at cloudbase (no visible columns)

    erase_thermals_on_screen()

    draw_clouds(lat, lon)

    if world.THERMALS_VISIBLE:
        draw_thermal_columns(lat, lon)

    world.world_update = False
    return 1
