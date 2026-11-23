"""TCP Client (asyncio, Python 3.14)

To use : python3 client.py --host <Server IP> --port 9000
"""

import argparse
import asyncio
import sys


async def receive(reader: asyncio.StreamReader) -> None:
    while True:
        data = await reader.readline()
        if not data:
            print("\n[Connection closed]")
            return
        print(data.decode(errors="replace").rstrip())


async def send(writer: asyncio.StreamWriter) -> None:
    loop = asyncio.get_running_loop()
    while True:
        try:
            line = await loop.run_in_executor(None, sys.stdin.readline)
        except (EOFError, KeyboardInterrupt):
            break
        if not line:  # EOF (Ctrl+D)
            break
        writer.write(line.encode())
        await writer.drain()
        if line.strip() == "/quit":
            break


async def main() -> None:
    parser = argparse.ArgumentParser(description="TCP Client")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=55555)
    args = parser.parse_args()

    try:
        reader, writer = await asyncio.open_connection(args.host, args.port)
    except OSError as e:
        print(f"Server Connection failed: {e}")
        return

    recv_task = asyncio.create_task(receive(reader))
    send_task = asyncio.create_task(send(writer))

    done, pending = await asyncio.wait({recv_task, send_task},
                                       return_when=asyncio.FIRST_COMPLETED)
    for t in pending:
        t.cancel()
    writer.close()
    try:
        await writer.wait_closed()
    except OSError:
        pass


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nEnded")

