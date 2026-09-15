# pandas 公開 API 索引

2026-09-15 查閱官方文件，文件版本 3.0.5。執行版本以 `pd.__version__` 與實測紀錄為準。
只依賴 pandas 公開 API，不使用 pandas.core、compat 或其他私有模組。
來源：[官方 API](https://pandas.pydata.org/docs/reference/index.html)、[原始碼](https://github.com/pandas-dev/pandas)。

| 需求 | 官方 API 與注意事項 |
| --- | --- |
| 表格 | [DataFrame](https://pandas.pydata.org/docs/reference/api/pandas.DataFrame.html)：欄位可有不同 dtype |
| CSV | [read_csv](https://pandas.pydata.org/docs/reference/api/pandas.read_csv.html)：dtype、usecols、encoding、chunksize 明確指定 |
| Excel | [read_excel](https://pandas.pydata.org/docs/reference/api/pandas.read_excel.html)：sheet_name、engine、dtype 明確指定 |
| 多 sheet | [ExcelFile](https://pandas.pydata.org/docs/reference/api/pandas.ExcelFile.html)：context manager 取得 sheet_names |
| Workbook 輸出 | [ExcelWriter](https://pandas.pydata.org/docs/reference/api/pandas.ExcelWriter.html)：context manager 完成關檔 |
| 疊列 | [concat](https://pandas.pydata.org/docs/reference/api/pandas.concat.html)：先驗 schema 再一次 concat |
| 合併 | [merge](https://pandas.pydata.org/docs/reference/api/pandas.merge.html)：validate/indicator；null key 會互配，m:m 不做唯一性檢查 |
| 分組 | [groupby](https://pandas.pydata.org/docs/reference/api/pandas.DataFrame.groupby.html)：明定 dropna=False、observed=True |
| 彙總 | [agg](https://pandas.pydata.org/docs/reference/api/pandas.DataFrame.agg.html)：明定欄位與運算，不讓數值字串被串接 |
| 轉寬表 | [pivot](https://pandas.pydata.org/docs/reference/api/pandas.DataFrame.pivot.html)：重複 index/column 組合會失敗 |
| 分組轉寬表 | [pivot_table](https://pandas.pydata.org/docs/reference/api/pandas.DataFrame.pivot_table.html)：必須明定 aggfunc，不能擅自採用預設平均值 |
| CSV 輸出 | [to_csv](https://pandas.pydata.org/docs/reference/api/pandas.DataFrame.to_csv.html)：index=False，CSV 不保留型別 |
| XLSX 輸出 | [to_excel](https://pandas.pydata.org/docs/reference/api/pandas.DataFrame.to_excel.html)：index=False，匯出前檢查 Excel 上限 |
| 日期 | [to_datetime](https://pandas.pydata.org/docs/reference/api/pandas.to_datetime.html)：errors=coerce 搭配失敗遮罩，格式須明確 |
| 數字 | [to_numeric](https://pandas.pydata.org/docs/reference/api/pandas.to_numeric.html)：errors=coerce 不等於成功；注意超大整數精度 |
| 重複 | [duplicated](https://pandas.pydata.org/docs/reference/api/pandas.DataFrame.duplicated.html)：keep=False 保留所有重複成員 |
| 去重 | [drop_duplicates](https://pandas.pydata.org/docs/reference/api/pandas.DataFrame.drop_duplicates.html)：只有已明定保留規則才用 |
| 缺值 | [missing data](https://pandas.pydata.org/docs/user_guide/missing_data.html)：isna/notna，禁止未授權填值 |

避免已移除的 DataFrame.append、applymap 與 errors='ignore' 轉型模式。
pandas 3.0 的 Copy-on-Write 下使用 `.loc[...] = ...` 或明確建立新欄，不依賴 chained assignment。
