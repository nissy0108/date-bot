# Phase C — Hugging Face Spaces デプロイ

| 項目 | 内容 |
|------|------|
| 更新日 | 2026-10-06 |
| 方式 | **Docker Space（CPU）** |
| 正本 | リポジトリ直下 [`Dockerfile`](../Dockerfile) |
| 待受ポート | **7860**（HF 既定） |
| 秘密情報 | Space **Settings → Secrets**（Git に載せない） |

---

## 1. 前提

- GitHub: [nissy0108/date-bot](https://github.com/nissy0108/date-bot)
- Phase B Web + エクスポート v1 が `main` に push 済みであること
- Hugging Face アカウント（無料枠で CPU Docker Space 可）
- **有料オプション**（専用 CPU/GPU 等）を押す前に HF の料金表示を必ず確認

---

## 2. リポジトリ側の準備（済み／確認）

| ファイル | 役割 |
|----------|------|
| `Dockerfile` | Python 3.11 + `uvicorn` on `0.0.0.0:7860` |
| `requirements-web.txt` | Web 依存のみ（LoRA/torch なし） |
| `app/` | FastAPI + 静的 UI |
| `docs/date_bot_preferences_summary.md` | イメージに同梱（将来拡張用） |
| `.dockerignore` | `.venv` / `.env` / notebooks 等を除外 |
| `README.md` 先頭 YAML | Space カード用 `sdk: docker` / `app_port: 7860` |

ローカルで Docker ビルド確認（任意）:

```bash
cd ~/Downloads/date-bot
docker build -t date-bot-space .
docker run --rm -p 7860:7860 \
  -e GEMINI_API_KEY=your_key \
  -e APP_PASSWORD=1234 \
  date-bot-space
# → http://127.0.0.1:7860
```

---

## 3. Space の作成（UI）

1. [huggingface.co/new-space](https://huggingface.co/new-space) を開く  
2. **Space name** — 例: `date-bot`（URL は `https://huggingface.co/spaces/<ユーザー名>/date-bot`）  
3. **License** — 任意  
4. **Space SDK** → **Docker**  
5. **Create Space**

### GitHub 連携（推奨）

1. Space → **Settings → Repository**  
2. **Link to GitHub repository** → `nissy0108/date-bot`  
3. ブランチ **`main`**、Dockerfile パス **`Dockerfile`**（リポジトリ直下）  
4. 保存後、**自動ビルド**が走る（数分）

**別方法:** Space を空で作り、HF Git に push する（GitHub 連携より手間）。

---

## 4. Secrets（必須）

Space → **Settings → Repository secrets**（または **Variables and secrets**）

| Name | Value |
|------|--------|
| `GEMINI_API_KEY` | Google AI Studio の API キー |
| `APP_PASSWORD` | 4 桁ログインパスワード |

任意:

| Name | 既定 |
|------|------|
| `GEMINI_MODEL_NAME` | `gemini-3.1-flash-lite` |
| `GEMINI_TIMEOUT_SEC` | `60` |
| `SESSION_TTL_SEC` | `43200`（12h） |

Secrets 変更後は **Factory reboot** または再デプロイで反映。

---

## 5. デプロイ後チェック（5 分）

1. Space 上部 **App** タブ → 公開 URL を開く  
2. **4 桁パスワード**でログイン  
3. 条件反映 → 案 3 つ  
4. **コピー**（履歴 or 結果画面）→ クリップボード  
5. `https://<space-url>/api/health` → `{"ok":true,"gemini_key":true,...}`  

---

## 6. 制約・注意（Phase B/C 共通）

| 項目 | 内容 |
|------|------|
| セッション | **プロセスメモリ**（1 レプリカ想定）。Sleep 後は履歴・ログ消える |
| Sleep | 無料 CPU Space はアイドルでスリープ → 初回アクセスが遅い |
| クリップボード | **HTTPS** 必須（HF は OK）。HTTP ローカルとは挙動が異なる場合あり |
| Cookie | HF 上では `SPACE_ID` 検出時 **Secure** Cookie（`app/main.py`） |
| スケール | 複数レプリカは **非対応**（セッション共有なし） |

---

## 7. トラブルシュート

| 症状 | 対処 |
|------|------|
| Build failed | Space **Logs** で `pip` / `COPY` エラーを確認。`main` が最新か GitHub 連携を確認 |
| App が起動しない | ポート **7860** か、`CMD` が `0.0.0.0` か確認 |
| ログイン 401 | Secret `APP_PASSWORD` が 4 桁数字か、再デプロイ |
| 案がテンプレのみ | `GEMINI_API_KEY` Secret、health の `gemini_key` |
| 502 / 起動直後失敗 | コールドスタート待ち → 再読み込み |

---

## 8. ローカルとの違い

| | ローカル | HF Spaces |
|---|----------|-----------|
| ポート | 8000 | 7860 |
| 環境変数 | `.env` | Secrets |
| URL | `127.0.0.1` | `*.hf.space` |
| `--reload` | 可 | 不可（イメージ再ビルド） |

---

## 9. 次（Phase C 以降）

- `main` へ push → 連携 Space が自動再ビルド  
- カスタムドメイン・Persistent ストレージは v1 外  
- 公開 Space URL を README に追記（デプロイ後）
