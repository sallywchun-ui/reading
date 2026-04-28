import random
import os
import time
import sys
from collections import deque
from typing import Dict, List, Tuple, Optional

class KoreanFastCleanerTrainer:
    """具備自動清理功能的韓文限時練習系統。
    
    特色：
    1. 答錯或超時後，自動清理輸入行，無需手動刪除。
    2. 維持 40 音完整邏輯與 10s 限時。
    """

    def __init__(self):
        self.MASTERY_GOAL = 3
        self.TIME_LIMIT = 10
        
        # 完整 40 音資料庫
        self.data_store = {
            "Phase 1: 基礎音": {
                "ㅏ": "a", "ㅓ": "eo", "ㅗ": "o", "ㅜ": "u", "ㅡ": "eu", "ㅣ": "i",
                "ㄱ": "g", "ㄴ": "n", "ㄷ": "d", "ㄹ": "r", "ㅁ": "m", "ㅂ": "b", 
                "ㅅ": "s", "ㅇ": "ng", "ㅈ": "j", "ㅎ": "h"
            },
            "Phase 2: 衍生/激音/雙子音": {
                "ㅑ": "ya", "ㅕ": "yeo", "ㅛ": "yo", "ㅠ": "yu", "ㅋ": "k", 
                "ㅌ": "t", "ㅍ": "p", "ㅊ": "ch", "ㄲ": "kk", "ㄸ": "tt", 
                "ㅃ": "pp", "ㅆ": "ss", "ㅉ": "jj"
            },
            "Phase 3: 複合母音": {
                "ㅐ": "ae", "ㅒ": "yae", "ㅔ": "e", "ㅖ": "ye", "ㅘ": "wa", 
                "ㅙ": "wae", "ㅚ": "oe", "ㅝ": "wo", "ㅞ": "we", "ㅟ": "wi", "ㅢ": "ui"
            }
        }
        
        self.level_names = list(self.data_store.keys())
        self.current_level_idx = 0
        self.question_pool = deque()
        self.mastery_map = {}
        self._load_level()

    def _load_level(self):
        data = self.data_store[self.level_names[self.current_level_idx]]
        items = list(data.items())
        random.shuffle(items)
        self.question_pool = deque(items)
        self.mastery_map = {char: 0 for char in data.keys()}

    def _clear_input_line(self):
        """清除當前終端機輸入行內容。"""
        if os.name == 'nt':
            # Windows: 回到行首並印出空白覆蓋
            sys.stdout.write('\r' + ' ' * 50 + '\r')
        else:
            # Unix: 使用 ANSI Escape Codes 清除行
            sys.stdout.write('\r\033[K')
        sys.stdout.flush()

    def _timed_input(self, prompt: str, timeout: int) -> Tuple[Optional[str], float]:
        """定時輸入並回傳 (答案, 耗時)。"""
        sys.stdout.write(prompt)
        sys.stdout.flush()
        start_time = time.time()
        input_str = ""
        
        while True:
            elapsed = time.time() - start_time
            if elapsed > timeout:
                return None, elapsed
            
            if os.name == 'nt':
                import msvcrt
                if msvcrt.kbhit():
                    char = msvcrt.getwche()
                    if char in ('\r', '\n'):
                        return input_str.strip().lower(), elapsed
                    elif char == '\b': # Backspace
                        if len(input_str) > 0:
                            input_str = input_str[:-1]
                            sys.stdout.write(' \b') # 清除視覺殘留
                            sys.stdout.flush()
                    else:
                        input_str += char
            else:
                import select
                r, _, _ = select.select([sys.stdin], [], [], 0.05)
                if r:
                    line = sys.stdin.readline().strip().lower()
                    return line, elapsed
            
            time.sleep(0.01)

    def run(self):
        while True:
            if not self.question_pool:
                print(f"\n🏆 {self.level_names[self.current_level_idx]} 完成！")
                if self.current_level_idx < len(self.level_names) - 1:
                    self.current_level_idx += 1
                    self._load_level()
                    input("按 Enter 進入下一階段...")
                    continue
                break

            char, roman = self.question_pool.popleft()
            os.system('cls' if os.name == 'nt' else 'clear')
            
            print(f"等級：{self.level_names[self.current_level_idx]}")
            progress = "★" * self.mastery_map[char] + "☆" * (self.MASTERY_GOAL - self.mastery_map[char])
            print(f"熟練度：{progress}")
            print(f"\n題目：{char}")
            
            user_input, elapsed = self._timed_input(f"拼音 ({self.TIME_LIMIT}s): ", self.TIME_LIMIT)

            if user_input == 'exit': break

            if user_input == roman:
                self.mastery_map[char] += 1
                if self.mastery_map[char] < self.MASTERY_GOAL:
                    self.question_pool.append((char, roman))
                print(f"\n✅ 正確！(耗時 {elapsed:.1f}s)")
                time.sleep(0.8)
            else:
                # 答錯或超時：自動清理
                self.mastery_map[char] = 0
                self.question_pool.append((char, roman))
                self._clear_input_line()
                error_msg = f"超時！" if user_input is None else f"錯誤！(答案是 {roman})"
                print(f"\n❌ {error_msg}。已自動清空，重新排入...")
                time.sleep(1.5)

if __name__ == "__main__":
    trainer = KoreanFastCleanerTrainer()
    trainer.run()