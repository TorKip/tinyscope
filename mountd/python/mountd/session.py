"""One client's LX200 conversation: turns each command into a call on the mount and a reply.

The session holds what the protocol keeps per connection (the target set by :Sr/:Sd, the
precision); the mount holds where the telescope is, the site where and when it stands.
Commands we don't know get no reply and a log line, so a real client's session shows what it
needs next.
"""
import logging

from .lx200 import ACK, format_dec, format_ra, parse_dec, parse_ra, split_commands
from .site import Site

log = logging.getLogger("mountd.lx200")

PRODUCT = "tinyscope"
FIRMWARE = "0.1"
FIRMWARE_DATE = "Oct 25 2026"                            # Meade's format, as :GVD# returns it
FIRMWARE_TIME = "00:00:00"


class Session:
    def __init__(self, mount, site=None):
        self.mount = mount
        self.site = site if site is not None else Site()  # shared by all clients, like the handset
        self.high = True                                 # precision; ':U#' toggles it
        self._target_ra = self._target_dec = None         # set by :Sr and :Sd
        self._buffer = ""

    def feed(self, text):
        """Bytes as they arrive (any split) → the replies, joined."""
        commands, self._buffer = split_commands(self._buffer + text)
        return "".join(self.handle(c) for c in commands)

    def handle(self, command):
        if command == ACK:
            return "P"                                   # polar (equatorial) mount
        body = command[1:-1]                             # strip ':' and '#'
        for prefix, method in self._COMMANDS:
            if body.startswith(prefix):
                return method(self, body[len(prefix):].strip())
        log.warning("unknown command %r", command)
        return ""

    # --- position and target ---

    def _get_ra(self, _):
        return format_ra(self.mount.position()[0], self.high) + "#"

    def _get_dec(self, _):
        return format_dec(self.mount.position()[1], self.high) + "#"

    def _set_ra(self, arg):
        ra = parse_ra(arg)
        if ra is None:
            return "0"                                   # refused; the old target stays
        self._target_ra = ra
        return "1"

    def _set_dec(self, arg):
        dec = parse_dec(arg)
        if dec is None:
            return "0"
        self._target_dec = dec
        return "1"

    def _slew(self, _):
        if self._target_ra is None or self._target_dec is None:
            return "2No target set#"
        reason = self.mount.slew(self._target_ra, self._target_dec)
        return "0" if reason is None else f"1{reason}#"

    def _sync(self, _):
        if self._target_ra is None or self._target_dec is None:
            return "No target set#"
        self.mount.sync(self._target_ra, self._target_dec)
        return f"{PRODUCT} synced#"

    def _abort(self, _):
        self.mount.abort()
        return ""

    # --- manual moves (arrow buttons); none of these reply ---

    def _move(axis, direction):
        def move(self, _):
            self.mount.move(axis, direction)
            return ""
        return move

    def _stop(axis):
        # Either direction stops the whole axis: INDI with Reverse on stops the opposite one.
        def stop(self, _):
            self.mount.stop(axis)
            return ""
        return stop

    def _rate(name):
        def rate(self, _):
            self.mount.set_rate(name)
            return ""
        return rate

    def _park(self, _):
        self.mount.park()
        return ""

    def _distance(self, _):
        return "\x7f#" if self.mount.is_slewing() else "#"   # a bar while slewing, as on the LX200

    def _toggle_precision(self, _):
        self.high = not self.high
        return ""

    # --- identity ---

    def _product(self, _):
        return PRODUCT + "#"

    def _firmware(self, _):
        return FIRMWARE + "#"

    def _constant(text):
        def get(self, _):
            return text + "#"
        return get

    # --- site and time (site.py converts Meade's signs) ---

    def _setter(name):
        def set_(self, arg):
            return "1" if getattr(self.site, name)(arg) else "0"
        return set_

    def _getter(name):
        def get(self, _):
            return getattr(self.site, name)() + "#"
        return get

    def _set_date(self, arg):
        if not self.site.set_local_date(arg):
            return "0"
        # The classic LX200 answers a date with '1' and two strings; INDI's driver reads them.
        return "1Updating Planetary Data#" + " " * 30 + "#"

    def _sidereal_time(self, _):
        return format_ra(self.site.lst()) + "#"           # always HH:MM:SS, whatever the precision

    # Longest prefixes first: 'GVP' before 'GV', 'Sr' and 'SG' are different commands.
    _COMMANDS = [
        ("GVP", _product), ("GVN", _firmware),
        # INDI's Autostar driver asks these on connect and waits 5 s for each unanswered one
        ("GVD", _constant(FIRMWARE_DATE)), ("GVT", _constant(FIRMWARE_TIME)),
        ("GVF", _constant(f"{PRODUCT} {FIRMWARE}")), ("GM", _constant(PRODUCT)),
        ("Gc", _constant("24")),                         # 24-hour clock
        ("GT", _constant("60.1")),                       # tracking rate in Meade's unit (sidereal)
        ("GR", _get_ra), ("GD", _get_dec),
        ("Sr", _set_ra), ("Sd", _set_dec),
        ("MS", _slew), ("CM", _sync), ("D", _distance), ("U", _toggle_precision),
        ("Mn", _move("dec", +1)), ("Ms", _move("dec", -1)), ("Me", _move("ra", +1)), ("Mw", _move("ra", -1)),
        ("Qn", _stop("dec")), ("Qs", _stop("dec")), ("Qe", _stop("ra")), ("Qw", _stop("ra")), ("Q", _abort),
        ("RG", _rate("guide")), ("RC", _rate("centering")), ("RM", _rate("find")), ("RS", _rate("slew")),
        ("hP", _park),
        ("St", _setter("set_latitude")), ("Sg", _setter("set_longitude")), ("SG", _setter("set_utc_offset")),
        ("SL", _setter("set_local_time")), ("SC", _set_date),
        ("Gt", _getter("latitude_text")), ("Gg", _getter("longitude_text")),
        ("GG", _getter("utc_offset_text")), ("GL", _getter("local_time_text")),
        ("GC", _getter("local_date_text")), ("GS", _sidereal_time),
    ]
