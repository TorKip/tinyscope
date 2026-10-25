# Benchmarks: measuring the "observatory"

*2026-10-22. Every rig (tinyscope,
mini-scope, EQ5, LX200, observatory) is measured the same way, so that each
upgrade can be tested as a hypothesis (see "The method" in
[GOALS.md](../GOALS.md)) and so that the article has numbers and pictures that
compare.*

## The headline numbers

My pick (2026-10-22): **the zero point** is the number to compare
scopes by. It belongs to the rig (aperture, optics, sensor) and barely depends
on the site. The sky background belongs to the site. Limiting magnitude and
SNR depend on both. Every other metric below is logged too; the scoreboard
(still to design) picks a handful.

## What we measure

Each metric says how it's measured and who records it: **auto** means `mountd`,
Ekos or the analysis script logs it with no effort; **hand** means I note it.

### Setup and reliability

| Metric | Unit | How | Who |
|---|---|---|---|
| Setup time: out the door → first light frame | min | Phone stopwatch from carrying out; stop at the first saved frame. Fuzzy (±1 min) is fine | hand |
| Boot time: power on → `mountd` ready | s | `mountd` logs `/proc/uptime` when it starts listening | auto |
| Power on → first plate-solved frame | s | Timestamps from the `mountd` log and the FITS headers | auto |
| Interruptions per session | count | Wi-Fi drops, crashes, lost steps, "had to touch it" | hand + log |
| Under-voltage and throttling | count | `vcgencmd get_throttled`, polled by `mountd` (a thin power cable sags under motor load) | auto |

### Camera and optics ("how much light it collects")

| Metric | Unit | How | Who |
|---|---|---|---|
| Longest usable exposure | s | Exposure series on a dark scene; the longest where the signal still grows | once per camera |
| Gain | e⁻/ADU | Photon transfer: pairs of flats at several levels, variance vs mean | once per camera |
| Read noise | e⁻ | Pairs of bias frames: std(difference) / √2 × gain | once per camera |
| Dark current vs temperature | e⁻/s/px | Darks at a few temperatures (the lens cap does this) | once per camera, then auto |
| **Zero point** | mag | The star magnitude that gives 1 e⁻/s. *The* "light collected" number: aperture, optics and sensor in one | auto per session |
| Sky background | e⁻/s/px, mag/arcsec² | Median of the frame; converts to an SQM-style number with the zero point | auto |
| SNR of reference stars | — | Photometry of a few fixed stars in the benchmark fields | auto |
| Limiting magnitude, 1 frame and 10/30/60 min stack | mag | Faintest catalogue stars detected at SNR 5 | auto |
| Star size (FWHM) and roundness | ″ and px | From the plate-solved frame; centre vs corners | auto |
| Image scale and field | ″/px, ° | From the plate solve | auto |

### Mount

| Metric | Unit | How | Who |
|---|---|---|---|
| Pointing error after GoTo | ′ | Plate solve vs where `mountd` thinks it points (`pointing.csv`) | auto |
| Backlash per axis | ′ | Pointing error with the approach direction flipped vs not | auto (a test routine) |
| Tracking drift | ″/min | Star positions across a sequence of frames | auto |
| Periodic error | ″ peak-to-peak, period | The tracking drift's wobble (FFT) over ≥ 2 gear turns | auto |
| Polar alignment error | ′ | Ekos polar alignment, or drift | auto |
| Slew speed and settle time | °/s, s | `mountd` log; the IMU in the head measures the wobble directly | auto |
| Wind and vibration | mg, Hz | IMU accelerometer during exposures | auto |

### Conditions (so that nights compare fairly)

Date, **site** (home / dark site), rig version, Moon phase and altitude,
temperature (Pi CPU + IMU), sky background from above, and clouds from the
**IR sky sensor** (see below; until it exists, by hand: clear / patchy / haze).

### The IR sky sensor (MLX90614)

A thermopile that reads the temperature of whatever it looks at, plus its own
(ambient) temperature. A clear sky is very cold to it (typically 20–40 °C
below ambient); clouds are almost as warm as the air. **Sky minus ambient**
is the cloud measure, logged every minute. The same sensor carries over to
mini-scope's dome safety.

The boards look alike but differ in more than the viewing angle. The suffix
on the can tells which one it is (MLX90614 + three letters):

| Letter | Means | Seen on the boards |
|---|---|---|
| 1st | Supply: A = 5 V, B = 3 V, D = 3 V with medical-grade accuracy | B, D |
| 2nd | A = single zone, B = dual zone, C = **gradient compensated** (corrects for the sensor body being warmer on one side, e.g. in wind) | A, C |
| 3rd | Field of view: A = 90° (bare can), C = 35°, F = 10°, I = 5° (long tube) | A, C, I |

On the boards I looked at: bare can = **BAA** (90°), short cap = **BCC** (35°,
gradient compensated), long tube = **DCI** (5°, medical accuracy, the most
expensive).

**Proposal: BCC (35°).** Pointed straight up, a 90° cone reaches down to 45°
altitude and picks up warm low sky, trees and houses; 5° sees a patch too
small to notice patchy cloud. 35° covers the useful sky around the zenith, and
the gradient compensation helps outdoors. Mount it **fixed on the foot,
pointing at the zenith, outside the fork's swing**, not on the moving head:
there its reading would change with where the camera points. It needs a dew
shield, and its wires must reach the Pi in the head: up the polar axis with
the power cable, then two more wires (SDA, SCL) in the Dec ribbon (10 → 12
wires; 3.3 V and GND can be shared). I²C at 100 kHz is fine over the ~1 m. A purchase, so: the hypothesis is
"sky − ambient tells clear from cloudy nights as well as the star count in
the frames", which the frames themselves can check. *To check:* the price
difference at Electrokit/AliExpress and that the board has a 3.3 V-safe
regulator.

## Benchmark targets

At 60° N, anything north of +30° declination never sets, so most benchmarks
can be **circumpolar: available every clear night of the year**. (From mid-May
to late July there is no astronomical darkness here, so expect a summer break.)

| ID | Target | Why | Measures |
|---|---|---|---|
| B1 | **The celestial pole field** (Polaris and around) | Always at the same altitude (= the site's latitude), never moves much: the same sky through the same air every night. Poor for testing tracking for the same reason | Zero point, SNR, limiting magnitude, sky background, star size |
| B2 | **Double Cluster** (NGC 869/884, +57°) | Circumpolar, rich in stars, about 1° across: a dot pair on tinyscope, frame-filling on the LX200. A good "same target, every rig" picture | Image comparison, star size, limiting magnitude |
| B3 | **Andromeda galaxy** (M31, +41°) | Circumpolar here, and everyone knows it: the article's headline comparison picture | Extended faint signal, image comparison |
| B4 | **A field near the celestial equator, near the meridian** (seasonal: Orion's belt in winter, Altair in late summer) | The sky moves fastest here, so tracking errors show most | Tracking drift, periodic error |
| B5 | **The Moon** (when it's up anyway) | Bright, quick, fun; from 22 px on tinyscope to a full-frame crater field on the LX200 | Resolution, a visual comparison for the article |

Every session images **B1 + one more**, with the same settings for a given
rig (exposure, gain, stack length), so that results compare. Once setup is
routine, aim for **all targets each session** when the night allows: then all
targets share the same conditions.

**The dark-site run.** Now and then, B1–B4 from a really dark site with the
same rig. Comparing home and dark site splits image quality into rig and
site: the zero point should barely move, the sky background should drop a lot,
and the limiting magnitude shows what the light pollution costs. (Seeing
matters only for the big scopes: tinyscope's 80″ pixels are far coarser than
the 2–4″ of a typical night's seeing.)

## Where things go

```
data/
  rigs/tinyscope-v0.md            what this rig version is; what changed and why
  sessions/2026-11-03-tinyscope-v0/
    session.md                    conditions, setup time, notes (hand, one template)
    mountd.log, pointing.csv, tracking.csv     (auto)
    results.json                  computed metrics (analysis script)
    previews/                     small JPEGs of each target, for comparison + article
images/                           final processed target images only (JPEG, ≤ 2000 px)
photos/build/NNNN-<what>.jpg      build photos, numbered in order (see photos/README.md)
docs/experiments/NNNN-<slug>.md   hypothesis → prediction → method → result → why
raw frames (FITS)                 never in git; on the Mac or the NAS (below)
```

**Raw frames:** Ekos saves them to a folder on the Mac (works in the field with
no network), and they're copied to the NAS at home. Session folders keep the
same name in both places, so `results.json` can point to its raw data.

**Later:** one analysis script turns a session folder into `results.json`, and
a comparison page (opens from Finder, data embedded) shows every rig and
session side by side: the numbers plus the B1–B5 previews.

## To check before relying on it

- **Star catalogue for offline photometry.** The whole Gaia DR3 (1.8 billion
  stars) is far too big to carry: hundreds of GB to TBs with all columns. We
  don't need it: tinyscope reaches about mag 9, so **Tycho-2** (2.5 million
  stars to about mag 11.5, about half a GB unpacked) is enough, and it is
  better than Gaia for the bright stars that saturate Gaia. Deeper rigs need
  a magnitude-limited Gaia subset, and ASTAP's own Gaia-derived star databases
  (a few hundred MB to a couple of GB) may already do it all: ASTAP can
  calibrate photometry and report a zero point and a limiting magnitude
  itself. To check which database fits which field, and what ASTAP reports.
  Download once on the Mac (no firewall change needed); it then works in the
  field with no network.
- That `indi_libcamera` writes raw (not processed) data to FITS; photometry
  needs raw.

## Open

- The scoreboard: which handful of numbers, and how it looks.
- Costs in kroner per rig: added as I go.
