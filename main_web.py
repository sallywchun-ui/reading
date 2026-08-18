"""Korean 40-sound web trainer built with Streamlit.

This module implements an interactive Korean alphabet (Hangul) pronunciation
trainer. It supports multi-phase progression (auto-advance when a phase is
mastered), text-to-speech playback via gTTS with server-side caching, and a
skip action that does not penalize the learner's mastery progress.

Typical usage example:
    streamlit run main_web.py
"""

from __future__ import annotations

import base64
import io
import logging
import random
from dataclasses import dataclass
from typing import Dict, List, Optional

import streamlit as st
from gtts import gTTS
from gtts.tts import gTTSError

# Module-level logger setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- Application Configuration and Data ---
# Number of consecutive correct answers required to master a character.
MASTERY_GOAL: int = 3

# Immutable source-of-truth for all 40 Hangul learning phases.
PHASE_DATA: Dict[str, Dict[str, str]] = {
    "Phase 1: 基礎音 (Basic Vowels & Consonants)": {
        "ㅏ": "a", "ㅓ": "eo", "ㅗ": "o", "ㅜ": "u", "ㅡ": "eu", "ㅣ": "i",
        "ㄱ": "g", "ㄴ": "n", "ㄷ": "d", "ㄹ": "r", "ㅁ": "m", "ㅂ": "b",
        "ㅅ": "s", "ㅇ": "ng", "ㅈ": "j", "ㅎ": "h"
    },
    "Phase 2: 衍生/激音/雙子音 (Derived, Aspirated & Tense)": {
        "ㅑ": "ya", "ㅕ": "yeo", "ㅛ": "yo", "ㅠ": "yu",
        "ㅋ": "k", "ㅌ": "t", "ㅍ": "p", "ㅊ": "ch",
        "ㄲ": "kk", "ㄸ": "tt", "ㅃ": "pp", "ㅆ": "ss", "ㅉ": "jj"
    },
    "Phase 3: 複合母音 (Compound Vowels)": {
        "ㅐ": "ae", "ㅒ": "yae", "ㅔ": "e", "ㅖ": "ye", "ㅘ": "wa",
        "ㅙ": "wae", "ㅚ": "oe", "ㅝ": "wo", "ㅞ": "we", "ㅟ": "wi", "ㅢ": "ui"
    },
}

# Fixed traversal order of phases derived from PHASE_DATA.
PHASE_ORDER: List[str] = list(PHASE_DATA.keys())


# --- Text-to-Speech Service ---

@st.cache_data(show_spinner=False, ttl=None)
def get_tts_audio_bytes(text: str) -> Optional[bytes]:
    """Generates Korean speech audio bytes for a given character via gTTS.

    Results are cached per unique `text` value for the lifetime of the
    Streamlit process, eliminating redundant outbound network calls.

    Args:
        text: The Korean Hangul character or string to synthesize.

    Returns:
        The raw MP3 audio bytes on success, or None if speech synthesis
        failed due to network or service errors.

    Raises:
        None. All internal exceptions are logged and caught gracefully.
    """
    try:
        buffer = io.BytesIO()
        tts = gTTS(text=text, lang="ko", slow=False)
        tts.write_to_fp(buffer)
        return buffer.getvalue()
    except gTTSError as exc:
        logger.warning("gTTS service error while synthesizing '%s': %s", text, exc)
        return None
    except (ConnectionError, OSError) as exc:
        logger.warning("Network error while synthesizing '%s': %s", text, exc)
        return None


def render_audio_player(text: str) -> None:
    """Renders an autoplaying, hidden HTML5 audio element for the given text.

    Fetches cached TTS audio for `text` and embeds it as a Base64 data URI.

    Args:
        text: The Korean text to speak aloud.

    Returns:
        None.
    """
    audio_bytes = get_tts_audio_bytes(text)
    if audio_bytes is None:
        st.warning("⚠️ 語音服務暫時無法使用，請先自行記憶發音。")
        return

    encoded_audio = base64.b64encode(audio_bytes).decode("utf-8")
    audio_html = f"""
        <audio autoplay="true">
            <source src="data:audio/mpeg;base64,{encoded_audio}" type="audio/mpeg">
        </audio>
    """
    st.components.v1.html(audio_html, height=0)


# --- Core State Management Logic ---

def init_session_state() -> None:
    """Initializes all session state variables safely on first script execution.

    Args:
        None.

    Returns:
        None.
    """
    if "initialized" in st.session_state:
        return

    st.session_state.data = PHASE_DATA
    st.session_state.mastery = {
        char: 0 for phase in PHASE_DATA.values() for char in phase
    }
    st.session_state.current_phase = PHASE_ORDER[0]
    st.session_state.target_char = random.choice(
        list(PHASE_DATA[PHASE_ORDER[0]].keys())
    )
    st.session_state.msg = ""
    st.session_state.play_now = True
    st.session_state.all_complete = False
    st.session_state.initialized = True


def is_phase_complete(phase: str) -> bool:
    """Checks whether every character in a phase has reached the MASTERY_GOAL.

    Args:
        phase: The phase key identifier.

    Returns:
        True if all characters in the phase have mastery >= MASTERY_GOAL,
        False otherwise.
    """
    return all(
        st.session_state.mastery[char] >= MASTERY_GOAL
        for char in st.session_state.data[phase]
    )


def pick_random_char(phase: str, exclude: Optional[str] = None) -> str:
    """Selects a random character from the active phase avoiding immediate repeats.

    Args:
        phase: The current phase name.
        exclude: A character to exclude if other candidates exist.

    Returns:
        A selected Hangul character key.
    """
    candidates = list(st.session_state.data[phase].keys())
    if exclude is not None and len(candidates) > 1:
        candidates = [c for c in candidates if c != exclude]
    return random.choice(candidates)


def advance_to_next_phase() -> bool:
    """Advances the user progression state to the next phase in sequence.

    Args:
        None.

    Returns:
        True if advanced to the next phase, False if already at final phase.
    """
    current_index = PHASE_ORDER.index(st.session_state.current_phase)
    next_index = current_index + 1

    if next_index >= len(PHASE_ORDER):
        return False

    st.session_state.current_phase = PHASE_ORDER[next_index]
    st.session_state.target_char = pick_random_char(PHASE_ORDER[next_index])
    return True


def handle_answer() -> None:
    """Evaluates the user's input against the active Hangul character.

    Updates mastery counters, displays feedback, and manages phase transitions.

    Args:
        None. Reads from `st.session_state.user_input`.

    Returns:
        None.
    """
    current_phase = st.session_state.current_phase
    target_char = st.session_state.target_char
    correct_answer = st.session_state.data[current_phase][target_char]
    user_answer = st.session_state.user_input.strip().lower()

    if user_answer == correct_answer:
        st.session_state.mastery[target_char] += 1
        st.session_state.msg = "✅ 正確！"
    else:
        st.session_state.mastery[target_char] = 0
        st.session_state.msg = f"❌ 錯誤！答案是 {correct_answer}。"

    if is_phase_complete(current_phase):
        advanced = advance_to_next_phase()
        if advanced:
            st.session_state.msg = (
                f"🏆 {current_phase} 完成！已晉級至 "
                f"{st.session_state.current_phase}"
            )
        else:
            st.session_state.all_complete = True
            st.session_state.msg = "🎉 恭喜！所有階段皆已完成！"
    else:
        st.session_state.target_char = pick_random_char(
            current_phase, exclude=target_char
        )

    st.session_state.user_input = ""
    st.session_state.play_now = True


def handle_skip() -> None:
    """Skips the current question without resetting or mutating mastery score.

    Args:
        None.

    Returns:
        None.
    """
    st.session_state.target_char = pick_random_char(
        st.session_state.current_phase, exclude=st.session_state.target_char
    )
    st.session_state.msg = "⏭️ 已跳過，不影響熟練度。"
    st.session_state.user_input = ""
    st.session_state.play_now = True


# --- UI View Rendering Layer ---

def render_completion_screen() -> None:
    """Renders the final completion screen when all characters are mastered.

    Args:
        None.

    Returns:
        None.
    """
    st.balloons()
    st.success("🎉 恭喜你！40 音全部階段皆已達成熟練度！")
    st.write("你可以重新整理頁面以重新開始練習。")


def render_practice_screen() -> None:
    """Renders the interactive question, progress bar, audio, and input field.

    Args:
        None.

    Returns:
        None.
    """
    mastery_value = st.session_state.mastery[st.session_state.target_char]
    progress_bar = "★" * mastery_value + "☆" * (MASTERY_GOAL - mastery_value)

    st.caption(f"當前階段：{st.session_state.current_phase}")
    st.write(f"當前進度：{progress_bar}")
    st.markdown(
        f"<h1 style='text-align: center; font-size: 100px;'>"
        f"{st.session_state.target_char}</h1>",
        unsafe_allow_html=True,
    )

    if st.session_state.play_now:
        render_audio_player(st.session_state.target_char)
        st.session_state.play_now = False

    st.text_input(
        "輸入拼音並按 Enter：", key="user_input", on_change=handle_answer
    )

    if st.session_state.msg:
        st.info(st.session_state.msg)


def main() -> None:
    """Main application entry point.

    Args:
        None.

    Returns:
        None.
    """
    st.set_page_config(page_title="韓文 40 音：穩定音訊版", layout="centered")
    init_session_state()

    st.title("🔊 韓文 40 音練習系統")

    with st.expander("🔇 還是沒聲音？請檢查這裡"):
        st.write("1. **實體靜音鍵**：請確認 iPhone 左側開關沒有露出紅色。")
        st.write("2. **控制中心**：請將『媒體音量』調大（不是鈴聲聲量）。")
        st.write("3. **瀏覽器權限**：iOS 預設會阻擋自動播放，請務必先點擊下方的『啟動聲音』按鈕。")

    if st.session_state.all_complete:
        render_completion_screen()
        return

    col1, col2 = st.columns(2)
    with col1:
        if st.button("🚀 啟動/重播聲音", use_container_width=True):
            st.session_state.play_now = True
    with col2:
        st.button("⏭️ 跳過此題", use_container_width=True, on_click=handle_skip)

    render_practice_screen()


if __name__ == "__main__":
    main()