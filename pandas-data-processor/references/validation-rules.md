# 驗證規則

結構錯誤（缺欄、重複表頭、未知 schema 規則）直接失敗。欄位資料錯誤先建立 Exceptions。
Raw 欄位保留字串，typed Cleaned 僅含合法列；original_value 永遠來自 Raw。

檢查層次：

1. Schema：required/optional 欄位、dtype、nullable、enum、min/max、pattern、unique_key。
2. Transformation：Filter 排除理由、Join cardinality、GroupBy/Pivot 的聚合語意與 lineage。
3. Result contract：row_count、required_columns、duplicate_count、null_counts、unique_ids、totals、exception_count。
4. Export round trip：回讀 Cleaned/Summary 比較 ID、筆數、總額，確認輸出完整。

`compare_totals` 用 Decimal 逐值累加，預設 atol=rtol=0。商業規則允許誤差時才設定 tolerance。
總額驗證含 missing 會失敗；沒有資料的空集合總額為 0，但必須另驗 row_count，避免把遺失資料誤認為空集合。
轉型或分組使用浮點時可能有表示誤差；高精度任務使用整數最小貨幣單位／Decimal 運算並指定捨入政策。

異常數和無效列數不同：同一列可能有日期、金額及鍵三個問題。
`raw_rows = valid_rows + invalid_rows` 必須成立；`exception_count` 是所有欄位問題的筆數。
無 schema 不代表沒有錯，只能回報觀測資訊或欄位集合相容。
combine_files 在各輸入通過 schema 後，還會檢查合併結果的跨檔／跨 sheet 唯一鍵重複。
數值轉型若改變原始數字的精確十進位值，會列為 NUMERIC_PARSE_ERROR；不靜默接受精度損失。

`--allow-exceptions` 僅供使用者接受「有效資料子集」時使用，必須保留 Exceptions 並讓結果契約承認異常數。
這不能豁免 MERGE_CARDINALITY_ERROR 或 TOTAL_MISMATCH。
