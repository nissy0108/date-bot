# date-bot — Render 無料枠デプロイ手順

| 項目 | 内容 |
|------|------|
| 更新日 | 2026-10-07 |
| 対象 | Phase B Web + エクスポート v1 |
| 料金 | **Free** Web Service（スリープあり） |
| 正本リポジトリ | https://github.com/nissy0108/date-bot |

Hugging Face の Docker Space が PRO 必須になった場合の **無料代替** として Render を使う。

---

## 0. 用語（30 秒）

- **Render** … インターネット上で uvicorn を動かしてくれるサービス  
- **$PORT** … Render が「この番号で待て」と渡す部屋番号（7860 固定ではない）  
- **Environment Variables** … HF の Secrets と同じ（`GEMINI_API_KEY` など）

---

## 1. 事前準備

1. [render.com](https://render.com) でアカウント作成（GitHub 連携可）  
2. GitHub に **最新の `main`** があること（`render.yaml` / `runtime.txt` 含む）  
3. 手元の `.env` と同じ値を用意  
   - `GEMINI_API_KEY`  
   - `APP_PASSWORD`（4 桁数字）

---

## 2. デプロイ（おすすめ: Python 直接）

Docker より設定が少ない。

### 2.1 Web Service 作成

1. Render ダッシュボード → **New +** → **Web Service**  
2. **Connect GitHub** → リポジトリ **`nissy0108/date-bot`** を選ぶ  
3. 次を設定:

| 項目 | 値 |
|------|-----|
| **Name** | `date-bot`（任意） |
| **Region** | 近いリージョン（例: Singapore） |
| **Branch** | `main` |
| **Runtime** | **Python 3** |
| **Build Command** | `pip install -r requirements-web.txt` |
| **Start Command** | `uvicorn app.main:app --host 0.0.0.0 --port $PORT` |
| **Instance Type** | **Free** |

**Python 版:** リポジトリの `runtime.txt`（**3.11**）を使う。Render が **3.14** だと Jinja 周りで落ちることがある → Dashboard の **Environment** に `PYTHON_VERSION` = `3.11.11` を足してもよい。

4. **Advanced** → **Health Check Path**（あれば）: `/api/health`

### 2.2 環境変数

**Environment** タブ（または作成画面の Environment Variables）:

| Key | Value |
|-----|--------|
| `GEMINI_API_KEY` | （API キー） |
| `APP_PASSWORD` | （4 桁） |

任意:

| Key | 既定 |
|-----|------|
| `GEMINI_MODEL_NAME` | `gemini-3.1-flash-lite` |
| `GEMINI_TIMEOUT_SEC` | `60` |

5. **Create Web Service** → ビルドログを待つ（5〜10 分）

### 2.3 公開 URL

デプロイ成功後、画面上部に:

`https://date-bot-xxxx.onrender.com`

のような URL が表示される。

---

## 3. 別ルート: Blueprint（`render.yaml`）

1. **New +** → **Blueprint**  
2. 同じ GitHub リポジトリを選択  
3. 内容を確認 → **Apply**  
4. **`GEMINI_API_KEY` / `APP_PASSWORD`** を Render が聞いてきたら入力  

---

## 4. 別ルート: Docker

1. **New +** → **Web Service** → リポジトリ選択  
2. **Runtime: Docker**  
3. Dockerfile パス: `./Dockerfile`（既定）  
4. 環境変数は §2.2 と同じ  

`Dockerfile` は `PORT` 未設定時 **7860**（HF 用）、Render では **`PORT` を自動注入**。

---

## 5. 動作確認（5 分）

1. 公開 URL を開く（初回は **コールドスタート 30 秒〜1 分** かかることがある）  
2. 4 桁パスワードでログイン  
3. 条件反映 → 案 3 つ  
4. **コピー** → 貼り付け  
5. `https://<your-app>.onrender.com/api/health` → `"gemini_key": true`

---

## 6. 無料枠の制限（重要）

| 項目 | 内容 |
|------|------|
| **スリープ** | 約 15 分アクセスがないと停止 → 次アクセスが遅い |
| **セッション** | メモリのみ（再起動・スリープで履歴消える） |
| **CPU/RAM** | 小さい（二人利用のデモには足りる想定） |

本番で常時起動したい場合は有料プランが必要。

---

## 7. トラブルシュート

| 症状 | 対処 |
|------|------|
| Build failed | Logs で `pip` エラー。`requirements-web.txt` / Python 版を確認 |
| Deploy failed / Port | Start Command に **`$PORT`** があるか |
| 502 / 起動直後 | 1 分待って再読み込み |
| ログインできない | `APP_PASSWORD` が 4 桁か、Deploy 後に変数を入れたか |
| 案がテンプレのみ | `GEMINI_API_KEY` と `/api/health` |

---

## 8. HF Spaces との違い

| | Render Free | HF Docker Space |
|---|-------------|-----------------|
| 料金 | 無料枠あり | Docker は PRO 等が必要なことが多い |
| ポート | **`$PORT`（Render が指定）** | **7860 固定** |
| URL | `*.onrender.com` | `*.hf.space` |

---

## 9. ローカルとの対応

| 環境 | 起動例 | URL |
|------|--------|-----|
| ローカル | `uvicorn ... --port 8000` | http://127.0.0.1:8000 |
| Render | `uvicorn ... --port $PORT` | https://xxx.onrender.com |
| HF | Docker → `${PORT:-7860}` | https://xxx.hf.space |
