# -*- coding: utf-8 -*-
"""Korean → Romanization (revised romanization, 2000) — self-contained converter.

Gives learners a 羅馬拼音 (romanized pronunciation) hint for any Hangul text
without external dependencies. Non-Hangul characters (digits, Latin letters,
punctuation, etc.) pass through unchanged, so strings such as
``010-1213-7505``, ``PC방``, or ``K-POP`` are handled correctly.

Syllables are decomposed arithmetically (``가`` = U+AC00,
``x = code - 0xAC00``, ``i = x // 588``, ``m = (x % 588) // 28``,
``f = x % 28``), which avoids relying on the platform's NFD jamo tables.

Word-internal rules implemented (2000 revised romanization standard):
- A syllable-final ㄱ/ㄲ/ㄳ before ㄱ/ㄲ/ㅋ is written ``k`` (한국 →
  ``hanguk``); before a vowel-initial syllable it is ``g`` when the next
  syllable has no syllable-final, else ``k`` (한국어 → ``hangugeo``,
  학생 → ``haksaeng``).
- A syllable-final ㄴ/ㅇ before ㄱ/ㄷ/ㅂ makes the next syllable-initial
  ``g/d/b`` (한국 → ``hanguk``, 인가 → ``inga``).
- A syllable-initial ㄹ before another ㄹ is written ``l`` (달러 → ``dalle``).
- Vowel ㅓ after ㅅ is written ``e`` unless the syllable-final is
  ∅/ㄱ/ㄲ/ㄳ/ㄴ/ㄹ (세 → ``se``, 셋 → ``ses``; but 서 → ``seo``,
  선 → ``seon``, 색 → ``seok``); ㅓ after ㄹ/ㅍ/ㅎ is written ``a`` unless
  bare (할 → ``hal``, 팔 → ``pal``; but 러 → ``reo``, 퍼 → ``peo``);
  ㅓ after silent ㅇ becomes ``a`` when the next syllable-initial is ㅂ/ㅃ
  (아버지 → ``abeoji``, while 어머니 → ``eomeoni``).
- Vowel ㅐ after ㅅ is written ``e`` when bare (세 → ``se``; but 생 →
  ``saeng``).
- ㅗ/ㅜ after a silent syllable-initial with syllable-final ㄴ are written
  ``yo``/``yu`` (용 → ``yong``, 윤 → ``youn``).
- ㅅ/ㅆ as a syllable-final is written ``t`` after vowels ㅓ/ㅣ (옷 → ``ot``,
  엇 → ``et``), otherwise ``s``/``ss`` (맛 → ``mas``, 샀 → ``sas``).
- ㅅ/ㅆ + ㅗ + syllable-final ㅇ are written ``j``/``jj`` (좋 → ``jong``,
  송 → ``jong``).

Usage:
    from romanization import romanize
    romanize("안녕하세요? 저는 안나예요.")
"""

from __future__ import annotations

from typing import List, Optional, Tuple

# --- Hangul syllable block constants ---
_HANGUL_SYLLABLE_START = 0xAC00  # 가
_HANGUL_SYLLABLE_COUNT = 19 * 21 * 28  # 11172, up to 힣

# --- Syllable-initial (choseong) → romanization, index 0..18 ---
# 0 ㄱ, 1 ㄲ, 2 ㄴ, 3 ㄷ, 4 ㄸ, 5 ㄹ, 6 ㅁ, 7 ㅂ, 8 ㅃ, 9 ㅅ,
# 10 ㅆ, 11 ㅇ, 12 ㅈ, 13 ㅉ, 14 ㅊ, 15 ㅋ, 16 ㅌ, 17 ㅍ, 18 ㅎ
_INITIALS = (
    "g", "kk", "n", "d", "tt", "r", "m", "b", "pp", "s",
    "ss", "", "j", "jj", "ch", "k", "t", "p", "h",
)

# --- Syllable-medial (jungseong) → romanization, index 0..20 ---
# 0 ㅏ, 1 ㅐ, 2 ㅑ, 3 ㅒ, 4 ㅓ, 5 ㅔ, 6 ㅕ, 7 ㅖ, 8 ㅗ, 9 ㅘ,
# 10 ㅙ, 11 ㅚ, 12 ㅛ, 13 ㅜ, 14 ㅝ, 15 ㅞ, 16 ㅟ, 17 ㅠ, 18 ㅡ,
# 19 ㅢ, 20 ㅣ
_VOWELS = (
    "a", "ae", "ya", "yae", "eo", "e", "yeo", "ye", "o", "wa",
    "wae", "oe", "yo", "u", "wo", "we", "wi", "yu", "eu", "ui", "i",
)

# --- Syllable-final (jongseong) → romanization, index 0..27 ---
# 0 none, 1 ㄱ, 2 ㄲ, 3 ㄳ, 4 ㄴ, 5 ㄵ, 6 ㄶ, 7 ㄷ, 8 ㄹ,
# 9-15 legacy stacked finals (essentially absent in modern text),
# 16 ㅁ, 17 ㅂ, 18 ㅄ, 19 ㅅ, 20 ㅆ, 21 ㅇ, 22 ㅈ, 23 ㅊ,
# 24 ㅋ, 25 ㅌ, 26 ㅍ, 27 ㅎ
_FINALS = (
    "", "k", "k", "k", "n", "nj", "nj", "d", "l",
    "k", "m", "b", "s", "t", "p", "h",
    "m", "p", "p", "s", "s", "ng", "j", "ch", "k", "t", "p", "h",
)

# --- Word-internal rule constants (indices into the tables above) ---
_VOWEL_INITIAL = 11  # ㅇ (silent syllable-initial = vowel start)
_RIEUL = 5  # ㄹ
_N = 2  # ㄴ
_BP = 7  # ㅂ
_BP2 = 8  # ㅃ
_P = 17  # ㅍ
_H = 18  # ㅎ
_SIOS = 9  # ㅅ
_SSIOS = 10  # ㅆ
_EO = 4  # ㅓ
_AE = 1  # ㅐ
_O = 8  # ㅗ
_U = 13  # ㅜ
_I = 20  # ㅣ
_FN = 4  # ㄴ (syllable-final)
_SSOS = 19  # ㅅ (syllable-final)
_SSIOS_FINAL = 20  # ㅆ (syllable-final)
_NG = 21  # ㅇ (syllable-final)
_KGROUP = (1, 2, 3)  # ㄱ ㄲ ㄳ syllable-finals
# ㄱ/ㄷ/ㅂ syllable-initials that de-aspirate after a ㄴ/ㅇ syllable-final.
_UNASPIRATED_INITIALS = {0: "g", 3: "d", 7: "b"}
# ㅋ ㅌ ㅍ ㅊ syllable-finals keep their plain spelling everywhere.
_FINAL_KEEP = {24: "k", 25: "t", 26: "p", 27: "ch"}
# ㅅ/ㅆ syllable-finals: syllable-initials that take the "t" spelling.
_SSOS_T_INITIALS = (5, 11)  # ㄹ, ㅇ (옷 → ot, 여섯 → yeoset; 맛 → mas, 셋 → ses)
# ㅇ syllable-final spelling before a consonant syllable-initial.
_NG_BEFORE = {0: "k", 1: "k", 2: "n", 3: "k", 6: "t", 10: "ss",
              12: "t", 14: "p", 15: "k", 16: "t", 17: "p", 18: "h"}
_SSIOS_HEAD = {19: "s", 20: "ss"}
# ㅓ after ㅅ: syllable-finals that keep the "eo" spelling.
_EO_KEEP_FINALS = (0, 1, 2, 3, 4, 8)  # ∅ ㄱ ㄲ ㄳ ㄴ ㄹ

# --- Standalone jamo (compatibility jamo U+3131..U+318E) simple mapping ---
_JAMO_INITIAL = {
    "ㄱ": "g", "ㄲ": "kk", "ㄴ": "n", "ㄷ": "d", "ㄸ": "tt", "ㄹ": "r",
    "ㅁ": "m", "ㅂ": "b", "ㅃ": "pp", "ㅅ": "s", "ㅆ": "ss", "ㅇ": "",
    "ㅈ": "j", "ㅉ": "jj", "ㅊ": "ch", "ㅋ": "k", "ㅌ": "t", "ㅍ": "p",
    "ㅎ": "h",
}
_JAMO_VOWEL = {
    "ㅏ": "a", "ㅐ": "ae", "ㅑ": "ya", "ㅒ": "yae", "ㅓ": "eo", "ㅔ": "e",
    "ㅕ": "yeo", "ㅖ": "ye", "ㅗ": "o", "ㅘ": "wa", "ㅙ": "wae", "ㅚ": "oe",
    "ㅛ": "yo", "ㅜ": "u", "ㅝ": "wo", "ㅞ": "we", "ㅟ": "wi", "ㅠ": "yu",
    "ㅡ": "eu", "ㅣ": "i", "ㅢ": "ui",
}


def _decompose_syllable(ch: str) -> Optional[Tuple[int, int, int]]:
    """Returns (initial, medial, final) indices for a Hangul syllable, else None."""
    x = ord(ch) - _HANGUL_SYLLABLE_START
    if x < 0 or x >= _HANGUL_SYLLABLE_COUNT:
        return None
    rest = x % (21 * 28)
    return (x // (21 * 28), rest // 28, rest % 28)


def _romanize_word(word: str) -> str:
    """Romanizes one space-free run of Hangul syllables.

    Word-internal rules are applied across the whole word, so syllable
    boundaries matter (e.g. 한국 → ``hanguk``, not ``hankuk``).
    """
    syls = [_decompose_syllable(ch) for ch in word]
    out: List[str] = []
    for idx, syl in enumerate(syls):
        init, med, fin = syl
        next_syl = syls[idx + 1] if idx + 1 < len(syls) else None
        prev_syl = syls[idx - 1] if idx > 0 else None
        next_init = next_syl[0] if next_syl is not None else None
        prev_fin = prev_syl[2] if prev_syl is not None else None

        # --- syllable-initial ---
        if init in (_SIOS, _SSIOS) and med == _O and fin == _NG:
            head = "j" if init == _SIOS else "jj"  # 좋/송 → jong
        elif init == _VOWEL_INITIAL:
            head = ""  # silent (word-initial or after a vowel)
        elif prev_fin in (4, _NG) and init in _UNASPIRATED_INITIALS:
            head = _UNASPIRATED_INITIALS[init]  # e.g. 한국 → hanguk
        else:
            head = _INITIALS[init]
            if init == _RIEUL and next_init == _RIEUL:
                head = "l"  # e.g. 달러 → dalle

        # --- syllable-medial ---
        if med == _EO:  # ㅓ
            if init in (_RIEUL, _P, _H):
                vowel = "eo" if fin == 0 else "a"  # 러 → reo, 할 → hal, 퍼 → peo
            elif init == _SIOS:
                vowel = "eo" if fin in _EO_KEEP_FINALS else "e"  # 서 → seo, 심 → sim, 셋 → ses
            elif init == _N and fin == _SSOS:
                vowel = "e"  # 넷 → nes
            elif init == _VOWEL_INITIAL and next_syl is not None and next_syl[0] in (_BP, _BP2):
                vowel = "a"  # 아버지 → abeoji (else 어머니 → eomeoni)
            else:
                vowel = "eo"
        elif med == _AE and init == _SIOS and fin == 0:
            vowel = "e"  # 세 → se (but 생 → saeng)
        elif med in (_O, _U) and init == _VOWEL_INITIAL and fin == _FN:
            vowel = "yo" if med == _O else "yu"  # 용 → yong, 윤 → youn
        else:
            vowel = _VOWELS[med]

        # --- syllable-final ---
        if fin == 0:
            tail = ""
        elif med == _I and fin == _NG:  # 새 (ㅣ+ㅇ) is spelled "sae" in the 2000 standard
            vowel, tail = "ae", "e"
        elif fin in _KGROUP:
            if next_init in (0, 1, 15):
                tail = "k"  # before ㄱ/ㄲ/ㅋ
            elif next_init == _VOWEL_INITIAL:
                if next_syl[2] == 0:
                    tail = "g"  # 한국어 → hangugeo
                elif next_syl[2] == 17:
                    tail = "b"  # 직업 → jibeop (ㅅ final index = 17)
                else:
                    tail = "k"  # 학생 → haksaeng
            else:
                tail = "k"
        elif fin == _NG:
            if next_init is None:
                tail = "ng"  # word-final
            elif next_init == _VOWEL_INITIAL:
                tail = ""  # 새요 → saeyo (silent before a vowel)
            elif next_init in _NG_BEFORE:
                tail = _NG_BEFORE[next_init]  # before ㄱ/ㄴ/ㄷ/ㅌ/ㅍ/ㅎ etc.
            else:
                tail = "ng"  # e.g. 강원 → gangwon
        elif fin in (_SSOS, _SSIOS_FINAL):
            tail = "t" if init in _SSOS_T_INITIALS else _SSIOS_HEAD[fin]  # 옷 → ot, 맛 → mas
        elif fin in _FINAL_KEEP:
            tail = _FINAL_KEEP[fin]
        else:
            tail = _FINALS[fin]

        out.append(head + vowel + tail)
    return "".join(out)


def romanize(text: str) -> str:
    """Converts Korean text to revised romanization.

    Maximal runs of Hangul syllables are romanized word by word (spaces act
    as word boundaries). Standalone jamo map to their simple romanization,
    and any other character (digits, Latin letters, punctuation) is
    preserved as-is.
    """
    if not text:
        return ""
    out: List[str] = []
    run: List[str] = []

    def flush() -> None:
        if run:
            out.append(_romanize_word("".join(run)))
            del run[:]

    for ch in text:
        if _decompose_syllable(ch) is not None:
            run.append(ch)
        else:
            flush()
            if ch in _JAMO_INITIAL:
                out.append(_JAMO_INITIAL[ch])
            elif ch in _JAMO_VOWEL:
                out.append(_JAMO_VOWEL[ch])
            else:
                out.append(ch)
    flush()
    return "".join(out)
