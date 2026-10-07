import re
from collections.abc import Collection, Mapping, Sequence

Pronunciation = Sequence[Sequence[str]]

PRONUNCIATION_OVERRIDES: dict[str, Pronunciation] = {
    "PLUGIN": (("P", "L", "AH1", "G"), ("IH0", "N")),
    "PLUGINS": (("P", "L", "AH1", "G"), ("IH0", "N", "Z")),
}

_INFORMAL_G_DROPPING = re.compile(r"\b([A-Za-z]+in)['\u2019](?=\W|$)")


def expand_informal_g_dropping(text: str, known_words: Collection[str]) -> str:
    """Expand forms such as ``chokin'`` when the canonical word is known."""

    def replace(match: re.Match[str]) -> str:
        stem = match.group(1)
        if stem.upper() in known_words:
            return match.group(0)

        suffix = "G" if stem.isupper() else "g"
        candidate = f"{stem}{suffix}"
        return candidate if candidate.upper() in known_words else match.group(0)

    return _INFORMAL_G_DROPPING.sub(replace, text)


def lookup_pronunciation(
    word: str,
    dictionary: Mapping[str, Pronunciation],
) -> Pronunciation | None:
    key = word.upper()
    return PRONUNCIATION_OVERRIDES.get(key) or dictionary.get(key)
