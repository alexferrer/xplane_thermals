#thermal model generator library.
''' Thermal generator module
      for now just generate a spiral lift pattern of decreasing
      strenght on a 2D (Lat,Lon) matrix.
      
      assorted helper & debug functions
'''

from random import randrange
import math
import csv

#for graphics
#from XPLMDisplay import *
#from XPLMScenery import *
from XPLMGraphics import * 

def printa(a):
    print a

#helper to print the array to the console
def aprint(array):
    print " ************ printing thermal array *********"
    map(printa,array)
    print "-----------------      Done    ----------------"

#helper to save a thermal model as .csv file
def SaveThermalModel(model,filename):
    with open(filename, "wb") as f:
        writer = csv.writer(f)
        writer.writerows(model)
        f.close()

def DrawThermal(lat,lon, wind_speed,wind_dir,thermal_top): #min_alt,max_alt
    ''' make a location list of thermal images along the raising thermal, accounting
        for wind drift along the climb. end at thermal tops
    '''
    base = 1
    Dew,Dud,Dns = XPLMWorldToLocal(lat,lon,0) #Dew=E/W,Dud=Up/Down,Dns=N/S 
    locs = []  #locations 
    for alt in range(base,thermal_top,100): #from 100 to thermal top by 100
        climb_time = alt/2.54           # assuming thermal raises at ~ 500ft/m
        drift = wind_speed * climb_time  
        dY = int(round(math.cos(wind_dir) * drift )) #east/west drift 
        dX = -int(round(math.sin(wind_dir) * drift )) #north/south drift
        locs.append([Dew+dX,Dud+alt,Dns+dY, 0, 0, 0])
    return locs

def DrawThermalMap(thermal_map):
    ''' make a location list for the drawing of all the thermal objects.
        thermal positionns are hiden in cell [0][1] of the matrix.. for now'''
    thermal_top = thermal_map[0][0]
    windvector = thermal_map[0][2]
    windspeed = windvector[0]
    winddir   = math.radians( windvector[1] )
    locations = []
    #for z in thermal_map[0][1] :   #hidden cell with center of thermals..
    #    locations = locations + DrawThermal(z[0],z[1], windspeed, winddir,thermal_top) 

    for lat,lon in thermal_map[0][1] :   #hidden cell with center of thermals..
        locations = locations + DrawThermal(lat,lon, windspeed, winddir,thermal_top) 


    return locations


def new_matrix(rows,cols):
    ''' initialize a matrix of zeros of size row x col''' 
    return [[0 for col in range(cols)] for row in range(rows)]

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

def make_thermal(matrix,size,x,y):
    ''' insert a thermal into the thermal matrix
        size = diameter of thermal
        x,y  = center
        if a lift already exists on [x,y], add new value to it
    '''
    for i in gen_points(size*size):
        x1,y1 = i[1]  # x,y coord
        n = i[0]      # cell number
        matrix[x+x1][y+y1] += gen_simple_lift(n,size) 


def MakeRandomThermalModel(size,tcount,_diameter):
    ''' return an array representing an area of Size x Size
        populated with random thermals
        size     =  size of model (10m each cell) 
        tcount   =  # of thermals
        diameter = largest thermal diameter
        model[0][0] = thermal tops altitude
        '''
    model = new_matrix(size,size)
    
    #populate array with tcount random thermals
    for i in range(tcount):
        diameter = randrange(_diameter/2,_diameter) #random diameter of thermal
        rad = diameter/2
        # each . = 11m,  between 44m ~ 550mm
        
        #locate thermal randomly, 
        #todo: eventually use terrain as hint
        
        #random model:
        x,y = randrange(rad,size-rad),randrange(rad,size-rad) #random center far from edge
        
        make_thermal(model,diameter,x,y)
        
    #aprint(model)       #for debug only 
    
    #insert thermal_top altitude into the model for others to use
    model[0][0] = 1524 # 5000 feet in meters

    return model

def MakeThermalModel(size,tcount,_diameter):
    ''' return an array representing an area of Size x Size
        populated with fixed position thermals
        note: ignore size,tcount,_diameter
    '''
    size = 10000 #increased play area to 70nm
    model = new_matrix(size,size)
    
    #Todo: read this thermals from a user .cvs file  lat,long, diameter,max lift
    
    #populate array with fixed thermals
    #make thermal size,lat,lon .. needs max power,
    make_thermal(model,100,3890,7581) #Libmandi
    make_thermal(model,50,3994,7666) #SantaMaria
    make_thermal(model,150,3774,7815) #Intersection san bartolo
    make_thermal(model,300,3016,8448) #Interseccion senoritas
    make_thermal(model,350,4647,7516) #trebol de chilca
    make_thermal(model,500,7623,6061) #vor asia
    #ask21 turn diameter at 60mph = 133m, 80mph = 420m

    #nasty hack.. because i am lazy..       
    #insert thermal_top altitude into the model for others to use
    model[0][0] = 1524 # 5000 feet in meters
    #insert the thermal centers into cell 0,1
    model[0][1]  = [[-12.3890,-76.7581],[-12.3994,-76.7666],[-12.3774,-76.7815],[-12.3016,-76.8448],[-12.4647,-76.7516],[-12.7623,-76.6061]]
    #insert wind
    model[0][2] = [0,0] # wind 0 from north

    return model

def ReadThermalModel(filename):
    ''' read a thermal model from an external .cvs file
        previously populated with thermals.
        Note: place the file on the Xplane root directory
    '''
    size = 1000
    model = new_matrix(size,size)
    
    print "reading thermal model ... "
    with open(filename, "r") as f:
        model = list(map(int,rec) for rec in csv.reader(f, delimiter=',')) 

    return model


def CalcThermal(thermal_map,lat,lon,alt,heading,roll_angle):
      '''
       Calculate the strenght of the thermal at this particular point 
       in space by using the x digits of lat/lon as index on a 
       2dimensional array representing space (lat,lon) 
       the value representing lift/sink (+/-) 
       b = [ [[11,12],[13,14]] , [[21,22],[23,24]] ]
       
       for lat/lon, 12.3456789
         .1     = 11,120 meters
         .01    =  1,120 m
         .001   =    120 m
         .0001  =     11 m
         .00001 =      1 m
         
       a matrix of [100,100] on a .0001 (11m resolution) represents 1.1km^2
       use 2nd,3rd,4rd decimal of the lat/lon nn.x123 (blocks of 11 meters) as the key
       on a [1000x1000] matrix = 10km^2 that repeats every 11km as the .1 digit changes
       
      '''       

      '''
       calculate the total lift and roll value :
      '''
      # current plane position  
      # use 2,3,4 decimals ex: -12.34567 should return : 3456
      #     equivalent to 10 x 1120 m2 with a cell resolution of 11m2
      planeX   = int(str(abs(lat-int(lat)))[2:6]) #test: increase area 10x by adding 1 digit [3:6]
      planeY   = int(str(abs(lon-int(lon)))[2:6])

      # winddrift: as the thermal climbs, it is pushed by the prevailing winds
      #    to account for the drift of the thermal add (wind vector * time to reach altitude) 
      #    to plane, 
      windvector = thermal_map[0][2]
      wind_speed = windvector[0]
      wind_dir   = math.radians( windvector[1] )

      #wind_speed = 5  # 5 m/s = 11 mph
      #wind_dir   = math.radians(270)  # wind comming from the west
      climb_time = alt/2.54           # assuming thermal raises at ~ 500ft/m
      drift = wind_speed * climb_time / 11 # 11 meters per matrix cell
      planeX = planeX - int(round(math.cos(wind_dir) * drift ))
      planeY = planeY - int(round(math.sin(wind_dir) * drift ))
      
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

      #Thermal Top: gradually reduce thermal strength when alt is getting close to thermal tops
      thermal_top = thermal_map[0][0]  # altitude in meters! from thermal model[0][0] 

      top_factor = 1
      if (thermal_top - alt) < 100:
          top_factor = (thermal_top - alt)/100


	  # lift for each area, left tip, right tip and middle.
      liftL  = thermal_map[ lwingX ][ lwingY ] * top_factor
      liftR  = thermal_map[ rwingX ][ rwingY ] * top_factor
      liftM  = thermal_map[ planeX ][ planeY ] * top_factor

      # total lift component
      thermal_value = liftL + liftR + liftM
      
      # total roll component 
      #         the more airplane is rolled, the less thermal roll effect
      #         if the plane is flying inverted the roll effect should be reversed
      roll_factor = math.cos(math.radians(roll_angle))
      roll_value    = (liftR - liftL) * roll_factor
      
      # for debug
      #print "pos[",planeX,",",planeY,"] @",'%.0f'%(heading), \
      #      ">",'%.1f'%(roll_angle), "T **[",'%.1f'%thermal_value,"|", '%.1f'%roll_value ,"]**",'%.1f'%alt
      
      #todo: thermals have cycles, begin, middle , end.. and reflect in strength.. 
      
      return thermal_value , roll_value


# ----- begin test code --------
'''
print 'test: make a thermal model size (1000x1000) with 10 random termals of avg diameter 200'
model  = MakeThermalModel(1000,20,200) 

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

