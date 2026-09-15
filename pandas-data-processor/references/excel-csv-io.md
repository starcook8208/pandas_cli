# Excel／CSV I/O

先 inspect 決定檔案、表頭及欄位，再載入。不要把數十萬列輸出給 Agent。
CLI 一致提供 encoding、delimiter、sheet、header、usecols、chunksize。
CSV 用 `dtype="string", keep_default_na=False, na_values=[""]` 保護識別碼與文字 NA；空欄保留 null。
UTF-8/BOM 為預設；已知 Big5 請明確設定 cp950。禁止 errors=ignore 與 on_bad_lines=skip。

Excel 讀取使用 openpyxl，写入 XlsxWriter。`ExcelFile` 適合 sheet discovery；`ExcelWriter` context manager 寫多 sheet。
來源含公式會停止：需由可信系統另行輸出已計算的 values-only 檔，避免 pandas 讀取過時公式 cache。
Excel 數字加前導零樣式不等於文字識別碼；已丟失的原始零不能憑空補回。

官方 engine 能力（本套件只啟用 CSV/XLSX）：

| engine | 官方用途 | 本套件 |
| --- | --- | --- |
| openpyxl | 新式 Excel 讀寫 | XLSX 讀取 |
| xlsxwriter | XLSX 寫入 | XLSX 安全字串輸出 |
| xlrd | 舊式 XLS 讀取 | 未安裝 |
| calamine / python-calamine | XLS/XLSX/XLSM/XLSB/ODS 讀取 | 未安裝 |
| pyxlsb | XLSB 讀取 | 未安裝 |
| odf / odfpy | OpenDocument 讀寫 | 未安裝 |

參考 [read_excel](https://pandas.pydata.org/docs/reference/api/pandas.read_excel.html)、[ExcelWriter](https://pandas.pydata.org/docs/reference/api/pandas.ExcelWriter.html)、[官方依賴](https://pandas.pydata.org/docs/getting_started/install.html)。

CSV 預設忠實輸出字串供資料交換；交由人用試算表開啟時，選 `--spreadsheet-safe-csv` 或 XLSX。
CSV 防公式前綴會改變字面值，因此須在回報保留 `csv_formula_cells_escaped`，不把安全呈現副本當原始資料。
XLSX 禁止自動公式／超連結／數值推斷。不要為了樣式在 pandas 重建原 workbook 的所有物件；交給 OfficeCLI。
