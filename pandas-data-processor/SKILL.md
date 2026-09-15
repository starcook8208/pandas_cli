---
name: pandas-data-processor
description: 用於大量表格資料或多檔批次資料的清理、型別正規化、資料集合併、結構轉換及結果驗證。一般單一 Excel 的讀寫、簡單修改、公式、格式、圖表與原生 PivotTable 優先使用 OfficeCLI；不要僅因提到 Excel、CSV 或少量清理就呼叫此 skill。單一檔案本身含大量資料且需要批次清理或轉換時也適用。
---

# Pandas Data Processor

優先順序：資料正確性 → 可追溯性 → 驗證 → 可復原性 → 效能 → 外觀。
使用者決定業務需求；Agent 規劃與解讀；pandas 執行確定性的表格運算。
主要操作入口為 `pandas-processor`；Windows 若 PATH 找不到指令，以此 skill 目錄下 `pandas-processor.cmd` 的完整路徑呼叫，不需手動啟用虛擬環境。輸入／輸出相對路徑以呼叫者的工作目錄為準。

## 入口與路由

先確認任務需要大量資料處理或多檔批次清理／轉換，再使用下列流程。一般單一 Excel 或少量資料的簡單操作優先交給 OfficeCLI；多個檔案若只需樣式或工作表操作，也不因此啟動本 skill。以資料量和處理需求判斷，不硬設檔案數或列數門檻：單一檔案本身含大量資料且需批次清理／轉換時仍適用。使用者明確指定本 skill 時依其需求使用。本 skill 的檢查、驗證與匯出工具僅支援已啟動的資料處理流程；完成後將 Excel 製作交回 OfficeCLI。

- 初次使用：讀 [執行政策](specs/execution-policy.md)、[輸入規格](specs/input-schema.md)。以 `pandas-processor doctor` 確認環境；找不到入口或要查指令映射時再讀 [CLI 操作](references/cli.md)。
- CSV/XLSX 匯入、表頭、sheet、編碼：讀 [I/O](references/excel-csv-io.md)，先執行 `pandas-processor inspect` 或 `workbook`。
- 欄位型別或業務規則：讀 [驗證規則](references/validation-rules.md)、[schema 範例](specs/schema.example.json)，執行 `pandas-processor validate`。
- 篩選、排序、GroupBy、Merge、Pivot：讀 [DataFrame 模式](references/dataframe-patterns.md)，需要 API 細節再讀 [API 索引](references/pandas-api.md)。
- 多檔案：`pandas-processor combine`；保持 [provenance](specs/provenance-schema.md)。
- 大型資料：操作前讀 [容量政策](references/large-data.md)。超過合理 RAM、分散式或資料庫查詢不要硬用 pandas；考慮 DuckDB、Polars、PyArrow 或資料庫。
- 清理與匯出：讀 [輸出契約](specs/output-schema.md)，執行 `pandas-processor clean`，並以 `validate-result`、必要時 `totals` 核對。
- 錯誤：依 [復原路由](troubleshooting/recovery.md) 及 [錯誤碼](specs/error-schema.md) 處理。
- 需要 Excel 美化：讀 [OfficeCLI handoff](references/officecli-handoff.md)。OfficeCLI 不可成為資料處理的必要依賴。

## 標準流程

1. 探索指定輸入，確認檔案數、大小、sheet、表頭與可用記憶體；輸出使用不同路徑。
2. Inspect 得到 metadata：實際筆數、欄數、null、樣本及樣本推斷。Metadata 是觀測，不是 schema。
3. 依使用者需求／業務規則定義 schema：應有的欄位、型別、nullability、唯一鍵、限制。不要用觀測結果自行降低標準。
4. 用字串讀取原始資料保護 `001234` 等識別碼；驗證並依 schema 正規化。缺值保留，不自行填零、Unknown、均值或前後值。
5. 保留 Raw 與 source_file/source_sheet/source_row。轉型失敗與重複鍵进入 Exceptions，記錄原始值；不得靜默丟棄。
6. 執行需求中的轉換。Merge 明確指定 cardinality、預期筆數，檢查兩側重複鍵與未配對鍵。使用 `operations.safe_merge`；空鍵先依明確業務規則處理。
7. 驗證結果：筆數、必填欄、null、唯一 ID、重複、異常數。應守恆的金額／數量另比對前後總額；容差必須有業務依據。
8. `MERGE_CARDINALITY_ERROR`、`TOTAL_MISMATCH` 一律停止報表輸出。其他失敗也不得宣稱成功；只能輸出標示清楚的診斷／Exceptions。
9. 將驗證通過的結果匯出。只在使用者明確接受有效子集時使用 `--allow-exceptions`，並讓 contract 接受實際異常數；最終回報此限制。
10. 若需呈現，再交給 OfficeCLI；完成後重新比對筆數、ID、總額及 Exceptions。

## 工具選擇

優先呼叫 CLI，參數不明時只讀 `pandas-processor <子指令> --help`；不預設把 src/ 或 scripts/ 原始碼全部載入。
`inspect`／`workbook` 回傳有限樣本；`profile`、`duplicates` 是完整記憶體運算。
`combine` 僅 concat，不暗中 join 或補缺欄。沒有 schema 時只保證欄位集合一致。
`exceptions` 輸出完整問題資料；一列可能有多個欄位問題。
`clean` 依 schema 正規化型別並驗證後匯出，XLSX 包含 Raw/Cleaned/Exceptions，可選 Summary；不擅自補值或去重。`export` 為相同指令別名。
CLI 未提供的業務轉換，由 Agent 使用 `pandas_processor` 共用模組及公開 pandas API 撰寫任務腳本，沿用驗證與來源規範。Skill 決定何時使用，CLI 執行固定流程，兩者互相配合。

## 交付

回報輸入與輸出路徑、使用的 schema/contract、筆數與異常數、總額核對、pandas 版本、實際測試範圍與限制。
區分資料處理完成與 OfficeCLI 呈現完成，不能用美化需求跳過資料驗證。
