"""SQLAlchemy DB + Flask-Login user models."""

from __future__ import annotations

import json
from datetime import datetime
from typing import Optional

import bcrypt
from flask_login import UserMixin
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class User(UserMixin, db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(32), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=True)
    password_hash = db.Column(db.String(128), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    wins = db.Column(db.Integer, default=0, nullable=False)
    games_played = db.Column(db.Integer, default=0, nullable=False)

    def set_password(self, password: str) -> None:
        self.password_hash = bcrypt.hashpw(
            password.encode("utf-8"), bcrypt.gensalt()
        ).decode("utf-8")

    def check_password(self, password: str) -> bool:
        try:
            return bcrypt.checkpw(
                password.encode("utf-8"), self.password_hash.encode("utf-8")
            )
        except ValueError:
            return False

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "username": self.username,
            "wins": self.wins,
            "games_played": self.games_played,
            "win_rate": (self.wins / self.games_played) if self.games_played else 0.0,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class GameRecord(db.Model):
    __tablename__ = "game_records"

    id = db.Column(db.Integer, primary_key=True)
    room_code = db.Column(db.String(16), index=True, nullable=False)
    host_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    status = db.Column(db.String(16), default="in_progress", nullable=False)
    winner_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    winner_name = db.Column(db.String(32), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    ended_at = db.Column(db.DateTime, nullable=True)
    snapshot_json = db.Column(db.Text, nullable=True)

    host = db.relationship("User", foreign_keys=[host_id])
    winner = db.relationship("User", foreign_keys=[winner_id])
    players = db.relationship(
        "GamePlayer", back_populates="game", cascade="all, delete-orphan"
    )

    def set_snapshot(self, snapshot: dict) -> None:
        self.snapshot_json = json.dumps(snapshot)

    def get_snapshot(self) -> Optional[dict]:
        if self.snapshot_json is None:
            return None
        return json.loads(self.snapshot_json)


class GamePlayer(db.Model):
    __tablename__ = "game_players"

    id = db.Column(db.Integer, primary_key=True)
    game_id = db.Column(
        db.Integer, db.ForeignKey("game_records.id"), nullable=False, index=True
    )
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    display_name = db.Column(db.String(32), nullable=False)
    color = db.Column(db.String(16), nullable=False)
    final_vp = db.Column(db.Integer, default=0, nullable=False)

    game = db.relationship("GameRecord", back_populates="players")
    user = db.relationship("User")
