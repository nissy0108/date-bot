# date-bot

自分とこゆたん向けのデートプランBot（学習用・公開用）。

## 構成

```text
発話
  → LoRA（スロット抽出: budget / time_slot / area / mood / avoid_areas）
  → 後処理（幻覚抑制）
  → slots マージ
  → Gemini REST（案3つ＋理由）  ※slots + 好み要約のみ
```

- ベースモデル: `Qwen/Qwen2.5-1.5B-Instruct`（毎回 Hugging Face から取得）
- 保存するもの: **LoRAアダプタのみ**（軽い。再学習不要）
- Gemini: `gemini-3.1-flash-lite`（APIキーは Colab Secrets。リポジトリに載せない）

## フォルダ

| パス | 内容 |
|------|------|
| `notebooks/date_bot_phase_a.ipynb` | Colab本体 |
| `data/*_sample.csv` | 公開用サンプル |
| `data/*.local.csv` | 本番学習データ（gitignore） |
| `adapters/` | 学習済みLoRA（Driveからコピー。大きい場合はgit LFSまたはDriveのみ） |
| `docs/` | 要件・設計 |
| `scripts/` | 評価・後処理 |

## 初回（学習して保存）

Colab GPU でノートを開き、学習後に次を実行（詳細は `docs/SAVE_LOAD.md`）。

1. LoRAを Google Drive に `save_pretrained`
2. zip をローカルにダウンロード → `adapters/date_bot_lora/` へ
3. このリポジトリを GitHub に push

## 2回目以降（再学習しない）

1. Colab GPU
2. ベースモデル読込 + `PeftModel.from_pretrained(adapters/...)`
3. Gemini セットアップ → 対話

学習セル（3〜5）はスキップ可。

## 秘密情報

- `GEMINI_API_KEY` は Colab Secrets のみ
- LINE生ログ・本名などは入れない
- 公開するのは sample CSV とコード。本番 `*.local.csv` は非公開

## ライセンス・注意

趣味・学習用途。予約代行・在庫確認・投資助言・恋愛深掘りは対象外。
