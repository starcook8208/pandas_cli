# 來源追蹤

| 欄位 | 定義 |
| --- | --- |
| source_file | 原始檔案的絕對路徑 |
| source_sheet | Excel sheet 名稱；CSV 為 null |
| source_row | 從 1 起算，含表頭的 Excel 列／CSV 邏輯記錄序號 |

表頭預設第一列，因此第一筆資料 source_row=2。CSV 引號內換行仍是一筆邏輯記錄，不代表文字檔實體行號。
自訂 `--header 2` 時第一筆資料 source_row=4。工具不跳過壞列。
這三個欄位為保留名稱；已有完整來源欄會保留並基本驗證，只有部分欄位時拒絕，請先重新命名業務欄。
外部提供的來源欄屬來源聲明，工具不會聲稱已獨立驗證其真實性。

concat 保留原始來源。Merge 使用 `_left`、`_right` 後綴保留兩側，不能只保留其中一邊。
彙總後不可把任一原始列冒充整群來源：以 Cleaned 的分組欄位連回 Summary，必要時另外輸出群組到來源的映射。
Exceptions 同時有 source/row 與這三欄，field、original_value 指向出錯欄位；不得以轉型後 null 取代原始錯誤值。
