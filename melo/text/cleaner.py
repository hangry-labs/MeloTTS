import copy
from importlib import import_module

from . import cleaned_text_to_sequence

language_module_map = {
    "ZH": "chinese",
    "JP": "japanese",
    "EN": "english",
    "ZH_MIX_EN": "chinese_mix",
    "KR": "korean",
    "FR": "french",
    "SP": "spanish",
    "ES": "spanish",
}


def _language_module(language):
    return import_module(f"{__package__}.{language_module_map[language]}")


def clean_text(text, language):
    language_module = _language_module(language)
    norm_text = language_module.text_normalize(text)
    phones, tones, word2ph = language_module.g2p(norm_text)
    return norm_text, phones, tones, word2ph


def clean_text_bert(text, language, device=None):
    language_module = _language_module(language)
    norm_text = language_module.text_normalize(text)
    phones, tones, word2ph = language_module.g2p(norm_text)

    word2ph_bak = copy.deepcopy(word2ph)
    for i in range(len(word2ph)):
        word2ph[i] = word2ph[i] * 2
    word2ph[0] += 1
    bert = language_module.get_bert_feature(norm_text, word2ph, device=device)

    return norm_text, phones, tones, word2ph_bak, bert


def text_to_sequence(text, language):
    _norm_text, phones, tones, _word2ph = clean_text(text, language)
    return cleaned_text_to_sequence(phones, tones, language)


if __name__ == "__main__":
    pass
