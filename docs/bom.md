# Bill of materials (tinyscope v0)

*2026-10-23. "Have?" is what I had or still need; costs in kroner get added
as I go (G6, the article).*

## Electronics

| Part | Qty | Have? | Notes |
|---|---|---|---|
| Raspberry Pi 3B | 1 | yes | |
| microSD card, ≥ 16 GB | 1 | ? | Raspberry Pi OS Lite 64-bit |
| Pi camera v2.1 (IMX219) + its ribbon | 1 | yes | measure the board's holes before printing (`CAM_HOLES`) |
| 28BYJ-48 5 V stepper + ULN2003 board | 2 | yes | often sold as a pair |
| SG90 servo | 1 | yes | for the lens cap (darks); one of its screws, at the shaft end |
| GY-BMI160 IMU | 1 | yes | in the head, flat on two pegs; homing and levelling. Measure its holes before printing the lid (`IMU_HOLES`) |
| 2.54 mm right-angle header, 7 pins | 1 | ? | for the IMU (a straight header with plugs is too tall); or solder 4 wires to the pads |
| ~~GY-271 compass~~ | 0 | | left out for now (2026-10-22); phone + arrow instead |
| ~~MLX90614 BCC IR sensor~~ | 0 | | later, as an experiment (docs/benchmarks.md) |
| USB power bank, 5 V ≥ 2 A | 1 | ? | |
| Spare USB-A cable | 1 | ? | cut for the Y harness: Pi header + the ULN boards |
| Dupont jumpers F–F | ~20 | ? | often come with the 28BYJ-48 kits; a 10-pin housing for the ribbon if there's one in the drawer |

## Mechanical

| Part | Qty | Have? | Notes |
|---|---|---|---|
| Printed parts | 15 + 4 pins | | see [print-plan.md](print-plan.md); ~200 g filament, PETG for the parts listed there |
| 1.75 mm filament as pins | a few cm | yes | hub pin, hood dowels |
| M3 × 10 screws | 4 | optional | instead of the printed push pins for the motor ears |
| Photo tripod with a 1/4"-20 screw | 1 | ? | |
| Vaseline | a bit | ? | the plain bearings |

## Tools

Soldering iron (harness), multimeter (check 5 V and GND before first power-up),
CA glue (pinions if loose), hot glue (IMU, ULN boards), a flush cutter.

## Total to buy now

Nothing essential (2026-10-28: the GY-BMI160 has arrived). A right-angle header if
there isn't one in the drawer. The M3 × 10s are optional (M3 is the most useful size to
keep in stock anyway).
