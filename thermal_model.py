#thermal model generator library.
''' Thermal generator module
      for now just generate a spiral lift pattern of decreasing
      strenght on a 2D (Lat,Lon) matrix.
'''


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

from math import sqrt
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
        matrix[x+x1][y+y1]= gen_simple_lift(n,size)

from random import randrange
def make_thermal_model(size,tcount):
    ''' return an array representing an area of SxS
        populated with random thermals'''
    model = new_matrix(size,size)
    
    #populate array with tcount random thermals
    for i in range(tcount):
        diameter = randrange(2,10) #random diameter between 2 ~ 10
        x,y = randrange(5,size-5),randrange(5,size-5) #random center far from edge
        make_thermal(model,10,x,y)
        print x,y,diameter
         
    return model


# ----- begin test code --------

b = new_matrix(20,20) #iniitialize matrix of 20x20
 
# make a 10x10 thermal centered at at 10,8
x,y = 10,8
make_thermal(b,10,x,y)

b = make_thermal_model(40,3) #40x40 area, 3 random termals

#--------- print the array

aprint(b)



