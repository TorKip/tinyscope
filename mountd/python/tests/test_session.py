import unittest

from mountd.fake import FakeMount
from mountd.session import Session


class Session_(unittest.TestCase):
    def test_unknown_command_is_logged(self):
        with self.assertLogs("mountd.lx200", "WARNING") as logs:
            self.assertEqual(Session(FakeMount()).feed(":XYZ#"), "")
        self.assertIn(":XYZ#", logs.output[0])

    def test_command_split_across_reads(self):
        s = Session(FakeMount())
        self.assertEqual(s.feed(":G"), "")
        self.assertEqual(s.feed("R#"), "00:00:00#")

    def test_sync_moves_the_mount_and_is_recorded(self):
        mount = FakeMount()
        s = Session(mount)
        s.feed(":Sr 05:35:17#:Sd -05*23:28#")
        self.assertEqual(s.feed(":CM#"), "tinyscope synced#")
        self.assertEqual(len(mount.syncs), 1)
        self.assertEqual(s.feed(":GR#"), "05:35:17#")

    def test_a_refused_target_keeps_the_old_one(self):
        s = Session(FakeMount())
        s.feed(":Sr 05:35:17#:Sd -05*23:28#")
        self.assertEqual(s.feed(":Sr 25:00:00#"), "0")
        self.assertEqual(s.feed(":MS#:GR#"), "005:35:17#")


if __name__ == "__main__":
    unittest.main()
