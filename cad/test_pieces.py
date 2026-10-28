"""Small test prints cut from the real parts, to check the fits before the big prints.

    python cad/test_pieces.py      # ~1 min → cad/out/stl/test/

Each piece is the real part (in its print pose) cut by a box, so it tests exactly the geometry
that will be printed. A light printability check runs on each piece (same rules as
test_tinyscope.py's, copied here because that file runs its whole suite on import).
"""
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from build123d import GeomType, Pos, Rot, export_stl  # noqa: E402
import tinyscope as ts  # noqa: E402

OUT = ts.OUT / "stl" / "test"
PLA = 1.24                         # g/cm³


def pieces(parts):
    """name: (shape in print pose, what it tests, what to do with it)."""
    z0, z1 = ts.PLATE
    foot = ts.print_pose("foot", parts["foot"][0])
    fork = ts.print_pose("fork", parts["fork"][0])
    head = ts.print_pose("head_body", parts["head_body"][0])
    head_raw = parts["head_body"][0]
    # the print poses are centred on the bed, so find each feature again from the part's bounding box
    fbb = parts["fork"][0].bounding_box()
    fdx, fdy, fdz = -fbb.center().X, -fbb.center().Y, -fbb.min.Z
    footbb = parts["foot"][0].bounding_box()
    tdx, tdy = -footbb.center().X, -footbb.center().Y
    cx = ts.RA_SHAFT[0] - ts.BYJ_OFFSET
    ux = ts.ULN_X
    return {
        "thread_test": (
            foot & ts.B(tdx - 14, tdx + 14, tdy - 14, tdy + 14, -1, 10.5),
            "the printed 1/4\"-20 thread",
            "screw it onto the tripod: snug and straight, no wobble. Tight: raise the 0.35 oversize in foot()",
        ),
        "ra_motor_test": (
            fork & ts.B(fdx + cx - 20, fdx - 22, fdy - 24, fdy + 24, fdz + z0 - 1, fdz + z1 - 0.05),
            "the RA motor pocket, its ear holes and the push pins, and the pinion through the plate",
            "press a motor in with two push_pin_ra, pinion on: the motor sits flat, the pins hold, the shaft is square",
        ),
        "uln_deck_test": (
            fork & ts.B(fdx + ux - ts.ULN[2] - 6, fdx + ux + 6, fdy - 43, fdy + 43, fdz + z0 - 1, fdz + z1 + 23),
            "the two ULN2003 slots",
            "slide both boards in: they stay put upside down but come out by hand",
        ),
        "camera_test": (
            head & _camera_box(head_raw),
            "the camera pegs, the lens window and the flex pocket",
            "the camera board presses onto the pegs and the lens sits centred in the window. MEASURE your board's holes first (CAM_HOLES)",
        ),
    }


def _camera_box(part):
    """The front wall round the camera. The print pose turns head z into y and puts the front face
    on the bed, then centres the part, so the camera (head x = z = 0) moves by that centring."""
    raw = Rot(-90, 0, 0) * part
    c = raw.bounding_box().center()
    x, y = -c.X, -c.Y
    return ts.B(x - 17, x + 17, y - 10, y + 17, -1, ts.HY - ts.CAM_Y + 2.5)   # head z -10..17


def worst_overhang(face):
    verts, tris = face.tessellate(0.05, 0.05)
    worst = 0.0
    for a, b, c in tris:
        A, B, C = verts[a], verts[b], verts[c]
        if max(A.Z, B.Z, C.Z) < 0.02:
            continue
        n = (B - A).cross(C - A)
        if n.length < 1e-12 or n.Z >= 0:
            continue
        worst = max(worst, 90 - math.degrees(math.acos(min(1.0, -n.Z / n.length))))
    return worst


# bridges the parent parts already accept (see ALLOWED and ZONES in test_tinyscope.py): the RA motor
# pocket's ceiling and its stepped bridges, everything facing down up to two layers over the face
POCKET_TOP = ts.RA_FACE - ts.PLATE[0] + 2 * ts.LAYER + 0.01


def problems(name, shape):
    out = []
    for f in shape.faces():
        bb = f.bounding_box()
        if f.geom_type == GeomType.CYLINDER and bb.size.Z <= 3.51:
            continue                   # a small horizontal hole's roof
        if f.geom_type == GeomType.PLANE and max(bb.size.X, bb.size.Y) <= 3.5:
            continue
        if name == "thread_test" and f.geom_type == GeomType.BSPLINE:
            continue                   # the thread's flanks
        if worst_overhang(f) <= 46.5:
            continue
        if name == "ra_motor_test" and bb.max.Z <= POCKET_TOP:
            continue
        out.append(f"{name}: face {bb.size.X:.1f} × {bb.size.Y:.1f} at z {bb.min.Z:.1f} overhangs")
    return out


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    parts = {k: v for g in ts.build().values() for k, v in g.items()}
    bad = []
    for name, (shp, what, how) in pieces(parts).items():
        bb = shp.bounding_box()
        shp = Pos(-bb.center().X, -bb.center().Y, -bb.min.Z) * shp
        assert shp.volume > 100, f"{name} is empty: the cut box missed the part"
        assert abs(shp.bounding_box().min.Z) < 0.01
        export_stl(shp, str(OUT / f"{name}.stl"), tolerance=0.01, angular_tolerance=0.2)
        bb = shp.bounding_box()
        print(f"{name:14s} {bb.size.X:5.1f} × {bb.size.Y:5.1f} × {bb.size.Z:4.1f} mm, "
              f"~{shp.volume / 1000 * PLA:4.1f} g solid  tests {what}")
        print(f"{'':14s} check: {how}")
        bad += problems(name, shp)
    print("\n".join(bad) if bad else "all pieces print without supports")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
