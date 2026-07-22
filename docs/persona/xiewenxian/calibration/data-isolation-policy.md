# 謝文憲本人校準版資料隔離政策

狀態：`3A / policy active / integrations not wired`

## 不共用原則

謝文憲校準環境不得與 Tracy／賴婷婷或其他 persona 共用 Persona ID、prompt、Voice ID、
LINE channel、LIFF ID、LiveKit project、memory namespace、DB tenant、object prefix、
conversation、evidence、cache 或 session state。共用程式引擎不等於共用身份或資料。

## 專屬秘密槽位

Repository 只保存槽位名稱，不保存任何值：

- `XIEWENXIAN_CALIBRATION_LINE_CHANNEL_ID`
- `XIEWENXIAN_CALIBRATION_LINE_CHANNEL_SECRET`
- `XIEWENXIAN_CALIBRATION_LINE_CHANNEL_ACCESS_TOKEN`
- `XIEWENXIAN_CALIBRATION_LIFF_ID`
- `XIEWENXIAN_CALIBRATION_MINIMAX_VOICE_ID`
- `XIEWENXIAN_CALIBRATION_LIVEKIT_URL`
- `XIEWENXIAN_CALIBRATION_LIVEKIT_API_KEY`
- `XIEWENXIAN_CALIBRATION_LIVEKIT_API_SECRET`

真實值只能放在未來批准的部署平台 Secret Manager。不得使用通用或其他 persona 的變數
名稱作 fallback，也不得在 log、文件、測試 fixture 或 Git history 顯示值。

## LINE 身份與角色

Allowlist 只從 `XIEWENXIAN_CALIBRATION_LINE_ALLOWLIST_JSON` 讀取，不進 Git。角色只有：

| 角色 | 互動 | 本人證據候選 | 治理 | 技術測試 |
|---|---:|---:|---:|---:|
| OWNER | 是 | 是 | 否 | 否 |
| GOVERNOR | 是 | 否 | 是 | 否 |
| TECHNICAL_TESTER | 是 | 否 | 否 | 是 |
| DENIED／未知 | 否 | 否 | 否 | 否 |

拒絕事件只保留安全稽核所需的最小資料；3A 不建立事件資料表，也不保存真實 User ID。

## 四層資料狀態

- `conversation_log`：一般校準對話，尚未實作儲存。
- `calibration_candidate`：候選修正，尚未實作儲存。
- `owner_evidence`：只有 OWNER 可提交，預設 `OWNER_PROVIDED_UNREVIEWED`。
- `approved_persona_fact`：必須經本人確認及治理批准；3A 禁止寫入。

禁止任何對話自動寫入 Mem0 或正式 persona。資料庫、R2 與 Mem0 在 3A 都是未接線狀態。

## Fail-closed 條件

以下任一成立即不得回覆：Sandbox 未啟用、kill switch 開啟、未知 User ID、角色權限不足、
非 Sandbox mode、秘密槽位未使用專屬前綴，或 namespace 與其他 tenant 重疊。

## 刪除與保存

3A 不收集對話或音訊。3B 只使用 synthetic digest proof；3C 或任何外部資料儲存前必須
先取得 consent version、保存天數、刪除政策與撤回方式。

## Phase 3B synthetic proof 補充

Phase 3B 仍不收集真實對話、身份或音訊。Python proof store 只接受以 `synthetic:` 明確
標示的 bounded content，且只保存 SHA-256 digest。外部 ID 只產生 SHA-256 指紋與穩定
`effective_user_id`；raw ID 不進 store、admin snapshot 或 log。

`migrations/phase3b/` 是尚未執行的 PostgreSQL staging contract，不代表資料保存已獲准。
在 retention、consent、DB identity 與 rollback window 經人工確認前，不得套用到外部 DB。
