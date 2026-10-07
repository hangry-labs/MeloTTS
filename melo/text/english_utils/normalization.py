import re

_CAMEL_CASE_BOUNDARY = re.compile(
    r"(?<=[a-z0-9])(?=[A-Z])|(?<=[A-Z])(?=[A-Z][a-z])"
)
_INITIALISM = re.compile(r"(?<![A-Za-z])([A-Z]{2,})(?![A-Za-z])")
_LETTER_NAMES = {
    "A": "ay",
    "B": "bee",
    "C": "cee",
    "D": "dee",
    "E": "ee",
    "F": "ef",
    "G": "gee",
    "H": "aitch",
    "I": "eye",
    "J": "jay",
    "K": "kay",
    "L": "el",
    "M": "em",
    "N": "en",
    "O": "oh",
    "P": "pee",
    "Q": "cue",
    "R": "ar",
    "S": "ess",
    "T": "tee",
    "U": "you",
    "V": "vee",
    "W": "double you",
    "X": "ex",
    "Y": "why",
    "Z": "zee",
}


def normalize_english_tokens(text: str) -> str:
    """Expose product-name boundaries and verbalize uppercase initialisms."""

    text = _CAMEL_CASE_BOUNDARY.sub(" ", text)
    return _INITIALISM.sub(
        lambda match: " ".join(_LETTER_NAMES[letter] for letter in match.group(1)),
        text,
    )
