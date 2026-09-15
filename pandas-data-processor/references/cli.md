# 統一 CLI

本套件的指令名稱為 `pandas-processor`，不是 pandas 官方提供的指令。
Skill 主要在大量資料或多檔批次清理／轉換時啟用；CLI 提供固定參數、驗證、JSON 與退出碼。一般單一 Excel 的簡單操作優先交給 OfficeCLI；單一檔案本身很大且需要批次資料處理時仍可使用此工具。

## 啟動

在 Windows 套件目錄，直接呼叫：

```powershell
.\pandas-processor.cmd --help
.\pandas-processor.cmd --version
.\pandas-processor.cmd doctor
.\pandas-processor.cmd inspect tests/fixtures/sales.csv --sample 3
```

`.cmd` 先找套件內 `.venv`，再找上一層 `.venv`；啟動選定的 Python，無須 activate。
從其他目錄呼叫時使用 launcher 完整路徑，並保留呼叫者 cwd。帶空白或 shell 特殊字元的檔名要加引號。
它不是內含 Python/pandas 的獨立執行檔，不能只複製 `.cmd` 就在其他電腦使用；需依 README 安裝環境。

套件安裝後也會在所選 Python 環境產生原生 console 入口：

```powershell
..\.venv\Scripts\pandas-processor.exe --help
..\.venv\Scripts\python.exe -m pandas_processor --help
```

若入口已在 PATH，可以直接使用 `pandas-processor`。本次安裝未修改全域 PATH。
安裝／版本問題先用 doctor 查看實際 interpreter 和依賴版本，不自動下載或切換環境。

此原始碼交付包不附 dist 建置產物；直接依 README 使用 `python -m pip install .` 安裝，安裝器會處理宣告的 runtime 依賴。
若另外取得建置出的 wheel，也可使用 `python -m pip install <wheel路徑>`。wheel 僅安裝 CLI 與核心程式；給 Agent 使用 skill 時仍需完整 skill 資料夾。

## 功能映射

| 子指令 | 原有 script | 用途 |
| --- | --- | --- |
| inspect | inspect_table.py | 表格 metadata 和有限樣本 |
| workbook | inspect_workbook.py | 所有 XLSX sheet 的 metadata |
| profile | profile_data.py | 完整記憶體內 profiling |
| combine | combine_files.py | schema 相容的多檔 concat |
| validate | validate_schema.py | schema、型別、鍵與限制 |
| validate-result | validate_result.py | 結果契約 |
| totals | compare_totals.py | 前後總額 |
| duplicates | find_duplicates.py | 所有重複群組成員 |
| exceptions | find_exceptions.py | 原始問題值與來源 |
| clean（別名 export） | export_report.py | 正規化、驗證、匯出 |

以 `pandas-processor combine --help` 等子指令 help 取得完整參數，不必讀取全部程式碼。
clean 只執行既有 schema 轉型／驗證流程，沒有隱含填值、去重、任意 SQL 或任意運算表達式。
GroupBy Summary 使用 `--group-by` 及 `--sum-columns`；自訂 Merge／Filter／Pivot 依 dataframe-patterns 使用共用 Python 模組。

## 輸出與穩定性

資料命令／doctor 返回 JSON；--help、--version 為文字。
成功 exit 0；輸入／驗證錯誤 exit 2；I/O、依賴或執行環境錯誤 exit 3。
doctor 只確認套件可匯入與版本，不宣稱已完整測試所有操作。
舊 scripts 和 CLI 使用 `src/pandas_processor/` 同一套核心邏輯，不另複製清洗算法。
統一入口改善參數一致性、部署與錯誤判讀；正確性依舊來自 schema、總額核對、來源追蹤及測試。
