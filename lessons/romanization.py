# -*- coding: utf-8 -*-
"""Korean → Romanization (revised romanization, 2000) — self-contained converter.

Gives learners a 羅馬拼音 (romanized pronunciation) hint for any Hangul text
without external dependencies. Non-Hangul characters (digits, Latin letters,
Chinese, punctuation, etc.) pass through unchanged, so strings such as
``010-1213-7505``, ``PC방``, or ``K-POP`` are handled correctly.

Syllables are decomposed arithmetically (``가`` = U+AC00,
``x = code - 0xAC00``, ``initial = x // 588``, ``medial = (x % 588) // 28``,
``final = x % 28``), which avoids relying on the platform's NFD jamo tables.

The output follows pronunciation, as the revised romanization does, with
these sound changes applied inside each space-separated word:
- Liaison (연음): a final consonant moves onto a following vowel-initial
  syllable (한국어 → ``hangugeo``, 직업은 → ``jigeobeun``, 있어요 →
  ``isseoyo``); final ㅇ stays (학생이에요 → ``haksaengieyo``); in a
  cluster only the second consonant moves (읽어요 → ``ilgeoyo``, 없어요 →
  ``eopseoyo``); final ㅎ is silent (좋아요 → ``joayo``, 괜찮아요 →
  ``gwaenchanayo``).
- Final neutralization: finals are pronounced k / n / t / l / m / p / ng,
  and clusters are simplified (닭 → ``dak``, 여덟 → ``yeodeol``).
- Aspiration: ㅎ next to ㄱ/ㄷ/ㅂ/ㅈ merges into ㅋ/ㅌ/ㅍ/ㅊ (좋고 → ``joko``,
  백화점 → ``baekwajeom``, 따뜻해요 → ``ttatteutaeyo``).
- Nasalization: k/t/p before ㄴ/ㅁ become ng/n/m (합니다 → ``hamnida``,
  학년 → ``hangnyeon``).
- ㄹ assimilation: ㄴ+ㄹ and ㄹ+ㄴ become ``ll`` (신라 → ``silla``); ㄹ after
  ㅁ/ㅇ (and k/p) becomes ㄴ (종로 → ``jongno``).
- Palatalization: final ㄷ/ㅌ before 이 become ``j``/``ch`` (같이 → ``gachi``).

Usage:
    from romanization import romanize
    romanize("안녕하세요? 저는 안나예요.")  # "annyeonghaseyo? jeoneun annayeyo."
"""

from __future__ import annotations

from typing import List, Optional, Tuple

# --- Hangul syllable block constants ---
_HANGUL_SYLLABLE_START = 0xAC00  # 가
_HANGUL_SYLLABLE_COUNT = 19 * 21 * 28  # 11172, up to 힣

# Syllable-initial (choseong) jamo, index 0..18.
_INITIAL_JAMO = "ㄱㄲㄴㄷㄸㄹㅁㅂㅃㅅㅆㅇㅈㅉㅊㅋㅌㅍㅎ"
# Syllable-final (jongseong) jamo, index 0..27 (0 = no final).
_FINAL_JAMO = (
    "", "ㄱ", "ㄲ", "ㄳ", "ㄴ", "ㄵ", "ㄶ", "ㄷ", "ㄹ", "ㄺ", "ㄻ", "ㄼ", "ㄽ", "ㄾ",
    "ㄿ", "ㅀ", "ㅁ", "ㅂ", "ㅄ", "ㅅ", "ㅆ", "ㅇ", "ㅈ", "ㅊ", "ㅋ", "ㅌ", "ㅍ", "ㅎ",
)
# Syllable-medial (jungseong) → romanization, index 0..20.
_VOWELS = (
    "a", "ae", "ya", "yae", "eo", "e", "yeo", "ye", "o", "wa",
    "wae", "oe", "yo", "u", "wo", "we", "wi", "yu", "eu", "ui", "i",
)
_VOWEL_I = 20  # ㅣ

_INITIAL_ROMAN = {
    "ㄱ": "g", "ㄲ": "kk", "ㄴ": "n", "ㄷ": "d", "ㄸ": "tt", "ㄹ": "r",
    "ㅁ": "m", "ㅂ": "b", "ㅃ": "pp", "ㅅ": "s", "ㅆ": "ss", "ㅇ": "",
    "ㅈ": "j", "ㅉ": "jj", "ㅊ": "ch", "ㅋ": "k", "ㅌ": "t", "ㅍ": "p",
    "ㅎ": "h",
}

# Clusters → (consonant kept as final, consonant carried to a vowel-initial syllable).
_CLUSTERS = {
    "ㄳ": ("ㄱ", "ㅅ"), "ㄵ": ("ㄴ", "ㅈ"), "ㄺ": ("ㄹ", "ㄱ"), "ㄻ": ("ㄹ", "ㅁ"),
    "ㄼ": ("ㄹ", "ㅂ"), "ㄽ": ("ㄹ", "ㅅ"), "ㄾ": ("ㄹ", "ㅌ"), "ㄿ": ("ㄹ", "ㅍ"),
    "ㅄ": ("ㅂ", "ㅅ"),
}
# Pronounced value of a final before a consonant or at the end of a word.
_FINAL_SOUND = {
    "": "",
    "ㄱ": "k", "ㄲ": "k", "ㅋ": "k", "ㄳ": "k", "ㄺ": "k",
    "ㄴ": "n", "ㄵ": "n", "ㄶ": "n",
    "ㄷ": "t", "ㅅ": "t", "ㅆ": "t", "ㅈ": "t", "ㅊ": "t", "ㅌ": "t", "ㅎ": "t",
    "ㄹ": "l", "ㄼ": "l", "ㄽ": "l", "ㄾ": "l", "ㅀ": "l",
    "ㅁ": "m", "ㄻ": "m",
    "ㅂ": "p", "ㅍ": "p", "ㅄ": "p", "ㄿ": "p",
    "ㅇ": "ng",
}
_ASPIRATED = {"ㄱ": "ㅋ", "ㄷ": "ㅌ", "ㅂ": "ㅍ", "ㅈ": "ㅊ"}
# Finals whose ㅎ merges with the next initial (ㄶ/ㅀ keep their ㄴ/ㄹ).
_H_FINALS = {"ㅎ": "", "ㄶ": "ㄴ", "ㅀ": "ㄹ"}
# Final sound + following ㅎ → aspirated initial.
_H_AFTER = {"k": "ㅋ", "t": "ㅌ", "p": "ㅍ"}
_NASAL = {"k": "ng", "t": "n", "p": "m"}

# --- Standalone jamo (compatibility jamo U+3131..U+318E) simple mapping ---
_JAMO_INITIAL = dict(_INITIAL_ROMAN)
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

    Each syllable boundary is resolved once, left to right: the pair
    (final of syllable k, initial of syllable k+1) is rewritten into a
    pronounced final sound and a (possibly changed) next initial.
    """
    inits: List[str] = []
    meds: List[int] = []
    finals: List[str] = []
    for ch in word:
        i, m, f = _decompose_syllable(ch)
        inits.append(_INITIAL_JAMO[i])
        meds.append(m)
        finals.append(_FINAL_JAMO[f])

    n = len(word)
    sounds = [""] * n  # pronounced final of each syllable
    l_before = [False] * n  # initial ㄹ that follows an "l" final (→ "l", not "r")

    for k in range(n):
        fin = finals[k]
        if k == n - 1:
            sounds[k] = _FINAL_SOUND[fin]
            break
        nxt = inits[k + 1]

        if nxt == "ㅇ":  # next syllable starts with a vowel
            if fin in ("", "ㅇ"):
                sounds[k] = _FINAL_SOUND[fin]
            elif fin in _H_FINALS:  # 좋아요 → joayo, 않아요 → anayo
                carried = _H_FINALS[fin]
                sounds[k], inits[k + 1] = "", (carried or "ㅇ")
            elif fin in ("ㄷ", "ㅌ") and meds[k + 1] == _VOWEL_I:  # 같이 → gachi
                sounds[k], inits[k + 1] = "", ("ㅈ" if fin == "ㄷ" else "ㅊ")
            elif fin in _CLUSTERS:  # 읽어요 → ilgeoyo
                keep, carried = _CLUSTERS[fin]
                sounds[k], inits[k + 1] = _FINAL_SOUND[keep], carried
            else:  # 한국어 → hangugeo
                sounds[k], inits[k + 1] = "", fin
            continue

        if fin in _H_FINALS:  # final ㅎ merges with the next consonant
            rest = _H_FINALS[fin]
            if nxt in _ASPIRATED:  # 좋고 → joko
                sounds[k], inits[k + 1] = _FINAL_SOUND[rest], _ASPIRATED[nxt]
                continue
            if nxt == "ㅅ":  # 좋습니다 → josseumnida
                sounds[k], inits[k + 1] = _FINAL_SOUND[rest], "ㅆ"
                continue
            sound = "n" if (rest == "" and nxt == "ㄴ") else _FINAL_SOUND[rest]  # 놓는 → nonneun
        elif fin == "ㄺ" and nxt == "ㄱ":
            sound = "l"  # 읽고 → ilgo
        else:
            sound = _FINAL_SOUND[fin]

        if nxt == "ㅎ" and sound in _H_AFTER:  # 축하 → chuka
            if fin == "ㅈ":
                inits[k + 1] = "ㅊ"
            elif fin in ("ㄷ",) and meds[k + 1] == _VOWEL_I:
                inits[k + 1] = "ㅊ"
            else:
                inits[k + 1] = _H_AFTER[sound]
            keep = _CLUSTERS.get(fin, ("",))[0]
            sounds[k] = _FINAL_SOUND[keep] if keep else ""
            continue

        if nxt in ("ㄴ", "ㅁ") and sound in _NASAL:  # 합니다 → hamnida
            sound = _NASAL[sound]
        if nxt == "ㄹ":
            if sound in _NASAL:  # 백리 → baengni
                sound = _NASAL[sound]
                inits[k + 1] = "ㄴ"
            elif sound in ("m", "ng"):  # 종로 → jongno
                inits[k + 1] = "ㄴ"
            elif sound == "n":  # 신라 → silla
                sound = "l"
                l_before[k + 1] = True
            elif sound == "l":  # 달러 → dalleo
                l_before[k + 1] = True
        elif nxt == "ㄴ" and sound == "l":  # 설날 → seollal
            inits[k + 1] = "ㄹ"
            l_before[k + 1] = True
        sounds[k] = sound

    out: List[str] = []
    for k in range(n):
        head = "l" if (inits[k] == "ㄹ" and l_before[k]) else _INITIAL_ROMAN[inits[k]]
        out.append(head + _VOWELS[meds[k]] + sounds[k])
    return "".join(out)


def romanize(text: str) -> str:
    """Converts Korean text to revised romanization.

    Maximal runs of Hangul syllables are romanized word by word (spaces and
    punctuation act as word boundaries). Standalone jamo map to their simple
    romanization, and any other character (digits, Latin letters,
    punctuation) is preserved as-is.
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
