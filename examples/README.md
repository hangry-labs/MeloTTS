---
layout: default
title: Examples guide
permalink: /examples/guide/
---
# Melo TTS examples

[Listen to voice examples](https://hangry-labs.github.io/MeloTTS/examples/)
or [SSML dialogues](https://hangry-labs.github.io/MeloTTS/examples/ssml.html).

## Voices and languages

The gallery contains 13 original MP3 recordings: eight English model/accent
samples and Spanish, French, Chinese, Japanese and Korean samples. Choose a
speech language or All; playback supports seeking, mute and a shared volume.
Starting another sample pauses the previous one.

Spanish and Korean recordings demonstrate the optional packs. They are not
baked into the default Docker images; enable them in System after reviewing
their upstream terms. The full image includes the three English model families
plus French, Chinese and Japanese. The smaller image includes English families.

The website offers six README locales. Gallery controls support English,
Spanish, French, Japanese, Chinese and Korean independently. Norwegian and
Polish keep English gallery text with a translation notice. Direct speech links
such as `?lang=fr` remain supported; `filter` remembers a speech choice while
`lang` selects the website documentation language.

## SSML dialogues

Five recordings demonstrate English accents, a multilingual café, East Asian
languages, directed delivery and a studio conversation. Each has a transcript,
copyable SSML and request settings. The source documents are embedded in
`ssml.html`; the generation task is `task ssml-examples`.

SSML is an explicit experimental input mode on the native API. The supported
subset routes loaded speakers and language models, controls prosody and pauses,
and compacts the handoff between turns. OpenAI-compatible speech remains plain
text. These pages play recordings; they do not perform live inference.

## Local preview

Run `task pages` for the complete website, `task pages-build` for a static build,
or `task pages-test` for public-staging and routing checks. These tasks use no
GPU and do not load speech models. See the [website guide](../site/README.md).

The `index.md` and `ssml.md` wrappers reuse the original standalone HTML content
in the common shell. Player code and recordings remain shared. Opening
`index.html` and `ssml.html` directly also works with the original directory
structure and local assets. To preview standalone files over HTTP:

```bash
python -m http.server 8055
```

Open <http://localhost:8055/examples/>.
