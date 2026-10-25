# tinyscope CAD (build123d)

    pip install -r cad/requirements.txt                 # build123d, bd_warehouse
    python cad/tinyscope.py                             # ~15 s → cad/out/
    python cad/test_pieces.py                           # ~1 min → cad/out/stl/test/ (print these first)
    python cad/test_tinyscope.py                        # ~15 min (clearance sweep, ~3 GB RAM); --print-only: ~1 min

Open `cad/out/tinyscope.html` by double-clicking it. The model is embedded in the page and
has sliders for hour angle and Dec, plus the camera's field drawn as a yellow pyramid. STLs
come out in `cad/out/stl/`, already in print orientation; STEP files hold the three groups.
`bd_warehouse` provides the tripod thread. `spur_gear.py` makes the involute spur gears.

## Parts

| Part | Qty | Print as | Material | Notes |
| --- | --- | --- | --- | --- |
| `foot` | 1 | foot down | PLA/PETG, 4 walls | printed 1/4"-20 thread: 0.2 mm layers, test with your tripod screw first |
| `hub` | 1 | hex key down | PETG, 4 walls, 40% | RA journal Ø28; filament pin through the column holds it |
| `ra_wheel`, `dec_wheel` | 1 + 1 | flat | PLA/PETG | 60 T module 1 |
| `ra_pinion`, `dec_pinion` | 2 | flat | PETG, 100% | double-D bore 5/3 mm; press on, CA if loose |
| `fork` | 1 | plate down | PLA/PETG, 4 walls | the big one; bridges: motor pocket (from below), cable tunnel, channel bridges |
| `head_body` | 1 | front face down | PLA/PETG | camera pegs can be heat-staked |
| `head_lid` | 1 | outer face down | PETG (snap hooks) | posts clamp the Pi |
| `hood` | 1 | plate down | any, black if you can | sized to the field +1.5° |
| `lens_cap` | 1 | cap down | any, black | press on the SG90 spline, horn screw |
| `dec_stub`, `cable_stub` | 1 + 1 | axis vertical | PETG, 100% | Dec journals Ø22 |
| `ra_clip`, `stub_clip` | 1 + 1 | flat | PETG | printed circlips |
| push pins | 2 + 2 | lying on a flat | PETG | motor ears; or M3 × 10 screws |

Filament: ~365 cm³ of solid, so roughly 180–220 g at normal walls and infill (the foot is
over a third of it; a heavier foot steadies the tripod).

## Assembly

1. Hub into the column (cone and hex), then a 1.75 mm filament pin across through the hole
   (cut flush). Thread the power lead up through the foot's groove, the column and the hub.
2. Fork onto the spindle (Vaseline on the journal and the flange), RA wheel onto the hex, then
   the circlip. RA motor into the pocket under the plate with its pinion on, so the pinion
   meshes as the motor goes in; push pins from below.
3. ULN2003 boards into the deck slots, components outward.
4. Head: camera onto its pegs, ribbon folded round the Pi's lower edge to the CSI connector,
   Pi onto its pegs. IMU into the lid's groove (the second groove is for an optional compass). Jumpers onto the GPIO.
5. Head between the tines. Dec stub in from the right, Dec wheel on its hex. Cable stub in from
   the left, circlip on inside the head. Lid on (snap).
6. Dec motor on the bracket with its pinion on, so the pinion meshes; push pins.
7. Hood onto the front with two filament pins, servo into its box (its own screws), cap on
   the spline with the servo at the "closed" end.

## Frames and numbers

See the docstring of `tinyscope.py`. In short: world (tripod, +y north), mount (z = polar
axis), head (x = Dec axis, y = optical axis); `head_loc(dec)` with dec = 90 at the pole.
Gears: 60:12 module 1 on both axes, centre distance 36. Dec axis 58 mm above the column top,
chosen from the head's swing (the check reports the closest pass).

## Checks (`test_tinyscope.py`)

- every printed part prints without supports; the bridges it accepts are listed in `ALLOWED`
  with a reason, and a stale entry fails;
- every part fits a 256 mm bed;
- the head clears the fork, wheel, clip and hub from Dec −35° to 100°;
- the fork, motors, boards and head (at three Dec angles) clear the foot through a full RA turn;
- nothing that turns comes lower than 12 mm above the tripod plate;
- gear centre distance and the step size quoted in the README.
