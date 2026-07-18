"""Slot helpers for date-bot Phase B."""

from __future__ import annotations

import re
from typing import Any

DEFAULT_BUDGET = 3000
SLOT_KEYS = ["budget", "time_slot", "area", "mood", "avoid_areas"]

SLOT_OPTIONS = {
    "budget": ["3000", "5000", "8000", "10000", "15000", "20000"],
    "time_slot": ["昼/午後", "夜/夕方", "朝から夜（終日）"],
    "area": ["渋谷", "上野", "新宿", "お台場", "品川", "池袋"],
    "mood": [
        "コスパ",
        "カフェ",
        "映画",
        "ご飯",
        "動物園",
        "水族館",
        "イベント",
        "散歩",
        "スイーツ",
        "猫カフェ",
        "美術館",
        "博物館",
    ],
    "avoid_areas": ["渋谷", "上野", "新宿", "お台場", "品川", "池袋"],
}


def normalize_slots(raw_slots: Any) -> dict:
    """Gemini / client JSON の slots を内部形式へ正規化。"""
    out: dict = {}
    if not isinstance(raw_slots, dict):
        return out

    budget = raw_slots.get("budget")
    if budget is not None and budget != "":
        m = re.search(r"\d+", str(budget).replace(",", ""))
        if m:
            out["budget"] = int(m.group())

    for k in ["time_slot", "area", "mood"]:
        v = raw_slots.get(k)
        if v is None or v == "":
            continue
        s = str(v).strip()
        if s in ("空", "なし", "None", "null", "-", "未定"):
            continue
        out[k] = s

    avoid = raw_slots.get("avoid_areas")
    avoided: list[str] = []
    if isinstance(avoid, list):
        avoided = [
            str(a).strip()
            for a in avoid
            if str(a).strip() and str(a).strip() not in ("空", "なし")
        ]
    elif isinstance(avoid, str) and avoid.strip() and avoid.strip() not in ("空", "なし"):
        avoided = [p for p in re.split(r"[、,/]+", avoid) if p.strip()]
    if avoided:
        out["avoid_areas"] = list(dict.fromkeys(avoided))
        if out.get("area") in out["avoid_areas"]:
            out.pop("area", None)
    return out


def merge_slots(slots: dict, patch: dict) -> dict:
    """今回渡された値で上書き。avoid_areas はリスト置換（クライアント最終形）。"""
    slots = dict(slots)
    norm = normalize_slots(patch)

    for k in ["budget", "time_slot", "area", "mood"]:
        if k in patch and (patch.get(k) is None or patch.get(k) == ""):
            slots.pop(k, None)
        elif k in norm:
            slots[k] = norm[k]

    if "avoid_areas" in patch:
        raw = patch.get("avoid_areas")
        if raw is None or raw == "" or raw == []:
            slots.pop("avoid_areas", None)
        elif "avoid_areas" in norm:
            slots["avoid_areas"] = norm["avoid_areas"]
        else:
            slots.pop("avoid_areas", None)

    avoided = slots.get("avoid_areas") or []
    if slots.get("area") in avoided:
        slots.pop("area", None)
    return slots


def missing_slots(slots: dict) -> list[str]:
    need = []
    if "time_slot" not in slots:
        need.append("時間帯（昼/午後/夜/終日など）")
    if "area" not in slots:
        need.append("エリア（渋谷・上野・新宿／お台場〜品川など）")
    return need


def template_clarify(need: list[str], slots: dict) -> str:
    msg = "おけ。もうちょい条件ほしい。"
    if need:
        msg += " " + " / ".join(need) + " を教えて。"
    avoid = slots.get("avoid_areas")
    if avoid:
        msg += f" （除外中: {'、'.join(avoid)}）"
    msg += " 例:『上野で午後、一人5000円』"
    return msg


def format_slots_summary(slots: dict) -> str:
    avoid = slots.get("avoid_areas") or []
    if isinstance(avoid, list):
        avoid_s = "、".join(avoid) if avoid else "なし"
    else:
        avoid_s = str(avoid) if avoid else "なし"
    return (
        f"予算 {slots.get('budget', '未設定')} / "
        f"{slots.get('time_slot', '時間未定')} / "
        f"{slots.get('area', 'エリア未定')} / "
        f"mood {slots.get('mood', 'なし')} / "
        f"除外 {avoid_s}"
    )


def parse_plans_text(text: str) -> list[dict]:
    """『案N: ... / 理由: ...』形式（全角コロン・見出し付きも）を list へ。"""
    if not text or not str(text).strip():
        return []
    t = str(text).strip()
    # 見出し行で分割: ### 案1： / 案1: / **案1**
    chunks = re.split(r"(?=(?:#{1,3}\s*)?案\d+\s*[：:])", t)
    plans: list[dict] = []
    for chunk in chunks:
        chunk = chunk.strip()
        if not chunk or not re.search(r"案\d+", chunk):
            continue
        m_head = re.search(
            r"(?:#{1,3}\s*)?案\d+\s*[：:]\s*(.+?)(?=\n\s*(?:\*\*)?理由|\n\s*[-*]\s*\*\*理由|$)",
            chunk,
            re.S,
        )
        m_reason = re.search(
            r"(?:\*\*)?理由(?:\*\*)?\s*[：:]\s*(.+?)(?=\n\s*(?:#{1,3}\s*)?案\d+|\n---|\Z)",
            chunk,
            re.S,
        )
        if m_head:
            plan = m_head.group(1).strip()
        else:
            # タイトルだけの行のあとに本文が続くケース
            m_title = re.search(r"(?:#{1,3}\s*)?案\d+\s*[：:]\s*(.+)", chunk)
            plan = m_title.group(1).strip() if m_title else ""
            # タイトル行以降を要約的に使う
            body = re.sub(r"(?:#{1,3}\s*)?案\d+\s*[：:].*", "", chunk, count=1).strip()
            if body and (not plan or len(plan) < 8):
                plan = body
        reason = m_reason.group(1).strip() if m_reason else ""
        # markdown装飾を軽く除去
        plan = re.sub(r"\*+", "", plan).strip()
        reason = re.sub(r"\*+", "", reason).strip()
        if plan:
            # 長すぎる本文は先頭をカード用に短縮
            if len(plan) > 280:
                plan = plan[:277].rstrip() + "…"
            if len(reason) > 160:
                reason = reason[:157].rstrip() + "…"
            plans.append({"plan": plan, "reason": reason})
        if len(plans) >= 3:
            break
    return plans[:3]
