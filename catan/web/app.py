"""Flask + Flask-SocketIO server for Multiplayer Catan.

All game state is authoritative on the server; every mutating event is
validated here, then per-viewer snapshots are broadcast back to clients.
"""

from __future__ import annotations

import datetime
import os
import sys
from typing import Optional

from flask import Flask, jsonify, send_from_directory
from flask_login import LoginManager
from flask_socketio import SocketIO, emit, join_room

# Allow running directly without installing the package
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from catan.src.components import Resource  # noqa: E402
from catan.src.phase import TurnPhase  # noqa: E402
from catan.web.auth import auth_bp  # noqa: E402
from catan.web.db import GamePlayer, GameRecord, User, db  # noqa: E402
from catan.web.rooms import RoomManager  # noqa: E402

# ---------------------------------------------------------------------------
# App + SocketIO setup
# ---------------------------------------------------------------------------

HERE = os.path.dirname(__file__)
# In development we serve only the legacy templates page (if any); the Phase 3
# React client is served from `client/dist` when built.
CLIENT_DIST = os.path.abspath(os.path.join(HERE, "..", "client", "dist"))

app = Flask(
    __name__,
    static_folder=CLIENT_DIST if os.path.isdir(CLIENT_DIST) else "static",
    static_url_path="",
    template_folder="templates",
)
app.config["SECRET_KEY"] = os.environ.get("CATAN_SECRET", "dev-secret-change-me")
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get(
    "DATABASE_URL", "sqlite:///catan.db"
)
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db.init_app(app)
login_manager = LoginManager()
login_manager.init_app(app)


@login_manager.user_loader
def _load_user(user_id):
    return User.query.get(int(user_id))


app.register_blueprint(auth_bp)

with app.app_context():
    db.create_all()

# GameRecord id per room_id (so we can throttle persistence per turn)
_game_records: dict[str, int] = {}
_last_persisted_turn: dict[str, int] = {}

socketio = SocketIO(app, cors_allowed_origins=os.environ.get("CATAN_CORS", "*"))
rooms_manager = RoomManager()


# ---------------------------------------------------------------------------
# HTTP
# ---------------------------------------------------------------------------

@app.route("/")
def index():
    """Serve React client in prod; fall back to a tiny message in dev."""
    if os.path.isdir(CLIENT_DIST):
        return send_from_directory(CLIENT_DIST, "index.html")
    return (
        "<h1>Catan dev server</h1>"
        "<p>Run the Vite dev server from <code>catan/client</code> "
        "and open <a href='http://localhost:5173'>http://localhost:5173</a>.</p>",
        200,
    )


@app.route("/<path:filename>")
def static_file(filename):
    if os.path.isdir(CLIENT_DIST):
        full = os.path.join(CLIENT_DIST, filename)
        if os.path.isfile(full):
            return send_from_directory(CLIENT_DIST, filename)
    return ("", 404)


@app.route("/api/health")
def health():
    return jsonify({"ok": True, "rooms": len(rooms_manager.rooms)})


@app.route("/api/rooms")
def list_rooms():
    return jsonify(rooms_manager.public_rooms())


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _err(message: str):
    emit("error", {"message": message})


def _broadcast_state(room, dice_event: Optional[int] = None):
    """Emit per-viewer game state + log to every seat in the room.

    Each connected seat receives the state redacted to their own hand.
    Bots (no sid) don't receive events.
    """
    if room.game is None:
        return
    for seat in room.seats:
        if seat.sid is None:
            continue
        snapshot = room.game.to_dict(viewer_name=seat.name)
        socketio.emit("game:state", snapshot, to=seat.sid)
    if dice_event is not None:
        socketio.emit("game:dice", {"roll": dice_event}, room=room.id)
    _persist_snapshot(room)
    if room.game.phase == TurnPhase.GAME_OVER and room.game.winner is not None:
        socketio.emit(
            "game:over",
            {"winner": room.game.winner.name, "victory_points": room.game.winner.victory_points},
            room=room.id,
        )
        _persist_game_over(room)


def _persist_snapshot(room):
    """Save a full-state snapshot to the DB once per turn."""
    if room.game is None:
        return
    try:
        with app.app_context():
            record_id = _game_records.get(room.id)
            if record_id is None:
                record = GameRecord(room_code=room.id, status="in_progress")
                # Link host user if authenticated when they created the room (best-effort)
                host_user = User.query.filter_by(username=room.host_name).first()
                if host_user is not None:
                    record.host_id = host_user.id
                db.session.add(record)
                db.session.flush()
                for seat in room.seats:
                    player = room.game.get_player(seat.name)
                    if player is None:
                        continue
                    u = User.query.filter_by(username=seat.name).first()
                    gp = GamePlayer(
                        game_id=record.id,
                        user_id=u.id if u else None,
                        display_name=seat.name,
                        color=player.color,
                    )
                    db.session.add(gp)
                db.session.commit()
                _game_records[room.id] = record.id
                record_id = record.id
            # Throttle: only persist snapshot on turn change
            last = _last_persisted_turn.get(room.id, -1)
            if room.game.turn != last:
                record = GameRecord.query.get(record_id)
                if record is not None:
                    record.set_snapshot(room.game.to_dict())
                    db.session.commit()
                _last_persisted_turn[room.id] = room.game.turn
    except Exception as exc:  # noqa: BLE001 - DB errors shouldn't kill the game loop
        print(f"[persist] skipped snapshot for room {room.id}: {exc}")


def _persist_game_over(room):
    if room.game is None or room.game.winner is None:
        return
    try:
        with app.app_context():
            record_id = _game_records.get(room.id)
            if record_id is None:
                return
            record = GameRecord.query.get(record_id)
            if record is None:
                return
            record.status = "completed"
            record.ended_at = datetime.datetime.utcnow()
            record.winner_name = room.game.winner.name
            winner_user = User.query.filter_by(username=room.game.winner.name).first()
            if winner_user is not None:
                record.winner_id = winner_user.id
                winner_user.wins = (winner_user.wins or 0) + 1
            record.set_snapshot(room.game.to_dict())
            for gp in record.players:
                player = room.game.get_player(gp.display_name)
                if player is not None:
                    gp.final_vp = player.public_victory_points
                if gp.user is not None:
                    gp.user.games_played = (gp.user.games_played or 0) + 1
            db.session.commit()
    except Exception as exc:  # noqa: BLE001
        print(f"[persist] game-over persist failed: {exc}")


def _broadcast_lobby(room):
    socketio.emit("lobby:update", room.public_lobby_dict(), room=room.id)


def _resolve_player(room):
    """Return the current sid's Player in this room, or None."""
    from flask import request
    _, name = rooms_manager.room_for_sid(request.sid)
    if name is None or room.game is None:
        return None
    return room.game.get_player(name)


# ---------------------------------------------------------------------------
# Lobby events
# ---------------------------------------------------------------------------

@socketio.on("lobby:create")
def on_lobby_create(data):
    from flask import request
    username = (data or {}).get("username", "").strip()
    if not username or len(username) > 20:
        _err("Username must be 1-20 characters")
        return
    room = rooms_manager.create_room(username, request.sid)
    join_room(room.id)
    emit("lobby:created", {"room_id": room.id, "you": username})
    _broadcast_lobby(room)


@socketio.on("lobby:join")
def on_lobby_join(data):
    from flask import request
    username = (data or {}).get("username", "").strip()
    room_id = (data or {}).get("room_id", "").strip().upper()
    if not username or not room_id:
        _err("Missing username or room id")
        return
    room, err = rooms_manager.join_room(room_id, username, request.sid)
    if err is not None:
        _err(err)
        return
    join_room(room.id)
    emit("lobby:joined", {"room_id": room.id, "you": username})
    _broadcast_lobby(room)
    if room.started:
        _broadcast_state(room)


@socketio.on("lobby:add_bot")
def on_lobby_add_bot(_data):
    from flask import request
    _, name = rooms_manager.room_for_sid(request.sid)
    room, _ = rooms_manager.room_for_sid(request.sid)
    if room is None:
        _err("Not in a room")
        return
    updated, err = rooms_manager.add_bot(room.id, request.sid)
    if err is not None:
        _err(err)
        return
    _broadcast_lobby(updated)


@socketio.on("lobby:start")
def on_lobby_start(_data):
    from flask import request
    room, _ = rooms_manager.room_for_sid(request.sid)
    if room is None:
        _err("Not in a room")
        return
    room, err = rooms_manager.start_game(room.id, request.sid)
    if err is not None:
        _err(err)
        return
    _broadcast_lobby(room)
    socketio.emit("game:started", {"room_id": room.id}, room=room.id)
    _broadcast_state(room)
    _maybe_run_bot(room)


@socketio.on("lobby:chat")
def on_chat(data):
    from flask import request
    room, name = rooms_manager.room_for_sid(request.sid)
    if room is None or name is None:
        return
    msg = (data or {}).get("message", "").strip()
    if not msg or len(msg) > 300:
        return
    entry = {"from": name, "message": msg}
    room.chat.append(entry)
    socketio.emit("chat:message", entry, room=room.id)


@socketio.on("disconnect")
def on_disconnect():
    from flask import request
    room = rooms_manager.handle_disconnect(request.sid)
    if room is not None:
        _broadcast_lobby(room)
        if room.started:
            _broadcast_state(room)


# ---------------------------------------------------------------------------
# Setup phase
# ---------------------------------------------------------------------------

@socketio.on("setup:place_settlement")
def on_setup_settlement(data):
    from flask import request
    room, name = rooms_manager.room_for_sid(request.sid)
    if room is None or room.game is None:
        _err("Not in a game")
        return
    player = room.game.get_player(name)
    if player is None:
        return
    vertex = (data or {}).get("vertex")
    ok, msg = room.game.place_setup_settlement(player, vertex)
    if not ok:
        _err(msg)
    _broadcast_state(room)


@socketio.on("setup:place_road")
def on_setup_road(data):
    from flask import request
    room, name = rooms_manager.room_for_sid(request.sid)
    if room is None or room.game is None:
        _err("Not in a game")
        return
    player = room.game.get_player(name)
    if player is None:
        return
    edge = tuple((data or {}).get("edge", ()))
    ok, msg = room.game.place_setup_road(player, edge)
    if not ok:
        _err(msg)
    _broadcast_state(room)
    _maybe_run_bot(room)


# ---------------------------------------------------------------------------
# Turn events
# ---------------------------------------------------------------------------

@socketio.on("turn:roll")
def on_roll(_data):
    from flask import request
    room, name = rooms_manager.room_for_sid(request.sid)
    if room is None or room.game is None:
        _err("Not in a game")
        return
    player = room.game.get_player(name)
    if player is None:
        return
    ok, result = room.game.roll_dice(player)
    if not ok:
        _err(str(result))
        return
    _broadcast_state(room, dice_event=int(result))
    _maybe_run_bot(room)


@socketio.on("turn:end")
def on_end_turn(_data):
    from flask import request
    room, name = rooms_manager.room_for_sid(request.sid)
    if room is None or room.game is None:
        return
    player = room.game.get_player(name)
    if player is None:
        return
    ok, msg = room.game.end_turn(player)
    if not ok:
        _err(msg)
    _broadcast_state(room)
    _maybe_run_bot(room)


# ---------------------------------------------------------------------------
# Building
# ---------------------------------------------------------------------------

@socketio.on("build:road")
def on_build_road(data):
    from flask import request
    room, name = rooms_manager.room_for_sid(request.sid)
    if room is None or room.game is None:
        return
    player = room.game.get_player(name)
    if player is None:
        return
    edge = tuple((data or {}).get("edge", ()))
    ok, msg = room.game.build_road(player, edge)
    if not ok:
        _err(msg)
    _broadcast_state(room)


@socketio.on("build:settlement")
def on_build_settlement(data):
    from flask import request
    room, name = rooms_manager.room_for_sid(request.sid)
    if room is None or room.game is None:
        return
    player = room.game.get_player(name)
    if player is None:
        return
    vertex = (data or {}).get("vertex")
    ok, msg = room.game.build_settlement(player, vertex)
    if not ok:
        _err(msg)
    _broadcast_state(room)


@socketio.on("build:city")
def on_build_city(data):
    from flask import request
    room, name = rooms_manager.room_for_sid(request.sid)
    if room is None or room.game is None:
        return
    player = room.game.get_player(name)
    if player is None:
        return
    vertex = (data or {}).get("vertex")
    ok, msg = room.game.build_city(player, vertex)
    if not ok:
        _err(msg)
    _broadcast_state(room)


# ---------------------------------------------------------------------------
# Development cards
# ---------------------------------------------------------------------------

@socketio.on("devcard:buy")
def on_devcard_buy(_data):
    from flask import request
    room, name = rooms_manager.room_for_sid(request.sid)
    if room is None or room.game is None:
        return
    player = room.game.get_player(name)
    if player is None:
        return
    ok, msg = room.game.buy_development_card(player)
    if not ok:
        _err(msg)
    _broadcast_state(room)


@socketio.on("devcard:play")
def on_devcard_play(data):
    from flask import request
    room, name = rooms_manager.room_for_sid(request.sid)
    if room is None or room.game is None:
        return
    player = room.game.get_player(name)
    if player is None:
        return
    data = data or {}
    kind = data.get("kind")
    payload = {k: v for k, v in data.items() if k != "kind"}
    ok, msg = room.game.play_development_card(player, kind, **payload)
    if not ok:
        _err(msg)
    _broadcast_state(room)


# ---------------------------------------------------------------------------
# Trading
# ---------------------------------------------------------------------------

def _parse_resource_dict(d):
    out = {}
    for k, v in (d or {}).items():
        try:
            out[Resource[k]] = int(v)
        except (KeyError, TypeError, ValueError):
            continue
    return out


@socketio.on("trade:offer")
def on_trade_offer(data):
    from flask import request
    room, name = rooms_manager.room_for_sid(request.sid)
    if room is None or room.game is None:
        return
    player = room.game.get_player(name)
    if player is None:
        return
    to_names = (data or {}).get("to") or []
    offer = _parse_resource_dict((data or {}).get("offer"))
    request_d = _parse_resource_dict((data or {}).get("request"))
    ok, res = room.game.offer_trade(player, to_names, offer, request_d)
    if not ok:
        _err(str(res))
    _broadcast_state(room)


@socketio.on("trade:accept")
def on_trade_accept(data):
    from flask import request
    room, name = rooms_manager.room_for_sid(request.sid)
    if room is None or room.game is None:
        return
    player = room.game.get_player(name)
    if player is None:
        return
    trade_id = (data or {}).get("trade_id")
    ok, msg = room.game.accept_trade(int(trade_id), player)
    if not ok:
        _err(str(msg))
    _broadcast_state(room)


@socketio.on("trade:reject")
def on_trade_reject(data):
    from flask import request
    room, name = rooms_manager.room_for_sid(request.sid)
    if room is None or room.game is None:
        return
    player = room.game.get_player(name)
    if player is None:
        return
    trade_id = (data or {}).get("trade_id")
    ok, msg = room.game.respond_trade(int(trade_id), player, False)
    if not ok:
        _err(str(msg))
    _broadcast_state(room)


@socketio.on("trade:cancel")
def on_trade_cancel(data):
    from flask import request
    room, name = rooms_manager.room_for_sid(request.sid)
    if room is None or room.game is None:
        return
    player = room.game.get_player(name)
    if player is None:
        return
    trade_id = (data or {}).get("trade_id")
    ok, msg = room.game.cancel_trade(int(trade_id), player)
    if not ok:
        _err(str(msg))
    _broadcast_state(room)


@socketio.on("trade:maritime")
def on_maritime(data):
    from flask import request
    room, name = rooms_manager.room_for_sid(request.sid)
    if room is None or room.game is None:
        return
    player = room.game.get_player(name)
    if player is None:
        return
    try:
        give = Resource[(data or {}).get("give")]
        get = Resource[(data or {}).get("get")]
    except (KeyError, TypeError):
        _err("Invalid resource names")
        return
    ok, msg = room.game.maritime_trade(player, give, get)
    if not ok:
        _err(str(msg))
    _broadcast_state(room)


# ---------------------------------------------------------------------------
# Robber / discard
# ---------------------------------------------------------------------------

@socketio.on("robber:move")
def on_robber_move(data):
    from flask import request
    room, name = rooms_manager.room_for_sid(request.sid)
    if room is None or room.game is None:
        return
    player = room.game.get_player(name)
    if player is None:
        return
    hex_index = (data or {}).get("hex")
    ok, msg = room.game.move_robber(player, int(hex_index))
    if not ok:
        _err(str(msg))
    _broadcast_state(room)


@socketio.on("robber:steal")
def on_robber_steal(data):
    from flask import request
    room, name = rooms_manager.room_for_sid(request.sid)
    if room is None or room.game is None:
        return
    player = room.game.get_player(name)
    if player is None:
        return
    target = (data or {}).get("target")
    ok, msg = room.game.steal_from(player, target)
    if not ok:
        _err(str(msg))
    _broadcast_state(room)


@socketio.on("discard:submit")
def on_discard(data):
    from flask import request
    room, name = rooms_manager.room_for_sid(request.sid)
    if room is None or room.game is None:
        return
    player = room.game.get_player(name)
    if player is None:
        return
    resources = _parse_resource_dict((data or {}).get("resources"))
    ok, msg = room.game.submit_discard(player, resources)
    if not ok:
        _err(str(msg))
    _broadcast_state(room)
    _maybe_run_bot(room)


# ---------------------------------------------------------------------------
# Bot integration (Phase 6 — hooks live here; implementation in ai/bot.py)
# ---------------------------------------------------------------------------

def _maybe_run_bot(room):
    """Advance any bot whose turn it is (or who owes a discard)."""
    if room.game is None:
        return
    try:
        from catan.ai.bot import advance_bots  # lazy import
    except Exception:
        return
    while True:
        changed = advance_bots(room.game)
        if not changed:
            break
    _broadcast_state(room)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    port = int(os.environ.get("PORT", "5001"))
    socketio.run(app, debug=True, host="0.0.0.0", port=port, allow_unsafe_werkzeug=True)
