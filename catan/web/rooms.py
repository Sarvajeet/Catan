"""In-memory room + player-session manager.

A "room" is a lobby + optional Game. Sessions map socket.io sids to
(room_id, username) so we can route events after disconnect/reconnect.

Phase 5 will replace this with a DB-backed implementation.
"""

from __future__ import annotations

import secrets
from dataclasses import dataclass, field
from typing import Dict, List, Optional

from catan.src.game import Game


MAX_PLAYERS = 4
MIN_PLAYERS = 2


@dataclass
class Seat:
    name: str
    is_bot: bool = False
    sid: Optional[str] = None  # current socket.io sid; None if disconnected


@dataclass
class Room:
    id: str
    host_name: str
    seats: List[Seat] = field(default_factory=list)
    started: bool = False
    game: Optional[Game] = None
    chat: List[dict] = field(default_factory=list)

    def is_full(self):
        return len(self.seats) >= MAX_PLAYERS

    def has_player(self, name: str) -> bool:
        return any(s.name == name for s in self.seats)

    def get_seat(self, name: str) -> Optional[Seat]:
        return next((s for s in self.seats if s.name == name), None)

    def player_names(self) -> List[str]:
        return [s.name for s in self.seats]

    def bot_flags(self) -> List[bool]:
        return [s.is_bot for s in self.seats]

    def public_lobby_dict(self) -> dict:
        return {
            "id": self.id,
            "host": self.host_name,
            "started": self.started,
            "players": [
                {"name": s.name, "is_bot": s.is_bot, "connected": s.sid is not None}
                for s in self.seats
            ],
        }


class RoomManager:
    def __init__(self):
        self.rooms: Dict[str, Room] = {}
        # sid -> (room_id, username)
        self.sessions: Dict[str, tuple[str, str]] = {}

    # ---------------- room lifecycle ----------------

    def new_room_id(self) -> str:
        while True:
            rid = secrets.token_hex(3).upper()  # e.g. 'A1B2C3'
            if rid not in self.rooms:
                return rid

    def create_room(self, host_name: str, sid: str) -> Room:
        rid = self.new_room_id()
        room = Room(id=rid, host_name=host_name)
        room.seats.append(Seat(name=host_name, sid=sid))
        self.rooms[rid] = room
        self.sessions[sid] = (rid, host_name)
        return room

    def join_room(self, room_id: str, name: str, sid: str) -> tuple[Optional[Room], Optional[str]]:
        room = self.rooms.get(room_id)
        if room is None:
            return None, "Room not found"
        # If name already exists and is disconnected, treat as reconnect
        existing = room.get_seat(name)
        if existing is not None:
            if existing.sid is None:
                existing.sid = sid
                self.sessions[sid] = (room_id, name)
                if room.game is not None:
                    player = room.game.get_player(name)
                    if player is not None:
                        player.connected = True
                return room, None
            else:
                return None, "Name already in use"
        if room.started:
            return None, "Game already started"
        if room.is_full():
            return None, "Room is full"
        room.seats.append(Seat(name=name, sid=sid))
        self.sessions[sid] = (room_id, name)
        return room, None

    def add_bot(self, room_id: str, host_sid: str) -> tuple[Optional[Room], Optional[str]]:
        room = self.rooms.get(room_id)
        if room is None:
            return None, "Room not found"
        if room.started:
            return None, "Game started"
        if room.is_full():
            return None, "Room full"
        session = self.sessions.get(host_sid)
        if session is None or session[1] != room.host_name:
            return None, "Only host can add bots"
        # Generate a unique bot name
        n = sum(1 for s in room.seats if s.is_bot) + 1
        base = f"Bot-{n}"
        name = base
        i = 2
        while room.has_player(name):
            name = f"{base}-{i}"
            i += 1
        room.seats.append(Seat(name=name, is_bot=True))
        return room, None

    def start_game(self, room_id: str, requester_sid: str) -> tuple[Optional[Room], Optional[str]]:
        room = self.rooms.get(room_id)
        if room is None:
            return None, "Room not found"
        session = self.sessions.get(requester_sid)
        if session is None or session[1] != room.host_name:
            return None, "Only host can start"
        if len(room.seats) < MIN_PLAYERS:
            return None, f"Need at least {MIN_PLAYERS} players"
        if room.started:
            return None, "Already started"
        room.game = Game(room.player_names(), is_bot_flags=room.bot_flags())
        room.started = True
        return room, None

    # ---------------- disconnect / lookup ----------------

    def handle_disconnect(self, sid: str) -> Optional[Room]:
        session = self.sessions.pop(sid, None)
        if session is None:
            return None
        room_id, name = session
        room = self.rooms.get(room_id)
        if room is None:
            return None
        seat = room.get_seat(name)
        if seat is not None:
            seat.sid = None
        if room.game is not None:
            player = room.game.get_player(name)
            if player is not None:
                player.connected = False
        # If the room is empty and not started, drop it.
        if not room.started and all(s.sid is None for s in room.seats):
            del self.rooms[room_id]
            return None
        return room

    def room_for_sid(self, sid: str) -> tuple[Optional[Room], Optional[str]]:
        session = self.sessions.get(sid)
        if session is None:
            return None, None
        rid, name = session
        return self.rooms.get(rid), name

    def public_rooms(self) -> list[dict]:
        return [r.public_lobby_dict() for r in self.rooms.values() if not r.started]
