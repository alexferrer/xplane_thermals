''' File: world.py
  Auth: Alex Ferrer @ 2014
  Central file to store all globally used variables.
  It is ugly to have globals but we depend on Xplane for lots of them
  so I rather read them once and store them here for all to use.
  * We store variables in their ready to use units format, (usually metric)
'''

from thermal import Thermal
LIB_VERSION = "Version ----------------------------   world.py v3.0"
print(LIB_VERSION)

plugin_enabled = False  # plugin enabled/disabled

# Holders for Stats Window display
#-------------------------------------
thermal_strength = 0 # meters per second
thermal_radius = 0 # meters
distance_from_center = 100000 # meters
tot_lift_force = 0 # Newtons
tot_thrust_force = 0 # Newtons
cal_lift_force = 0 # Newtons
tot_roll_force = 0 # Newtons
tot_pitch_force = 0 # Newtons

applied_lift_force = 0 # Newtons
applied_thrust_force = 0 # Newtons
applied_roll_force = 0 # Newtons
applied_pitch_force = 0 # Newtons

message  = "- - - - -"
message1 = " - - - - "
message2 = " x x x x "
#-------------------------------------
# debug mode  0 = off , 1= stats, 2 = some, 3 = more, 4 = all 
DEBUG = 0
PLUGIN_ENABLED = True
# handle image loading before plane bug
images_loaded = False   
update_loop = 0 
sun_factor = 0

kk7_hotspot_file_name = 'kk7_hotspots.csv'

# Conversion constants
nm2meter = 1852  # nautical miles to meters
latlon2meter = 111200  # crude conversion value for lat/lon to meters
f2m = 0.3048        # feet to meter conversion value
m2f = 3.280         # meter to feet
# max_draw_distance = 18520  # furthest thermals shown, 18.52km = 10nm visibility
max_draw_distance = 18520000  # furthest thermals shown, 18.52km = 10nm visibility

''' The wind vector is used to calculate the thermal drift 
    and it is considered when reading thermal strength and
    locations for thermal graphics display
    * later may want to consider more wind layers
'''
wind_speed = 0  # m/s
wind_dir = 0    # radians
world_update = True  # toggle on wind change
'''
   Thermal behaviour information
   There are many factors that affect thermal size and strength as they move
   up from the ground to the highest point.
   For now I will store those values here.. 

*http://www.skynomad.com/articles/height_bands.html
http://www.pilotoutlook.com/glider_flying/soaring_faster_and_farther
http://www.southerneaglessoaring.com/Storms/liftstrenghtgraph.htm
http://www.southerneaglessoaring.com/Storms/stormlift.htm
http://www.xcskies.com/map # may interact with this to get baseline data? 
'''

# ask21 turn diameter at 60mph = 133m, 80mph = 420m

# A list of thermals for testing { (lat,lon):(radius,strength) }
#Texas Soaring Gliderport TSA Airport Designator: TA11
'''
'''
default_thermal_list = [
    Thermal(32.324161530, -97.039894104, 200,  1), #lake 1
    Thermal(32.380264282, -97.079566956, 300,  2), # lake2
    Thermal(32.581195831, -96.719421387, 100,  3), #Lancaster Windsock
    Thermal(31.916921616, -97.204803467, 500,  4), #Y lake island
    Thermal(32.456172943, -96.911354065, 1000, 5), #KJWY Midlothian Windsock
    Thermal(32.390254974, -97.011375427, 50, .1),  #TSA Windsock
 
    ]

thermal_list = default_thermal_list

if DEBUG > 3:  print("Thermal dict->", thermal_list)

thermal_band = {1000: .8, 2000: .9, 3000: 1, 5000: 1, 5100: .4, 5500: 0}

# thermal_height_band # size/strength of thermal depending on altitude
''' need to model size/strenght of thermal against:
        time of day    : average lift depends on sun angle over the earth. 
                         sunrise  - - | - - - - - -| - sunset
                                low        best         low 
                         
                         thermal tops depends on time of day
                         sunrise  - - | - - - - - -| - sunset
                                low        high       high

                                  
        temperature
        altitude band : average lift increases with altitude until 10% of thermal top where it starts decreasing
                        beginning of band is terrain altitude dependant... 
                        todo:adjust calcthermal to account for this..
                        
        raob ?
'''
# GUI state variables
THERMAL_COLUMN_VISIBLE = False  # are thermals visible as clouds, start false
CALIBRATE_MODE = False  # set calibration mode on/off to generate fake thermal to adjust lift factor

# Thermal auto refersh data
thermal_map_start_time = 0    # Thermal map age in seconds
thermal_refresh_time = 60  # auto-refresh timr for thermal map in minutes

# Default thermal config values
thermal_tops = 2000  # 2000 meters thermal top
thermal_distance = 1000  # meters min separation distance between thermals
thermal_density = 200  #  qty of thermal generated

''''
Thermal size
50 <  small <= 150
150 > mid >= 400
400 > large >= 800
800 < xlarge
'''
thermal_size = 1500     # diameter of thermals in meters

'''
Thermal climb rate
0   <  weak   <= 2 m/s
2   <  mid    <= 4 m/s
4   <  strong <= 6 ms
6   <  bomb  
max = 15
'''
thermal_power = 5    # strength of thermals in m/s  * 10
thermal_cycle = 30    # thermal life cycle time in minutes
cloud_streets = False # not yet implemented..

'''Control factors
Constants for fine tuning the value of the lift forces from the thermal model into the plane. 
lift_val from model * lift_factor = final force to apply to plane
I suspect that different CPU's  will need different values and since a larger plane would 
have larger wing area, the lift factor will be different too.
Adjust using the Glider config menu in Xplane
'''
# 1kilo weights ~ 1 newton (9.8) newton
# ask21 (360kg) + pilot (80) = = 440kg,
# lift 440kg 1/ms = ~ 4400 newtons ?
# according to Ask21 manual at 70mph sink is 1m/s
# multiplication factor, calculated experimentally = 500...
# plugin refesh time affects this a lot!

# Lift and thrust force generated by the wings adjusted for ask21
lift_factor = 29  # ask21  3.9
thrust_factor = 29  # ask21  1.5

# Roll effect because of differential lift between wings.
roll_factor = 50  # ask21  
roll_test_pulse =  0  

pitch_factor = 2
pitch_test_pulse =  0

# wing span in meters for lift differential calculation
# size of each wing   10m -> -----(*)----- <-10m
wing_size = 25  # 10  times 2.5 to improve thefeel of roll effect as test
tail_size = 5  # distance of the tail from the center of gravity

def dummy_terrain_is_water(lat, lon):
    ''' Function that gets a value indicating whether the terrain at the geo location is water'''
    return False


terrain_is_water = dummy_terrain_is_water

# stuff for drawing of thermals
cloud_instance_list = []  # a list of all draw object instances
thermal_rings_instance_list = []    