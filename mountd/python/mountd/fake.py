"""A mount that moves instantly: for tests and for running mountd with no hardware."""


class FakeMount:
    def __init__(self, ra=0.0, dec=90.0):
        self.ra, self.dec = ra, dec              # hours, degrees; starts at the pole, like a parked mount
        self.syncs = []                          # (ra, dec) of every sync, for tests

    def position(self):
        return self.ra, self.dec

    def slew(self, ra, dec):
        """Start a slew. Returns None if it started, or a reason it can't."""
        self.ra, self.dec = ra, dec
        return None

    def sync(self, ra, dec):
        self.syncs.append((ra, dec))
        self.ra, self.dec = ra, dec

    def abort(self):
        pass

    def is_slewing(self):
        return False
