# Alignment: rough by hand and sensors, fine by plate solving

*2026-10-22: where the IMU and compass go, whether they can be trusted, and a
quick setup routine.*

## How rough is rough enough?

tinyscope's field is 53° × 41°. If the polar axis is off by 5°, a GoTo still
lands the target well inside the frame, and the first plate solve then tells
the truth to a fraction of a pixel. So the sensors only need to get within a
few degrees; plate solving does the rest. (The LX200 at 2500 mm sees about
0.3°: there the same 5° would miss completely, which is why big rigs need
the routine below much more.)

## Where the sensors go

**IMU (BMI160) in the head, as designed.** Its accelerometer reads the
direction of gravity in the head's frame. That alone gives two numbers (pitch
and roll), but each step `mountd` makes is known exactly. Read gravity in 4–6
head poses and solve for all four unknowns at once: the two axis positions
(this is homing, no endstops) and the base's two tilts (this is levelling).
An IMU in the base would give the tilt directly, but not the axis positions.
So one sensor in the head does both, at the price of a short calibration
"dance". The gyro adds little for alignment, but it measures wobble after a
slew and in wind (see benchmarks).

**Compass (GY-271): the weak link.** In the head it sits next to the Pi and
the Dec motor (a 28BYJ-48 holds a permanent magnet) and turns with the head,
so it would need recalibrating for every pose. In the base it sits under the
RA motor and on a steel tripod. Expect ±3–5° at best after calibration, plus
the magnetic declination (about 4–5° east in southern Norway; `mountd` can
correct it from the World Magnetic Model). That's good enough for tinyscope,
but a phone compass plus the engraved arrow is just as good and free. **So:
start with phone + arrow; fit the GY-271 later as an experiment** ("the
onboard compass finds north within 5° of what the plate solve says").

## The setup routine

| Step | What happens | Who | Accuracy |
|---|---|---|---|
| 1. Level | `mountd` shows the base tilt live (a bubble on a small web page on the phone, or beeps): "raise the north leg" | guided | ~0.5° (IMU) |
| 2. North | Arrow to north with the phone compass (later: the onboard compass, live on the same page) | guided | ~3–5° |
| 3. Home | The IMU dance: `mountd` finds both axis positions | robotic | ~1° |
| 4. First solve | Take a frame, plate-solve, sync: from here the pointing is exact | robotic | < 1 px |
| 5. Polar error | Ekos polar alignment (three frames while turning RA) measures the remaining error. With a fixed wedge you correct it by turning the tripod and adjusting a leg, while Ekos updates live, **or skip that** | guided, optional | arcminutes |
| 6. Compensate | `mountd`'s pointing model takes the measured polar error and tracks on both axes to cancel it. A few more solves across the sky refine the model | robotic | the target stays put |

Steps 1–2 make it fast, steps 3–6 make it exact. This is also how
professional robotic observatories work: mechanics good enough, then a
pointing model measured from the sky (the classic tool is called TPoint).

Each step's accuracy is a benchmark: log the IMU's and compass's guesses next
to the plate solve's truth, every session.
