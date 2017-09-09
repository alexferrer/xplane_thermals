#!/usr/bin/env python2

''' 
  File: world.py
  Auth: Alex Ferrer @ 2014
  Central file to store all globally used variables.
  
  It is ugly to have globals but we depend on Xplane for lots of them
  so I rather read them once and store them here for all to use.
 
  * We store variables in their ready to use units format, (usually metric)
'''
from thermal import Thermal

# Conversion constants
nm2meter = 1852 # nautical miles to meters
latlon2meter = 111200  # crude conversion value for lat/lon to meters
f2m = 0.3048        # feet to meter conversion value
m2f = 3.280         # meter to feet
max_draw_distance = 18520 # furthest thermals shown, 18.52km = 10nm visibility

''' The wind vector is used to calculate the thermal drift 
    and it is considered when reading thermal strength and
    locations for thermal graphics display
    * later may want to consider more wind layers
'''
wind_speed = 0  # m/s
wind_dir   = 0    # radians
world_update = False # toggle on wind change
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
default_thermal_dict = [
        Thermal(-12.3890,-76.7581, 500,30),
        Thermal(-12.3994,-76.7666, 400,10),
        Thermal(-12.3774,-76.7815, 300,20),
        Thermal(-12.3016,-76.8448, 200,40),
        Thermal(-12.4647,-76.7516, 150,50),
        Thermal(-12.7623,-76.6061, 900,60) ]

thermal_dict = default_thermal_dict

thermal_band = {1000:.8,2000:.9,3000:1,5000:1,5100:.4,5500:0}

thermal_tops  = 1500 # maximum altitude for thermals in meters (may change based on temp/time of day/ etc. 
#thermal_height_band # size/strength of thermal depending on altitude
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
#GUI state variables
thermals_visible = True

#Default thermal config values
thermal_tops    = 2000    # meters thermal top
thermal_density = 60      # qty of thermal generated
thermal_size    = 500     # diameter of thermals in meters
thermal_power   = 1000     # strength of thermals in fpm lift
thermal_cycle   = 30      # thermal life cycle time in minutes
cloud_streets   = False   # not yet implemented.. 

''' 
Control factors
Constants for fine tuning the value of the lift forces from the thermal model into the plane. 
lift_val from model * lift_factor = final force to apply to plane
I suspect that different CPU's  will need different values and since a larger plane would 
have larger wing area, the lift factor will be different too.
Adjust at your own peril.. :) 
'''
        # 1kilo weights ~ 1 newton (9.8) newton               
        # ask21 (360kg) + pilot (80) = = 440kg, 
        # lift 440kg 1/ms = ~ 4400 newtons ?
        # according to Ask21 manual at 70mph sink is 1m/s
        # multiplication factor, calculated experimentally = 500...
        # plugin refesh time affects this a lot!

# Lift force generated by the wings adjusted for ask21
lift_factor   = 6.0   #ask21  3.9

# Roll effect because of differential lift between wings. 
roll_factor   = 100   #ask21  100

# For realism purposes, some of the lift has to go to forward thrust
thrust_factor = 5.0  #ask21  1.1

# wing span in meters for lift differential calculation
# size of each wing   10m -> -----(*)----- <-10m
wing_size     = 10     #10


# Function that converts a geo location lat/lon/alt to coordinates x/y/z; returns tuple(x,y,z)
def dummy_world_to_local(lat, lon, alt):
    return (lat, lon, alt)

world_to_local = dummy_world_to_local


# Function that gets a value indicating whether the terrain at the geo location is water
def dummy_terrain_is_water(lat, lon):
    return False

terrain_is_water = dummy_terrain_is_water
