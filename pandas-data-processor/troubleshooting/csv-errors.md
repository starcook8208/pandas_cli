# CSV 錯誤

CSV_PARSE_ERROR 常見原因為分隔符不對、不閉合引號或某列欄數不同。
確認 delimiter 和 quoting 的來源規格；本工具採標準雙引號 escaping 與單字元 delimiter。
報告中的 row 是邏輯記錄序號，內嵌換行會讓它不同於實體文字行號。
不要使用 on_bad_lines=skip。要求來源重新匯出，或建立另存的修復副本並記錄逐列修改依據。
空白標題、重複欄名先修正明確 schema；不要接受 pandas 自動補出的欄名作為業務欄名。
