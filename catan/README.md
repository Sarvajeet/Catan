# Catan Online

A multiplayer implementation of the classic Catan board game.

- **Backend**: Python 3.12, Flask, Flask-SocketIO, SQLAlchemy + SQLite/Postgres, Flask-Login, bcrypt
- **Frontend**: React 18 + TypeScript + Vite + Tailwind, Zustand, Framer Motion, Socket.IO client
- **AI**: Heuristic bot that can fill empty seats
- **Deployment**: Docker Compose (app + Postgres), GitHub Actions CI

## Game rules

See [GAME_RULES.md](GAME_RULES.md) for a rules summary.

## Architecture

```
┌────────────────┐     Socket.IO     ┌───────────────────┐     SQLAlchemy   ┌────────────┐
│ React client   │ ◀────────────────▶│ Flask + SocketIO  │ ◀───────────────▶│ Postgres   │
│ (catan/client) │                    │ (catan/web/app.py)│                  │  / SQLite  │
└────────────────┘                    └─────────┬─────────┘                  └────────────┘
                                                │
                                                ▼
                                        ┌──────────────────┐
                                        │ Game engine      │
                                        │ (catan/src/*)    │
                                        └──────────────────┘
                                                ▲
                                                │
                                        ┌──────────────────┐
                                        │ AI bot           │
                                        │ (catan/ai/bot.py)│
                                        └──────────────────┘
```

All game state is authoritative on the server. Each client receives a per-viewer
redacted snapshot so hidden information (own resources, hidden dev cards) never
leaks.

## Directory layout

```
catan/
  src/                    # pure-Python game engine (board, game, phase, player, ...)
  web/                    # Flask app, Socket.IO handlers, auth, DB models
  ai/                     # heuristic bot
  client/                 # React/TS/Vite frontend
  tests/                  # unittest suites
  Dockerfile              # multi-stage build (Vite + Flask + Gunicorn)
  docker-compose.yml      # app + postgres
  requirements.txt
  README.md
  GAME_RULES.md
```

## Local development

### Backend

```bash
pip install -r catan/requirements.txt
python -m catan.web.app     # serves on :5001
```

### Frontend

```bash
cd catan/client
npm install
npm run dev                 # Vite on :5173, proxies /socket.io and /api → :5001
```

Open <http://localhost:5173> in two browser windows to play a 2-player game
against yourself, or click **Add Bot** as the host to fill seats with AI
opponents.

### Tests

```bash
python -m unittest discover -s catan/tests -t .
cd catan/client && npm run typecheck && npm run build
```

## Socket.IO API

Client → server:

| Event | Payload |
| --- | --- |
| `lobby:create` | `{ username }` |
| `lobby:join` | `{ username, room_id }` |
| `lobby:add_bot` | `{}` |
| `lobby:start` | `{}` |
| `lobby:chat` | `{ message }` |
| `setup:place_settlement` | `{ vertex }` |
| `setup:place_road` | `{ edge: [v1, v2] }` |
| `turn:roll` / `turn:end` | `{}` |
| `build:road` / `build:settlement` / `build:city` | `{ edge }` / `{ vertex }` |
| `devcard:buy` | `{}` |
| `devcard:play` | `{ kind, ...params }` |
| `trade:offer` / `trade:accept` / `trade:reject` / `trade:cancel` / `trade:maritime` | see `web/app.py` |
| `robber:move` / `robber:steal` | `{ hex }` / `{ target }` |
| `discard:submit` | `{ resources }` |

Server → client: `lobby:created`, `lobby:joined`, `lobby:update`, `chat:message`,
`game:started`, `game:state` (per-viewer), `game:dice`, `game:over`, `error`.

REST:

| Endpoint | Description |
| --- | --- |
| `GET /api/health` | Health check |
| `GET /api/rooms` | Public lobby list |
| `POST /api/auth/register` | `{ username, password, email? }` |
| `POST /api/auth/login` | `{ username, password }` |
| `POST /api/auth/logout` | Requires login |
| `GET /api/auth/me` | Current user |
| `GET /api/auth/history` | Past games (requires login) |

## Turn state machine

```
SETUP_1 → SETUP_2 → ROLL ⇄ MAIN → ROLL (next player)
                       │
                       └→ DISCARD → MOVE_ROBBER → ROBBER_STEAL → MAIN  (if 7 is rolled)

MAIN --(VP ≥ 10)--> GAME_OVER
```

## Docker

```bash
cd catan
docker compose up --build
```

The `app` service runs Flask + Gunicorn (eventlet worker) on port 5001 and the
`db` service runs Postgres. The first-time database schema is created on
startup; set `CATAN_SECRET` in a `.env` file for a real deployment.

## Environment variables

| Variable | Default | Purpose |
| --- | --- | --- |
| `CATAN_SECRET` | `dev-secret-change-me` | Flask session secret |
| `CATAN_CORS` | `*` | Socket.IO allowed origins |
| `DATABASE_URL` | `sqlite:///catan.db` | SQLAlchemy DB URI |
| `PORT` | `5001` | HTTP port |

## Continuous integration

GitHub Actions (`.github/workflows/ci.yml`) runs:

1. Python lint (`ruff check`) and unit tests (`unittest`)
2. Frontend typecheck (`tsc`) and production build (`vite build`)
3. Docker image build
