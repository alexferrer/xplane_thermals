''' Thermal datastructures '''
from thermal_model import convert_lat_lon2meters


class Thermal:
    ''' Define a datastructure to hold thermal infomation'''

    def __init__(self, lat, lon, radius, strength):
        self.set_location(lat, lon)    # location of the base of the thermal at ground
        self.set_radius(radius)        # radius of the thermal in meters
        self.strength = strength       # strength of the thermal in meters/second lift

    def set_location(self, lat, lon):
        ''' store location of the thermal '''
        self.lat = lat
        self.lon = lon
        self.alt = 0
        self.p_x, self.p_y = convert_lat_lon2meters(lat, lon)

    def set_radius(self, radius):
        ''' store radius of the thermal '''
        self.radius = radius
        self.radius_square = radius * radius

    def __str__(self):
        return f"Thermal at {self.lat},{self.lon} radius={self.radius} strength={self.strength}"