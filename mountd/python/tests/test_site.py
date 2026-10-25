"""The site and clock: Meade's signs in, mountd's out, and a clock the client sets."""
import unittest
from datetime import datetime, timezone

from mountd import sky
from mountd.site import Site

EPOCH = 1767225600                       # 2026-01-01 00:00:00 UTC


class Clock:
    def __init__(self, t=EPOCH):
        self.t = t

    def __call__(self):
        return self.t


class Signs(unittest.TestCase):
    def test_longitude_west_positive_in_east_positive_out(self):
        site = Site()
        for text, east in [("-05*00", 5.0), ("005*30", -5.5), ("355*00", 5.0), ("180*00", -180.0), ("000*00", 0.0)]:
            with self.subTest(text):
                self.assertTrue(site.set_longitude(text))
                self.assertAlmostEqual(site.longitude, east)

    def test_longitude_reads_back_west_positive(self):
        site = Site(longitude=5.5)
        self.assertEqual(site.longitude_text(), "-005*30")
        site.longitude = -120.25
        self.assertEqual(site.longitude_text(), "+120*15")

    def test_latitude_south_keeps_its_sign(self):
        site = Site()
        self.assertTrue(site.set_latitude("-00*30"))
        self.assertEqual(site.latitude, -0.5)
        self.assertEqual(site.latitude_text(), "-00*30")

    def test_utc_offset_text(self):
        for offset, text in [(0, "+00"), (-1, "-01"), (-5.5, "-05.5"), (10, "+10")]:
            self.assertEqual(Site(utc_offset=offset).utc_offset_text(), text)

    def test_invalid_input_is_refused_and_changes_nothing(self):
        site = Site(latitude=45.0, longitude=5.0, utc_offset=-1.0)
        for setter, text in [("set_latitude", "+91*00"), ("set_longitude", "361*00"), ("set_longitude", "10*60"),
                             ("set_utc_offset", "+15"), ("set_utc_offset", "one"),
                             ("set_local_time", "24:00:00"), ("set_local_date", "02/30/26")]:
            with self.subTest(f"{setter}({text})"):
                self.assertFalse(getattr(site, setter)(text))
        self.assertEqual((site.latitude, site.longitude, site.utc_offset), (45.0, 5.0, -1.0))


class ClientClock(unittest.TestCase):
    def setUp(self):
        self.clock = Clock()
        self.site = Site(utc_offset=-1.0, clock=self.clock)       # CET, as Ekos sent on 2026-10-25

    def test_set_time_keeps_running(self):
        self.site.set_local_date("10/25/26")
        self.site.set_local_time("20:11:47")
        self.assertEqual(self.site.now(), datetime(2026, 10, 25, 19, 11, 47, tzinfo=timezone.utc))
        self.clock.t += 3600
        self.assertEqual(self.site.local_time_text(), "21:11:47")

    def test_changing_the_zone_keeps_the_utc_time(self):
        before = self.site.now()
        self.site.set_utc_offset("-2.0")
        self.assertEqual(self.site.now(), before)
        self.assertEqual(self.site.local_time_text(), "02:00:00")

    def test_two_digit_years(self):
        self.site.set_local_date("04/10/87")
        self.assertEqual(self.site.local_date_text(), "04/10/87")
        self.assertEqual(self.site.local().year, 1987)
        self.site.set_local_date("01/01/68")
        self.assertEqual(self.site.local().year, 2068)

    def test_lst_uses_the_clients_time_and_longitude(self):
        self.site.set_longitude("-15*00")
        self.site.set_local_date("10/25/26")
        self.site.set_local_time("22:00:00")
        expected = sky.lst(datetime(2026, 10, 25, 21, 0, tzinfo=timezone.utc), 15.0)
        self.assertAlmostEqual(self.site.lst(), expected, places=9)


if __name__ == "__main__":
    unittest.main()
