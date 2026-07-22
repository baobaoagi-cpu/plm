# 謝文憲核心主題提示詞 V2 · Source Registration v0.1

## Source identity

| Field | Value |
|---|---|
| Source ID | `xww-core-topic-prompt-v2` |
| Title | `謝文憲 AI 分身｜靈魂級核心主題提示詞 V2` |
| Original custody | PLM maintainer local workspace；raw source 維持 untracked |
| Bytes | `27291` |
| SHA-256 | `5585cdde72525432729fc1ce2b15411ecf1e60d7df7b5fb19d785d0a620a817f` |
| Registered at | `2026-07-19T20:52:32+08:00` |
| Custody | Raw source registered by hash；canonical PLM 只提交治理衍生物，不提交母稿全文 |

## Governance classification

`PROJECT_OWNER_APPROVED_ENGINEERING_INTERPRETATION`

專案治理方核准此文件作為 Persona Core、Method、Style、Safety 與 Conversation Policy
候選母稿，並核准 Phase 2 candidate classification、來源映射、衝突清單、離線 Harness 與
golden-case 設計。

這項核准不等於：

- `OWNER_CONFIRMED_EVIDENCE`
- 謝文憲老師本人逐條確認
- 本人逐字原話
- production-ready persona
- 對 Mem0、LINE OA、聲音、正式資料或 production infrastructure 的連線授權

## Evidence tiers

| Tier | Meaning | V2 current state |
|---|---|---|
| `E0_UNMAPPED` | 只有母稿敘述，尚無公開來源映射 | 部分內容 |
| `E1_PUBLIC_SOURCE_MAPPED` | 已連回公開來源、時間或頁碼，權利狀態已記錄 | 尚無 |
| `E2_PROJECT_OWNER_APPROVED_INTERPRETATION` | 專案治理方核准作為工程候選 | **目前** |
| `E3_OWNER_CONFIRMED` | 謝老師本人或正式授權代表確認 | 尚無 |
| `E4_PUBLISHED` | 經安全、測試與發布流程正式生效 | 禁止／尚無 |

候選不得把 E2 顯示成 E3。典型句型若沒有逐字來源，`owner_quote` 必須保持空白。

## Source handling decision

Migration Repair 已確認原始檔未包含高信心秘密，但其中仍有未經本人確認的個人敘事、
典型句型與工程推論。安全與歸屬審查因此判定為 `REFERENCE_ONLY`：PLM 保存來源標題、
大小、雜湊、分類及衍生候選，raw file 由 `.gitignore` 防止誤提交。未來若人工另行核准
母稿全文入庫，必須以相同 hash 驗證並另記 custody 與公開權利變更。
