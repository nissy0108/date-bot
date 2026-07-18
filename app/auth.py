"""Simple 4-digit password + in-memory session for Phase B."""

from __future__ import annotations

import os
import secrets
import time
from dataclasses import dataclass, field
from typing import Any


COOKIE_NAME = "date_bot_session"
SESSION_TTL_SEC = int(os.environ.get("SESSION_TTL_SEC", str(60 * 60 * 12)))


@dataclass
class SessionState:
    slots: dict = field(default_factory=dict)
    messages: list[dict] = field(default_factory=list)
    last_plans: list[dict] | None = None
    plan_history: list[dict] = field(default_factory=list)
    created_at: float = field(default_factory=time.time)
    last_seen: float = field(default_factory=time.time)


_sessions: dict[str, SessionState] = {}


def expected_password() -> str:
    pw = os.environ.get("APP_PASSWORD", "0000").strip()
    if not pw.isdigit() or len(pw) != 4:
        # keep running but force a known shape for local defaults
        return "0000"
    return pw


def create_session() -> str:
    sid = secrets.token_urlsafe(24)
    _sessions[sid] = SessionState()
    return sid


def get_session(sid: str | None) -> SessionState | None:
    if not sid:
        return None
    state = _sessions.get(sid)
    if not state:
        return None
    now = time.time()
    if now - state.last_seen > SESSION_TTL_SEC:
        _sessions.pop(sid, None)
        return None
    state.last_seen = now
    return state


def destroy_session(sid: str | None) -> None:
    if sid:
        _sessions.pop(sid, None)


def reset_session(state: SessionState) -> None:
    state.slots = {}
    state.messages = []
    state.last_plans = None
    state.plan_history = []


def public_state(state: SessionState) -> dict[str, Any]:
    return {
        "slots": state.slots,
        "messages": state.messages,
        "last_plans": state.last_plans,
        "plan_history": state.plan_history,
        "slot_options": None,  # filled by main
    }
