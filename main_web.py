import streamlit as st
import random
import time

# --- 頁面設定 ---
st.set_page_config(page_title="韓文 40 音聽力練習器", layout="centered")

# --- 語音播放組件 (JavaScript) ---
def speak_korean(text):
    """透過 HTML/JS 呼叫瀏覽器原生 TTS"""
    js_code = f"""
    <script>
        var msg = new SpeechSynthesisUtterance();
        msg.text = "{text}";
        msg.lang = "ko-KR";
        msg.rate = 0.8; // 稍微放慢一點，聽得更清楚
        window.speechSynthesis.speak(msg);
    </script>
    """
    st.components.v1.html(js_code, height=0)

# --- 初始化資料庫 ---
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
    st.session_state.target_char = random.choice(list(st.session_state.data[st.session_state.current_phase].keys()))
    st.session_state.last_time = time.time()
    st.session_state.msg = ""
    st.session_state.should_speak = False

# --- 核心邏輯 ---
def check_answer():
    user_ans = st.session_state.user_input.strip().lower()
    correct_ans = st.session_state.data[st.session_state.current_phase][st.session_state.target_char]
    elapsed = time.time() - st.session_state.last_time
    
    if elapsed > 10:
        st.session_state.mastery[st.session_state.target_char] = 0
        st.session_state.msg = f"❌ 超時！熟練度重置。"
    elif user_ans == correct_ans:
        st.session_state.mastery[st.session_state.target_char] += 1
        st.session_state.msg = f"✅ 正確！({elapsed:.1f}s)"
    else:
        st.session_state.mastery[st.session_state.target_char] = 0
        st.session_state.msg = f"❌ 錯誤！正確答案是 {correct_ans}。"

    # 選題
    phase_chars = list(st.session_state.data[st.session_state.current_phase].keys())
    not_mastered = [c for c in phase_chars if st.session_state.mastery[c] < 3]
    
    if not_mastered:
        st.session_state.target_char = random.choice(not_mastered)
        st.session_state.should_speak = True # 標記新題目需要發音
    else:
        st.session_state.msg = "🎉 此階段已精通！"
    
    st.session_state.user_input = ""
    st.session_state.last_time = time.time()

# --- UI 介面 ---
st.title("🇰🇷 韓文 40 音：聽寫強化版")

# iOS 語音解鎖按鈕
if st.button("🔊 點此啟動語音模式 (iOS 必點)"):
    st.session_state.should_speak = True
    st.toast("語音已啟動！")

new_phase = st.selectbox("切換學習階段", list(st.session_state.data.keys()))
if new_phase != st.session_state.current_phase:
    st.session_state.current_phase = new_phase
    st.session_state.target_char = random.choice(list(st.session_state.data[new_phase].keys()))
    st.session_state.should_speak = True
    st.rerun()

# 進度與題目
m_val = st.session_state.mastery[st.session_state.target_char]
st.write(f"熟練度：{'★' * m_val}{'☆' * (3-m_val)}")
st.markdown(f"<h1 style='text-align: center; font-size: 100px;'>{st.session_state.target_char}</h1>", unsafe_allow_html=True)

# 執行發音
if st.session_state.should_speak:
    speak_korean(st.session_state.target_char)
    st.session_state.should_speak = False # 防止重複播放

# 輸入框
st.text_input("輸入拼音：", key="user_input", on_change=check_answer)

if st.session_state.msg:
    if "✅" in st.session_state.msg:
        st.success(st.session_state.msg)
    else:
        st.error(st.session_state.msg)

st.info("練習建議：戴上耳機，聽音辨位，挑戰 10 秒內直覺反應！")