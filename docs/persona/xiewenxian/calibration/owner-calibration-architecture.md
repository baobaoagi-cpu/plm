# 謝文憲 OWNER_CALIBRATION_SANDBOX 架構

狀態：`MILESTONE_3A_IDENTITY_ISOLATION_IMPLEMENTED`

本文件只定義封閉校準環境的身份與隔離邊界。LINE 回覆、STT、TTS、LIFF、Mem0、
公開部署及正式 Persona Release 均未接線。

## 產品身份

- 名稱：`謝文憲 AI 分身｜本人校準版`
- 固定標示：`目前為本人校準測試版本。內容尚未代表謝文憲老師正式立場。`
- Persona source binding：`xiewenxian-v2-candidate-register-v0.1`
- Persona status：candidate；不是 release persona，也不是本人已確認人格。

## 邊界圖

```text
未來專屬 LINE OA / LIFF
        |
        v
allowlist + role policy -- kill switch -- sandbox notice
        |
        v
xie_wenxian tenant / candidate persona binding
        |
        +-- calibration conversation namespace (尚未接 DB)
        +-- calibration evidence namespace     (尚未接 DB)
        +-- audio/transcript prefixes           (尚未接 storage)
        +-- memory namespace                    (禁止接 Mem0)
```

## 固定身份綁定

| 項目 | 3A 綁定 |
|---|---|
| tenant | `xie_wenxian` |
| persona | `xie_wenxian_owner_calibration_v0_1` |
| persona version source | `xiewenxian-v2-candidate-register-v0.1` |
| memory namespace | `xie_wenxian/calibration` |
| Mem0 user ID reservation | `xie_wenxian/calibration/owner`（3A 未接 Mem0） |
| database tenant | `xie_wenxian` |
| audio prefix | `xie_wenxian/calibration/audio` |
| transcript prefix | `xie_wenxian/calibration/transcripts` |
| LiveKit room namespace | `xie_wenxian/calibration/livekit` |
| prompt cache | `xie_wenxian/calibration/prompt-cache` |
| session state | `xie_wenxian/calibration/session-state` |

## 存取決策

1. Sandbox 預設停用。
2. Kill switch 預設開啟。
3. 未列入 allowlist 的 LINE User ID 一律 `DENIED`。
4. `OWNER` 可互動及提交「本人證據候選」。
5. `GOVERNOR` 可互動及治理，但不能冒充 OWNER 提交本人證據。
6. `TECHNICAL_TESTER` 只能互動及技術測試。
7. 所有輸出必須帶 Sandbox 標示。

程式證據：`src/duplex_voice/calibration/identity.py`。此模組不 import 任何既有 persona、LINE
webhook、memory 或模型 runtime；3A 不會產生任何外部回覆。

## Phase 3B staging proof

Phase 3B 已由人工批准，新增 verified identity assertion → hashed `effective_user_id` 映射、
synthetic-only proof store、候選人格 fail-closed loader、PostgreSQL schema contract 與四個
read-only admin contracts。這些能力沒有連接真實 LINE、DB、Mem0、R2 或 provider。

PostgreSQL migration 的 schema 固定為 `xiewenxian_staging`，所有資料表 forced RLS，並以
tenant／principal／principal kind composite foreign key 防止 Owner Evidence 與 Student Memory
混用。因尚未取得外部 staging DB identity，目前只有 AST parse 與 contract-test 證據。

3B 不會自動授權 3C、3D、Task 005 或 production。
