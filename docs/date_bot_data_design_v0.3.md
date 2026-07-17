# デートBot データ設計書（v0.4）

| 項目 | 内容 |
|------|------|
| 更新日 | 2026-07-18 |
| 対応要件 | `date_bot_requirements_v1.md` v1.3 |
| 準拠 | 現行ノート（スロット抽出＋後処理＋Gemini REST） |

---

## 1. 確定事項

| 項目 | 決定 |
|------|------|
| 予算未指定時 | 一人 **3000円** |
| 自前モデル | Qwen2.5-1.5B-Instruct + LoRA（スロット抽出） |
| Gemini | 3.1-flash-lite / REST。入力は slots＋好み要約 |
| 店舗CSV | **使わない** |
| 学習データ | `date_bot_train_slots.csv`（公開は sample のみ） |

---

## 2. スロット定義

| キー | 意味 | 例 |
|------|------|-----|
| budget | 一人あたり円 | 3000, 10000 |
| time_slot | 時間帯 | 昼/午後, 夜/夕方, 朝から夜（終日） |
| area | 希望エリア | 渋谷, 上野, 新宿, お台場, 品川, 池袋 |
| mood | 雰囲気・アクティビティ | コスパ, カフェ, 映画（読点区切り可） |
| avoid_areas | 除外エリア | 新宿（list） |

提案前に必須: `time_slot` と `area`（budget は無ければ 3000）。

---

## 3. 学習データ（output例）

```text
budget:3000
time_slot:昼/午後
area:上野
mood:コスパ
avoid_areas:
```

空欄は値なし。除外のみの発話では area を空、avoid_areas のみ埋める。  
短い発話・予算だけの更新では、触らないスロットは空のまま。

---

## 4. 後処理ルール（概要）

| ルール | 内容 |
|--------|------|
| avoid | 「以外/やめ/避け/NG」等が文に無いのに avoid が付いたら削除 |
| time | 時間語が無いのに time_slot が付いたら削除 |
| area | エリア語が無いのに area が付いたら削除 |
| budget | `円` `万` `やっぱ5000` 等を正規表現で補完 |
| budget_only | 予算だけの発話なら他スロットを None（マージで既存維持） |
| mood | 文中キーワードから補完 |

実装: ノート内 `postprocess_slots` / `scripts/date_bot_postprocess_slots.py`

---

## 5. 好み要約

`date_bot_preferences_summary.md`  
Gemini には短縮版（`prefs_for_gemini`）を渡す。店舗マスタは渡さない。

---

## 6. ファイル配置（リポジトリ）

| ファイル | 公開 |
|----------|------|
| `data/date_bot_train_slots_sample.csv` | 可 |
| `data/date_bot_train_slots.local.csv` | 不可（gitignore） |
| `data/date_bot_eval_gold.csv` | 可（個人情報なし） |
| `docs/*` | 可 |
| Drive上の `date_bot_lora/` | 任意（Gitに載せるかは任意） |

---

## 7. 対話上の注意（実装知見）

- `for model in [...]` は LoRA の `model` を上書きする → ループ変数は `cand_name`
- `len(text)<=2` で短文スキップすると「渋谷」が落ちる → 地名は例外にする
- slots は累積。前ターンの area が残る。`reset` でクリア
