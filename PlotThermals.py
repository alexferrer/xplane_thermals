"""
Program to show the thermal map as a plot of points with size and strength (color)
pip install  numby matplotlib
"""
import numpy as np
import matplotlib.pyplot as plt
from world import *
from thermal_model import *

world.DEBUG = True
def makeRandomThermalMap():
    lat = 52.52
    lon = 13.37
    strength = 5
    count = 100
    radius = 90
     
    thermals = MakeRandomThermalMap(1, lat, lon, strength, count, radius)
    return thermals

#funcion to save on a file 
def save_thermal(thermal_map):
    f = open('thermals.csv', "w")
    f.write("x,y"+"\n")
    for t in thermal_map:
        f.write(str(int(t.px))+","+str(int(t.py))+"\n")
    f.close()

#convert to np array 
def thermal_to_np_array(thermal_map):
    x = []
    y = []
    s = []
    c = []
    for t in thermal_map:
        x.append( int(t.px) ) 
        y.append( int(t.py) )
        s.append( int(t.radius) )   #thermal radius 
        c.append( int(t.strength) ) #thermal strength as a color

    return x,y,s,c

N = 50
colors = np.random.rand(N)
#area = np.pi * (15 * np.random.rand(N))**2  # 0 to 15 point radii
#save_thermal( makeRandomThermalMap() )
#data = np.loadtxt('thermals.csv', delimiter = ',', skiprows = 1) 
x,y,area,color = thermal_to_np_array( makeRandomThermalMap() )

plt.scatter(x, y,s=area,c=color, alpha=0.5)
plt.show()