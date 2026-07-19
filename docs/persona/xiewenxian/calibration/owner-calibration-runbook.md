# 謝文憲 OWNER_CALIBRATION_SANDBOX Runbook

適用範圍：Milestone 3A Identity Isolation。這不是部署手冊，也不授權啟動外部服務。

## 預設安全狀態

```text
XIEWENXIAN_CALIBRATION_ENABLED=false
XIEWENXIAN_CALIBRATION_KILL_SWITCH=true
XIEWENXIAN_CALIBRATION_SANDBOX_MODE=true
```

Allowlist、secret 與 Voice ID 不得寫入 repository。檢查環境時只輸出 `present=true/false`，
不得輸出值、末碼或 Authorization header。

## 3A 離線驗證

在 `backend/` 執行：

```text
uv run ruff check .
uv run mypy
uv run pytest -q -p no:cacheprovider
```

完整測試需由 test runner 或 CI 在 process scope 注入固定假值 `test-key`，只用來通過既有
module import guard；不得使用真實 Anthropic key，也不得對外呼叫模型。

驗證內容：namespace 不重疊、秘密槽位專屬、未知 User ID 拒絕、OWNER/GOVERNOR 權限
不同、預設 fail closed、kill switch 阻止回覆、Sandbox 標示不可移除。

## 未來配置前置（3A 不執行）

1. 建立專屬 LINE OA、LIFF、LiveKit project、DB tenant 與 object prefix。
2. 在 Secret Manager 建立本文件列出的專屬槽位，不使用其他 persona 的 secret。
3. 將 OWNER、GOVERNOR、TECHNICAL_TESTER 的 LINE User ID 寫入部署環境 allowlist。
4. 完成本人 consent checklist 與 Voice 授權紀錄。
5. 先保持 kill switch 開啟，再由未來里程碑做非 production smoke test。

## 緊急停止

1. 設定 `XIEWENXIAN_CALIBRATION_KILL_SWITCH=true`。
2. 若 LINE 已在後續里程碑接線，停用 webhook 並撤銷／輪替專屬 channel token。
3. 若 LIFF 已接線，停用入口並撤銷專屬 LiveKit credentials。
4. 禁止 fallback 到其他 persona、Voice ID、LINE channel 或 memory namespace。
5. 記錄事件時間、影響範圍與處置，不記錄 secret 或多餘個資。
6. 只有 GOVERNOR 完成事件審查後，才可另案解除 kill switch。

## 回滾

3A 回滾只需停止引用 `owner_calibration.py`；目前沒有 DB migration、外部資源或 runtime
接線。刪除政策與外部資源回收必須在未來相應里程碑另行驗證。

## 停止點

Migration Repair 完成後固定停在 `NEEDS_HUMAN_PLM_MIGRATION_REVIEW`，不得自動開始 3B。
