''' Thermal datastructures '''
from thermal_model import convert_lat_lon2meters


class Thermal:
    ''' Define a datastructure to hold thermal infomation'''

    def __init__(self, lat, lon, radius, strength):
        self.set_location(lat, lon)
        self.set_radius(radius)
        self.strength = strength

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
