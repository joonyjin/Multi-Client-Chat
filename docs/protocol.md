# Protocol Specification (v1)

Status: Draft
Requirements covered: FR-1 to FR-5, NFR-3

## 1. Transport

- TCP, UTF-8 encoded text
- Framing: JSON Lines. One message is one JSON object followed by `\n`.
- Maximum message size: 4096 bytes, including the trailing `\n`.
- Every message is a JSON object with a required string field `type`.
- Unknown extra fields are ignored.

## 2. Connection State

```
CONNECTED --login--> LOGGED_IN --join--> (member of one or more rooms)
```

- In `CONNECTED`, only `login` and `quit` are accepted.
- In `LOGGED_IN`, `join`, `leave`, `msg`, and `quit` are accepted.
- A client may be a member of multiple rooms at the same time.
- Membership is tracked per room. `msg` and `leave` act only on the room named in the `room` field.
- Rooms are created on first join and removed when the last member leaves.

## 3. Client to Server Messages

| type | Fields | Description |
|------|--------|-------------|
| `login` | `nick` | Register a nickname (FR-1) |
| `join` | `room` | Join a room (FR-2) |
| `leave` | `room` | Leave a room (FR-2) |
| `msg` | `room`, `text` | Send a message to a room (FR-3) |
| `quit` | none | Close the session gracefully |

Examples:

```
{"type":"login","nick":"alice"}
{"type":"join","room":"general"}
{"type":"msg","room":"general","text":"hello"}
{"type":"leave","room":"general"}
{"type":"quit"}
```

## 4. Server to Client Messages

| type | Fields | Description |
|------|--------|-------------|
| `ok` | `ref` | The request of type `ref` succeeded |
| `error` | `code`, `message` | The request failed (FR-5) |
| `msg` | `room`, `from`, `text`, `ts` | A message broadcast in a room (FR-3) |
| `event` | `kind`, `room`, `nick` | A room event, `kind` is `join` or `leave` (FR-4) |

Examples:

```
{"type":"ok","ref":"login"}
{"type":"error","code":"NICK_TAKEN","message":"nickname already in use"}
{"type":"msg","room":"general","from":"alice","text":"hello","ts":1764201600}
{"type":"event","kind":"join","room":"general","nick":"bob"}
```

`ts` is a Unix timestamp in seconds, set by the server.

## 5. Field Rules

| Field | Rule |
|-------|------|
| `nick` | 3 to 16 characters, `[A-Za-z0-9]` only, unique among connected clients |
| `room` | 1 to 32 characters, `[a-z0-9-]` only |
| `text` | 1 to 1000 characters |

## 6. Behavior

- **login**: On success the server replies `ok`. The nickname is released when the connection closes.
- **join**: On success the server replies `ok` to the sender and sends `event` (`join`) to the other members of the room.
- **leave**: On success the server replies `ok` to the sender and sends `event` (`leave`) to the remaining members.
- **msg**: The sender must be a member of the room. The server sends `msg` to all other members and replies `ok` to the sender. The sender does not receive its own message back.
- **quit**: The server closes the connection after cleanup.
- **Disconnect (graceful or abnormal)**: The server removes the client from all rooms and sends `event` (`leave`) for each room. A failing client must not affect delivery to other clients (NFR-3).

## 7. Errors

Each `error` message has a machine-readable `code` and a human-readable `message`.

| Code | Fatal | Meaning |
|------|-------|---------|
| `INVALID_JSON` | yes | The line is not valid JSON or not a JSON object |
| `MESSAGE_TOO_LARGE` | yes | The line exceeds 4096 bytes |
| `UNKNOWN_TYPE` | no | Missing or unsupported `type` |
| `INVALID_FIELD` | no | A required field is missing or violates the field rules |
| `NOT_LOGGED_IN` | no | The request requires login first |
| `ALREADY_LOGGED_IN` | no | `login` sent twice on the same connection |
| `NICK_TAKEN` | no | The nickname is already in use |
| `ALREADY_IN_ROOM` | no | `join` for a room the client is already in |
| `NOT_IN_ROOM` | no | `leave` or `msg` for a room the client is not in |

For fatal errors the server sends the `error` message and then closes the connection. For non-fatal errors the connection stays open.

## 8. Example Session

```
C: {"type":"login","nick":"alice"}
S: {"type":"ok","ref":"login"}
C: {"type":"join","room":"general"}
S: {"type":"ok","ref":"join"}
S: {"type":"event","kind":"join","room":"general","nick":"bob"}
C: {"type":"msg","room":"general","text":"hi bob"}
S: {"type":"ok","ref":"msg"}
S: {"type":"msg","room":"general","from":"bob","text":"hi alice","ts":1764201612}
C: {"type":"quit"}
```

## 9. Future Extensions (out of scope for v1)

- Version handshake (`hello` message)
- Heartbeat / idle timeout
- Length-prefixed framing for binary safety
- Authentication and TLS
- Direct messages
