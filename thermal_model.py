#!/usr/bin/env python2

#thermal model generator library.
''' Thermal generator module
      for now just generate a spiral lift pattern of decreasing
      strength on a 2D (Lat,Lon) matrix.
      
      assorted helper & debug functions
'''

import world
import thermal
import random
from random import randrange, sample, choice
import math
import csv



# Calculates square distance between (p1x,p1y) and (p2x,p2y) in meter^2
def calcDistSquare(p1x,p1y,p2x,p2y):
    return (p2x-p1x)**2 + (p2y-p1y)**2

# Calculates distance between (p1x,p1y) and (p2x,p2y) in meters
def calcDist(p1x,p1y,p2x,p2y):
    return math.sqrt( calcDistSquare(p1x,p1y, p2x,p2y) )

# Converts lat/lon to meters (approximation); returns (px,py)
def convertLatLon2Meters(lat, lon):
    px = lat * world.latlon2meter
    py = lon * world.latlon2meter * math.cos(math.radians(lat))
    return (px, py)

# Calculates drift (based on wind direction and speed) in meters for the given altitude; returns (dx,dy)
def calcDrift(alt):
    '''winddrift: as the thermal climbs, it is pushed by the prevailing winds.
       To account for the drift of the thermal use :
         wind vector (Dx,Dy) * time to reach altitude
    '''
    climb_time = alt/2.54                              # assuming a thermal raises at ~ 500ft/m
    drift = world.wind_speed * climb_time  
    dX = -(math.sin(world.wind_dir) * drift ) #east/west drift 
    dY = (math.cos(world.wind_dir) * drift ) #north/south drift
    return dX,dY

def calcLift(p1x,p1y):
    lift = 0
    #test if we are inside any listed thermal
    for thermal in world.thermal_dict:
        p2x, p2y = thermal.px, thermal.py
        #print "calclift:",p1x,p1y,p2x,p2y

        distance_square = calcDistSquare(p1x,p1y, p2x,p2y)
        if distance_square < thermal.radius_square:
            distance = math.sqrt(distance_square)
            lift += thermal.strength * round((thermal.radius - distance) / thermal.radius,2)
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
    Dew,Dud,Dns = world.world_to_local(lat,lon,0) #Dew=E/W,Dud=Up/Down,Dns=N/S 
    locs = []  #locations 
    for alt in range(base,world.thermal_tops,200): #from 100 to thermal top steps of  200
        dX,dY = calcDrift(alt)
        locs.append([Dew+dX,Dud+alt,Dns+dY, 0, 0, 0])
    return locs

def DrawThermalMap(lat,lon):
    locations = []
    p1x, p1y = convertLatLon2Meters(lat, lon)
    
    for thermal in world.thermal_dict:
        p2x, p2y = thermal.px, thermal.py
        #print "DrawThermalmap:",p1x,p1y,p2x,p2y
        if calcDist(p1x,p1y, p2x,p2y) < world.max_draw_distance :
            locations = locations + DrawThermal(thermal.lat, thermal.lon)
    return locations



def CalcThermal(lat,lon,alt,heading,roll_angle):
      '''
       Calculate the strength of the thermal at this particular point 
       in space by computing the distance from center of all thermals
       and testing for thermal radius. 
       
       the value representing lift is the maxpower times a  % of distance away from center 
       
       Return the total lift and roll value 
      '''       
      # current plane position
      planeX, planeY = convertLatLon2Meters(lat, lon)

      dX,dY = calcDrift(alt)     # total wind drift
      planeX +=  dY              # instead off aplying it to the thermal list, reverse apply to the current plane position
      planeY +=  dX
      
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
    
      liftL  =  calcLift(lwingX,lwingY) * tband_factor 
      liftR  =  calcLift(rwingX,rwingY) * tband_factor
      liftM  =  calcLift(planeX,planeY) * tband_factor

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
      thermals = []
      for r in sample(xrange(1,40000), _count):
          x = r/200      # col
          y = r - x*200  # row
          radius = randrange(average_radius/5,average_radius) #random diameter for the thermal
          #randomize thermal strength weighted towards stronger
          strength = choice((3,4,5,6,6,7,7,7,8,8,9,9,10)) * _strength * .1
          lat = _lat + (x -100) * .001   # min thermal separation = 1km
          lon = _lon + (y -100) * .001   # max distance =  100x100 km 
          
          #No thermals start over water..
          if world.terrain_is_water(lat, lon):
              continue

          #(lat,lon):(radius,strength)
          #print "makeRandomThermal",lat,lon,radius,strength
          #thermals[(lat,lon)] = (radius,strength)
          thermals.append(thermal.Thermal(lat, lon, radius, strength))

      return thermals

def MakeCSVThermalMap(_lat,_lon,_strength,_count,_radius) :
      ''' Create xx random thermals around the hotspot lat/lon point 
        us parameters average strength
        Params: center (lat,lon) , max strength, count , radius 
        thermal_list =     { (lat,lon):(radius,strength) }
      '''
      #csv_list = world.hotspots
      hotspots = world.hotspots
      #print csv_list
      #hotspots = [(36.7913278, -119.3000250,255,70),(36.7845528, -119.3029139,275, 20),(36.7974417, -119.2900083,435, 100)]
      #print hotspots
      average_radius = _radius
      thermals = []
      print  _strength
      if _count < len(hotspots):
        count = _count 
      else:
        count =len(hotspots)

      for select_spot in sample(xrange(0,len(hotspots)),count):

          r =  randrange(1,40000)
          prob_test = random.random()*100/2
          # probabilty test has to be random.random()*100 , but we need would need more thermal hotspots then
          hotspot_prob = hotspots[select_spot][3]
          if hotspot_prob > prob_test:
            hotspot_lat = hotspots[select_spot][0]
            hotspot_lon = hotspots[select_spot][1]
            x = r/200      # col
            y = r - x*200  # row
            radius = randrange(average_radius/5,average_radius) #random diameter for the thermal
            #randomize thermal strength weighted towards stronger
            strength = choice((4,5,5,6,6,7,7,7,8,8,9,9,10)) * _strength * .1
            lat = hotspot_lat + (x -100) * .00001   # min thermal separation = 100m
            lon = hotspot_lon + (y -100) * .00001   # max distance =  100x100 100m
                      
            #No thermals start over water..
            if world.terrain_is_water(lat, lon):
              continue

            #(lat,lon):(radius,strength)
            #print "makeRandomThermal",lat,lon,radius,strength
            #thermals[(lat,lon)] = (radius,strength)
            thermals.append(thermal.Thermal(lat, lon, radius, strength))

      return thermals


# ----- begin test code --------

#print CalcThermal(-12.389,-76.7582,1000,0,45)