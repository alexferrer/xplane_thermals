# thermal model generator library.
''' Thermal generator module
    for now just generate a spiral lift pattern of decreasing
    strength on a 2D (Lat,Lon) matrix.
    assorted helper & debug functions
'''

import random
from random import randrange, sample, choice
import math
import world
import thermal

# comment out before testing with PlotThermals!!
#import xp


def calc_dist_square(p1x, p1y, p2x, p2y):
    ''' Calculates square distance between (p1x,p1y) and (p2x,p2y) in meter^2 '''
    return (p2x - p1x)**2 + (p2y - p1y)**2


def calc_dist(p1x, p1y, p2x, p2y):
    ''' Calculates distance between (p1x,p1y) and (p2x,p2y) in meters'''
    return math.sqrt(calc_dist_square(p1x, p1y, p2x, p2y))


def convert_lat_lon2meters(lat, lon):
    ''' Converts lat/lon to meters (approximation); returns a point (px,py)'''
    _px = lat * world.latlon2meter
    _py = lon * world.latlon2meter * math.cos(math.radians(lat))
    return (_px, _py)


def calc_drift(alt):
    ''' Calculates drift (based on wind direction and speed) in meters for the given altitude;
        returns (dx,dy)
        winddrift: as the thermal climbs, it is pushed by the prevailing winds.
        To account for the drift of the thermal use :
        wind vector (Dx,Dy) * time to reach altitude
    '''
    climb_time = alt / 2.54                              # assuming a thermal raises at ~ 500ft/m
    drift = world.wind_speed * climb_time
    _dx = -(math.sin(world.wind_dir) * drift)  # east/west drift
    _dy = (math.cos(world.wind_dir) * drift)  # north/south drift
    return _dx, _dy


def calc_lift(p1x, p1y):
    '''Claculate the lift component at this exact point'''
    lift = 0
    # test if we are inside any listed thermal
    for _thermal in world.thermal_dict:
        p2x, p2y = _thermal.p_x, _thermal.p_y
        distance_square = calc_dist_square(p1x, p1y, p2x, p2y)
        # print( "calclift:",int(p1x), int(p1y), int(p2x), int(p2y),
        #       "dist >",int(distance_square),thermal.radius )

        if distance_square < _thermal.radius_square:
            distance = math.sqrt(distance_square)
            lift += _thermal.strength * \
                round((_thermal.radius - distance) / _thermal.radius, 2)
            # print( "Dist ",lat1,lon1,radius, distance ,lift)
    return lift


def calc_thermal_band(alt):
    '''Calculate the lift per altitude band'''
    top_factor = 1
    if (world.thermal_tops - alt) < 100:
        top_factor = (world.thermal_tops - alt) / 100
    return top_factor


def calc_thermal(lat, lon, alt, heading, roll_angle):
    """
     Calculate the strength of the thermal at this particular point
     in space by computing the distance from center of all thermals
     and testing for thermal radius.
     the value representing lift is the maxpower times a  % of distance away from center
     Return the total lift and roll value.
    """
    # current plane position
    _plane_x, _plane_y = convert_lat_lon2meters(lat, lon)

    _dx, _dy = calc_drift(alt)     # total wind drift
    # instead off aplying it to the thermal list, reverse apply to the current plane position
    _plane_x += _dy
    _plane_y += _dx

    # left and right wings position from current plane heading
    _angle_l = math.radians(heading - 90)
    _angle_r = math.radians(heading + 90)

    # size of each wing   10m -> -----(*)----- <-10m
    wingsize = world.wing_size

    # left wing tip coordinates
    _lwing_x = _plane_x + math.cos(_angle_l) * wingsize
    _lwing_y = _plane_y + math.sin(_angle_l) * wingsize

    # right wing tip coordinates
    _rwing_x = _plane_x + math.cos(_angle_r) * wingsize
    _rwing_y = _plane_y + math.sin(_angle_r) * wingsize

    # Thermal Band: adjust thermal strength according to altitude band
    tband_factor = calc_thermal_band(alt)

    _lift_l = calc_lift(_lwing_x, _lwing_y) * tband_factor
    _lift_r = calc_lift(_rwing_x, _rwing_y) * tband_factor
    _lift_m = calc_lift(_plane_x, _plane_y) * tband_factor

    # total lift component
    thermal_value = (_lift_l + _lift_r + _lift_m) / 3

    # total roll component
    #         the more airplane is rolled, the less thermal roll effect
    #         if the plane is flying inverted the roll effect should be reversed

    roll_factor = math.cos(math.radians(roll_angle))
    roll_value = -(_lift_r - _lift_l) * roll_factor

    """ For debug.

    print( "pos[",'%.4f'%planeX,",",'%.4f'%planeY,"] @",'%.0f'%(heading), \
         ">",'%.1f'%(roll_angle), "T **[",'%.1f'%thermal_value,"|",
      '%.1f'%roll_value ,"]**",'%.1f'%alt)
    """

    """Todo: thermals have cycles, begin, middle , end.. and reflect in strength.."""

    return thermal_value, roll_value


def make_random_thermal_map(time, _lat, _lon, _strength, _count, _radius):
    ''' Create xx random thermals around the current lat/lon point.
      us parameters average strength
      Params: center (lat,lon) , max strength, count , radius
      thermal_list =     { (lat,lon):(radius,strength) }
    '''
    random.seed()  # initialize the random generator using system time
    average_radius = _radius
    thermals = []
    ''' to position a new thermal:
        create a 200x200 grid numbered sequentially 1 to 40000
        pick spots on the grid at random and multiply x,y times thermal-distance
        add distance to current plane lat/lon
    '''
    for _r in sample(range(1, 40000), _count):
        _x = int(_r / 200)      # get a column from 0 - 200
        _y = _r % 200     # get row from 0 - 200
        #print("new thermal = ",r,x,y )

        # random diameter for the thermal
        radius = randrange(int(average_radius / 5), average_radius)
        # randomize thermal strength weighted towards stronger
        strength = choice((3, 4, 5, 6, 6, 7, 7, 7, 8,
                          8, 9, 9, 10)) * _strength * .1

        # calculate position for new thermal
        # thermal separation in meters
        lat = _lat + (_x-100) * world.thermal_distance * .00001
        lon = _lon + (_y-100) * world.thermal_distance * .00001

        # No thermals start over water..
        if world.terrain_is_water(lat, lon):
            #print("we are over water ?....")
            continue

        # create the thermal
        thermals.append(thermal.Thermal(lat, lon, radius, strength))
        if world.DEBUG:
            print("makeRandomThermal", lat, lon, radius, strength)

    # for debug make a large thermal arount current _lat,_lon position
    if world.DEBUG:
        thermals.append(thermal.Thermal(
            _lat, _lon, average_radius*10, _strength*10))

    # reset the thermal start time to now
    world.thermal_map_start_time = time
    print("# of generated thermals", len(thermals))
    return thermals


def make_csv_thermal_map(_lat, _lon, _strength, _count, _radius):
    ''' Create xx random thermals around the hotspot lat/lon point
      us parameters average strength
      Params: center (lat,lon) , max strength, count , radius
      thermal_list =     { (lat,lon):(radius,strength) }
    '''
    #csv_list = world.hotspots
    hotspots = world.hotspots
    # hotspots = [(36.7913278, -119.3000250,255,70),(36.7845528,
    # -119.3029139,275, 20),(36.7974417, -119.2900083,435, 100)]
    average_radius = _radius
    thermals = []
    print(_strength)
    if _count < len(hotspots):
        count = _count
    else:
        count = len(hotspots)

    for select_spot in sample(range(0, len(hotspots)), count):

        _r = randrange(1, 40000)
        prob_test = random.random() * 100 / 2
        # probabilty test has to be random.random()*100 ,
        # but we need would need more thermal hotspots then
        hotspot_prob = hotspots[select_spot][3]
        if hotspot_prob > prob_test:
            hotspot_lat = hotspots[select_spot][0]
            hotspot_lon = hotspots[select_spot][1]
            _x = _r / 200      # col
            _y = _r - _x * 200  # row
            # random diameter for the thermal
            radius = randrange(average_radius / 5, average_radius)
            # randomize thermal strength weighted towards stronger
            strength = choice((4, 5, 5, 6, 6, 7, 7, 7, 8,
                              8, 9, 9, 10)) * _strength * .1
            # min thermal separation = 100m
            lat = hotspot_lat + (_x - 100) * .00001
            # max distance =  100x100 100m
            lon = hotspot_lon + (_y - 100) * .00001

            # No thermals start over water..
            if world.terrain_is_water(lat, lon):
                continue

            # (lat,lon):(radius,strength)
            # print( "makeRandomThermal",lat,lon,radius,strength)
            #thermals[(lat,lon)] = (radius,strength)
            thermals.append(thermal.Thermal(lat, lon, radius, strength))

    return thermals
