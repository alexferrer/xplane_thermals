""" For developers:
    This is a program to show the thermal map as a plot of points with size and strength (color)
    you need the libraries below :
    pip install numby matplotlib
"""
import numpy as np
import matplotlib.pyplot as plt
import world
from thermal_model import make_random_thermal_map

world.DEBUG = True


def make_test_random_thermal_map():
    """docstring"""
    lat = 52.52
    lon = 13.37
    strength = 10
    count = 100
    radius = 190

    thermals = make_random_thermal_map(1, lat, lon, strength, count, radius)
    return thermals

# funcion to save on a file


def save_thermal(thermal_map):
    """docstring"""
    _f = open('thermals.csv', "w")
    _f.write("x,y"+"\n")
    for _t in thermal_map:
        _f.write(str(int(_t.p_x))+","+str(int(_t.p_y))+"\n")
    _f.close()

# convert to np array


def thermal_to_np_array(thermal_map):
    """docstring"""
    _x = []
    _y = []
    _s = []
    _c = []
    for _t in thermal_map:
        _x.append(int(_t.p_x))
        _y.append(int(_t.p_y))
        _s.append(int(_t.radius))  # thermal radius
        _c.append(int(_t.strength))  # thermal strength as a color
        print(f"T={_t.strength}")

    return _x, _y, _s, _c


N = 50
colors = np.random.rand(N)
# area = np.pi * (15 * np.random.rand(N))**2  # 0 to 15 point radii
#save_thermal( makeRandomThermalMap() )
#data = np.loadtxt('thermals.csv', delimiter = ',', skiprows = 1)
x, y, area, color = thermal_to_np_array(make_test_random_thermal_map())

plt.scatter(x, y, s=area, c=color, alpha=0.5)
plt.show()
