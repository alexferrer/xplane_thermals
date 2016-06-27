#!/usr/bin/env python2

from world import *
from thermal_model import *

import unittest


class ThermalModelTest(unittest.TestCase):

    def testConvertLatLon2Meters(self):
        pos = convertLatLon2Meters(0, 0)
        self.assertEqual(pos[0], 0.0)
        self.assertEqual(pos[1], 0.0)

        expect = world.latlon2meter # Not 1851 * 60?

        # 1deg latitude
        pos = convertLatLon2Meters(1, 0)
        self.assertEqual(pos[0], expect)
        self.assertEqual(pos[1], 0.0)

        pos = convertLatLon2Meters(52, 0)
        self.assertEqual(pos[0], expect * 52)
        self.assertEqual(pos[1], 0.0)

        pos = convertLatLon2Meters(-37, 0)
        self.assertEqual(pos[0], expect * -37)
        self.assertEqual(pos[1], 0.0)

        # 1deg longitude at the equator
        pos = convertLatLon2Meters(0, 1)
        self.assertEqual(pos[0], 0.0)
        self.assertEqual(pos[1], expect)

        # 1deg longitude at 60deg north
        pos = convertLatLon2Meters(60, 1)
        self.assertEqual(pos[0], expect * 60)

        diff = math.fabs(pos[1] - (expect / 2.0))
        self.assertTrue(diff < 0.01)

    def testCalcGeoDist(self):
        pos1 = convertLatLon2Meters(0, 0)
        pos2 = convertLatLon2Meters(1, 0)

    def testMakeRandomThermalMap(self):
        lat = 52.52
        lon = 13.37
        strength = 1
        count = 10
        radius = 10

        thermals = MakeRandomThermalMap(lat,lon,strength,count,radius)
        self.assertEqual(len(thermals), count)


if __name__ == "__main__":
    unittest.main()
