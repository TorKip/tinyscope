"""Sky maths: the clock → sidereal time → hour angle, and degrees ↔ motor steps.

Conventions inside mountd: RA, sidereal time and hour angle in hours, angles in degrees,
longitude positive east (the LX200's :Sg# is positive west; the session converts).
Hour angle = LST − RA, in −12…12: negative east of the meridian (rising), positive west (setting).

Sidereal time follows Meeus, Astronomical Algorithms, eq. 12.4. It wants UT1; we feed it UTC,
which is within 0.9 s of UT1: 13″ on the sky, a fifth of a half-step.
"""
from datetime import timezone

SIDEREAL_DAY = 86164.0905                       # s, one turn of the sky

# 28BYJ-48: four spur stages, 32/9 · 22/11 · 26/9 · 31/10. Sold as "64:1"; the 0.5 % matters.
GEAR_28BYJ = (32 * 22 * 26 * 31) / (9 * 11 * 9 * 10)
HALF_STEPS_PER_MOTOR_TURN = 64
PRINTED_STAGE = 5
HALF_STEPS_PER_TURN = HALF_STEPS_PER_MOTOR_TURN * GEAR_28BYJ * PRINTED_STAGE   # per axis turn, ≈ 20 379
SIDEREAL_HALF_STEP = SIDEREAL_DAY / HALF_STEPS_PER_TURN                         # s between steps when tracking


def julian_date(t):
    """A timezone-aware datetime → Julian Date. Naive times are refused: their zone is a guess."""
    if t.tzinfo is None:
        raise ValueError("julian_date needs a timezone-aware datetime")
    t = t.astimezone(timezone.utc)
    # Days since 2000-01-01 12:00 UTC (JD 2451545.0) by datetime's own calendar maths
    j2000 = t.replace(year=2000, month=1, day=1, hour=12, minute=0, second=0, microsecond=0)
    return 2451545.0 + (t - j2000).total_seconds() / 86400


def gmst(t):
    """Greenwich mean sidereal time in hours (0–24) at datetime `t`."""
    d = julian_date(t) - 2451545.0
    c = d / 36525                               # Julian centuries since J2000
    degrees = 280.46061837 + 360.98564736629 * d + 0.000387933 * c * c - c ** 3 / 38710000
    return degrees / 15 % 24


def lst(t, longitude):
    """Local sidereal time in hours (0–24): the RA on my meridian. `longitude` in degrees, east positive."""
    return (gmst(t) + longitude / 15) % 24


def hour_angle(ra, lst):
    """How far a star at `ra` is past my meridian, in hours, −12…12 (west positive)."""
    return (lst - ra + 12) % 24 - 12


def ra_at(hour_angle, lst):
    """The RA at `hour_angle` from my meridian: the inverse of hour_angle()."""
    return (lst - hour_angle) % 24


def degrees_to_steps(degrees):
    """An axis angle → the nearest whole number of half-steps (negative = backwards)."""
    return round(degrees / 360 * HALF_STEPS_PER_TURN)


def steps_to_degrees(steps):
    """Half-steps → the axis angle in degrees."""
    return steps * 360 / HALF_STEPS_PER_TURN
