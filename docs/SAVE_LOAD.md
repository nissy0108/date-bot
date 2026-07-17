# LoRA の保存・読み込み（再学習しない）

ベースの Qwen 本体は毎回 DL でよい。  
**保存するのは LoRA アダプタだけ**（数MB〜数十MB程度が多い）。

---

## A. 今の Colab セッションで保存（学習直後）

### 1) Google Drive に保存（おすすめ）

```python
from google.colab import drive
drive.mount("/content/drive")

SAVE_DIR = "/content/drive/MyDrive/date_bot_lora"
model.save_pretrained(SAVE_DIR)
tokenizer.save_pretrained(SAVE_DIR)
print("saved to", SAVE_DIR)
```

### 2) ローカルにダウンロード（GitHub用）

```python
import shutil
from google.colab import files

shutil.make_archive("/content/date_bot_lora", "zip", SAVE_DIR)
files.download("/content/date_bot_lora.zip")
```

解凍してリポジトリの `adapters/date_bot_lora/` に置く。

---

## B. 次回 Colab（学習スキップ）

```python
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
from peft import PeftModel
from google.colab import drive

drive.mount("/content/drive")

MODEL_ID = "Qwen/Qwen2.5-1.5B-Instruct"
ADAPTER_DIR = "/content/drive/MyDrive/date_bot_lora"  # or アップロードした adapters/date_bot_lora

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
print("LoRA loaded. trainable check:")
model.print_trainable_parameters()
```

このあと **Gemini セットアップ → engine → 対話** だけ実行。  
セクション3〜5（学習）は不要。

---

## C. GitHub に載せるもの / 載せないもの

| 載せる | 載せない |
|--------|----------|
| コード・ノート・README | `GEMINI_API_KEY` |
| sample CSV | LINE生ログ |
| 小さめの LoRA（任意） | 本番 `*.local.csv`（gitignore済み） |
| 要件・設計ドキュメント | |

LoRAをGitに入れたくない場合は Drive のみで運用してよい。

---

## D. 動作確認

```python
print(type(model))
raw = local_generate("こゆたんと土曜の午後、上野で安く遊びたい", max_new_tokens=96)
print(raw)
```
