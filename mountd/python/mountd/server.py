"""LX200 over TCP: each client gets its own Session; all of them share one mount and one site.

With `record`, every exchange is appended in the conversation-file format, so a session with a
real client (Ekos, SkySafari) becomes a conversation test by copying the file into
mountd/conversations/. A '# t=1.234' comment before each exchange gives the seconds since the
client connected, so a recording also shows how often a client polls.
"""
import asyncio
import datetime
import logging
import time

from .session import Session
from .site import Site

log = logging.getLogger("mountd.server")


def _escape(text):
    return text.encode("unicode_escape").decode("ascii")


class Server:
    def __init__(self, mount, record=None, clock=time.monotonic, site=None):
        self.mount = mount
        self.site = site if site is not None else Site()
        self.record = record                     # an open text file, or None
        self.clock = clock

    async def handle_client(self, reader, writer):
        peer = writer.get_extra_info("peername")
        log.info("client connected: %s", peer)
        session = Session(self.mount, self.site)
        start = self.clock()
        if self.record:
            self.record.write(f"# client {peer} at {datetime.datetime.now().isoformat(timespec='seconds')}\n")
        try:
            while data := await reader.read(256):
                text = data.decode("latin-1")    # LX200 is bytes; latin-1 keeps 0xDF and 0x06 as they are
                reply = session.feed(text)
                if self.record:
                    self.record.write(f"# t={self.clock() - start:.3f}\n> {_escape(text)}\n" + (f"< {_escape(reply)}\n" if reply else ""))
                    self.record.flush()
                if reply:
                    writer.write(reply.encode("latin-1"))
                    await writer.drain()
        except ConnectionError:
            pass
        finally:
            log.info("client gone: %s", peer)
            writer.close()

    async def serve(self, host, port):
        server = await asyncio.start_server(self.handle_client, host, port)
        log.info("LX200 on %s:%d", host, port)
        async with server:
            await server.serve_forever()
