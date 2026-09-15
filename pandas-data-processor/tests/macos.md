# 真實 macOS 驗證

目前尚未取得真實 macOS 執行結果。Windows 測試、跨平台原始碼檢查與 wheel 標籤不能取代 Mac 實測。

將完整原始碼套件放到你的 Mac，在套件目錄執行：

```bash
python3 scripts/verify_macos.py
```

需要該 Mac 上的 Python 3.11 以上及套件下載網路；若 python3 是舊版，使用已安裝的新版本，例如 `python3.12 scripts/verify_macos.py`。
Apple Silicon 建議使用原生 arm64 Python；報告會記錄目前程序架構，x86_64 結果不能冒稱驗證過 arm64。

此指令會：

1. 確認正在 macOS 執行；在 Windows/Linux 上拒絕，避免產生誤標的 Mac 成功紀錄。
2. 在新的 `.macos-test-runs/run-*/environment` 建立隔離 Python 環境並安裝 CLI 與測試依賴。
3. 執行 help、doctor 及完整 pytest，包含安裝後指令、中文／空白檔名、CSV/XLSX、來源追蹤、異常與總額核對。
4. 另外保留 CSV/XLSX 清理結果、回讀驗證、總額核對及預期失敗的 Exceptions 工作流。
5. 留下 `report.json`、`pytest.xml` 及各步驟 `.log`。安裝或測試失敗會記錄錯誤並以非零退出碼停止。

現有 90 項測試中，Windows `.cmd` 專用測試在 Mac 會 skip。以實際產生的 report/pytest.xml 為準，不預填成功結果。
這是功能與安裝相容性驗證，不是大量資料容量壓測；不能由一次通過推論所有 Mac、OS/Python 版本與任意資料量都穩定。

請把該次執行的 `report.json` 與 `.log`／`pytest.xml` 回傳給協助排錯的 AI。
不必分享 `environment/`；它只是這次測試用的 Python 與依賴。`.macos-test-runs/` 不必打包交付。
