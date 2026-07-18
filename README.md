# date-bot

自分とこゆたん向けのデートプランBot。

## いまの動き

**LoRA版（本来）**

```text
発話
  → LoRA（スロット抽出）
  → 後処理
  → slots 蓄積
  → Gemini REST（案3つ＋理由）
```

**Gemini一本モード（GPU制限時の一時経路）** — [notebooks/date_bot_gemini_only.ipynb](notebooks/date_bot_gemini_only.ipynb)

```text
発話 + これまでのslots
  → Gemini REST 1回（slots更新＋案3つ＋理由）
  → slots を Python 側で保持
```

- ベース: `Qwen/Qwen2.5-1.5B-Instruct` + LoRA（LoRA版）  
- Gemini: `gemini-3.1-flash-lite`（REST、Secretsでキー管理）  
- LoRAは Google Drive に保存済み想定 → **再学習なしで再開可**（[docs/SAVE_LOAD.md](docs/SAVE_LOAD.md)）

## ドキュメント

→ [docs/](docs/)（要件・設計・好み・保存手順）

## クイックスタート

### Gemini一本（CPU可・おすすめ暫定）

1. [notebooks/date_bot_gemini_only.ipynb](notebooks/date_bot_gemini_only.ipynb) を Colab で開く  
2. Secrets に `GEMINI_API_KEY`  
3. セクション 0 → 1 → 6 → 7 → 8（2〜5はスキップ）  
4. 各ターンで `1: 対話入力` / `2: 条件選択`（固定リスト＋その他。揃えばそのターンで案3つ）

### LoRA版（2回目以降・GPUあり）

1. GPU  
2. `scripts/colab_load_lora.py` でアダプタ読込  
3. LoRA版ノートの Gemini → engine → 対話  
4. 学習セルはスキップ  

初回学習やトラブルは [docs/SAVE_LOAD.md](docs/SAVE_LOAD.md) とノート本体を参照。

## 公開ポリシー

- 載せる: コード、docs、sample CSV  
- 載せない: APIキー、LINE生ログ、本番学習CSV  

リポジトリ: https://github.com/nissy0108/date-bot
