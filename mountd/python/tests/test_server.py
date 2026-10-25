"""The server over a real socket on localhost: replies arrive, mounts are shared, recordings replay."""
import asyncio
import io
import unittest

from mountd.fake import FakeMount
from mountd.server import Server
from tests.test_conversations import exchanges


class ServerTest(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.mount, self.record = FakeMount(), io.StringIO()
        self.server = await asyncio.start_server(Server(self.mount, self.record).handle_client, "127.0.0.1", 0)
        self.port = self.server.sockets[0].getsockname()[1]

    async def asyncTearDown(self):
        self.server.close()
        await self.server.wait_closed()

    async def ask(self, writer, reader, text, expect):
        writer.write(text.encode("latin-1"))
        await writer.drain()
        got = await asyncio.wait_for(reader.readexactly(len(expect)), 2)
        self.assertEqual(got.decode("latin-1"), expect)

    async def connect(self):
        return await asyncio.open_connection("127.0.0.1", self.port)

    async def test_goto_over_tcp(self):
        reader, writer = await self.connect()
        await self.ask(writer, reader, ":Sr 05:35:17#", "1")
        await self.ask(writer, reader, ":Sd -05*23:28#", "1")
        await self.ask(writer, reader, ":MS#", "0")
        await self.ask(writer, reader, ":GR#", "05:35:17#")
        writer.close()

    async def test_two_clients_share_the_mount(self):
        r1, w1 = await self.connect()
        r2, w2 = await self.connect()
        await self.ask(w1, r1, ":Sr 12:00:00#:Sd +10*00:00#:MS#", "110")
        await self.ask(w2, r2, ":GR#", "12:00:00#")       # the second client sees where the first one went
        w1.close()
        w2.close()

    async def test_recording_is_a_conversation_test(self):
        reader, writer = await self.connect()
        await self.ask(writer, reader, ":GVP#", "tinyscope#")
        await self.ask(writer, reader, "\x06", "P")
        writer.close()
        await asyncio.sleep(0.05)
        recorded = [e[1:] for e in exchanges(self.record.getvalue())]
        self.assertEqual(recorded, [[":GVP#", "tinyscope#"], ["\x06", "P"]])

    async def test_recording_has_times(self):
        ticks = iter([100.0, 100.25, 101.5])                     # connect, then one per exchange
        self.server.close()
        self.server = await asyncio.start_server(
            Server(self.mount, self.record, clock=lambda: next(ticks)).handle_client, "127.0.0.1", 0)
        self.port = self.server.sockets[0].getsockname()[1]
        reader, writer = await self.connect()
        await self.ask(writer, reader, ":GR#", "00:00:00#")
        await self.ask(writer, reader, ":GD#", "+90*00:00#")
        writer.close()
        await asyncio.sleep(0.05)
        times = [line for line in self.record.getvalue().splitlines() if line.startswith("# t=")]
        self.assertEqual(times, ["# t=0.250", "# t=1.500"])      # seconds since the client connected


if __name__ == "__main__":
    unittest.main()
