"""Letter-by-letter spelling help: how each character of a word is written and read."""
from __future__ import annotations

import unicodedata

HIRAGANA = {
    "あ": "a", "い": "i", "う": "u", "え": "e", "お": "o",
    "か": "ka", "き": "ki", "く": "ku", "け": "ke", "こ": "ko",
    "が": "ga", "ぎ": "gi", "ぐ": "gu", "げ": "ge", "ご": "go",
    "さ": "sa", "し": "shi", "す": "su", "せ": "se", "そ": "so",
    "ざ": "za", "じ": "ji", "ず": "zu", "ぜ": "ze", "ぞ": "zo",
    "た": "ta", "ち": "chi", "つ": "tsu", "て": "te", "と": "to",
    "だ": "da", "ぢ": "ji", "づ": "zu", "で": "de", "ど": "do",
    "な": "na", "に": "ni", "ぬ": "nu", "ね": "ne", "の": "no",
    "は": "ha", "ひ": "hi", "ふ": "fu", "へ": "he", "ほ": "ho",
    "ば": "ba", "び": "bi", "ぶ": "bu", "べ": "be", "ぼ": "bo",
    "ぱ": "pa", "ぴ": "pi", "ぷ": "pu", "ぺ": "pe", "ぽ": "po",
    "ま": "ma", "み": "mi", "む": "mu", "め": "me", "も": "mo",
    "や": "ya", "ゆ": "yu", "よ": "yo",
    "ら": "ra", "り": "ri", "る": "ru", "れ": "re", "ろ": "ro",
    "わ": "wa", "を": "wo", "ん": "n",
    "ぁ": "a", "ぃ": "i", "ぅ": "u", "ぇ": "e", "ぉ": "o",
    "ゃ": "ya", "ゅ": "yu", "ょ": "yo", "っ": "(small tsu — doubles the next consonant)",
}

YOON = {"ゃ": "ya", "ゅ": "yu", "ょ": "yo"}

CYRILLIC = {
    "а": "a", "б": "b", "в": "v", "г": "g", "д": "d", "е": "ye", "ё": "yo", "ж": "zh",
    "з": "z", "и": "i", "й": "y", "к": "k", "л": "l", "м": "m", "н": "n", "о": "o",
    "п": "p", "р": "r", "с": "s", "т": "t", "у": "u", "ф": "f", "х": "kh", "ц": "ts",
    "ч": "ch", "ш": "sh", "щ": "shch", "ъ": "(hard sign)", "ы": "y", "ь": "(soft sign)",
    "э": "e", "ю": "yu", "я": "ya",
}

HANGUL_INITIALS = [
    "g", "kk", "n", "d", "tt", "r", "m", "b", "pp", "s", "ss", "", "j", "jj", "ch", "k", "t", "p", "h",
]
HANGUL_VOWELS = [
    "a", "ae", "ya", "yae", "eo", "e", "yeo", "ye", "o", "wa", "wae", "oe", "yo",
    "u", "wo", "we", "wi", "yu", "eu", "ui", "i",
]
HANGUL_FINALS = [
    "", "k", "k", "k", "n", "n", "n", "t", "l", "lk", "lm", "lp", "lt", "lt", "lp", "lh",
    "m", "p", "p", "t", "t", "ng", "t", "t", "k", "t", "p", "t",
]


def _katakana_to_hiragana(char: str) -> str:
    if "ァ" <= char <= "ヶ":
        return chr(ord(char) - 0x60)
    return char


def _hangul_parts(char: str) -> str | None:
    code = ord(char) - 0xAC00
    if not 0 <= code <= 11171:
        return None
    initial, vowel, final = code // 588, (code % 588) // 28, code % 28
    return HANGUL_INITIALS[initial] + HANGUL_VOWELS[vowel] + HANGUL_FINALS[final]


def _japanese(word: str) -> list[dict[str, str]]:
    letters: list[dict[str, str]] = []
    chars = list(word)
    i = 0
    while i < len(chars):
        char = chars[i]
        base = _katakana_to_hiragana(char)
        script = "katakana" if base != char else "hiragana" if base in HIRAGANA else ""
        if base in HIRAGANA:
            reading = HIRAGANA[base]
            if i + 1 < len(chars):
                nxt = _katakana_to_hiragana(chars[i + 1])
                if nxt in YOON and len(reading) > 1 and reading.endswith("i"):
                    stem = reading[:-1]
                    reading = stem + YOON[nxt][1:] if stem in {"sh", "ch", "j"} else stem + YOON[nxt]
                    char += chars[i + 1]
                    i += 1
            letters.append({"char": char, "reading": reading, "script": script or "kana"})
        elif char == "ー":
            letters.append({"char": char, "reading": "(long vowel mark)", "script": "mark"})
        elif unicodedata.category(char) == "Lo":
            letters.append({"char": char, "reading": "kanji", "script": "kanji"})
        elif char.strip():
            letters.append({"char": char, "reading": "", "script": "other"})
        i += 1
    return letters


SMALL_KANA = "ぁぃぅぇぉゃゅょっ"
_reverse: dict[str, str] = {}
for _kana, _reading in HIRAGANA.items():
    if _kana not in SMALL_KANA and _reading.isalpha():
        _reverse.setdefault(_reading, _kana)
for _base, _small in (("ya", "ゃ"), ("yu", "ゅ"), ("yo", "ょ")):
    for _reading, _kana in list(_reverse.items()):
        if _reading.endswith("i") and len(_reading) > 1:
            _reverse.setdefault(_reading[:-1] + _base, _kana + _small)
for _prefix, _kana in (("sh", "し"), ("ch", "ち"), ("j", "じ")):
    for _vowel, _small in (("a", "ゃ"), ("u", "ゅ"), ("o", "ょ")):
        _reverse.setdefault(_prefix + _vowel, _kana + _small)
ROMAJI = sorted(_reverse.items(), key=lambda item: -len(item[0]))


def romaji_to_kana(word: str) -> str:
    """Turn typed romaji ('neko') into hiragana ('ねこ') so a learner can see the real spelling."""
    out, i = "", 0
    lower = word.lower()
    while i < len(lower):
        for reading, kana in ROMAJI:
            if lower.startswith(reading, i):
                out += kana
                i += len(reading)
                break
        else:
            if lower[i] == lower[i + 1 : i + 2] and lower[i] not in "aeioun":
                out += "っ"
            else:
                out += lower[i]
            i += 1
    return out


def spell(word: str, lang: str = "ja") -> dict:
    """Break a word into characters with a pronunciation hint for each."""
    word = word.strip()
    if not word:
        return {"word": "", "letters": [], "romaji": "", "tip": ""}

    typed_romaji = ""
    if lang == "ja" and word.replace(" ", "").isascii() and any(c.isalpha() for c in word):
        typed_romaji, word = word, romaji_to_kana(word)

    if lang == "ja":
        letters = _japanese(word)
        tip = "Write each kana in one stroke order group; small kana (ゃゅょ) join the character before them."
        if typed_romaji:
            tip = f'"{typed_romaji}" is written {word} in hiragana. ' + tip
    elif lang == "ko":
        letters = [
            {"char": c, "reading": _hangul_parts(c) or "", "script": "hangul" if _hangul_parts(c) else "other"}
            for c in word
            if c.strip()
        ]
        tip = "Each Hangul block is built from an initial consonant, a vowel and an optional final consonant."
    elif lang == "ru":
        letters = [
            {"char": c, "reading": CYRILLIC.get(c.lower(), ""), "script": "cyrillic"} for c in word if c.strip()
        ]
        tip = "Cyrillic is phonetic — say each letter in order and the word comes out right."
    elif lang in {"zh", "ar", "hi"}:
        letters = [{"char": c, "reading": "", "script": "character"} for c in word if c.strip()]
        tip = "Copy each character separately, then say the whole word out loud three times."
    else:
        letters = [
            {"char": c, "reading": c.upper() if c.isalpha() else "", "script": "latin"} for c in word if c.strip()
        ]
        tip = "Spell it out loud letter by letter, then say the whole word."

    sounded = [
        letter["reading"]
        for letter in letters
        if letter["reading"] and letter["script"] not in {"kanji", "mark", "other", "character", "latin"}
    ]
    romaji = " · ".join(sounded)
    return {"word": word, "letters": letters, "romaji": romaji, "tip": tip}
