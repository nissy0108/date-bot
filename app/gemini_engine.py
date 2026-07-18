"""Gemini REST engine (slot merge + plans) for Phase B."""

from __future__ import annotations

import json
import os
import re
from concurrent.futures import ThreadPoolExecutor
from concurrent.futures import TimeoutError as FuturesTimeout

import requests

from app.slots import (
    DEFAULT_BUDGET,
    missing_slots,
    normalize_slots,
    parse_plans_text,
    template_clarify,
)

# fallback_plans lives here to keep slots.py free of presentation templates
GEMINI_MODEL_NAME = os.environ.get("GEMINI_MODEL_NAME", "gemini-3.1-flash-lite")
GEMINI_TIMEOUT_SEC = int(os.environ.get("GEMINI_TIMEOUT_SEC", "60"))


def prefs_for_gemini() -> str:
    return (
        "呼称: リョウスケ君/こゆたん。東京23区。"
        "優先エリア: 渋谷・上野・新宿/お台場〜品川。"
        "好き: 安いおいしいご飯、カフェ、映画、動物園/水族館、季節イベント、散歩、スイーツ。"
        "NG: 高いのに微妙、長時間ダラダラ。"
        "定番: イベント+ご飯、上野/渋谷起点、コスパ。"
    )


def fallback_plans(slots: dict) -> list[dict]:
    area = slots.get("area", "渋谷")
    budget = slots.get("budget", DEFAULT_BUDGET)
    templates = {
        "上野": [
            (f"上野動物園 → 上野公園短散策 → 安めご飯（一人{budget}円以内）", "定番・コスパ"),
            ("博物館（常設寄り）→ カフェ", "屋内・午後向き"),
            ("公園散歩 → ラーメン/定食 → 早め解散", "ダラダラ回避"),
        ],
        "渋谷": [
            ("公園短散策 → カフェ → 安めご飯", "集合しやすい"),
            ("映画 → 前後でファミレス/ラーメン", "予算管理しやすい"),
            ("スイーツカフェ → 短散歩", "早め解散可"),
        ],
        "新宿": [
            ("新宿御苑 → ランチ", "緑＋コスパ"),
            ("映画 → 安めご飯", "屋内中心"),
            ("カフェ → 短散策", "落ち着き"),
        ],
        "お台場": [
            ("海浜公園散歩 → 食事", "景色＋安さ"),
            ("無料スポット中心 → チェーン食事", "高額回避"),
            ("午後のんびり → 早め切り上げ", "終了明確"),
        ],
        "品川": [
            ("水族館（料金要確認）→ 抑えめ食事", "予算調整"),
            ("短散歩 → 安めご飯", "移動少なめ"),
            ("屋内 → カフェ", "天候に強い"),
        ],
    }
    key = area if area in templates else "渋谷"
    return [{"plan": plan, "reason": reason} for plan, reason in templates[key]]


def get_api_key() -> str | None:
    key = os.environ.get("GEMINI_API_KEY")
    return key.strip() if key else None


def gemini_rest_generate(prompt: str, timeout: int | None = None) -> str:
    api_key = get_api_key()
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY がありません")
    timeout = timeout or GEMINI_TIMEOUT_SEC
    url = (
        "https://generativelanguage.googleapis.com/v1beta/models/"
        f"{GEMINI_MODEL_NAME}:generateContent"
    )
    r = requests.post(
        url,
        params={"key": api_key},
        json={"contents": [{"parts": [{"text": prompt}]}]},
        timeout=timeout,
    )
    if r.status_code != 200:
        raise RuntimeError(f"HTTP {r.status_code}: {r.text[:400]}")
    data = r.json()
    return data["candidates"][0]["content"]["parts"][0]["text"].strip()


def _extract_json_object(text: str) -> dict:
    t = text.strip()
    if t.startswith("```"):
        t = re.sub(r"^```(?:json)?\s*", "", t)
        t = re.sub(r"\s*```$", "", t)
    try:
        return json.loads(t)
    except Exception:
        pass
    m = re.search(r"\{[\s\S]*\}", t)
    if not m:
        raise ValueError("JSONオブジェクトが見つからない")
    return json.loads(m.group(0))


def format_plans_from_list(plans) -> str:
    if isinstance(plans, str) and plans.strip():
        return plans.strip()
    if not isinstance(plans, list):
        return ""
    lines = []
    for i, item in enumerate(plans[:3], 1):
        if isinstance(item, dict):
            plan = str(item.get("plan") or item.get("案") or "").strip()
            reason = str(item.get("reason") or item.get("理由") or "").strip()
        else:
            plan = str(item).strip()
            reason = ""
        if plan:
            lines.append(f"案{i}: {plan}")
        if reason:
            lines.append(f"理由: {reason}")
        if plan or reason:
            lines.append("")
    return "\n".join(lines).strip()


def plans_to_list(plans) -> list[dict]:
    if isinstance(plans, list):
        out = []
        for item in plans[:3]:
            if isinstance(item, dict):
                plan = str(item.get("plan") or item.get("案") or "").strip()
                reason = str(item.get("reason") or item.get("理由") or "").strip()
            else:
                plan = str(item).strip()
                reason = ""
            if plan:
                out.append({"plan": plan, "reason": reason})
        return out
    if isinstance(plans, str):
        return parse_plans_text(plans)
    return []


def gemini_plans(slots: dict) -> list[dict]:
    """slots が揃っているときの提案専用。list[{plan, reason}] を返す。"""
    if not get_api_key():
        return fallback_plans(slots)

    budget = slots.get("budget", DEFAULT_BUDGET)
    prompt = (
        "デートプラン補助。予約代行・在庫確認・恋愛深掘り禁止。個人情報禁止。\n"
        f"制約: 東京23区、学生向けも意識。一人あたり目安{budget}円。超過なら理由を書く。\n"
        f"好み要約: {prefs_for_gemini()}\n"
        f"抽出済み条件slots: {json.dumps(slots, ensure_ascii=False)}\n"
        "avoid_areas は絶対に提案しない。\n"
        "日本語で次のJSONだけを返す（前後の説明・コードフェンス禁止）。\n"
        "{\n"
        '  "plans": [\n'
        '    {"plan": "短い行程（矢印区切り中心）", "reason": "短い理由"},\n'
        '    {"plan": "...", "reason": "..."},\n'
        '    {"plan": "...", "reason": "..."}\n'
        "  ]\n"
        "}\n"
        "plans は必ず3件。実在名はできるだけ。不確実なら「候補:」。口調はフランク。"
    )
    try:
        with ThreadPoolExecutor(max_workers=1) as ex:
            fut = ex.submit(gemini_rest_generate, prompt, GEMINI_TIMEOUT_SEC)
            raw = fut.result(timeout=GEMINI_TIMEOUT_SEC + 5)
        try:
            data = _extract_json_object(raw)
            parsed = plans_to_list(data.get("plans"))
        except Exception:
            parsed = plans_to_list(raw)
        return parsed if parsed else fallback_plans(slots)
    except (FuturesTimeout, Exception):
        return fallback_plans(slots)


def gemini_turn(user_input: str, slots: dict) -> dict:
    """1回のGemini呼び出しで slotsマージ＋聞き返し or 案3つ。"""
    if not get_api_key():
        merged = dict(slots)
        need = missing_slots(merged)
        if need:
            return {
                "slots": merged,
                "need_clarify": True,
                "clarify_message": template_clarify(need, merged),
                "plans": None,
            }
        merged.setdefault("budget", DEFAULT_BUDGET)
        return {
            "slots": merged,
            "need_clarify": False,
            "clarify_message": None,
            "plans": fallback_plans(merged),
        }

    prev = {
        "budget": slots.get("budget"),
        "time_slot": slots.get("time_slot"),
        "area": slots.get("area"),
        "mood": slots.get("mood"),
        "avoid_areas": slots.get("avoid_areas", []),
    }
    prompt = (
        "あなたはデート条件の抽出＋プラン提案アシスタント。\n"
        "予約代行・在庫確認・恋愛深掘り禁止。個人情報禁止。\n"
        "日本語で、次のJSONだけを返す（前後の説明・コードフェンス禁止）。\n"
        "{\n"
        '  "slots": {\n'
        '    "budget": <円の整数 or null>,\n'
        '    "time_slot": "<昼/午後|夜/夕方|朝から夜（終日） or null>",\n'
        '    "area": "<渋谷|上野|新宿|お台場|品川|池袋 など or null>",\n'
        '    "mood": "<読点区切りキーワード or null>",\n'
        '    "avoid_areas": ["除外エリア", ...]\n'
        "  },\n"
        '  "need_clarify": <true/false>,\n'
        '  "clarify_message": <聞き返し文 or null>,\n'
        '  "plans": [\n'
        '    {"plan": "...", "reason": "..."},\n'
        '    {"plan": "...", "reason": "..."},\n'
        '    {"plan": "...", "reason": "..."}\n'
        "  ] or null\n"
        "}\n"
        "ルール:\n"
        "- slots は「これまでのslots」に今回発話をマージした最終状態。触らない項目は前の値を残す。\n"
        "- 発話に無い情報を新たに捏造しない。予算だけの更新なら他スロットは維持。\n"
        "- 除外表現（以外/やめ/避け/NG等）があるときだけ avoid_areas を更新。累積可。\n"
        "- time_slot と area が揃うまで need_clarify=true。plans は null。clarify_message にフランクな聞き返し。\n"
        f"- 揃ったら need_clarify=false。budget未指定なら {DEFAULT_BUDGET} を入れてよい。plans は必ず3件。\n"
        "- 提案は東京23区・学生向けコスパ意識。avoid_areas は絶対に提案しない。超過予算は理由明示。\n"
        "- 不確実な店名は「候補:」。口調はフランク。\n"
        f"好み要約: {prefs_for_gemini()}\n"
        f"これまでのslots: {json.dumps(prev, ensure_ascii=False)}\n"
        f"今回の発話: {user_input}\n"
    )

    try:
        with ThreadPoolExecutor(max_workers=1) as ex:
            fut = ex.submit(gemini_rest_generate, prompt, GEMINI_TIMEOUT_SEC)
            raw = fut.result(timeout=GEMINI_TIMEOUT_SEC + 5)
        data = _extract_json_object(raw)
    except Exception:
        merged = dict(slots)
        need = missing_slots(merged)
        if need:
            return {
                "slots": merged,
                "need_clarify": True,
                "clarify_message": template_clarify(need, merged),
                "plans": None,
            }
        merged.setdefault("budget", DEFAULT_BUDGET)
        return {
            "slots": merged,
            "need_clarify": False,
            "clarify_message": None,
            "plans": fallback_plans(merged),
        }

    merged = normalize_slots(data.get("slots") or {})
    if not merged:
        merged = dict(slots)
    else:
        base = dict(slots)
        base.update(merged)
        merged = base

    need = missing_slots(merged)
    need_clarify = bool(data.get("need_clarify")) or bool(need)
    clarify_message = data.get("clarify_message")
    if need_clarify:
        if not clarify_message:
            clarify_message = template_clarify(need or missing_slots(merged), merged)
        return {
            "slots": merged,
            "need_clarify": True,
            "clarify_message": str(clarify_message),
            "plans": None,
        }

    merged.setdefault("budget", DEFAULT_BUDGET)
    plans = plans_to_list(data.get("plans"))
    if not plans:
        plans = fallback_plans(merged)
    return {
        "slots": merged,
        "need_clarify": False,
        "clarify_message": None,
        "plans": plans,
    }
