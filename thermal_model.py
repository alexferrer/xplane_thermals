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
import xp

# comment out before testing with PlotThermals!!
LIB_VERSION = "Version ----------------------------   thermal_model V3.0"
print(LIB_VERSION)

def calc_dist_square(p1x, p1y, p2x, p2y):
    ''' Calculates square distance between (p1x,p1y) and (p2x,p2y) in meter^2 '''
    return (p2x - p1x)**2 + (p2y - p1y)**2


def calc_dist(p1x, p1y, p2x, p2y):
    ''' Calculates distance between (p1x,p1y) and (p2x,p2y) in meters'''
    return math.sqrt(calc_dist_square(p1x, p1y, p2x, p2y))

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
    '''Calculate the lift component at this exact point'''
    lift = 0

    #Find closest thermal in the Thermal array
    closest_thermal = world.thermal_list[0]  # first entry of the thermal array
    min_distance = 1000000000000
    
    n = 0
    for _thermal in world.thermal_list:
        #n += 1
        p2x,alt,p2y = xp.worldToLocal(_thermal.lat, _thermal.lon, 0)
        distance = calc_dist(p1x, p1y, p2x, p2y)
        if distance < min_distance:
            min_distance = distance
            closest_thermal = _thermal
            #close_n = n

    #print ("-------------  thermal dict size =", len(world.thermal_list) , "closest = ", close_n)

    distance = min_distance
    #if inside the thermal compute forces
    if closest_thermal is not None and distance < closest_thermal.radius:
        # lift is the thermal strength times % of distance away from center
        lift += closest_thermal.strength *                                  \
            round((closest_thermal.radius - distance) / closest_thermal.radius, 2)
        
        world.tot_lift_force = lift

    world.thermal_strength = closest_thermal.strength
    world.thermal_radius = closest_thermal.radius
    world.distance_from_center = distance

    p2x,alt,p2y = xp.worldToLocal(closest_thermal.lat, closest_thermal.lon, 0)
    
    return lift


def calc_thermal_band(alt):
    '''Calculate the lift per altitude band'''
    top_factor = 1
    if (world.thermal_tops - alt) < 100:
        top_factor = (world.thermal_tops - alt) / 100
    return top_factor


def calc_thermalx(lat, lon, alt, heading, airplane_roll_angle, airplane_pitch_angle):
    """
     Calculate the strength of the thermal at this particular point
     in space by computing the distance from center of all thermals
     and testing for thermal radius.
     the value representing lift is the maxpower times a  % of distance away from center
     Return the total lift and roll value.
    """
    world.message  =  "Lat( "+str(round(lat,3)) + ") Lon( "+str(round(lon,3)) 
    world.message1 =  "Hed("+str(round(heading,3) ) + ") Rl("+str(round(airplane_roll_angle,3) ) + ") Pt("+str(round(airplane_pitch_angle,3) )
    # current plane position
    _plane_ew, _plane_alt, _plane_ns = xp.worldToLocal(lat, lon, alt)
    _dx, _dy = calc_drift(alt)     # total wind drift

    # instead off aplying it to the thermal list, reverse apply to the current plane position
    _plane_ew = _plane_ew - _dx  # east / west
    _plane_ns = _plane_ns - _dy # north / south

    # left and right wings position from current plane heading
    _angle_l = math.radians(heading ) # left wing position
    _angle_r = math.radians(heading + 180) # right wing position
    _angle_t = math.radians(heading + 90)  # tail position

    # size of each wing   10m -> -----(*)----- <-10m
    # tail size is 5m

    # left wing tip coordinates
    _lwing_x = _plane_ew + math.cos(_angle_l) * world.wing_size*3 #* 2 for testing feeling of wing bump
    _lwing_y = _plane_ns + math.sin(_angle_l) * world.wing_size*3

    # right wing tip coordinates
    _rwing_x = _plane_ew + math.cos(_angle_r) * world.wing_size*3
    _rwing_y = _plane_ns + math.sin(_angle_r) * world.wing_size*3

    # tail coordinates
    _tail_x = _plane_ew + math.cos(_angle_t) * world.tail_size
    _tail_y = _plane_ns + math.sin(_angle_t) * world.tail_size


    # Thermal Band: adjust thermal strength according to altitude band
    #alx tband_factor = calc_thermal_band(alt)
    tband_factor = 1

    _lift_l = calc_lift(_lwing_x, _lwing_y) 
    _lift_r = calc_lift(_rwing_x, _rwing_y) 
    _lift_m = calc_lift(_plane_ew, _plane_ns) 
    _lift_t = calc_lift(_tail_x, _tail_y) 

    # total lift component
    lift_value = (_lift_l + _lift_r + _lift_m) / 3 * tband_factor
    
    # total roll component
    #         the more airplane is rolled, the less thermal roll effect
    #         if the plane is flying inverted the roll effect should be reversed
    #         the roll effect is proportional to the difference in lift between wings
    #         should add some pitch change to the roll effect.

    #compensate for the roll angle of the plane on the roll forces
    roll_angle_factor = math.cos(math.radians(airplane_roll_angle))   
    roll_speed_factor = 1 # TBD should be inversly proportional to the speed of the plane

    roll_value = (_lift_r - _lift_l) * roll_angle_factor * world.roll_factor * 2.5 * roll_speed_factor
    world.tot_roll_force = roll_value


    # total pitch component
    #         the more airplane is pitched, the less thermal effect
    #         if the plane is flying inverted the pitch effect should be reversed
    #         the pitch effect is proportional to the difference in lift between wings and tail
    pitch_angle_factor = math.cos(math.radians(airplane_pitch_angle))   
    pitch_value = (_lift_r - _lift_l) * pitch_angle_factor * world.pitch_factor 
    world.tot_pitch_force = pitch_value
    
    if world.DEBUG > 6 : print( "pos[",'%.4f'%_plane_ew,",",'%.4f'%_plane_ns,"] head",'%.0f'%(heading), \
         "roll ",'%.1f'%(airplane_roll_angle), "   Lift [",'%.1f'%lift_value,"| Roll:",
      '%.1f'%roll_value ,"]   ",'%.1f'%alt)      

    world.message2  =  "L("+str(round(lift_value,3)) + ") R("+str(round(roll_value,3)) + ") P("+str(round(pitch_value,3)) 

    """Todo: thermals have cycles, begin, middle , end.. and reflect in strength.."""
    return lift_value, roll_value, pitch_value


def make_random_thermal_map(time, _lat, _lon, _strength, _count, _radius):
    ''' Create xx random thermals around the current lat/lon point.
      us parameters average strength
      Params: center (lat,lon) , max strength, count , radius
      thermal_list =     { (lat,lon):(radius,strength) }
    '''

    if world.DEBUG > 3:
        print("makeRandomThermalMap lat lon strength count radius", _lat, _lon, _strength, _count, _radius)
    

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
        # from 30% to 100% _strength
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
        if world.DEBUG > 3:
            print("RandomThermal > ", lat, lon, radius, strength)

    # reset the thermal start time to now
    world.thermal_map_start_time = time
    if world.DEBUG > 3: print("# of generated thermals", len(thermals))
    return thermals

import csv
import os
def make_thermal_map_kk7(_time, _strength, _radius):
    ''' Create xx random thermals around the hotspot provded by thermals.kk7
        https://thermal.kk7.ch/#30.862,-96.53,10
        use CSV file
        Lat , Lon , Altitude , Probability

    '''
    file_path = world.kk7_hotspot_file_name

    average_radius = _radius
    thermals = []
    if not os.path.exists(file_path):
        print(f"File {file_path} does not exist. Skipping thermal map creation.")
        return thermals
    
    with open(file_path, mode='r') as file:
        csv_reader = csv.reader(file)
        next(csv_reader)  # Skip the header row
        for row in csv_reader:
            lat, lon, alt, prob = row
            _lat = float(lat)
            _lon = float(lon)
            _prob = float(prob)
            # random diameter for the thermal
            radius = randrange(int(average_radius / 5), average_radius)
            # randomize thermal strength weighted towards stronger
            strength = choice((4, 5, 5, 6, 6, 7, 7, 7, 8,
                              8, 9, 9, 10)) * _strength * .1
            thermals.append(thermal.Thermal(_lat, _lon, radius, strength))
            print("makeKK7Thermal", _lat, _lon, radius, strength)

    # reset the thermal start time to now
    world.thermal_map_start_time = _time
    print("# of generated thermals", len(thermals))    
    return thermals
