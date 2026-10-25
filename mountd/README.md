# mountd

The mount daemon on the Pi: it steps the motors, tracks, and speaks LX200 over
TCP ([ADR 0001](../docs/adr/0001-lx200-first.md)). Built in Python first, then
each finished slice again in Go ([ADR 0002](../docs/adr/0002-mountd-in-python-and-go.md)).
Shape: a core with no protocol or GPIO code, LX200 in front, real or fake
motors behind ([docs/software.md](../docs/software.md)).

Python: standard library only (3.11, as on Raspberry Pi OS Bookworm), so it
runs on the Mac and the Pi with nothing to install.

    cd mountd/python && python3 -m unittest

## Slices

Each slice ends with tests that pass, and later with the same slice in Go.

| # | Slice | Done when | State |
|---|---|---|---|
| 1 | **LX200 codec**: split the byte stream into commands; RA/Dec text ↔ numbers, both precisions | edge cases tested: 23:59:59.6 wraps to 00:00:00, −0°30′ keeps its sign, invalid input is refused | done 2026-10-23 |
| 2 | **Session + fake mount**: answer each command from a mount that moves instantly; conversation tests (below) | Ekos's start-up conversation replays correctly | done 2026-10-23 |
| 3 | **TCP server** | SkySafari, Stellarium or KStars on the Mac connect to a fake tinyscope on `localhost` (Sunday's goal); unknown commands are logged | done 2026-10-23 (tested on localhost; real clients on Sunday) |
| 4 | **Sky maths**: sidereal time from clock and longitude, RA ↔ hour angle, the exact gear ratio (63.684 × 5) to steps | tested against published values | done 2026-10-25 (`sky.py`: Meeus 7.a, 12.a, 12.b to 1 ms; 20 378.9 half-steps per axis turn, one every 4.228 s when tracking). Wired in: `site.py` keeps the site and clock clients set (`:St :Sg :SG :SL :SC`), `:GS#` answers the sidereal time |
| 5 | **Core motion**: slews at a set speed, tracking, limits (RA ±150°, Dec −35°…100°), backlash take-up in one direction | a fake motor with a fake clock moves as expected | started 2026-10-25: the fake mount's manual moves (`:M`/`:Q` per axis, four rates, park) on a fake clock |
| 6 | **Pointing log**: commanded vs synced position to CSV | a sync writes a row | |
| 7 | **GPIO back-end** on the Pi | the RA axis turns from Ekos | |

## Running it (the fake mount)

    cd mountd/python
    python3 -m mountd --fake --record ~/Desktop/session.txt -v

It listens on `127.0.0.1:4030` (`--host 0.0.0.0` to reach it from the phone).
`--record` writes every exchange in the conversation format below, so a
session with a real client can be copied into `conversations/` as a test.

**With KStars/Ekos on the Mac** (first done 2026-10-25):

1. Ekos profile: mount driver *LX200 Basic* (only the essentials) or
   *LX200 Autostar* (asks for more). Leave **Remote** unchecked: Remote means
   the INDI server runs on another machine, and Ekos then speaks INDI's XML to
   port 4030 instead of starting a local LX200 driver.
2. Start the profile (▶). In the INDI Control Panel: the driver → *Connection*
   → **Network**, address `127.0.0.1` (not `localhost`, which macOS may resolve
   to IPv6 `::1`), port `4030`, then **Set**. Back in *Main Control* →
   *Connect*. Each driver keeps its own connection settings, so switching
   from Basic to Autostar means setting Network again.
3. Connect, GoTo, sync, abort, the arrow buttons. Unknown commands show up as warnings in the log.

Until a client sets the clock, mountd uses the system clock; a client's
`:SL`/`:SC`/`:SG` sets an offset from it, since the Pi 3B has no battery-backed
clock and in the field Ekos may be the only one that knows the time.

If it won't connect, take Ekos out of the picture: `nc 127.0.0.1 4030`, type
`:GR#` and expect `00:00:00#` and a `client connected` line from `-v`.

What LX200 Basic sent on 2026-10-25: no handshake, only `:GR#`/`:GD#` polled
over and over, `:Sr`/`:Sd` (no space after the command), `:MS#`, `:CM#`, `:Q#`.
*LX200 Autostar* adds the handshake (`\x06`), queries for the clock, site and
version on connect (each unanswered one costs a 5 s timeout), the rates
`:RG#`…`:RS#`, the moves `:Mn#`…`:Mw#` with their stops `:Qn#`…`:Qw#`, and park
`:hP#`. With *Reverse* on, INDI stops the opposite direction (`:Ms#` then
`:Qn#`), so mountd stops the whole axis whichever direction a `:Q` names.

## Conversation tests

The behaviour tests both languages must pass: plain text files in
`conversations/`, one exchange per pair of lines. `>` is what the client
sends, `<` the exact reply; a `>` with no `<` after it expects silence.

```
# Ekos connects and reads the position
> :GR#
< 00:00:00#
> :GD#
< +90*00:00#
> :Sr 05:34:32#
< 1
```

A `# t=12.5` comment sets the fake mount's clock to that many seconds, so moves
can be tested (`--record` writes these lines too). See `conversations/moves.txt`.
