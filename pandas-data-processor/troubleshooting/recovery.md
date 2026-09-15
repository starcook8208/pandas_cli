# 錯誤復原路由

| 錯誤 | 允許的下一步 | 停止條件 |
| --- | --- | --- |
| ENCODING_ERROR | 查來源編碼聲明／BOM，明定 encoding 後一次重試 | 仍失敗則回報，不連續猜編碼 |
| DTYPE_ERROR/NUMERIC_PARSE_ERROR/DATE_PARSE_ERROR | 保留原始值，以安全轉型建立 Exceptions | 不自行把錯值改成零或日期 |
| MERGE_CARDINALITY_ERROR | 停止；查雙方 duplicate keys、null keys、預期筆數 | 修正 schema／規則前不產出報表 |
| TOTAL_MISMATCH | 停止；逐群組／ID 比對前後與受影響來源 | 未解釋差異不繼續，不自行放寬容差 |
| OUT_OF_MEMORY | 減 usecols、可結合運算分 chunk，或改引擎 | 禁止同一運算原樣重試 |
| EXPORT_ERROR | 查鎖檔、目的地、大小上限及覆寫保護 | 不刪除來源或既有報表以繞過保護 |

詳細指南：[Excel](excel-errors.md)、[CSV](csv-errors.md)、[dtype](dtype-errors.md)、[merge](merge-errors.md)、[memory](memory-errors.md)、[encoding](encoding-errors.md)。
保留失敗 JSON 與 Exceptions，說明已做的復原、仍需的資料／規則。
