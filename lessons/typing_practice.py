# -*- coding: utf-8 -*-
"""타자 연습 (Korean typing practice) — Streamlit learning module.

Shows a reference diagram of the standard 두벌식 (2-beolsik) Korean keyboard
layout, then lets the user practice typing a set of short beginner-level
Korean sentences: type the target sentence and press Enter to see a
character-by-character diff plus accuracy and typing-speed stats.

This module is designed to be imported by main_web.py rather than run
standalone: it exposes a single entry point, ``render_typing_mode()``, that
main_web.py calls when the user selects the typing-practice mode from its
sidebar.

This module intentionally does not call ``st.set_page_config()`` — that can
only be called once per app, and main_web.py owns it.

Standalone usage (for local development of this module only):
    pip install streamlit
    streamlit run lessons/typing_practice.py
"""

from __future__ import annotations

import html
import random
import time
from typing import List, Tuple

import streamlit as st

# =========================================================
# 0. 共用樣式（沿用教材模式的暗色系）
# =========================================================

CUSTOM_CSS = """
<style>
  @import url('https://fonts.googleapis.com/css2?family=Noto+Serif+KR:wght@500;700&family=Noto+Sans+KR:wght@400;500;700&display=swap');

  :root{
    --bg:#12161A; --paper:#1B2126; --paper-alt:#20272C; --ink:#E7ECE9; --ink-soft:#9AA7A0;
    --jade:#5FC9A8; --jade-soft:#17342C; --clay:#E98B6C; --clay-soft:#3A241C;
    --gold:#E8BB63; --gold-soft:#3A2E14; --gold-ink:#F0CE8C; --gold-line:#5A4A22;
    --line:#2B3339; --wrong:#E2685C;
  }
  .stApp{ background:var(--bg); }
  html, body, [class*="css"]{ font-family:"Noto Sans KR","Noto Serif KR",sans-serif; color:var(--ink); }

  [data-testid="stSidebar"]{ background:var(--paper); border-right:1px solid var(--line); }
  [data-testid="stSidebar"] *{ color:var(--ink); }
  .stButton>button{ background:var(--paper-alt); color:var(--ink); border:1px solid var(--line); }
  .stButton>button:hover{ border-color:var(--jade); color:var(--jade); }
  .stButton>button[kind="primary"]{ background:var(--jade); color:#0E1512; border:none; }
  .stButton>button[kind="primary"]:hover{ background:var(--jade); opacity:0.9; color:#0E1512; }
  [data-testid="stExpander"]{ background:var(--paper); border:1px solid var(--line); border-radius:6px; }
  [data-testid="stTextInput"] input{
    background:var(--paper-alt); color:var(--ink); border:1px solid var(--line);
    font-size:17px; padding:10px 14px;
  }
  [data-testid="stTextInput"] input:focus{ border-color:var(--jade); box-shadow:none; }
  [data-testid="stMetric"]{
    background:var(--paper); border:1px solid var(--line); border-radius:6px; padding:10px 14px;
  }

  .hero{
    background:var(--paper); border:1px solid var(--line); border-radius:6px;
    padding:26px 28px 22px; margin-bottom:16px;
  }
  .book-tag{ font-size:12px; color:var(--ink-soft); }
  .headline{
    font-family:"Noto Serif KR",serif; font-weight:700; font-size:28px;
    margin:6px 0 10px; color:var(--ink);
  }
  .goal-pill{
    display:inline-block; background:var(--gold-soft); border:1px solid var(--gold-line);
    color:var(--gold-ink); padding:6px 14px; border-radius:20px; font-size:13px;
  }

  /* --- 鍵盤參考圖 --- */
  .kb-wrap{ overflow-x:auto; padding:6px 2px 12px; }
  .kb-row{ display:flex; gap:6px; margin-bottom:6px; }
  .kb-row.indent-1{ margin-left:20px; }
  .kb-row.indent-2{ margin-left:40px; }
  .kb-key{
    position:relative; width:54px; height:54px; flex-shrink:0;
    background:var(--paper-alt); border:1px solid var(--line); border-radius:8px;
    display:flex; align-items:center; justify-content:center;
  }
  .kb-key.cons{ border-color:#5A3A2E; background:linear-gradient(180deg, var(--clay-soft), var(--paper-alt)); }
  .kb-key.vowel{ border-color:#2E4A3E; background:linear-gradient(180deg, var(--jade-soft), var(--paper-alt)); }
  .kb-key .letter{ position:absolute; top:4px; left:6px; font-size:9px; color:var(--ink-soft); }
  .kb-key .shift{ position:absolute; top:3px; right:5px; font-size:12px; font-weight:700; color:var(--gold); }
  .kb-key .base{
    font-family:"Noto Serif KR",serif; font-size:21px; font-weight:700;
    color:var(--ink); margin-top:6px;
  }
  .kb-key.cons .base{ color:var(--clay); }
  .kb-key.vowel .base{ color:var(--jade); }
  .kb-space{
    margin-top:2px; width:280px; max-width:90%; height:30px; background:var(--paper-alt);
    border:1px solid var(--line); border-radius:8px; display:flex; align-items:center;
    justify-content:center; font-size:11px; color:var(--ink-soft);
  }
  .kb-legend{ font-size:12.5px; color:var(--ink-soft); margin-top:10px; line-height:1.7; }
  .kb-legend b{ color:var(--ink); font-weight:500; }
  .kb-legend .swatch{
    display:inline-block; width:10px; height:10px; border-radius:3px; margin:0 4px -1px 0;
  }
  .kb-legend .sw-cons{ background:var(--clay); }
  .kb-legend .sw-vowel{ background:var(--jade); }

  /* --- 打字練習區 --- */
  .tp-level{
    display:inline-block; font-size:11px; padding:3px 10px; border-radius:10px;
    background:var(--jade-soft); color:var(--jade); margin-bottom:10px;
  }
  .tp-target{
    background:var(--paper); border:1px solid var(--line); border-radius:6px;
    padding:22px 24px; margin-bottom:6px;
    font-family:"Noto Serif KR",serif; font-size:26px; font-weight:700; line-height:1.6;
    letter-spacing:0.5px;
  }
  .tp-correct{ color:var(--jade); }
  .tp-wrong{ color:var(--wrong); text-decoration:underline wavy var(--wrong); }
  .tp-pending{ color:var(--ink-soft); }
  .tp-extra{ color:var(--wrong); opacity:0.7; text-decoration:line-through; }

  footer, #MainMenu{ visibility:hidden; }
  .app-footer{ text-align:center; font-size:12px; color:var(--ink-soft); margin-top:30px; }
</style>
"""
# CUSTOM_CSS is injected inside render_typing_mode(), not at import time, so
# it only applies while the typing-practice mode is actually being shown.


# =========================================================
# 1. 資料：두벌식 키보드 배열 & 연습 문장
# =========================================================

# Each row entry: (physical key, base jamo (no shift), shift jamo or None, group)
# group is "cons" (consonant, entered with left/right pinky-ring fingers on
# the standard layout) or "vowel". This mirrors the standard KS X 5002
# 두벌식 (2-beolsik) layout used on virtually all Korean keyboards.
KB_ROW_1: List[Tuple[str, str, str, str]] = [
    ("Q", "ㅂ", "ㅃ", "cons"), ("W", "ㅈ", "ㅉ", "cons"), ("E", "ㄷ", "ㄸ", "cons"),
    ("R", "ㄱ", "ㄲ", "cons"), ("T", "ㅅ", "ㅆ", "cons"),
    ("Y", "ㅛ", "", "vowel"), ("U", "ㅕ", "", "vowel"), ("I", "ㅑ", "", "vowel"),
    ("O", "ㅐ", "ㅒ", "vowel"), ("P", "ㅔ", "ㅖ", "vowel"),
]
KB_ROW_2: List[Tuple[str, str, str, str]] = [
    ("A", "ㅁ", "", "cons"), ("S", "ㄴ", "", "cons"), ("D", "ㅇ", "", "cons"),
    ("F", "ㄹ", "", "cons"), ("G", "ㅎ", "", "cons"),
    ("H", "ㅗ", "", "vowel"), ("J", "ㅓ", "", "vowel"), ("K", "ㅏ", "", "vowel"), ("L", "ㅣ", "", "vowel"),
]
KB_ROW_3: List[Tuple[str, str, str, str]] = [
    ("Z", "ㅋ", "", "cons"), ("X", "ㅌ", "", "cons"), ("C", "ㅊ", "", "cons"), ("V", "ㅍ", "", "cons"),
    ("B", "ㅠ", "", "vowel"), ("N", "ㅜ", "", "vowel"), ("M", "ㅡ", "", "vowel"),
]
KB_ROWS: List[List[Tuple[str, str, str, str]]] = [KB_ROW_1, KB_ROW_2, KB_ROW_3]

# (difficulty label, target sentence, Chinese hint)
PRACTICE_SENTENCES: List[Tuple[str, str, str]] = [
    ("초급", "안녕하세요?", "你好？"),
    ("초급", "감사합니다.", "謝謝。"),
    ("초급", "저는 안나예요.", "我是安娜。"),
    ("초급", "이름이 뭐예요?", "你叫什麼名字？"),
    ("초급", "만나서 반갑습니다.", "很高興認識你。"),
    ("초급", "이건 뭐예요?", "這是什麼？"),
    ("초급", "저는 학생이에요.", "我是學生。"),
    ("초급", "오늘 날씨가 좋아요.", "今天天氣很好。"),
    ("중급", "저는 한국어를 배우고 싶어요.", "我想學韓語。"),
    ("중급", "주말에 뭐 했어요?", "你週末做了什麼？"),
    ("중급", "같이 영화 볼까요?", "要不要一起看電影？"),
    ("중급", "사과 다섯 개 주세요.", "請給我五顆蘋果。"),
    ("중급", "여기에서 사진을 찍어도 돼요?", "可以在這裡拍照嗎？"),
    ("중급", "공원에서 친구를 만났어요.", "我在公園見了朋友。"),
    ("중급", "우리 같이 놀이공원에 갈까요?", "我們要不要一起去遊樂園？"),
]


# =========================================================
# 2. 鍵盤參考圖
# =========================================================

def _kb_key_html(key: str, base: str, shift: str, group: str) -> str:
    shift_html = f'<span class="shift">{shift}</span>' if shift else ""
    return (
        f'<div class="kb-key {group}">'
        f'<span class="letter">{key}</span>{shift_html}'
        f'<span class="base">{base}</span>'
        f"</div>"
    )


def render_keyboard_hint() -> None:
    """Renders a reference diagram of the standard 두벌식 keyboard layout."""
    rows_html = []
    for row_idx, row in enumerate(KB_ROWS):
        indent_class = f" indent-{row_idx}" if row_idx > 0 else ""
        keys_html = "".join(_kb_key_html(*k) for k in row)
        rows_html.append(f'<div class="kb-row{indent_class}">{keys_html}</div>')

    keyboard_html = f"""
    <div class="kb-wrap">
      {''.join(rows_html)}
      <div class="kb-row indent-1"><div class="kb-space">스페이스바 (space)</div></div>
      <div class="kb-legend">
        <span class="swatch sw-cons"></span><b>粉色鍵＝子音</b>（子音字母）
        <span class="swatch sw-vowel"></span><b>綠色鍵＝母音</b>（母音字母）<br/>
        右上角的金色字＝按住 <b>Shift</b> 再按同一顆鍵所輸入的雙子音／複合母音
        （例如 Shift+Q → ㅃ，Shift+O → ㅒ）。
      </div>
    </div>
    """
    st.markdown(keyboard_html, unsafe_allow_html=True)


# =========================================================
# 3. 打字比對與統計
# =========================================================

def _render_diff_html(target: str, typed: str) -> str:
    """Builds the target sentence HTML, colored by comparison to typed text."""
    spans = []
    for i, ch in enumerate(target):
        esc = html.escape(ch)
        if i < len(typed):
            css_class = "tp-correct" if typed[i] == ch else "tp-wrong"
            spans.append(f'<span class="{css_class}">{esc}</span>')
        else:
            spans.append(f'<span class="tp-pending">{esc}</span>')
    if len(typed) > len(target):
        extra = html.escape(typed[len(target):])
        spans.append(f'<span class="tp-extra">{extra}</span>')
    return "".join(spans)


def _compute_stats(target: str, typed: str, elapsed_seconds: float) -> Tuple[int, int]:
    """Returns (accuracy_percent, chars_per_minute) for the current attempt."""
    total = len(target)
    if total == 0:
        return 0, 0
    correct = sum(1 for i, ch in enumerate(typed[:total]) if ch == target[i])
    accuracy = round(correct / total * 100)
    minutes = max(elapsed_seconds, 1.0) / 60
    speed = round(len(typed) / minutes) if elapsed_seconds > 0 else 0
    return accuracy, speed


# =========================================================
# 4. 主畫面（模組進入點）
# =========================================================

def render_typing_mode() -> None:
    """Renders the full typing-practice mode.

    This is the single entry point main_web.py calls after the user picks
    the typing-practice mode from its sidebar. It shows the 두벌식 keyboard
    reference, a target sentence, and a live diff/stat panel driven by a
    plain text input (Streamlit commits text-input values on Enter/blur, so
    feedback appears once the user finishes typing and presses Enter).

    Returns:
        None.
    """
    st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

    if "typing_idx" not in st.session_state:
        st.session_state.typing_idx = 0
    if "typing_start_time" not in st.session_state:
        st.session_state.typing_start_time = None

    idx = st.session_state.typing_idx
    level, target, hint = PRACTICE_SENTENCES[idx]
    input_key = f"typing_input_{idx}"

    st.markdown(
        f"""
        <div class="hero">
          <div class="book-tag">세종한국어 1A · 타자 연습</div>
          <div class="headline">⌨️ 韓文打字練習</div>
          <span class="goal-pill">學習目標：熟悉 두벌식 鍵盤配置，並能對照句子正確輸入</span>
        </div>
        """,
        unsafe_allow_html=True,
    )

    with st.expander("⌨️ 두벌식 키보드 배열 참고（韓文鍵盤參考圖）", expanded=True):
        render_keyboard_hint()

    st.markdown(f'<span class="tp-level">{level} · 第 {idx + 1} / {len(PRACTICE_SENTENCES)} 句</span>', unsafe_allow_html=True)

    typed = st.session_state.get(input_key, "")
    st.markdown(f'<div class="tp-target">{_render_diff_html(target, typed)}</div>', unsafe_allow_html=True)
    st.caption(f"中文提示：{hint}")

    st.text_input(
        "在這裡輸入上面的句子，打完按 Enter 確認：",
        key=input_key,
    )
    typed = st.session_state.get(input_key, "")

    if typed and st.session_state.typing_start_time is None:
        st.session_state.typing_start_time = time.time()

    elapsed = (
        time.time() - st.session_state.typing_start_time
        if st.session_state.typing_start_time else 0.0
    )
    accuracy, speed = _compute_stats(target, typed, elapsed)
    is_complete = (typed == target)

    col1, col2, col3 = st.columns(3)
    col1.metric("정확도 正確率", f"{accuracy}%")
    col2.metric("속도 速度", f"{speed} 자/분")
    col3.metric("시간 用時", f"{elapsed:.0f} 초")

    if is_complete:
        st.success(f"✅ 완료! 완성했습니다 · 用時 {elapsed:.1f} 秒，速度 {speed} 字/分。")

    btn_col1, btn_col2, btn_col3 = st.columns(3)
    with btn_col1:
        if st.button("🔄 다시 입력 重新輸入", use_container_width=True):
            st.session_state.pop(input_key, None)
            st.session_state.typing_start_time = None
            st.rerun()
    with btn_col2:
        if st.button("🔀 랜덤 隨機換一句", use_container_width=True):
            st.session_state.pop(input_key, None)
            st.session_state.typing_idx = random.randrange(len(PRACTICE_SENTENCES))
            st.session_state.typing_start_time = None
            st.rerun()
    with btn_col3:
        if st.button("다음 문장 → 下一句", use_container_width=True, type="primary"):
            st.session_state.pop(input_key, None)
            st.session_state.typing_idx = (idx + 1) % len(PRACTICE_SENTENCES)
            st.session_state.typing_start_time = None
            st.rerun()

    st.markdown(
        '<div class="app-footer">타자 연습 · 두벌식 표준 키보드 배열 기준</div>',
        unsafe_allow_html=True,
    )


if __name__ == "__main__":
    # Allows standalone development/preview of just this module:
    #     streamlit run lessons/typing_practice.py
    # The deployed app instead imports render_typing_mode() from
    # main_web.py, which owns st.set_page_config().
    st.set_page_config(page_title="타자 연습", page_icon="⌨️", layout="centered")
    render_typing_mode()
