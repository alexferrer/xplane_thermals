#thermal model generator library.
''' Thermal generator module
      for now just generate a spiral lift pattern of decreasing
      strenght on a 2D (Lat,Lon) matrix.
'''

'''
this block only if you have pylab

from pylab import *
def show_thermal(model):
    #show the thermal as image
    figure(1)              
    imshow(model, interpolation='nearest')
    #imshow(model, cmap='hot')
    savefig('thermal_image.png')
    show()
'''

from random import randrange
from math import sqrt


def printa(a):
    print a

def aprint(array):
    print " printing array "
    map(printa,array)
    print"-----------------"


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
    '''' generates coordinates to form a spiral
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
        
#4,16,36,64,100
#2  4  6  8   10

def gen_simple_lift(n,size):
    ''' function to calculate a lift number for the given
        matrix cell n
    '''
    max_lift = 9 
    min_lift = 0
    #reduction of lift for each layer
    spread = (max_lift-min_lift)/(size/2.0)

    #each outward circular layer grows by (2n)^2
    layer = int( sqrt(n)/2)
    
    #simple round decreasing lift from center out
    lift = max_lift - int(layer*spread)
    return lift

def make_thermal(matrix,size,x,y):
    '''
     size = diameter of thermal
     x,y  = center
    '''
    for i in gen_points(size*size):
        x1,y1 = i[1]  #x,y coord
        n = i[0]    # cell #
        #matrix[x+x1][y+y1]= gen_simple_lift(n,size) #simple
        matrix[x+x1][y+y1] += gen_simple_lift(n,size) 


def MakeThermalModel(size,tcount):
    ''' return an array representing an area of SxS
        populated with random thermals'''
    model = new_matrix(size,size)
    
    #populate array with tcount random thermals
    for i in range(tcount):
        diameter = randrange(5,50) #random diameter of thermal
        rad = diameter/2
        # each . = 11m,  between 44m ~ 550mm
        
        #locate thermal randomly, 
        #todo: eventually use terrain as hint
        x,y = randrange(rad,size-rad),randrange(rad,size-rad) #random center far from edge
        make_thermal(model,diameter,x,y)
        print x,y,diameter
        
    #aprint(model)       #for debug only 
    print "thermal model..."
    #show_thermal(model) # us only if pylab availabe
    return model



def CalcThermal(thermal_map,lat,lon,alt,heading):
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
       calculate the roll value by :
       lwing_pos = wingspan * sin(heading)
       rwing_pos = wingspan * cos(heading)
       l_lift = self.CalcThermal(lwing_pos)
       r_lift = self.CalcThermal(rwing_pos)
       rol_val = l_lift - rlift
       tot_lift = l_lift + rlift 
      '''

      #bug: will fail when - sign is not present in lat/lon, later change to abs(lat)
      #     might fail when lon > 99 because of extra digit

      planeX = int(str(lat)[5:8])
      planeY = int(str(lon)[5:8])
         
      lwingX = planeX+1  #need sin/cos
      lwingY = planeY+1
      
      rwingX = planeX-1
      rwingY = planeY-1

      liftL  = thermal_map[ lwingX ][ lwingY ] 
      liftR  = thermal_map[ rwingX ][ rwingY ] 

      thermal_value = liftL + liftR
      roll_value    = liftL - liftR
      
      print "lift > ",str(lat)[5:8]," | ",str(lon)[5:8], thermal_value, roll_value      
      
      return thermal_value , roll_value


# ----- begin test code --------

#b = new_matrix(20,20) #iniitialize matrix of 20x20
 
# make a 10x10 thermal centered at at 10,8
#x,y = 10,8
#make_thermal(b,10,x,y)

b = MakeThermalModel(1000,95) #40x40 area, 3 random termals

c = CalcThermal(b,-12.00123,-76.00123,1000,180)

print "CalcThermal= " , c
#--------- print the array

#aprint(b)



