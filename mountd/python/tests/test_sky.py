"""Sky maths against published values: Meeus, Astronomical Algorithms (2nd ed.), examples 7.a, 12.a, 12.b."""
import unittest
from datetime import datetime, timedelta, timezone

from mountd.sky import (GEAR_28BYJ, HALF_STEPS_PER_TURN, SIDEREAL_DAY, SIDEREAL_HALF_STEP,
                        degrees_to_steps, gmst, hour_angle, julian_date, lst, ra_at, steps_to_degrees)

UTC = timezone.utc
SECOND = 1 / 3600                                    # one second of time, in hours


class JulianDate(unittest.TestCase):
    def test_j2000(self):
        self.assertEqual(julian_date(datetime(2000, 1, 1, 12, tzinfo=UTC)), 2451545.0)

    def test_sputnik(self):
        # Meeus 7.a: 1957 October 4.81 → JD 2436116.31
        t = datetime(1957, 10, 4, tzinfo=UTC) + timedelta(days=0.81)
        self.assertAlmostEqual(julian_date(t), 2436116.31, places=6)

    def test_local_time_is_converted(self):
        oslo = timezone(timedelta(hours=2))
        self.assertEqual(julian_date(datetime(2000, 1, 1, 14, tzinfo=oslo)), 2451545.0)

    def test_naive_time_is_refused(self):
        # A time with no zone is a guess about the zone; the Pi's clock zone must not leak in
        with self.assertRaises(ValueError):
            julian_date(datetime(2000, 1, 1, 12))


class SiderealTime(unittest.TestCase):
    def test_gmst_at_midnight(self):
        # Meeus 12.a: 1987 April 10, 0h UT → 13h10m46.3668s
        self.assertAlmostEqual(gmst(datetime(1987, 4, 10, tzinfo=UTC)),
                               13 + 10 / 60 + 46.3668 / 3600, delta=0.001 * SECOND)

    def test_gmst_in_the_evening(self):
        # Meeus 12.b: 1987 April 10, 19h21m00s UT → 8h34m57.0896s
        self.assertAlmostEqual(gmst(datetime(1987, 4, 10, 19, 21, tzinfo=UTC)),
                               8 + 34 / 60 + 57.0896 / 3600, delta=0.001 * SECOND)

    def test_lst_adds_east_longitude(self):
        t = datetime(1987, 4, 10, 19, 21, tzinfo=UTC)
        self.assertAlmostEqual(lst(t, 15.0), gmst(t) + 1)    # 15° east = one hour later

    def test_lst_west_longitude_wraps(self):
        t = datetime(1987, 4, 10, tzinfo=UTC)                 # GMST 13.18 h
        self.assertAlmostEqual(lst(t, -210.0), gmst(t) - 14 + 24)

    def test_the_sky_turns_once_per_sidereal_day(self):
        t = datetime(2026, 10, 25, 21, tzinfo=UTC)
        later = t + timedelta(seconds=SIDEREAL_DAY)
        self.assertAlmostEqual(gmst(later), gmst(t), delta=0.01 * SECOND)


class HourAngle(unittest.TestCase):
    def test_on_the_meridian(self):
        self.assertEqual(hour_angle(ra=5.5, lst=5.5), 0)

    def test_west_of_the_meridian_is_positive(self):
        # The star crossed an hour ago: it is setting
        self.assertAlmostEqual(hour_angle(ra=4.5, lst=5.5), 1)

    def test_wraps_across_0h(self):
        # M31 (RA 0h43m) with LST 23h00m: 1h43m east, not 22h17m west
        self.assertAlmostEqual(hour_angle(ra=0 + 43 / 60, lst=23.0), -(1 + 43 / 60))

    def test_range_is_minus_12_to_12(self):
        self.assertEqual(hour_angle(ra=0, lst=12), -12)

    def test_ra_at_is_the_inverse(self):
        for ha in (-11.5, -1, 0, 3.25, 11.9):
            self.assertAlmostEqual(hour_angle(ra_at(ha, lst=2.0), lst=2.0), ha)


class Gear(unittest.TestCase):
    def test_28byj48_ratio_is_not_64(self):
        # (32·22·26·31) / (11·9·10·9), the tooth counts of its four stages
        self.assertAlmostEqual(GEAR_28BYJ, 63.68395, places=5)

    def test_half_steps_per_axis_turn(self):
        # 64 half-steps per motor turn × gearbox × the printed 5:1 stage; the README's 20 380
        self.assertAlmostEqual(HALF_STEPS_PER_TURN, 20378.9, places=1)

    def test_sidereal_rate_is_one_half_step_every_4_23_s(self):
        self.assertAlmostEqual(SIDEREAL_HALF_STEP, 4.228, places=3)

    def test_steps_round_trip(self):
        self.assertEqual(degrees_to_steps(360), round(HALF_STEPS_PER_TURN))
        self.assertAlmostEqual(steps_to_degrees(degrees_to_steps(90)), 90, delta=steps_to_degrees(1))

    def test_negative_angles_step_backwards(self):
        self.assertEqual(degrees_to_steps(-90), -degrees_to_steps(90))

    def test_assuming_64_drifts(self):
        # Why the exact ratio matters: step timing worked out for 64:1 turns the axis 0.5 % too fast,
        # 0.75° ahead of the sky after 10 h of tracking (about 34 px)
        night = 10 * 3600
        steps = night / (SIDEREAL_DAY / (64 * 64 * 5))
        axis = steps_to_degrees(steps)
        sky = night / SIDEREAL_DAY * 360
        self.assertAlmostEqual(axis - sky, 0.75, delta=0.005)


if __name__ == "__main__":
    unittest.main()
