import streamlit as st
import random
import time
import urllib.parse

# --- 頁面設定 ---
st.set_page_config(page_title="韓文 40 音：iOS 終極音訊版", layout="centered")

# --- 音訊播放函數 (使用 Google TTS) ---
def play_korean_audio(text):
    """產生 Google TTS 連結並嵌入自動播放的 HTML5 音訊組件"""
    # 將韓文編碼為 URL 格式
    query = urllib.parse.quote(text)
    audio_url = f"https://translate.google.com/translate_tts?ie=UTF-8&q={query}&tl=ko&client=tw-ob"
    
    # 利用 HTML5 Audio 標籤，並加上 hidden 屬性
    # 這裡加上隨機參數避免瀏覽器快取舊的聲音
    audio_html = f"""
        <audio autoplay name="media">
            <source src="{audio_url}&timestamp={time.time()}" type="audio/mpeg">
        </audio>
    """
    st.components.v1.html(audio_html, height=0)

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
    st.session_state.last_time = time.time()
    st.session_state.msg = ""
    st.session_state.play_now = False

# --- 答題邏輯 ---
def handle_answer():
    user_ans = st.session_state.user_input.strip().lower()
    correct_ans = st.session_state.data[st.session_state.current_phase][st.session_state.target_char]
    
    if user_ans == correct_ans:
        st.session_state.mastery[st.session_state.target_char] += 1
        st.session_state.msg = "✅ 正確！"
    else:
        st.session_state.mastery[st.session_state.target_char] = 0
        st.session_state.msg = f"❌ 錯誤！答案是 {correct_ans}。"

    # 切換題目
    chars = list(st.session_state.data[st.session_state.current_phase].keys())
    st.session_state.target_char = random.choice(chars)
    st.session_state.user_input = ""
    st.session_state.last_time = time.time()
    st.session_state.play_now = True # 下一題自動播放

# --- UI 介面 ---
st.title("🔊 韓文 40 音：iOS 終極音訊版")

# 1. 檢查清單 (給使用者的重要提示)
with st.expander("🔇 還是沒聲音？請檢查這裡"):
    st.write("1. **實體靜音鍵**：請確認 iPhone 左側開關沒有露出紅色。")
    st.write("2. **控制中心**：請將『媒體音量』調大（不是鈴聲聲量）。")
    st.write("3. **瀏覽器權限**：iOS 預設會阻擋自動播放，請務必先點擊下方的『啟動聲音』按鈕。")

# 2. 啟動/手動播放按鈕 (關鍵點擊事件)
col1, col2 = st.columns(2)
with col1:
    if st.button("🚀 啟動/重播聲音", use_container_width=True):
        st.session_state.play_now = True
with col2:
    if st.button("⏭️ 跳過此題", use_container_width=True):
        handle_answer()

# 顯示題目
m_val = st.session_state.mastery[st.session_state.target_char]
st.write(f"當前進度：{'★' * m_val}{'☆' * (3-m_val)}")
st.markdown(f"<h1 style='text-align: center; font-size: 100px;'>{st.session_state.target_char}</h1>", unsafe_allow_html=True)

# 3. 執行發音
if st.session_state.play_now:
    play_korean_audio(st.session_state.target_char)
    st.session_state.play_now = False

# 4. 輸入框
st.text_input("輸入拼音並按 Enter：", key="user_input", on_change=handle_answer)

if st.session_state.msg:
    st.info(st.session_state.msg)