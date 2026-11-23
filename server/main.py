"""Multi-Client Chat Server (asyncio, Python 3.14)

Protocol: UTF-8 text, One line(\n) = One message.
Command:
  /nick <name>        change nickname
  /list               list of online users
  /w <name> <message>   private chat
  /quit               close
"""
import argparse
import asyncio
import logging

log = logging.getLogger("chat-server")

MAX_LINE = 4096  # byte


class ChatServer:
    def __init__(self) -> None:
        # nickname -> StreamWriter
        self.clients: dict[str, asyncio.StreamWriter] = {}
        self._counter = 0

    def _new_nick(self) -> str:
        self._counter += 1
        return f"user{self._counter}"

    async def send(self, writer: asyncio.StreamWriter, text: str) -> None:
        try:
            writer.write((text + "\n").encode())
            await writer.drain()
        except (ConnectionError, OSError):
            pass  # if a client closed connection -> handle() -> finally

    async def broadcast(self, text: str, exclude: str | None = None) -> None:
        targets = [w for n, w in self.clients.items() if n != exclude]
        await asyncio.gather(*(self.send(w, text) for w in targets))

    async def handle(self, reader: asyncio.StreamReader,
                     writer: asyncio.StreamWriter) -> None:
        addr = writer.get_extra_info("peername")
        nick = self._new_nick()
        self.clients[nick] = writer
        log.info("login: %s (%s)", nick, addr)

        await self.send(writer, f"[server] Welcome your nickname: {nick} "
                                f"(/nick, /list, /w, /quit)")
        await self.broadcast(f"[server] {nick} has joined the chat.", exclude=nick)

        try:
            while True:
                try:
                    raw = await reader.readuntil(b"\n")
                except asyncio.IncompleteReadError:
                    break  # 연결 종료
                except asyncio.LimitOverrunError:
                    await self.send(writer, "[server] message too long.")
                    break

                line = raw.decode(errors="replace").strip()
                if not line:
                    continue

                if line.startswith("/"):
                    nick, keep = await self.command(nick, writer, line)
                    if not keep:
                        break
                else:
                    log.info("%s: %s", nick, line)
                    await self.broadcast(f"[{nick}] {line}")
        except (ConnectionError, OSError):
            pass
        finally:
            self.clients.pop(nick, None)
            writer.close()
            try:
                await writer.wait_closed()
            except (ConnectionError, OSError):
                pass
            log.info("Closed connection: %s (%s)", nick, addr)
            await self.broadcast(f"[server] {nick} has left the chat.")

    async def command(self, nick: str, writer: asyncio.StreamWriter,
                      line: str) -> tuple[str, bool]:
        """Process commands."""
        cmd, _, rest = line.partition(" ")
        rest = rest.strip()

        match cmd:
            case "/quit":
                await self.send(writer, "[서버] 안녕히 가세요!")
                return nick, False

            case "/list":
                names = ", ".join(sorted(self.clients))
                await self.send(writer, f"[server] Online({len(self.clients)}): {names}")

            case "/nick":
                new = rest.split()[0] if rest else ""
                if not new or len(new) > 16:
                    await self.send(writer, "[server] To use : /nick <1~16 length of new nickname>")
                elif new in self.clients:
                    await self.send(writer, "[server] already in use.")
                else:
                    del self.clients[nick]
                    self.clients[new] = writer
                    await self.broadcast(f"[server] nickname has changed to {nick} → {new}")
                    nick = new

            case "/w":
                target, _, msg = rest.partition(" ")
                msg = msg.strip()
                if not target or not msg:
                    await self.send(writer, "[server] To use : /w <name> <message>")
                elif target not in self.clients:
                    await self.send(writer, f"[server] can't find '{target}'.")
                else:
                    await self.send(self.clients[target], f"[Private {nick}] {msg}")
                    await self.send(writer, f"[Private → {target}] {msg}")

            case _:
                await self.send(writer, f"[server] command not found: {cmd}")

        return nick, True


async def main() -> None:
    parser = argparse.ArgumentParser(description="TCP MCS server")
    parser.add_argument("--host", default="0.0.0.0")
    parser.add_argument("--port", type=int, default=9000)
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO,
                        format="%(asctime)s %(levelname)s %(message)s")

    chat = ChatServer()
    server = await asyncio.start_server(chat.handle, args.host, args.port,
                                        limit=MAX_LINE)
    addrs = ", ".join(str(s.getsockname()) for s in server.sockets)
    log.info("Server starts: %s", addrs)

    async with server:
        await server.serve_forever()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        log.info("server closed")

