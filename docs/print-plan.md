# Print plan

*2026-10-23. Each stage ends with something you can test, so the next stage
starts from what the last one taught. Masses are solid volume × PLA density; with
normal walls and infill the real ones are lower (the foot most of all).*

## Before the first print

- [ ] **Measure your parts** and correct the parameters at the top of
      `cad/tinyscope.py` if they differ: the camera board's four holes
      (`CAM_HOLES`), the IMU (`IMU_BOARD`, `IMU_HOLES`), the ULN2003 board (`ULN`, drawn 35 × 32 × 1.6), the
      28BYJ-48's ear spacing (`BYJ_EARS`, 35) and shaft flats (`BYJ_FLATS`, 3).
      Then `python cad/tinyscope.py` and `python cad/test_pieces.py`.
- [ ] **Filament:** PETG for the parts marked below (strength, snap hooks,
      100 % infill); PLA or PETG for the rest; black for the hood and cap if
      you have it.
- [ ] The full clearance check (`cad/test_tinyscope.py`, ~15 min) passed on
      2026-10-28 (closest passes: head–fork 1.0 mm, fork–foot 3.0 mm); rerun it after
      changing any parameter.

## Print list

*Updated 2026-10-28.* Everything to print, with how many. "g" is solid mass in PLA; with
normal walls and infill the real mass is roughly half (about 180–220 g for the lot, ~455 g
solid). STLs are in `cad/out/stl/` (test pieces in `test/`), already in print orientation.
Status: what I know has been printed; **reprint** = the design changed after the print.

| Part | Qty | Material | g (solid) | Stage | Status |
|---|---|---|---|---|---|
| `thread_test` | 1 | PLA/PETG | 9.5 | 1 | ? |
| `ra_motor_test` | 1 | PLA/PETG | 9.9 | 1 | **reprint** (wire-cover notch, stepped bridges, 2026-10-28) |
| `uln_deck_test` | 1 | PLA/PETG | 12.8 | 1 | ? |
| `camera_test` | 1 | PLA/PETG | 2.4 | 1 | printed 2026-10-23, fits |
| `imu_test` | 1 | PLA/PETG | 1.3 | 1 | printing (peg version, 2026-10-28) |
| `push_pin_ra` | 2 | PETG | 0.1 each | 1 | |
| `ra_pinion` | 1 | PETG, 100 % | 0.6 | 1 | |
| `foot` | 1 | PLA/PETG, 4 walls | 170.4 | 2 | |
| `hub` | 1 | PETG, 4 walls, 40 % | 16.5 | 2 | **reprint** (pin slot, 2026-10-28) |
| `ra_wheel` | 1 | PLA/PETG | 17.0 | 2 | |
| `ra_clip` | 1 | PETG | 0.3 | 2 | |
| `fork` | 1 | PLA/PETG, 4 walls | 113.1 | 2 | |
| `head_body` | 1 | PLA/PETG | 56.4 | 3 | |
| `dec_stub` | 1 | PETG, 100 % | 8.7 | 3 | |
| `cable_stub` | 1 | PETG, 100 % | 6.5 | 3 | |
| `stub_clip` | 1 | PETG | 0.2 | 3 | |
| `dec_wheel` | 1 | PLA/PETG | 19.1 | 3 | |
| `dec_pinion` | 1 | PETG, 100 % | 0.6 | 3 | |
| `push_pin_dec` | 2 | PETG | 0.1 each | 3 | |
| `head_lid` | 1 | PETG (snap hooks) | 25.8 | 3 | after `imu_test` |
| `hood` | 1 | any, black | 15.0 | 4 | **reprint** (cable channel, 2026-10-28) |
| `lens_cap` | 1 | any, black | 2.7 | 4 | |

Per stage (solid): test pieces ~37 g, RA axis ~318 g, head and Dec ~117 g, hood and cap ~18 g.

## Stage 1: test pieces (~37 g, one plate)

From `cad/out/stl/test/` (made by `cad/test_pieces.py`), plus three real
small parts:

| Piece | Tests | Pass when |
|---|---|---|
| `thread_test` | the printed 1/4"-20 thread | it screws onto the tripod snugly, without wobble |
| `ra_motor_test` + 2 × `push_pin_ra` + `ra_pinion` | the motor pocket, ear holes, push pins, the pinion's press fit | the motor sits flat, the pins hold, the pinion grips the shaft |
| `uln_deck_test` | the ULN2003 slots | both boards slide in, stay put upside down, come out by hand |
| `camera_test` | the camera pegs and lens window | the board presses on and the lens sits centred |
| `imu_test` | the IMU's pegs and pads | the holes go over the pegs without forcing, the board lies flat on all three pads |

Adjust, regenerate, and reprint only what failed.

## What each big print waits for

The stages can overlap: a part is ready to print once the test it depends on
has passed.

| Part | Waits for |
|---|---|
| `foot` | `thread_test` (the hub's hex socket is a snug 0.15 mm fit; if it's tight, sand the hub, not the foot) |
| `hub`, `ra_wheel`, `ra_clip` | nothing |
| `head_body` | `camera_test` with your camera |
| `fork` | `ra_motor_test` and `uln_deck_test` with the real motors and boards |
| `head_lid` | `imu_test` with your IMU |
| `dec_stub`, `cable_stub`, `dec_wheel`, `hood`, `lens_cap` | nothing |

## Stage 2: the RA axis (~320 g solid)

`foot`, `hub` (PETG), `ra_wheel`, `ra_clip` (PETG), `fork`. Then assemble
steps 1–3 of `cad/README.md`.

**Test:** the fork turns smoothly by hand on the journal; the RA motor (from
stage 1) walks round the wheel when stepped from a terminal. This is the
first thing `mountd` can drive (S3 in docs/software.md), with only one axis.

## Stage 3: the head and the Dec axis (~120 g solid)

`head_body`, `dec_stub` (PETG, 100 %), `cable_stub` (PETG, 100 %),
`stub_clip` (PETG), `dec_wheel`, `dec_pinion` (PETG, 100 %), 2 ×
`push_pin_dec`. **`head_lid` (PETG) last, once `imu_test` has shown the
IMU's holes land on the pegs (`IMU_BOARD`, `IMU_HOLES`: from photos until measured).**

**Test:** both axes by hand through their full range (RA ±150°, Dec −35° to
100°) with the cables in: nothing catches, the ribbon doesn't pull.

## Stage 4: hood and lens cap (~18 g solid)

`hood`, `lens_cap`, black if possible. Not needed for first light; needed for
automatic darks.

## Why this order

The thread and the motor fit decide whether the two big prints (foot and
fork, about two thirds of the filament) come out right, so they're tested
first. The RA axis alone can already be stepped and made to track, so it's
a milestone worth stopping at, and `mountd` can start on it. The lid waits for
`imu_test`.
