import re

_COMPATIBILITY_JAMO_NAMES = {
    "ㄱ": "기역",
    "ㄲ": "쌍기역",
    "ㄳ": "기역시옷",
    "ㄴ": "니은",
    "ㄵ": "니은지읒",
    "ㄶ": "니은히읗",
    "ㄷ": "디귿",
    "ㄸ": "쌍디귿",
    "ㄹ": "리을",
    "ㄺ": "리을기역",
    "ㄻ": "리을미음",
    "ㄼ": "리을비읍",
    "ㄽ": "리을시옷",
    "ㄾ": "리을티읕",
    "ㄿ": "리을피읖",
    "ㅀ": "리을히읗",
    "ㅁ": "미음",
    "ㅂ": "비읍",
    "ㅃ": "쌍비읍",
    "ㅄ": "비읍시옷",
    "ㅅ": "시옷",
    "ㅆ": "쌍시옷",
    "ㅇ": "이응",
    "ㅈ": "지읒",
    "ㅉ": "쌍지읒",
    "ㅊ": "치읓",
    "ㅋ": "키읔",
    "ㅌ": "티읕",
    "ㅍ": "피읖",
    "ㅎ": "히읗",
    "ㅏ": "아",
    "ㅐ": "애",
    "ㅑ": "야",
    "ㅒ": "얘",
    "ㅓ": "어",
    "ㅔ": "에",
    "ㅕ": "여",
    "ㅖ": "예",
    "ㅗ": "오",
    "ㅘ": "와",
    "ㅙ": "왜",
    "ㅚ": "외",
    "ㅛ": "요",
    "ㅜ": "우",
    "ㅝ": "워",
    "ㅞ": "웨",
    "ㅟ": "위",
    "ㅠ": "유",
    "ㅡ": "으",
    "ㅢ": "의",
    "ㅣ": "이",
}
_COMPATIBILITY_JAMO_PATTERN = re.compile(
    "[" + re.escape("".join(_COMPATIBILITY_JAMO_NAMES)) + "]+"
)

_DIGIT_NAMES = str.maketrans("0123456789", "영일이삼사오육칠팔구")
_NUMBER_PATTERN = re.compile(r"(?<![0-9,])[0-9](?:[0-9,]*[0-9])?(?![0-9,])")
_MAX_G2PKK_CARDINAL_DIGITS = 16


def normalize_compatibility_jamo(text: str) -> str:
    """Verbalize standalone modern Korean letters before phoneme conversion."""

    return _COMPATIBILITY_JAMO_PATTERN.sub(
        lambda match: ", ".join(
            _COMPATIBILITY_JAMO_NAMES[char] for char in match.group()
        ),
        text,
    )


def normalize_oversized_numbers(text: str) -> str:
    """Read numbers beyond g2pK's cardinal range one digit at a time."""

    def replace(match: re.Match[str]) -> str:
        digits = match.group().replace(",", "")
        if len(digits) <= _MAX_G2PKK_CARDINAL_DIGITS:
            return match.group()
        return digits.translate(_DIGIT_NAMES)

    return _NUMBER_PATTERN.sub(replace, text)
