# MiniMax 全雙工即時語音系統

以 Pipecat 作為唯一對話編排核心、LiveKit 作為 WebRTC 媒體層，並以 MiniMax
WebSocket TTS 作為正式聲音輸出的可中斷即時語音系統。

目前狀態：Task 001 至 Task 004 已完成驗收。Task 004 提供供應商無關的 Generation
Guard Core；Legacy LINE OA 打電話功能包仍只作為唯讀參考，正式整合尚未獲准。

## 核心原則

- Pipecat 是唯一流程與狀態編排器。
- LiveKit 只負責雙向媒體傳輸，不疊加 LiveKit Agents 編排。
- STT 與 LLM 經由可替換介面接入。
- 播放、生成與晚到音訊以 generation ID 隔離並可立即取消。
- API key、LiveKit secret、MiniMax Voice ID 均由環境或生產 secret manager 注入。
- 預設不保存音訊，不在 log 記錄秘密或完整 Voice ID。

## 本機開發

需求：Python 3.12 與 [uv](https://docs.astral.sh/uv/)。

```bash
uv sync
uv run ruff check .
uv run mypy
uv run pytest
```

複製 `.env.example` 為 `.env` 後再填入本機秘密；`.env` 已被 Git 忽略。Task 001
不需要任何供應商憑證。

## MiniMax WebSocket Spike

先以環境變數提供 `MINIMAX_API_KEY`、`MINIMAX_MODEL`、`MINIMAX_VOICE_ID` 與
`MINIMAX_OUTPUT_FORMAT`。模型與 Voice ID 必須是帳號實際可用值；不得提交 `.env`。

```bash
# 標準串流、兩次 task_continue、task_finish
uv run python scripts/run_minimax_spike.py \
  --probe-id probe-standard-001 \
  --generation-id generation-standard-001 \
  --overwrite

# 首個音訊 chunk 後關閉 socket，驗證取消替代方案
uv run python scripts/run_minimax_spike.py \
  --probe-id probe-close-001 \
  --generation-id generation-close-001 \
  --close-after-first-audio \
  --output artifacts/minimax-close-probe.mp3 \
  --result-json artifacts/minimax-close-probe.json \
  --report artifacts/minimax-close-probe.md

# 在同一 session 嘗試第二次 task_start，實測是否可重用
uv run python scripts/run_minimax_spike.py \
  --probe-id probe-reuse-001 \
  --generation-id generation-reuse-001-a \
  --reuse-generation-id generation-reuse-001-b \
  --probe-reuse \
  --output artifacts/minimax-reuse-probe.mp3 \
  --result-json artifacts/minimax-reuse-probe.json \
  --report artifacts/minimax-reuse-probe.md
```

加上 `--play` 可透過 `mpv` 邊收邊播。事件 log、JSON 與 Markdown 報告不保存 API
Key、完整 Voice ID 或輸入文字；Voice ID 僅保存 SHA-256 前 12 碼。三種真實探針的
去敏結論已彙整至 `docs/minimax-spike-results.md`；請勿在未授權下重跑付費探針。

## LINE OA 打電話模組整合設計

Legacy 功能包僅是唯讀參考，不是本專案 runtime、submodule 或第二套編排器。整合方向為
LINE OA → LIFF → 版本化 WebSocket → Python Voice Runtime → Pipecat；MiniMax TTS 每個
generation 使用獨立 WebSocket session，LiveKit 僅保留為後續 WebRTC transport。

- 完整串接節點與契約：`docs/line-oa-voice-call-integration-blueprint.md`
- Legacy 模組分類：`docs/legacy-voice-call-audit.md`
- 現況協定盤點：`docs/legacy-websocket-protocol.md`
- 音訊生命週期：`docs/legacy-audio-lifecycle.md`

上述內容是設計與審批依據，不代表已實作正式 LIFF、Pipecat Pipeline、LiveKit 或
MiniMaxTTSService。

## 里程碑

1. Task 001：專案骨架與 CI。
2. Phase 0 / Task 002：MiniMax WebSocket Spike 與真實事件、音訊格式、TTFA 驗證。
3. Task 003：協定模型與真實事件 fixtures。
4. Legacy audit：LINE OA 功能包唯讀盤點與分階段整合藍圖。
5. Task 004：Generation lifecycle、取消登記、晚到資料硬閘門、cleanup 與安全事件。
6. Task 005 之後：須另經人工 milestone 核准；不得自動啟動。

完整需求見 `minimax-duplex-voice-spec-v1.0.md`。
