# 輸入與 Schema

Metadata 描述觀測狀態，schema 描述應符合的規則；兩者不能互換。
必須把使用者的欄位／業務規則寫成 JSON，不能從資料自動推斷唯一鍵或補值規則。

JSON 根物件允許：

| 欄位 | 意義 |
| --- | --- |
| required_columns | 必填的欄名 → dtype 字串或規則物件；必須存在，可為空物件 |
| optional_columns | 可缺少的欄位；出現時同樣驗證 |
| unique_key | 字串陣列，作為複合唯一鍵，不能空值；省略表示不檢查 |
| allow_extra_columns | boolean，預設 true；false 時拒絕未定義欄，來源欄除外 |

欄位規則：`dtype` 必填，允許 string/number/integer/datetime/boolean。
`nullable` 預設 true；`min`/`max` 僅數值；`enum` 是正規化後的允許值陣列；
`pattern` 對原始字串執行完整 regex match；`format` 指定日期格式，預設 ISO8601。
布林值只接受不分大小寫 true/false。數值禁止無限值；integer 禁止小數。
未知規則會拒絕，避免拼字錯誤造成未執行驗證。

例見 [schema.example.json](schema.example.json)。optional 不代表出現後可以不驗證。
唯一鍵依正規化後值檢查，所有重複成員列都進入 Exceptions，不任意保留第一筆。

原始 CSV/XLSX 以 nullable string 讀取，空欄是 missing；NA/NULL/Unknown 是原始文字，除非任務另有明確規則。
來源檔案必須是穩定快照；支援單列完整表頭，拒絕空白或重複欄名。
