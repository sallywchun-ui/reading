# -*- coding: utf-8 -*-
"""
세종한국어 1A · 제1과 안녕하세요? 저는 안나예요
Streamlit 版本 — 單字 / 文法 / 課文 / 測驗

獨立執行：
    streamlit run lesson01_app.py

若要整合進現有的 main_web.py，把本檔存成 lessons/lesson01.py，
在 main_web.py 裡 `from lessons.lesson01 import render_lesson01`，
並在你的模式選單多加一個分支呼叫 render_lesson01()。
（檔案最下方有整合說明。）
"""

import random
import streamlit as st

# =========================================================
# 0. 頁面設定 + 樣式（呼應紙本教材：米杏底、墨綠主色、赤陶點綴）
# =========================================================

st.set_page_config(page_title="세종한국어 1A · 제1과", page_icon="📘", layout="centered")

CUSTOM_CSS = """
<style>
  @import url('https://fonts.googleapis.com/css2?family=Noto+Serif+KR:wght@500;700&family=Noto+Sans+KR:wght@400;500;700&display=swap');

  :root{
    --bg:#F2F5F1; --paper:#FFFFFF; --ink:#1F2A24; --ink-soft:#55635B;
    --jade:#2F5D50; --jade-soft:#E4EDE9; --clay:#BD4630; --clay-soft:#F7E4DE;
    --gold:#C9922E; --gold-soft:#FBF0D9; --line:#D9DED9; --wrong:#A83B3B;
  }
  .stApp{ background:var(--bg); }
  html, body, [class*="css"]{ font-family:"Noto Sans KR","Noto Serif KR",sans-serif; color:var(--ink); }

  .hero{
    background:var(--paper); border:1px solid var(--line); border-radius:6px;
    padding:26px 28px 22px; margin-bottom:8px;
  }
  .book-tag{ font-size:12px; color:var(--ink-soft); }
  .unit-row{ display:flex; align-items:center; gap:14px; margin:10px 0 16px; }
  .unit-badge{
    width:46px; height:46px; border-radius:50%; border:2px solid var(--jade);
    display:flex; align-items:center; justify-content:center;
    font-family:"Noto Serif KR",serif; font-weight:700; font-size:18px; color:var(--jade);
    flex-shrink:0;
  }
  .unit-meta{ font-size:13px; color:var(--ink-soft); line-height:1.5; }
  .unit-meta b{ color:var(--ink); font-weight:500; }
  .headline{
    font-family:"Noto Serif KR",serif; font-weight:700; font-size:30px;
    margin:0 0 12px; color:var(--ink);
  }
  .goal-pill{
    display:inline-block; background:var(--gold-soft); border:1px solid #EAD9AE;
    color:#7A5A15; padding:6px 14px; border-radius:20px; font-size:13px;
  }

  .section-label{ display:flex; align-items:center; gap:10px; margin:22px 0 10px; }
  .section-label .dot{
    width:32px; height:32px; border-radius:50%; border:1.5px solid var(--ink);
    display:flex; align-items:center; justify-content:center;
    font-size:10px; font-weight:500; text-align:center; line-height:1.1; flex-shrink:0;
  }
  .section-label .title{ font-family:"Noto Serif KR",serif; font-size:18px; font-weight:700; }

  .vocab-hint{ color:var(--ink-soft); font-size:13px; margin:2px 0 10px; }

  .grammar-card{
    background:var(--paper); border:1px solid var(--line); border-radius:6px;
    padding:20px 22px; margin-bottom:16px;
  }
  .grammar-card .pattern{
    font-family:"Noto Serif KR",serif; font-size:22px; font-weight:700; color:var(--jade);
    margin-bottom:6px;
  }
  .grammar-card .rule{
    font-size:13.5px; color:var(--ink-soft); border-left:3px solid var(--jade-soft);
    padding-left:12px; margin:8px 0 14px;
  }
  .ex-block{ background:var(--jade-soft); border-radius:6px; padding:10px 14px; margin-bottom:6px; }
  .ex-line{ font-size:14.5px; margin:3px 0; }
  .ex-line .gana{ color:var(--ink-soft); }
  .ex-line .highlight{ color:var(--clay); font-weight:700; }

  .dialogue{
    background:var(--paper); border:1px solid var(--line); border-radius:6px;
    padding:16px 20px; margin-bottom:14px; font-size:14.5px;
  }
  .dialogue p{ margin:4px 0; }
  .dialogue .who{ color:var(--jade); font-weight:700; }

  .q-tag{
    display:inline-block; font-size:11px; padding:3px 10px; border-radius:10px; margin-bottom:8px;
  }
  .tag-text{ background:var(--jade-soft); color:var(--jade); }
  .tag-extra{ background:var(--gold-soft); color:#7A5A15; }
  .q-text{
    font-family:"Noto Serif KR",serif; font-size:18px; font-weight:500; margin-bottom:6px; color:var(--ink);
  }
  .q-text .blank{ color:var(--clay); border-bottom:2px solid var(--clay); }

  div[data-testid="stVerticalBlockBorderWrapper"]{ border-radius:6px !important; }

  footer, #MainMenu{ visibility:hidden; }
  .app-footer{ text-align:center; font-size:12px; color:var(--ink-soft); margin-top:30px; }
</style>
"""
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)


# =========================================================
# 1. 資料：第1課 안녕하세요? 저는 안나예요
# =========================================================

COUNTRIES = [
    ("한국", "韓國"), ("캐나다", "加拿大"), ("베트남", "越南"), ("미국", "美國"),
    ("프랑스", "法國"), ("태국", "泰國"), ("인도네시아", "印尼"), ("중국", "中國"),
    ("일본", "日本"), ("러시아", "俄羅斯"), ("케냐", "肯亞"),
]
JOBS = [
    ("회사원", "上班族"), ("대학생", "大學生"), ("의사", "醫生"), ("경찰", "警察"),
    ("선생님", "老師"), ("가수", "歌手"), ("요리사", "廚師"),
]
ETC = [
    ("나라", "國家"), ("직업", "職業"), ("네", "是"), ("아니요", "不是"),
    ("모자", "帽子"), ("책", "書"), ("공책", "筆記本"), ("한복", "韓服"),
    ("커피", "咖啡"), ("언니", "姊姊"), ("동생", "弟弟/妹妹"), ("누구", "誰"),
    ("친구", "朋友"), ("씨", "∼先生/小姐"), ("제", "我的（謙稱）"), ("아버지", "父親"),
    ("어머니", "母親"), ("형", "哥哥"), ("이름", "名字"), ("학생", "學生"),
    ("자기소개", "自我介紹"),
]

GRAMMAR = [
    {
        "pattern": "이에요 / 예요",
        "rule": "接在名詞後面，用來敘述人或事物「是什麼」。名詞以子音收尾接 <b>이에요</b>，以母音收尾接 <b>예요</b>。",
        "examples": [
            ("가: 회사원<hl>이에요</hl>?", "（是上班族嗎？）"),
            ("나: 네. 회사원<hl>이에요</hl>.", "（是的，是上班族。）"),
            ("가: 모자<hl>예요</hl>?", "（是帽子嗎？）"),
            ("나: 네. 모자<hl>예요</hl>.", "（是的，是帽子。）"),
        ],
    },
    {
        "pattern": "은 / 는",
        "rule": "接在名詞後面，標示該名詞是句子的主題（主題助詞）。子音收尾接 <b>은</b>，母音收尾接 <b>는</b>。",
        "examples": [
            ("가: 유진 씨 동생<hl>은</hl> 대학생이에요?", "（俊英的弟弟/妹妹是大學生嗎？）"),
            ("나: 네. 제 동생<hl>은</hl> 대학생이에요.", ""),
            ("가: 아버지<hl>는</hl> 요리사예요?", "（爸爸是廚師嗎？）"),
            ("나: 네. 아버지<hl>는</hl> 요리사예요.", ""),
        ],
    },
]

DIALOGUES = [
    {
        "label": "활동 1",
        "title": "인사 대화",
        "lines": [
            ("안나", "안녕하세요? 저는 안나예요."),
            ("주노", "안녕하세요? 저는 주노예요. 안나 씨는 학생이에요?"),
            ("안나", "네. 학생이에요. 주노 씨는요?"),
            ("주노", "저는 회사원이에요."),
        ],
    },
    {
        "label": "활동 2",
        "title": "자기소개",
        "lines": [
            (None, "안녕하세요? 저는 웨이예요. 저는 중국 사람이에요. 요리사예요."),
            (None, "안녕하세요? 저는 유나예요. 저는 한국 사람이에요. 가수예요."),
            (None, "이 사람은 마리 씨예요. 마리 씨는 제 친구예요. 마리 씨는 회사원이에요."),
        ],
    },
    {
        "label": "연습",
        "title": "延伸例句（測驗會用到）",
        "lines": [
            (None, "가: 마이클 씨는 어느 나라 사람이에요? 나: 저는 미국 사람이에요. 의사예요."),
            (None, "가: 리나 씨는 일본 사람이에요? 나: 네, 저는 일본 사람이에요. 가수예요."),
            (None, "다니엘 씨는 캐나다 사람이에요. 다니엘 씨는 선생님이에요."),
            (None, "가: 이 사람은 누구예요? 나: 제 언니예요. 언니는 대학생이에요."),
            (None, "가: 아버지는 무슨 일을 해요? 나: 아버지는 경찰이에요."),
        ],
    },
]

# 課文題：直接根據課本內容
TEXTBOOK_QUESTIONS = [
    {"q": "「의사」的意思是？", "choices": ["警察", "醫生", "歌手", "老師"], "a": 1},
    {"q": "「베트남 사람」是指哪一國人？", "choices": ["泰國人", "越南人", "印尼人", "肯亞人"], "a": 1},
    {"q": "「요리사」的意思是？", "choices": ["廚師", "上班族", "大學生", "老師"], "a": 0},
    {"q": "「친구」的意思是？", "choices": ["朋友", "名字", "弟妹", "父親"], "a": 0},
    {"q": "「어머니」的意思是？", "choices": ["父親", "母親", "姊姊", "哥哥"], "a": 1},
    {"q": '「회사원<span class="blank">___</span>?」空格應填入？（회사원 以子音 ㄴ 收尾）',
     "choices": ["예요", "이에요", "은", "는"], "a": 1},
    {"q": '「모자<span class="blank">___</span>?」空格應填入？（모자 以母音 자 收尾）',
     "choices": ["이에요", "예요", "은", "는"], "a": 1},
    {"q": '「아버지<span class="blank">___</span> 요리사예요.」（아버지 以母音收尾）',
     "choices": ["은", "는", "이에요", "예요"], "a": 1},
    {"q": '「제 동생<span class="blank">___</span> 대학생이에요.」（동생 以子音 ㅇ 收尾）',
     "choices": ["은", "는", "이에요", "예요"], "a": 0},
    {"q": "안나: 안녕하세요? 저는 안나예요. 주노: … 안나 씨는 학생이에요? 안나: 네, 학생이에요. — 주노 씨의 직업은 뭐예요?",
     "choices": ["학생", "의사", "회사원", "가수"], "a": 2},
    {"q": "웨이 씨는 어느 나라 사람이에요？（根據課文：저는 웨이예요. 저는 중국 사람이에요.）",
     "choices": ["한국", "중국", "베트남", "태국"], "a": 1},
    {"q": "유나 씨의 직업은 뭐예요？（根據課文：저는 유나예요. 가수예요.）",
     "choices": ["가수", "의사", "선생님", "경찰"], "a": 0},
    {"q": "마리 씨는 누구예요？（이 사람은 마리 씨예요. 마리 씨는 제 친구예요.）",
     "choices": ["가족", "선생님", "친구", "동생"], "a": 2},
    {"q": "「누구예요?」是在問什麼？", "choices": ["是什麼東西", "是誰", "幾歲", "住哪裡"], "a": 1},
    {"q": "「경찰」的意思是？", "choices": ["警察", "醫生", "歌手", "廚師"], "a": 0},
]
for item in TEXTBOOK_QUESTIONS:
    item["tag"] = "課文"

# 延伸題：用本課單字與文法另外造的句子，課本沒有出現過（依你的要求擴充）
EXTRA_QUESTIONS = [
    {"q": "가: 마이클 씨는 어느 나라 사람이에요? 나: 저는 미국 사람이에요. 의사예요. — 마이클 씨의 직업은 뭐예요?",
     "choices": ["의사", "경찰", "가수", "요리사"], "a": 0},
    {"q": "가: 리나 씨는 일본 사람이에요? 나: 네, 저는 일본 사람이에요. 가수예요. — 리나 씨는 어느 나라 사람이에요?",
     "choices": ["한국", "중국", "일본", "태국"], "a": 2},
    {"q": "다니엘 씨는 캐나다 사람이에요. 다니엘 씨는 선생님이에요. — 다니엘 씨의 직업은 뭐예요?",
     "choices": ["학생", "선생님", "경찰", "회사원"], "a": 1},
    {"q": '「경찰<span class="blank">___</span>?」空格應填入？（경찰 以子音 ㄹ 收尾）',
     "choices": ["이에요", "예요", "은", "는"], "a": 0},
    {"q": '「의사<span class="blank">___</span>?」空格應填入？（의사 以母音 사 收尾）',
     "choices": ["이에요", "예요", "은", "는"], "a": 1},
    {"q": '「이거 책<span class="blank">___</span>? 아니요, 공책이에요.」（책 以子音 ㄱ 收尾）',
     "choices": ["이에요", "예요", "은", "는"], "a": 0},
    {"q": '「이거 커피<span class="blank">___</span>? 네, 커피예요.」（커피 以母音 피 收尾）',
     "choices": ["이에요", "예요", "은", "는"], "a": 1},
    {"q": '「형<span class="blank">___</span> 회사원이에요? 아니요, 형은 선생님이에요.」（형 以子音 ㅇ 收尾）',
     "choices": ["은", "는", "이에요", "예요"], "a": 0},
    {"q": '「언니<span class="blank">___</span> 케냐 사람이에요.」（언니 以母音 니 收尾）',
     "choices": ["은", "는", "이에요", "예요"], "a": 1},
    {"q": '「친구<span class="blank">___</span> 인도네시아 사람이에요.」（친구 以母音 구 收尾）',
     "choices": ["은", "는", "이에요", "예요"], "a": 1},
    {"q": '「선생님<span class="blank">___</span> 러시아 사람이에요.」（선생님 以子音 ㅁ 收尾）',
     "choices": ["은", "는", "이에요", "예요"], "a": 0},
    {"q": "如果朋友是「태국 사람」，他是哪一國人？", "choices": ["泰國人", "印尼人", "肯亞人", "俄羅斯人"], "a": 0},
    {"q": "如果朋友是「인도네시아 사람」，他是哪一國人？", "choices": ["印度人", "印尼人", "伊朗人", "越南人"], "a": 1},
    {"q": "가: 이 사람은 누구예요? 나: 제 언니예요. 언니는 대학생이에요. — 이 사람의 직업은 뭐예요?",
     "choices": ["대학생", "회사원", "가수", "의사"], "a": 0},
    {"q": "가: 아버지는 무슨 일을 해요? 나: 아버지는 경찰이에요. — 아버지의 직업은 뭐예요?",
     "choices": ["의사", "경찰", "선생님", "요리사"], "a": 1},
    # --- 進一步擴充（新增，非課本原句） ---
    {"q": "가: 사라 씨는 프랑스 사람이에요? 나: 아니요, 저는 러시아 사람이에요. 대학생이에요. — 사라 씨는 어느 나라 사람이에요?",
     "choices": ["프랑스", "러시아", "미국", "케냐"], "a": 1},
    {"q": "가: 사라 씨 직업은 뭐예요? 나: 저는 대학생이에요. — 사라 씨의 직업은 뭐예요?",
     "choices": ["회사원", "의사", "대학생", "가수"], "a": 2},
    {"q": "왕 선생님은 중국 사람이에요. 왕 선생님은 선생님이에요. — 왕 선생님의 직업은 뭐예요?",
     "choices": ["선생님", "의사", "경찰", "요리사"], "a": 0},
    {"q": "가: 이 사람은 누구예요? 나: 제 형이에요. 형은 경찰이에요. — 형의 직업은 뭐예요?",
     "choices": ["경찰", "회사원", "가수", "의사"], "a": 0},
    {"q": "가: 어머니는 무슨 일을 하세요? 나: 어머니는 의사예요. — 어머니의 직업은 뭐예요?",
     "choices": ["간호사", "의사", "요리사", "선생님"], "a": 1},
    {"q": '「대학생<span class="blank">___</span>?」空格應填入？（대학생 以子音 ㅇ 收尾）',
     "choices": ["이에요", "예요", "은", "는"], "a": 0},
    {"q": '「가수<span class="blank">___</span>?」空格應填入？（가수 以母音 수 收尾）',
     "choices": ["이에요", "예요", "은", "는"], "a": 1},
    {"q": '「한복<span class="blank">___</span>?」空格應填入？（한복 以子音 ㄱ 收尾）',
     "choices": ["이에요", "예요", "은", "는"], "a": 0},
    {"q": '「누구<span class="blank">___</span>?」空格應填入？（누구 以母音 구 收尾）',
     "choices": ["이에요", "예요", "은", "는"], "a": 1},
    {"q": '「아버지<span class="blank">___</span> 요리사, 어머니<span class="blank">___</span> 의사예요.」兩個空格依序應為？',
     "choices": ["는 / 는", "은 / 은", "는 / 은", "은 / 는"], "a": 0},
    {"q": "가: 웨이 씨는 회사원이에요? 나: 아니요, 웨이 씨는 요리사예요. — 웨이 씨의 직업은 뭐예요?",
     "choices": ["회사원", "요리사", "의사", "경찰"], "a": 1},
    {"q": "가: 유나 씨는 미국 사람이에요? 나: 아니요, 유나 씨는 한국 사람이에요. — 유나 씨는 어느 나라 사람이에요?",
     "choices": ["미국", "한국", "일본", "중국"], "a": 1},
]
for item in EXTRA_QUESTIONS:
    item["tag"] = "延伸"

ALL_QUESTIONS = TEXTBOOK_QUESTIONS + EXTRA_QUESTIONS


# =========================================================
# 2. Session state 初始化
# =========================================================

def _init_state():
    ss = st.session_state
    ss.setdefault("revealed", set())
    ss.setdefault("quiz_scope", "全部")
    ss.setdefault("quiz_order", None)
    ss.setdefault("quiz_idx", 0)
    ss.setdefault("quiz_score", 0)
    ss.setdefault("answered", False)
    ss.setdefault("chosen", None)


_init_state()


def _scope_pool(scope: str):
    if scope == "課文題":
        return TEXTBOOK_QUESTIONS
    if scope == "延伸題":
        return EXTRA_QUESTIONS
    return ALL_QUESTIONS


def _start_quiz(scope: str):
    ss = st.session_state
    ss.quiz_scope = scope
    pool = _scope_pool(scope)
    order = list(range(len(pool)))
    random.shuffle(order)
    ss.quiz_order = order
    ss.quiz_idx = 0
    ss.quiz_score = 0
    ss.answered = False
    ss.chosen = None


# =========================================================
# 3. Header
# =========================================================

st.markdown(
    """
    <div class="hero">
      <div class="book-tag">세종한국어 1A</div>
      <div class="unit-row">
        <div class="unit-badge">01</div>
        <div class="unit-meta">
          <div><b>어휘와 표현</b> — 나라와 직업</div>
          <div><b>문법</b> — 이에요/예요, 은/는</div>
        </div>
      </div>
      <div class="headline">안녕하세요? 저는 안나예요</div>
      <span class="goal-pill">學習目標：能說出自己的國籍與職業、做自我介紹</span>
    </div>
    """,
    unsafe_allow_html=True,
)

tab_vocab, tab_grammar, tab_reading, tab_quiz = st.tabs(["📖 單字", "✏️ 文法", "💬 課文", "📝 測驗"])


# =========================================================
# 4. 單字（點擊卡片查看中文意思）
# =========================================================

with tab_vocab:
    st.markdown('<p class="vocab-hint">點擊卡片查看中文意思</p>', unsafe_allow_html=True)

    def render_vocab_grid(section_key, dot_label, title, words, per_row=3):
        st.markdown(
            f'<div class="section-label"><div class="dot">{dot_label}</div>'
            f'<div class="title">{title}</div></div>',
            unsafe_allow_html=True,
        )
        for row_start in range(0, len(words), per_row):
            row_words = words[row_start:row_start + per_row]
            cols = st.columns(per_row)
            for col, (kr, zh) in zip(cols, row_words):
                key = f"vocab_{section_key}_{kr}"
                is_revealed = key in st.session_state.revealed
                with col:
                    label = f"{kr}\n\n{zh}" if is_revealed else f"{kr}\n\n점击"
                    if st.button(label, key=key, use_container_width=True):
                        if is_revealed:
                            st.session_state.revealed.discard(key)
                        else:
                            st.session_state.revealed.add(key)
                        st.rerun()

    render_vocab_grid("countries", "나라", "國家", COUNTRIES)
    render_vocab_grid("jobs", "직업", "職業", JOBS)
    render_vocab_grid("etc", "기타", "其他詞彙", ETC)


# =========================================================
# 5. 文法
# =========================================================

with tab_grammar:
    for g in GRAMMAR:
        ex_html = ""
        for line, note in g["examples"]:
            line_hl = line.replace("<hl>", '<span class="highlight">').replace("</hl>", "</span>")
            note_html = f' <span class="gana">{note}</span>' if note else ""
            ex_html += f'<p class="ex-line">{line_hl}{note_html}</p>'
        st.markdown(
            f"""
            <div class="grammar-card">
              <div class="pattern">{g['pattern']}</div>
              <div class="rule">{g['rule']}</div>
              <div class="ex-block">{ex_html}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )


# =========================================================
# 6. 課文 / 對話
# =========================================================

with tab_reading:
    for d in DIALOGUES:
        st.markdown(
            f'<div class="section-label"><div class="dot">{d["label"]}</div>'
            f'<div class="title">{d["title"]}</div></div>',
            unsafe_allow_html=True,
        )
        lines_html = ""
        for who, text in d["lines"]:
            if who:
                lines_html += f'<p><span class="who">{who}</span>: {text}</p>'
            else:
                lines_html += f"<p>{text}</p>"
        st.markdown(f'<div class="dialogue">{lines_html}</div>', unsafe_allow_html=True)


# =========================================================
# 7. 測驗（全部 / 課文題 / 延伸題）
# =========================================================

with tab_quiz:
    ss = st.session_state

    scope_choice = st.radio(
        "選擇測驗範圍",
        ["全部", "課文題", "延伸題"],
        horizontal=True,
        index=["全部", "課文題", "延伸題"].index(ss.quiz_scope),
        label_visibility="collapsed",
        key="scope_radio",
    )
    if scope_choice != ss.quiz_scope or ss.quiz_order is None:
        _start_quiz(scope_choice)

    pool = _scope_pool(ss.quiz_scope)
    order = ss.quiz_order

    if not order:
        st.info("這個分類目前沒有題目。")
    elif ss.quiz_idx >= len(order):
        pct = round(ss.quiz_score / len(order) * 100)
        st.markdown(
            f"""
            <div style="text-align:center;padding:24px 8px;">
              <div style="font-family:'Noto Serif KR',serif;font-size:48px;font-weight:700;color:var(--jade);">
                {ss.quiz_score}<span style="font-size:20px;color:var(--ink-soft);"> / {len(order)}</span>
              </div>
              <p style="color:var(--ink-soft);">答對率 {pct}%</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
        if st.button("再測一次", use_container_width=True):
            _start_quiz(ss.quiz_scope)
            st.rerun()
    else:
        item = pool[order[ss.quiz_idx]]

        st.progress(ss.quiz_idx / len(order))
        st.caption(f"第 {ss.quiz_idx + 1} / {len(order)} 題　·　目前分數：{ss.quiz_score}")

        tag_class = "tag-extra" if item["tag"] == "延伸" else "tag-text"
        st.markdown(f'<span class="q-tag {tag_class}">{item["tag"]}</span>', unsafe_allow_html=True)
        st.markdown(f'<div class="q-text">{item["q"]}</div>', unsafe_allow_html=True)

        # 選項固定順序（每題重新進入時才洗牌一次）
        order_key = f"choice_order_{ss.quiz_scope}_{ss.quiz_idx}_{order[ss.quiz_idx]}"
        if order_key not in ss:
            choice_idx = list(range(len(item["choices"])))
            random.shuffle(choice_idx)
            ss[order_key] = choice_idx
        choice_order = ss[order_key]

        for ci in choice_order:
            choice_text = item["choices"][ci]
            btn_key = f"opt_{order_key}_{ci}"
            if not ss.answered:
                if st.button(choice_text, key=btn_key, use_container_width=True):
                    ss.answered = True
                    ss.chosen = ci
                    if ci == item["a"]:
                        ss.quiz_score += 1
                    st.rerun()
            else:
                if ci == item["a"]:
                    st.success(choice_text, icon="✅")
                elif ci == ss.chosen:
                    st.error(choice_text, icon="❌")
                else:
                    st.button(choice_text, key=btn_key, use_container_width=True, disabled=True)

        if ss.answered:
            if ss.chosen == item["a"]:
                st.markdown('<p style="color:var(--jade-soft);">　</p>', unsafe_allow_html=True)
                feedback = "答對了！"
            else:
                feedback = "再想想 — 正確答案已標示為綠色。"
            st.caption(feedback)

            if st.button("下一題 →", type="primary"):
                ss.quiz_idx += 1
                ss.answered = False
                ss.chosen = None
                st.rerun()

st.markdown(
    '<div class="app-footer">세종한국어 1A · 제1과 데이터를 바탕으로 제작 · 국립국어원</div>',
    unsafe_allow_html=True,
)


# =========================================================
# 8. 整合到你現有 main_web.py 的方式（說明，不影響執行）
# =========================================================
#
# 1) 把這個檔案存成 lessons/lesson01.py
# 2) 把最上面 `st.set_page_config(...)` 那一行拿掉（一個 app 只能設定一次頁面）
# 3) 把整個 body（從 Header 開始到最後）包進一個函式：
#
#        def render_lesson01():
#            ...（原本 st.markdown / tabs 的內容都搬進來，記得縮排）
#
# 4) 在 main_web.py 的主選單（sidebar）多加一個模式：
#
#        mode = st.sidebar.radio("학습 모드", ["40음 · 기초 단어 트레이너", "교재 학습 (세종한국어 1A)"])
#        if mode == "교재 학습 (세종한국어 1A)":
#            from lessons.lesson01 import render_lesson01
#            lesson = st.sidebar.selectbox("과 선택", ["1과: 안녕하세요? 저는 안나예요"])
#            if lesson.startswith("1과"):
#                render_lesson01()
#        else:
#            ...（原本 40音/單字 trainer 的程式碼）
#
# 之後第2~10課只要照同樣的資料格式（COUNTRIES/JOBS/... -> GRAMMAR -> DIALOGUES ->
# TEXTBOOK_QUESTIONS/EXTRA_QUESTIONS）建立 lessons/lesson02.py ... lesson10.py，
# 並在 selectbox 裡加選項即可，架構完全可重複使用。
