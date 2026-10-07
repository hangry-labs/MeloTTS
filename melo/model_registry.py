"""Audited upstream model revisions used by reproducible Docker builds."""

import os

TTS_MODEL_REPOSITORIES = {
    "EN": "myshell-ai/MeloTTS-English",
    "EN_V2": "myshell-ai/MeloTTS-English-v2",
    "EN_NEWEST": "myshell-ai/MeloTTS-English-v3",
    "FR": "myshell-ai/MeloTTS-French",
    "JP": "myshell-ai/MeloTTS-Japanese",
    "ES": "myshell-ai/MeloTTS-Spanish",
    "ZH": "myshell-ai/MeloTTS-Chinese",
    "KR": "myshell-ai/MeloTTS-Korean",
}

TTS_MODEL_REVISIONS = {
    "EN": "bb4fb7346d566d277ba8c8c7dbfdf6786139b8ef",
    "EN_V2": "a53e3509c4ee4ff16d79272feb2474ff864e18f3",
    "EN_NEWEST": "f7c4a35392c0e9be24a755f1edb4c3f63040f759",
    "FR": "1e9bf590262392d8bffb679b0a3b0c16b0f9fdaf",
    "JP": "367f8795464b531b4e97c1515bddfc1243e60891",
    "ES": "dbb5496df39d11a66c1d5f5a9ca357c3c9fb95fb",
    "ZH": "af5d207a364ea4208c6f589c89f57f88414bdd16",
    "KR": "0207e5adfc90129a51b6b03d89be6d84360ed323",
}

BERT_MODEL_REVISIONS = {
    "bert-base-uncased": "86b5e0934494bd15c9632b12f734a8a67f723594",
    "bert-base-multilingual-uncased": "7cbf9a625e29989f6b9c6c2fa68234c304f7e38f",
    "dbmdz/bert-base-french-europeana-cased": ("b895c3cf291f7bf4c15639078a6bee0b3e272c5b"),
    "dccuchile/bert-base-spanish-wwm-uncased": ("d1c9c4565c9d6731e57ed7f027b802697bad861e"),
    "kykim/bert-kor-base": "1779cc0982ada0216dd6de0dd4e86fb78201926d",
    "tohoku-nlp/bert-base-japanese-v3": "65243d6e5629b969c77309f217bd7b1a79d43c7e",
}


def local_files_only() -> bool:
    return os.getenv("MELOTTS_LOCAL_FILES_ONLY", "0").strip().lower() in {
        "1",
        "true",
        "yes",
        "on",
    }


def bert_revision_kwargs(model_id: str) -> dict[str, str | bool]:
    revision = BERT_MODEL_REVISIONS.get(model_id)
    options: dict[str, str | bool] = {"local_files_only": local_files_only()}
    if revision:
        options["revision"] = revision
    return options
