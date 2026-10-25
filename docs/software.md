# tinyscope: software sketch

*2026-10-22. What's decided is listed at the end; the rest is a plan. It builds on the README's "Software plan" and is shaped by
[GOALS.md](../GOALS.md).*

## The stack, sky to Mac

Every robotic telescope, from tinyscope to a professional observatory, has the
same layers. Only the boxes at the bottom change from rung to rung.

```
 ┌─ Me ──────────────────────────────────────────────────────────────────┐
 │  "image M31 tonight, 2 h, when it's above 30°"                         │
 ├─ Scheduler / sequencer ──────── Ekos Scheduler (later: N.I.N.A. + Target Scheduler)
 │  picks the job, checks twilight + weather, runs startup/shutdown        │
 ├─ Services ───────────────────── plate solving (ASTAP / astrometry.net),
 │                                  focus, guiding (PHD2), polar alignment  │
 ├─ Client ─────────────────────── KStars/Ekos on the Mac                  │
 ├─ Device API (network) ───────── INDI (Linux/Mac)  |  ASCOM Alpaca (HTTP/JSON, any OS)
 ├─ Drivers ────────────────────── one per device: mount, camera, dome, weather …
 ├─ Device protocol ────────────── LX200 text commands, SynScan/EQMOD, USB camera …
 └─ Hardware ───────────────────── steppers, sensor, servo, IMU             │
```

| Rung | Mount driver | Camera | The rest |
|---|---|---|---|
| tinyscope | **our `mountd`**, speaking LX200 over TCP | `indi_libcamera` on the Pi | Ekos, ASTAP |
| EQ5 GoTo | INDI EQMod (EQDirect cable) or SynScan driver | whatever goes on it | same Ekos profile, new devices |
| LX200 10" | INDI LX200 driver over RS-232 → USB | same | same |
| Observatory | any of the above | cooled camera | + dome driver, weather/safety, scheduler running all night |

**Principle 2 in practice:** tinyscope's mount looks to Ekos like any LX200
mount. My Ekos setup, scheduler jobs and habits carry over to the EQ5 and
the LX200 unchanged, and when I later connect the real LX200 I'll already
know the protocol from the inside, because I implemented it.

## What we write vs what we reuse

Reuse almost everything. Only the part no one sells is ours:

- **Ours: `mountd`** on the Pi. Steps two 28BYJ-48s, tracks at sidereal rate,
  enforces cable limits, homes from the IMU, keeps a pointing model, closes the
  lens cap for darks, and logs everything.
- **Reused:** INDI server + `indi_libcamera` (camera), KStars/Ekos (client,
  scheduler, polar alignment), ASTAP or astrometry.net (plate solving), Siril
  (stacking).

### `mountd` shape: core + adapters

```
 LX200 over TCP ──┐                   ┌── GPIO steppers (real)
 (later) Alpaca ──┼──▶  core  ◀───────┼── fake steppers (tests, desk sim)
 (later) web UI ──┘   motion, model,  └── IMU, servo
                      limits, log
```

- The **core** knows nothing about protocols or GPIO. It's plain logic, so it
  can be developed test-first on the laptop (TDD).
- **Front-ends** translate a protocol into core calls. LX200 first; Alpaca
  later is just another adapter, and that one opens the door to N.I.N.A.
- **Back-ends** are the hardware. The fake one makes the whole mount run with
  no Pi: Ekos can slew a pretend tinyscope on the desk.

### Measuring with it (G3, G4)

The best measuring instrument is already in the loop: **the plate solve**.
After every slew Ekos solves the frame and syncs. The difference between where
`mountd` *thought* it pointed and where the sky says it points is the pointing
error, for free. `mountd` logs each one (time, commanded, solved, direction of
the last move, temperature) to a CSV per session. From that I can read:

- **Backlash**: the error jumps when the approach direction flips.
- **Gear ratio / rate error**: the error grows steadily while tracking.
- **Periodic error**: the error wobbles with the period of the 5:1 stage or
  the motor's gearbox.
- **Polar misalignment and flex**: the error depends on where in the sky the
  scope points.

The same CSV from the EQ5 or the LX200 later gives a fair comparison:
what a "good mount" buys, in arcseconds.

## Order of work (each step one evening or less)

| Step | Hardware needed | Result |
|---|---|---|
| S0 | **None.** KStars on the Mac with INDI's telescope + CCD simulators | The whole chain today: slew, simulated frames, plate solve, a scheduler job queue. A taste of the end goal at the kitchen table |
| S1 | Pi + camera on the tripod (= phase 0) | `indi_libcamera` in Ekos, the exposure cap measured, the first real plate solve, the baseline |
| S2 | None (laptop) | `mountd` core + LX200 adapter + fake back-end, tested; Ekos and SkySafari drive the fake mount |
| S3 | The printed mount | Real steppers; slew → solve → sync → track; the first pointing-error CSV |
| S4 | Mount, clear night | A scheduled sequence that runs with no hands; compare with the S1 baseline |
| Later | — | Alpaca adapter, IMU homing, auto-darks, two-axis tracking, the EQ5 and the LX200 in the same Ekos |

## Claims to check before relying on them

- That INDI's LX200 Basic/Generic driver connects over TCP (not only serial).
- Which plate-solve index covers a 53° × 41° field (ASTAP and astrometry.net
  both need their wide-field sets).
- That `indi_libcamera` runs well on a Pi 3B with 1 GB RAM next to `mountd`.

## Decided (2026-10-22)

1. **Protocol first:** LX200 over TCP ([ADR 0001](adr/0001-lx200-first.md)).
2. **Language:** `mountd` is built twice, Python first, then each finished
   feature again in Go ([ADR 0002](adr/0002-mountd-in-python-and-go.md)).
3. **Repo:** its own, created 2026-10-22.
4. **Desktop software:** KStars/Ekos on the Mac. Considered: CCDciel (lighter,
   INDI + Alpaca), N.I.N.A. (Windows only; later through Alpaca),
   SGP/APT/Voyager/ACP (Windows, paid). Ekos covers every rung up to the
   observatory with one program and runs with simulators first.

What gets measured and logged: [benchmarks.md](benchmarks.md).
