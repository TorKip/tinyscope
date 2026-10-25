"""Where the mount stands and what time it is: what LX200 clients set with :St :Sg :SG :SL :SC.

One Site is shared by all clients, as on a real handset: Ekos sets it, SkySafari reads it back.

The clock is the system clock plus an offset. The Pi 3B has no battery-backed clock, so in the
field with no network the time a client sends is the only good time; setting it keeps the
difference from the system clock, and the clock keeps running from there.

Meade's conventions, converted here so the rest of mountd never sees them:
    :Sg sDDD*MM   longitude, positive WEST (mountd: positive east, −180…180)
    :SG sHH.H     hours to ADD to local time to get UTC (CET, UTC+1, is −1)
    :SL :SC       local time HH:MM:SS and local date MM/DD/YY
"""
import re
import time
from datetime import datetime, timedelta, timezone

from . import sky
from .lx200 import parse_dec

_LONGITUDE = re.compile(r"^\s*([+-]?)(\d{1,3})[*\xdf:'](\d{1,2})\s*$")
_OFFSET = re.compile(r"^\s*([+-]?\d{1,2}(?:\.\d)?)\s*$")


class Site:
    def __init__(self, latitude=60.0, longitude=0.0, utc_offset=0.0, clock=time.time):
        self.latitude, self.longitude = latitude, longitude   # degrees, longitude east positive
        self.utc_offset = utc_offset                          # Meade's sign: UTC = local + offset
        self.clock = clock                                    # seconds since 1970, like time.time
        self._ahead = 0.0                                     # s the client's clock is ahead of ours

    # --- time ---

    def now(self):
        """The time as the clients set it, timezone-aware UTC."""
        return datetime.fromtimestamp(self.clock() + self._ahead, timezone.utc)

    def local(self):
        """Local time as a naive datetime: the clock a client set with :SL/:SC, read back by :GL/:GC."""
        return (self.now() - timedelta(hours=self.utc_offset)).replace(tzinfo=None)

    def lst(self):
        """Local sidereal time in hours: the RA on my meridian right now."""
        return sky.lst(self.now(), self.longitude)

    def _set_local(self, local):
        utc = (local + timedelta(hours=self.utc_offset)).replace(tzinfo=timezone.utc)
        self._ahead = utc.timestamp() - self.clock()

    # --- the LX200 setters: True if accepted ---

    def set_latitude(self, text):
        value = parse_dec(text)                               # same shape as a Dec: sDD*MM
        if value is None:
            return False
        self.latitude = value
        return True

    def set_longitude(self, text):
        m = _LONGITUDE.match(text)
        if not m or int(m[2]) > 360 or int(m[3]) > 59:
            return False
        west = int(m[2]) + int(m[3]) / 60
        if m[1] == "-":
            west = -west
        self.longitude = (180 - west) % 360 - 180         # flip to east positive; 355*00 W is 5° E
        return True

    def set_utc_offset(self, text):
        """Changes how local time is shown; the UTC time stays (the sky doesn't care about zones)."""
        m = _OFFSET.match(text)
        if not m or abs(float(m[1])) > 14:
            return False
        self.utc_offset = float(m[1])
        return True

    def set_local_time(self, text):
        try:
            t = datetime.strptime(text.strip(), "%H:%M:%S").time()
        except ValueError:
            return False
        self._set_local(datetime.combine(self.local().date(), t))
        return True

    def set_local_date(self, text):
        try:
            d = datetime.strptime(text.strip(), "%m/%d/%y").date()   # %y: 69–99 → 19xx, 00–68 → 20xx
        except ValueError:
            return False
        self._set_local(datetime.combine(d, self.local().time()))
        return True

    # --- the LX200 getters, in Meade's formats ---

    def latitude_text(self):
        m = round(abs(self.latitude) * 60)
        return f"{'-' if self.latitude < 0 else '+'}{m // 60:02d}*{m % 60:02d}"

    def longitude_text(self):
        west = -self.longitude
        m = round(abs(west) * 60)
        return f"{'-' if west < 0 else '+'}{m // 60:03d}*{m % 60:02d}"

    def utc_offset_text(self):
        o = self.utc_offset
        return f"{o:+03.0f}" if o == int(o) else f"{o:+05.1f}"

    def local_time_text(self):
        return self.local().strftime("%H:%M:%S")

    def local_date_text(self):
        return self.local().strftime("%m/%d/%y")
