"""Run from mountd/python: python3 -m unittest"""
import unittest

from mountd.lx200 import ACK, format_dec, format_ra, parse_dec, parse_ra, split_commands


class SplitCommands(unittest.TestCase):
    def test_one_command(self):
        self.assertEqual(split_commands(":GR#"), ([":GR#"], ""))

    def test_several_in_one_read(self):
        self.assertEqual(split_commands(":GR#:GD#"), ([":GR#", ":GD#"], ""))

    def test_unfinished_command_is_kept(self):
        self.assertEqual(split_commands(":GR#:Sr 05:3"), ([":GR#"], ":Sr 05:3"))

    def test_noise_before_a_command_is_dropped(self):
        self.assertEqual(split_commands("#\r\n:GD#"), ([":GD#"], ""))

    def test_ack_on_its_own(self):
        self.assertEqual(split_commands(ACK + ":GR#"), ([ACK, ":GR#"], ""))


class FormatRa(unittest.TestCase):
    def test_high(self):
        self.assertEqual(format_ra(5 + 34 / 60 + 32 / 3600), "05:34:32")

    def test_low(self):
        self.assertEqual(format_ra(5 + 34.5 / 60, high=False), "05:34.5")

    def test_rounds_up_into_the_next_day(self):
        # 23:59:59.6 rounds to 24:00:00, which must wrap to 00:00:00, not print "24"
        self.assertEqual(format_ra(24 - 0.4 / 3600), "00:00:00")

    def test_negative_hours_wrap(self):
        self.assertEqual(format_ra(-1), "23:00:00")


class FormatDec(unittest.TestCase):
    def test_high(self):
        self.assertEqual(format_dec(41 + 16 / 60 + 9 / 3600), "+41*16:09")

    def test_low(self):
        self.assertEqual(format_dec(-5.5, high=False), "-05*30")

    def test_minus_zero_degrees_keeps_its_sign(self):
        # −0°30′: the degrees are 0, so a sign taken from the degrees would be lost
        self.assertEqual(format_dec(-0.5), "-00*30:00")

    def test_pole(self):
        self.assertEqual(format_dec(90), "+90*00:00")


class ParseRa(unittest.TestCase):
    def test_high(self):
        self.assertAlmostEqual(parse_ra("05:34:32"), 5 + 34 / 60 + 32 / 3600)

    def test_low(self):
        self.assertAlmostEqual(parse_ra("05:34.5"), 5 + 34.5 / 60)

    def test_round_trip(self):
        for text in ("00:00:00", "12:30:45", "23:59:59"):
            self.assertEqual(format_ra(parse_ra(text)), text)

    def test_invalid(self):
        for text in ("24:00:00", "12:60:00", "12:30:60", "abc", ""):
            self.assertIsNone(parse_ra(text), text)


class ParseDec(unittest.TestCase):
    def test_high(self):
        self.assertAlmostEqual(parse_dec("+41*16:09"), 41 + 16 / 60 + 9 / 3600)

    def test_low(self):
        self.assertAlmostEqual(parse_dec("-05*30"), -5.5)

    def test_meade_degree_byte(self):
        self.assertAlmostEqual(parse_dec("+41\xdf16:09"), 41 + 16 / 60 + 9 / 3600)

    def test_minus_zero(self):
        self.assertAlmostEqual(parse_dec("-00*30:00"), -0.5)

    def test_round_trip(self):
        for text in ("+00*00:00", "-00*00:01", "+89*59:59", "-90*00:00"):
            self.assertEqual(format_dec(parse_dec(text)), text)

    def test_invalid(self):
        for text in ("+91*00:00", "+45*60:00", "+45*00:60", "north", ""):
            self.assertIsNone(parse_dec(text), text)


if __name__ == "__main__":
    unittest.main()
