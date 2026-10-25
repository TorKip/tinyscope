"""Replays every file in mountd/conversations/ against a Session on a FakeMount.

File format (shared with the Go version): '>' lines are sent, the '<' line after one is the exact
reply expected (no '<' line = expect silence), '#' at the start of a line is a comment.
Escapes such as \\x06 are allowed on both sides. A '# t=12.5' comment sets the mount's clock to
that many seconds, for commands whose answer depends on time (moves); --record writes them.
"""
import codecs
import logging
import unittest
from pathlib import Path

from mountd.fake import FakeMount
from mountd.session import Session
from tests.test_fake import Clock

CONVERSATIONS = Path(__file__).resolve().parents[2] / "conversations"


def unescape(text):
    return codecs.decode(text, "unicode_escape")


def exchanges(text, name="conversation"):
    """(line number, sent, expected reply) for each '>' line of a conversation file's text."""
    out = []
    for n, line in enumerate(text.splitlines(), 1):
        if line.startswith("> "):
            out.append([n, unescape(line[2:]), ""])
        elif line.startswith("< "):
            assert out and out[-1][2] == "", f"{name}:{n}: a reply with no command before it"
            out[-1][2] = unescape(line[2:])
        elif line.strip() and not line.startswith("#"):
            raise AssertionError(f"{name}:{n}: lines start with '> ', '< ' or '#'")
    return out


def times(text):
    """(line number, seconds) for each '# t=' line."""
    return [(n, float(line[4:])) for n, line in enumerate(text.splitlines(), 1) if line.startswith("# t=")]


class Conversations(unittest.TestCase):
    def test_every_file(self):
        files = sorted(CONVERSATIONS.glob("*.txt"))
        self.assertTrue(files, f"no conversations in {CONVERSATIONS}")
        quiet = logging.getLogger("mountd")                     # errors.txt sends unknown commands on purpose
        self.addCleanup(quiet.setLevel, quiet.level)
        quiet.setLevel(logging.ERROR)
        for path in files:
            with self.subTest(path.name):
                text, clock = path.read_text(), Clock()
                session, ticks = Session(FakeMount(clock=clock)), times(text)
                for n, sent, expected in exchanges(text, path.name):
                    while ticks and ticks[0][0] < n:
                        clock.t = ticks.pop(0)[1]
                    self.assertEqual(session.feed(sent), expected, f"{path.name}:{n}: sent {sent!r}")


if __name__ == "__main__":
    unittest.main()
