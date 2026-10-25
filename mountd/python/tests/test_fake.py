"""The fake mount's motion against a fake clock: manual moves, rates, stops, park."""
import unittest

from mountd.fake import RATES, FakeMount


class Clock:
    """Time that only moves when a test says so."""
    def __init__(self, t=0.0):
        self.t = t

    def __call__(self):
        return self.t


class FakeMotion(unittest.TestCase):
    def setUp(self):
        self.clock = Clock()
        self.mount = FakeMount(ra=6.0, dec=0.0, clock=self.clock)

    def after(self, seconds):
        self.clock.t += seconds
        return self.mount.position()

    def test_north_at_guide_rate(self):
        self.mount.set_rate("guide")
        self.mount.move("dec", +1)
        ra, dec = self.after(60)
        self.assertAlmostEqual(dec, 0.25)                        # 15″/s for a minute = 900″
        self.assertEqual(ra, 6.0)

    def test_east_raises_ra_west_lowers_it(self):
        self.mount.set_rate("find")
        self.mount.move("ra", +1)
        self.assertAlmostEqual(self.after(15)[0], 7.0)           # 15° = 1 h
        self.mount.move("ra", -1)
        self.assertAlmostEqual(self.after(30)[0], 5.0)

    def test_ra_wraps(self):
        self.mount.set_rate("slew")
        self.mount.move("ra", -1)
        self.assertAlmostEqual(self.after(15)[0], 21.0)          # 135° = 9 h west of 6 h

    def test_stop_holds_the_position(self):
        self.mount.set_rate("find")
        self.mount.move("dec", -1)
        self.after(5)
        self.mount.stop("dec")
        self.assertAlmostEqual(self.after(100)[1], -5.0)

    def test_dec_stops_at_the_pole(self):
        self.mount.set_rate("slew")
        self.mount.move("dec", +1)
        self.assertEqual(self.after(60)[1], 90.0)

    def test_abort_stops_both_axes(self):
        self.mount.set_rate("find")
        self.mount.move("dec", +1)
        self.mount.move("ra", +1)
        self.after(3)
        self.mount.abort()
        self.assertEqual(self.after(10), self.after(10))

    def test_rate_change_applies_from_then_on(self):
        self.mount.set_rate("find")
        self.mount.move("dec", +1)
        self.after(2)
        self.mount.set_rate("slew")
        self.assertAlmostEqual(self.after(1)[1], 2.0 + RATES["slew"])

    def test_park_goes_to_the_pole_and_stops(self):
        self.mount.set_rate("find")
        self.mount.move("ra", +1)
        self.mount.park()
        self.assertEqual(self.after(10), (6.0, 90.0))


if __name__ == "__main__":
    unittest.main()
