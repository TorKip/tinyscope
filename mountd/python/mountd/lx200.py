"""The Meade LX200 text protocol: splitting the byte stream into commands, and the coordinate formats.

A command starts with ':' and ends with '#', e.g. ':GR#' (get RA) or ':Sr 05:34:32#' (set target RA).
One exception: a lone ACK byte (0x06) asks for the alignment mode and gets one letter back.
Replies end with '#', except the one-character answers ('1'/'0' for set commands, '0' for a slew
that starts).

Two precisions, toggled by ':U#':
    low   RA HH:MM.T    Dec sDD*MM
    high  RA HH:MM:SS   Dec sDD*MM:SS
The real LX200 sends byte 0xDF as the degree sign; '*' is what most clients send and accept.
"""
import re

ACK = "\x06"


def split_commands(buffer):
    """Take the complete commands off the front of `buffer`. Returns (commands, rest), where rest is
    an unfinished command to keep for the next read. Bytes before a ':' that aren't ACK are noise."""
    commands = []
    while True:
        if buffer.startswith(ACK):
            commands.append(ACK)
            buffer = buffer[1:]
            continue
        start = buffer.find(":")
        ack = buffer.find(ACK)
        if ack != -1 and (start == -1 or ack < start):
            buffer = buffer[ack:]              # drop the noise, handle the ACK next round
            continue
        if start == -1:
            return commands, ""
        end = buffer.find("#", start)
        if end == -1:
            return commands, buffer[start:]
        commands.append(buffer[start:end + 1])
        buffer = buffer[end + 1:]


def format_ra(hours, high=True):
    """RA in hours (any value, wrapped into 0–24) → 'HH:MM:SS' or 'HH:MM.T'."""
    if high:
        s = round(hours % 24 * 3600) % (24 * 3600)
        return f"{s // 3600:02d}:{s // 60 % 60:02d}:{s % 60:02d}"
    t = round(hours % 24 * 600) % (24 * 600)          # tenths of a minute
    return f"{t // 600:02d}:{t // 10 % 60:02d}.{t % 10}"


def format_dec(degrees, high=True):
    """Dec in degrees (−90…90) → 'sDD*MM:SS' or 'sDD*MM'. The sign is always there, also for −0°30′."""
    sign = "-" if degrees < 0 else "+"
    if high:
        s = round(abs(degrees) * 3600)
        return f"{sign}{s // 3600:02d}*{s // 60 % 60:02d}:{s % 60:02d}"
    m = round(abs(degrees) * 60)
    return f"{sign}{m // 60:02d}*{m % 60:02d}"


_RA = re.compile(r"^\s*(\d{1,2}):(\d{1,2})(?::(\d{1,2})|\.(\d))?\s*$")
_DEC = re.compile(r"^\s*([+-]?)(\d{1,2})[*\xdf:'](\d{1,2})(?:[:'](\d{1,2}))?\s*$")


def parse_ra(text):
    """'HH:MM:SS' or 'HH:MM.T' → hours, or None if it isn't a valid RA."""
    m = _RA.match(text)
    if not m:
        return None
    h, mi = int(m[1]), int(m[2])
    sec = int(m[3]) if m[3] else (int(m[4]) * 6 if m[4] else 0)
    if h > 23 or mi > 59 or sec > 59:
        return None
    return h + mi / 60 + sec / 3600


def parse_dec(text):
    """'sDD*MM:SS' or 'sDD*MM' → degrees, or None if it isn't a valid Dec."""
    m = _DEC.match(text)
    if not m:
        return None
    d, mi, sec = int(m[2]), int(m[3]), int(m[4] or 0)
    if mi > 59 or sec > 59:
        return None
    value = d + mi / 60 + sec / 3600
    if value > 90:
        return None
    return -value if m[1] == "-" else value
