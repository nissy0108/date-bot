# date-bot

自分とこゆたん向けのデートプランBot。

## いまの動き

```text
発話
  → LoRA（スロット抽出）
  → 後処理
  → slots 蓄積
  → Gemini REST（案3つ＋理由）
```

- ベース: `Qwen/Qwen2.5-1.5B-Instruct` + LoRA  
- Gemini: `gemini-3.1-flash-lite`（REST、Secretsでキー管理）  
- LoRAは Google Drive に保存済み想定 → **再学習なしで再開可**（[docs/SAVE_LOAD.md](docs/SAVE_LOAD.md)）

## ドキュメント

→ [docs/](docs/)（要件・設計・好み・保存手順）

## クイックスタート（Colab・2回目以降）

1. GPU  
2. `scripts/colab_load_lora.py` でアダプタ読込  
3. ノートの Gemini → engine → 対話  
4. 学習セルはスキップ  

初回学習やトラブルは [docs/SAVE_LOAD.md](docs/SAVE_LOAD.md) とノート本体を参照。

## 公開ポリシー

- 載せる: コード、docs、sample CSV  
- 載せない: APIキー、LINE生ログ、本番学習CSV  

リポジトリ: https://github.com/nissy0108/date-bot
