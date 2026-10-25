"""Checks for the tinyscope CAD. Run: python cad/test_tinyscope.py

1. Printable without supports: every face of every printed part, in its print pose, sits on the bed,
   overhangs at most 45° from vertical, is a small horizontal hole, or is listed in ALLOWED (bridges).
2. Clearances through the motion: the head through its Dec range, and everything that turns with RA
   through a full turn, keep their distance from what they must not touch. Pairs that touch by
   design (bearings, meshing gears, thrust faces) are listed with the distance they should keep.
3. Gear centre distances and the RA/Dec numbers quoted in the docs.
"""
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from build123d import GeomType, Pos, Rot  # noqa: E402
import tinyscope as ms  # noqa: E402

OVERHANG, TOL, SMALL_HOLE, ON_BED = 45.0, 1.5, 3.5, 0.02
GAP = 1.0            # mm, default clearance between parts that must not touch

# part: [(what, size_x, size_y, reason)]: faces this check flags and we accept; matched by size
ALLOWED = {
    "foot": [("cable groove's roof, under the foot", 7.0, 24.59, "a 7 mm bridge")],
    "hub": [("circlip groove's upper face", 22.0, 22.0, "a 1.2 mm ring; it is the face the clip bears on, so it stays square")],
    "fork": [
        ("RA motor pocket's ceiling (2 mm deep, from below)", 28.6, 42.6, "a 28.6 mm bridge, fine on a Bambu"),
        ("power-cable tunnel's roof through the left tine root", 5.0, 8.0, "an 8 mm bridge"),
        ("ribbon channel bridges", 1.6, 14.0, "14 mm bridges"),
        ("ribbon channel's top end", 2.4, 14.0, "a 14 mm bridge"),
    ],
    "head_body": [
        ("hex sockets' flat roofs", 6.0, 10.57, "10.4 mm bridges (a corner up would overhang 60°)"),
        ("snap-hook windows' roofs", 13.0, 2.4, "13 mm bridges"),
    ],
    "head_lid": [("snap hooks' catch faces", 12.0, 0.6, "0.6 mm ledges")],
    "hood": [("servo wire slot's roof in the end wall", 3.5, 8.5, "a 3.5 mm bridge")],
    "dec_stub": [("journal's underside round the hex key", 22.0, 22.0, "a ring up to 2 mm wide from the hex flats")],
    "cable_stub": [("circlip groove's upper face", 17.0, 17.0, "a 1 mm ring")],
    "lens_cap": [
        ("arm's underside over the servo's round top", 9.33, 10.6, "a 10 mm bridge"),
        ("spline bore's end", 4.6, 4.6, "a 4.6 mm bridge"),
    ],
}

failed = 0
GROUPS = ms.build()
PARTS = {k: v for g in GROUPS.values() for k, v in g.items()}


def test(name, fn):
    global failed
    try:
        fn()
        print("ok  ", name)
    except AssertionError as e:
        failed += 1
        print("FAIL", name, "\n     ", e)


def worst_overhang(face):
    verts, tris = face.tessellate(0.05, 0.05)
    worst, z = 0.0, None
    for a, b, c in tris:
        A, B, C = verts[a], verts[b], verts[c]
        if max(A.Z, B.Z, C.Z) < ON_BED:
            continue
        n = (B - A).cross(C - A)
        if n.length < 1e-12 or n.Z >= 0:
            continue
        ov = 90 - math.degrees(math.acos(min(1.0, -n.Z / n.length)))
        if ov > worst:
            worst, z = ov, min(A.Z, B.Z, C.Z)
    return worst, z


def problems(name, shape, allowed=()):
    out, used = [], set()
    for f in shape.faces():
        worst, _ = worst_overhang(f)
        bb = f.bounding_box()
        if f.geom_type == GeomType.CYLINDER and bb.size.Z <= SMALL_HOLE + 0.01 and worst > 80:
            continue                       # a small horizontal hole's roof
        if f.geom_type == GeomType.PLANE and max(bb.size.X, bb.size.Y) <= SMALL_HOLE:
            continue                       # a tiny bridge, e.g. the end of a blind vertical hole
        if name == "foot" and f.geom_type == GeomType.BSPLINE and bb.max.Z < 10.5:
            continue                       # the 1/4"-20 thread's flanks (30° from horizontal, fine at this size)
        if worst <= OVERHANG + TOL:
            continue
        for k, (what, sx, sy, _) in enumerate(allowed):
            if abs(bb.size.X - sx) < 0.3 and abs(bb.size.Y - sy) < 0.3:
                used.add(k)
                break
        else:
            out.append(f"{name}: {f.geom_type.name.lower()} face at z {bb.min.Z:.2f}–{bb.max.Z:.2f}, "
                       f"{bb.size.X:.2f} × {bb.size.Y:.2f} at ({bb.center().X:.1f}, {bb.center().Y:.1f}), overhangs {worst:.0f}°")
    stale = [f"{name}: ALLOWED '{a[0]}' matches no face" for k, a in enumerate(allowed) if k not in used]
    return out, stale


def printable():
    bad = []
    for name in ms.PRINTED:
        out, stale = problems(name, ms.print_pose(name, PARTS[name][0]), ALLOWED.get(name, ()))
        bad += out + stale
    assert not bad, "\n      ".join(bad)


def catches_upside_down():
    for name in ("hood", "head_lid", "fork"):
        flipped = Rot(180, 0, 0) * ms.print_pose(name, PARTS[name][0])
        flipped = Pos(0, 0, -flipped.bounding_box().min.Z) * flipped
        out, _ = problems(name, flipped, ALLOWED.get(name, ()))
        assert out, f"{name} upside down passed"


def fits_the_bed():
    big = [f"{n}: {bb.size.X:.0f} × {bb.size.Y:.0f} × {bb.size.Z:.0f}" for n in ms.PRINTED
           for bb in [ms.print_pose(n, PARTS[n][0]).bounding_box()] if max(bb.size.X, bb.size.Y) > 250 or bb.size.Z > 250]
    assert not big, big


# ---------- clearances ----------

def dist(a, b, limit):
    """Distance between two shapes, or `limit` + 1 when their boxes are clearly apart."""
    A, B = a.bounding_box(), b.bounding_box()
    sep = max(A.min.X - B.max.X, B.min.X - A.max.X, A.min.Y - B.max.Y, B.min.Y - A.max.Y,
              A.min.Z - B.max.Z, B.min.Z - A.max.Z)
    if sep > limit:
        return limit + 1
    return a.distance_to(b)


# (a, b): least distance they keep; None = not checked (they touch or mesh by design)
DESIGNED = {
    ("dec_stub", "fork"): ms.CLEAR * 0.9, ("cable_stub", "fork"): 0.0,
    ("dec_wheel", "dec_pinion"): None, ("dec_wheel", "fork"): 0.5, ("dec_stub", "dec_pinion"): None,
    ("hub", "fork"): None, ("ra_wheel", "fork"): 0.3, ("ra_wheel", "ra_pinion"): None,
    ("hub", "ra_pinion"): 0.5, ("ra_clip", "fork"): 0.5,
}


def keep(a, b):
    return DESIGNED.get((a, b), DESIGNED.get((b, a), GAP))


HEAD_MOVING = [k for k in GROUPS["head"]]
RA_PARTS = [k for k in GROUPS["ra"]]
DECS = list(range(-35, 101, 5))


def head_clears_the_fork():
    """Head (incl. stubs, wheel, hood, cap) against everything on the fork, Dec −35°…100°."""
    bad, worst = [], (99, None)
    for dec in DECS:
        loc = ms.head_loc(dec)
        for h in HEAD_MOVING:
            hs = loc * PARTS[h][0]
            for r in RA_PARTS + ["ra_wheel", "ra_clip", "hub"]:
                k = keep(h, r)
                if k is None:
                    continue
                d = dist(hs, PARTS[r][0] if r in GROUPS["ra"] else ms.MOUNT.inverse() * PARTS[r][0], k + 3)
                if d < worst[0] and k == GAP:
                    worst = (d, f"{h}–{r} at Dec {dec}")
                if d < k - 1e-3:
                    bad.append(f"{h}–{r} at Dec {dec}: {d:.2f} mm (keep {k})")
    print(f"      closest head–fork pass: {worst[0]:.1f} mm ({worst[1]})")
    assert not bad, "\n      ".join(bad[:20])


def ra_clears_the_foot():
    """Fork + head at three Dec angles against the foot, hub, wheel and clip, a full RA turn."""
    bad, worst = [], (99, None)
    fixed = {k: v[0] for k, v in GROUPS["fixed"].items()}
    for ha in range(0, 360, 15):
        R = ms.MOUNT * Rot(0, 0, ha)
        moving = {k: R * PARTS[k][0] for k in RA_PARTS}
        for dec in (-35, 30, 100):
            for h in ("head_body", "hood", "lens_cap", "head_lid"):
                moving[f"{h}@{dec}"] = R * ms.head_loc(dec) * PARTS[h][0]
        for m, ms_ in moving.items():
            for f, fs in fixed.items():
                k = keep(m.split("@")[0], f)
                if k is None:
                    continue
                d = dist(ms_, fs, k + 3)
                if f == "foot" and d < worst[0]:
                    worst = (d, f"{m} at HA {ha}")
                if d < k - 1e-3:
                    bad.append(f"{m}–{f} at RA {ha}: {d:.2f} mm (keep {k})")
    print(f"      closest pass over the foot: {worst[0]:.1f} mm ({worst[1]})")
    assert not bad, "\n      ".join(bad[:20])


def tripod_head_clear():
    """Nothing that turns may reach below z = 12 in world within 45 mm of the tripod screw
    (a tripod head or quick-release clamp up to Ø90 sits under the foot)."""
    low = 99
    for ha in range(0, 360, 15):
        R = ms.MOUNT * Rot(0, 0, ha)
        for k in RA_PARTS:
            low = min(low, (R * PARTS[k][0]).bounding_box().min.Z)
    print(f"      lowest point of the turning parts: z = {low:.1f} mm (foot top at 10)")
    assert low > 12, low


def gears_and_numbers():
    assert abs(ms.CD - 36.0) < 1e-9
    steps = 4096 * 63.68395 / 64 * ms.ZW / ms.ZP           # half-steps per axis turn (gearbox is 63.684:1)
    arcsec = 360 * 3600 / steps
    assert 63 < arcsec < 64.5, arcsec
    scale = 206.265 * 1.4 / 3.6                               # ″/px, OV5647 1.4 µm, 3.6 mm lens
    print(f"      {steps:.0f} half-steps per axis turn → {arcsec:.1f}″ per half-step = {arcsec / scale:.2f} px; "
          f"sidereal: one half-step every {arcsec / 15.041:.2f} s")


test("every printed part prints without supports (bar the listed bridges)", printable)
test("the check catches the hood, lid and fork upside down", catches_upside_down)
test("every printed part fits a 256 mm bed", fits_the_bed)
test("gear centre distance and step size", gears_and_numbers)
if "--print-only" in sys.argv:
    sys.exit(1 if failed else 0)
test("the head clears the fork through Dec −35°…100°", head_clears_the_fork)
test("the fork, head and motors clear the foot through a full RA turn", ra_clears_the_foot)
test("nothing turning comes near the tripod head", tripod_head_clear)
print(f"\n{failed} failed" if failed else "\nall passed")
sys.exit(1 if failed else 0)
