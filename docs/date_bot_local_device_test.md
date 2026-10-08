# 実機（iPhone / Android）でローカル確認

| 項目 | 内容 |
|------|------|
| 更新日 | 2026-10-08 |
| 前提 | [date_bot_ui_phase_b.md](./date_bot_ui_phase_b.md) |

---

## 1. サーバー起動（LAN）

```bash
cd date-bot
source .venv/bin/activate
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Mac とスマホを **同じ Wi‑Fi** にする。モバイルデータ OFF 推奨。

---

## 2. URL

```bash
ipconfig getifaddr en0
```

ブラウザで `http://<上記IP>:8000/`。**Google アプリの検索欄ではなく Safari のアドレス欄**、または QR。

---

## 3. QR コード（おすすめ）

```bash
.venv/bin/pip install 'qrcode[pil]'
.venv/bin/python -c "
import qrcode, subprocess
ip = subprocess.check_output(['ipconfig','getifaddr','en0'], text=True).strip()
qrcode.make(f'http://{ip}:8000/').save('local-dev-phone-qr.png')
print('http://' + ip + ':8000/')
"
open local-dev-phone-qr.png
```

iPhone **カメラ**で読み取り → **Safari で開く**。

`local-dev-phone-qr.png` は Git 除外（IP 依存のため）。

---

## 4. チェック項目（Phase D/E）

- タブ「おしゃべり｜条件を選ぶ」
- 上部条件サマリー
- 候補履歴 **0 件で非表示**
- 条件タブから聞き返し → おしゃべり切替＋トースト
- チャット入力・送るボタンが画面内に収まる

---

## 5. Render 本番

[date_bot_render_deploy.md](./date_bot_render_deploy.md) — push 後に Render が自動デプロイ（設定による）。
