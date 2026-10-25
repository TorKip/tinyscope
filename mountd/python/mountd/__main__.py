"""python3 -m mountd --fake [--host 127.0.0.1] [--port 4030] [--record session.txt] [-v]"""
import argparse
import asyncio
import logging

from .fake import FakeMount
from .server import Server


def main():
    p = argparse.ArgumentParser(prog="mountd", description="tinyscope's mount daemon (LX200 over TCP)")
    p.add_argument("--fake", action="store_true", help="a simulated mount that moves instantly (the only one so far)")
    p.add_argument("--host", default="127.0.0.1", help="0.0.0.0 to accept clients from the network")
    p.add_argument("--port", type=int, default=4030, help="4030 is SkySafari's default for LX200 over Wi-Fi")
    p.add_argument("--record", metavar="FILE", help="append every exchange in the conversation-test format")
    p.add_argument("-v", "--verbose", action="store_true")
    args = p.parse_args()
    logging.basicConfig(level=logging.INFO if args.verbose else logging.WARNING,
                        format="%(asctime)s %(name)s %(levelname)s %(message)s")
    if not args.fake:
        p.error("only --fake exists so far (the GPIO back-end is slice 7)")
    record = open(args.record, "a") if args.record else None
    try:
        asyncio.run(Server(FakeMount(), record).serve(args.host, args.port))
    except KeyboardInterrupt:
        pass
    finally:
        if record:
            record.close()


if __name__ == "__main__":
    main()
