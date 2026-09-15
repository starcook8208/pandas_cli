# 實測紀錄

日期：2026-09-15。環境：Windows PowerShell、Python 3.12.14。

此為歷史實測紀錄。交付包已移除快取、build/dist、egg-info 與 output；下方列出的 wheel／範例輸出不隨包附送，可依 README 重新產生。清理不代表已新增或通過 Mac 實測。

| 元件 | 實測版本 |
| --- | --- |
| pandas-processor CLI | 0.1.0 |
| pandas | 3.0.5 |
| openpyxl | 3.1.5 |
| XlsxWriter | 3.2.9 |
| pytest | 9.1.1 |

## 結果

- CLI 整合後 pytest：**90 passed in 90.18s**；包含原本 68 項與新增 22 項 CLI 整合測試。
- 包含舊 scripts 及統一 CLI 的 help、CSV/XLSX、跨 sheet、schema、duplicate、exception、result contract、total、merge、輸出保護等功能測試。
- 已實測安裝後的 console 入口、`python -m pandas_processor`、Windows `.cmd` 啟動器；不需啟用虛擬環境，從其他工作目錄亦能使用。
- 中文、空白及 `&` 檔名傳遞成功，相對輸入路徑仍以呼叫者 cwd 解析，退出碼保留。
- Skill Creator 的 `quick_validate.py`：`Skill is valid!`。Windows 需 `python -X utf8` 讀取本 UTF-8 SKILL.md。
- 套件實際檔案沒有空檔或未完成標記；scripts 沒有 pandas 私有 API、eval/exec 或 shell=True。

## 獨立工作流（pytest 之外）

1. sales.csv → output/cleaned.csv：2 筆，schema/result contract 通過，金額 30.00 守恆。
2. sales.csv → output/report.xlsx：Raw=2、Cleaned=2、Summary=1、Exceptions=0。
3. 回讀 report.xlsx 的 Cleaned，筆數、必填欄、ID、null、重複、金額與 Exceptions 數全部通過。
4. 回讀 Summary 比對來源金額：30.00 → 30，差額 0.00。
5. invalid.csv → output/exceptions.xlsx：3 筆無效來源資料、5 筆欄位問題，回傳 VALIDATION_FAILED；診斷檔保留原值與來源。
6. 完整 XLSX 輸入 → XLSX 輸出、duplicate CLI 與預期非零退出碼另由 pytest 實際驗證。

目前工作區可在套件目錄使用：

```powershell
..\.venv\Scripts\python.exe -m pytest -q
.\pandas-processor.cmd workbook output/report.xlsx
.\pandas-processor.cmd doctor
```

虛擬環境在套件上一層 `.venv`；下載用 uv/Python/cache 位於工作區 `.tools`。
CLI 以 editable package 安裝於上述 `.venv`，產生 `.venv/Scripts/pandas-processor.exe`。
原始碼移至 src/pandas_processor，舊 scripts 為相容入口；新版 CLI 與舊版共用相同核心模組。
套件可複製至其他環境後依 README 安裝；未修改全域 PATH 或安裝至全域 skills 目錄。

## Wheel 安裝驗證

已建置 `dist/pandas_data_processor-0.1.0-py3-none-any.whl`，並在獨立 `.tools/cli-wheel-env` 安裝驗證。
這個 wheel 包含 CLI 和 Python 核心程式，不包含 Python interpreter、pandas 二進位依賴或完整 skill 文件。

- 僅安裝 wheel、尚無 runtime 依賴時：根 help 成功 exit 0；doctor 及 inspect 回 DEPENDENCY_ERROR／exit 3。
- 安裝 runtime 依賴後：doctor、clean、validate-result、totals 全部成功 exit 0。
- 產生 `output/cli-wheel-report.xlsx`：Raw=2、Cleaned=2、Summary=1、Exceptions=0，金額 30.00 守恆。
- wheel 測試從原始碼套件以外的工作目錄呼叫獨立環境 exe，確認不依赖 editable 安裝或 checkout import 路徑。

## 驗證範圍

這些測試證明小型代表性資料與特定失敗案例可運作，未做大規模容量壓測、其他作業系統或其他 pandas 版本矩陣。
OfficeCLI handoff 文件已完成；未實際執行 OfficeCLI 美化或原生 PivotTable。
支援範圍與已知限制以 README、large-data 與 I/O 文件為準。
