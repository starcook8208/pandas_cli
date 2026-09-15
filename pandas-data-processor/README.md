# pandas-data-processor

表格資料清理與轉換 CLI，指令名稱 `pandas-processor`。這是自訂工具，不是 pandas 官方 CLI。
同時保留供 Agent 使用的 [SKILL.md](SKILL.md)，提供按需文件、資料規格及復原指南。一般 Excel 操作仍交由 OfficeCLI。

## 複製到 Mac

將完整資料夾複製或解壓到 Mac 即可，不需複製 Windows 的 `.venv`、`.tools` 或其他工作區檔案。
交付包保留原始碼、skill 文件、測試及 fixtures；已排除快取、build/dist、egg-info 與歷史範例輸出。
Mac 首次使用需安裝 Python 3.11 以上，再依下方安裝步驟操作。要先驗證該 Mac 是否可正常使用，在套件目錄執行 `python3 scripts/verify_macos.py`；詳見 [macOS 驗證](tests/macos.md)。

## 架構與目錄

```text
使用者 → Agent → SKILL.md → Inspect/Metadata → Schema 驗證
       → pandas-processor CLI → pandas 轉換 → 結果驗證 → CSV/XLSX → OfficeCLI（選用）

pandas-data-processor/
  SKILL.md                 Agent 入口與路由
  pyproject.toml           套件依賴、版本及 CLI 註冊
  pandas-processor.cmd     Windows 專案啟動器（不用 activate）
  requirements.txt         執行與測試依賴
  references/              API、I/O、運算、驗證、容量與 OfficeCLI
  src/pandas_processor/    共用運算、驗證、CLI 分派
  scripts/                 舊版相容入口與啟動器
  specs/                   schema、輸出契約、來源、錯誤與執行政策
  troubleshooting/         依錯誤分類的復原方式
  tests/fixtures/          測試程式與小型文字資料
```

## 安裝

需要 Python 3.11 以上；本套件以 pandas 3.0 公開 API 為目標。
新環境在套件目錄安裝（Windows PowerShell）：

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install ".[test]"
.\pandas-processor.cmd doctor
```

只需執行工具可用 `pip install .`，不安裝 test extra；開發時可使用 `pip install -e ".[test]"`。
macOS/Linux 用 `.venv/bin/python -m pip install .`，再直接呼叫 `.venv/bin/pandas-processor`，不需 activate。
PyYAML 用於 skill 格式檢查，pytest 用於測試；runtime 只依賴 pandas/openpyxl/XlsxWriter。
`requirements.txt` 保留給舊版 scripts 的依賴安裝；正式 CLI 的版本與依賴以 pyproject.toml 為準。
讓 Agent 讀取本套件的 SKILL.md 即可使用；若需自動發現，將整個資料夾放到目標 Agent 設定的 skills 目錄。此產物未更動全域 Agent 設定。

本工作區已安裝 CLI 至上一層 `.venv`，可直接執行下列 quick start。
若要在目前 PowerShell 視窗直接輸入 `pandas-processor`，在套件目錄執行：

```powershell
$env:Path = (Get-Location).Path + [IO.Path]::PathSeparator + $env:Path
pandas-processor --version
```

這只改目前視窗的 PATH，不修改使用者／系統設定。也可以始終用 `.cmd` 完整路徑，從任何工作目錄呼叫。
此版本不是打包 Python 的單一獨立 exe；環境仍需存在，但不用手動啟用。安裝會另產生 `.venv/Scripts/pandas-processor.exe`（Windows）或 `.venv/bin/pandas-processor`（Unix）。

## 快速開始

以下命令在本套件目錄執行，不需 activate。範例輸出使用新檔名；重跑時需換名稱，或明確指定 `--overwrite` 替換既有輸出。

```powershell
.\pandas-processor.cmd --help
.\pandas-processor.cmd inspect tests/fixtures/sales.csv
.\pandas-processor.cmd validate tests/fixtures/sales.csv --schema specs/schema.example.json
.\pandas-processor.cmd clean tests/fixtures/sales.csv --schema specs/schema.example.json --contract tests/fixtures/result.json --output output/cli-report.xlsx --group-by department --sum-columns amount
.\pandas-processor.cmd workbook output/cli-report.xlsx
.\pandas-processor.cmd validate-result output/cli-report.xlsx --sheet Cleaned --contract tests/fixtures/result.json --exceptions-file output/cli-report.xlsx --exceptions-sheet Exceptions
.\pandas-processor.cmd totals tests/fixtures/sales.csv output/cli-report.xlsx --after-sheet Summary --columns amount
```

CSV 工作流：

```powershell
.\pandas-processor.cmd clean tests/fixtures/sales.csv --schema specs/schema.example.json --contract tests/fixtures/result.json --output output/cli-cleaned.csv
.\pandas-processor.cmd totals tests/fixtures/sales.csv output/cli-cleaned.csv --columns amount
```

多檔案與診斷：

```powershell
.\pandas-processor.cmd combine "input/*.csv" --schema specs/schema.example.json --output output/combined.xlsx
.\pandas-processor.cmd combine input --all-sheets --output output/all-sheets.xlsx
.\pandas-processor.cmd duplicates tests/fixtures/invalid.csv --keys employee_id --output output/duplicates.csv
.\pandas-processor.cmd exceptions tests/fixtures/invalid.csv --schema specs/schema.example.json --output output/exceptions.xlsx
.\pandas-processor.cmd profile tests/fixtures/sales.csv --sample 0
```

重複／異常命令找到問題時，診斷檔仍會寫出，但 JSON `status=error` 且 exit code 非零，這是預期行為。
所有 CLI 支援 `--help`。`--sheet` 使用精確名稱；`--header` 是從零起算的表頭位置。
完整映射與退出碼見 [CLI 操作](references/cli.md)。舊 `python scripts/*.py` 入口仍可用，和 CLI 共用核心程式。
clean 表示 schema 型別正規化與驗證，不會自行去重或填值；特殊業務轉換仍可用 `pandas_processor` 模組組合。
`--encoding cp950` 可用於已確認 Big5/CP950 的 CSV；不會自動猜測編碼或略過壞列。

## 測試

```powershell
..\.venv\Scripts\python.exe -m pytest -q
```

涵蓋 CSV/XLSX、多 sheet、來源追蹤、前導零、missing、重複鍵、數值異常、schema 不相容、總額不符、merge 膨脹、匯出保護及各 CLI。
測試以暫存目錄生成 XLSX，不需要提交 binary fixtures。

Mac 真機驗證可執行 `python3 scripts/verify_macos.py`，自動建立隔離環境、執行測試並保存結果；步驟與範圍見 [macOS 驗證](tests/macos.md)。目前尚未取得真實 Mac 實測結果。

## 錯誤模型

正常 stdout 是單一 JSON 物件。成功 exit 0；輸入／schema／資料驗證失敗 exit 2；I/O、記憶體、匯出失敗 exit 3。
`--help` 與 `--version` 印文字並 exit 0；根目錄 help 不載入 pandas。統一 CLI 在資料引擎依賴缺失時返回 DEPENDENCY_ERROR，可用 doctor 診斷。舊 scripts 在未安裝依賴時仍可能先出現 Python import 錯誤。
詳見 [error-schema](specs/error-schema.md)。MERGE_CARDINALITY_ERROR 與 TOTAL_MISMATCH 禁止產出成功報表。

## 格式、限制與 OfficeCLI

- 目前執行工具讀寫 CSV、XLSX；XLS/XLSB/ODS/XLSM 未啟用。可依官方 engine 文件另行擴充及測試，不自動安裝不用的 engine。
- CSV inspect 使用 chunksize；concat、profile、唯一鍵檢查、report、Excel 仍在記憶體執行。大到 RAM 不足時改選 out-of-core 引擎。
- CSV 先串流檢查每筆欄數，再以 pandas 讀取，會掃描兩次。來源需保持穩定；請對可變檔使用已完成的快照。
- 原始欄位以字串保存；Excel 數值儲存格的顯示格式 `000000` 無法還原為來源文字識別碼，請提供文字欄。日期 ISO8601 預設正規化為 UTC 無時區，其他格式需 schema 明定。
- XLSX 公式輸入會被拒絕，避免使用過時 cache 或把公式當空值；先以可信工具產生獨立 values-only 資料來源。不保留原 workbook 樣式、巨集與公式。
- 數值正規化使用 pandas，偵測到精度損失時列為異常；極大數／高精度財務轉換應另用 Decimal 或最小貨幣單位。總額比較使用原始字串轉 Decimal，預設零容差；不會略過缺值。Excel 數值儲存亦有精度限制，高精度值須以字串交付並另外驗證。
- CSV 本身不含型別；`NA` 等字串保留，只有空欄表示缺值。CSV 直接用 Excel 開啟可能觸發型別推斷；識別碼呈現優先用 XLSX。
- CSV 為忠實交換格式；若將交給試算表使用，可明確選 `--spreadsheet-safe-csv`，會以 apostrophe 前綴公式樣字串並回報修改數。XLSX 原始字串不會被寫成公式或自動超連結。
- XLSX 上限為每 sheet 1,048,575 筆資料加表頭、16,384 欄與每 cell 32,767 字元；超出停止。
- OfficeCLI handoff 規格已提供，但未綁定或自動執行未知版本的 OfficeCLI。pandas 先輸出正常 XLSX；OfficeCLI 可接手样式、圖表、原生 PivotTable、Dashboard，再重新驗證。

官方依据：[pandas API](https://pandas.pydata.org/docs/reference/index.html)、[I/O](https://pandas.pydata.org/docs/user_guide/io.html)、[GitHub](https://github.com/pandas-dev/pandas)。版本與實測結果見 [驗證紀錄](tests/verification.md)。
