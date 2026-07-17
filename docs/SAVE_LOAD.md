# LoRA の保存・読み込み（再学習しない）

更新日: 2026-07-18  
ベースモデルは毎回 Hugging Face から取得してよい。  
**保存するのは LoRA アダプタのみ。**

現行ノートでは Drive 保存セルあり:

```python
from google.colab import drive
drive.mount("/content/drive")
SAVE_DIR = "/content/drive/MyDrive/date_bot_lora"
model.save_pretrained(SAVE_DIR)
tokenizer.save_pretrained(SAVE_DIR)
```

---

## A. 保存（学習直後・済）

Google Drive: `/content/drive/MyDrive/date_bot_lora`

任意で zip ダウンロード → リポジトリの `adapters/date_bot_lora/` へ。

```python
import shutil
from google.colab import files
shutil.make_archive("/content/date_bot_lora", "zip", SAVE_DIR)
files.download("/content/date_bot_lora.zip")
```

---

## B. 次回起動（学習スキップ）

実行順の例:

1. ライブラリインストール  
2. 設定（MODEL_ID, DEFAULT_BUDGET 等）  
3. **読込セル（下記）** ← セクション2+5の代わり  
4. Gemini セットアップ（セクション6）  
5. 対話エンジン（セクション7）  
6. 対話（セクション8）  

```python
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
from peft import PeftModel
from google.colab import drive

drive.mount("/content/drive")

MODEL_ID = "Qwen/Qwen2.5-1.5B-Instruct"
ADAPTER_DIR = "/content/drive/MyDrive/date_bot_lora"

USE_GPU = torch.cuda.is_available()
tokenizer = AutoTokenizer.from_pretrained(ADAPTER_DIR, use_fast=True, trust_remote_code=True)
if tokenizer.pad_token is None:
    tokenizer.pad_token = tokenizer.eos_token

base = AutoModelForCausalLM.from_pretrained(
    MODEL_ID,
    dtype=torch.bfloat16 if USE_GPU else torch.float32,
    device_map="auto" if USE_GPU else None,
    trust_remote_code=True,
)
model = PeftModel.from_pretrained(base, ADAPTER_DIR)
model.eval()
peft_model = model
print("loaded", ADAPTER_DIR)
```

スクリプト版: `scripts/colab_load_lora.py` / `scripts/colab_save_lora.py`

---

## C. GitHub

| 載せる | 載せない |
|--------|----------|
| コード・docs・sample CSV | APIキー |
| 小さめ LoRA（任意） | LINE生ログ・本番CSV |

Driveのみ運用でも可。

---

## D. 確認

```python
print(type(model), isinstance(model, str))  # str なら NG
raw = local_generate("こゆたんと土曜の午後、上野で安く遊びたい", max_new_tokens=96)
print(raw)
```
