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

def DrawThermal(lat,lon): #min_alt,max_alt
    ''' make a location list of thermal images along the raising thermal, accounting
        for wind drift along the climb. end at thermal tops
    '''
    base = 1
    Dew,Dud,Dns = XPLMWorldToLocal(lat,lon,0) #Dew=E/W,Dud=Up/Down,Dns=N/S 
    locs = []  #locations 
    for alt in range(base,world.thermal_tops,200): #from 100 to thermal top steps of  200
        climb_time = alt/2.54           # assuming thermal raises at ~ 500ft/m
        drift = world.wind_speed * climb_time  
        dY = int(round(math.cos(world.wind_dir) * drift )) #east/west drift 
        dX = -int(round(math.sin(world.wind_dir) * drift )) #north/south drift
        locs.append([Dew+dX,Dud+alt,Dns+dY, 0, 0, 0])
    return locs

def DrawThermalMap():
    locations = []
    for lat,lon,size in world.thermal_list :   
        locations = locations + DrawThermal(lat,lon) 

    return locations

def MakeThermalModelFromList(_thermal_list):
    ''' return an array representing an area of Size x Size
        populated with fixed position thermals
        note: ignore size,tcount,_diameter
    '''
    model = [[0 for col in range(world.map_size)] for row in range(world.map_size)] 
    #populate thermal map with thermals from a list on world file
    for lat,lon,size in _thermal_list :   
        make_thermal(model,size,lat,lon)

    return model

def calcDist(p1x,p1y,p2x,p2y):
    return math.sqrt( (p2x-p1x)**2 + (p2y-p1y)**2 )  # in meters


def calcLift(p1x,p1y):
    lift = 0
    #test if we are inside any listed thermal
    for (lat1,lon1),radius in world.thermal_dict.items() :
        p2x = lat1 * 111200
        p2y = lon1 * 111200
        distance = calcDist(p1x,p1y,p2x,p2y) 
        # if our distance to center is < than radius, we are in!
        if distance < radius :
           lift += 10 * (radius - distance)/radius
           #print "Dist ",lat1,lon1,radius, distance    
    
    return lift



def CalcThermal(lat,lon,alt,heading,roll_angle):
      '''
       Calculate the strenght of the thermal at this particular point 
       in space by computing the distance from center of all thermals
       and testing for thermal radius. 
       
       the value representing lift is the maxpower times a  % of distance away from center 
       
       for lat/lon, 12.3456789
         .1     = 11,120 meters
         .01    =  1,120 m
         .001   =    120 m
         .0001  =     11 m
         .00001 =      1 m
       
      '''       

      '''
       calculate the total lift and roll value :
      '''
      # current plane position  
      # use 2,3,4 decimals ex: -12.34567 should return : 3456
      #     equivalent to 10 x 1120 m2 with a cell resolution of 11m2
      planeX   = lat * 111200 
      planeY   = lon * 111200

      # winddrift: as the thermal climbs, it is pushed by the prevailing winds
      #    to account for the drift of the thermal add (wind vector * time to reach altitude) 
      #    to plane, 

      climb_time = alt/2.54           # assuming thermal raises at ~ 500ft/m
      drift = world.wind_speed * climb_time # drift in cells at 11meters per cell.. 
      planeX = planeX - int(round(math.cos(world.wind_dir) * drift ))
      planeY = planeY - int(round(math.sin(world.wind_dir) * drift ))
      
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
      #print "------------",liftL,liftM,liftR

      # total lift component
      thermal_value = liftL + liftR + liftM
      
      # total roll component 
      #         the more airplane is rolled, the less thermal roll effect
      #         if the plane is flying inverted the roll effect should be reversed
      roll_factor = math.cos(math.radians(roll_angle))
      roll_value    = (liftR - liftL) * roll_factor
      
      # for debug
      print "pos[",planeX,",",planeY,"] @",'%.0f'%(heading), \
           ">",'%.1f'%(roll_angle), "T **[",'%.1f'%thermal_value,"|", '%.1f'%roll_value ,"]**",'%.1f'%alt,world.thermal_map[ planeX ][ planeY ]
      
      #todo: thermals have cycles, begin, middle , end.. and reflect in strength.. 
      
      return thermal_value , roll_value


# ----- begin test code --------

#print CalcThermal(-12.389,-76.7582,1000,0,45)

