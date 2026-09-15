# 韓文打字練習功能規劃

參考網站：[hangul-sprint.12qwer.workers.dev](https://hangul-sprint.12qwer.workers.dev)（한글 SPRINT｜韓文打字練習室）
整合目標專案：[sallywchun-ui/reading](https://github.com/sallywchun-ui/reading)（Python + Streamlit）

---

## 1. 現況對比

### 1.1 目標專案（Python + Streamlit）

- `main_web.py`：整個 app 的入口，用 `st.sidebar.radio` 切換三種模式（40音測驗 / 教材課程 / 打字練習）。
- `lessons/typing_practice.py`：已存在一個打字練習模組——鍵盤參考圖 + 練習句 + `render_typing_mode()`，但屬於較陽春版本：無即時鍵位標示、無 CSV 匯入、無結算頁。
- 技術本質：Streamlit 是伺服器端渲染、靠 rerun 更新畫面的框架，`st.text_input` 需按 Enter 才會觸發 Python 端邏輯。

### 1.2 參考網站（Cloudflare Workers，純前端 SPA）

- **即時鍵位提示**：每打一個字元，畫面立刻標示下一個要按的鍵（逐鍵 `keydown` 監聽，非整段輸入完才判斷）。
- 4 種練習模式：一般 / 聽寫 / 無提示 / 中文回想，另有每日「休閒天梯 Beta」。
- CSV 匯入自訂單字庫、匯出/匯入練習紀錄（存於瀏覽器 localStorage）。
- 完整結算頁、韓文 TTS 發音。

### 1.3 關鍵落差

Streamlit 原生元件無法做到「逐鍵即時標示」——這需要 JS 監聽 `keydown` 並即時更新 DOM，中間沒有伺服器往返，Streamlit 每次互動都要走一次 rerun，不適合逐字元判斷。

---

## 2. 技術方案選項

### 方案 A：務實版，留在 Streamlit 生態內

- 保留現有 `st.text_input` + `on_change` 的整段/整句提交模式。
- 借鏡參考網站的部分：CSV 匯入單字庫、多種練習模式切換、結算統計（正確率、練習紀錄）。
- 優點：與現有 `main_web.py` 架構完全相容，改動小。
- 缺點：拿不到「即時鍵位提示」這個最吸睛的功能。

### 方案 B：Streamlit Custom Component 嵌入 HTML/JS

- 用 `st.components.v1.html()` 嵌入一段自製 HTML+JS（類似參考網站的前端邏輯），在瀏覽器端做逐鍵判斷、即時標示鍵位、計算 WPM/準確率。
- 練習結果透過 `Streamlit.setComponentValue` 傳回 Python，寫入 `mastery_map` / 練習紀錄。
- 優點：使用體驗可真正貼近參考網站。
- 缺點：需維護兩套邏輯（JS 前端練習引擎 + Python 端資料整合），複雜度明顯提高。

### 建議路線

1. 先用**方案 A** 補齊 `typing_practice.py` 的功能/資料層（CSV 匯入、多模式、結算頁、練習紀錄匯出入），此部分與 UI 框架無關，改動風險低。
2. 若之後仍在意「即時鍵位提示」的手感，再把打字練習頁面獨立做成**方案 B** 的自訂元件，其餘部分（教材、40音測驗）維持原生 Streamlit。

---

## 3. 檔案切分規劃

`vocab.py`／`csv_io.py`／`records.py` 對應的功能（CSV 匯入、練習紀錄匯出入）現在都還不存在，先把整個資料夾骨架搭出來會變成「先蓋房間再決定要不要住」。**第一階段只切 4 個檔**，把現有功能（鍵盤圖＋整句練習）搬過去；等真的要做 CSV 匯入或練習紀錄時，再把對應功能從 `engine.py`／`models.py` 拆出成獨立檔案。

```
lessons/
├── textbook_app.py          (既有，不動)
├── romanization.py           (既有，不動——keymap.py 會直接複用它的音節拆解)
└── typing/                   (新增子套件)
    ├── __init__.py            # 對外只 export render_typing_mode()
    ├── models.py              # 資料類別 + Enum
    ├── keymap.py              # 韓文字元 → 두벌식鍵位 對照表
    ├── engine.py              # 出題邏輯、判分、統計（不含 st.* UI 呼叫）
    └── ui.py                  # render_typing_mode() 主體，只做畫面組裝
```

第二階段（真的要做 CSV 匯入單字庫時）才新增：

```
    ├── vocab.py               # 內建單字庫定義 + 目前單字庫管理
    └── csv_io.py              # CSV 匯入/匯出、格式驗證
```

`records.py`（練習紀錄匯出/匯入）**先不做**，見第 7 節的決定。

`main_web.py` 只需把：

```python
from lessons.typing_practice import render_typing_mode
```

改為：

```python
from lessons.typing import render_typing_mode
```

對外介面不變。

**設計理由**：`engine.py`（邏輯）與 `ui.py`（畫面）刻意分離——未來若要改用方案 B（自訂 HTML/JS 元件），只需重寫 `ui.py`，`engine.py` 與資料層完全不用動。

---

## 4. 資料模型（`models.py`）

```python
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional

class PracticeMode(str, Enum):
    NORMAL = "一般"              # 看韓文與鍵位提示
    DICTATION = "聽寫"            # 聽發音後輸入
    NO_HINT = "無提示"            # 顯示韓文，不提示按鍵
    MEANING_RECALL = "中文回想"    # 看繁中回想韓文

@dataclass(frozen=True)
class VocabItem:
    hangul: str                          # 韓文欄（必填）
    meaning: str                         # 中文欄（必填）
    reading: str = ""                    # 單字讀音，只給 TTS 用，留空則用 hangul 發音
    part_of_speech: str = ""
    status: str = ""                     # 例如「複習」
    source_row: int = -1                 # 方便回報錯誤列號

@dataclass(frozen=True)
class VocabSource:
    name: str                            # 「內建基礎單字」或匯入檔名
    items: list[VocabItem]
    is_builtin: bool = True

@dataclass
class QuestionResult:
    item: VocabItem
    mode: PracticeMode
    is_correct: bool
    expected_keys: int
    correct_keys: int
    elapsed_seconds: float

@dataclass
class PracticeRecord:
    """一輪練習結束後的結算摘要，只留當下這一輪、不做跨輪歷史（見第7節）"""
    mode: PracticeMode
    vocab_source_name: str
    question_count: int
    correct_count: int
    accuracy: float
    valid_keys_per_min: float
    total_seconds: float
    results: list[QuestionResult] = field(default_factory=list)
```

---

## 5. CSV 格式規劃（`csv_io.py`，第二階段才做）

這屬於第3節「第二階段」才新增的功能，第一階段（方案A的最小版本）不需要它。
沿用參考網站頁面上的欄位規則，讓使用者的 CSV 可兩邊共用，但先簡化成單一
中文/詞性欄位——「一詞多義」(中文1~4/詞性1~4) 對個人學習用途價值有限，
真的遇到需要多義詞時再擴充，不用一開始就把 `MeaningEntry` 列表結構做出來：

| 欄名 | 必填 | 說明 |
|---|---|---|
| 韓文 | 是 | 只接受完整韓文字與空格 |
| 單字讀音 | 否 | 留空則自動改用「韓文」欄發音 |
| 中文 | 是 | 詞義 |
| 詞性 | 否 | |
| 狀態 | 否 | 例如「複習」 |

**匯入邏輯重點**：

- 依欄名自動配對，不受欄位順序影響（用 `csv.DictReader`）。
- 無標題列時，前兩欄視為 韓文/中文（fallback 模式）。
- 錯誤或重複列需收集成 `ImportReport(valid: list[VocabItem], skipped: list[tuple[int, str]])`，回傳給 UI 顯示「匯入 N 筆，略過 M 筆（原因）」，不悄悄丟棄。

---

## 6. 鍵位對照（`keymap.py`）

「即時鍵位提示」的基礎資料，不論走方案 A 或 B 都用得到。

**音節拆解不重寫，直接複用 `romanization.py`**：`lessons/romanization.py` 裡的
`_decompose_syllable()` 已經是驗證過、跑過全部 10 課近 3000 句韓文都沒出錯的
Unicode 算術拆解（`가`=U+AC00 起算 初聲/中聲/終聲 index）。`keymap.py` 只需要
`from .romanization import _decompose_syllable as decompose_syllable`
（或把它提升成 `lessons/hangul.py` 共用工具，兩邊都 import），在上面疊一層
「音位 index → 鍵位」的對照表即可，不要在 `keymap.py` 裡重新寫一份拆解邏輯。

**Shift 鍵慣例**：對照表裡用**大寫字母代表「按住 Shift 再按這顆鍵」**，例如
`"ㄲ": "R"` 表示 Shift+R。`ui.py` 顯示鍵位提示時，遇到大寫要額外畫出
「⇧ Shift」標記，不能直接把字母原樣印出來。

**非韓文字元一律原樣通過**：練習句裡本來就有空白、`?`、`.`（例如「안녕하세요?」），
두벌식鍵盤的標點與數字鍵位和一般 QWERTY 相同，所以 `syllable_to_keys()`
遇到非韓文音節字元時，直接回傳該字元本身（小寫視為不需要 Shift、大寫或需要
Shift 的符號則回傳對應的 `(key, need_shift)`），不能假設輸入永遠是韓文音節，
否則遇到標點會直接查表失敗。

```python
# 두벌식（2-beolsik）鍵位對照：韓文子母音 → 實體鍵（大寫＝需按 Shift）
CHOSUNG_KEYS: dict[int, str] = {0: "r", 1: "R", 2: "s", ...}    # index 對應 romanization._INITIALS 的順序
JUNGSUNG_KEYS: dict[int, str] = {0: "k", 2: "w", ...}           # index 對應 romanization._VOWELS 的順序
JONGSUNG_KEYS: dict[int, str] = {0: "", 1: "r", 3: "rt", ...}   # index 對應 romanization._FINALS 的順序；複合終聲＝兩顆鍵依序按

def syllable_to_keys(char: str) -> list[str]:
    """把一個字轉成依序要按的鍵序列。

    韓文音節：依初聲/中聲/終聲各自查表展開成 1~4 個鍵（終聲為複合子音時展開成
    兩個鍵，例如 ㄳ → ["r", "t"]；終聲為空時該音節只佔 2 個鍵）。
    非韓文字元（空白、標點、數字、英文字母等）：原樣回傳單一鍵 [char]。

    例：'안' → ['d', 'k', 's']（ㅇ 靜音仍佔一鍵 d，因為 d 鍵本身就是 ㅇ）
        '안녕하세요?' 的 '?' → ['?']
    """
    ...
```

`engine.py` 判分時，就是把 `syllable_to_keys()` 攤平整句話後得到的鍵序列，
和使用者目前輸入位置逐鍵比對——這部分邏輯不受 UI（Streamlit 或自訂元件）
影響，值得獨立成乾淨模組先做好。

---

## 7. Session State 規劃

**決定：不做練習紀錄的匯出/匯入。** 參考網站是給不特定訪客用的公開網站，才需要
「資料只存在這個瀏覽器」的匯出/匯入機制；這個專案是自己的學習工具，不是要
共用給其他人，reload 後紀錄歸零並不影響學習本身（正確率/速度這種單次統計，
看完當下就沒有保留的必要）。先只用 `st.session_state` 撐過同一次瀏覽階段，
不做 `records.py`、不做 JSON 持久化。如果之後真的想跨裝置/跨天追蹤進度，
再回頭評估要不要做（那時候多半會想要一個真正的資料庫而不是 JSON 檔案）。

```python
# st.session_state 的 key 規劃
"typing_vocab_source": VocabSource          # 目前使用中的單字庫
"typing_mode": PracticeMode
"typing_queue": list[int]                    # 本輪題目索引順序
"typing_current_idx": int
"typing_last_result": Optional[QuestionResult]  # 只留「這一題」的結果，不做歷史紀錄
```

---

## 8. 決定事項 / 下一步

以下都已拍板，不再是待討論的開放問題：

- **方案 A/B**：先做方案 A（第一階段，留在 Streamlit 生態內），把即時鍵位提示這種
  需要 JS 的功能明確排除在第一階段之外；等第一階段用起來覺得手感不夠再評估方案 B。
- **音節拆解**：不重寫，`keymap.py` 直接複用 `lessons/romanization.py` 的
  `_decompose_syllable()`（見第6節）。鍵位對照表本身（`CHOSUNG_KEYS` 等三張表）
  仍是新東西，需要針對兩벌식全部 27 種終聲＋雙子音初聲寫測試，比照
  `romanization.py` 當初的驗證方式（跑過現有教材全部句子 + 手寫已知案例）。
- **練習紀錄持久化**：不做（見第7節）。只在單一瀏覽階段內用 `st.session_state`
  保留當下這一輪的統計。
- **TTS**：直接複用 `main_web.py` 既有的 `get_tts_audio_bytes()`（gTTS + 快取），
  不需另外評估或重寫；聽寫模式（`PracticeMode.DICTATION`）呼叫它取得音檔即可。

下一步（依實作順序）：

1. 建立 `lessons/typing/` 的 4 個檔案（`models.py` / `keymap.py` / `engine.py` /
   `ui.py`），把現有 `typing_practice.py` 的鍵盤圖與整句練習邏輯搬過去，功能不變。
2. `keymap.py`：三張鍵位對照表 + `syllable_to_keys()`，寫測試涵蓋雙子音終聲
   （ㄳ/ㄵ/ㄺ/ㄼ/ㅄ 等）與非韓文字元（空白、`?`、`.`、數字）。
3. `engine.py`：把逐鍵比對、正確率/速度統計獨立出來，供 `ui.py` 呼叫。
4. 確認第一階段功能穩定後，再視需要做第二階段（CSV 匯入單字庫）。
