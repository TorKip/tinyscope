"""LX200 over TCP: each client gets its own Session; all of them share one mount.

With `record`, every exchange is appended in the conversation-file format, so a session with a
real client (Ekos, SkySafari) becomes a conversation test by copying the file into
mountd/conversations/.
"""
import asyncio
import logging

from .session import Session

log = logging.getLogger("mountd.server")


def _escape(text):
    return text.encode("unicode_escape").decode("ascii")


class Server:
    def __init__(self, mount, record=None):
        self.mount = mount
        self.record = record                     # an open text file, or None

    async def handle_client(self, reader, writer):
        peer = writer.get_extra_info("peername")
        log.info("client connected: %s", peer)
        session = Session(self.mount)
        if self.record:
            self.record.write(f"# client {peer}\n")
        try:
            while data := await reader.read(256):
                text = data.decode("latin-1")    # LX200 is bytes; latin-1 keeps 0xDF and 0x06 as they are
                reply = session.feed(text)
                if self.record:
                    self.record.write(f"> {_escape(text)}\n" + (f"< {_escape(reply)}\n" if reply else ""))
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
