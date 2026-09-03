"""HTTP auth endpoints: register, login, logout, profile, history."""

from __future__ import annotations

import re

from flask import Blueprint, jsonify, request
from flask_login import current_user, login_required, login_user, logout_user

from catan.web.db import GamePlayer, GameRecord, User, db

auth_bp = Blueprint("auth", __name__, url_prefix="/api/auth")

USERNAME_RE = re.compile(r"^[A-Za-z0-9_-]{3,20}$")


@auth_bp.post("/register")
def register():
    data = request.get_json(force=True, silent=True) or {}
    username = (data.get("username") or "").strip()
    password = data.get("password") or ""
    email = (data.get("email") or "").strip() or None

    if not USERNAME_RE.match(username):
        return jsonify({"error": "Username must be 3-20 chars (letters/digits/_-)"}), 400
    if len(password) < 6:
        return jsonify({"error": "Password must be at least 6 chars"}), 400
    if User.query.filter_by(username=username).first():
        return jsonify({"error": "Username already taken"}), 400

    user = User(username=username, email=email)
    user.set_password(password)
    db.session.add(user)
    db.session.commit()
    login_user(user)
    return jsonify(user.to_dict()), 201


@auth_bp.post("/login")
def login():
    data = request.get_json(force=True, silent=True) or {}
    username = (data.get("username") or "").strip()
    password = data.get("password") or ""
    user = User.query.filter_by(username=username).first()
    if user is None or not user.check_password(password):
        return jsonify({"error": "Invalid credentials"}), 401
    login_user(user)
    return jsonify(user.to_dict())


@auth_bp.post("/logout")
@login_required
def logout():
    logout_user()
    return jsonify({"ok": True})


@auth_bp.get("/me")
def me():
    if not current_user.is_authenticated:
        return jsonify({"authenticated": False})
    return jsonify({"authenticated": True, "user": current_user.to_dict()})


@auth_bp.get("/history")
@login_required
def history():
    rows = (
        GamePlayer.query.filter_by(user_id=current_user.id)
        .join(GameRecord)
        .order_by(GameRecord.created_at.desc())
        .limit(50)
        .all()
    )
    out = []
    for row in rows:
        out.append(
            {
                "room_code": row.game.room_code,
                "status": row.game.status,
                "final_vp": row.final_vp,
                "winner": row.game.winner_name,
                "is_win": row.game.winner_id == current_user.id,
                "created_at": row.game.created_at.isoformat() if row.game.created_at else None,
                "ended_at": row.game.ended_at.isoformat() if row.game.ended_at else None,
            }
        )
    return jsonify(out)
