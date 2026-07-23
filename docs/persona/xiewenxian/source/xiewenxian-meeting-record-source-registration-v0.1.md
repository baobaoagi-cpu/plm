# 謝文憲 AI 分身工作會議暨人生故事訪談 · Source Registration v0.1

## Source identity

| Field | Value |
|---|---|
| Source ID | `xww-meeting-record-owner-interview-157-158` |
| Registered title | `會議記錄_憲哥AI分身.docx` |
| Source kind | `AUTOMATED_TRANSCRIPT_DERIVED_MEETING_SUMMARY` |
| Underlying media named by the record | `錄製 (157).mp3`、`錄製 (158).mp3`；未納入本次 custody |
| Raw source custody | PLM maintainer local workspace；raw DOCX 維持 untracked |
| Bytes | `15762` |
| SHA-256 | `ED2215566A028E4AC31B1E77F410BEF961F5423A122DEDD270C3664FB796209C` |
| Registered at | `2026-07-23` |
| Render review | `NOT_COMPLETED_SOFFICE_UNAVAILABLE`；已完成 DOCX 結構與全文抽取 |

## Governance classification

```text
PROJECT_OWNER_AUTHORIZED_SOURCE_REGISTRATION
MEETING_SUMMARY_ATTRIBUTED_CLAIMS_PENDING_PRIMARY_MEDIA_VERIFICATION
NOT_OWNER_CONFIRMED_EVIDENCE
NOT_RUNTIME_ELIGIBLE
NOT_PRODUCTION_ELIGIBLE
```

本次人工授權允許將會議記錄登錄、分類並建立追溯關係。它不代表謝文憲老師已逐項確認
摘要內容，也不代表摘要中的引號、數字、故事、方法名稱或價值排序是可直接引用的本人逐字原話。

## Provenance limitation

文件自述由兩段、合計約 63 分鐘的多人錄音經自動轉錄後整理而成，並明載姓名、年代、
公司名、金額與專有名詞可能有辨識誤差。現有 DOCX 不是逐字稿，沒有逐句時間碼，也沒有
逐段 speaker label。底層錄音、原始逐字稿、轉錄模型、人工校訂紀錄、受訪同意書與素材
權利文件均未在本次 source package 中提供。

因此本來源只可產生以下兩種衍生物：

1. `MEETING_DECISION_OR_PRODUCT_REQUIREMENT`：由文件明確列為決議或 Action Item，仍需由專案治理方確認執行範圍。
2. `OWNER_ATTRIBUTED_SUMMARY_PENDING_VERIFICATION`：文件歸因給謝老師的內容，只能作為尋找原始錄音時間碼與本人確認的線索。

禁止由摘要中的引號直接填入 `owner_quote`。只有取得原始錄音或經本人核准的逐字稿、確認
speaker 與時間碼、完成權利及隱私審查後，才可另案考慮升級證據。

## Evidence handling

| Evidence state | Meaning | This source |
|---|---|---|
| `E0_SUMMARY_UNVERIFIED` | 自動轉錄衍生摘要，無逐句 speaker/timecode 驗證 | **目前** |
| `E1_PRIMARY_MEDIA_MAPPED` | 已對照原始錄音、speaker、時間碼與精確措辭 | 尚無 |
| `E2_PROJECT_OWNER_APPROVED_INTERPRETATION` | 專案治理方核准成為工程候選 | 需逐項另審；不得由本次登錄自動取得 |
| `E3_OWNER_CONFIRMED` | 本人或正式授權代表確認 | 尚無 |
| `E4_PUBLISHED` | 經安全、測試與發布流程正式生效 | 禁止／尚無 |

## Content classes

- `OWNER_ATTRIBUTED_SUMMARY_PENDING_VERIFICATION`：價值排序、職涯轉場、決策方法、人生故事、家庭觀與典型句型。
- `TEAM_STATEMENT_OR_SUMMARY`：思想與聲音分流、訪談萃取方式、素材蒐集作法。
- `MEETING_DECISION`：思想／聲音分流、增量錄製、品牌視覺、正式錄音安排。
- `PRODUCT_REQUIREMENT_OR_ACTION_ITEM`：題目設計、錄製、公開素材蒐集、品牌與錄音安排。
- `EDITORIAL_INFERENCE`：與會者身份、專案角色、內容概括及整理者對「核心價值」的詮釋。

## Privacy and rights controls

此來源涉及本人與家屬的健康、家庭關係、職涯、財務／投資、公益、年齡與人生事件。衍生
治理資產只保存最低必要摘要與風險標籤，不保存家屬姓名、可識別細節、完整引語、逐字稿
或原始聲音。公開文章、演講、廣播、說書與 Podcast 並不因「公開可取得」而自動取得訓練、
聲音複製、全文爬取或衍生使用權；每一來源仍需權利、用途、保存與撤回審查。

## Source handling decision

```text
RAW_DOCX = LOCAL_UNTRACKED_REFERENCE_ONLY
RAW_AUDIO = NOT_ACCESSED
RAW_TRANSCRIPT = NOT_PROVIDED
DERIVED_GOVERNANCE_RECORDS = COMMITTABLE_AFTER_PRIVACY_REVIEW
OWNER_QUOTE_POPULATION = FORBIDDEN_IN_THIS_MISSION
```

本次不建立 release persona，不修改 runtime，不連接 Mem0、LINE、聲音服務、資料庫或任何
production infrastructure，也不引入 Tracy 的人格、記憶、聲音、資料或校準資產。
