# ===== Colab: 保存済みLoRAを読み込み（再学習スキップ） =====
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
from peft import PeftModel
from google.colab import drive

drive.mount("/content/drive")

MODEL_ID = "Qwen/Qwen2.5-1.5B-Instruct"
ADAPTER_DIR = "/content/drive/MyDrive/date_bot_lora"

USE_GPU = torch.cuda.is_available()
print("GPU:", USE_GPU)

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
print("loaded from", ADAPTER_DIR)
model.print_trainable_parameters()
