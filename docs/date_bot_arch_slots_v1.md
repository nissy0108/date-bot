# デートBot構成（スロット抽出版）v1.1

更新日: 2026-07-18  
準拠ノート: 最新 Phase A（LoRA=抽出 / Gemini=提案）

## 役割分担

| 部品 | 役割 | 出力 |
|------|------|------|
| 自前 LoRA | 発話から条件抽出 | `budget` `time_slot` `area` `mood` `avoid_areas` の行形式のみ |
| parse_slot_text | LoRA文字列→dict | リテラル `\n` も改行として解釈 |
| postprocess_slots | 幻覚抑制・ルール補完 | 除外/時間/エリアの根拠なき値を削除。`１万` `やっぱ5000` 等を budget 化 |
| slots | 複数ターンの条件保持 | dict（`reset` でクリア） |
| Gemini REST | 具体プラン | 案3つ＋理由 |
| フォールバック | Gemini失敗時 | エリア別テンプレ3案 |

**方針文は生成しない・Geminiにも渡さない。**

## データフロー

```text
user_input
  → local_generate (chat template, use_cache=False)
  → parse_slot_text
  → postprocess_slots(user_input, ...)
  → merge_slots(slots, ...)
  → missing? → template_clarify
  → gemini_rest_generate(slots + 好み要約)
  → 表示
```

## Gemini

- モデル: `gemini-3.1-flash-lite`
- 方式: `requests.post` で REST（`google.generativeai` SDK は使わない）
- キー: Colab Secrets `GEMINI_API_KEY`（手入力しない）
- タイムアウト: 約45秒 → 失敗時フォールバック

## 学習

| 項目 | 値 |
|------|-----|
| データ | `date_bot_train_slots.csv` |
| 形式 | `Input: ... --- Output:` + スロット行 + ` ### END` |
| 損失 | 回答部分のみ（プロンプトは labels=-100） |
| EPOCHS | 15目安（ロスが十分下がれば途中停止可） |
| LR / BATCH | 2e-4 / 2 |

## 評価

- gold: `data/date_bot_eval_gold.csv`
- Colabセル: `scripts/date_bot_eval_colab_cell.py`
- 指標: field_acc（各スロット）と exact_match_acc（全一致）

参考実績（後処理前の一例）: exact ≈ 13%、budget ≈ 80%、avoid_areas ≈ 53%  
→ 後処理＋データ増強で改善する方針。

## 永続化

- 保存: `model.save_pretrained` → Google Drive `date_bot_lora`
- 再開: ベースQwen + `PeftModel.from_pretrained`
- 詳細: [SAVE_LOAD.md](./SAVE_LOAD.md)
