#thermal model generator library.
''' Thermal generator module
      for now just generate a spiral lift pattern of decreasing
      strenght on a 2D (Lat,Lon) matrix.
      
      assorted helper & debug functions
'''

import world
from random import randrange, sample
import math
import csv
from XPLMGraphics import * 

def calcDist(p1x,p1y,p2x,p2y):
    return math.sqrt( (p2x-p1x)**2 + (p2y-p1y)**2 )  # in meters


def calcDrift(alt):
    '''winddrift: as the thermal climbs, it is pushed by the prevailing winds.
       To account for the drift of the thermal use :
         wind vector (Dx,Dy) * time to reach altitude
    '''
    climb_time = alt/2.54                              # assuming a thermal raises at ~ 500ft/m
    drift = world.wind_speed * climb_time  
    dX = int(round(math.cos(world.wind_dir) * drift )) #east/west drift 
    dY = int(round(math.sin(world.wind_dir) * drift )) #north/south drift
    return dX,dY

def calcLift(p1x,p1y):
    lift = 0
    #test if we are inside any listed thermal
    for (lat1,lon1),(radius,strenght) in world.thermal_dict.items() :
        p2x = lat1 * world.latlon2meter
        p2y = lon1 * world.latlon2meter
        distance = calcDist(p1x,p1y,p2x,p2y) 
        # if our distance to center is < than radius, we are in!
        if distance < radius :
           lift += strenght * (radius - distance)/radius
           #print "Dist ",lat1,lon1,radius, distance    
    return lift


def DrawThermal(lat,lon): #min_alt,max_alt
    ''' make a location list of thermal images along the raising thermal, accounting
        for wind drift along the climb. end at thermal tops
    '''
    base = 1
    Dew,Dud,Dns = XPLMWorldToLocal(lat,lon,0) #Dew=E/W,Dud=Up/Down,Dns=N/S 
    locs = []  #locations 
    for alt in range(base,world.thermal_tops,200): #from 100 to thermal top steps of  200
        dX,dY = calcDrift(alt)
        locs.append([Dew+dX,Dud+alt,Dns-dY, 0, 0, 0])
    return locs

def DrawThermalMap(lat,lon):
    locations = []
    p1x = lat * world.latlon2meter
    p1y = lon * world.latlon2meter
    
    for (thermal_lat,thermal_lon),(radius,strenght) in world.thermal_dict.items() :
        p2x = thermal_lat * world.latlon2meter
        p2y = thermal_lon * world.latlon2meter
        if calcDist(p1x,p1y,p2x,p2y) < world.max_draw_distance :
            locations = locations + DrawThermal(thermal_lat,thermal_lon) 
    return locations



def CalcThermal(lat,lon,alt,heading,roll_angle):
      '''
       Calculate the strenght of the thermal at this particular point 
       in space by computing the distance from center of all thermals
       and testing for thermal radius. 
       
       the value representing lift is the maxpower times a  % of distance away from center 
      '''       

      # calculate the total lift and roll value :
      planeX   = lat * world.latlon2meter       # current plane position  
      planeY   = lon * world.latlon2meter

      dX,dY = calcDrift(alt)        #total drift
      
      planeX +=  dX
      planeY +=  dY
      
      # left and right wings position from current plane heading
      angleL   = math.radians(heading-90)
      angleR   = math.radians(heading+90)

      wingsize = 10  #size of each wing   10m -> -----(*)----- <-10m
      
      # left wing tip coordinates
      lwingX = planeX + int(round(math.cos(angleL)*wingsize))
      lwingY = planeY + int(round(math.sin(angleL)*wingsize))

      # rigth wing tip coordinates
      rwingX = planeX + int(round(math.cos(angleR)*wingsize))
      rwingY = planeY + int(round(math.sin(angleR)*wingsize))

      #Thermal Top: gradually reduce thermal strength when alt is getting close to 10% of thermal tops
      top_factor = 1
      if (world.thermal_tops - alt) < 100:
          top_factor = ( world.thermal_tops - alt)/100

	  # lift for each area, left tip, right tip and middle.
      #print ">>>>>>>>>>>>>>",lwingX,lwingY,rwingX,rwingY,top_factor
	  
      liftL  =  calcLift(lwingX,lwingY) * top_factor 
      liftR  =  calcLift(rwingX,rwingY) * top_factor
      liftM  =  calcLift(planeX,planeY) * top_factor

      # total lift component
      thermal_value = liftL + liftR + liftM
      
      # total roll component 
      #         the more airplane is rolled, the less thermal roll effect
      #         if the plane is flying inverted the roll effect should be reversed
      roll_factor = math.cos(math.radians(roll_angle))
      roll_value    = -(liftR - liftL) * roll_factor
      
      # for debug
      print "pos[",'%.4f'%planeX,",",'%.4f'%planeY,"] @",'%.0f'%(heading), \
           ">",'%.1f'%(roll_angle), "T **[",'%.1f'%thermal_value,"|", '%.1f'%roll_value ,"]**",'%.1f'%alt
      
      #todo: thermals have cycles, begin, middle , end.. and reflect in strength.. 
      
      return thermal_value , roll_value


# ----- begin test code --------

#print CalcThermal(-12.389,-76.7582,1000,0,45)

