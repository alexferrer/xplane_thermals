#!/usr/bin/env python2

#thermal model generator library.
''' Thermal generator module
      for now just generate a spiral lift pattern of decreasing
      strength on a 2D (Lat,Lon) matrix.
      
      assorted helper & debug functions
'''

import world
from random import randrange, sample, choice
import math
import csv

# for lat2xyz
from XPLMGraphics import * 

#for terrain probe
from XPLMScenery import *

def calcDist(p1x,p1y,p2x,p2y):
    return math.sqrt( (p2x-p1x)**2 + (p2y-p1y)**2 )  # in meters


def calcDrift(alt):
    '''winddrift: as the thermal climbs, it is pushed by the prevailing winds.
       To account for the drift of the thermal use :
         wind vector (Dx,Dy) * time to reach altitude
    '''
    climb_time = alt/2.54                              # assuming a thermal raises at ~ 500ft/m
    drift = world.wind_speed * climb_time  
    dX = -int(round(math.sin(world.wind_dir) * drift )) #east/west drift 
    dY = int(round(math.cos(world.wind_dir) * drift )) #north/south drift
    return dX,dY

def calcLift(p1x,p1y,lat):
    lift = 0
    #test if we are inside any listed thermal
    for (lat1,lon1),(radius,strength) in world.thermal_dict.items() :
        p2x = lat1 * world.latlon2meter
        p2y = lon1 * world.latlon2meter * math.cos(math.radians(lat))
        #print "calclift:",p1x,p1y,p2x,p2y
        distance = calcDist(p1x,p1y,p2x,p2y) 
        # if our distance to center is < than radius, we are in!
        if distance < radius :
           lift += strength * round((radius - distance)/radius,2)
           #print "Dist ",lat1,lon1,radius, distance ,lift   
    return lift

def calcThermalBand(alt):
    top_factor = 1
    if (world.thermal_tops - alt) < 100:
       top_factor = ( world.thermal_tops - alt)/100
    return top_factor



def DrawThermal(lat,lon): #min_alt,max_alt
    ''' make a location list of thermal images along the raising thermal, accounting
        for wind drift along the climb. end at thermal tops
    '''
    base = 1
    Dew,Dud,Dns = XPLMWorldToLocal(lat,lon,0) #Dew=E/W,Dud=Up/Down,Dns=N/S 
    locs = []  #locations 
    for alt in range(base,world.thermal_tops,200): #from 100 to thermal top steps of  200
        dX,dY = calcDrift(alt)
        locs.append([Dew+dX,Dud+alt,Dns+dY, 0, 0, 0])
    return locs

def DrawThermalMap(lat,lon):
    locations = []
    p1x = lat * world.latlon2meter
    p1y = lon * world.latlon2meter * math.cos(math.radians(lat))
    
    for (thermal_lat,thermal_lon),(radius,strength) in world.thermal_dict.items() :
        p2x = thermal_lat * world.latlon2meter
        p2y = thermal_lon * world.latlon2meter * math.cos(math.radians(lat))
        #print "DrawThermalmap:",p1x,p1y,p2x,p2y
        if calcDist(p1x,p1y,p2x,p2y) < world.max_draw_distance :
            locations = locations + DrawThermal(thermal_lat,thermal_lon) 
    return locations



def CalcThermal(lat,lon,alt,heading,roll_angle):
      '''
       Calculate the strength of the thermal at this particular point 
       in space by computing the distance from center of all thermals
       and testing for thermal radius. 
       
       the value representing lift is the maxpower times a  % of distance away from center 
       
       Return the total lift and roll value 
      '''       
      planeX   = lat * world.latlon2meter       # current plane position  
      planeY   = lon * world.latlon2meter * math.cos(math.radians(lat))

      dX,dY = calcDrift(alt)     # total wind drift
      planeX +=  dX              # reverse apply to plane x,y
      planeY +=  dY
      
      # left and right wings position from current plane heading
      angleL   = math.radians(heading-90)
      angleR   = math.radians(heading+90)

      wingsize = world.wing_size  #size of each wing   10m -> -----(*)----- <-10m
      
      # left wing tip coordinates
      lwingX = planeX + math.cos(angleL)*wingsize
      lwingY = planeY + math.sin(angleL)*wingsize

      # right wing tip coordinates
      rwingX = planeX + math.cos(angleR)*wingsize
      rwingY = planeY + math.sin(angleR)*wingsize

      #Thermal Band: adjust thermal strength according to altitude band
      tband_factor = calcThermalBand(alt) 
	  
      liftL  =  calcLift(lwingX,lwingY,lat) * tband_factor 
      liftR  =  calcLift(rwingX,rwingY,lat) * tband_factor
      liftM  =  calcLift(planeX,planeY,lat) * tband_factor

      # total lift component
      thermal_value = ( liftL + liftR + liftM ) / 3
      
      # total roll component 
      #         the more airplane is rolled, the less thermal roll effect
      #         if the plane is flying inverted the roll effect should be reversed
      roll_factor = math.cos(math.radians(roll_angle))
      roll_value    = -(liftR - liftL) * roll_factor
      
      # for debug
      #print "pos[",'%.4f'%planeX,",",'%.4f'%planeY,"] @",'%.0f'%(heading), \
      #     ">",'%.1f'%(roll_angle), "T **[",'%.1f'%thermal_value,"|", '%.1f'%roll_value ,"]**",'%.1f'%alt
      
      #todo: thermals have cycles, begin, middle , end.. and reflect in strength.. 
      
      return thermal_value, roll_value


      #---------------- should move below to a different file
def MakeRandomThermalMap(_lat,_lon,_strength,_count,_radius) :
      ''' Create xx random thermals around the current lat/lon point 
        us parameters average strength
        Params: center (lat,lon) , max strength, count , radius 
        thermal_list =     { (lat,lon):(radius,strength) }
      '''
    
      average_radius = _radius
      tdict = {}
      count = 1
      for r in sample(xrange(1,40000), 900):
          x = r/200      # col
          y = r - x*200  # row
          radius = randrange(average_radius/5,average_radius) #random diameter for the thermal
          #randomize thermal strength weighted towards stronger
          strength = choice((3,4,5,6,6,7,7,7,8,8,9,9,10)) * _strength * .1
          lat = _lat + (x -100) * .001   # min thermal separation = 1km
          lon = _lon + (y -100) * .001   # max distance =  100x100 km 
          
          #No thermals start over water..
          info = []       
          x,y,z = XPLMWorldToLocal(lat,lon,0) #Dew=E/W,Dud=Up/Down,Dns=N/S 
          if (XPLMProbeTerrainXYZ(world.probe,x,y,z,info) == xplm_ProbeHitTerrain):
              if info[10]:  #if terrain is water, skip!
                  continue

          #(lat,lon):(radius,strength)  
          #print "makeRandomThermal",lat,lon,radius,strength
          tdict[(lat,lon)] = (radius,strength)
          count +=1 
          if count > _count :
             break 
           
      return tdict


# ----- begin test code --------

#print CalcThermal(-12.389,-76.7582,1000,0,45)
