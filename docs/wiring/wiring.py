"""tinyscope wiring: the pin plan, and the pages drawn from it.

    python docs/wiring/wiring.py          # → docs/wiring/{overview,header}.svg, docs/wiring.md, docs/wiring.html
    python docs/wiring/wiring.py --check  # the plan is sound and the outputs are up to date

The plan lives in WIRES; everything else is drawn from it. Stdlib only.
"""
import html
import re
import sys
from pathlib import Path

HERE = Path(__file__).parent
DOCS = HERE.parent

# Raspberry Pi 3B, 40-pin header (same on every 40-pin Pi)
HEADER = {1: "3V3", 2: "5V", 3: "GPIO2", 4: "5V", 5: "GPIO3", 6: "GND", 7: "GPIO4", 8: "GPIO14", 9: "GND",
          10: "GPIO15", 11: "GPIO17", 12: "GPIO18", 13: "GPIO27", 14: "GND", 15: "GPIO22", 16: "GPIO23",
          17: "3V3", 18: "GPIO24", 19: "GPIO10", 20: "GND", 21: "GPIO9", 22: "GPIO25", 23: "GPIO11",
          24: "GPIO8", 25: "GND", 26: "GPIO7", 27: "ID_SD", 28: "ID_SC", 29: "GPIO5", 30: "GND", 31: "GPIO6",
          32: "GPIO12", 33: "GPIO13", 34: "GND", 35: "GPIO19", 36: "GPIO16", 37: "GPIO26", 38: "GPIO20",
          39: "GND", 40: "GPIO21"}
HW_PWM = {"GPIO12", "GPIO13", "GPIO18", "GPIO19"}

# kind: colour and what the header pin must be
KINDS = {
    "5v": ("5 V", "#d1453b"), "gnd": ("GND", "var(--gnd)"), "3v3": ("3.3 V", "#e08a1e"),
    "ra": ("RA step", "#2f6fdb"), "dec": ("Dec step", "#8b4fd6"), "i2c": ("I²C", "#1f9d6b"),
    "pwm": ("servo PWM", "#b8860b"),
}

# (pin, kind, signal, goes to, via): one row per wire on the Pi's header
WIRES = [
    (31, "ra", "RA IN1", "RA ULN2003 IN1", "ribbon"),
    (32, "ra", "RA IN2", "RA ULN2003 IN2", "ribbon"),
    (33, "ra", "RA IN3", "RA ULN2003 IN3", "ribbon"),
    (35, "ra", "RA IN4", "RA ULN2003 IN4", "ribbon"),
    (36, "dec", "Dec IN1", "Dec ULN2003 IN1", "ribbon"),
    (37, "dec", "Dec IN2", "Dec ULN2003 IN2", "ribbon"),
    (38, "dec", "Dec IN3", "Dec ULN2003 IN3", "ribbon"),
    (40, "dec", "Dec IN4", "Dec ULN2003 IN4", "ribbon"),
    (34, "gnd", "GND", "Y splice GND", "ribbon"),
    (39, "gnd", "GND", "Y splice GND", "ribbon"),
    (2, "5v", "5 V in", "Y splice 5 V", "ribbon, own housing"),
    (4, "5v", "servo 5 V", "SG90 red", "head"),
    (12, "pwm", "servo signal", "SG90 orange", "head"),
    (14, "gnd", "servo GND", "SG90 brown", "head"),
    (1, "3v3", "IMU power", "BMI160 VIN", "head"),
    (3, "i2c", "SDA", "BMI160 SDA", "head"),
    (5, "i2c", "SCL", "BMI160 SCL", "head"),
    (9, "gnd", "IMU GND", "BMI160 GND", "head"),
]
RIBBON_HOUSING = [31, 32, 33, 34, 35, 36, 37, 38, 39, 40]   # one 2×5 housing, flush with the header's end

# wiring that never touches the header: (from, to, via)
FORK = [
    ("USB cable 5 V (red)", "Y splice 5 V", "up the hollow column (Ø15)"),
    ("USB cable GND (black)", "Y splice GND", "up the hollow column"),
    ("Y splice 5 V", "RA ULN2003 +, Dec ULN2003 +", "Dupont F"),
    ("Y splice GND", "RA ULN2003 −, Dec ULN2003 −", "Dupont F"),
    ("RA 28BYJ-48", "RA ULN2003 motor socket", "its own 5-pin cable (keyed)"),
    ("Dec 28BYJ-48", "Dec ULN2003 motor socket", "its own 5-pin cable (keyed)"),
    ("Camera v2.1", "Pi CSI connector", "flat flex cable, contacts towards the HDMI port"),
]

NOTES = [
    ("The ribbon housing", "8 step lines and 2 GND in one 2×5 housing on pins **31–40**, flush with the header's "
     "USB end. It has no 5 V in it, so a wrong fit can't put 5 V on a GPIO. It still goes on turned round, which "
     "puts the GND wires on GPIO12 and GPIO26: mark the pin-31 corner on the housing and the head."),
    ("5 V in", "On its own red, marked 1-pin housing on pin **2**. Before the first power-up, with the multimeter: "
     "5 V between pin 2 and pin 6 (red probe on 2), and nothing between pin 2 and any ribbon pin."),
    ("Through the Dec stub", "The stub's bore is Ø12. The 1×4 housings at the fork end fit through it, the 2×5 "
     "(about 13.7 mm across the corners) doesn't, so thread the ribbon from the head outwards."),
    ("The Y splice", "A spare USB-A cable, cut and soldered at the fork: 5 V to both boards' **+** and the ribbon's "
     "5 V, GND to both boards' **−** and the ribbon's two GND wires. Check which wire is 5 V with the meter, "
     "cheap cables don't always use red and black. Keep each ULN2003's on/off jumper on."),
    ("The servo", "5 V from pin 4, which is the same net as pin 2 (the header's 5 V pins are joined on the board), so "
     "it is really the harness wire, split at the header. A stall shows in `vcgencmd get_throttled`; the servo "
     "only moves for darks, never during an exposure. Its 3-pin plug doesn't fit pins 4/12/14: three M–F jumpers "
     "into the plug."),
    ("The IMU", "VIN to 3.3 V (pin 1). Leave CS open (I²C mode) and SA0 open; `i2cdetect -y 1` should show 0x68 or "
     "0x69. Tie CS to 3.3 V if nothing shows up."),
    ("Boot", "The step pins come up as inputs. GPIO0–8 have pull-ups at boot, so GPIO6 (RA IN1) may light RA's first "
     "LED until `mountd` starts. Harmless, but `mountd` must begin by driving all eight low."),
    ("Mark the boards", "Label the ULN2003 boards RA and Dec. The IN order only matters to the step sequence in "
     "`mountd`, so a swapped pair shows up as a motor that hums instead of turning."),
    ("Later", "The IR sky sensor shares I²C, but it sits on the foot, two axes away from the Pi: it needs its own "
     "route, not planned yet."),
]

INTRO = ("Only power and one ribbon cross an axis. The USB cable comes up the hollow polar axis to the fork, and an "
         "11-wire Dupont ribbon (8 step lines, 2 GND, 5 V) runs from the fork through the hollow left Dec stub into "
         "the head. Drawn by `docs/wiring/wiring.py`, which holds the pin plan: change it there, run it, and "
         "`--check` checks the plan.")

STYLE = """
.w-t{font:12px system-ui,-apple-system,sans-serif;fill:var(--text)}
.w-s{font-size:10.5px;fill:var(--muted)}.w-b{font-weight:600}.w-h{font-size:14px;font-weight:600}
.w-zone{fill:var(--zone);stroke:none}.w-box{fill:var(--box);stroke:var(--line);stroke-width:1.2}
.w-axis{stroke:var(--muted);stroke-width:1.2;stroke-dasharray:5 4;fill:none}
.w-pinno{font:600 10px system-ui,sans-serif;fill:#fff}
"""
TOKENS = """
:root{--text:#1d2330;--muted:#5f6876;--zone:#f1f3f6;--box:#ffffff;--line:#9aa3b2;--gnd:#2b2f36;--gndtext:#ffffff;--unused:#a3aab5;--hdr:#3a3f48}
@media (prefers-color-scheme:dark){:root{--text:#e6e9ef;--muted:#9aa3b2;--zone:#1c2028;--box:#252a33;--line:#59616e;--gnd:#c9ced6;--gndtext:#14171d;--unused:#59616e;--hdr:#0f1115}}
"""


def esc(s):
    return html.escape(str(s), quote=True)


def text(x, y, s, cls="w-t", anchor="start", extra=""):
    return f'<text x="{x}" y="{y}" class="{cls}" text-anchor="{anchor}"{extra}>{esc(s)}</text>'


def svg(w, h, body, title):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="{w}" height="{h}" '
            f'role="img" aria-label="{esc(title)}"><title>{esc(title)}</title>'
            f'<style>{TOKENS}{STYLE}</style>\n' + "\n".join(body) + "\n</svg>\n")


def colour(kind):
    return KINDS[kind][1]


def wire(d, kind, w=2.2):
    return f'<path d="{d}" fill="none" stroke="{colour(kind)}" stroke-width="{w}" stroke-linecap="round"/>'


def dot(x, y, kind):
    return f'<circle cx="{x}" cy="{y}" r="3.2" fill="{colour(kind)}"/>'


def box(x0, y0, x1, y1, r=6):
    return f'<rect x="{x0}" y="{y0}" width="{x1 - x0}" height="{y1 - y0}" rx="{r}" class="w-box"/>'


def by_pin(pin):
    return next(w for w in WIRES if w[0] == pin)


def overview():
    b = []
    zones = [(16, 176, "Foot (fixed)"), (196, 576, "Fork (turns with RA)"), (596, 984, "Head (turns with Dec)")]
    for x0, x1, name in zones:
        b.append(f'<rect x="{x0}" y="40" width="{x1 - x0}" height="584" rx="10" class="w-zone"/>')
        b.append(text((x0 + x1) / 2, 64, name, "w-t w-h", "middle"))
    b.append('<line x1="186" y1="80" x2="186" y2="610" class="w-axis"/>')
    b.append(text(186, 30, "RA axis", "w-t w-s", "middle"))
    b.append('<line x1="586" y1="80" x2="586" y2="610" class="w-axis"/>')
    b.append(text(586, 30, "Dec axis", "w-t w-s", "middle"))

    # power bank → Y splice
    b.append(box(36, 500, 156, 564))
    b += [text(96, 527, "Power bank", "w-t w-b", "middle"), text(96, 545, "5 V, USB-A", "w-t w-s", "middle")]
    b += [text(96, 468, "USB cable up the", "w-t w-s", "middle"), text(96, 482, "hollow column (Ø15)", "w-t w-s", "middle")]
    b.append(wire("M156,520 H236", "5v", 3))
    b.append(wire("M156,544 H236", "gnd", 3))
    b.append(box(236, 470, 316, 590))
    b += [text(276, 462, "Y splice (soldered)", "w-t w-b", "middle")]
    b += [text(244, 524, "5 V", "w-t w-s"), text(244, 548, "GND", "w-t w-s")]
    b += [text(308, 490, "5 V", "w-t w-s", "end"), text(308, 506, "GND", "w-t w-s", "end"),
          text(308, 566, "ribbon", "w-t w-s", "end")]

    # ULN boards and motors
    lanes5, lanesg = 346, 358
    for top, axis, kind in [(80, "RA", "ra"), (290, "Dec", "dec")]:
        b.append(box(376, top, 486, top + 150))
        b.append(text(431, top + 20, f"ULN2003 · {axis}", "w-t w-b", "middle"))
        for i in range(4):
            y = top + 40 + 22 * i
            b.append(text(478, y + 4, f"IN{i + 1}", "w-t w-s", "end"))
        b += [text(384, top + 114, "+", "w-t w-s"), text(384, top + 134, "−", "w-t w-s")]
        cy = top + 45
        b.append(f'<circle cx="290" cy="{cy}" r="34" class="w-box"/>')
        b += [text(290, cy - 2, "28BYJ-48", "w-t w-s", "middle"), text(290, cy + 12, axis, "w-t w-b", "middle")]
        b.append(f'<path d="M324,{cy} H376" stroke="var(--line)" stroke-width="6" stroke-linecap="round"/>')
        b.append(text(350, cy - 8, "5-pin", "w-t w-s", "middle"))
        b.append(f'<path d="M{lanes5},{top + 110} H{lanesg - 4} A4,4 0 0 1 {lanesg + 4},{top + 110} H376" fill="none" '
                 f'stroke="{colour("5v")}" stroke-width="2.2"/>')
        b.append(wire(f"M{lanesg},{top + 130} H376", "gnd"))
        b += [dot(lanes5, top + 110, "5v"), dot(lanesg, top + 130, "gnd")]
    b.append(wire(f"M316,486 H{lanes5} V190", "5v"))
    b.append(wire(f"M316,502 H{lanesg} V210", "gnd"))

    # the ribbon: sources in the fork → through the stub → ports on the Pi's left edge
    sources = [(486, 80 + 40 + 22 * i) for i in range(4)] + [(486, 290 + 40 + 22 * i) for i in range(4)] \
        + [(316, 548), (316, 562), (316, 576)]
    pins = [31, 32, 33, 35, 36, 37, 38, 40, 34, 39, 2]
    b.append('<rect x="566" y="226" width="68" height="110" rx="8" fill="none" stroke="var(--line)" stroke-width="1.2"/>')
    b += [text(600, 352, "cable stub Ø12", "w-t w-s", "middle"), text(600, 218, "11-wire ribbon", "w-t w-s", "middle")]
    for i, ((sx, sy), pin) in enumerate(zip(sources, pins)):
        kind = by_pin(pin)[1]
        by, py = 236 + 9 * i, 150 + 22 * i
        b.append(wire(f"M{sx},{sy} H505 C540,{sy} 525,{by} 560,{by} H640 C675,{by} 670,{py} 700,{py}", kind))

    # the Pi and what hangs on it in the head
    b.append(box(700, 80, 850, 590))
    b += [text(775, 104, "Raspberry Pi 3B", "w-t w-b", "middle"), text(775, 120, "GPIO header (pin · name)", "w-t w-s", "middle")]
    for i, pin in enumerate(pins):
        b.append(text(708, 150 + 22 * i + 4, f"{pin} · {HEADER[pin]}", "w-t w-s"))
    right = [(1, 160), (3, 182), (5, 204), (9, 226), (4, 320), (12, 342), (14, 364)]
    for pin, y in right:
        b.append(text(842, y + 4, f"{pin} · {HEADER[pin]}", "w-t w-s", "end"))
        b.append(wire(f"M850,{y} H890", by_pin(pin)[1]))
    b.append(box(890, 136, 980, 250))
    b += [text(935, 130, "GY-BMI160", "w-t w-b", "middle")]
    for s, y in [("VIN", 160), ("SDA", 182), ("SCL", 204), ("GND", 226)]:
        b.append(text(898, y + 4, s, "w-t w-s"))
    b.append(box(890, 296, 980, 388))
    b += [text(935, 290, "SG90 (hood)", "w-t w-b", "middle")]
    for s, y in [("red", 320), ("orange", 342), ("brown", 364)]:
        b.append(text(898, y + 4, s, "w-t w-s"))
    b.append('<rect x="850" y="492" width="40" height="16" fill="var(--line)" opacity=".55"/>')
    b.append(box(890, 466, 980, 534))
    b += [text(935, 496, "Camera v2.1", "w-t w-b", "middle"), text(935, 512, "IMX219", "w-t w-s", "middle"),
          text(886, 530, "CSI flex", "w-t w-s", "end")]

    # legend
    x = 210
    for k in ["5v", "gnd", "3v3", "ra", "dec", "i2c", "pwm"]:
        b.append(f'<rect x="{x}" y="604" width="14" height="4" fill="{colour(k)}"/>')
        b.append(text(x + 19, 610, KINDS[k][0], "w-t w-s"))
        x += 84 if k not in ("ra", "dec") else 94
    return svg(1000, 640, b, "tinyscope wiring overview")


def pin_xy(pin):
    col = (pin - 1) // 2
    return 70 + col * 42, (176 if pin % 2 == 0 else 218)


def header():
    b = ['<rect x="44" y="152" width="852" height="90" rx="6" fill="var(--hdr)"/>']
    used = {w[0]: w for w in WIRES}
    for pin, name in HEADER.items():
        x, y = pin_xy(pin)
        w = used.get(pin)
        fill = colour(w[1]) if w else "var(--unused)"
        ring = 'stroke="#ffffff" stroke-opacity=".6" stroke-width="1.5"'
        if pin == 1:
            b.append(f'<rect x="{x - 13}" y="{y - 13}" width="26" height="26" rx="3" fill="{fill}" {ring}/>')
        else:
            b.append(f'<circle cx="{x}" cy="{y}" r="13" fill="{fill}" {ring}/>')
        ink = ' style="fill:var(--gndtext)"' if w and w[1] == "gnd" else ""
        b.append(f'<text x="{x}" y="{y + 3.5}" class="w-pinno" text-anchor="middle"{ink}>{pin}</text>')
        # rotated labels reading upwards: the signal (bold) and the Pi's name beside it
        top = pin % 2 == 0
        y0, anchor = (152, "start") if top else (242, "end")
        lines = [(w[2], "w-t w-b"), (name, "w-t w-s")] if w else [(name, "w-t w-s")]
        for i, (s, cls) in enumerate(lines):
            lx = x - 2 + 13 * i if w else x + 4
            b.append(text(lx, y0 - 4 if top else y0 + 4, s, cls, anchor,
                          f' transform="rotate(-90 {lx} {y0 - 4 if top else y0 + 4})"'))
    for pins in (RIBBON_HOUSING, [2]):
        xs = [pin_xy(p)[0] for p in pins]
        ys = [pin_xy(p)[1] for p in pins]
        b.append(f'<rect x="{min(xs) - 18}" y="{min(ys) - 18}" width="{max(xs) - min(xs) + 36}" '
                 f'height="{max(ys) - min(ys) + 36}" rx="4" fill="none" stroke="#ffd23f" stroke-width="2.4"/>')
    b.append(text(40, 362, "← SD card end", "w-t w-s"))
    b.append(text(470, 362, "seen from the component side, board edge at the top; yellow = housings", "w-t w-s", "middle"))
    b.append(text(900, 362, "USB / Ethernet end →", "w-t w-s", "end"))
    x = 120
    for k in ["5v", "gnd", "3v3", "ra", "dec", "i2c", "pwm"]:
        b.append(f'<circle cx="{x}" cy="386" r="6" fill="{colour(k)}"/>')
        b.append(text(x + 10, 390, KINDS[k][0], "w-t w-s"))
        x += 92
    b.append(f'<circle cx="{x}" cy="386" r="6" fill="var(--unused)"/>')
    b.append(text(x + 10, 390, "free", "w-t w-s"))
    return svg(940, 404, b, "Raspberry Pi GPIO header with tinyscope's pins")


def header_rows():
    return [(p, HEADER[p], s, to, via) for p, _, s, to, via in sorted(WIRES)]


def md_table(head, rows):
    out = ["| " + " | ".join(head) + " |", "|" + "---|" * len(head)]
    out += ["| " + " | ".join(str(c) for c in r) + " |" for r in rows]
    return "\n".join(out)


def markdown():
    notes = "\n".join(f"- **{t}.** {s}" for t, s in NOTES)
    return f"""# Wiring

<!-- generated by docs/wiring/wiring.py: edit the plan there, then run it -->

{INTRO}

A page with the same content that opens from Finder: [wiring.html](wiring.html).

## Overview

![Wiring overview](wiring/overview.svg)

## The GPIO header

![GPIO header](wiring/header.svg)

## Pin table

On the Pi's header (fill in the wire colours as you go):

{md_table(["Pin", "Pi name", "Signal", "Goes to", "Via", "Colour"], [r + ("",) for r in header_rows()])}

Not on the header:

{md_table(["From", "To", "Via"], FORK)}

## Building it

{notes}
"""


def inline(s):
    s = esc(s)
    s = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", s)
    return re.sub(r"`(.+?)`", r"<code>\1</code>", s)


def page(over, hdr):
    def table(head, rows):
        th = "".join(f"<th>{esc(h)}</th>" for h in head)
        tr = "".join("<tr>" + "".join(f"<td>{esc(c)}</td>" for c in r) + "</tr>" for r in rows)
        return f'<div class="scroll"><table><thead><tr>{th}</tr></thead><tbody>{tr}</tbody></table></div>'
    notes = "".join(f"<li><b>{esc(t)}.</b> {inline(s)}</li>" for t, s in NOTES)
    return f"""<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>tinyscope wiring</title>
<!-- generated by docs/wiring/wiring.py: edit the plan there, then run it -->
<style>{TOKENS}
html,body{{margin:0;background:var(--box);color:var(--text);font:15px/1.5 system-ui,-apple-system,sans-serif}}
main{{max-width:1040px;margin:0 auto;padding:24px 16px 48px}}h1{{margin:0 0 8px}}h2{{margin:32px 0 8px}}
.scroll{{overflow-x:auto}}.scroll svg{{display:block;max-width:100%;height:auto;min-width:640px}}
table{{border-collapse:collapse;font-size:14px;min-width:560px}}th,td{{text-align:left;padding:5px 10px;border-bottom:1px solid var(--line)}}
th{{color:var(--muted);font-weight:600}}code{{font-size:13px;background:var(--zone);padding:1px 4px;border-radius:3px}}
li{{margin:6px 0}}
</style></head><body><main>
<h1>tinyscope wiring</h1>
<p>{inline(INTRO)}</p>
<h2>Overview</h2><div class="scroll">{over}</div>
<h2>The GPIO header</h2><div class="scroll">{hdr}</div>
<h2>Pin table</h2><p>On the Pi's header:</p>
{table(["Pin", "Pi name", "Signal", "Goes to", "Via"], header_rows())}
<p>Not on the header:</p>
{table(["From", "To", "Via"], FORK)}
<h2>Building it</h2><ul>{notes}</ul>
</main></body></html>
"""


def problems():
    """What's wrong with the plan, as a list of sentences (empty = sound)."""
    out = []
    pins = [w[0] for w in WIRES]
    out += [f"pin {p} is used twice" for p in set(pins) if pins.count(p) > 1]
    for pin, kind, signal, *_ in WIRES:
        name = HEADER[pin]
        need = {"5v": name == "5V", "gnd": name == "GND", "3v3": name == "3V3",
                "ra": name.startswith("GPIO") and name not in ("GPIO2", "GPIO3"),
                "dec": name.startswith("GPIO") and name not in ("GPIO2", "GPIO3"),
                "pwm": name in HW_PWM,
                "i2c": name == {"SDA": "GPIO2", "SCL": "GPIO3"}.get(signal)}[kind]
        if not need:
            out.append(f"{signal} on pin {pin} ({name}) is the wrong kind of pin")
    ribbon = sorted(w[0] for w in WIRES if w[4] == "ribbon")
    lo = min(RIBBON_HOUSING)
    if ribbon != sorted(RIBBON_HOUSING) or lo % 2 == 0 or sorted(RIBBON_HOUSING) != list(range(lo, lo + 10)):
        out.append("the ribbon's pins don't fill one 2×5 block")
    if any(HEADER[p] == "5V" for p in RIBBON_HOUSING):
        out.append("5 V is in the ribbon housing: a reversed housing would put it on a GPIO")
    for k in ("ra", "dec"):
        if sum(w[1] == k for w in WIRES) != 4:
            out.append(f"{k} needs exactly four step lines")
    return out


def outputs():
    over, hdr = overview(), header()
    return {HERE / "overview.svg": over, HERE / "header.svg": hdr,
            DOCS / "wiring.md": markdown(), DOCS / "wiring.html": page(over, hdr)}


def main():
    bad = problems()
    for p in bad:
        print("plan:", p)
    if "--check" in sys.argv:
        stale = [p for p, s in outputs().items() if not p.exists() or p.read_text() != s]
        for p in stale:
            print("stale:", p.relative_to(DOCS.parent), "(run python docs/wiring/wiring.py)")
        print("wiring: ok" if not bad and not stale else "wiring: FAILED")
        sys.exit(1 if bad or stale else 0)
    if bad:
        sys.exit(1)
    for p, s in outputs().items():
        p.write_text(s)
        print("wrote", p.relative_to(DOCS.parent))


if __name__ == "__main__":
    main()
