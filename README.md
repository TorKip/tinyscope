# Tinyscope - et grunnarbeids-prosjekt.

Grunnet tidsklemma brukes KI flittig i dette prosjektet, det kan derfor virke noe verbost. Men la deg ikke bekymre, prosjektet er mitt, fullt og helt og drevet fremover av meg og min innsikt (eller mangel derpå).

Målet med prosjektet er å bygge forståelse for meg selv, og forhåpentligvis tilby noe nyttig til andre som kunne tenke seg å lære om astronomi, astrofoto, teleskop, montering, kameraer og styringssystemer.

Velkommen!

Jeg ønsker å lage et fullt funksjonelt robotisk observatorium og forstå godt hvordan disse fungerer.
Den første iterasjonen blir en veldig enkel, 3d-printet eq-montering med en raspberry pi og tilhørende enkelt kamera. Det skal likevel være "fullt" kontrollerbart og automatisk, selv om jeg allerede før jeg har begynt antar at bildene kommer til å bli så som så.

Første iterasjon heter altså tinyscope, og jeg håper å lære veldig mye av dette teleskopet.
Kostnaden vil være minimal, selv om en raspberry pi er dyr for tiden hadde jeg denne fra før, med kameraet inkludert.

# tinyscope — the smallest robotic sky camera that still works

*Started 2026-10-22. Goals: [GOALS.md](GOALS.md). Software:
[docs/software.md](docs/software.md). Building it: [docs/bom.md](docs/bom.md)
and [docs/print-plan.md](docs/print-plan.md).*

*Written with a lot of help from an AI assistant (Claude); the project, its
decisions and its mistakes are mine.*

## The idea

A fork-mounted Raspberry Pi 3B + Pi camera v1 (OV5647, "v1.2/1.3") on a printed
equatorial wedge, on an ordinary levelled tripod. Pi and camera live in one printed
unit; only power has to be routed, and Wi-Fi does the rest. 2–4 × 28BYJ-48 +
ULN2003, SG90 servos as needed, a GY-BMI160 IMU and optionally a GY-271 (QMC5883L)
compass. Controlled over the local network from KStars/Ekos.
Goals: **almost no setup time, almost no cost** (I already had the Pi and the
camera), and a **baseline** for what very limited hardware can do.
#goodEnough: find the limits myself, then decide whether the hobby earns a
better rig.

## What to expect, in one paragraph

With the stock lens this is a **wide-field sky camera**, not a telescope. One
pixel covers about 80″ and the frame is 53.5° × 41.4°, a bit more than the Big
Dipper. Expect constellations, the Milky Way in a dark sky, the Pleiades as a
small cluster, Andromeda and the Orion Nebula as smudges a few pixels across,
meteors, satellites, the ISS, and (from Norway) **aurora**, where the wide field
is a strength. Jupiter is one pixel and the Moon is about 22 pixels across. A
single frame reaches roughly the stars the eye sees from a suburb (mag 4–5.5).
A 15–20 minute stack reaches roughly mag 8–9. These are ±1 mag estimates from
the photon budget below; my own sky will set the real number.

## The surprising part: tracking barely matters for one frame

At 80″/px the sky drifts one pixel in **5.3 s** at the celestial equator, and
more slowly towards the pole. The OV5647's longest exposure is somewhere
between 1 s and 3.3 s: sources disagree, so **measuring it is task 1**. So an
untracked single frame from a fixed tripod looks almost the same as a tracked
one. What the mount does buy:

1. **GoTo and framing**: pick a target in KStars and it's in the frame.
2. **Long stacks with the full frame overlapping.** Untracked, the field slides
   1° every 4 minutes, so the overlap in a one-hour stack shrinks and the
   distorted corners mix in.
3. **A platform for later**: the same mount takes a better camera or lens
   without redesign. Narrower fields need the tracking that this one doesn't.
4. **The learning**: plate solving, pointing models and INDI drivers, on
   hardware that can't break anything expensive.

That makes a cheap first step possible. **Phase 0 is the camera on a tripod with
no mount**, which gives the baseline in one evening. The mount then shows what it
adds on top of that.

## Challenges and trade-offs

| # | Challenge | What it means | What the design does |
|---|---|---|---|
| 1 | **Exposure cap** (OV5647) | The hard limit on depth per frame. libcamera's tuning historically capped it far lower than the sensor can do | Measure first (phase 0). Stack many short frames; the mount keeps the field fixed for it |
| 2 | **1.2 mm aperture** (3.6 mm f/2.9) | Read-noise limited: faint stars need many frames | Stacking (Siril on the Mac). An M12 lens would be the one upgrade worth paying for (see *Purchases*) |
| 3 | **28BYJ-48 gearbox**: 1–3° backlash, ratio 63.684:1 (not 64), weak, slow | Pointing slop of about 0.2–0.6° at the axis after reversals; 0.5% rate error if you assume 64 | Printed 5:1 spur stage on both axes (backlash ÷5, torque ×5, 63.6″ per half-step = 0.8 px). Use the exact ratio. Finish GoTos in the tracking direction. Plate-solve and sync after each slew |
| 4 | **Printed plain bearings** instead of ball bearings | Some friction and a little slop; zero cost | Big journals (Ø28 RA, Ø22 Dec), 0.2 mm clearance, Vaseline. A little friction helps: it keeps the gear train loaded in one direction |
| 5 | **Balance** | Off-balance loads that flip side flip the backlash too | The Dec motor (right) balances the RA motor and ULN boards (left) within a few % |
| 6 | **Linux step timing** on the Pi | Jitter of a few ms | Irrelevant at sidereal rate (one half-step every 4.2 s); fine for slews at ~500 steps/s. Keep RA coils powered (half-steps drift when unpowered) |
| 7 | **Heat vs dew** | The Pi warms the sealed head by maybe 10–15 °C | **On purpose:** it's a free dew heater for a lens that would otherwise fog in Norwegian autumn. The cost is more sensor noise, which dark frames take care of: the servo cap closes for darks automatically. If the Pi throttles in summer (`vcgencmd measure_temp`), cut vents in the lid |
| 8 | **Cable wrap** | Power and the step ribbon twist as the axes turn | Power goes through the hollow polar axis and the ribbon through the hollow left Dec stub, so they twist rather than wrap. Software limits: RA ±150° from home, Dec −35°…100° |
| 9 | **Wi-Fi in the field** | Pi 3B: 2.4 GHz only | Home Wi-Fi in the garden; otherwise the Pi's own hotspot (NetworkManager) |
| 10 | **"N.I.N.A. or similar"** | N.I.N.A. is **Windows-only**; I'm on a Mac | **KStars/Ekos on the Mac** talking to **INDI on the Pi**. It's the native stack for a Pi rig, has a libcamera camera driver (`indi_libcamera`), plate solving and a polar alignment assistant. N.I.N.A. stays possible later through ASCOM Alpaca (a small Python Alpaca server on the Pi) |
| 11 | **Fixed wedge** | No latitude adjustment; mechanical polar alignment only as good as "arrow north, tripod level" | Fine here: 2–3° of misalignment drifts 10–20 px over a 30-minute stack, which stacking removes. Ekos's polar alignment assistant measures the error using the camera itself; the daemon can compensate in software (two-axis tracking). Another latitude = reprint the foot |
| 12 | **Self-levelling / north-finding** | Motorised alt/az adjusters (steppers 3 and 4) add two motors, four parts and a failure point, for an accuracy this camera doesn't need | **Not motorised.** The IMU in the head gives the camera's altitude and roll, so the mount homes itself without endstops and reports the tilt. No compass for now: near steppers expect ±3–5° at best, so a phone compass and the engraved arrow do as well, and the first plate solve does better. See [docs/alignment.md](docs/alignment.md) |
| 13 | **Unknown part dimensions** | Clone camera boards, ULN2003 boards and IMU boards vary | Parameters at the top of `cad/tinyscope.py`; print the small test pieces first ([docs/print-plan.md](docs/print-plan.md)) |

## The photon budget behind the magnitudes

Aperture area π·0.062² = 0.012 cm². A mag-0 star gives roughly 10⁶ photons/s/cm²
in the visible, so ~1.1·10⁴ photons/s reach the sensor. With ~25% net efficiency
(QE × Bayer × filter) that's ~2700 e⁻/s, spread over ~4 px. The sky is ~0.04
e⁻/s/px (dark site) to ~0.7 (suburb), so **read noise (~4 e⁻) dominates**.
Detection at SNR 5 then needs ~54 e⁻ per frame: mag ≈ 4.3 at 1 s and ≈ 5.4 at
3 s. Stacking N frames needs only 40/√N e⁻ per frame: mag ≈ 8.3 for 1000 × 1 s
and ≈ 8.9 for 300 × 3 s. A warm sensor's dark current lowers these.

## Purchases

**Almost none.** Everything is printed or already in the drawer, except the
IMU ([docs/bom.md](docs/bom.md)):

- Fasteners: printed push pins for the two motors (or M3 × 10 screws), **1.75 mm filament as dowel pins** (hub, hood), the screws that come
  with the SG90. The camera's pegs can be heat-staked with a soldering iron.
- Power: a USB power bank (≥ 2 A, 5 V).
- Wiring: F–F Dupont jumpers (often in the 28BYJ-48 kits), plus one spare USB-A
  cable cut and soldered to a small Y harness (Pi + two ULN boards).
- Lubricant: Vaseline.

**The one purchase worth considering later, and why.** An **M12 lens + M12
holder** for the OV5647 (a 6–8 mm f/1.4–1.6 CCTV lens, ~100–200 kr). The stock
lens's 1.2 mm aperture is the bottleneck. A 6 mm f/1.4 has a 4.3 mm aperture:
**~12× the light, about 2.7 magnitudes deeper per frame**. It also gives a
finer 48″/px, which is where the mount's tracking starts to matter. I'll only
buy it **after** phase 0–1 have shown the baseline: that's the point of the
project. If your camera is a clone with an M12 mount already (a square holder
with a threaded barrel), only the lens is needed.

## The design (CAD in `cad/`, see `cad/README.md`)

- **Foot** (wedge + pier in one, latitude 60°): 10 mm plate with a **printed
  1/4"-20 thread** for the tripod screw, an engraved north arrow, and a Ø43
  column leaning at 30° along the polar axis. The power cable runs up the
  hollow column.
- **Hub**: a hex-keyed spindle in the column, held by a filament pin. It is the
  RA journal; the **RA wheel** (60 teeth) is keyed on top and held by a printed
  circlip, which also holds the fork on.
- **Fork**: one print with the plate, two tines, the Dec motor bracket, a
  ribbon channel with two bridges on the left tine, and a deck for two ULN2003
  boards on edge (their LEDs show the stepping). The **RA motor** hangs under
  the plate and its pinion walks round the fixed wheel.
- **Head**: Pi 3B on pegs, clamped by the lid's posts (no screws); the camera
  behind a lens window; IMU and compass on edge in grooved ribs on the lid; two
  snap hooks. Hex sockets take the **Dec stub** (with the 60-tooth Dec wheel)
  and the hollow **cable stub**, held by a circlip inside.
- **Hood**: sized exactly to the 53.5° × 41.4° field (plus 1.5°), with the
  **SG90** in a box on top and a **lens cap** on its spline: darks with nobody there.

Movement: 5:1 on both axes → 20 380 half-steps per axis turn → 63.6″ per
half-step (0.8 px). Sidereal tracking = one half-step every 4.23 s. Slew at
~500 half-steps/s ≈ 9°/s.

## Power: header or USB?

As designed, power comes up the polar axis to the fork, and **the Pi gets 5 V
through its GPIO header**, on the same 10-wire ribbon as the step lines
(through the Dec stub). The two options:

| | GPIO header (as designed) | Micro-USB |
|---|---|---|
| Protection | **None**: the 5 V pin bypasses the Pi 3B's polyfuse and reverse-polarity protection. One swapped wire and the Pi is gone | Fuse and polarity protection; the plug only fits one way |
| Voltage drop | Slightly less (no socket and fuse in the path) | The socket and fuse cost ~0.1–0.2 V |
| Mechanics | One ribbon through the Dec stub, nothing new | A second cable with a bulky plug through the Dec stub and into the head: a CAD change |

**Decided (2026-10-22): the header**, and make the mistake hard: 5 V
and GND in one fixed 10-pin housing that is marked and glued as a block, and
a multimeter check before the first power-up. The motors and servo take their
5 V from the harness, not from the Pi's pins, so a stalled servo can't brown
out the Pi.

The real risk either way is **voltage drop**: the rig draws about 2 A peak,
and the thin wires in a cheap USB cable lose 0.5–1 V at that current. The
Pi warns about under-voltage below about 4.6 V. `mountd` logs
`vcgencmd get_throttled`, so the first sessions tell whether the cable is good
enough (a measurable hypothesis). Keep it short, and make it thicker if the log says so.

## Setup routine (target: under 3 minutes)

1. Tripod up and roughly level (its bubble, or a phone).
2. Screw the mount on, **arrow to north** (phone compass; ±5° is fine).
3. Plug in the power bank. The Pi boots and joins Wi-Fi (or starts its hotspot).
4. Mac: KStars → Ekos → connect. The mount homes from the IMU, takes a frame,
   plate-solves and syncs.
5. Optional: Ekos polar alignment (three frames) for a numeric error report.

Details and the guided/robotic alignment routine: [docs/alignment.md](docs/alignment.md).

## Software plan (details in [docs/software.md](docs/software.md))

- **Pi** (Raspberry Pi OS Lite 64-bit): `indiserver` with `indi_libcamera_ccd`
  for the camera, and a small Python **mount daemon** (`mountd`). The daemon
  steps both motors, homes from the IMU, does the pointing model, and speaks
  **LX200 over TCP** ([mountd/](mountd/README.md)). Ekos reaches it through an
  INDI LX200 driver (to check: that INDI's LX200 Basic connects over TCP), and
  SkySafari can talk LX200 over Wi-Fi directly.
- **Mac**: KStars/Ekos (imaging, plate solving with ASTAP or astrometry.net,
  polar alignment), Siril for stacking.
- **Later**: an ASCOM Alpaca endpoint for N.I.N.A. on Windows.

GPIO plan (BCM, physical pin): RA IN1–4 = 17, 27, 22, 23 (11, 13, 15, 16);
Dec IN1–4 = 24, 25, 5, 6 (18, 22, 29, 31); servo = 18 (12, hardware PWM);
I²C = 2, 3 (3, 5) for the IMU (+ IR sky sensor later) at 3.3 V (1); 5 V in on
pin 2, GND on pin 6; servo and motor 5 V from the harness, not the Pi's pins (see
*Power*).

## Build order

1. **Phase 0 (no printing):** Pi + camera on the tripod. Measure the longest
   exposure (`rpicam-still --shutter <µs> --gain 8 --raw`, check that the image
   really brightens), check focus on stars, stack 10 minutes in Siril. **That's
   the baseline.**
2. Test pieces and then the rest, in the order of
   [docs/print-plan.md](docs/print-plan.md).
3. Print and assemble; `mountd` first steps: slew by hand from a terminal.
4. INDI + Ekos; plate-solve and sync; first tracked stack. Compare with phase 0.
5. Extras: IMU homing, auto-darks with the cap, two-axis tracking.

## Decisions

Decided so far (the reasons are in the linked documents and [docs/adr/](docs/adr/)):

- **Software:** KStars/Ekos on the Mac (2026-10-22, [docs/software.md](docs/software.md)).
- **Protocol:** `mountd` speaks LX200 over TCP first ([ADR 0001](docs/adr/0001-lx200-first.md)).
- **Language:** `mountd` in Python first, then each slice in Go ([ADR 0002](docs/adr/0002-mountd-in-python-and-go.md)).
- **Self-levelling:** the IMU for homing and a tilt read-out; no motorised alt/az.
- **Compass:** left out for now; maybe later as an experiment.
- **Power:** through the GPIO header, with the under-voltage logged.

## Licence

Copyright © 2026 Tor Magne Kippersund.

Code (including the CAD scripts and `mountd`): GNU GPL v3 or later, see
[LICENSE](LICENSE). Photos and images: CC BY 4.0, see
[photos/README.md](photos/README.md).
