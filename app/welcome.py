"""Phase D welcome messages (chat-first, JST)."""

from __future__ import annotations

from datetime import datetime
from zoneinfo import ZoneInfo

JST = ZoneInfo("Asia/Tokyo")

WELCOME_BODY = (
    "次のデートプランを一緒に考えよ！「条件を選ぶ」タブか、この「おしゃべり」で希望を書いてね。\n"
    "ふたりのデート、全力でサポートするからね。"
)


def jst_greeting_line() -> str:
    hour = datetime.now(JST).hour
    if 5 <= hour <= 10:
        return "今日が素敵な一日になるように！"
    if 11 <= hour <= 16:
        return "昼ごはん食べた？"
    if 17 <= hour <= 23:
        return "今日もお疲れ様！"
    return "遅くまでお疲れ様！"


def append_welcome_messages(messages: list[dict]) -> None:
    if messages:
        return
    messages.append({"role": "bot", "content": jst_greeting_line()})
    messages.append({"role": "bot", "content": WELCOME_BODY})
