# 結果契約與輸出

`validate_result.py --contract result.json` 與 `export_report.py --contract result.json` 使用相同結果契約。
至少指定一項真正的檢查；下列為完整範例：

```json
{
  "row_count": 2,
  "required_columns": ["employee_id", "amount"],
  "duplicate_keys": ["employee_id"],
  "duplicate_count": 0,
  "null_counts": {"employee_id": 0, "amount": 0},
  "unique_ids": {"employee_id": ["001234", "001235"]},
  "totals": {"amount": {"value": "30.00", "atol": "0", "rtol": "0"}},
  "exception_count": 0
}
```

筆數與 null 數是精確等值檢查。duplicate_count 計算所有重複群組成員，非僅多出的筆數；不含 provenance。
unique_ids 同時要求非空、唯一、集合與指定字串 ID 完全一致。
exception_count 是欄位問題數，非無效來源列數；使用 `--exceptions-file` 才能核對外部資料，省略表示目前沒有提供異常資料（0）。
總額容差公式：`abs(actual - expected) <= atol + rtol * abs(expected)`，預設均為零。
total 遇缺值、不合法數字或無限值失敗，不默認零。

XLSX 預設 Raw/Cleaned/Exceptions；指定 group-by/sum-columns 增加 Summary。
結果契約檢查 Cleaned；Summary 額外檢查金額守恆，保留空 group key，sum 使用 min_count=1。
CSV 僅輸出單一 Cleaned。含 Exceptions 或 Summary 時必須選 XLSX。
寫入使用同目錄暫存檔，完成後才發佈；預設不覆寫已存在輸出，永不覆寫列為來源的檔案。
