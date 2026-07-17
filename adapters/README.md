# adapters/

学習済み LoRA アダプタを置く場所。

Colabで保存した `date_bot_lora/` をここにコピーする。

```text
adapters/
  date_bot_lora/
    adapter_config.json
    adapter_model.safetensors  (または .bin)
    tokenizer 関連ファイル
```

GitHubに上げるか、Google Driveのみにするかは任意。  
ベースモデル本体（Qwen）はここに置かない。
