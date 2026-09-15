# Merge 錯誤

MERGE_CARDINALITY_ERROR 是 hard stop。
查看 audit 的 left/right/result rows、duplicate key rows 與 unmatched key counts。
對兩側執行 find_duplicates --keys，依來源檔／sheet／row 查重複是否合理。
many_to_one 失敗不可直接改 many_to_many；需使用者／業務規格確認關係。
null keys 在 pandas 可能互配，本 helper 先拒絕；依明確政策將缺鍵列列為 Exceptions 或單獨處理。
不得任意 drop_duplicates 來通過 merge；定義資料保留規則後重新驗證筆數與守恆總額。
