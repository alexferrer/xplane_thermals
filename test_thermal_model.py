"""Test the thermal model """
import unittest
import timeit
import math
import world
from thermal import Thermal
from thermal_model import convert_lat_lon2meters, calc_lift, calc_drift, make_random_thermal_map, calc_dist


class ThermalModelTest(unittest.TestCase):
    """ Test the thermal model """

    def assert_equal_epsilon(self, value, expect, epsilon=0.0001):
        """docstring"""
        diff = math.fabs(value - expect)
        self.assertTrue(diff <= epsilon, "%f > %f" % (value, expect))

    def test_convert_lat_lon2meters(self):
        """docstring"""
        expect = world.latlon2meter

        pos = convert_lat_lon2meters(0, 0)
        self.assertEqual(pos, (0, 0))

        # 1deg latitude
        pos = convert_lat_lon2meters(1, 0)
        self.assertEqual(pos, (expect, 0))

        pos = convert_lat_lon2meters(52, 0)
        self.assertEqual(pos, (expect * 52, 0))

        pos = convert_lat_lon2meters(-37, 0)
        self.assertEqual(pos, (expect * -37, 0))

        # 1deg longitude at the equator
        pos = convert_lat_lon2meters(0, 1)
        self.assertEqual(pos, (0, expect))

        # 1deg longitude at 60deg north
        pos = convert_lat_lon2meters(60, 1)
        self.assertEqual(pos[0], expect * 60)
        self.assert_equal_epsilon(pos[1], expect / 2.0)

    def _calc_geo_dist(self, pos1, pos2, expect_distance):
        """docstring"""
        expect = world.latlon2meter
        dist = calc_dist(pos1[0], pos1[1], pos2[0], pos2[1])
        self.assertEqual(dist, expect * expect_distance)

    def test_calc_geo_dist(self):
        """docstring"""
        pos1 = convert_lat_lon2meters(0, 0)
        pos2 = convert_lat_lon2meters(1, 0)
        self._calc_geo_dist(pos1, pos2, 1)

        pos1 = convert_lat_lon2meters(0, 0)
        pos2 = convert_lat_lon2meters(0, 1)
        self._calc_geo_dist(pos1, pos2, 1)

    def test_make_a_thermal_map(self):
        """docstring"""
        lat = 52.52
        lon = 13.37
        strength = 1
        count = 1000
        radius = 10

        thermals = make_random_thermal_map(
            1, lat, lon, strength, count, radius)
        self.assertEqual(len(thermals), count)

    def _calc_drift(self, wind_speed, wind_dir, alt, expected_xy):
        """docstring"""
        world.wind_speed = wind_speed
        world.wind_dir = math.radians(wind_dir)
        dx, dy = calc_drift(alt)
        self.assert_equal_epsilon(dx, expected_xy[0])
        self.assert_equal_epsilon(dy, expected_xy[1])

    def test_calc_drift(self):
        """docstring"""
        self._calc_drift(1, 0, 2.54, (0, 1))
        self._calc_drift(1, 90, 2.54, (-1, 0))
        self._calc_drift(1, 180, 2.54, (0, -1))
        self._calc_drift(1, 270, 2.54, (1, 0))

    def _calc_lift(self, pos, expected_lift):
        """docstring"""
        _x, _y = convert_lat_lon2meters(pos[0], pos[1])
        lift = calc_lift(_x, _y)
        self.assert_equal_epsilon(lift, expected_lift)

    def test_calc_lift(self):
        """docstring"""
        world.thermal_dict = [Thermal(52.52, 13.37, 2000, 30)]
        self._calc_lift((52.52, 13.37), 30)
        self._calc_lift((52.515, 13.37), 21.6)
        self._calc_lift((52.51, 13.37), 12.9)
        self._calc_lift((52.5, 13.37), 0)


def test_performance():
    """docstring"""
    lat = 52.52
    lon = 13.37
    strength = 100
    count = 1000
    radius = 500

    tstart = timeit.default_timer()
    world.thermal_dict = make_random_thermal_map(
        1, lat, lon, strength, count, radius)
    tend = timeit.default_timer()
    print(f"MakeRandomThermalMap took {(tend - tstart)} s.")

    tstart = timeit.default_timer()
    for _i in range(count):
        calc_lift(lat, lon)

    tend = timeit.default_timer()
    print(f"calcLift took {(tend - tstart)} s.")


if __name__ == "__main__":
    test_performance()

    unittest.main()
