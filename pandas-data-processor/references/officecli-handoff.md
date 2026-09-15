# OfficeCLI Handoff

## 分工

| pandas：Data Engine | OfficeCLI：Workbook/Presentation Engine |
| --- | --- |
| Clean/Filter/Sort/GroupBy/Merge | Sheet/Cell/Formula |
| 計算 pivot table 資料 | Excel 原生 PivotTable |
| schema、總額、異常檢查 | Font/Color/Border/Column width |
| 來源追蹤、大量表格運算 | Chart/Dashboard/最終樣式 |

## 交接內容

1. 先完成 `export_report.py`，產生 Intermediate.xlsx。
2. 提供絕對路徑、sheet 名、表頭與資料範圍、schema、result contract、驗證 JSON 與 pandas 版本。
3. 清楚說明 Raw、Cleaned、Summary、Exceptions；Summary 的分組鍵可連回 Cleaned 的原始來源。
4. 列出使用者指定的呈現需求與最終輸出路徑 Final Report.xlsx。
5. 先確認環境中的 OfficeCLI 真正可用，讀取該版本的工具說明／help。此套件不猜測 CLI 語法、不安裝同名未知工具。
6. 只操作已授權的 workbook 呈現範圍；不改寫 Raw/Cleaned 的業務值。公式與圖表引用已驗證資料範圍。
7. 另存最終報表，對資料 sheets 回讀核對 row_count、ID、total、Exceptions；如果新增公式 sheet，資料驗證仍針對原資料 sheets。

交接摘要範本：

```text
Input: Intermediate.xlsx
Data sheets: Raw, Cleaned, Summary, Exceptions
Cleaned contract: result.json
Lineage: source_file/source_sheet/source_row
Presentation request: 使用者指定的樣式、圖表、原生 PivotTable
Output: Final Report.xlsx
Required post-checks: Cleaned 筆數/ID/總額與 Exceptions 數不變
```

沒有 OfficeCLI 時以 pandas 產出的功能正常 XLSX 完成資料交付，回報「呈現未執行」；不把 optional handoff 當硬依賴。
handoff 文件完成不等於 OfficeCLI 已實際執行，回報時需明確區分。
