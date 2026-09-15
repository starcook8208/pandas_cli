# Excel 錯誤

- EXCEL_READ_ERROR：確認真的是 XLSX ZIP，而非改副檔名的 CSV、加密 workbook 或損毀下載。要求完整 values-only 匯出副本。
- 公式輸入被拒絕：由可信 Excel 流程計算並另存純值資料；不能把 missing cache 當零。工具不執行公式／巨集。
- SHEET_NOT_FOUND：先使用 workbook_sheets 或 inspect_workbook 的名稱，注意空白與大小寫。
- HEADER_NOT_FOUND：確認實際表頭列，設定 --header；合併儲存格／多層表頭需另外明確展平。
- EXPORT_ERROR：檢查 workbook 是否在 Excel 開啟被鎖住、sheet 名是否合法、資料及文字是否超過 Excel 上限。

輸出新檔不保留原 workbook style/macros。美化或原生 PivotTable 交給已確認可用的 OfficeCLI。
