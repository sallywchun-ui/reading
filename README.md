# reading

韓文自學小工具（Streamlit）。`streamlit run main_web.py` 啟動後，側邊欄可切換三種學習模式：

- **40음 · 단어 트레이너**：40 音與基礎單字的多維度測驗（看字拼音／聽音辨字／看字選義）。
- **교재 학습 (세종한국어 1A)**：세종한국어 1A 教材第1~10課，每課含單字、文法、課文與測驗四個分頁；
  每課另有兩項自動生成的練習——「詞語填空」（測驗範圍之一，例句挖空選詞）與
  「🧩 組句」分頁（點選詞塊依序組裝成完整句子）。
- **타자 연습**：두벌식（2-beolsik）韓文鍵盤參考圖，搭配短句打字練習，即時顯示正確率與速度。

## 檔案結構

- `main.py`：40 音練習的終端機（CLI）版本，獨立執行：`python main.py`。
- `main_web.py`：Streamlit 入口，整合上述三種模式。
- `lessons/textbook_app.py`：세종한국어 1A 教材模組（`LESSONS`、`LESSON_ORDER`、`render_textbook_mode()`），
  由 `main_web.py` 匯入使用；也可獨立預覽：`streamlit run lessons/textbook_app.py`。
- `lessons/typing_practice.py`：打字練習模組（鍵盤參考圖 + 練習句 + `render_typing_mode()`），
  由 `main_web.py` 匯入使用；也可獨立預覽：`streamlit run lessons/typing_practice.py`。
- `requirements.txt`：`pip install -r requirements.txt` 安裝相依套件（streamlit、gTTS）。
