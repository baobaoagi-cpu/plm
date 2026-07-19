# MiniMax 全雙工即時語音系統｜開發規格書

**文件版本：** v1.0  
**文件日期：** 2026-07-19  
**文件狀態：** Ready for Codex Implementation  
**主要技術：** Python、Pipecat、LiveKit WebRTC、MiniMax WebSocket TTS  
**目標語言：** 繁體中文優先  
**專案代號：** `minimax-duplex-voice`

---

## 0. Codex 執行指令

你是本專案的首席後端與即時音訊工程師。請嚴格依照本規格書開發，不要擅自更換核心架構。

### 核心架構不可更動

1. **Pipecat 是唯一對話編排核心。**
2. **LiveKit 只作為 WebRTC 媒體傳輸層，第一版不使用 LiveKit Agents 作為第二套編排器。**
3. **MiniMax WebSocket TTS 是唯一正式聲音輸出引擎。**
4. STT 與 LLM 必須透過介面抽象，可替換供應商。
5. 所有音訊播放必須可被立即中斷。
6. 使用者在 AI 說話時，麥克風上行音訊不得停止。
7. 不得把 API Key、Voice ID 或 Token 寫死在程式碼中。
8. 先完成可量測、可中斷、可測試的 MVP，再加入 backchannel 與進階話語權判斷。
9. 每完成一個里程碑，必須執行測試、更新 `README.md`、`CHANGELOG.md` 與驗收記錄。
10. 不確定的 MiniMax API 行為必須以獨立 Spike 測試驗證，不得猜測。

---

# 1. 專案目的

建立一套可與 MiniMax Voice ID 整合的模組化即時語音系統，使 AI 能夠：

- 持續聆聽使用者。
- 串流辨識使用者語音。
- 串流生成 LLM 回答。
- 串流送入 MiniMax WebSocket TTS。
- 收到 MiniMax 音訊後立即播放。
- AI 說話期間仍持續收音。
- 使用者真正打斷時立即停止 AI。
- 保留使用者打斷內容，形成下一輪輸入。
- 區分背景噪音、短暫附和與真正打斷。
- 對所有延遲節點進行量測。
- 未來能加入語氣靈、人格、記憶、RAG、工具調用與微回合回應。

本系統不是第一階段便追求「單一模型原生 speech-to-speech 全雙工」，而是先完成工程上穩定、可控制、可觀測的：

> **雙向持續音訊＋串流級聯管線＋可打斷式雙工＋可演進的話語權控制器。**

---

# 2. 非目標

MVP 階段不處理以下項目：

- 不訓練自有 STT、LLM 或 TTS 模型。
- 不自行開發 WebRTC SFU。
- 不實作電話 SIP/PSTN。
- 不實作多人會議。
- 不做完整管理後台。
- 不做支付、帳務或多租戶計費。
- 不做原生手機 App。
- 不承諾 AI 與使用者可長時間同時朗讀不同完整句子而互不干擾。
- 不在第一版實作 Moshi、PersonaPlex 或其他原生語音模型。
- 不在第一版疊加 LiveKit Agents。
- 不以「等待整句文字完成後才呼叫 TTS」作為正式方案。

---

# 3. 架構決策紀錄

## ADR-001：Pipecat 是唯一編排核心

Pipecat 的 Pipeline、FrameProcessor 與 Frame 模型適合處理音訊、文字、轉錄、控制事件與中斷事件。自訂 MiniMax TTS 應實作成 Pipecat Service 或 FrameProcessor，避免在框架外建立不可觀測的旁路。

Pipecat 官方文件說明，Pipeline 由 Frames 與 FrameProcessors 組成，且可建立自訂 FrameProcessor；其使用者語音回合開始策略可在啟用 interruption 時停止機器人說話、清除待播音訊與文字，並準備接收新輸入。  
參考：Pipecat Pipeline、Custom FrameProcessor、Speech Input 官方文件。  
https://docs.pipecat.ai/pipecat/learn/pipeline  
https://docs.pipecat.ai/pipecat/fundamentals/custom-frame-processor  
https://docs.pipecat.ai/pipecat/learn/speech-input

## ADR-002：LiveKit 只負責媒體層

LiveKit 提供基於 WebRTC 的即時音訊、視訊與資料傳輸能力。第一版透過 Pipecat 的 LiveKit transport 或正式相容介面接入，不另外使用 LiveKit Agents 的 AgentSession 作為第二套流程控制器。

原因：

- 避免 Pipecat 與 LiveKit Agents 同時管理 VAD、turn detection、TTS queue 與 interruption。
- 維持單一狀態來源。
- 保留 LiveKit 在 WebRTC、房間、音訊上下行、網路調適與未來 SIP 接入方面的優勢。
- 降低取消事件跨兩套 runtime 傳播的複雜度。

LiveKit 是開源 WebRTC 即時影音資料平台；Pipecat 官方 repository 亦提供 LiveKit transport 範例。  
參考：  
https://docs.livekit.io/intro/overview/  
https://github.com/pipecat-ai/pipecat/blob/main/examples/transports/transports-livekit.py

## ADR-003：MiniMax WebSocket TTS 是唯一聲音輸出

MiniMax 官方 T2A WebSocket API 支援透過持久連線執行同步文字轉語音，並以音訊資料事件串流回傳，可邊收邊播。正式實作必須封裝為 `MiniMaxTTSService`。

參考：  
https://platform.minimax.io/docs/api-reference/speech-t2a-websocket

## ADR-004：打斷採用「本地立即止播＋上游取消／廢棄」

無論 MiniMax 是否提供可用的即時取消事件，系統都必須先保證：

1. 本地播放 queue 立即清空。
2. 後續 MiniMax 音訊 chunk 被 generation ID 擋掉。
3. LLM 串流停止或其後續輸出被丟棄。
4. MiniMax 任務被取消、關閉或標記廢棄。
5. 新一輪對話不受到舊音訊污染。

因此，「聽感上的停止」不能依賴遠端供應商回應。

## ADR-005：以 Generation ID 防止幽靈音訊

每一輪回答建立唯一 `generation_id`。所有 LLM 文字片段、TTS 任務、音訊 chunk 與播放 queue item 均攜帶該 ID。

一旦打斷：

- 將該 ID 標記為 cancelled。
- 任一晚到的文字或音訊立即丟棄。
- 新回答使用新 ID。

此機制必須作為系統不變量。

---

# 4. 系統分層

```text
┌─────────────────────────────────────────────────────┐
│ Web Client                                           │
│ 麥克風、喇叭、LiveKit Client、狀態顯示、延遲顯示      │
└───────────────────────┬─────────────────────────────┘
                        │ WebRTC
┌───────────────────────▼─────────────────────────────┐
│ LiveKit Media Layer                                  │
│ Room、上行音軌、下行音軌、AEC、jitter、網路傳輸       │
└───────────────────────┬─────────────────────────────┘
                        │ PCM Audio Frames
┌───────────────────────▼─────────────────────────────┐
│ Pipecat Runtime                                      │
│ Pipeline、Frames、VAD、Turn Detection、Interruption   │
│ Dialogue Floor Controller、Metrics、Session State    │
└──────────────┬──────────────────────┬───────────────┘
               │                      │
       ┌───────▼────────┐     ┌──────▼───────────┐
       │ Streaming STT   │     │ Streaming LLM     │
       │ 可替換 Provider │     │ 可替換 Provider   │
       └───────┬────────┘     └──────┬───────────┘
               │                     │ text deltas
               └──────────┬──────────┘
                          ▼
                Semantic Text Chunker
                          │
                          ▼
               MiniMax WebSocket TTS
                          │ audio chunks
                          ▼
              Interruptible Audio Output
                          │
                          ▼
                 LiveKit Downstream Track
```

---

# 5. 關鍵角色與責任

## 5.1 Pipecat

負責：

- Pipeline 執行。
- Frame 流動。
- STT、LLM、TTS 協調。
- 使用者回合開始與結束。
- 打斷事件。
- generation cancellation。
- 文字切塊。
- 音訊 queue 控制。
- 對話狀態。
- 指標打點。
- 錯誤復原。
- 未來 backchannel 與話語權策略。

不負責：

- WebRTC SFU。
- 聲音合成模型本身。
- LLM 推理本身。

## 5.2 LiveKit

負責：

- 房間與參與者。
- 使用者上行音訊。
- AI 下行音訊。
- WebRTC 連線。
- 客戶端 AEC 能力與音訊裝置整合。
- jitter buffer、網路調適與封包處理。
- 未來 SIP 或電話橋接。

不負責：

- 對話狀態機。
- LLM。
- MiniMax TTS 任務。
- generation cancellation 的業務邏輯。

## 5.3 MiniMax TTS

負責：

- 指定 Voice ID。
- 文字到語音。
- 音訊串流輸出。
- 聲線、語速、音量、音高及供應商支援的語音參數。

不負責：

- 判斷誰擁有話語權。
- 判斷使用者是否打斷。
- 對話記憶。
- 播放 queue。
- 本地立即止播。

## 5.4 LLM

負責：

- 理解轉錄文字。
- 推理。
- 回答。
- 工具調用。
- 未來人格、記憶與 RAG。

LLM 必須以串流文字輸出，並接受取消。

---

# 6. MVP 使用者故事

## US-001：開始對話

使用者開啟頁面、允許麥克風權限、進入 LiveKit 房間並開始說話。系統顯示：

- 連線狀態。
- 麥克風狀態。
- AI 狀態。
- 即時轉錄。
- 最終轉錄。
- LLM 文字。
- TTS 播放狀態。
- 基本延遲指標。

## US-002：正常問答

使用者說完一句話後，系統完成：

1. STT final。
2. LLM 首 token。
3. 語意文字切塊。
4. MiniMax TTS 首個音訊 chunk。
5. AI 開始播放。
6. 完成回答。

## US-003：AI 說話時持續收音

AI 播放 MiniMax 聲音時，使用者麥克風仍持續上行；系統仍可收到 VAD 與 STT partial。

## US-004：使用者打斷

使用者在 AI 回答中說「等一下」，系統必須：

- 在目標延遲內停止目前播放。
- 取消或廢棄當前生成。
- 保留「等一下」及後續語句。
- 將新的完整輸入交給 LLM。
- 不得播放舊回答晚到的音訊。

## US-005：短暫附和

使用者在 AI 說話時說「嗯」、「對」或極短聲音，MVP 可以先採簡單規則：

- 少於門檻且屬於 allowlist 的附和語，不打斷 AI。
- 其他重疊語音先視為打斷。

進階版再加入語意／聲學 interruption classifier。

## US-006：供應商故障

MiniMax WebSocket 失敗時：

- 不得造成 Pipeline 卡死。
- 顯示錯誤。
- 記錄 trace ID、錯誤碼、generation ID。
- 可依設定重試一次。
- 重試失敗後結束該輪並回到 LISTENING。
- MVP 不自動切換另一個正式聲音供應商，避免聲線突然改變。

---

# 7. Dialogue Floor Controller

## 7.1 狀態

```python
class FloorState(str, Enum):
    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    LISTENING = "listening"
    USER_SPEAKING = "user_speaking"
    USER_TURN_ENDING = "user_turn_ending"
    THINKING = "thinking"
    TTS_BUFFERING = "tts_buffering"
    BOT_SPEAKING = "bot_speaking"
    USER_OVERLAP = "user_overlap"
    INTERRUPTING = "interrupting"
    CANCELLED = "cancelled"
    RECOVERING = "recovering"
    ERROR = "error"
```

第二階段可加入：

```python
BACKCHANNELING
YIELDING
RESUMING
```

## 7.2 主要狀態轉移

```text
DISCONNECTED → CONNECTING → LISTENING

LISTENING
  └─ user speech start → USER_SPEAKING

USER_SPEAKING
  └─ user turn end → THINKING

THINKING
  ├─ first speakable text chunk → TTS_BUFFERING
  ├─ new user speech → INTERRUPTING
  └─ error → RECOVERING / ERROR

TTS_BUFFERING
  ├─ first audio chunk → BOT_SPEAKING
  ├─ new user speech → INTERRUPTING
  └─ TTS error → RECOVERING

BOT_SPEAKING
  ├─ bot finished → LISTENING
  ├─ short backchannel → BOT_SPEAKING
  └─ intentional interruption → USER_OVERLAP → INTERRUPTING

INTERRUPTING
  ├─ local playback cleared
  ├─ current generation cancelled
  ├─ user continues speaking → USER_SPEAKING
  └─ false positive → LISTENING or BOT_SPEAKING（第二階段）
```

## 7.3 不變量

1. 任一時間只能有一個 active generation。
2. 所有輸出音訊必須帶 generation ID。
3. cancelled generation 的音訊不得進入播放層。
4. `BOT_SPEAKING` 期間輸入音訊不得停止。
5. 所有狀態轉移均須產生結構化事件。
6. 任一遠端 API 失敗不得永久鎖住狀態。
7. interruption 發生後，必須先完成本地止播，不等待供應商 ACK。

---

# 8. MiniMax TTS Adapter 規格

## 8.1 類別

建議名稱：

```python
class MiniMaxTTSService(TTSService):
    ...
```

若目前 Pipecat 版本的抽象類別介面不同，Codex 應依已安裝版本的官方型別定義調整，但外部行為不可改變。

## 8.2 建構參數

```python
MiniMaxTTSService(
    api_key: str,
    model: str,
    voice_id: str,
    sample_rate: int,
    output_format: str,
    speed: float,
    volume: float,
    pitch: int,
    language_boost: str | None,
    connect_timeout_s: float,
    receive_timeout_s: float,
    max_retries: int,
)
```

預設建議：

```text
model = 以帳號當下可用且支援 WebSocket 的 speech-2.x 模型為準
sample_rate = 24000 或經 Spike 驗證後採 LiveKit/Pipecat 最少轉碼者
output_format = PCM 優先；若 API 僅適合其他格式，需加入單一解碼層
speed = 1.0
volume = 1.0
pitch = 0
language_boost = Chinese / auto，依官方參數實測
```

不得在規格階段硬寫不存在或未驗證的模型名稱與參數值。啟動時需執行設定驗證。

## 8.3 生命週期

```text
connect()
start_generation(generation_id, voice_config)
push_text(generation_id, text_chunk)
finish_input(generation_id)
cancel_generation(generation_id, reason)
close()
```

## 8.4 事件

Adapter 必須產生：

```python
TTSConnectionStarted
TTSConnectionReady
TTSRequestStarted
TTSFirstAudioReceived
TTSAudioChunkReceived
TTSInputFinished
TTSRequestFinished
TTSRequestCancelled
TTSRequestFailed
TTSConnectionClosed
```

每個事件至少包含：

```json
{
  "session_id": "...",
  "generation_id": "...",
  "provider": "minimax",
  "model": "...",
  "voice_id_hash": "...",
  "timestamp_monotonic_ms": 0,
  "trace_id": "...",
  "metadata": {}
}
```

Voice ID 只記錄 hash 或末四碼，不得完整寫入一般 log。

## 8.5 WebSocket 行為

1. 使用 TLS WebSocket。
2. Authorization 由環境變數取得。
3. 驗證 session started/ready 事件後才送文字。
4. 支援在同一生成任務內依序送入經切塊的文字。
5. 音訊 chunk 一到便轉成 Pipecat audio frame。
6. 不等待完整回答。
7. 收到 provider error 時立即終止該 generation。
8. WebSocket close 必須是 idempotent。
9. 同一個 service instance 是否重用連線，需由 Spike 決定：
   - 若官方 session 一次只允許單一任務，採「每 generation 一個 session」。
   - 若可安全重用且重用明顯降低 TTFA，建立受控 connection pool。
10. 不得讓兩個 generation 在同一個不支援 multiplex 的 session 中交錯。

## 8.6 取消策略

取消必須分為四層：

```text
A. 標記 generation cancelled
B. 清空本地待播 queue
C. 停止接受該 generation 的新文字與音訊
D. 關閉、取消或廢棄 MiniMax 任務
```

若 MiniMax API 沒有已驗證的即時 cancel：

- 立即關閉該任務的 WebSocket，或將它放入 drain-and-discard。
- 晚到 chunk 依 generation ID 丟棄。
- 不等待 `task_finish` 才停止本地播放。
- 新 generation 必須可獨立開始。

## 8.7 背壓

設定最大緩衝：

```text
MAX_PENDING_TEXT_CHARS
MAX_PENDING_AUDIO_MS
MAX_UNPLAYED_AUDIO_MS
```

若 MiniMax 產生速度快於播放速度：

- 允許有限 queue。
- 超過門檻時停止送新文字。
- 不可無限累積記憶體。
- 需發出 `tts_backpressure` 指標。

---

# 9. Semantic Text Chunker

## 9.1 目的

避免將 LLM 每個 token 直接送入 TTS，也避免等待完整段落。

## 9.2 規則

優先切點：

1. `。！？`
2. `；：`
3. `，、`
4. 語意短語邊界
5. 超過最大字數時強制切分

預設建議：

```python
min_chars = 6
preferred_chars = 16
max_chars = 32
max_wait_ms = 250
```

以上值必須透過實測調整，不視為永久常數。

## 9.3 行為

- 少於 `min_chars` 且未遇強切點：暫存。
- 遇句末標點：立即輸出。
- 達 `preferred_chars` 且有弱切點：輸出。
- 達 `max_chars`：在最近可接受邊界切分。
- 超過 `max_wait_ms` 且已有可說內容：輸出。
- 不得重複輸出文字。
- interruption 時清空未送出的舊 generation 文字。
- 工具調用 JSON、Markdown code block、URL 等不得直接朗讀，需先正規化。

## 9.4 中文正規化

需建立：

```python
normalize_for_speech(text: str) -> str
```

處理：

- Markdown 標記。
- 多餘空白。
- 表情符號策略。
- 數字與日期。
- 英文字母縮寫。
- URL。
- 程式碼。
- 特殊符號。
- 不應朗讀的引用標記。

MVP 先採保守規則；不要自行把所有數字轉成中文，以免語意錯誤。

---

# 10. Interruption Detector

## 10.1 MVP 判斷

觸發候選：

- AI 為 `TTS_BUFFERING` 或 `BOT_SPEAKING`。
- 上行 VAD 判定語音開始。
- 持續超過 `min_overlap_ms`。
- 音量或 VAD confidence 達門檻。

預設：

```text
min_overlap_ms = 180
confirmation_window_ms = 300
```

## 10.2 Backchannel allowlist

初始繁中：

```text
嗯
恩
喔
哦
對
對啊
好
了解
是
是喔
```

只有在符合所有條件時不打斷：

- 最終轉錄字數極短。
- 無命令詞。
- 無否定詞。
- 無「等一下」、「不是」、「停」、「先等等」等高優先詞。
- 持續時間低於門檻。
- 後續沒有延伸語句。

## 10.3 高優先打斷詞

```text
等一下
等等
停
先停
不是
不對
你先聽我說
先不要
換一個
重來
```

只要 STT partial 明確命中，立即打斷，不必等待 final transcript。

## 10.4 第二階段

加入：

- Acoustic interruption classifier。
- 語意 interruption classifier。
- LiveKit 或 Pipecat 可用的進階 interruption prediction。
- backchannel 與真正 barge-in 分類。
- false interruption recovery。

Pipecat 官方亦有可區分 genuine interruption 與 backchannel 的相關整合能力可供後續評估；正式採用前需驗證授權、成本與語言效果。  
參考：https://docs.pipecat.ai/pipecat/features/krisp-viva

---

# 11. STT 介面

```python
class StreamingSTT(Protocol):
    async def connect(self) -> None: ...
    async def push_audio(self, frame: AudioFrame) -> None: ...
    async def events(self) -> AsyncIterator[STTEvent]: ...
    async def close(self) -> None: ...
```

事件：

```python
SpeechStarted
PartialTranscript
FinalTranscript
SpeechEnded
STTError
```

要求：

- 支援串流 partial。
- 支援繁體中文。
- 每個事件有 monotonic timestamp。
- 不因 AI 播放而停止。
- 能與 AEC 後的麥克風音訊配合。
- 對 partial transcript 做 revision，而不是把每次 partial 重複附加。
- 可替換 provider。

---

# 12. LLM 介面

```python
class StreamingLLM(Protocol):
    async def generate(
        self,
        messages: list[Message],
        generation_id: str,
        cancel_token: CancelToken,
    ) -> AsyncIterator[LLMEvent]: ...
```

事件：

```python
LLMRequestStarted
LLMFirstToken
LLMTextDelta
LLMToolCall
LLMCompleted
LLMCancelled
LLMFailed
```

要求：

- 串流。
- 可取消。
- cancellation 後不得繼續送入 Chunker。
- 支援 system prompt。
- 支援未來工具調用。
- 回答文字與語音用文字可分離：
  - `display_text`
  - `speak_text`

---

# 13. Session State

```python
@dataclass
class VoiceSessionState:
    session_id: str
    room_name: str
    participant_id: str | None
    floor_state: FloorState
    active_generation_id: str | None
    cancelled_generation_ids: set[str]
    user_is_speaking: bool
    bot_is_speaking: bool
    current_partial_transcript: str
    current_final_transcript: str
    pending_text_chars: int
    pending_audio_ms: int
    started_at_monotonic: float
```

要求：

- 每個 LiveKit room participant 對應獨立 session。
- 不使用跨 session 的可變 global state。
- session 結束時取消所有 task、關閉 WebSocket、清空 queue。
- 所有 cleanup 可重複執行。

---

# 14. 建議專案目錄

```text
minimax-duplex-voice/
├─ README.md
├─ CHANGELOG.md
├─ pyproject.toml
├─ uv.lock
├─ .env.example
├─ .gitignore
├─ docker/
│  ├─ Dockerfile
│  └─ docker-compose.yml
├─ docs/
│  ├─ architecture.md
│  ├─ state-machine.md
│  ├─ minimax-spike-results.md
│  ├─ latency-budget.md
│  ├─ operations.md
│  └─ acceptance-record.md
├─ src/
│  └─ duplex_voice/
│     ├─ __init__.py
│     ├─ main.py
│     ├─ config.py
│     ├─ logging.py
│     ├─ app/
│     │  ├─ session.py
│     │  ├─ pipeline_factory.py
│     │  └─ lifecycle.py
│     ├─ transports/
│     │  └─ livekit_transport.py
│     ├─ stt/
│     │  ├─ base.py
│     │  └─ provider.py
│     ├─ llm/
│     │  ├─ base.py
│     │  └─ provider.py
│     ├─ tts/
│     │  ├─ minimax_service.py
│     │  ├─ minimax_protocol.py
│     │  ├─ audio_decoder.py
│     │  └─ generation_guard.py
│     ├─ dialogue/
│     │  ├─ floor_controller.py
│     │  ├─ state.py
│     │  ├─ interruption.py
│     │  ├─ backchannel.py
│     │  └─ events.py
│     ├─ text/
│     │  ├─ chunker.py
│     │  └─ normalization.py
│     ├─ audio/
│     │  ├─ queue.py
│     │  ├─ formats.py
│     │  └─ timing.py
│     ├─ observability/
│     │  ├─ metrics.py
│     │  ├─ tracing.py
│     │  └─ event_log.py
│     └─ api/
│        ├─ health.py
│        └─ debug.py
├─ web/
│  ├─ package.json
│  ├─ src/
│  │  ├─ app/
│  │  ├─ components/
│  │  └─ lib/livekit.ts
│  └─ ...
├─ tests/
│  ├─ unit/
│  │  ├─ test_chunker.py
│  │  ├─ test_floor_controller.py
│  │  ├─ test_generation_guard.py
│  │  ├─ test_interruption.py
│  │  └─ test_minimax_protocol.py
│  ├─ integration/
│  │  ├─ test_minimax_websocket_fake.py
│  │  ├─ test_pipeline_interruption.py
│  │  └─ test_livekit_loopback.py
│  ├─ contract/
│  │  └─ test_minimax_contract.py
│  └─ fixtures/
│     ├─ audio/
│     └─ minimax_events/
└─ scripts/
   ├─ run_minimax_spike.py
   ├─ run_latency_benchmark.py
   └─ simulate_interruption.py
```

---

# 15. 環境變數

`.env.example`：

```bash
APP_ENV=development
LOG_LEVEL=INFO

LIVEKIT_URL=
LIVEKIT_API_KEY=
LIVEKIT_API_SECRET=

MINIMAX_API_KEY=
MINIMAX_MODEL=
MINIMAX_VOICE_ID=
MINIMAX_OUTPUT_FORMAT=
MINIMAX_SAMPLE_RATE=24000
MINIMAX_SPEED=1.0
MINIMAX_VOLUME=1.0
MINIMAX_PITCH=0
MINIMAX_LANGUAGE_BOOST=

STT_PROVIDER=
STT_API_KEY=
STT_MODEL=

LLM_PROVIDER=
LLM_API_KEY=
LLM_MODEL=

ENABLE_INTERRUPTION=true
MIN_OVERLAP_MS=180
INTERRUPTION_CONFIRMATION_MS=300
TTS_MAX_PENDING_AUDIO_MS=2000
TEXT_CHUNK_MIN_CHARS=6
TEXT_CHUNK_PREFERRED_CHARS=16
TEXT_CHUNK_MAX_CHARS=32
TEXT_CHUNK_MAX_WAIT_MS=250

ENABLE_DEBUG_EVENTS=true
ENABLE_AUDIO_DUMP=false
```

安全要求：

- `.env` 不可 commit。
- 生產環境使用 secret manager。
- log 不得輸出 API Key。
- 音訊 dump 預設關閉。
- 開啟音訊 dump 時需明確標示隱私風險與保存期限。

---

# 16. 音訊格式

## 16.1 內部標準

優先採用：

```text
PCM signed 16-bit little-endian
mono
24 kHz 或 16 kHz
固定 frame duration
```

最終 sample rate 由 MiniMax 輸出、Pipecat pipeline 與 LiveKit publish 所需轉碼成本的 Spike 決定。

## 16.2 原則

- 全系統只允許一個主要內部 PCM 格式。
- 解碼／重採樣集中在明確邊界。
- 不得在多個處理器反覆轉碼。
- 每個音訊 frame 必須能計算 duration。
- 播放 queue 使用毫秒而非只用 byte 數量衡量。

## 16.3 Spike 必測

- MiniMax PCM 是否為裸 PCM 或封裝 WAV。
- byte order。
- sample width。
- sample rate。
- channel count。
- 每個 chunk 是否可獨立播放。
- chunk 邊界是否會產生爆音。
- MP3 串流解碼是否增加明顯延遲。
- 24k → 48k 重採樣成本。
- LiveKit 發布音訊所需 frame 格式。

---

# 17. 延遲預算

## 17.1 指標定義

```text
T0  使用者語音開始
T1  Server 收到首個音訊 frame
T2  STT speech_start
T3  STT first partial
T4  STT final / turn end
T5  LLM request start
T6  LLM first token
T7  first speakable text chunk
T8  MiniMax request start
T9  MiniMax first audio chunk
T10 first audio queued
T11 first audio published to LiveKit
T12 client playback start
T13 interruption candidate
T14 local playback stopped
```

## 17.2 主要 KPI

### 正常回應

- `turn_end_to_llm_first_token = T6 - T4`
- `llm_first_token_to_tts_request = T8 - T6`
- `tts_ttfa = T9 - T8`
- `turn_end_to_first_audio = T12 - T4`
- `user_speech_start_to_first_audio = T12 - T0`

### 打斷

- `interruption_stop_latency = T14 - T13`
- `stale_audio_after_cancel_ms`
- `cancelled_generation_chunks_dropped`
- `false_interruptions_per_100_turns`

## 17.3 MVP 驗收目標

本地／良好網路環境：

- AI 說話時麥克風持續上行：100%。
- 打斷後本地可聽音訊停止：P50 ≤ 250ms，P95 ≤ 500ms。
- cancelled generation 晚到音訊實際播放：0。
- TTS first audio：建立基準；優化後目標 P50 ≤ 800ms，實際受 MiniMax、地區與模型影響。
- 使用者回合結束到首音：第一版 P50 ≤ 2.5s；後續目標 ≤ 1.5s。
- 不得出現 10 秒以上無解釋停頓；若發生需記錄分段 timing。
- 30 分鐘壓力對話不得記憶體無限成長。
- 100 次 interruption 測試不得出現舊 generation 復活播放。

上述是工程目標，不是對第三方服務的保證。

---

# 18. Observability

## 18.1 結構化事件

使用 JSON logging：

```json
{
  "event": "tts_first_audio",
  "session_id": "s_...",
  "generation_id": "g_...",
  "state": "tts_buffering",
  "provider": "minimax",
  "elapsed_ms": 412,
  "timestamp": "2026-07-19T00:00:00Z"
}
```

## 18.2 必記事件

- room connected/disconnected
- participant joined/left
- audio input started/stopped
- VAD start/end
- STT partial/final
- LLM start/first token/finish/cancel/error
- chunker emit
- MiniMax connect/session/task/audio/finish/error
- playback start/finish/clear
- interruption candidate/confirmed/rejected
- generation created/cancelled/completed
- state transition
- queue depth
- backpressure
- cleanup complete

## 18.3 禁止記錄

預設禁止：

- API Key。
- 完整 Voice ID。
- 原始音訊。
- 未遮罩的敏感個資。
- 完整 prompt 或醫療、金融等敏感內容。

開發模式可透過明確旗標記錄轉錄，但需在 README 警告。

## 18.4 Debug Timeline

每輪產生：

```json
{
  "generation_id": "g_123",
  "timeline": [
    {"name": "user_turn_end", "t_ms": 0},
    {"name": "llm_first_token", "t_ms": 310},
    {"name": "chunk_emit", "t_ms": 370},
    {"name": "tts_first_audio", "t_ms": 760},
    {"name": "playback_start", "t_ms": 820}
  ]
}
```

---

# 19. Web Client MVP

功能：

- Join/leave room。
- 麥克風開關。
- 音訊輸出。
- 連線狀態。
- AI 狀態文字：
  - 聆聽中
  - 你正在說話
  - 思考中
  - 準備說話
  - AI 說話中
  - 已被打斷
  - 重新連線
- partial transcript。
- final transcript。
- AI display text。
- 即時延遲面板。
- Debug event stream（開發模式）。
- 手動「立即停止 AI」按鈕，用來驗證取消鏈。

瀏覽器要求：

- 使用 HTTPS 或 localhost。
- 申請麥克風權限。
- 啟用 browser AEC、noise suppression、auto gain control 的可配置參數。
- 顯示目前 audio input device。
- 重新整理或離開頁面時清理 participant。

---

# 20. 錯誤處理

## 20.1 MiniMax 連線錯誤

- connect timeout。
- auth failure。
- invalid voice/model config。
- provider rate limit。
- malformed event。
- receive timeout。
- unexpected close。
- audio decode failure。

處理：

1. 記錄結構化錯誤。
2. generation 標記 failed。
3. 清空該 generation queue。
4. 可重試一次，僅限可重試錯誤。
5. 回到 LISTENING。
6. 不得進入無限重連。

## 20.2 LiveKit 斷線

- 暫停新生成。
- 取消 active generation。
- 清理 queue。
- 依 SDK 能力重連。
- 重連成功後回到 LISTENING。
- 不自動重播斷線前舊回答。

## 20.3 STT 失敗

- 不將空字串送給 LLM。
- 顯示辨識失敗。
- 回到 LISTENING。
- 允許使用者重說。

## 20.4 LLM 失敗

- 取消 TTS。
- 不播放半截未完成舊回答，除非產品策略另行定義。
- 回到 LISTENING。
- 記錄錯誤與 provider latency。

---

# 21. 測試規格

## 21.1 Unit Tests

### Chunker

- 句號切分。
- 逗號切分。
- 最大長度。
- timeout flush。
- 中文標點。
- Markdown 清理。
- 不重複文字。
- cancel 後清空。
- 不同 generation 不混合。

### Generation Guard

- active generation 通過。
- cancelled generation 丟棄。
- 舊 generation 晚到音訊丟棄。
- concurrent cancel idempotent。
- 完成後不可復活。

### Floor Controller

- 合法狀態轉移。
- 非法狀態轉移拒絕並記錄。
- BOT_SPEAKING + user interruption。
- TTS_BUFFERING + interruption。
- LLM THINKING + interruption。
- error recovery。
- session cleanup。

### Interruption

- 高優先詞立即中斷。
- 短「嗯」不打斷。
- 「嗯等一下」必須打斷。
- 背景短噪音不打斷。
- 持續語音超過門檻中斷。

### MiniMax Protocol

- session started。
- audio event。
- task finished。
- task failed。
- unknown event。
- malformed JSON。
- close。
- timeout。

## 21.2 Integration Tests

以 fake MiniMax WebSocket server 測試：

- 正常串流。
- 延遲首包。
- 中途斷線。
- cancellation 後繼續送晚到 chunk。
- 大量 chunk。
- malformed audio。
- provider error。
- reconnect。

Pipeline 測試：

- STT final → LLM deltas → chunker → TTS audio。
- bot speaking → user overlap → playback clear。
- cancellation 後新 generation 正常播放。
- 連續 100 輪無 task leak。

## 21.3 Contract Test

只有在 `RUN_MINIMAX_CONTRACT_TESTS=1` 時執行真實 API：

- 驗證目前 model。
- 驗證 Voice ID。
- 驗證 WebSocket event schema。
- 驗證 audio format。
- 測量 TTFA。
- 驗證多次 `task_continue`。
- 驗證 `task_finish`。
- 實測關閉 socket 後 provider 行為。
- 實測連線能否跨 generation 重用。
- 實測同 session 是否允許多任務。
- 保存去敏後結果至 `docs/minimax-spike-results.md`。

## 21.4 E2E 人工測試

情境：

1. 正常問答 20 輪。
2. AI 開口 200ms 後打斷。
3. AI 回答中段打斷。
4. AI 快結束時打斷。
5. 只說「嗯」。
6. 說「嗯，等一下」。
7. 背景播放人聲。
8. 戴耳機。
9. 使用筆電喇叭。
10. 網路降速與抖動。
11. MiniMax 暫時斷線。
12. 連續對話 30 分鐘。
13. 快速連續打斷三次。
14. 打斷後立刻提出新問題。
15. 使用同一 Voice ID 驗證聲線一致。

---

# 22. Definition of Done

一個工作項目完成必須同時符合：

- 程式碼完成。
- 型別檢查通過。
- lint 通過。
- unit test 通過。
- 相關 integration test 通過。
- 無 API key。
- 有結構化 log。
- 有錯誤處理。
- README 已更新。
- CHANGELOG 已更新。
- 有驗收步驟。
- 無未說明的 TODO。
- 不破壞 generation cancellation 不變量。

---

# 23. 開發階段

## Phase 0：MiniMax WebSocket Spike

目標：在不接 Pipecat、LiveKit 前，確認 MiniMax 真實協議行為。

交付：

- `scripts/run_minimax_spike.py`
- 可送一段文字並即時保存／播放音訊。
- 去敏事件 log。
- 音訊格式報告。
- TTFA 基準。
- task_continue 行為。
- task_finish 行為。
- socket close/cancel 行為。
- 連線重用結論。
- `docs/minimax-spike-results.md`

驗收閘門：

- 未完成 Spike，不進入正式 Adapter 開發。

## Phase 1：MiniMaxTTSService

交付：

- WebSocket client。
- protocol parser。
- audio decoder。
- generation guard。
- fake server tests。
- contract tests。
- structured events。

驗收：

- 可從文字 chunk 產生 Pipecat audio frame。
- cancellation 後晚到音訊 0 播放。
- 連線錯誤不鎖死。

## Phase 2：Pipecat 基本 Pipeline

交付：

```text
Transport Input
→ STT
→ Context/User Aggregator
→ LLM
→ Semantic Text Chunker
→ MiniMaxTTSService
→ Transport Output
```

驗收：

- 不接 interruption 時完成 20 輪正常對話。
- 每階段 timing 可見。
- 無明顯 queue 累積。

## Phase 3：LiveKit WebRTC

交付：

- LiveKit room token endpoint。
- Web client。
- Pipecat LiveKit transport。
- 雙向音訊。
- 麥克風與播放。
- session cleanup。

驗收：

- AI 說話時使用者上行音訊持續存在。
- 瀏覽器可完成正常問答。
- reload 不殘留 active session。

## Phase 4：硬中斷

交付：

- Floor Controller。
- interruption detector。
- local playback clear。
- LLM cancel。
- MiniMax generation cancel/discard。
- generation ID guard。

驗收：

- P50 停播 ≤ 250ms。
- P95 ≤ 500ms。
- 舊 generation 音訊復活 = 0/100。

## Phase 5：語意切塊與延遲優化

交付：

- Chunker。
- 中文正規化。
- 首音指標。
- queue/backpressure。
- benchmark script。

驗收：

- 回答不明顯斷字。
- 不重複朗讀。
- 首音明顯早於完整回答完成。
- 產出延遲瀑布圖資料。

## Phase 6：Backchannel MVP

交付：

- allowlist。
- 高優先 interruption phrases。
- 短附和判斷。
- 測試與人工驗收記錄。

驗收：

- 「嗯」大多不打斷。
- 「等一下」可靠打斷。
- 「嗯，等一下」可靠打斷。

## Phase 7：Production Hardening

交付：

- Docker。
- health/readiness。
- graceful shutdown。
- rate limit。
- secret handling。
- tracing/metrics。
- load test。
- runbook。

---

# 24. Codex 第一批任務

## Task 001：建立專案骨架

建立：

- Python 3.12 專案。
- `uv` dependency management。
- `ruff`。
- `mypy` 或 pyright。
- `pytest`。
- `pytest-asyncio`。
- `README.md`。
- `.env.example`。
- 上述目錄。
- CI 執行 lint、typecheck、unit tests。

完成後只提交骨架，不先寫假 API。

## Task 002：MiniMax Spike

依 MiniMax 官方 WebSocket 文件建立獨立腳本：

- 使用環境變數。
- 連線。
- 發送 session/task 事件。
- 串流接收音訊。
- 保存音訊。
- 輸出 timing。
- 去敏 log。
- 支援 Ctrl+C cleanup。

將所有實測結果寫進 `docs/minimax-spike-results.md`。

## Task 003：建立 Protocol Models

使用 typed dataclass、TypedDict 或 Pydantic 定義：

- outbound events。
- inbound events。
- error schema。
- audio event。
- task lifecycle。
- unknown event fallback。

建立 fixture 與 unit tests。

## Task 004：Generation Guard

實作 thread-safe / async-safe generation registry：

```python
create()
activate()
cancel()
complete()
is_active()
assert_active()
```

建立 late chunk tests。

## Task 005：MiniMaxTTSService

在 Spike 結論基礎上實作正式 service。

不得複製 Spike 的臨時結構；需抽象：

- connection。
- protocol。
- decoder。
- cancellation。
- metrics。

## Task 006：Semantic Text Chunker

先做純函式與狀態式測試，再接 Pipecat FrameProcessor。

## Task 007：Floor Controller

建立明確 state transition table，不可把狀態散落在多個 boolean callback 中。

## Task 008：Fake Providers

建立：

- FakeStreamingSTT。
- FakeStreamingLLM。
- FakeMiniMaxServer。

使 CI 不需要付費 API。

## Task 009：基本 Pipeline

先用 fake transport 或 local transport 驗證完整資料流。

## Task 010：LiveKit 接入

依目前安裝的 Pipecat 版本使用官方 LiveKit transport 實作；若 API 與範例不同，以當下官方 package 型別與文件為準，並在 ADR 記錄差異。

---

# 25. Codex 每次回報格式

每個任務完成後回報：

```text
任務：
狀態：完成 / 部分完成 / 阻塞

已完成：
- ...

修改檔案：
- path
- path

測試：
- command
- result

驗收結果：
- ...

實測數據：
- ...

已知限制：
- ...

下一步：
- 僅列規格書中的下一個任務
```

禁止只說「已完成」而沒有測試證據。

---

# 26. 風險清單

| 風險 | 影響 | 緩解 |
|---|---|---|
| MiniMax 沒有低延遲 cancel | 舊音訊持續產生 | 本地立即止播＋generation discard＋關 socket |
| MiniMax 僅支援壓縮格式 | 解碼增加延遲 | Spike 比較 PCM/WAV/MP3，集中解碼 |
| TTS 文字切太碎 | 語調斷裂 | Semantic Chunker＋最小字數＋標點 |
| TTS 文字切太大 | 首音慢 | timeout flush＋preferred chunk |
| LiveKit 與 Pipecat 版本不相容 | Transport 問題 | pin versions＋官方範例＋integration test |
| AEC 不足 | AI 聲音被當成使用者 | browser AEC＋耳機測試＋far-end reference 策略 |
| 短附和誤判成打斷 | 對話卡頓 | allowlist＋持續時間＋partial/final 結合 |
| 真打斷被視為附和 | AI 不停 | 高優先詞＋持續語音立即中斷 |
| 晚到 chunk 復活 | 嚴重 UX bug | generation guard 作為硬閘門 |
| 遠端 API 延遲波動 | 首音不穩 | 完整 timing＋連線重用 Spike＋區域部署 |
| 多套編排器衝突 | 難以除錯 | Pipecat 單一編排，LiveKit 僅 transport |
| log 洩漏語音或個資 | 隱私風險 | 預設不 dump 音訊，內容 log 可關閉 |

---

# 27. 成功標準

MVP 成功不是「看起來能聊天」，而是同時滿足：

1. 使用者與 AI 音訊上下行真正並行。
2. MiniMax Voice ID 穩定輸出。
3. 回答採串流，不等待完整文本。
4. 使用者打斷可迅速止播。
5. 舊 generation 永不復活。
6. 每一段延遲都可被量測。
7. STT、LLM、TTS 與 transport 可獨立替換。
8. 系統可連續運作，不因取消與重連累積殭屍 task。
9. 有自動化測試證明核心不變量。
10. 後續能在 Floor Controller 上加入語氣靈、backchannel、搶話、讓話與恢復策略。

---

# 28. 最終技術定義

本系統採用 Pipecat、LiveKit 與 MiniMax 組成模組化即時語音架構：

- **Pipecat** 作為唯一的對話編排與雙工話語權控制核心，負責 Frame 流程、打斷、重疊語音、狀態管理、generation cancellation、文字切塊、音訊 queue 與模型協調。
- **LiveKit** 作為 WebRTC 雙向媒體基礎設施，負責持續收音、即時播放、回聲消除能力、網路傳輸與房間連線。
- **MiniMax WebSocket TTS** 作為唯一正式聲音輸出引擎，保留指定 Voice ID、聲線與語氣表現。
- **獨立 Streaming STT 與 Streaming LLM** 分別負責語音辨識與語意推理，並透過抽象介面保持可替換性。

系統採用單一編排器、雙向持續音訊、generation ID 硬隔離、本地優先止播與全鏈路可觀測設計，使對話智能、雙工控制、媒體傳輸與聲音生成彼此解耦，能分別替換、測試與優化。

---

# 29. 官方技術依據

- Pipecat Pipeline 與 Frames：  
  https://docs.pipecat.ai/pipecat/learn/pipeline
- Pipecat 自訂 FrameProcessor：  
  https://docs.pipecat.ai/pipecat/fundamentals/custom-frame-processor
- Pipecat Speech Input 與 interruption：  
  https://docs.pipecat.ai/pipecat/learn/speech-input
- Pipecat Text-to-Speech：  
  https://docs.pipecat.ai/pipecat/learn/text-to-speech
- Pipecat LLMTextProcessor：  
  https://docs.pipecat.ai/api-reference/server/utilities/frame/llm-text-processor
- Pipecat LiveKit Transport 範例：  
  https://github.com/pipecat-ai/pipecat/blob/main/examples/transports/transports-livekit.py
- LiveKit 平台概覽：  
  https://docs.livekit.io/intro/overview/
- LiveKit Pipeline 模組化與串流概念：  
  https://docs.livekit.io/agents/models/pipelines/
- MiniMax Text to Speech WebSocket：  
  https://platform.minimax.io/docs/api-reference/speech-t2a-websocket

---

**規格書結束**
