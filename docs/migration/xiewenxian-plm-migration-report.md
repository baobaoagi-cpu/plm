# 謝文憲 PLM Repository Migration Repair

狀態：`LOCAL_VALIDATION_COMPLETE / GITHUB_ACTIONS_PENDING`

## Canonical ownership

- Canonical repository：`baobaoagi-cpu/plm`
- Migration branch：`codex/xie-wenxian-plm-migration`
- Historical source：`baobaoagi-cpu/holygrail2`
- Source branch：`codex/xie-wenxian-soul-container-v0.1`
- Source SHA：`a1ad3825cf17935622c158795dee019be99bcaaa`
- Legacy reference SHA：`2ae148d46b5d018ae5999ee68f3db6da5cc5566f`

holygrail2 分支只保留為歷史證據；本輪不刪除、不修改、不 force push，也不把它視為
謝文憲系統的正式交付。

## 移植結果

完整逐檔分類、來源 SHA、目標路徑、相依、隔離、測試、敏感度與本人確認需求見
`docs/migration/xiewenxian-plm-migration-inventory.json`，共 31 筆。

### Phase 2

- 46 筆候選與 15 筆 Owner Confirmation Queue 已移入
  `docs/persona/xiewenxian/source/`。
- 46 筆狀態維持 `candidate`；source classification 維持
  `PROJECT_OWNER_APPROVED_ENGINEERING_INTERPRETATION`。
- `owner_quote` 非空數為 0；runtime／production eligibility 均為 false。
- 沒有建立 `OWNER_CONFIRMED`、`RELEASE_APPROVED` 或正式 persona。

### Phase 3A

- 在 `src/duplex_voice/calibration/identity.py` 依 PLM package 重建 tenant identity、
  allowlist、角色權限、Sandbox notice、kill switch、persona version、Mem0 reservation、
  storage／LiveKit／cache／session namespaces 與專屬 secret slots。
- 預設 `enabled=false`、`kill_switch=true`、`sandbox_mode=true`。
- 模組不 import holygrail2、Tracy runtime、LINE、Mem0、LiveKit Agents 或 provider service。

### Legacy LIFF shell

- 只重寫 backend-free 的 Call Shell、Mic Permission、Waveform 與 Dial Tone。
- Shell 預設 `callEnabled=false`，固定顯示本人校準版聲明。
- 未搬 avatar、其他 persona 品牌、BreathingOrb、`useAudio`、`useWebSocket`、LIFF profile
  trust、TypeScript backend、VoicePipeline、MiniMax pool 或 provider code。
- 這是可型別檢查的 UI 外殼，不代表 LINE、LIFF identity、麥克風、WebSocket 或通話已接線。

## V2 安全與歸屬審查

- 檔名：`謝文憲 AI 分身｜靈魂級核心主題提示詞 V2.md`
- Bytes：27,291
- SHA-256：`5585cdde72525432729fc1ce2b15411ecf1e60d7df7b5fb19d785d0a620a817f`
- 高信心 secret pattern：未發現。
- 治理風險：含未經本人逐條確認的個人敘事、典型句型、價值排序與工程推論。
- 決策：`REFERENCE_ONLY`；raw source 保持 untracked 並由 `.gitignore` 阻止誤提交。
- PLM 只提交經治理的候選 register、來源雜湊、衝突／缺口與 confirmation queue。

## 核心架構檢查

- Pipecat 仍是唯一編排核心；未新增其他 orchestrator。
- Generation Guard 原始實作未被繞過或修改。
- MiniMax 仍為 `ONE_SESSION_PER_GENERATION`；未加入 connection pool。
- LiveKit 未自動加入；既有 transport stub 與藍圖狀態不變。
- 沒有正式 LINE OA、STT、TTS、MiniMaxTTSService、Pipecat pipeline、Mem0 或 production。

## Rollback

本輪沒有 DB migration、secret、外部資源或 deployment。回滾範圍限於本 migration branch
新增的 persona governance、calibration policy、UI shell 與文件；holygrail2 歷史分支保持不變。

## 停止點

驗收及 GitHub Actions 通過後，狀態必須停在：

`NEEDS_HUMAN_PLM_MIGRATION_REVIEW`

不得自行開始正式 LINE OA 部署、老師帳號交付、3B/3C/3D、Mem0、公開聲音或 Persona Release。
