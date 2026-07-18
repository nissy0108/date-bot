"""FastAPI entry for date-bot Phase B."""

from __future__ import annotations

import copy
import os
import time
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, Field

from app import auth
from app.gemini_engine import gemini_plans, gemini_turn
from app.slots import (
    DEFAULT_BUDGET,
    SLOT_OPTIONS,
    format_slots_summary,
    merge_slots,
    missing_slots,
    template_clarify,
)

ROOT = Path(__file__).resolve().parent
load_dotenv(ROOT.parent / ".env")

app = FastAPI(title="デートBot", version="0.2.0")
app.mount("/static", StaticFiles(directory=str(ROOT / "static")), name="static")
templates = Jinja2Templates(directory=str(ROOT / "templates"))


class LoginBody(BaseModel):
    password: str = Field(..., min_length=4, max_length=4)


class ChatBody(BaseModel):
    message: str = Field(..., min_length=1, max_length=2000)


class SlotsBody(BaseModel):
    slots: dict = Field(default_factory=dict)


def _require_session(request: Request) -> tuple[str, auth.SessionState]:
    sid = request.cookies.get(auth.COOKIE_NAME)
    state = auth.get_session(sid)
    if not state or not sid:
        raise HTTPException(status_code=401, detail="login required")
    return sid, state


def _append_plan_history(state: auth.SessionState, plans: list) -> dict:
    """案3つセットを履歴に追加して返す。"""
    entry = {
        "id": len(state.plan_history) + 1,
        "slots": copy.deepcopy(state.slots),
        "slots_summary": format_slots_summary(state.slots),
        "plans": copy.deepcopy(plans or []),
        "created_at": time.time(),
    }
    state.plan_history.append(entry)
    return entry


def _state_payload(state: auth.SessionState, *, view_hint: str | None = None) -> dict:
    return {
        "slots": state.slots,
        "messages": state.messages,
        "last_plans": state.last_plans,
        "plan_history": state.plan_history,
        "slots_summary": format_slots_summary(state.slots),
        "slot_options": SLOT_OPTIONS,
        "default_budget": DEFAULT_BUDGET,
        "view_hint": view_hint,
    }


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "app_name": "デートBot",
        },
    )


@app.post("/api/login")
async def login(body: LoginBody, response: Response):
    if body.password != auth.expected_password():
        raise HTTPException(status_code=401, detail="パスワードが違うよ")
    sid = auth.create_session()
    response.set_cookie(
        key=auth.COOKIE_NAME,
        value=sid,
        httponly=True,
        samesite="lax",
        max_age=auth.SESSION_TTL_SEC,
    )
    state = auth.get_session(sid)
    assert state is not None
    return _state_payload(state, view_hint="main")


@app.post("/api/logout")
async def logout(request: Request, response: Response):
    sid = request.cookies.get(auth.COOKIE_NAME)
    auth.destroy_session(sid)
    response.delete_cookie(auth.COOKIE_NAME)
    return {"ok": True}


@app.get("/api/state")
async def state(request: Request):
    _, sess = _require_session(request)
    hint = "results" if sess.last_plans else "main"
    return _state_payload(sess, view_hint=hint)


@app.post("/api/chat")
async def chat(body: ChatBody, request: Request):
    _, sess = _require_session(request)
    text = body.message.strip()
    if not text:
        raise HTTPException(status_code=400, detail="empty message")

    if any(k in text for k in ["予約して", "空席", "恋愛相談", "復縁", "住所", "電話番号"]):
        bot = "それは対応外だよ。デート案の相談だけ続けるね。"
        sess.messages.append({"role": "user", "content": text})
        sess.messages.append({"role": "bot", "content": bot})
        return _state_payload(sess, view_hint="main")

    # スロットが残っている状態での一文字入力は Gemini に渡さず定型で聞き直す
    if len(text) <= 1 and sess.slots:
        sess.messages.append({"role": "user", "content": text})
        need = missing_slots(sess.slots)
        if need:
            bot = template_clarify(need, sess.slots)
        else:
            bot = (
                "おけ。一文字だけだと意図がわからないよ。"
                f"いまの条件は「{format_slots_summary(sess.slots)}」。"
                "変えたいところや希望を文章でもう一度教えてね。"
                " 例:『上野で午後、一人5000円』"
            )
        sess.messages.append({"role": "bot", "content": bot})
        return _state_payload(sess, view_hint="main")

    sess.messages.append({"role": "user", "content": text})
    result = gemini_turn(text, sess.slots)
    sess.slots = result["slots"]

    if result["need_clarify"]:
        msg = result["clarify_message"] or template_clarify(missing_slots(sess.slots), sess.slots)
        sess.messages.append({"role": "bot", "content": msg})
        sess.last_plans = None
        return _state_payload(sess, view_hint="main")

    plans = result["plans"] or []
    sess.last_plans = plans
    entry = _append_plan_history(sess, plans)
    sess.messages.append(
        {
            "role": "bot",
            "content": (
                f"条件そろったから案を3つ出したよ（候補セット#{entry['id']}）。"
                "この画面で見てね。戻ったら下の「候補履歴」にも残してあるよ。"
            ),
        }
    )
    return _state_payload(sess, view_hint="results")


@app.post("/api/slots")
async def update_slots(body: SlotsBody, request: Request):
    _, sess = _require_session(request)
    sess.slots = merge_slots(sess.slots, body.slots or {})
    sess.messages.append(
        {
            "role": "bot",
            "content": f"条件を更新したよ。（{format_slots_summary(sess.slots)}）",
        }
    )

    need = missing_slots(sess.slots)
    if need:
        msg = template_clarify(need, sess.slots)
        sess.messages.append({"role": "bot", "content": msg})
        sess.last_plans = None
        return _state_payload(sess, view_hint="main")

    sess.slots.setdefault("budget", DEFAULT_BUDGET)
    plans = gemini_plans(sess.slots)
    sess.last_plans = plans
    entry = _append_plan_history(sess, plans)
    sess.messages.append(
        {
            "role": "bot",
            "content": (
                f"条件そろったから案を3つ出したよ（候補セット#{entry['id']}）。"
                "この画面で見てね。戻ったら下の「候補履歴」にも残してあるよ。"
            ),
        }
    )
    return _state_payload(sess, view_hint="results")


@app.post("/api/reset")
async def reset(request: Request):
    _, sess = _require_session(request)
    auth.reset_session(sess)
    sess.messages.append({"role": "bot", "content": "条件と履歴をリセットしたよ。"})
    return _state_payload(sess, view_hint="main")


@app.get("/api/health")
async def health():
    return {
        "ok": True,
        "gemini_key": bool(os.environ.get("GEMINI_API_KEY")),
        "model": os.environ.get("GEMINI_MODEL_NAME", "gemini-3.1-flash-lite"),
    }
