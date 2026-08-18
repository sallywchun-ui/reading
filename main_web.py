"""Korean 40-sound web trainer with robust audio playback for Streamlit.

This module implements a web-based Hangul trainer featuring multi-phase
progression, dynamic text-to-speech audio streaming via gTTS, and an
autoplay-compliant audio delivery architecture designed to bypass modern
browser media engagement restrictions safely.

Typical usage example:
    streamlit run main_web.py
"""

from __future__ import annotations

import base64
import io
import logging
import random
from typing import Dict, Final, List, Optional

import streamlit as st
from gtts import gTTS
from gtts.tts import gTTSError

# Configure module-level logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger(__name__)

# --- Domain Constants and Curriculum Data ---

MASTERY_GOAL: Final[int] = 3

PHASE_DATA: Final[Dict[str, Dict[str, str]]] = {
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

PHASE_ORDER: Final[List[str]] = list(PHASE_DATA.keys())


# --- Audio Generation and Serialization Service ---

@st.cache_data(show_spinner=False, ttl=None)
def get_tts_audio_bytes(text: str) -> Optional[bytes]:
    """Synthesizes Korean speech audio using gTTS with process-level caching.

    Args:
        text: Single Korean Hangul character or phrase to synthesize.

    Returns:
        Raw MP3 bytes upon success, or None if network/API errors occur.
    """
    try:
        buffer = io.BytesIO()
        tts = gTTS(text=text, lang="ko", slow=False)
        tts.write_to_fp(buffer)
        return buffer.getvalue()
    except gTTSError as exc:
        logger.error("gTTS API failure for character '%s': %s", text, exc)
        return None
    except (ConnectionError, OSError, TimeoutError) as exc:
        logger.error("Network connectivity issue synthesizing '%s': %s", text, exc)
        return None


def render_audio_controller(text: str, auto_play: bool = True) -> None:
    """Renders robust audio playback using Web Audio API and Fallback controls.

    Embeds a resilient JavaScript snippet that attempts programmatic playback
    via Base64 Data URI. If blocked by browser autoplay policies, it logs
    a non-intrusive warning and falls back to user interaction.

    Args:
        text: The Korean character to pronounce.
        auto_play: Whether to attempt automatic audio playback.

    Returns:
        None. Renders HTML/JS directly into Streamlit DOM.
    """
    audio_bytes = get_tts_audio_bytes(text)
    if audio_bytes is None:
        st.warning("⚠️ 語音服務暫時無法連線，請依字形練習。")
        return

    encoded_audio = base64.b64encode(audio_bytes).decode("utf-8")
    audio_id = f"audio_{abs(hash(text))}_{random.randint(1000, 9999)}"

    # Embedded HTML5 with explicit play Promise handling
    audio_html = f"""
    <div style="margin-top: 10px; margin-bottom: 10px; text-align: center;">
        <audio id="{audio_id}" preload="auto" controls style="width: 100%; max-width: 320px; height: 36px;">
            <source src="data:audio/mpeg;base64,{encoded_audio}" type="audio/mpeg">
            您的瀏覽器不支援 Audio 標籤。
        </audio>
    </div>
    <script>
        (function() {{
            const audioEl = document.getElementById("{audio_id}");
            if (!audioEl) return;

            // Ensure audio element volume is normalized
            audioEl.volume = 1.0;

            const shouldAutoPlay = {str(auto_play).lower()};
            if (shouldAutoPlay) {{
                const playPromise = audioEl.play();
                if (playPromise !== undefined) {{
                    playPromise.catch(function(error) {{
                        console.warn("Autoplay blocked by browser policy: ", error);
                        // Browser blocked autoplay; fallback to user manual click
                    }});
                }}
            }}
        }})();
    </script>
    """
    st.components.v1.html(audio_html, height=55)


# --- State Management & Curriculum Progression ---

def initialize_session_state() -> None:
    """Initializes default variables in Streamlit session_state safely.

    Args:
        None.

    Returns:
        None.
    """
    if "is_initialized" not in st.session_state:
        st.session_state.is_initialized = True
        st.session_state.data = PHASE_DATA
        st.session_state.mastery = {
            char: 0 for phase in PHASE_DATA.values() for char in phase
        }
        st.session_state.current_phase = PHASE_ORDER[0]
        st.session_state.target_char = random.choice(
            list(PHASE_DATA[PHASE_ORDER[0]].keys())
        )
        st.session_state.feedback_msg = ""
        st.session_state.feedback_type = "info"
        st.session_state.trigger_audio = True
        st.session_state.curriculum_finished = False


def check_phase_completion(phase_name: str) -> bool:
    """Evaluates if every character in the given phase meets MASTERY_GOAL.

    Args:
        phase_name: Name of the phase key to validate.

    Returns:
        True if all characters in the phase are mastered, False otherwise.
    """
    phase_characters = st.session_state.data[phase_name]
    return all(
        st.session_state.mastery[char] >= MASTERY_GOAL
        for char in phase_characters
    )


def select_next_character(phase_name: str, exclude_char: Optional[str] = None) -> str:
    """Selects an unmastered or randomized character avoiding direct repetition.

    Args:
        phase_name: Name of the phase.
        exclude_char: The character that was just shown (to prevent consecutive duplicates).

    Returns:
        A selected Hangul character string.
    """
    candidates = list(st.session_state.data[phase_name].keys())
    
    # Filter candidates that still need mastery
    unmastered = [c for c in candidates if st.session_state.mastery[c] < MASTERY_GOAL]
    pool = unmastered if unmastered else candidates

    if exclude_char and len(pool) > 1:
        pool = [c for c in pool if c != exclude_char]

    return random.choice(pool)


def advance_phase() -> bool:
    """Advances session state to the next phase index.

    Args:
        None.

    Returns:
        True if successfully advanced, False if all phases are completed.
    """
    current_idx = PHASE_ORDER.index(st.session_state.current_phase)
    next_idx = current_idx + 1

    if next_idx >= len(PHASE_ORDER):
        return False

    st.session_state.current_phase = PHASE_ORDER[next_idx]
    st.session_state.target_char = select_next_character(PHASE_ORDER[next_idx])
    return True


def submit_answer_callback() -> None:
    """Evaluates the learner's answer and updates mastery scoring.

    Args:
        None. Reads from `st.session_state.user_answer_input`.

    Returns:
        None.
    """
    current_phase = st.session_state.current_phase
    target_char = st.session_state.target_char
    correct_answer = st.session_state.data[current_phase][target_char]
    raw_input = st.session_state.get("user_answer_input", "").strip().lower()

    if raw_input == correct_answer:
        st.session_state.mastery[target_char] += 1
        st.session_state.feedback_msg = f"✅ 正確！【{target_char}】= {correct_answer}"
        st.session_state.feedback_type = "success"
    else:
        st.session_state.mastery[target_char] = 0
        st.session_state.feedback_msg = (
            f"❌ 答錯了！【{target_char}】的正確拼音是：{correct_answer}（已重置熟練度）"
        )
        st.session_state.feedback_type = "error"

    if check_phase_completion(current_phase):
        if advance_phase():
            st.session_state.feedback_msg = (
                f"🏆 恭喜！{current_phase} 已達標！進入下一階段：{st.session_state.current_phase}"
            )
            st.session_state.feedback_type = "success"
        else:
            st.session_state.curriculum_finished = True
            st.session_state.feedback_msg = "🎉 恭喜完成韓文 40 音所有階段！"
            st.session_state.feedback_type = "success"
    else:
        st.session_state.target_char = select_next_character(
            current_phase, exclude_char=target_char
        )

    # Clean input box and trigger audio playback
    st.session_state.user_answer_input = ""
    st.session_state.trigger_audio = True


def skip_question_callback() -> None:
    """Skips the active character without penalizing learner mastery.

    Args:
        None.

    Returns:
        None.
    """
    st.session_state.target_char = select_next_character(
        st.session_state.current_phase,
        exclude_char=st.session_state.target_char
    )
    st.session_state.feedback_msg = "⏭️ 已跳過當前題目，熟練度不受影響。"
    st.session_state.feedback_type = "info"
    st.session_state.user_answer_input = ""
    st.session_state.trigger_audio = True


# --- View Presentation Layer ---

def render_completion_view() -> None:
    """Renders the final congratulatory screen upon curriculum completion."""
    st.balloons()
    st.success("🎉 太棒了！您已經完全掌握韓文 40 音所有字元發音！")
    if st.button("🔄 重新開始練習", use_container_width=True):
        st.session_state.clear()
        st.rerun()


def render_practice_view() -> None:
    """Renders active training user interface and input forms."""
    target_char = st.session_state.target_char
    current_phase = st.session_state.current_phase
    current_mastery = st.session_state.mastery[target_char]

    # Progress visualizer
    stars = "★" * current_mastery + "☆" * (MASTERY_GOAL - current_mastery)
    
    st.markdown(f"#### 📍 當前進度：`{current_phase}`")
    st.markdown(f"**字元熟練度：** `{stars}` (目標: {MASTERY_GOAL} 次連續正確)")

    # Large character display
    st.markdown(
        f"""
        <div style="background-color: #f8f9fa; border-radius: 12px; padding: 20px; margin: 15px 0; text-align: center; border: 1px solid #e9ecef;">
            <span style="font-size: 96px; font-weight: bold; color: #212529; font-family: 'Apple SD Gothic Neo', 'Malgun Gothic', sans-serif;">
                {target_char}
            </span>
        </div>
        """,
        unsafe_allow_html=True
    )

    # Audio playback element
    render_audio_controller(
        text=target_char,
        auto_play=st.session_state.trigger_audio
    )
    st.session_state.trigger_audio = False

    # Input and Action Section
    st.text_input(
        "請輸入羅馬拼音並按 Enter 送出：",
        key="user_answer_input",
        on_change=submit_answer_callback
    )

    col1, col2 = st.columns(2)
    with col1:
        if st.button("🔊 再次播放發音", use_container_width=True):
            st.session_state.trigger_audio = True
            st.rerun()
    with col2:
        st.button("⏭️ 跳過此題", on_click=skip_question_callback, use_container_width=True)

    # Feedback Notification
    if st.session_state.feedback_msg:
        if st.session_state.feedback_type == "success":
            st.success(st.session_state.feedback_msg)
        elif st.session_state.feedback_type == "error":
            st.error(st.session_state.feedback_msg)
        else:
            st.info(st.session_state.feedback_msg)


def main() -> None:
    """Application entry point configuring page layout and rendering lifecycle."""
    st.set_page_config(
        page_title="韓文 40 音發音即時測驗系統",
        page_icon="🔊",
        layout="centered"
    )

    initialize_session_state()

    st.title("🔊 韓文 40 音發音訓練系統")

    with st.expander("🛠️ 發音無法播放？聲音排查指南", expanded=False):
        st.markdown(
            """
            - **iOS / iPhone 裝置**：
              1. 請確認左側 **實體靜音切換鍵** 未撥至靜音（未露出橘紅色標記）。
              2. 請確認「控制中心」之 **媒體音量** 已調大（非僅通話鈴聲）。
              3. Safari 預設禁止網頁無互動自動播放，請直接點擊音訊播放列的 **Play 按鈕**。
            - **桌面版 Chrome / Edge / Safari**：
              1. 瀏覽器若禁止自動發音，請點擊畫面中的 **「🔊 再次播放發音」** 授權音訊權限。
              2. 檢查分頁標籤是否被瀏覽器設定為「靜音網站」。
            """
        )

    if st.session_state.curriculum_finished:
        render_completion_view()
    else:
        render_practice_view()


if __name__ == "__main__":
    main()