# 錯誤協定

stdout 錯誤物件：

```json
{"status":"error","error":{"code":"SCHEMA_MISMATCH","file":"sales.xlsx","sheet":"Sales","column":"amount","message":"Required column missing."}}
```

file/sheet/column 無適用值時為 null；可附 columns、row、checks、audit、exception_count、output 等可機讀診斷。
成功為 `status=success`，不可在驗證未通過時回 success。經明確授權輸出有效子集時，成功仍需標示 `validation_status=passed_with_exceptions`。

| code | 含義／處理 |
| --- | --- |
| FILE_NOT_FOUND | 路徑不存在或 pattern 無結果 |
| UNSUPPORTED_FORMAT | 僅支援 CSV/XLSX |
| EXCEL_READ_ERROR | 損壞檔、公式輸入、Excel 讀取失敗 |
| CSV_PARSE_ERROR | 不合法引號、欄數不符或 parser 失敗 |
| ENCODING_ERROR | 依指定編碼無法解碼 |
| SHEET_NOT_FOUND | 名稱不符 |
| HEADER_NOT_FOUND | 無表頭或空欄名 |
| SCHEMA_MISMATCH | 結構／規則不符 |
| DTYPE_ERROR | 不符合布林／計算型別 |
| DATE_PARSE_ERROR | 日期轉型失敗（Exceptions 欄位錯誤碼） |
| NUMERIC_PARSE_ERROR | 非有限數字或轉型失敗 |
| DUPLICATE_KEY | 唯一鍵重複／不合法 |
| MERGE_CARDINALITY_ERROR | 合併基數或筆數異常；hard stop |
| ROW_COUNT_MISMATCH | 結果筆數錯誤 |
| TOTAL_MISMATCH | 總額／守恆錯誤；hard stop |
| OUT_OF_MEMORY | 變更處理方式，禁止原樣反覆重試 |
| EXPORT_ERROR | 覆寫保護、Excel 上限或輸出失敗 |
| VALIDATION_FAILED | 一般驗證或多欄問題，詳見 Exceptions |
| INVALID_ARGUMENT | CLI 或 JSON 參數格式錯誤 |
| IO_ERROR | 非特定讀寫錯誤 |
| DEPENDENCY_ERROR | 缺少依賴 |

exit 0：成功；exit 2：輸入／資料／驗證錯誤；exit 3：I/O、Excel 讀取、記憶體、依賴或匯出失敗。
find_duplicates/find_exceptions 可先產生診斷檔再返回 exit 2；這不代表可繼續產出成功報表。
