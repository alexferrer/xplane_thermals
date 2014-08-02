#thermal model generator library.
''' Thermal generator module
      for now just generate a spiral lift pattern of decreasing
      strenght on a 2D (Lat,Lon) matrix.
      
      assorted helper & debug functions
'''

from random import randrange
import math
import csv


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
    return model

def MakeThermalModel(size,tcount,_diameter):
    ''' return an array representing an area of Size x Size
        populated with fixed position thermals
        note: ignore size,tcount,_diameter
    '''
    size = 10000 #increased size to 70nm
    model = new_matrix(size,size)
    
    #populate array with fixed thermals
    make_thermal(model,100,3890,7581) #Libmandi
    make_thermal(model,50,3994,7666) #SantaMaria
    make_thermal(model,150,3774,7815) #Intersection san bartolo
    make_thermal(model,300,3016,8448) #Interseccion senoritas
    make_thermal(model,350,4647,7516) #trebol de chilca
    make_thermal(model,500,7623,6061) #vor asia
        
    '''
    for i in range(0,999):         #for testing use fixed thermal pattern  | 1 |  3  | 0  |  0|
        for n in range(0,9):
            for p in range(0,30):     
                model[i][n*100+p] = 1
                model[i][n*100+31+p] = 3
    '''            
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

      #bug: will fail when - sign is not present in lat/lon, later change to abs(lat)
      #     might fail when lon > 99 because of extra digit
      # Todo: should substract initial lat/long, to center the covered area and 
      #       solve the problems that - and 3 digit lat/longs create.

      '''
       calculate the total lift and roll value :
      '''
      # current plane position  
      # use 2,3,4 decimals ex: -12.34567 should return : 456
      #     equivalent to 10 x 1120 m2 with a cell resolution of 11m2
      planeX   = int(str(abs(lat-int(lat)))[2:6]) #test: increase area 10x by adding 1 digit [3:6]
      planeY   = int(str(abs(lon-int(lon)))[2:6])
      # left and right wings position from current plane heading
      angleL   = math.radians(heading-90)
      angleR   = math.radians(heading+90)

      wingspan = 7
      
      # left wing tip coordinates
      lwingX = planeX + int(round(math.cos(angleL)*wingspan))
      lwingY = planeY + int(round(math.sin(angleL)*wingspan))

      # rigth wing tip coordinates
      rwingX = planeX + int(round(math.cos(angleR)*wingspan))
      rwingY = planeY + int(round(math.sin(angleR)*wingspan))

	  # lift for each area, left tip, right tip and middle.
      liftL  = thermal_map[ lwingX ][ lwingY ] 
      liftR  = thermal_map[ rwingX ][ rwingY ] 
      liftM  = thermal_map[ planeX ][ planeY ] 

      # total lift component
      thermal_value = liftL + liftR + liftM
      
      # total roll component 
      #         the more airplane is rolled, the less thermal roll effect
      #         if the plane is flying inverted the roll effect should be reversed
      roll_factor = math.cos(math.radians(roll_angle))
      roll_value    = (liftR - liftL) * roll_factor
      
      # for debug
      print "pos[",planeX,",",planeY,"] @",'%.0f'%(heading), \
            ">",'%.1f'%(roll_angle), "T **[",thermal_value,"|", '%.1f'%roll_value ,"]**"
      
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
