# ===== A: 後処理（セクション7に追加 / parse_slot_text の後ろ） =====

def postprocess_slots(user_text: str, extracted: dict) -> dict:
    """LoRA抽出の後処理（幻覚抑制・部分更新）。"""
    t = str(user_text)
    t_norm = t.translate(str.maketrans("０１２３４５６７８９", "0123456789"))

    out = dict(extracted)
    out["avoid_areas"] = list(out.get("avoid_areas") or [])

    neg_cues = ["以外", "やめ", "じゃなく", "じゃない", "除外", "なしで", "NG", "避け"]
    if not any(c in t for c in neg_cues):
        out["avoid_areas"] = []

    time_cues = ["朝", "昼", "午後", "夜", "夕方", "ランチ", "ディナー", "終日", "一日", "晩"]
    if out.get("time_slot") and not any(c in t for c in time_cues):
        out["time_slot"] = None

    area_cues = ["渋谷", "上野", "新宿", "お台場", "品川", "池袋", "23区", "都内"]
    if out.get("area") and not any(c in t for c in area_cues):
        out["area"] = None

    m = re.search(r"(\d{3,6})\s*円", t_norm)
    if m:
        out["budget"] = int(m.group(1))
    m = re.search(r"(\d+(?:\.\d+)?)\s*万\s*円?", t_norm)
    if m:
        out["budget"] = int(float(m.group(1)) * 10000)
    if out.get("budget") is None and re.fullmatch(
        r"\s*(?:やっぱ|やはり|やっぱり)?\s*\d{3,6}\s*円?\s*", t_norm
    ):
        m = re.search(r"(\d{3,6})", t_norm)
        if m:
            out["budget"] = int(m.group(1))
    if any(k in t for k in ["安め", "安く", "コスパ", "抑えめ"]) and out.get("budget") is None:
        out["budget"] = 3000

    budget_only = bool(
        re.fullmatch(
            r"\s*(?:予算は?|一人)?\s*(?:やっぱ|やはり|やっぱり)?\s*(?:\d+(?:\.\d+)?\s*万\s*円?|\d{3,6}\s*円?)\s*(?:で|にする|くらい)?\s*",
            t_norm,
        )
    ) or bool(re.fullmatch(r"\s*(?:やっぱ|やはり|やっぱり)\s*\d{3,6}\s*円?\s*", t_norm))
    if budget_only:
        out["time_slot"] = None
        out["area"] = None
        out["mood"] = None
        if not any(c in t for c in neg_cues):
            out["avoid_areas"] = []

    mood_map = {
        "カフェ": "カフェ", "映画": "映画", "動物園": "動物園", "水族館": "水族館",
        "ご飯": "ご飯", "食事": "ご飯", "イベント": "イベント", "散歩": "散歩",
        "美術館": "美術館", "博物館": "博物館", "スイーツ": "スイーツ",
        "猫カフェ": "猫カフェ", "コスパ": "コスパ", "安く": "コスパ", "安め": "コスパ",
    }
    moods = []
    if out.get("mood"):
        moods.extend(re.split(r"[、,/]", str(out["mood"])))
    for k, v in mood_map.items():
        if k in t and v not in moods:
            moods.append(v)
    moods = [m for m in moods if m and m not in ("空", "なし")]
    out["mood"] = "、".join(dict.fromkeys(moods)) if moods else None

    areas = ["渋谷", "上野", "新宿", "お台場", "品川", "池袋"]
    avoided = list(out.get("avoid_areas") or [])
    for a in areas:
        if any(p in t for p in [f"{a}以外", f"{a}はやめ", f"{a}じゃなく", f"{a}じゃない", f"{a}は避け", f"{a}NG", f"{a}はNG"]):
            if a not in avoided:
                avoided.append(a)
    out["avoid_areas"] = avoided
    if out.get("area") in out["avoid_areas"]:
        out["area"] = None
    return out


# ===== セクション8の抽出部分 =====
# extracted = parse_slot_text(raw)
# extracted = postprocess_slots(user_input, extracted)
# slots = merge_slots(slots, extracted)
