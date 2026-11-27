# ADR 0001: Message Framing for the TCP Protocol

Status: Accepted
Date: 2026-11-27
Related: docs/protocol.md, FR-3, NFR-3

## Context

TCP is a byte stream and does not preserve message boundaries. A single `recv()` may return a partial message or several messages at once. The protocol therefore needs an explicit framing rule so that both sides can split the stream into messages.

## Options Considered

1. **JSON Lines**: one JSON object per line, terminated by `\n`.
2. **Length-prefixed frames**: a 4-byte length header followed by the payload.

## Decision

Use **JSON Lines** with a maximum message size of 8192 bytes.

### Why 8192 bytes

- The `text` field is limited to 1000 characters. In UTF-8 a character takes up to 4 bytes (3 bytes for Korean, 4 for emoji), so the worst case is about 4000 bytes of text.
- A server-to-client `msg` adds `type`, `room`, `from`, `ts`, and JSON syntax, about 100 to 150 bytes.
- The worst case is therefore about 4.2 KB. The limit is set at roughly twice that to leave headroom for future fields.
- The limit is still small enough to protect the server from clients that send very long lines without a newline.
- Both sides must serialize JSON with `ensure_ascii=False`. With the default escaping, non-ASCII characters grow to 6 bytes each and could exceed the limit.

## Rationale

- Easy to debug: a session can be tested manually with `nc` or `telnet`.
- Human-readable logs and test fixtures.
- asyncio provides `StreamReader.readline()`, so the server needs very little framing code.
- The size limit protects the server from clients that never send a newline (see `MESSAGE_TOO_LARGE` in protocol.md).

## Consequences

- Payloads must be valid UTF-8 JSON. Raw binary data is not supported without encoding (for example base64).
- Messages must not contain a raw newline. JSON string escaping (`\n`) already guarantees this.
- The server must enforce the 8192-byte limit itself, because `readline()` has its own default limit that must be configured.
- If binary payloads or higher throughput are needed later, the framing can be replaced with length-prefixed frames. This would require a new protocol version.
