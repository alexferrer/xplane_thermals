#!/usr/bin/env python2

from thermal_model import convertLatLon2Meters

class Thermal:

    def __init__(self, lat, lon, radius, strength):
        self.set_location(lat, lon)
        self.set_radius(radius)
        self.strength = strength

    def set_location(self, lat, lon):
        self.lat = lat
        self.lon = lon
        self.alt = 0
        self.px, self.py = convertLatLon2Meters(lat, lon)

    def set_radius(self, radius):
        self.radius = radius
        self.radius_square = radius * radius
