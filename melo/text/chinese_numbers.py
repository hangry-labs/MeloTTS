import re

import cn2an


FOUR_DIGIT_YEAR_PATTERN = re.compile(r"\d{4}(?=年)")
NUMBER_PATTERN = re.compile(r"\d+(?:\.?\d+)?")


def normalize_chinese_numbers(text):
    text = FOUR_DIGIT_YEAR_PATTERN.sub(
        lambda match: cn2an.an2cn(match.group(), mode="direct"),
        text,
    )
    return NUMBER_PATTERN.sub(lambda match: cn2an.an2cn(match.group()), text)
