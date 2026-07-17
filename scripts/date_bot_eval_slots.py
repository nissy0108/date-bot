#!/usr/bin/env python3
"""デートBot スロット抽出の性能評価。

使い方:
1) Colabで LoRA 予測を走らせて pred CSV を作る（ノートの評価セル）
2) または本スクリプトで gold と pred を比較する

  python date_bot_eval_slots.py \
    --gold date_bot_eval_gold.csv \
    --pred date_bot_eval_pred.csv

pred CSV 列:
  input, pred_budget, pred_time_slot, pred_area, pred_mood, pred_avoid_areas
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

import pandas as pd


FIELDS = ["budget", "time_slot", "area", "mood", "avoid_areas"]


def norm_text(x) -> str:
    if x is None or (isinstance(x, float) and pd.isna(x)):
        return ""
    s = str(x).strip()
    if s.lower() in {"nan", "none", "null", "空", "なし", "-"}:
        return ""
    # 終日表記ゆれ
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


def norm_avoid(x) -> str:
    s = norm_text(x)
    if not s:
        return ""
    parts = re.split(r"[、,/|]+", s)
    parts = sorted({p.strip() for p in parts if p.strip()})
    return "、".join(parts)


def norm_mood(x) -> str:
    s = norm_text(x)
    if not s:
        return ""
    parts = re.split(r"[、,/|]+", s)
    parts = sorted({p.strip() for p in parts if p.strip()})
    return "、".join(parts)


def normalize_row(prefix: str, row: dict) -> dict:
    return {
        "budget": norm_budget(row.get(f"{prefix}budget")),
        "time_slot": norm_text(row.get(f"{prefix}time_slot")),
        "area": norm_text(row.get(f"{prefix}area")),
        "mood": norm_mood(row.get(f"{prefix}mood")),
        "avoid_areas": norm_avoid(row.get(f"{prefix}avoid_areas")),
    }


def field_match(field: str, gold: str, pred: str) -> bool:
    return gold == pred


def evaluate(gold_df: pd.DataFrame, pred_df: pd.DataFrame) -> dict:
    merged = gold_df.merge(pred_df, on="input", how="inner", suffixes=("_g", "_p"))
    if merged.empty:
        raise ValueError("gold と pred で共通の input がありません")

    per_field = {f: {"correct": 0, "total": 0} for f in FIELDS}
    exact = 0
    rows = []

    for _, r in merged.iterrows():
        gold = normalize_row("gold_", {
            "gold_budget": r.get("gold_budget", r.get("budget_g")),
            "gold_time_slot": r.get("gold_time_slot", r.get("time_slot_g")),
            "gold_area": r.get("gold_area", r.get("area_g")),
            "gold_mood": r.get("gold_mood", r.get("mood_g")),
            "gold_avoid_areas": r.get("gold_avoid_areas", r.get("avoid_areas_g")),
        })
        # merge may rename columns; handle both styles
        if "gold_budget" in merged.columns:
            gold = normalize_row("gold_", r.to_dict())
        if "pred_budget" in merged.columns:
            pred = normalize_row("pred_", r.to_dict())
        else:
            pred = normalize_row("pred_", r.to_dict())

        # Robust read
        gold = {
            "budget": norm_budget(r["gold_budget"] if "gold_budget" in r else ""),
            "time_slot": norm_text(r["gold_time_slot"] if "gold_time_slot" in r else ""),
            "area": norm_text(r["gold_area"] if "gold_area" in r else ""),
            "mood": norm_mood(r["gold_mood"] if "gold_mood" in r else ""),
            "avoid_areas": norm_avoid(r["gold_avoid_areas"] if "gold_avoid_areas" in r else ""),
        }
        pred = {
            "budget": norm_budget(r["pred_budget"] if "pred_budget" in r else ""),
            "time_slot": norm_text(r["pred_time_slot"] if "pred_time_slot" in r else ""),
            "area": norm_text(r["pred_area"] if "pred_area" in r else ""),
            "mood": norm_mood(r["pred_mood"] if "pred_mood" in r else ""),
            "avoid_areas": norm_avoid(r["pred_avoid_areas"] if "pred_avoid_areas" in r else ""),
        }

        ok_all = True
        detail = {"input": r["input"]}
        for f in FIELDS:
            per_field[f]["total"] += 1
            hit = field_match(f, gold[f], pred[f])
            if hit:
                per_field[f]["correct"] += 1
            else:
                ok_all = False
            detail[f"gold_{f}"] = gold[f]
            detail[f"pred_{f}"] = pred[f]
            detail[f"ok_{f}"] = hit
        if ok_all:
            exact += 1
        detail["exact_match"] = ok_all
        rows.append(detail)

    n = len(merged)
    report = {
        "n": n,
        "exact_match_acc": exact / n if n else 0.0,
        "field_acc": {
            f: per_field[f]["correct"] / per_field[f]["total"]
            for f in FIELDS
        },
    }
    return report, pd.DataFrame(rows)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--gold", default="date_bot_eval_gold.csv")
    ap.add_argument("--pred", default="date_bot_eval_pred.csv")
    ap.add_argument("--out", default="date_bot_eval_report.csv")
    args = ap.parse_args()

    gold_df = pd.read_csv(args.gold)
    pred_df = pd.read_csv(args.pred)
    report, detail = evaluate(gold_df, pred_df)

    print("=== Slot Extraction Eval ===")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    detail.to_csv(args.out, index=False)
    print(f"detail -> {args.out}")

    # show misses
    misses = detail[~detail["exact_match"]]
    print(f"\nmisses: {len(misses)}/{report['n']}")
    if len(misses):
        print(misses[["input", "exact_match"] + [c for c in detail.columns if c.startswith("ok_")]].head(20).to_string(index=False))


if __name__ == "__main__":
    main()
