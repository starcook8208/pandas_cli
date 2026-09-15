# 編碼錯誤

預設 UTF-8 with optional BOM。ENCODING_ERROR 時先查 BOM、供應系統匯出設定或使用者指定編碼。
Big5/CP950 確定後使用 --encoding cp950；UTF-16 確定後使用 --encoding utf-16。
偵測工具只能提供線索，不能保證語意正確；重試後仍應檢查代表性中文欄名與值。
禁止 errors=ignore／replace，避免不可逆丟字；不得把任何可解碼的候選都當正確。
拿不到可靠編碼依據或一次明確編碼重試仍失敗時，回報並要求來源重匯出 UTF-8，保留原檔。
