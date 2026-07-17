# デートBot構成（スロット抽出版）

## 役割分担

| 部品 | 役割 | 出力 |
|------|------|------|
| 自前 LoRA | 発話から条件抽出 | `budget` `time_slot` `area` `mood` `avoid_areas` のキーワード行のみ（方針文なし） |
| slots | 条件の保持・マージ | dict |
| Gemini | 具体案 | 案3つ＋理由 |
| 渡し方 | Geminiへ | **slots + 好み要約のみ**（方針文は渡さない） |

## LoRA出力フォーマット

```
budget:3000
time_slot:昼/午後
area:上野
mood:コスパ
avoid_areas:新宿
```

空欄はキーだけ残すか値なし。

## 学習データ

`date_bot_train_slots.csv`

## 再学習手順（Colab）

1. `date_bot_train_slots.csv` をアップロード
2. セクション3〜5で再学習
3. セクション6（Gemini）→7→8
