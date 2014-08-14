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

# helpers to save/read a thermal model as .csv file
def SaveThermalModel(model,filename):
    with open(filename, "wb") as f:
        writer = csv.writer(f)
        writer.writerows(model)
        f.close()

def ReadThermalModel(filename):
    ''' read a thermal model from an external .cvs file
        previously populated with thermals.
        Note: place the file on the Xplane root directory
    '''
    model = world.thermal_map
    print "reading thermal model ... "
    with open(filename, "r") as f:
        model = list(map(int,rec) for rec in csv.reader(f, delimiter=',')) 
    return model


def DrawThermal(lat,lon): #min_alt,max_alt
    ''' make a location list of thermal images along the raising thermal, accounting
        for wind drift along the climb. end at thermal tops
    '''
    base = 1
    Dew,Dud,Dns = XPLMWorldToLocal(lat,lon,0) #Dew=E/W,Dud=Up/Down,Dns=N/S 
    locs = []  #locations 
    for alt in range(base,world.thermal_tops,200): #from 100 to thermal top steps of  150
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

'''------- stuf tow populate thermals ---------------'''

def left(x,y):
    return x,y+1

def down(x,y):
    return x+1,y

def move_right(x,y):
    return x+1, y

def move_down(x,y):
    return x,y-1

def move_left(x,y):
    return x-1,y

def move_up(x,y):
    return x,y+1

moves = [move_right, move_down, move_left, move_up]

def gen_points(end):
    '''' generator: generates coordinates to form a spiral
         of sequential numbers '''

    from itertools import cycle
    _moves = cycle(moves)
    n = 1
    pos = 0,0
    times_to_move = 1

    yield n,pos

    while True:
        for _ in range(2):
            move = next(_moves)
            for _ in range(times_to_move):
                if n >= end:
                    return
                pos = move(*pos)
                n+=1
                yield n,pos

        times_to_move+=1
        

def gen_simple_lift(n,size):
    ''' function to calculate a lift number for the given
        matrix cell n
    '''
    max_lift = 9 
    min_lift = 0
    #reduction of lift for each layer
    spread = (max_lift-min_lift)/(size/2.0)

    #each outward circular layer grows by (2n)^2
    layer = int( math.sqrt(n)/2)
    
    #simple round decreasing lift from the center to the outmost layer
    lift = max_lift - int(layer*spread)
    return lift


def make_thermal(matrix,size,lat,lon):
    ''' insert a thermal into the thermal matrix
        size = diameter of thermal
        x,y  = center
        if a lift already exists on [x,y], add new value to it
    '''
    x   = int(abs(lat-int(lat))*10000) 
    y   = int(abs(lon-int(lon))*10000)
    print "make_thermal",lat,lon,x,y
    for i in gen_points(size*size):
        x1,y1 = i[1]  # x,y coord
        n = i[0]      # cell number
        matrix[x+x1][y+y1] += gen_simple_lift(n,size) 


def MakeRandomThermalModel(tcount,_diameter):
    ''' return an array representing an area of Size x Size
        populated with random thermals
        tcount   =  # of thermals
        diameter = largest thermal diameter
        model[0][0] = thermal tops altitude
        '''
     #start with a thermal map from scratch
    model = [[0 for col in range(world.map_size)] for row in range(world.map_size)] 
    tlist = []

    radius = _diameter/2 
    #get randomly distributed x,y positions
    count = 1
    for r in sample(xrange(1,10000), 2000):
    
        x = r/100
        y = r - x*100
    
        x=x*100
        y=y*100
        diameter = randrange(_diameter/2,_diameter) #random diameter of thermal
        #if number+/- radius out of bounds, skip
        if x < radius or x > (9900 - diameter) :
           #print x,y,"out of bound x"
           continue
       
        if y < radius or y > (9900 - diameter) :
           #print x,y,"out of bound y"
           continue
        #print "number",x,y
        #account for lat/lon negatives
        if world.lat_origin < 0:
           x = -1 * x
        if world.lon_origin < 0:
           y = -1 * y
           
        lat = world.lat_origin + (x * .0001 )
        lon = world.lon_origin + (y * .0001 )
        
        
        make_thermal(model,diameter,lat,lon)
        tlist.append([lat,lon,diameter])
        #stop if we build enough thermals
        count +=1
        if count > tcount:
           break
           
    world.thermal_list  = tlist
    print  "wtllist",world.thermal_list
    return model

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


def CalcThermal(lat,lon,alt,heading,roll_angle):
      '''
       Calculate the strenght of the thermal at this particular point 
       in space by using the decimal digits of lat/lon as index on a 
       2dimensional array representing space (lat,lon) 
       the value representing lift/sink (+/-) 
       
       for lat/lon, 12.3456789
         .1     = 11,120 meters
         .01    =  1,120 m
         .001   =    120 m
         .0001  =     11 m
         .00001 =      1 m
         
       a matrix of [10000,10000] on a .0001 (11m resolution) represents 1.1km^2
       use 2nd,3rd,4rd decimal of the lat/lon nn.x123 (blocks of 11 meters) as the key
       on a [1000x1000] matrix = 10km^2 that repeats every 11km as the . digit changes
       
      '''       

      '''
       calculate the total lift and roll value :
      '''
      # current plane position  
      # use 2,3,4 decimals ex: -12.34567 should return : 3456
      #     equivalent to 10 x 1120 m2 with a cell resolution of 11m2
      planeX   = int(abs(lat-int(lat))*10000) #test: increase area 10x by adding 1 digit [3:6]
      planeY   = int(abs(lon-int(lon))*10000)

      # winddrift: as the thermal climbs, it is pushed by the prevailing winds
      #    to account for the drift of the thermal add (wind vector * time to reach altitude) 
      #    to plane, 

      climb_time = alt/2.54           # assuming thermal raises at ~ 500ft/m
      drift = world.wind_speed * climb_time / 11 # drift in cells at 11meters per cell.. 
      planeX = planeX - int(round(math.cos(world.wind_dir) * drift ))
      planeY = planeY - int(round(math.sin(world.wind_dir) * drift ))
      
      # left and right wings position from current plane heading
      angleL   = math.radians(heading-90)
      angleR   = math.radians(heading+90)

      wingspan = 2  #need to check this, 7 meters or 7 clicks of lat long? (70 meters)
      
      # left wing tip coordinates
      lwingX = planeX + int(round(math.cos(angleL)*wingspan))
      lwingY = planeY + int(round(math.sin(angleL)*wingspan))

      # rigth wing tip coordinates
      rwingX = planeX + int(round(math.cos(angleR)*wingspan))
      rwingY = planeY + int(round(math.sin(angleR)*wingspan))

      #Thermal Top: gradually reduce thermal strength when alt is getting close to 10% of thermal tops
      top_factor = 1
      if (world.thermal_tops - alt) < 100:
          top_factor = ( world.thermal_tops - alt)/100

	  # lift for each area, left tip, right tip and middle.
      liftL  = world.thermal_map[ lwingX ][ lwingY ] * top_factor
      liftR  = world.thermal_map[ rwingX ][ rwingY ] * top_factor
      liftM  = world.thermal_map[ planeX ][ planeY ] * top_factor

      # total lift component
      thermal_value = liftL + liftR + liftM
      
      # total roll component 
      #         the more airplane is rolled, the less thermal roll effect
      #         if the plane is flying inverted the roll effect should be reversed
      roll_factor = math.cos(math.radians(roll_angle))
      roll_value    = (liftR - liftL) * roll_factor
      
      # for debug
      #print "pos[",planeX,",",planeY,"] @",'%.0f'%(heading), \
      #     ">",'%.1f'%(roll_angle), "T **[",'%.1f'%thermal_value,"|", '%.1f'%roll_value ,"]**",'%.1f'%alt,world.thermal_map[ planeX ][ planeY ]
      
      #todo: thermals have cycles, begin, middle , end.. and reflect in strength.. 
      
      return thermal_value , roll_value


# ----- begin test code --------
'''
***Warning**** Tests are out of sync... 

print 'test: make a thermal with 10 random termals of avg diameter 200'
model  = MakeThermalModel(20,200) 

print 'test: make a random thermal model'
random_model = MakeRandomThermalModel(1000,20,200)

print 'test: make a 10x10 thermal centered at at 10,8'
x,y = 10,8
make_thermal(model,10,x,y)

print 'test: CalcThermal reading thermal values '
for i in range(10):
    c = CalcThermal(model,-12.00001 - i*.0001,-76.00001,1000,45)
print "CalcThermal= " , c

print 'test: print the model'
aprint(random_model)

print 'test: save the thermal model'
SaveThermalModel(model,'test_columns_thermal.csv')

print 'test: All tests completed !  '
'''

