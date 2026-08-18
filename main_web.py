"""Korean 40-Sound and Vocabulary Trainer built with Streamlit.

This module provides an interactive web-based trainer for learning the 40
Korean Hangul characters (vowels, consonants, tense/aspirated sounds, compounds)
and progressing into Phase 4: foundational vocabulary words. It features
real-time audio synthesis via gTTS, dynamic romanization grading, and
mastery-based progression.

Typical usage example:
    streamlit run main_web.py
"""

from __future__ import annotations

import base64
import io
import logging
import random
from dataclasses import dataclass, field
from typing import Dict, Final, List, Optional

import streamlit as st
from gtts import gTTS
from gtts.tts import gTTSError

# Module-level logging setup
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger(__name__)

# --- Domain Constants ---
MASTERY_GOAL: Final[int] = 3


# --- Domain Data Entities ---

@dataclass(frozen=True)
class StudyItem:
    """Represents a single learning unit (character or vocabulary word).

    Attributes:
        prompt: The Hangul character or word displayed to the user.
        romanization: The standard romanized answer required for input.
        meaning: Optional translation or semantic meaning (used for Phase 4 words).
    """

    prompt: str
    romanization: str
    meaning: Optional[str] = None


@dataclass(frozen=True)
class Phase:
    """Represents a discrete curriculum stage containing study items.

    Attributes:
        name: The display name of the learning phase.
        items: List of StudyItem objects contained within this phase.
    """

    name: str
    items: List[StudyItem]

    @property
    def item_map(self) -> Dict[str, StudyItem]:
        """Provides prompt-to-item dictionary mapping."""
        return {item.prompt: item for item in self.items}


# --- Curriculum Definition (40 Sounds + Phase 4 Vocabulary) ---

CURRICULUM: Final[List[Phase]] = [
    Phase(
        name="Phase 1: 基礎音 (Basic Vowels & Consonants)",
        items=[
            StudyItem(prompt="ㅏ", romanization="a"),
            StudyItem(prompt="ㅓ", romanization="eo"),
            StudyItem(prompt="ㅗ", romanization="o"),
            StudyItem(prompt="ㅜ", romanization="u"),
            StudyItem(prompt="ㅡ", romanization="eu"),
            StudyItem(prompt="ㅣ", romanization="i"),
            StudyItem(prompt="ㄱ", romanization="g"),
            StudyItem(prompt="ㄴ", romanization="n"),
            StudyItem(prompt="ㄷ", romanization="d"),
            StudyItem(prompt="ㄹ", romanization="r"),
            StudyItem(prompt="ㅁ", romanization="m"),
            StudyItem(prompt="ㅂ", romanization="b"),
            StudyItem(prompt="ㅅ", romanization="s"),
            StudyItem(prompt="ㅇ", romanization="ng"),
            StudyItem(prompt="ㅈ", romanization="j"),
            StudyItem(prompt="ㅎ", romanization="h"),
        ],
    ),
    Phase(
        name="Phase 2: 衍生/激音/雙子音 (Derived, Aspirated & Tense)",
        items=[
            StudyItem(prompt="ㅑ", romanization="ya"),
            StudyItem(prompt="ㅕ", romanization="yeo"),
            StudyItem(prompt="ㅛ", romanization="yo"),
            StudyItem(prompt="ㅠ", romanization="yu"),
            StudyItem(prompt="ㅋ", romanization="k"),
            StudyItem(prompt="ㅌ", romanization="t"),
            StudyItem(prompt="ㅍ", romanization="p"),
            StudyItem(prompt="ㅊ", romanization="ch"),
            StudyItem(prompt="ㄲ", romanization="kk"),
            StudyItem(prompt="ㄸ", romanization="tt"),
            StudyItem(prompt="ㅃ", romanization="pp"),
            StudyItem(prompt="ㅆ", romanization="ss"),
            StudyItem(prompt="ㅉ", romanization="jj"),
        ],
    ),
    Phase(
        name="Phase 3: 複合母音 (Compound Vowels)",
        items=[
            StudyItem(prompt="ㅐ", romanization="ae"),
            StudyItem(prompt="ㅒ", romanization="yae"),
            StudyItem(prompt="ㅔ", romanization="e"),
            StudyItem(prompt="ㅖ", romanization="ye"),
            StudyItem(prompt="ㅘ", romanization="wa"),
            StudyItem(prompt="ㅙ", romanization="wae"),
            StudyItem(prompt="ㅚ", romanization="oe"),
            StudyItem(prompt="ㅝ", romanization="wo"),
            StudyItem(prompt="ㅞ", romanization="we"),
            StudyItem(prompt="ㅟ", romanization="wi"),
            StudyItem(prompt="ㅢ", romanization="ui"),
        ],
    ),
    Phase(
        name="Phase 4: 基礎單字 (Basic Vocabulary Words)",
        items=[
            StudyItem(prompt="나무", romanization="namu", meaning="樹木"),
            StudyItem(prompt="우유", romanization="uyu", meaning="牛奶"),
            StudyItem(prompt="고기", romanization="gogi", meaning="肉"),
            StudyItem(prompt="사자", romanization="saja", meaning="獅子"),
            StudyItem(prompt="바다", romanization="bada", meaning="大海"),
            StudyItem(prompt="오이", romanization="oi", meaning="小黃瓜"),
            StudyItem(prompt="모자", romanization="moja", meaning="帽子"),
            StudyItem(prompt="치마", romanization="chima", meaning="裙子"),
            StudyItem(prompt="코", romanization="ko", meaning="鼻子"),
            StudyItem(prompt="포도", romanization="podo", meaning="葡萄"),
            StudyItem(prompt="사과", romanization="sagwa", meaning="蘋果"),
            StudyItem(prompt="의사", romanization="uisa", meaning="醫生"),
            StudyItem(prompt="돼지", romanization="dwaeji", meaning="豬"),
            StudyItem(prompt="기차", romanization="gicha", meaning="火車"),
            StudyItem(prompt="토끼", romanization="tokki", meaning="兔子"),
            StudyItem(prompt="찌개", romanization="jjigae", meaning="鍋物/燉湯"),
        ],
    ),
]


# --- Text-to-Speech Service ---

@st.cache_data(show_spinner=False, ttl=None)
def get_tts_audio_bytes(text: str) -> Optional[bytes]:
    """Synthesizes Korean audio using gTTS and caches the byte content.

    Args:
        text: The Korean character or word string to synthesize.

    Returns:
        Raw MP3 bytes on success, or None if network/API failure occurs.

    Raises:
        None. Errors are captured and logged internally.
    """
    try:
        buffer = io.BytesIO()
        tts = gTTS(text=text, lang="ko", slow=False)
        tts.write_to_fp(buffer)
        return buffer.getvalue()
    except gTTSError as exc:
        logger.error("gTTS API exception for text '%s': %s", text, exc)
        return None
    except (ConnectionError, OSError, TimeoutError) as exc:
        logger.error("Network connection error synthesizing '%s': %s", text, exc)
        return None


def render_audio_controller(text: str, auto_play: bool = True) -> None:
    """Renders an HTML5 audio element with an automatic playback script.

    Args:
        text: Korean prompt text to synthesize.
        auto_play: Flag indicating whether programmatic playback is requested.

    Returns:
        None.
    """
    audio_bytes = get_tts_audio_bytes(text)
    if audio_bytes is None:
        st.warning("⚠️ 語音服務連線異常，請先手動輸入拼音練習。")
        return

    encoded_audio = base64.b64encode(audio_bytes).decode("utf-8")
    audio_id = f"audio_{abs(hash(text))}_{random.randint(1000, 9999)}"

    audio_html = f"""
    <div style="margin-top: 8px; margin-bottom: 8px; text-align: center;">
        <audio id="{audio_id}" preload="auto" controls style="width: 100%; max-width: 320px; height: 36px;">
            <source src="data:audio/mpeg;base64,{encoded_audio}" type="audio/mpeg">
            您的瀏覽器不支援 Audio 標籤。
        </audio>
    </div>
    <script>
        (function() {{
            const audioEl = document.getElementById("{audio_id}");
            if (!audioEl) return;
            audioEl.volume = 1.0;
            const autoPlayEnabled = {str(auto_play).lower()};
            if (autoPlayEnabled) {{
                const promise = audioEl.play();
                if (promise !== undefined) {{
                    promise.catch(function(err) {{
                        console.warn("Autoplay was prevented by browser security policy: ", err);
                    }});
                }}
            }}
        }})();
    </script>
    """
    st.components.v1.html(audio_html, height=52)


# --- Core Engine & State Management ---

class TrainerEngine:
    """Manages progression logic, mastery mapping, and item selection."""

    @staticmethod
    def initialize_state() -> None:
        """Initializes Streamlit session_state with schema keys."""
        if "trainer_initialized" in st.session_state:
            return

        st.session_state.trainer_initialized = True
        st.session_state.current_phase_idx = 0
        
        # Build mastery map for all items across all phases
        mastery_map: Dict[str, int] = {}
        for phase in CURRICULUM:
            for item in phase.items:
                mastery_map[item.prompt] = 0
        st.session_state.mastery_map = mastery_map

        initial_phase = CURRICULUM[0]
        st.session_state.target_prompt = random.choice(initial_phase.items).prompt
        st.session_state.feedback_msg = ""
        st.session_state.feedback_type = "info"
        st.session_state.trigger_audio = True
        st.session_state.curriculum_complete = False

    @classmethod
    def get_current_phase(cls) -> Phase:
        """Retrieves the active Phase instance."""
        idx = st.session_state.current_phase_idx
        return CURRICULUM[idx]

    @classmethod
    def get_active_item(cls) -> StudyItem:
        """Retrieves the currently targeted StudyItem."""
        phase = cls.get_current_phase()
        prompt = st.session_state.target_prompt
        return phase.item_map[prompt]

    @classmethod
    def is_phase_mastered(cls, phase: Phase) -> bool:
        """Checks if all items in a phase have reached the mastery goal."""
        return all(
            st.session_state.mastery_map[item.prompt] >= MASTERY_GOAL
            for item in phase.items
        )

    @classmethod
    def pick_next_prompt(cls, phase: Phase, exclude_prompt: Optional[str] = None) -> str:
        """Picks the next prompt prioritizing unmastered items.

        Args:
            phase: Current active Phase.
            exclude_prompt: Prompt string to avoid repeating immediately.

        Returns:
            A prompt string representing the chosen item.
        """
        unmastered = [
            item.prompt
            for item in phase.items
            if st.session_state.mastery_map[item.prompt] < MASTERY_GOAL
        ]
        pool = unmastered if unmastered else [item.prompt for item in phase.items]

        if exclude_prompt and len(pool) > 1:
            pool = [p for p in pool if p != exclude_prompt]

        return random.choice(pool)

    @classmethod
    def advance_phase_or_finish(cls) -> None:
        """Advances the phase index or flags full completion."""
        next_idx = st.session_state.current_phase_idx + 1
        if next_idx >= len(CURRICULUM):
            st.session_state.curriculum_complete = True
            st.session_state.feedback_msg = "🎉 恭喜！您已成功完成包含基礎單字在內的所有階段！"
            st.session_state.feedback_type = "success"
        else:
            st.session_state.current_phase_idx = next_idx
            new_phase = CURRICULUM[next_idx]
            st.session_state.target_prompt = cls.pick_next_prompt(new_phase)
            st.session_state.feedback_msg = (
                f"🏆 晉級成功！進入【{new_phase.name}】"
            )
            st.session_state.feedback_type = "success"

    @classmethod
    def process_answer(cls) -> None:
        """Evaluates the submitted answer against the target prompt."""
        active_item = cls.get_active_item()
        raw_input = st.session_state.get("user_text_input", "").strip().lower()
        correct_answer = active_item.romanization.strip().lower()

        meaning_hint = f"（{active_item.meaning}）" if active_item.meaning else ""

        if raw_input == correct_answer:
            st.session_state.mastery_map[active_item.prompt] += 1
            st.session_state.feedback_msg = (
                f"✅ 正確！【{active_item.prompt}】= {active_item.romanization} {meaning_hint}"
            )
            st.session_state.feedback_type = "success"
        else:
            st.session_state.mastery_map[active_item.prompt] = 0
            st.session_state.feedback_msg = (
                f"❌ 答錯了！【{active_item.prompt}】正確拼音為：{active_item.romanization} {meaning_hint}（熟練度已重置）"
            )
            st.session_state.feedback_type = "error"

        current_phase = cls.get_current_phase()
        if cls.is_phase_mastered(current_phase):
            cls.advance_phase_or_finish()
        else:
            st.session_state.target_prompt = cls.pick_next_prompt(
                current_phase, exclude_prompt=active_item.prompt
            )

        st.session_state.user_text_input = ""
        st.session_state.trigger_audio = True

    @classmethod
    def skip_current_item(cls) -> None:
        """Skips active prompt without mutating mastery counters."""
        current_phase = cls.get_current_phase()
        current_prompt = st.session_state.target_prompt
        st.session_state.target_prompt = cls.pick_next_prompt(
            current_phase, exclude_prompt=current_prompt
        )
        st.session_state.feedback_msg = "⏭️ 已跳過當前題目，熟練度保持不變。"
        st.session_state.feedback_type = "info"
        st.session_state.user_text_input = ""
        st.session_state.trigger_audio = True


# --- View Presentation Layer ---

def render_completion_view() -> None:
    """Renders the comprehensive congratulation screen."""
    st.balloons()
    st.success("🏆 恭喜您！韓文 40 音全體發音與 Phase 4 基礎單字測驗已全數達標！")
    if st.button("🔄 重新開始完整課程", use_container_width=True):
        st.session_state.clear()
        st.rerun()


def render_practice_view() -> None:
    """Renders the interactive question panel and controls."""
    current_phase = TrainerEngine.get_current_phase()
    active_item = TrainerEngine.get_active_item()
    mastery_score = st.session_state.mastery_map[active_item.prompt]

    # Progress Indicators
    stars = "★" * mastery_score + "☆" * (MASTERY_GOAL - mastery_score)
    st.markdown(f"#### 📍 當前進度：`{current_phase.name}`")
    st.markdown(f"**項目熟練度：** `{stars}` (目標: 連續 {MASTERY_GOAL} 次正確)")

    # Dynamic Font Size Adjustments for Multi-syllable Words
    is_word = len(active_item.prompt) > 1
    font_size_px = 72 if is_word else 100

    # Meaning container for Phase 4 vocabulary
    meaning_html = (
        f"<div style='font-size: 20px; color: #6c757d; margin-top: 8px;'>中文意義：<b>{active_item.meaning}</b></div>"
        if active_item.meaning
        else ""
    )

    st.markdown(
        f"""
        <div style="background-color: #ffffff; border-radius: 12px; padding: 24px; margin: 16px 0; text-align: center; border: 2px solid #e9ecef; box-shadow: 0 4px 6px rgba(0,0,0,0.04);">
            <div style="font-size: {font_size_px}px; font-weight: bold; color: #1e293b; font-family: 'Apple SD Gothic Neo', 'Malgun Gothic', sans-serif;">
                {active_item.prompt}
            </div>
            {meaning_html}
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Audio Playback
    render_audio_controller(
        text=active_item.prompt,
        auto_play=st.session_state.trigger_audio
    )
    st.session_state.trigger_audio = False

    # Form Submission Input
    st.text_input(
        "請輸入羅馬拼音並按 Enter 送出：",
        key="user_text_input",
        on_change=TrainerEngine.process_answer
    )

    # Secondary Action Buttons
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🔊 重新播放發音", use_container_width=True):
            st.session_state.trigger_audio = True
            st.rerun()
    with col2:
        st.button(
            "⏭️ 跳過此題",
            on_click=TrainerEngine.skip_current_item,
            use_container_width=True
        )

    # Notification Message Banner
    if st.session_state.feedback_msg:
        if st.session_state.feedback_type == "success":
            st.success(st.session_state.feedback_msg)
        elif st.session_state.feedback_type == "error":
            st.error(st.session_state.feedback_msg)
        else:
            st.info(st.session_state.feedback_msg)


def main() -> None:
    """Application entry point."""
    st.set_page_config(
        page_title="韓文 40 音與基礎單字訓練系統",
        page_icon="🇰🇷",
        layout="centered"
    )

    TrainerEngine.initialize_state()

    st.title("🇰🇷 韓文 40 音 ＆ 基礎單字訓練系統")

    with st.expander("ℹ️ 課程說明與聲音故障排查", expanded=False):
        st.markdown(
            """
            - **課程階段規劃**：
              1. **Phase 1**：單母音與基礎子音（共 16 音）
              2. **Phase 2**：衍生母音、激音與雙子音（共 13 音）
              3. **Phase 3**：複合母音（共 11 音）
              4. **Phase 4**：基礎實用單字（共 16 組核心詞彙）
            - **發音無聲排查**：
              1. 行動裝置（如 iPhone）請關閉左側**實體靜音開關**並調大媒體音量。
              2. 若瀏覽器自動播放被阻擋，可直接點擊發音控制列上的播放鈕。
            """
        )

    if st.session_state.curriculum_complete:
        render_completion_view()
    else:
        render_practice_view()


if __name__ == "__main__":
    main()