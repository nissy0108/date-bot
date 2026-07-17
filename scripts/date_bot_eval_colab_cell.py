# ===== Colab用: スロット抽出の性能評価 =====
# 前提: 学習済み local_model / tokenizer / parse_slot_text / local_generate が使えること
# 先に date_bot_eval_gold.csv をアップロード

import pandas as pd
from pathlib import Path

gold_path = "date_bot_eval_gold.csv"
if not Path(gold_path).exists():
    from google.colab import files
    print("date_bot_eval_gold.csv をアップロード")
    uploaded = files.upload()
    gold_path = next(iter(uploaded.keys()))

gold_df = pd.read_csv(gold_path)
print("gold samples:", len(gold_df))

pred_rows = []
for i, row in gold_df.iterrows():
    text = str(row["input"])
    raw = local_generate(text, max_new_tokens=96)
    parsed = parse_slot_text(raw)
    if 'postprocess_slots' in globals():
        parsed = postprocess_slots(text, parsed)
    pred_rows.append({
        "input": text,
        "raw": raw,
        "pred_budget": parsed.get("budget"),
        "pred_time_slot": parsed.get("time_slot"),
        "pred_area": parsed.get("area"),
        "pred_mood": parsed.get("mood"),
        "pred_avoid_areas": "、".join(parsed.get("avoid_areas") or []),
    })
    print(f"[{i+1}/{len(gold_df)}]", text[:30], "->", parsed)

pred_df = pd.DataFrame(pred_rows)
pred_df.to_csv("date_bot_eval_pred.csv", index=False)
print("saved date_bot_eval_pred.csv")

# --- 採点 ---
import re, json

FIELDS = ["budget", "time_slot", "area", "mood", "avoid_areas"]

def norm_text(x) -> str:
    if x is None or (isinstance(x, float) and pd.isna(x)):
        return ""
    s = str(x).strip()
    if s.lower() in {"nan", "none", "null", "空", "なし", "-"}:
        return ""
    s = s.replace("朝から夜", "朝から夜（終日）")
    if s == "朝から夜（終日）（終日）":
        s = "朝から夜（終日）"
    return s

def norm_budget(x):
    s = norm_text(x)
    if not s:
        return ""
    m = re.search(r"\d+", s.replace(",", ""))
    return m.group() if m else s

def norm_list(x) -> str:
    s = norm_text(x)
    if not s:
        return ""
    parts = re.split(r"[、,/|]+", s)
    parts = sorted({p.strip() for p in parts if p.strip()})
    return "、".join(parts)

merged = gold_df.merge(pred_df, on="input", how="inner")
per_field = {f: 0 for f in FIELDS}
exact = 0
details = []

for _, r in merged.iterrows():
    gold = {
        "budget": norm_budget(r.get("gold_budget")),
        "time_slot": norm_text(r.get("gold_time_slot")),
        "area": norm_text(r.get("gold_area")),
        "mood": norm_list(r.get("gold_mood")),
        "avoid_areas": norm_list(r.get("gold_avoid_areas")),
    }
    pred = {
        "budget": norm_budget(r.get("pred_budget")),
        "time_slot": norm_text(r.get("pred_time_slot")),
        "area": norm_text(r.get("pred_area")),
        "mood": norm_list(r.get("pred_mood")),
        "avoid_areas": norm_list(r.get("pred_avoid_areas")),
    }
    ok_all = True
    d = {"input": r["input"], "raw": r.get("raw")}
    for f in FIELDS:
        hit = gold[f] == pred[f]
        per_field[f] += int(hit)
        ok_all &= hit
        d[f"gold_{f}"] = gold[f]
        d[f"pred_{f}"] = pred[f]
        d[f"ok_{f}"] = hit
    exact += int(ok_all)
    d["exact_match"] = ok_all
    details.append(d)

n = len(merged)
report = {
    "n": n,
    "exact_match_acc": exact / n if n else 0.0,
    "field_acc": {f: per_field[f] / n for f in FIELDS},
}
print("=== REPORT ===")
print(json.dumps(report, ensure_ascii=False, indent=2))

detail_df = pd.DataFrame(details)
detail_df.to_csv("date_bot_eval_report.csv", index=False)
print("saved date_bot_eval_report.csv")
print("misses:")
print(detail_df.loc[~detail_df["exact_match"], ["input", "ok_budget", "ok_time_slot", "ok_area", "ok_mood", "ok_avoid_areas"]].head(30))
