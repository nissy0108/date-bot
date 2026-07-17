# ===== Colab: 学習済みLoRAを保存 =====
from google.colab import drive
drive.mount("/content/drive")

SAVE_DIR = "/content/drive/MyDrive/date_bot_lora"
model.save_pretrained(SAVE_DIR)
tokenizer.save_pretrained(SAVE_DIR)
print("saved:", SAVE_DIR)

# 任意: zipダウンロード
import shutil
from google.colab import files
shutil.make_archive("/content/date_bot_lora", "zip", SAVE_DIR)
files.download("/content/date_bot_lora.zip")
