# 大型資料政策

開始前計算檔案數、磁碟大小、欄數、筆數，並確認可用 RAM。
CSV 磁碟大小或壓縮 XLSX 大小不是記憶體需求；字串、索引、concat 與 merge 副本可顯著增加使用量。
用代表性樣本的 `memory_usage(deep=True)` 估算，再為轉型、join、輸出保留空間；沒有通用安全倍數。

`inspect_table` 的 CSV 讀取使用 chunksize，累加筆數/null 並保留最多 20 筆樣本。
精確全域重複數需存全域狀態，所以 inspect 的 duplicate_count 為 null，不能冒稱零。
`find_duplicates` 與 `profile_data` 提供記憶體內完整檢查。

讀取優先用 `usecols`；CSV 可對 chunk 做可結合的 sum/count，再合併局部結果。
跨 chunk 的唯一鍵、去重、排序、join、median 不能靠逐 chunk 獨立檢查保證正確；需要全域 state 或外部引擎。
本套件 combine/report/validation 會載入完整資料；`--chunksize` 不會把這些命令變成 streaming pipeline。
Excel 沒有 read_csv 相同的 chunksize API；必要時先由可信流程提供 CSV/Parquet 分區。

若估算超出合理 RAM，選 DuckDB SQL、Polars lazy、PyArrow 或資料庫，並沿用 schema/provenance/total contracts。
OUT_OF_MEMORY 後不得原樣反覆重試；改欄位投影／分批算法，仍不適合則換引擎。
參考 [pandas scaling guide](https://pandas.pydata.org/docs/user_guide/scale.html)。
