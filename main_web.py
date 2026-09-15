"""Korean Learning App: 40-Sound Trainer + 세종한국어 1A Textbook Lessons.

This module is the single Streamlit entry point for two learning modes,
picked from the sidebar:
1. 40음 · 단어 트레이너 (this module): an interactive trainer for the 40
   Korean Hangul characters and Phase 4 vocabulary, with three learning
   dimensions:
     a. Standard Romanization Typing (Look at Hangul -> Type Romanization)
     b. Listen & Type (Listen to audio -> Type Hangul character)
     c. Multiple Choice (Look at Hangul -> Select correct Chinese meaning)
2. 교재 학습 (세종한국어 1A) (lessons/textbook_app.py): vocabulary, grammar,
   dialogue, and quiz tabs for lessons 1-10 of the 세종한국어 1A textbook.
3. 타자 연습 (lessons/typing_practice.py): a 두벌식 (2-beolsik) keyboard-layout
   reference plus a short-sentence Korean typing drill with diff/accuracy/
   speed feedback.

Typical usage example:
    streamlit run main_web.py
"""

from __future__ import annotations

import base64
import enum
import io
import logging
import random
from dataclasses import dataclass
from typing import Dict, Final, List, Optional

import streamlit as st
from gtts import gTTS
from gtts.tts import gTTSError

from lessons.textbook_app import render_textbook_mode
from lessons.typing_practice import render_typing_mode

# Module-level logging setup
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger(__name__)

# --- Domain Constants ---
MASTERY_GOAL: Final[int] = 3


# --- Domain Enums & Entities ---

class AppMode(str, enum.Enum):
    """Enumeration of the top-level learning modes offered in the sidebar."""
    SOUND_TRAINER = "40음 · 단어 트레이너 (40音與單字測驗)"
    TEXTBOOK_LESSONS = "교재 학습 (세종한국어 1A 教材課程)"
    TYPING_PRACTICE = "타자 연습 (韓文打字練習)"


class ExerciseMode(str, enum.Enum):
    """Enumeration of available training dimensions."""
    ROMAJA_INPUT = "看字拼音 (Type Romanization)"
    LISTEN_AND_TYPE = "聽音辨字 (Listen & Type Hangul)"
    MULTIPLE_CHOICE = "看字選義 (Multiple Choice: Meaning)"


@dataclass(frozen=True)
class StudyItem:
    """Represents a single learning unit (character or vocabulary word).

    Attributes:
        prompt: The Hangul character or word.
        romanization: Standard Romanized transcription.
        meaning: Optional Chinese translation.
    """
    prompt: str
    romanization: str
    meaning: Optional[str] = None


@dataclass(frozen=True)
class Phase:
    """Represents a discrete curriculum stage containing study items.

    Attributes:
        name: Display name of the phase.
        items: List of StudyItem objects contained in this phase.
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
            StudyItem(prompt="ㅏ", romanization="a", meaning="母音 a"),
            StudyItem(prompt="ㅓ", romanization="eo", meaning="母音 eo"),
            StudyItem(prompt="ㅗ", romanization="o", meaning="母音 o"),
            StudyItem(prompt="ㅜ", romanization="u", meaning="母音 u"),
            StudyItem(prompt="ㅡ", romanization="eu", meaning="母音 eu"),
            StudyItem(prompt="ㅣ", romanization="i", meaning="母音 i"),
            StudyItem(prompt="ㄱ", romanization="g", meaning="子音 g/k"),
            StudyItem(prompt="ㄴ", romanization="n", meaning="子音 n"),
            StudyItem(prompt="ㄷ", romanization="d", meaning="子音 d/t"),
            StudyItem(prompt="ㄹ", romanization="r", meaning="子音 r/l"),
            StudyItem(prompt="ㅁ", romanization="m", meaning="子音 m"),
            StudyItem(prompt="ㅂ", romanization="b", meaning="子音 b/p"),
            StudyItem(prompt="ㅅ", romanization="s", meaning="子音 s"),
            StudyItem(prompt="ㅇ", romanization="ng", meaning="子音 silent/ng"),
            StudyItem(prompt="ㅈ", romanization="j", meaning="子音 j/ch"),
            StudyItem(prompt="ㅎ", romanization="h", meaning="子音 h"),
        ],
    ),
    Phase(
        name="Phase 2: 衍生/激音/雙子音 (Derived, Aspirated & Tense)",
        items=[
            StudyItem(prompt="ㅑ", romanization="ya", meaning="母音 ya"),
            StudyItem(prompt="ㅕ", romanization="yeo", meaning="母音 yeo"),
            StudyItem(prompt="ㅛ", romanization="yo", meaning="母音 yo"),
            StudyItem(prompt="ㅠ", romanization="yu", meaning="母音 yu"),
            StudyItem(prompt="ㅋ", romanization="k", meaning="激音 k"),
            StudyItem(prompt="ㅌ", romanization="t", meaning="激音 t"),
            StudyItem(prompt="ㅍ", romanization="p", meaning="激音 p"),
            StudyItem(prompt="ㅊ", romanization="ch", meaning="激音 ch"),
            StudyItem(prompt="ㄲ", romanization="kk", meaning="雙子音 kk"),
            StudyItem(prompt="ㄸ", romanization="tt", meaning="雙子音 tt"),
            StudyItem(prompt="ㅃ", romanization="pp", meaning="雙子音 pp"),
            StudyItem(prompt="ㅆ", romanization="ss", meaning="雙子音 ss"),
            StudyItem(prompt="ㅉ", romanization="jj", meaning="雙子音 jj"),
        ],
    ),
    Phase(
        name="Phase 3: 複合母音 (Compound Vowels)",
        items=[
            StudyItem(prompt="ㅐ", romanization="ae", meaning="複合母音 ae"),
            StudyItem(prompt="ㅒ", romanization="yae", meaning="複合母音 yae"),
            StudyItem(prompt="ㅔ", romanization="e", meaning="複合母音 e"),
            StudyItem(prompt="ㅖ", romanization="ye", meaning="複合母音 ye"),
            StudyItem(prompt="ㅘ", romanization="wa", meaning="複合母音 wa"),
            StudyItem(prompt="ㅙ", romanization="wae", meaning="複合母音 wae"),
            StudyItem(prompt="ㅚ", romanization="oe", meaning="複合母音 oe"),
            StudyItem(prompt="ㅝ", romanization="wo", meaning="複合母音 wo"),
            StudyItem(prompt="ㅞ", romanization="we", meaning="複合母音 we"),
            StudyItem(prompt="ㅟ", romanization="wi", meaning="複合母音 wi"),
            StudyItem(prompt="ㅢ", romanization="ui", meaning="複合母音 ui"),
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


# --- Text-to-Speech Engine ---

@st.cache_data(show_spinner=False, ttl=None)
def get_tts_audio_bytes(text: str) -> Optional[bytes]:
    """Synthesizes Korean audio using gTTS with caching.

    Args:
        text: The Korean text to speak.

    Returns:
        MP3 audio bytes on success, or None on failure.
    """
    try:
        buffer = io.BytesIO()
        tts = gTTS(text=text, lang="ko", slow=False)
        tts.write_to_fp(buffer)
        return buffer.getvalue()
    except gTTSError as exc:
        logger.error("gTTS API error for text '%s': %s", text, exc)
        return None
    except (ConnectionError, OSError, TimeoutError) as exc:
        logger.error("Network error during TTS generation for '%s': %s", text, exc)
        return None


def render_audio_controller(text: str, auto_play: bool = True) -> None:
    """Renders HTML5 audio element with automatic play fallback.

    Args:
        text: The Korean character or word to pronounce.
        auto_play: Whether to trigger automatic playback via JS.

    Returns:
        None.
    """
    audio_bytes = get_tts_audio_bytes(text)
    if audio_bytes is None:
        st.warning("⚠️ 語音服務暫時無法連線。")
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
                        console.warn("Autoplay blocked: ", err);
                    }});
                }}
            }}
        }})();
    </script>
    """
    st.components.v1.html(audio_html, height=52)


# --- Core Progression and Domain Engine ---

class TrainerEngine:
    """Encapsulates test grading, question generation, and progression logic."""

    @staticmethod
    def initialize_state() -> None:
        """Initializes session state keys."""
        if "trainer_initialized" in st.session_state:
            return

        st.session_state.trainer_initialized = True
        st.session_state.current_phase_idx = 0
        st.session_state.active_mode = ExerciseMode.ROMAJA_INPUT.value

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
        st.session_state.choice_options = []

    @classmethod
    def get_current_phase(cls) -> Phase:
        """Retrieves active Phase."""
        idx = st.session_state.current_phase_idx
        return CURRICULUM[idx]

    @classmethod
    def get_active_item(cls) -> StudyItem:
        """Retrieves currently targeted StudyItem."""
        phase = cls.get_current_phase()
        prompt = st.session_state.target_prompt
        return phase.item_map[prompt]

    @classmethod
    def is_phase_mastered(cls, phase: Phase) -> bool:
        """Checks whether all items in phase have reached the mastery goal."""
        return all(
            st.session_state.mastery_map[item.prompt] >= MASTERY_GOAL
            for item in phase.items
        )

    @classmethod
    def pick_next_prompt(cls, phase: Phase, exclude_prompt: Optional[str] = None) -> str:
        """Selects next prompt prioritizing unmastered items."""
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
    def generate_choice_options(cls, active_item: StudyItem, phase: Phase) -> List[str]:
        """Generates 4 unique choices for multiple choice mode."""
        correct_meaning = active_item.meaning or active_item.romanization
        other_items = [item for item in phase.items if item.prompt != active_item.prompt]
        
        # Sample 3 distractors
        num_distractors = min(3, len(other_items))
        sampled = random.sample(other_items, num_distractors)
        distractor_meanings = [item.meaning or item.romanization for item in sampled]
        
        options = [correct_meaning] + distractor_meanings
        random.shuffle(options)
        return options

    @classmethod
    def advance_phase_or_finish(cls) -> None:
        """Advances to the next phase or marks curriculum completion."""
        next_idx = st.session_state.current_phase_idx + 1
        if next_idx >= len(CURRICULUM):
            st.session_state.curriculum_complete = True
            st.session_state.feedback_msg = "🎉 恭喜！您已成功通過全階段測驗！"
            st.session_state.feedback_type = "success"
        else:
            st.session_state.current_phase_idx = next_idx
            new_phase = CURRICULUM[next_idx]
            st.session_state.target_prompt = cls.pick_next_prompt(new_phase)
            st.session_state.feedback_msg = f"🏆 晉級成功！進入【{new_phase.name}】"
            st.session_state.feedback_type = "success"
            # Refresh choice options for new item
            st.session_state.choice_options = cls.generate_choice_options(
                cls.get_active_item(), new_phase
            )

    @classmethod
    def evaluate_submission(cls, submitted_answer: str) -> None:
        """Evaluates submitted answer against the expected response for active mode.

        Args:
            submitted_answer: Raw string submitted by text input or choice button.

        Returns:
            None. Mutates st.session_state.
        """
        active_item = cls.get_active_item()
        mode = st.session_state.active_mode
        user_ans = submitted_answer.strip()

        # Determine expected answer and match logic based on active mode
        if mode == ExerciseMode.ROMAJA_INPUT.value:
            is_correct = (user_ans.lower() == active_item.romanization.strip().lower())
            expected_display = active_item.romanization
        elif mode == ExerciseMode.LISTEN_AND_TYPE.value:
            is_correct = (user_ans == active_item.prompt.strip())
            expected_display = active_item.prompt
        elif mode == ExerciseMode.MULTIPLE_CHOICE.value:
            expected_meaning = active_item.meaning or active_item.romanization
            is_correct = (user_ans == expected_meaning)
            expected_display = expected_meaning
        else:
            is_correct = False
            expected_display = ""

        meaning_text = f"（{active_item.meaning}）" if active_item.meaning else ""

        if is_correct:
            st.session_state.mastery_map[active_item.prompt] += 1
            st.session_state.feedback_msg = (
                f"✅ 正確！【{active_item.prompt}】= {active_item.romanization} {meaning_text}"
            )
            st.session_state.feedback_type = "success"
        else:
            st.session_state.mastery_map[active_item.prompt] = 0
            st.session_state.feedback_msg = (
                f"❌ 錯誤！正確答案為：{expected_display}（字元：{active_item.prompt}，熟練度已重置）"
            )
            st.session_state.feedback_type = "error"

        current_phase = cls.get_current_phase()
        if cls.is_phase_mastered(current_phase):
            cls.advance_phase_or_finish()
        else:
            st.session_state.target_prompt = cls.pick_next_prompt(
                current_phase, exclude_prompt=active_item.prompt
            )
            # Update options for next question
            st.session_state.choice_options = cls.generate_choice_options(
                cls.get_active_item(), current_phase
            )

        st.session_state.user_text_input = ""
        st.session_state.trigger_audio = True

    @classmethod
    def skip_current_item(cls) -> None:
        """Skips the active item without penalizing mastery score."""
        current_phase = cls.get_current_phase()
        current_prompt = st.session_state.target_prompt
        st.session_state.target_prompt = cls.pick_next_prompt(
            current_phase, exclude_prompt=current_prompt
        )
        st.session_state.feedback_msg = "⏭️ 已跳過當前題目，熟練度保持不變。"
        st.session_state.feedback_type = "info"
        st.session_state.user_text_input = ""
        st.session_state.trigger_audio = True
        st.session_state.choice_options = cls.generate_choice_options(
            cls.get_active_item(), current_phase
        )


# --- View Presentation Layer ---

def render_completion_view() -> None:
    """Renders final congratulatory interface."""
    st.balloons()
    st.success("🏆 恭喜！您已成功在多維度測驗模式下完成所有階段！")
    if st.button("🔄 重新開始完整練習", use_container_width=True):
        st.session_state.clear()
        st.rerun()


def render_practice_view() -> None:
    """Renders active question display, audio playback, and dynamic inputs."""
    current_phase = TrainerEngine.get_current_phase()
    active_item = TrainerEngine.get_active_item()
    mastery_score = st.session_state.mastery_map[active_item.prompt]
    mode = st.session_state.active_mode

    # Ensure choice options exist
    if not st.session_state.choice_options:
        st.session_state.choice_options = TrainerEngine.generate_choice_options(
            active_item, current_phase
        )

    # Progress and Mode Selector
    stars = "★" * mastery_score + "☆" * (MASTERY_GOAL - mastery_score)
    st.markdown(f"#### 📍 當前階段：`{current_phase.name}`")
    st.markdown(f"**熟練度：** `{stars}` (目標: 連續 {MASTERY_GOAL} 次正確)")

    # Prompt Card Rendering
    if mode == ExerciseMode.LISTEN_AND_TYPE.value:
        display_html = """
        <div style="font-size: 64px; color: #adb5bd; font-weight: bold;">
            🎧 請聽音辨字
        </div>
        <div style="font-size: 16px; color: #6c757d; margin-top: 8px;">
            (字元已隱藏，請輸入聽到的韓文字)
        </div>
        """
    else:
        is_word = len(active_item.prompt) > 1
        font_size_px = 72 if is_word else 100
        display_html = f"""
        <div style="font-size: {font_size_px}px; font-weight: bold; color: #1e293b; font-family: 'Apple SD Gothic Neo', 'Malgun Gothic', sans-serif;">
            {active_item.prompt}
        </div>
        """

    st.markdown(
        f"""
        <div style="background-color: #ffffff; border-radius: 12px; padding: 24px; margin: 16px 0; text-align: center; border: 2px solid #e9ecef; box-shadow: 0 4px 6px rgba(0,0,0,0.04);">
            {display_html}
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Audio Engine
    render_audio_controller(
        text=active_item.prompt,
        auto_play=st.session_state.trigger_audio
    )
    st.session_state.trigger_audio = False

    # Dynamic Input Form Dispatch
    if mode == ExerciseMode.ROMAJA_INPUT.value:
        st.text_input(
            "請輸入羅馬拼音並按 Enter：",
            key="user_text_input",
            on_change=lambda: TrainerEngine.evaluate_submission(st.session_state.user_text_input)
        )
    elif mode == ExerciseMode.LISTEN_AND_TYPE.value:
        st.text_input(
            "請輸入聽到的韓文字（Hangul）並按 Enter：",
            key="user_text_input",
            on_change=lambda: TrainerEngine.evaluate_submission(st.session_state.user_text_input)
        )
    elif mode == ExerciseMode.MULTIPLE_CHOICE.value:
        st.markdown("**請選擇正確的中文意義或發音：**")
        cols = st.columns(2)
        for idx, option in enumerate(st.session_state.choice_options):
            col_target = cols[idx % 2]
            if col_target.button(
                f"{idx + 1}. {option}",
                key=f"choice_btn_{idx}_{option}",
                use_container_width=True
            ):
                TrainerEngine.evaluate_submission(option)
                st.rerun()

    # Action Controls
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🔊 重播語音", use_container_width=True):
            st.session_state.trigger_audio = True
            st.rerun()
    with col2:
        st.button(
            "⏭️ 跳過此題",
            on_click=TrainerEngine.skip_current_item,
            use_container_width=True
        )

    # Feedback Alerts
    if st.session_state.feedback_msg:
        if st.session_state.feedback_type == "success":
            st.success(st.session_state.feedback_msg)
        elif st.session_state.feedback_type == "error":
            st.error(st.session_state.feedback_msg)
        else:
            st.info(st.session_state.feedback_msg)


def main() -> None:
    """Application entry point.

    Renders the sidebar's top-level mode switch first, then dispatches to
    either the textbook lesson mode (lessons.textbook_app) or the 40-sound
    trainer implemented in the rest of this module.
    """
    st.set_page_config(
        page_title="韓文學習系統 · 40音與세종한국어 1A教材",
        page_icon="🇰🇷",
        layout="centered"
    )

    st.sidebar.markdown("### 🇰🇷 韓文學習")
    app_mode = st.sidebar.radio(
        "학습 모드 선택 (選擇學習模式)",
        [m.value for m in AppMode],
        label_visibility="collapsed",
    )
    st.sidebar.divider()

    if app_mode == AppMode.TEXTBOOK_LESSONS.value:
        render_textbook_mode()
        return

    if app_mode == AppMode.TYPING_PRACTICE.value:
        render_typing_mode()
        return

    TrainerEngine.initialize_state()

    st.title("🇰🇷 韓文 40 音多維度測驗系統")

    # Mode Selector
    modes = [m.value for m in ExerciseMode]
    current_mode_idx = modes.index(st.session_state.active_mode)
    selected_mode = st.selectbox(
        "🎯 選擇測驗維度：",
        options=modes,
        index=current_mode_idx
    )
    if selected_mode != st.session_state.active_mode:
        st.session_state.active_mode = selected_mode
        st.session_state.choice_options = TrainerEngine.generate_choice_options(
            TrainerEngine.get_active_item(),
            TrainerEngine.get_current_phase()
        )
        st.rerun()

    with st.expander("ℹ️ 題型說明與聲音故障排查", expanded=False):
        st.markdown(
            """
            - **三大測驗維度**：
              1. **看字拼音**：依據畫面的韓文字母/單字輸入對應的羅馬拼音。
              2. **聽音辨字**：隱藏字形，僅透過語音播放，直接在鍵盤輸入對應的韓文字（Hangul）。
              3. **看字選義**：適合單字與音標記憶，提供 4 選 1 中文語義選擇題。
            - **發音無聲排查**：
              - 行動裝置請關閉實體靜音開關並調高媒體音量。
            """
        )

    if st.session_state.curriculum_complete:
        render_completion_view()
    else:
        render_practice_view()


if __name__ == "__main__":
    main()