"""A mount with no hardware: for tests and for running mountd on the desk.

GoTo, sync and park arrive instantly. Manual moves (Ekos's arrow buttons) take time, so a client
polling the position sees it change. The clock is injectable so tests can move time by hand.
"""
import time

SIDEREAL = 15 / 3600                     # °/s, roughly
RATES = {                                # °/s on the sky, by the LX200 names (:RG# :RC# :RM# :RS#)
    "guide": 1 * SIDEREAL,
    "centering": 8 * SIDEREAL,
    "find": 1.0,
    "slew": 9.0,                         # the README's ~500 half-steps/s
}


class FakeMount:
    def __init__(self, ra=0.0, dec=90.0, clock=time.monotonic):
        self.ra, self.dec = ra, dec              # hours, degrees; starts at the pole, like a parked mount
        self.syncs = []                          # (ra, dec) of every sync, for tests
        self.clock = clock
        self.rate = RATES["centering"]
        self._moving = {"ra": 0, "dec": 0}       # +1 = east / north, -1 = west / south
        self._since = clock()

    def _advance(self):
        """Apply the moves since the last call."""
        now = self.clock()
        degrees = self.rate * (now - self._since)
        self._since = now
        self.ra = (self.ra + self._moving["ra"] * degrees / 15) % 24
        self.dec = max(-90.0, min(90.0, self.dec + self._moving["dec"] * degrees))

    def position(self):
        self._advance()
        return self.ra, self.dec

    def slew(self, ra, dec):
        """Start a slew. Returns None if it started, or a reason it can't."""
        self.abort()
        self.ra, self.dec = ra, dec
        return None

    def sync(self, ra, dec):
        self._advance()
        self.syncs.append((ra, dec))
        self.ra, self.dec = ra, dec

    def set_rate(self, name):
        self._advance()
        self.rate = RATES[name]

    def move(self, axis, direction):
        self._advance()
        self._moving[axis] = direction

    def stop(self, axis):
        self._advance()
        self._moving[axis] = 0

    def abort(self):
        self.stop("ra")
        self.stop("dec")

    def park(self):
        self.abort()
        self.dec = 90.0

    def is_slewing(self):
        return False
