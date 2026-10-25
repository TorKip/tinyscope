"""tinyscope: a Raspberry Pi 3B + Pi camera v1 on a printed fork mount, on a fixed EQ wedge.

    ulimit -v 3300000
    python cad/tinyscope.py       # → cad/out/

Three frames, each a kinematic group:
- world: the tripod plate at z = 0, +y = north. The foot (fixed wedge) lives here.
- mount: z = the polar (RA) axis, z = 0 at the column's top face. The fork, both 28BYJ-48s and the
  ULN2003 boards turn with RA. mount = Pos(0, 0, HC) * Rot(-TILT, 0, 0) in world.
- head: x = the Dec axis, y = the optical axis (forward), z = "up" on the head. The Pi, camera,
  lens hood and cap servo turn with Dec. head = Pos(0, 0, DEC_H) * Rot(dec, 0, 0) in mount, so
  dec = 90 points the camera at the pole.

Only power crosses an axis: it comes up through the hollow polar axis, and a 10-wire Dupont
ribbon (8 step lines, 5 V, GND) goes through the hollow left Dec stub into the head.
No bought hardware: printed push pins (or M3 screws), 1.75 mm filament as dowels, the screws
that come with the SG90.
"""
import base64
import math
import sys
from pathlib import Path

from build123d import (Align, Box, Color, Compound, Cone, Cylinder, Location, Plane, Polygon, Pos,
                       Rot, export_gltf, export_step, export_stl, extrude, fillet, Axis)
from bd_warehouse.thread import IsoThread

sys.path.insert(0, str(Path(__file__).parent))
from spur_gear import SpurGear, phase_to_mesh  # noqa: E402

OUT = Path(__file__).parent / "out"
MIN3 = (Align.MIN, Align.MIN, Align.MIN)
CCM = (Align.CENTER, Align.CENTER, Align.MIN)

# ---------- site ----------
LAT = 60.0                    # Oslo is 59.9°; a reprint per latitude, the wedge has no adjustment
TILT = 90.0 - LAT
HC = 60.0                     # world height of the column's top face centre

# ---------- polar axis (mount frame) ----------
COL_R = 21.5                  # column radius
FLANGE = (0.0, 3.0)           # hub flange; the fork plate rests on its top
FLANGE_R = 19.0
KEY_AF = 20.0                 # hub's hex key into the column
KEY_Z = (-15.0, -9.0)         # key; a 45° cone from its flats (r 10) joins it to the flange (r 19)
BORE = 15.0                   # cable bore through column and hub
PLATE = (3.0, 8.0)            # fork plate
JOURNAL_D = 28.0              # spindle, the RA plain bearing
SPIN_HEX = 24.0               # spindle hex the RA wheel keys on
WHEEL_Z = (8.4, 14.4)         # RA wheel (fixed): 0.4 above the plate = the plate's axial play
TOP_D, GROOVE_D, GROOVE = 22.0, 19.6, (14.5, 15.9)   # spindle top and its circlip groove
SPIN_TOP = 18.0
CLEAR = 0.2                   # sliding fit, per side
FIT = 0.15                    # snug fit, per side

# ---------- gears: module 1, 60:12 = 5:1 on both axes ----------
M, ZW, ZP = 1.0, 60, 12
CD = M * (ZW + ZP) / 2        # 36 mm
BACKLASH = 0.2                # total, at the pitch circle (FDM)
WHEEL = SpurGear(ZW, M, backlash=BACKLASH)
PINION = SpurGear(ZP, M, backlash=BACKLASH)
PIN_LEN = 5.5

# ---------- 28BYJ-48 (local: shaft at origin along +z, mounting face z = 0, body towards -y) ----------
BYJ_R, BYJ_DEPTH, BYJ_OFFSET = 14.0, 19.0, 8.0
BYJ_EARS, BYJ_EAR_W, BYJ_EAR_HOLE = 35.0, 7.0, 4.2
BYJ_BOSS = (9.0, 1.5)
BYJ_SHAFT, BYJ_FLATS, BYJ_SHAFT_LEN = 5.0, 3.0, 9.5
RA_SHAFT = (-36.0, 0.0)       # RA motor shaft in mount xy; body radially outward, at x -44
RA_FACE = 5.0                 # motor face 2 mm up in a pocket under the plate, so the shaft reaches the wheel

# ---------- fork (mount frame) ----------
DEC_H = 58.0                  # Dec axis height; set by the head's swing, see test_tinyscope.py
TINE_IN, TINE_T, TINE_HW = 55.0, 9.0, 20.0
TINE_OUT = TINE_IN + TINE_T   # 64
STUB_D = 22.0                 # Dec journals
DEC_WHEEL_X = (64.5, 70.5)
BRACKET_X = (71.5, 75.5)      # Dec motor bracket; the motor face sits on its outer side
DECK_X = (-84.0, -64.0)       # ULN2003 deck beyond the left tine
ULN_X = -73.2                 # boards' solder side; components face -x
ULN = (35.0, 32.0, 1.6)       # board: width, height, PCB
ULN_Y = 19.0                  # board centres at y = ±19, edges 1.5 deep in the posts

# ---------- head (head frame) ----------
HX, HY, HZ, WALL = 54.0, 18.5, 33.0, 2.4
BACK = -HY + WALL             # -16.1: body's open back; the lid closes it
FRONT_IN = HY - WALL          # 16.1
SOCK_AF = 18.0                # stubs' hex key into the head
SOCK_X = 48.0                 # inner end of the head's side bosses
PI_Y = 10.0                   # Pi's solder side (faces the camera); component side at 8.6
PI_HOLES = [(-39.0, -24.5), (-39.0, 24.5), (19.0, -24.5), (19.0, 24.5)]   # USB end at +x
CAM_Y = 15.3                  # camera PCB front (0.8 standoffs)
CAM_HOLES = [(-10.5, 7.46), (10.5, 7.46), (-10.5, -5.04), (10.5, -5.04)]  # around the lens; MEASURE yours
LENS_SQ = 8.5
DOWELS = [(-17.0, -15.0), (-17.0, 24.0)]   # 1.75 mm filament pins, hood ↔ head
FIL_HOLE = 1.85
HOOD_END = 44.5               # hood mouth (y); lens front ≈ 20.3
SERVO = (8.0, 20.0)           # SG90 shaft (x, z) on the hood
SERVO_FLOOR = HY + 2.4        # hood plate top, the servo's bottom

FOV_H, FOV_V = 53.5, 41.4     # OV5647 + stock 3.6 mm lens


# ---------- helpers ----------

def B(x0, x1, y0, y1, z0, z1):
    return Pos(x0, y0, z0) * Box(x1 - x0, y1 - y0, z1 - z0, align=MIN3)


def cyl_z(r, z0, z1, x=0.0, y=0.0):
    return Pos(x, y, z0) * Cylinder(r, z1 - z0, align=CCM)


def cyl_x(r, x0, x1, y=0.0, z=0.0):
    return Pos(x0, y, z) * Rot(0, 90, 0) * Cylinder(r, x1 - x0, align=CCM)


def hex_z(af, z0, z1, phase=90.0, x=0.0, y=0.0):
    """Hex prism, axis z; phase 90 puts a corner on +y."""
    rc = af / math.sqrt(3)
    pts = [(rc * math.cos(math.radians(phase + 60 * k)), rc * math.sin(math.radians(phase + 60 * k))) for k in range(6)]
    return Pos(x, y, z0) * extrude(Polygon(*pts, align=None), z1 - z0)


def hex_x(af, x0, x1):
    """Hex prism on the x axis with corners on ±z: printed with the head's y vertical, its roof is a
    flat 10 mm bridge and the faces beside it overhang 30° (a corner up would overhang 60°)."""
    return Pos(x0, 0, 0) * Rot(0, 90, 0) * hex_z(af, 0, x1 - x0, phase=0.0)


def teardrop_x(d, x0, x1, y=0.0, z=0.0):
    """Hole along x with a 45° point towards +z, so its roof prints without support."""
    r = d / 2
    # Rot(0, 90, 0) maps local -x to +z, so the point goes on local -x
    tri = poly((-r * math.sqrt(2), 0), (-r * math.cos(math.radians(45)), r * math.sin(math.radians(45))),
               (-r * math.cos(math.radians(45)), -r * math.sin(math.radians(45))))
    prof = Cylinder(r, x1 - x0, align=CCM) + extrude(tri, x1 - x0)
    return Pos(x0, y, z) * Rot(0, 90, 0) * prof


def poly(*pts):
    """Polygon face whose normal is +z whatever the point order, so extrude() goes the way you expect."""
    area = sum(x0 * y1 - x1 * y0 for (x0, y0), (x1, y1) in zip(pts, pts[1:] + pts[:1]))
    return Polygon(*(pts if area > 0 else pts[::-1]), align=None)


def frame(origin, x_dir, z_dir):
    return Plane(origin=origin, x_dir=x_dir, z_dir=z_dir).location


def double_d_bore(z0, z1):
    r = BYJ_SHAFT / 2 + 0.05
    flat = BYJ_FLATS / 2 + 0.05
    return cyl_z(r, z0, z1) & B(-r, r, -flat, flat, z0, z1)


MOUNT = Pos(0, 0, HC) * Rot(-TILT, 0, 0)          # mount frame → world


def head_loc(dec):
    return Pos(0, 0, DEC_H) * Rot(dec, 0, 0)       # head frame → mount


# ---------- fixed group: foot (world frame) ----------

def foot():
    """Wedge and pier in one: a 10 mm foot on the tripod and a Ø43 column along the polar axis.
    Prints standing on the foot; the column leans 30° (fine without support)."""
    plate = fillet(B(-36, 36, -64, 38, 0, 10).edges().filter_by(Axis.Z), 8)
    column = MOUNT * cyl_z(COL_R, -120, 0)
    body = (plate + column) & B(-100, 100, -150, 150, 0, 200)
    # socket for the hub: 45° cone, hex, through-bore for the cable
    sock = cyl_z(BORE / 2, -130, 1)
    # the socket's 45° cone starts at the hex corners (no ceilings in the hole); the hub's starts at
    # its flats (no ledges on the part); both lie on the same 45° line, FIT apart
    rc = (KEY_AF + 2 * FIT) / math.sqrt(3)
    hc = FLANGE_R + FIT - rc
    sock += hex_z(KEY_AF + 2 * FIT, KEY_Z[0] - 0.4, -hc + 0.01, phase=0)
    sock += Pos(0, 0, -hc) * Cone(rc, FLANGE_R + FIT, hc, align=CCM)
    body -= MOUNT * sock
    # 1.75 mm filament pin along x, tangent to the key's +y flat: keeps the hub in when you lift the fork
    body -= MOUNT * cyl_x(FIL_HOLE / 2, -30, 30, y=KEY_AF / 2, z=sum(KEY_Z) / 2)
    # cable out under the foot towards the south edge
    body -= B(-3.5, 3.5, -64.1, -28, -1, 5)
    # 1/4"-20 UNC for the tripod screw, printed (0.35 oversize); 10 mm of thread
    body -= cyl_z((6.35 + 0.35) / 2, -1, 11)
    body += IsoThread(major_diameter=6.35 + 0.35, pitch=25.4 / 20, length=10, external=False,
                      end_finishes=("fade", "fade"))
    # north arrow, engraved 0.8
    arrow = poly((0, 36), (-7, 26), (-2.5, 26), (-2.5, 15), (2.5, 15), (2.5, 26), (7, 26))
    body -= Pos(0, 0, 9.2) * extrude(arrow, 2)
    return body


def hub():
    """Hex key, 45° cone, flange (thrust face for the fork plate), RA journal, hex for the wheel,
    circlip groove. Prints key-down."""
    h = hex_z(KEY_AF, KEY_Z[0], KEY_Z[1], phase=0)
    h += Pos(0, 0, KEY_Z[1]) * Cone(KEY_AF / 2, FLANGE_R, -KEY_Z[1], align=CCM)   # from the flats: no ledges
    h += cyl_z(FLANGE_R, *FLANGE)
    h += cyl_z(JOURNAL_D / 2, FLANGE[1], WHEEL_Z[0])
    h += hex_z(SPIN_HEX, WHEEL_Z[0], WHEEL_Z[1], phase=0)
    h += cyl_z(TOP_D / 2, WHEEL_Z[1], SPIN_TOP)
    h -= cyl_z(TOP_D, GROOVE[0], GROOVE[1]) - cyl_z(GROOVE_D / 2, GROOVE[0], GROOVE[1])
    h -= cyl_z(BORE / 2, KEY_Z[0] - 1, SPIN_TOP + 1)
    h -= cyl_x(FIL_HOLE / 2, -30, 30, y=KEY_AF / 2, z=sum(KEY_Z) / 2)
    return h


def ra_wheel():
    """60 teeth, fixed: the RA pinion walks round it. Hex-keyed to the spindle."""
    w = WHEEL.solid(0, WHEEL_Z[1] - WHEEL_Z[0])
    return w - hex_z(SPIN_HEX + 2 * FIT, -1, 10, phase=0)


def circlip(groove_d, od, t=1.2):
    """Printed C-clip: ID a hair under the groove so it grips; the gap is 0.75 × ID, so it must
    flex open to go on. PETG."""
    ring = cyl_z(od / 2, 0, t) - cyl_z(groove_d / 2 - 0.1, -1, t + 1)
    gap = 0.75 * groove_d
    ring -= B(-gap / 2, gap / 2, 0, od, -1, t + 1)
    ears = cyl_z(1.6, -0, t, x=-(gap / 2 + 1.8), y=od / 2 - 2.2) + cyl_z(1.6, 0, t, x=gap / 2 + 1.8, y=od / 2 - 2.2)
    return ring + ears - cyl_z(0.7, -1, t + 1, x=-(gap / 2 + 1.8), y=od / 2 - 2.2) - cyl_z(0.7, -1, t + 1, x=gap / 2 + 1.8, y=od / 2 - 2.2)


# ---------- RA group: fork (mount frame) ----------

def plate_outline():
    pts = [(DECK_X[0], -42), (DECK_X[1], -42), (DECK_X[1], -24), (BRACKET_X[1] + 10, -24), (BRACKET_X[1] + 10, 24),
           (DECK_X[1], 24), (DECK_X[1], 42), (DECK_X[0], 42)]
    f = Polygon(*pts, align=None)
    return fillet(f.vertices(), 3)


def fork():
    """Plate, two tines, the Dec motor bracket and the ULN2003 deck in one piece. Prints plate-down
    (tines up). The RA motor hangs under the plate, its pinion comes up through it."""
    z0, z1 = PLATE
    f = Pos(0, 0, z0) * extrude(plate_outline(), z1 - z0)
    f += cyl_z(30, z0, z1)
    # tines: rectangle up to the Dec axis plus a half-disc round it
    for s in (-1, 1):
        x0, x1 = sorted((s * TINE_IN, s * TINE_OUT))
        f += B(x0, x1, -TINE_HW, TINE_HW, z1 - 0.01, DEC_H) + cyl_x(TINE_HW, x0, x1, z=DEC_H)
        f -= teardrop_x(STUB_D + 2 * CLEAR, x0 - 1, x1 + 1, z=DEC_H)
        # root fillets as 45° wedges (both faces of each tine)
        for side in (x0, x1):
            d = -1 if side == x0 else 1
            tri = poly((0, 0), (d * 6, 0), (0, 6))
            f += Pos(side, TINE_HW, z1) * Rot(90, 0, 0) * extrude(tri, 2 * TINE_HW)
    # left tine (cable side): ribbon channel on the outer face, closed into a tunnel at two bridges
    ch = B(-TINE_OUT - 1, -TINE_OUT + 4, -7, 7, z1 + 6, DEC_H - 16)
    for zb in (z1 + 16, z1 + 32):
        ch -= B(-TINE_OUT - 1, -TINE_OUT + 1.6, -8, 8, zb, zb + 6)
    f -= ch
    f -= B(-TINE_OUT - 7, -TINE_IN + 7, -4, 4, z1 - 0.01, z1 + 6)          # power cable through the tine root
    # Dec motor bracket: plate parallel to the tine, gussets on the outside
    bx0, bx1 = BRACKET_X
    f += B(bx0, bx1, -24, 24, z1 - 0.01, DEC_H - 20)
    for y in (-24, 21.5):
        tri = poly((0, 0), (9.5, 0), (0, 14))
        f += Pos(bx1, y + 2.5, z1) * Rot(90, 0, 0) * extrude(tri, 2.5)
    f -= teardrop_x(BYJ_BOSS[0] + 1.0, bx0 - 1, bx1 + 1, z=DEC_H - CD)
    for y in (-BYJ_EARS / 2, BYJ_EARS / 2):
        f -= teardrop_x(BYJ_EAR_HOLE, bx0 - 1, bx1 + 1, y=y, z=DEC_H - CD + BYJ_OFFSET)
    # spindle bore
    f -= cyl_z(JOURNAL_D / 2 + CLEAR, z0 - 1, z1 + 1)
    # RA motor: pocket for the face and ears (2 deep, from below), boss hole, ear pin holes
    sx, sy = RA_SHAFT
    cx = sx - BYJ_OFFSET
    pocket = cyl_z(BYJ_R + 0.3, z0 - 1, RA_FACE, x=cx)
    pocket += B(cx - BYJ_EAR_W / 2 - 0.3, cx + BYJ_EAR_W / 2 + 0.3, -BYJ_EARS / 2, BYJ_EARS / 2, z0 - 1, RA_FACE)
    for y in (-BYJ_EARS / 2, BYJ_EARS / 2):
        pocket += cyl_z(BYJ_EAR_W / 2 + 0.3, z0 - 1, RA_FACE, x=cx, y=y)
        pocket += cyl_z(BYJ_EAR_HOLE / 2 - 0.1, z0 - 1, z1 + 1, x=cx, y=y)
    pocket += cyl_z(BYJ_BOSS[0] / 2 + 0.5, z0 - 1, z1 + 1, x=sx, y=sy)
    f -= pocket
    # ULN2003 deck: a grooved rib and three slotted posts hold two boards on edge
    ux0, ux1 = ULN_X - ULN[2] - 0.15 - 2.0, ULN_X + 0.15 + 2.0          # rib, 2 mm walls each side of the groove
    gx0, gx1 = ULN_X - ULN[2] - 0.15, ULN_X + 0.15
    f += B(ux0 - 1, ux1 + 1, -41, 41, z1 - 0.01, z1 + 4)
    for y0, y1 in ((-41.5, -35.0), (-3.0, 3.0), (35.0, 41.5)):
        f += B(ux0 - 1, ux1 + 1, y0, y1, z1 - 0.01, z1 + 22)
    f -= B(gx0, gx1, -ULN_Y - ULN[0] / 2 - 0.5, ULN_Y + ULN[0] / 2 + 0.5, z1 + 0.5, z1 + 30)   # groove + post slots
    return f


def pinion():
    """12 teeth on the 28BYJ-48's double-D shaft (5 mm, 3 mm flats). Press fit; a drop of CA if loose."""
    return PINION.solid(0, PIN_LEN) - double_d_bore(-1, PIN_LEN + 1)


def dec_wheel():
    w = WHEEL.solid(0, DEC_WHEEL_X[1] - DEC_WHEEL_X[0])
    return w - hex_z(16 + 2 * FIT, -1, 10, phase=90)


def push_pin(grip):
    """Split push pin, Ø3.9 through a Ø4.2 ear and a Ø4.2 hole, `grip` mm of material. Local axis z,
    head at z < 0. Flats at y = ±1.6 so it prints lying on one (strong across the shank)."""
    p = cyl_z(3.75, -1.2, 0) + cyl_z(1.95, 0, grip) + Pos(0, 0, grip) * Cone(2.4, 1.6, 2.0, align=CCM)
    p -= B(-0.6, 0.6, -5, 5, grip * 0.35, grip + 3)                          # slot: two prongs
    return p & B(-5, 5, -1.6, 1.6, -2, grip + 3)


# ---------- Dec group: head (head frame) ----------

def dec_stub():
    """Right (+x) Dec stub: hex key into the head, journal in the tine, shoulder, hex for the wheel.
    Local axis z = head +x, z = 0 at the head's side face (x = 54)."""
    s = hex_z(SOCK_AF, SOCK_X - HX, 0, phase=90)        # corners on head ±z, as the socket
    s += cyl_z(STUB_D / 2, 0, DEC_WHEEL_X[0] - HX)
    s += hex_z(16, DEC_WHEEL_X[0] - HX - 0.01, DEC_WHEEL_X[1] - HX, phase=90)
    return s


def cable_stub():
    """Left (-x) stub, hollow for the 10-wire ribbon: flange outside the tine, journal, hex key, and a
    round end with a groove for a circlip inside the head. Local z = head -x, z = 0 at x = -54."""
    s = cyl_z(15, TINE_OUT - HX, TINE_OUT - HX + 2)
    s += cyl_z(STUB_D / 2, 0, TINE_OUT - HX + 0.01)
    s += hex_z(SOCK_AF, SOCK_X - HX, 0.01, phase=90)
    s += cyl_z(8.5, SOCK_X - HX - 4, SOCK_X - HX + 0.01)
    s -= cyl_z(9, SOCK_X - HX - 1.4, SOCK_X - HX) - cyl_z(7.5, SOCK_X - HX - 1.4, SOCK_X - HX)
    s -= cyl_z(6, -20, 20)
    return s


def head_body():
    """The box: Pi on pegs off the front wall, camera behind the lens window, hex sockets in two
    side bosses. Prints front face down; the open back is closed by the lid."""
    outer = fillet(B(-HX, HX, BACK, HY, -HZ, HZ).edges().filter_by(Axis.Y), 4)
    inner = fillet(B(-HX + WALL, HX - WALL, BACK - 1, FRONT_IN, -HZ + WALL, HZ - WALL).edges().filter_by(Axis.Y), 1.6)
    h = outer - inner
    for s in (-1, 1):                                                     # side bosses, down to the front wall
        x0, x1 = sorted((s * SOCK_X, s * (HX - WALL + 0.01)))
        h += B(x0, x1, -12.5, FRONT_IN + 0.01, -14, 14)
        h -= Pos(min(s * SOCK_X, s * HX) - (1 if s < 0 else 0), 0, 0) * hex_x(SOCK_AF + 2 * FIT, 0, HX - SOCK_X + 1)
    # Pi standoffs with pegs (Pi holes are 2.75)
    for x, z in PI_HOLES:
        h += Pos(x, 0, z) * Rot(-90, 0, 0) * (cyl_z(3.0, PI_Y, FRONT_IN + 0.01) + cyl_z(1.2, PI_Y - 2.0, PI_Y))
    # camera: 0.8 standoffs with Ø1.9 pegs (holes 2.2), window for the lens module
    for x, z in CAM_HOLES:
        h += Pos(x, 0, z) * Rot(-90, 0, 0) * (cyl_z(2.0, CAM_Y, FRONT_IN + 0.01) + cyl_z(0.95, CAM_Y - 1.8, CAM_Y))
    h -= B(-LENS_SQ / 2 - 0.35, LENS_SQ / 2 + 0.35, FRONT_IN - 1, HY + 1, -LENS_SQ / 2 - 0.35, LENS_SQ / 2 + 0.35)
    # dowel bosses for the hood (filament pins)
    for x, z in DOWELS:
        h += Pos(x, 0, z) * Rot(-90, 0, 0) * cyl_z(2.6, 12.1, FRONT_IN + 0.01)
        h -= Pos(x, 0, z) * Rot(-90, 0, 0) * cyl_z(FIL_HOLE / 2, 12.6, HY + 1)
    # servo wire into the head
    h -= B(24.5, 28.5, FRONT_IN - 1, HY + 1, 16, 24.5)
    # windows for the lid's snap hooks
    for s in (-1, 1):
        z0, z1 = sorted((s * (HZ - WALL - 0.5), s * (HZ + 1)))
        h -= B(-6.5, 6.5, -8.4, -6.1, z0, z1)
    return h


def head_lid():
    """Back lid: lip into the opening, two snap hooks, four posts that clamp the Pi onto its pegs,
    and two grooved ribs that hold the IMU and compass boards on edge. Prints outer face down."""
    lid = fillet(B(-HX, HX, -HY, BACK, -HZ, HZ).edges().filter_by(Axis.Y), 4)
    lip = B(-HX + WALL + 0.2, HX - WALL - 0.2, BACK - 0.01, BACK + 3, -HZ + WALL + 0.2, HZ - WALL - 0.2)
    lip -= B(-HX + WALL + 1.8, HX - WALL - 1.8, BACK - 1, BACK + 4, -HZ + WALL + 1.8, HZ - WALL - 1.8)
    for s in (-1, 1):                                                     # gaps in the lip for the hooks
        z0, z1 = sorted((s * (HZ - WALL - 2.5), s * HZ))
        lip -= B(-7.5, 7.5, BACK - 1, BACK + 4, z0, z1)
    lid += lip
    for s in (-1, 1):                                                     # snap hooks: 1.4 tab, 0.6 hook
        zi = s * (HZ - WALL - 0.2)                                        # tab's outer face
        z0, z1 = sorted((zi, zi - s * 1.4))
        lid += B(-6, 6, BACK - 0.01, -6.3, z0, z1)
        # hook in the (y, z) plane, extruded along x: catch face towards the lid, ramp on the leading side
        hook = poly((-8.3, zi), (-8.3, zi + s * 0.6), (-7.5, zi + s * 0.6), (-6.3, zi))
        lid += frame((-6, 0, 0), (0, 1, 0), (1, 0, 0)) * extrude(hook, 12)
    for x, z in PI_HOLES:                                                 # clamp posts (hollow for the peg tips)
        post = cyl_z(2.3, BACK - 0.01, PI_Y - 1.4 + 0.1) - cyl_z(1.5, PI_Y - 4, PI_Y)
        lid += Pos(x, 0, z) * Rot(-90, 0, 0) * post
    for x0, x1 in ((-28, -4), (2, 24)):                                   # sensor ribs, 1.7 groove
        lid += B(x0, x1, BACK - 0.01, BACK + 4, -10, -6) - B(x0 - 1, x1 + 1, BACK + 1, BACK + 5, -8.85, -7.15)
    return lid


def hood():
    """Dew/stray-light hood sized to the field (53.5° × 41.4° plus 1.5°), and the box the lens-cap
    servo drops into. Two filament pins locate it on the head. Prints plate down."""
    y0, y1 = HY, SERVO_FLOOR
    plate = fillet(B(-21, 31, y0, y1, -19, 29.5).edges().filter_by(Axis.Y), 3)
    # frustum shell: inner half-sizes from (6, 5) at the plate to the field's size at the mouth
    lens_y = HY + 1.8
    L = HOOD_END - lens_y
    wx = 2.0 + L * math.tan(math.radians(FOV_H / 2 + 0.75))
    wz = 2.0 + L * math.tan(math.radians(FOV_V / 2 + 0.75))
    def frustum(a0, b0, a1, b1, pad=0.0):
        """Rectangular frustum from y1 to the mouth; pad extends it past both ends (for cutting)."""
        from build123d import Rectangle, loft
        k = pad / (HOOD_END - y1)
        ends = [(y1 - pad, a0 - (a1 - a0) * k, b0 - (b1 - b0) * k), (HOOD_END + pad, a1 + (a1 - a0) * k, b1 + (b1 - b0) * k)]
        return loft([Plane(origin=(0, y, 0), x_dir=(1, 0, 0), z_dir=(0, 1, 0)) * Rectangle(2 * a, 2 * b) for y, a, b in ends])
    shell = frustum(6 + 1.6, 5 + 1.6, wx + 1.6, wz + 1.6) - frustum(6, 5, wx, wz, pad=1)
    h = plate + shell
    h -= B(-5, 5, y0 - 1, y1 + 1, -5, 5)                                  # aperture
    # servo box: walls up to the ears; thick end walls take the SG90's own screws
    sx, sz = SERVO
    bx0, bx1 = sx - 6.2, sx + 17.0
    bz0, bz1 = sz - 6.3, sz + 6.3
    ear_y = y1 + 15.9
    box = B(bx0 - 5, bx1 + 5, y1 - 0.01, ear_y, bz0 - 1.6, bz1 + 1.6) - B(bx0, bx1, y1 - 1, ear_y + 1, bz0, bz1)
    h += box
    h -= frustum(6, 5, wx, wz, pad=1)                                     # keep the field clear of the box
    for x in (sx - 6.0 - 2.35, sx + 16.8 + 2.35):
        h -= Pos(x, 0, sz) * Rot(90, 0, 0) * cyl_z(0.9, -ear_y - 1, -ear_y + 8)
    h -= B(24.5, 28.5, y0 - 1, y1 + 4, 16, 24.5)                          # wire slot into the head
    for x, z in DOWELS:
        h -= Pos(x, 0, z) * Rot(-90, 0, 0) * cyl_z(FIL_HOLE / 2, y0 - 1, y1 + 1)
    return h, (wx, wz)


def lens_cap():
    """Cap on an arm, pressed onto the SG90 spline and held by the horn screw. Closed it shades the
    hood mouth for dark frames; the servo swings it 180° clear. Local: shaft on z, cap plate z 0..1.6
    (just in front of the hood mouth), hub z 2.9..8 in front of the servo's round top."""
    sx, sz = SERVO
    L = HOOD_END - HY - 1.8
    hw = 2.0 + L * math.tan(math.radians(FOV_H / 2 + 0.75)) + 1.6 + 1.5
    hh = 2.0 + L * math.tan(math.radians(FOV_V / 2 + 0.75)) + 1.6 + 1.5
    cx, cy = -sx, sz                       # cap centre from the shaft; local y = head -z (see build())
    c = fillet(B(cx - hw, cx + hw, cy - hh, cy + hh, 0, 1.6).edges().filter_by(Axis.Z), 3)
    ang = math.degrees(math.atan2(cy, cx))
    arm = Rot(0, 0, ang) * B(0, math.hypot(cx, cy), -3.5, 3.5, 0, 4.6)
    arm -= cyl_z(6.6, -1, 2.9)             # clear of the servo's round top
    c += arm + cyl_z(4.0, 2.9, 8.0)
    c -= cyl_z(6.6, -1, 2.9) & cyl_z(6.6, -1, 2.9)
    c -= cyl_z(2.3, 2.8, 6.5) + cyl_z(1.0, 2.0, 9)                         # spline bore (press) + screw
    return c


# ---------- bought parts (for the viewer and the clearance checks) ----------

def byj48():
    b = Pos(0, -BYJ_OFFSET, 0) * (cyl_z(BYJ_R, -BYJ_DEPTH, 0))
    ears = B(-BYJ_EARS / 2, BYJ_EARS / 2, -BYJ_OFFSET - BYJ_EAR_W / 2, -BYJ_OFFSET + BYJ_EAR_W / 2, -0.8, 0)
    for x in (-BYJ_EARS / 2, BYJ_EARS / 2):
        ears += cyl_z(BYJ_EAR_W / 2, -0.8, 0, x=x, y=-BYJ_OFFSET)
        ears -= cyl_z(BYJ_EAR_HOLE / 2, -2, 1, x=x, y=-BYJ_OFFSET)
    b += ears
    b += cyl_z(BYJ_BOSS[0] / 2, 0, BYJ_BOSS[1])
    b += (cyl_z(BYJ_SHAFT / 2, 0, BYJ_SHAFT_LEN) & B(-3, 3, -BYJ_FLATS / 2, BYJ_FLATS / 2, 0, BYJ_SHAFT_LEN)) + cyl_z(BYJ_SHAFT / 2, 0, BYJ_SHAFT_LEN - 6)
    b += B(-7.5, 7.5, -BYJ_OFFSET - BYJ_R - 3.5, -BYJ_OFFSET - BYJ_R + 3, -BYJ_DEPTH + 2, -1)   # wire cover
    return b


def pi3b():
    """Board centred at the origin, component side +z, GPIO along +y, USB/Ethernet at +x."""
    p = B(-42.5, 42.5, -28, 28, 0, 1.4)
    for x, y in PI_HOLES:
        p -= cyl_z(1.375, -1, 2, x=x, y=y)
    p += B(23, 44.6, -26, -10, 1.4, 14.9)                                  # Ethernet
    p += B(27, 44.6, -7.5, 6, 1.4, 17.4) + B(27, 44.6, 9.5, 23, 1.4, 17.4)  # USB
    p += B(-35.4, 15.4, 21.5, 26.5, 1.4, 9.9)                              # GPIO header
    p += B(-12, 3, -28, -20, 1.4, 7.9)                                     # HDMI
    p += B(-8, 14, -23, -18, 1.4, 6.9)                                     # CSI
    p += B(-20, -6, -8, 6, 1.4, 2.6)                                       # SoC
    return p


def dupont_block():
    """The jumpers on the GPIO header (straight housings, 14 mm), as a keep-out."""
    return B(-35.4, 15.4, 21.5, 26.5, 9.9, 23.9)


def cam_v1():
    c = B(-12.5, 12.5, -14.5, 9.5, -1.0, 0)
    for x, y in CAM_HOLES:
        c -= cyl_z(1.1, -2, 1, x=x, y=y)
    c += B(-LENS_SQ / 2, LENS_SQ / 2, -LENS_SQ / 2, LENS_SQ / 2, 0, 3.2) + cyl_z(3.0, 3.2, 5.0)
    c += B(-10, 10, -14.5, -9.5, -3.0, -1.0)                               # FFC connector (back)
    return c


def uln2003():
    """Board with its bottom edge at y = 0, solder side z = 0, components +z."""
    u = B(-ULN[0] / 2, ULN[0] / 2, 0, ULN[1], 0, ULN[2])
    u += B(-10, 6, 6, 26, ULN[2], ULN[2] + 5)                              # ULN2003 DIP
    u += B(8, 16, 4, 28, ULN[2], ULN[2] + 6)                               # JST + LEDs
    u += B(-16, -10, 10, 22, ULN[2], ULN[2] + 8.5)                         # IN1-4 pins
    return u


def sg90():
    """Shaft on z at the origin, bottom of the case z = 0."""
    s = B(-6.0, 16.8, -6.1, 6.1, 0, 22.7)
    s += B(-10.7, 21.5, -6.1, 6.1, 15.9, 18.4)
    s += cyl_z(5.9, 22.7, 26.7) & B(-6.0, 6, -6.1, 6.1, 22.7, 26.7)
    s += cyl_z(2.4, 26.7, 30.0)
    return s


def sensor_board(w, h):
    return B(-w / 2, w / 2, 0, h, 0, 1.6)


# ---------- assembly ----------

def build():
    """Every part, placed in its group's frame. Returns {group: {name: (shape, kind)}}."""
    hood_shape, _ = hood()
    fixed = {
        "foot": (foot(), "print"),
        "hub": (MOUNT * hub(), "print"),
        "ra_wheel": (MOUNT * Pos(0, 0, WHEEL_Z[0]) * ra_wheel(), "print"),
        "ra_clip": (MOUNT * Pos(0, 0, GROOVE[0] + 0.1) * circlip(GROOVE_D, 27), "print"),
    }
    sx, sy = RA_SHAFT
    ph = phase_to_mesh(WHEEL, (0, 0), 0.0, PINION, (sx, sy))
    ra = {
        "fork": (fork(), "print"),
        "ra_pinion": (Pos(sx, sy, WHEEL_Z[0]) * Rot(0, 0, math.degrees(ph)) * pinion(), "print"),
        "ra_motor": (Pos(sx, sy, RA_FACE) * Rot(0, 0, -90) * byj48(), "bought"),
        "dec_motor": (frame((BRACKET_X[1], 0, DEC_H - CD), (0, 1, 0), (-1, 0, 0)) * byj48(), "bought"),
        "dec_pinion": (frame((DEC_WHEEL_X[0] + 1.4 + PIN_LEN, 0, DEC_H - CD), (0, 1, 0), (-1, 0, 0)) * pinion(), "print"),
        # boards on edge: local y up, components (local +z) towards -x, solder side at ULN_X
        "uln_ra": (frame((ULN_X, -ULN_Y, PLATE[1] + 0.6), (0, -1, 0), (-1, 0, 0)) * uln2003(), "bought"),
        "uln_dec": (frame((ULN_X, ULN_Y, PLATE[1] + 0.6), (0, -1, 0), (-1, 0, 0)) * uln2003(), "bought"),
    }
    head = {
        "head_body": (head_body(), "print"),
        "head_lid": (head_lid(), "print"),
        "hood": (hood_shape, "print"),
        "dec_stub": (frame((HX, 0, 0), (0, 1, 0), (1, 0, 0)) * dec_stub(), "print"),
        "cable_stub": (frame((-HX, 0, 0), (0, 1, 0), (-1, 0, 0)) * cable_stub(), "print"),
        "dec_wheel": (frame((DEC_WHEEL_X[0], 0, 0), (0, 1, 0), (1, 0, 0)) * dec_wheel(), "print"),
        "stub_clip": (frame((-SOCK_X, 0, 0), (0, 1, 0), (1, 0, 0)) * circlip(15.0, 21), "print"),
        "lens_cap": (frame((SERVO[0], HOOD_END + 0.3, SERVO[1]), (1, 0, 0), (0, 1, 0)) * lens_cap(), "print"),
        "pi": (frame((0, PI_Y, 0), (1, 0, 0), (0, -1, 0)) * pi3b(), "bought"),
        "jumpers": (frame((0, PI_Y, 0), (1, 0, 0), (0, -1, 0)) * dupont_block(), "bought"),
        "camera": (frame((0, CAM_Y, 0), (-1, 0, 0), (0, 1, 0)) * cam_v1(), "bought"),
        "servo": (frame((SERVO[0], SERVO_FLOOR, SERVO[1]), (1, 0, 0), (0, 1, 0)) * sg90(), "bought"),
        "imu": (frame((-16, BACK + 1.0, -8 - 0.8), (1, 0, 0), (0, 0, 1)) * Pos(0, 0, 0) * sensor_board(13, 18), "bought"),
        "compass": (frame((13, BACK + 1.0, -8 - 0.8), (1, 0, 0), (0, 0, 1)) * sensor_board(14, 18), "bought"),
    }
    return {"fixed": fixed, "ra": ra, "head": head}


PRINTED = ["foot", "hub", "ra_wheel", "ra_clip", "fork", "ra_pinion", "dec_pinion", "head_body", "head_lid",
           "hood", "dec_stub", "cable_stub", "dec_wheel", "stub_clip", "lens_cap"]


COLORS = {"print": (0.93, 0.55, 0.22), "print2": (0.25, 0.55, 0.85), "bought": (0.45, 0.48, 0.52)}
ACCENT = {"pi": (0.15, 0.55, 0.3), "camera": (0.15, 0.5, 0.3), "uln_ra": (0.15, 0.35, 0.75), "uln_dec": (0.15, 0.35, 0.75),
          "ra_motor": (0.75, 0.75, 0.78), "dec_motor": (0.75, 0.75, 0.78), "servo": (0.2, 0.4, 0.85),
          "imu": (0.6, 0.2, 0.6), "compass": (0.6, 0.2, 0.6), "jumpers": (0.15, 0.15, 0.15)}
SECOND = {"hub", "ra_wheel", "ra_pinion", "dec_pinion", "dec_wheel", "dec_stub", "cable_stub", "head_lid", "lens_cap",
          "ra_clip", "stub_clip"}


def print_pose(name, shp):
    """The part as it lies on the bed (z = 0 up), from its placed shape."""
    from build123d import Location
    poses = {
        # fixed: foot as is; the rest back into the mount frame, then per part
        "foot": lambda s: s,
        "hub": lambda s: Pos(0, 0, -KEY_Z[0]) * MOUNT.inverse() * s,
        "ra_wheel": lambda s: MOUNT.inverse() * s,
        "ra_clip": lambda s: MOUNT.inverse() * s,
        "fork": lambda s: s,
        "ra_pinion": lambda s: s,
        "dec_pinion": lambda s: Rot(0, 90, 0) * s,
        "head_body": lambda s: Rot(-90, 0, 0) * s,          # front face down
        "head_lid": lambda s: Rot(90, 0, 0) * s,            # outer face down
        "hood": lambda s: Rot(90, 0, 0) * s,                # plate down
        "dec_stub": lambda s: Rot(0, -90, 0) * s,           # inner hex end down
        "cable_stub": lambda s: Rot(0, -90, 0) * s,         # flange down
        "dec_wheel": lambda s: Rot(0, -90, 0) * s,
        "stub_clip": lambda s: Rot(0, -90, 0) * s,
        "lens_cap": lambda s: Rot(90, 0, 0) * s,            # cap plate down
    }
    s = poses[name](shp)
    bb = s.bounding_box()
    return Pos(-bb.center().X, -bb.center().Y, -bb.min.Z) * s


def write_viewer(glbs, html):
    """A page that opens from Finder: the three groups' GLBs embedded as base64."""
    data = {k: base64.b64encode(v.read_bytes()).decode() for k, v in glbs.items()}
    page = VIEWER
    for k, v in data.items():
        page = page.replace(f"__{k.upper()}__", v)
    page = page.replace("__TILT__", str(TILT)).replace("__HC__", str(HC)).replace("__DECH__", str(DEC_H))
    html.write_text(page)


VIEWER = (Path(__file__).parent / "viewer_template.html").read_text() if (Path(__file__).parent / "viewer_template.html").exists() else ""


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "stl").mkdir(exist_ok=True)
    groups = build()
    glbs = {}
    for g, parts in groups.items():
        children = []
        for name, (shp, kind) in parts.items():
            c = shp.moved(Location())
            col = ACCENT.get(name) or COLORS["print2" if name in SECOND else kind]
            c.color = Color(*col)
            c.label = name
            children.append(c)
            if kind == "print":
                pp = print_pose(name, shp)
                export_stl(pp, str(OUT / "stl" / f"{name}.stl"), tolerance=0.01, angular_tolerance=0.2)
        asm = Compound(label=g, children=children)
        glbs[g] = OUT / f"{g}.glb"
        export_gltf(asm, str(glbs[g]), binary=True, linear_deflection=0.05, angular_deflection=0.4)
        export_step(asm, str(OUT / f"{g}.step"))
    for name, grip in (("push_pin_ra", RA_FACE - PLATE[0] + 2.0), ("push_pin_dec", 5.0)):   # 2 of each
        pin = Rot(90, 0, 0) * push_pin(grip)                               # lying on a flat
        bb = pin.bounding_box()
        export_stl(Pos(0, 0, -bb.min.Z) * pin, str(OUT / "stl" / f"{name}.stl"), tolerance=0.01, angular_tolerance=0.2)
    write_viewer(glbs, OUT / "tinyscope.html")
    print(f"STL → {OUT / 'stl'}, viewer → {OUT / 'tinyscope.html'}")


if __name__ == "__main__":
    main()
