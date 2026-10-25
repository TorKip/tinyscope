"""Flat spur gears (20° involute), for flat test prints such as the differential.

outline() gives (radius, azimuth) pairs with tooth k centred at phase + k·pitch.
"""
import math

from build123d import Pos, Vector, Wire, extrude, make_face


class SpurGear:
    def __init__(self, z, m=1.0, alpha=20.0, backlash=0.1):
        self.z, self.m = z, m
        self.rp = m * z / 2
        self.rb = self.rp * math.cos(math.radians(alpha))
        self.ra = self.rp + m
        self.rf = self.rp - 1.25 * m
        self.pitch = 2 * math.pi / z
        self.half = math.pi / (2 * z) - (backlash / 4) / self.rp

    def _inv(self, r):
        """Involute function at radius r ≥ rb; grows with r, so a tooth narrows towards its tip."""
        a = math.acos(min(1.0, self.rb / r))
        return math.tan(a) - a

    def outline(self, phase=0.0, n_flank=10, n_tip=3, n_root=4):
        a_p = self._inv(self.rp)
        r0 = max(self.rf, self.rb)
        rs = [r0 + (self.ra - r0) * i / n_flank for i in range(n_flank + 1)]
        pts = []
        for k in range(self.z):
            c = phase + k * self.pitch
            lower = [(r, c - self.half + (self._inv(r) - a_p)) for r in rs]
            upper = [(r, c + self.half - (self._inv(r) - a_p)) for r in reversed(rs)]
            if self.rf < r0:
                lower.insert(0, (self.rf, lower[0][1]))
                upper.append((self.rf, upper[-1][1]))
            tip = [(self.ra, lower[-1][1] + (upper[0][1] - lower[-1][1]) * i / (n_tip + 1)) for i in range(1, n_tip + 1)]
            nxt = phase + (k + 1) * self.pitch - self.half + (self._inv(r0) - a_p)
            root = [(self.rf, upper[-1][1] + (nxt - upper[-1][1]) * i / (n_root + 1)) for i in range(1, n_root + 1)]
            pts += lower + tip + upper + root
        return pts

    def xy(self, phase=0.0, n_flank=10):
        return [(r * math.cos(a), r * math.sin(a)) for r, a in self.outline(phase, n_flank)]

    def solid(self, z0, z1, phase=0.0):
        """The toothed body from height z0 to z1, axle on +z through the origin."""
        w = Wire.make_polygon([Vector(x, y, 0) for x, y in self.xy(phase)], close=True)
        return Pos(0, 0, z0) * extrude(make_face(w), z1 - z0)


def mesh_error(ga, pa, phase_a, gb, pb, phase_b):
    """How far (in teeth, 0 = perfect) two gears at centres pa, pb are from meshing."""
    ab = math.atan2(pb[1] - pa[1], pb[0] - pa[0])
    fa = ((ab - phase_a) / ga.pitch) % 1.0
    fb = ((ab + math.pi - phase_b) / gb.pitch) % 1.0
    e = (fa + fb - 0.5) % 1.0
    return min(e, 1.0 - e)


def phase_to_mesh(ga, pa, phase_a, gb, pb):
    """Phase for gear b at pb so it meshes gear a (rule f_a + f_b = 1/2, see mesh_phases)."""
    ab = math.atan2(pb[1] - pa[1], pb[0] - pa[0])
    fa = ((ab - phase_a) / ga.pitch) % 1.0
    return ab + math.pi - (0.5 - fa) * gb.pitch
