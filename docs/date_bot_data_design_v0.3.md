# デートBot データ設計書（v0.3）

| 項目 | 内容 |
|------|------|
| 作成日 | 2026-07-17 |
| 対応要件 | `date_bot_requirements_v1.md` v1.2 |
| 更新 | **店舗CSV廃止**。エリア＋好み要約＋train.csv のみ |

---

## 1. 確認済み決定

| 項目 | 決定 |
|------|------|
| 予算未指定時 | 一人 **3000円** 目安 |
| 自前モデル | 授業寄り **軽量 + LoRA**（Qwen2.5-0.5B/1.5B 優先） |
| 分業 | 自前＝口調・好み／Gemini＝具体プラン・店名案 |
| 店舗リスト | **持たない**。優先エリア＋好み要約だけで十分 |

---

## 2. 全体アーキテクチャ（分業）

```text
ユーザー（複数ターン）
    → 条件ヒアリング（budget / time_slot / area）
    → 自前LoRA（口調・好み・NG・安価方針）
    → Gemini（案3つ＋理由。入力は条件＋preferences要約のみ）
    → 表示
```

Geminiへの材料:
- スロット（予算・時間帯・エリア）
- `preferences_summary` の要点（渋谷・上野・新宿／お台場〜品川、動物・カフェ・ご飯・コスパ 等）
- 自前モデルが出した口調・方針文

※実在店名は Gemini の一般知識。不確実なら「候補」と書かせる。空席・予約は扱わない。

提案前に揃えるスロット: `budget`（無ければ3000円想定と伝えて確認）, `time_slot`, `area`

---

## 3. よく行くエリア（確認済み）

| # | エリア | メモ |
|---|--------|------|
| 1 | 渋谷 | 集合・ハブ多い |
| 2 | 上野 | 動物園・博物館・公園口集合 |
| 3 | 新宿 / お台場〜品川 | 同程度 |

詳細: `date_bot_preferences_summary.md`

---

## 4. 好み要約

確認済み。学習の元データ＆Geminiへの固定コンテキスト。

---

## 5. 学習用CSVスキーマ

`input,output,category`

10件: preference×3 / ng×2 / plan_style×3 / clarify×2  
ファイル: `date_bot_train.csv`（非公開）／`date_bot_train_sample.csv`（公開可）

---

## 6. 店舗CSV

**廃止。** 作成済みの `date_bot_shops*.csv` は使わない（削除してよい）。

---

## 7. 成果物（Downloads）

| ファイル | 内容 | 公開 |
|----------|------|------|
| `date_bot_preferences_summary.md` | 好み要約（確認済み） | 要約のみなら可 |
| `date_bot_train.csv` | 学習10件 | **非公開** |
| `date_bot_train_sample.csv` | 公開用サンプル | 公開可 |

---

## 8. 次アクション

1. Colab Phase A（軽量LoRA + Gemini分業 + 複数ターン）
2. GitHub公開時は sample のみ
