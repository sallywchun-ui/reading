import streamlit as st
import random
import time
import urllib.parse

# --- 頁面設定 ---
st.set_page_config(page_title="韓文 40 音：iOS 穩定版", layout="centered")

# --- 初始化狀態 ---
if 'data' not in st.session_state:
    st.session_state.data = {
        "Phase 1: 單母音/子音": {
            "ㅏ": "a", "ㅓ": "eo", "ㅗ": "o", "ㅜ": "u", "ㅡ": "eu", "ㅣ": "i",
            "ㄱ": "g", "ㄴ": "n", "ㄷ": "d", "ㄹ": "r", "ㅁ": "m", "ㅂ": "b"
        },
        "Phase 2: 激音/雙子音": {
            "ㅋ": "k", "ㅌ": "t", "ㅍ": "p", "ㅊ": "ch", "ㅎ": "h",
            "ㄲ": "kk", "ㄸ": "tt", "ㅃ": "pp", "ㅆ": "ss", "ㅉ": "jj"
        },
        "Phase 3: 複合母音": {
            "ㅐ": "ae", "ㅒ": "yae", "ㅔ": "e", "ㅖ": "ye", "ㅘ": "wa", 
            "ㅙ": "wae", "ㅚ": "oe", "ㅝ": "wo", "ㅞ": "we", "ㅟ": "wi", "ㅢ": "ui"
        }
    }
    st.session_state.mastery = {char: 0 for phase in st.session_state.data.values() for char in phase}
    st.session_state.current_phase = "Phase 1: 單母音/子音"
    st.session_state.target_char = "ㅏ"
    st.session_state.msg = ""

def handle_next():
    chars = list(st.session_state.data[st.session_state.current_phase].keys())
    st.session_state.target_char = random.choice(chars)
    st.session_state.user_input = ""
    st.session_state.msg = ""

def check_answer():
    user_ans = st.session_state.user_input.strip().lower()
    correct_ans = st.session_state.data[st.session_state.current_phase][st.session_state.target_char]
    if user_ans == correct_ans:
        st.session_state.mastery[st.session_state.target_char] += 1
        st.session_state.msg = "✅ 太棒了！正確！"
        time.sleep(0.5)
        handle_next()
    else:
        st.session_state.mastery[st.session_state.target_char] = 0
        st.session_state.msg = f"❌ 錯誤！正確答案是：{correct_ans}"

# --- UI 介面 ---
st.title("🇰🇷 韓文 40 音練習")

# 顯示當前題目與進度
m_val = st.session_state.mastery[st.session_state.target_char]
st.write(f"【{st.session_state.current_phase}】 熟練度：{'★' * m_val}{'☆' * (3-m_val)}")

st.markdown(f"<h1 style='text-align: center; font-size: 100px; margin: 0;'>{st.session_state.target_char}</h1>", unsafe_allow_html=True)

# --- 核心發音組件 (iOS 點擊版) ---
st.write("👇 請點擊下方播放鈕聽發音：")
query = urllib.parse.quote(st.session_state.target_char)
audio_url = f"https://translate.google.com/translate_tts?ie=UTF-8&q={query}&tl=ko&client=tw-ob"
st.audio(audio_url, format="audio/mpeg")

# --- 輸入與控制 ---
st.text_input("請輸入羅馬拼音：", key="user_input", on_change=check_answer)

if st.session_state.msg:
    st.toast(st.session_state.msg)
    st.write(st.session_state.msg)

if st.button("換一題 (跳過)"):
    handle_next()
    st.rerun()

st.divider()
st.caption("備註：若點擊播放器仍無聲，請檢查手機左側「實體靜音開關」是否關閉（不要看到紅色）。")