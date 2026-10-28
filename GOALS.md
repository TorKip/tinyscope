# tinyscope: goals

*Written 2026-10-22.*

## Why this project exists

tinyscope is the first, smallest rung on a long ladder. Most of the value is in
what I **learn**, not in what the hardware can do.

| # | Goal | What "done enough" looks like on tinyscope |
|---|---|---|
| G1 | **Pictures** | A stacked wide-field image that beats the phase 0 baseline |
| G2 | **A working robotic telescope** | Pick a target on the Mac; the mount slews, plate-solves, centres, tracks and takes a sequence with no hands on it |
| G3 | **Learn what makes a good mount (and camera) by doing** | Know from my own data, not YouTube, what backlash, periodic error, flex, balance and polar error *cost* |
| G4 | **A platform for test data and informed decisions** | Each session leaves a log I can compare: mechanics, setup and boot time, exposure, SNR, light collected, and images of the same benchmark targets ([docs/benchmarks.md](docs/benchmarks.md)). Upgrades are chosen from numbers |
| G5 | **Understand how the whole picture fits together** | I can draw the stack from the sky to the Mac and say what each layer does: Wi-Fi, INDI/ASCOM/Alpaca, the LX200 protocol, cameras, mounts, sky sensors, alignment, plate solving, scheduling |
| G6 | **Inspire others; open source** | Someone else can rebuild it from the repo. An article for the local astronomy magazine and the local astronomy Facebook group ([docs/article.md](docs/article.md)) |

## The ladder

The "castle in the sky": an observatory-grade telescope with a dome, where I
**add imaging jobs to a queue and the telescope works through the night**.
Years away, and that's fine. The way there is bottom-up, so that trying
something on an ordinary evening stays cheap: no unpacking, no hour of setup
for a 10-minute window.

| Rung | What | Teaches |
|---|---|---|
| 0 | **tinyscope**: Pi 3B + camera v2.1 on a printed fork | The whole stack end to end, on hardware that can't break anything expensive |
| 1 | **mini-scope**: HQ camera, worm drives, the dome sketch | Precision mechanics, guiding, weather safety |
| 2 | **EQ5 GoTo** (I have one) | A real mount through the same software (SynScan/EQMOD) |
| 3 | **LX200 10"** (I have one) | Long focal length; the scope the LX200 protocol is named after |
| 4 | **Observatory**: dome, sky sensors, queue | Unattended operation and safety |

Open-source "product line" over time: minimal → value-ideal → over-engineered,
each one rebuildable by others.

## Principles that follow from the goals

1. **Bottom-up, low bar.** A session must be worth it in 10 minutes (setup under
   3 minutes; see the README).
2. **Same software on every rung.** Speak the standard protocols, so the Mac
   side (Ekos, later a scheduler) stays the same when the hardware grows. What
   I learn on tinyscope carries over to the EQ5, the LX200 and the
   observatory. (G2, G5)
3. **Measure, then decide.** Baseline first; every upgrade is justified by data
   (G3, G4). Purchases are a negative and must be argued for.
4. **Built to be shared.** Licence, bill of materials, printable files and the
   reasons behind decisions live in the repo. (G6)

## The method (2026-10-22)

> The first scope should be a bit "naive": as simple as possible while still
> checking all the boxes we can tick. Then build out the
> mount/scope/imaging system one bit at a time, each change based on a
> **measurable hypothesis** about what it will improve. We measure whether we
> actually hit that improvement, and try to figure out why or why not.

In practice, each upgrade gets a short note before it's built: the hypothesis
("the 5:1 stage cuts backlash from X to X/5"), how it's measured (usually the
pointing-error log in [docs/software.md](docs/software.md)), the result, and
why. Being wrong is a result too.

## Not goals (for tinyscope)

- Deep-sky detail. The stock lens is a 53° × 41° sky camera, by design.
- Running all night unattended outdoors. That's rung 4.
- Being beautiful or polished before it works.
