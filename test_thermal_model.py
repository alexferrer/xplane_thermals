#!/usr/bin/env python2

from world import *
from thermal_model import *

import unittest
import timeit


class ThermalModelTest(unittest.TestCase):

    def assertEqualEpsilon(self, value, expect, epsilon = 0.0001):
        diff = math.fabs(value - expect)
        self.assertTrue(diff <= epsilon, "%f > %f" % (value, expect))

    def testConvertLatLon2Meters(self):
        expect = world.latlon2meter

        pos = convertLatLon2Meters(0, 0)
        self.assertEqual(pos, (0,0))

        # 1deg latitude
        pos = convertLatLon2Meters(1, 0)
        self.assertEqual(pos, (expect, 0))

        pos = convertLatLon2Meters(52, 0)
        self.assertEqual(pos, (expect * 52,0))

        pos = convertLatLon2Meters(-37, 0)
        self.assertEqual(pos, (expect * -37,0))

        # 1deg longitude at the equator
        pos = convertLatLon2Meters(0, 1)
        self.assertEqual(pos, (0,expect))

        # 1deg longitude at 60deg north
        pos = convertLatLon2Meters(60, 1)
        self.assertEqual(pos[0], expect * 60)
        self.assertEqualEpsilon(pos[1], expect / 2.0)

    def _testCalcGeoDist(self, pos1, pos2, expect_distance):
        expect = world.latlon2meter
        dist = calcDist(pos1[0], pos1[1], pos2[0], pos2[1])
        self.assertEqual(dist, expect * expect_distance)

    def testCalcGeoDist(self):
        pos1 = convertLatLon2Meters(0, 0)
        pos2 = convertLatLon2Meters(1, 0)
        self._testCalcGeoDist(pos1, pos2, 1)

        pos1 = convertLatLon2Meters(0, 0)
        pos2 = convertLatLon2Meters(0, 1)
        self._testCalcGeoDist(pos1, pos2, 1)

    def testMakeRandomThermalMap(self):
        lat = 52.52
        lon = 13.37
        strength = 1
        count = 1000
        radius = 10

        thermals = MakeRandomThermalMap(lat,lon,strength,count,radius)
        self.assertEqual(len(thermals), count)

    def _testCalcDrift(self, wind_speed, wind_dir, alt, expected_xy):
        world.wind_speed = wind_speed
        world.wind_dir = math.radians(wind_dir)
        dx, dy = calcDrift(alt)
        self.assertEqualEpsilon(dx, expected_xy[0])
        self.assertEqualEpsilon(dy, expected_xy[1])

    def testCalcDrift(self):
        self._testCalcDrift(1, 0, 2.54, (0,1))
        self._testCalcDrift(1, 90, 2.54, (-1,0))
        self._testCalcDrift(1, 180, 2.54, (0,-1))
        self._testCalcDrift(1, 270, 2.54, (1,0))

    def _testCalcLift(self, pos, expected_lift):
        x,y = convertLatLon2Meters(pos[0], pos[1])
        lift = calcLift(x, y)
        self.assertEqualEpsilon(lift, expected_lift)

    def testCalcLift(self):
        world.thermal_dict = {(52.52,13.37):(2000,30) }
        self._testCalcLift((52.52, 13.37), 30)
        self._testCalcLift((52.515, 13.37), 21.6)
        self._testCalcLift((52.51, 13.37), 12.9)
        self._testCalcLift((52.5, 13.37), 0)


def testPerformance():
    lat = 52.52
    lon = 13.37
    strength = 100
    count = 1000
    radius = 500

    tstart = timeit.default_timer()
    world.thermal_dict = MakeRandomThermalMap(lat,lon,strength,count,radius)
    tend = timeit.default_timer()
    print "MakeRandomThermalMap took %f s" % (tend - tstart)

    tstart = timeit.default_timer()
    for i in xrange(count):
        calcLift(lat, lon)
    tend = timeit.default_timer()
    print "calcLift took %f s" % (tend - tstart)


if __name__ == "__main__":
    testPerformance()

    unittest.main()
