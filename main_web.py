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
from typing import Dict, List, Optional

import streamlit as st
from gtts import gTTS
from gtts.tts import gTTSError

# --- Module-level logger (visible in the terminal running `streamlit run`) ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- Constants ---
MASTERY_GOAL: int = 3
"""int: Number of consecutive correct answers required to master a character."""

PHASE_DATA: Dict[str, Dict[str, str]] = {
    "Phase 1: 單母音/子音": {
        "ㅏ": "a", "ㅓ": "eo", "ㅗ": "o", "ㅜ": "u", "ㅡ": "eu", "ㅣ": "i",
        "ㄱ": "g", "ㄴ": "n", "ㄷ": "d", "ㄹ": "r", "ㅁ": "m", "ㅂ": "b",
    },
    "Phase 2: 激音/雙子音": {
        "ㅋ": "k", "ㅌ": "t", "ㅍ": "p", "ㅊ": "ch", "ㅎ": "h",
        "ㄲ": "kk", "ㄸ": "tt", "ㅃ": "pp", "ㅆ": "ss", "ㅉ": "jj",
    },
    "Phase 3: 複合母音": {
        "ㅐ": "ae", "ㅒ": "yae", "ㅔ": "e", "ㅖ": "ye", "ㅘ": "wa",
        "ㅙ": "wae", "ㅚ": "oe", "ㅝ": "wo", "ㅞ": "we", "ㅟ": "wi", "ㅢ": "ui",
    },
}
"""Dict[str, Dict[str, str]]: Immutable source-of-truth for all learning phases.

Each outer key is a phase name; each inner dict maps a Hangul character to its
romanized pronunciation.
"""

PHASE_ORDER: List[str] = list(PHASE_DATA.keys())
"""List[str]: Fixed traversal order of phases, derived once from PHASE_DATA."""


# --- Text-to-Speech layer ---------------------------------------------------

@st.cache_data(show_spinner=False, ttl=None)
def get_tts_audio_bytes(text: str) -> Optional[bytes]:
    """Generates Korean speech audio bytes for a given character via gTTS.

    Results are cached per unique `text` value for the lifetime of the
    Streamlit process, so repeated playback of the same character never
    triggers a duplicate network call.

    Args:
        text: The Korean text (typically a single Hangul jamo) to synthesize.

    Returns:
        The raw MP3 audio bytes on success, or None if speech synthesis
        failed for any reason (network error, service error, etc.). Callers
        must handle the None case gracefully instead of assuming success.

    Raises:
        This function intentionally does not raise; all known failure modes
        are caught internally and logged, returning None instead. This keeps
        the calling UI code free of try/except boilerplate.
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

    Fetches (or reuses cached) TTS audio for `text` and embeds it as a
    Base64 data URI, avoiding any client-side network dependency on external
    TTS endpoints. If synthesis fails, shows a non-blocking warning instead
    of silently producing no sound.

    Args:
        text: The Korean text to speak aloud.

    Returns:
        None. Renders directly into the current Streamlit app via
        `st.components.v1.html` or `st.warning`.
    """
    audio_bytes = get_tts_audio_bytes(text)
    if audio_bytes is None:
        st.warning("⚠️ 語音服務暫時無法使用，請先靠自己的記憶作答，稍後會自動重試。")
        return

    encoded_audio = base64.b64encode(audio_bytes).decode("utf-8")
    audio_html = f"""
        <audio autoplay="true">
            <source src="data:audio/mpeg;base64,{encoded_audio}" type="audio/mpeg">
        </audio>
    """
    st.components.v1.html(audio_html, height=0)


# --- Session state management ------------------------------------------------

def init_session_state() -> None:
    """Initializes all Streamlit session_state keys used by this app.

    This is idempotent: if state already exists (e.g. on script rerun), it
    does nothing, preserving the learner's in-progress state.

    Args:
        None.

    Returns:
        None. Mutates `st.session_state` in place.
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
    """Checks whether every character in a phase has reached MASTERY_GOAL.

    Args:
        phase: The phase name to check, must be a key in `PHASE_DATA`.

    Returns:
        True if all characters in the phase have mastery >= MASTERY_GOAL,
        False otherwise.
    """
    return all(
        st.session_state.mastery[char] >= MASTERY_GOAL
        for char in st.session_state.data[phase]
    )


def pick_random_char(phase: str, exclude: Optional[str] = None) -> str:
    """Picks a random character from the given phase, avoiding immediate repeats.

    Args:
        phase: The phase name to draw a character from.
        exclude: A character to avoid picking again if the phase has more
            than one character available (prevents the same question
            appearing twice in a row).

    Returns:
        A Hangul character key from `st.session_state.data[phase]`.
    """
    candidates = list(st.session_state.data[phase].keys())
    if exclude is not None and len(candidates) > 1:
        candidates = [c for c in candidates if c != exclude]
    return random.choice(candidates)


def advance_to_next_phase() -> bool:
    """Advances the learner to the next phase in PHASE_ORDER, if any remains.

    Args:
        None.

    Returns:
        True if there was a next phase and the state was advanced to it.
        False if the current phase was already the last one (i.e. the
        entire curriculum is complete).
    """
    current_index = PHASE_ORDER.index(st.session_state.current_phase)
    next_index = current_index + 1

    if next_index >= len(PHASE_ORDER):
        return False

    st.session_state.current_phase = PHASE_ORDER[next_index]
    st.session_state.target_char = pick_random_char(PHASE_ORDER[next_index])
    return True


def handle_answer() -> None:
    """Callback for the answer text_input's on_change event.

    Grades the learner's input against the current target character, updates
    mastery, and either advances the phase (if just completed), moves to the
    next question within the phase, or marks the whole curriculum complete.

    Args:
        None. Reads `st.session_state.user_input` as the raw learner input.

    Returns:
        None. Mutates `st.session_state` in place.
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
    """Callback for the '跳過此題' (skip) button.

    Moves to a new question within the current phase WITHOUT judging the
    current input and WITHOUT modifying any mastery counters. This is the
    fix for the bug where skipping used to incorrectly zero out mastery.

    Args:
        None.

    Returns:
        None. Mutates `st.session_state` in place.
    """
    st.session_state.target_char = pick_random_char(
        st.session_state.current_phase, exclude=st.session_state.target_char
    )
    st.session_state.msg = "⏭️ 已跳過，不影響熟練度。"
    st.session_state.user_input = ""
    st.session_state.play_now = True


# --- Page rendering -----------------------------------------------------------

def render_completion_screen() -> None:
    """Renders the final congratulations screen once all phases are mastered.

    Args:
        None.

    Returns:
        None.
    """
    st.balloons()
    st.success("🎉 恭喜你！40 音全部階段皆已達成熟練度！")
    st.write("你可以重新整理頁面以重新開始練習。")


def render_practice_screen() -> None:
    """Renders the active practice UI: progress, character, audio, and input.

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
    """Application entry point: sets up the page and dispatches rendering.

    Args:
        None.

    Returns:
        None.
    """
    st.set_page_config(page_title="韓文 40 音：穩定音訊版", layout="centered")
    init_session_state()

    st.title("🔊 韓文 40 音")

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