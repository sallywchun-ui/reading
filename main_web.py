import streamlit as st
import random
import time

# --- 頁面設定 ---
st.set_page_config(page_title="韓文 40 音：iOS 聲音修復版", layout="centered")

# --- 強化版 JavaScript 語音組件 ---
def speak_korean_script(text, auto=False):
    """
    透過注入 JS 解決 iOS 靜音問題。
    text: 要發音的韓文字
    auto: 是否為自動播放模式
    """
    js_code = f"""
    <script>
        function speak() {{
            window.speechSynthesis.cancel(); // 先取消所有排隊中的語音
            var msg = new SpeechSynthesisUtterance();
            msg.text = "{text}";
            msg.lang = "ko-KR";
            msg.rate = 0.8;
            msg.volume = 1.0;
            window.speechSynthesis.speak(msg);
        }}
        
        // 確保在環境準備好時執行
        if ("{text}" !== "") {{
            speak();
        }}
    </script>
    """
    st.components.v1.html(js_code, height=0)

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
    st.session_state.target_char = "ㅏ" # 初始題目
    st.session_state.last_time = time.time()
    st.session_state.msg = ""
    st.session_state.trigger_audio = False

# --- 答題邏輯 ---
def check_answer():
    user_ans = st.session_state.user_input.strip().lower()
    correct_ans = st.session_state.data[st.session_state.current_phase][st.session_state.target_char]
    elapsed = time.time() - st.session_state.last_time
    
    if user_ans == correct_ans and elapsed <= 10:
        st.session_state.mastery[st.session_state.target_char] += 1
        st.session_state.msg = f"✅ 正確！({elapsed:.1f}s)"
    else:
        st.session_state.mastery[st.session_state.target_char] = 0
        st.session_state.msg = f"❌ 錯誤或超時！答案是 {correct_ans}。"

    # 選下一題
    phase_chars = list(st.session_state.data[st.session_state.current_phase].keys())
    st.session_state.target_char = random.choice(phase_chars)
    st.session_state.user_input = ""
    st.session_state.last_time = time.time()
    st.session_state.trigger_audio = True # 標記需要發音

# --- UI 介面 ---
st.title("🔊 韓文 40 音：iOS 聲音修復版")

# 關鍵：iOS 解鎖按鈕
st.warning("⚠️ iOS 使用者請先點擊下方按鈕以啟用聲音：")
if st.button("🔴 點我啟動語音系統 (解鎖 iOS 限制)", use_container_width=True):
    # 這裡執行一次空發音來騙過 iOS 的安全性檢查
    speak_korean_script("開始")
    st.session_state.trigger_audio = True
    st.toast("語音權限已解除！")

# 階段選擇
new_phase = st.selectbox("學習階段", list(st.session_state.data.keys()))
if new_phase != st.session_state.current_phase:
    st.session_state.current_phase = new_phase
    st.session_state.target_char = random.choice(list(st.session_state.data[new_phase].keys()))
    st.session_state.trigger_audio = True
    st.rerun()

# 顯示題目
m_val = st.session_state.mastery[st.session_state.target_char]
st.write(f"進度：{'★' * m_val}{'☆' * (3-m_val)}")
st.markdown(f"<h1 style='text-align: center; font-size: 80px; color: #FF4B4B;'>{st.session_state.target_char}</h1>", unsafe_allow_html=True)

# 觸發發音 (只有在狀態改變時執行一次)
if st.session_state.trigger_audio:
    speak_korean_script(st.session_state.target_char)
    st.session_state.trigger_audio = False

# 輸入框
st.text_input("請輸入拼音：", key="user_input", on_change=check_answer)

if st.session_state.msg:
    st.write(st.session_state.msg)

# 重聽按鈕
if st.button("👂 沒聽清楚？點我重聽"):
    speak_korean_script(st.session_state.target_char)