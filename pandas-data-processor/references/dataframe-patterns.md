# 資料轉換模式

先 `read_table` 取得 raw，`validate_frame` 取得 typed valid rows 與 exceptions，再進行任務轉換。
CLI 已支援的操作優先直接執行；以下為需要自訂轉換時，從已安裝套件匯入 helpers 的方式。完整執行仍須依使用者需求定義契約。

```python
from pandas_processor.table_io import read_table
from pandas_processor.validation import validate_frame
from pandas_processor.errors import read_json

raw = read_table("sales.csv")
cleaned, exceptions = validate_frame(raw, read_json("schema.json"))
selected = cleaned.loc[cleaned["amount"] >= 100].copy()
ordered = selected.sort_values(["date", "employee_id"], kind="stable")
```

篩選會改變筆數及總額；驗證應依篩選條件計算，不聲稱原始總額必然守恆。排序／純重排則應守恆。
保留被排除列及原因，尤其是因資料無效而被排除的列。

分組總額：

```python
summary = cleaned.groupby("department", dropna=False, observed=True)[["amount"]].sum(min_count=1).reset_index()
```

多指標可用 named aggregation，例如 `.agg(order_count=("employee_id", "size"))`。
若金額含 null，先按業務規則處理；不得用 sum 預設零掩蓋缺值。

Merge 用本套件的已檢查 helper：

```python
from pandas_processor.operations import safe_merge
joined, audit = safe_merge(
    orders, customers, on=["customer_id"],
    cardinality="many_to_one", expected_rows=len(orders), how="left",
)
```

兩側需具來源資訊（read_table attrs 或既有 provenance）；result 保留兩側來源與 `_merge`。
audit 包含兩側筆數、重複鍵列數、未配對鍵數及結果筆數。m:m 仍須 expected_rows。
多次串接 join 時先為各來源欄設定不衝突的角色名稱；不要 drop lineage 來避開欄名衝突。
合併完成後，按業務契約檢查 unmatched 與應守恆的 measures。

Pivot 必須先確認每個 index/column pair 唯一；重複時停止並確認是否要聚合。
使用 pivot_table 前明定 aggfunc（sum/count/mean 等），不默認平均值；不擅自 fill_value=0。
pandas pivot_table 是計算後的資料表，不是 Excel 原生 PivotTable；原生物件交由 OfficeCLI。
