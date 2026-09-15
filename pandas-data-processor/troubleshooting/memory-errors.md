# 記憶體不足

OUT_OF_MEMORY 後停止原有策略，保留來源與已有診斷。
查看所需欄位與代表性樣本記憶體，使用 usecols，降低不必要的中間副本。
CSV 的 sum/count 可分 chunk 累加；跨 chunk duplicate/join/sort 需要全域演算法。
combine_files、validate_schema、profile、export_report 仍使用完整 DataFrame，單純把 chunksize 調小無法解決最終資料超出 RAM。
如果輸入根本不適合記憶體，切換 DuckDB、Polars、PyArrow 或資料庫，保留相同 validation/provenance。
不要反覆執行同一條耗盡記憶體的指令，也不要把不完整輸出當成功資料。
