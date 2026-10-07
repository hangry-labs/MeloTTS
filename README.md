<p align="center">
  <a href="https://hangrylabs.app/software/melotts">
    <img src="assets/melotts_logo_horizontal.webp" alt="Hangry Labs Melo TTS logo" width="1000">
  </a>
</p>

<p align="center">
  <strong>English</strong> ·
  <a href="README.nb.md">Norsk bokmål</a> ·
  <a href="README.pl.md">Polski</a> ·
  <a href="README.ja.md">日本語</a> ·
  <a href="README.zh.md">简体中文</a> ·
  <a href="README.es.md">Español</a>
</p>

# Hangry Labs Melo TTS

Easy-to-run, offline-friendly multilingual text to speech with a complete browser workspace and HTTP API in one Docker image.

This Hangry Labs fork turns the original MeloTTS research project into a practical application for home users, developers, and production evaluation. The full image includes English, French, Chinese, and Japanese model families for immediate offline use; the smaller English-family image contains the three English model generations. Spanish and Korean are optional one-time online downloads because their encoder terms require individual review.

> **Yes, you can use it.** Melo TTS is free software under AGPL-3.0. You may run
> it at home or at work, use it commercially, keep an image offline, call its API
> from a separately licensed application, and use the generated audio. If you
> distribute a modified Melo TTS or let users interact with your modified Melo
> service over a network, you must offer those users the complete corresponding
> source under AGPL-3.0. Model, voice, input, and third-party rights remain subject
> to their own terms; see [Third-Party Notices](THIRD_PARTY_NOTICES.md).

Official images are published on [Docker Hub](https://hub.docker.com/r/hangrylabs/melotts/tags) and [GitHub Container Registry](https://github.com/hangry-labs/MeloTTS/pkgs/container/melotts).

Product overview and guided installation: [hangrylabs.app/software/melotts](https://hangrylabs.app/software/melotts).

## Contents

- [Listen and Have a Look](#listen-and-have-a-look)
- [Quick Start](#quick-start)
- [API Usage](#api-usage)
- [About This Fork](#about-this-fork)
- [Support and Issues](#support-and-issues)
- [Docker Images](#docker-images)
- [Local Development](#local-development)
- [Version History](#version-history)
- [License](#license)

---

## Listen and Have a Look

[Open the interactive voice examples](https://hangry-labs.github.io/MeloTTS/examples/?lang=en) to compare every bundled language and English accent, or hear [multi-voice and multilingual SSML dialogues](https://hangry-labs.github.io/MeloTTS/examples/ssml.html). The browser application at `http://localhost:8888` adds waveform playback and trimming, generation and sentence-streaming workspaces, model controls, output controls, live API discovery, model residency management, and GPU telemetry.

<p align="center">
  <a href="assets/ui.webp">
    <img src="assets/ui.webp" alt="Melo TTS browser workspace with model and output controls" width="1200">
  </a>
</p>

Featured samples: [British English](examples/melotts-en-br.mp3), [newest English model](examples/melotts-en-newest.mp3), [Spanish](examples/melotts-es.mp3), [French](examples/melotts-fr.mp3), [Chinese](examples/melotts-zh.mp3), [Japanese](examples/melotts-jp.mp3), and [Korean](examples/melotts-kr.mp3).

<details>
<summary>All direct MP3 links</summary>

| Language or model | Sample |
| --- | --- |
| English British | [Listen](examples/melotts-en-br.mp3) |
| English newest | [Listen](examples/melotts-en-newest.mp3) |
| English v2 | [Listen](examples/melotts-en-v2.mp3) |
| English | [Listen](examples/melotts-en.mp3) |
| English Indian | [Listen](examples/melotts-en-india.mp3) |
| English Australian | [Listen](examples/melotts-en-au.mp3) |
| English American | [Listen](examples/melotts-en-us.mp3) |
| English default | [Listen](examples/melotts-en-default.mp3) |
| Spanish | [Listen](examples/melotts-es.mp3) |
| French | [Listen](examples/melotts-fr.mp3) |
| Chinese | [Listen](examples/melotts-zh.mp3) |
| Japanese | [Listen](examples/melotts-jp.mp3) |
| Korean | [Listen](examples/melotts-kr.mp3) |

</details>

---

## Quick Start

### Current Snapshot

**Full image**

```bash
docker run --rm -p 8888:8888 --gpus all -v melotts_data:/app/persistent hangrylabs/melotts:latest
```

**English-family image**

```bash
docker run --rm -p 8888:8888 --gpus all -v melotts_data:/app/persistent hangrylabs/melotts:latest_en
```

The smaller English-family image contains `EN`, `EN_V2`, and `EN_NEWEST`. Omit `--gpus all` to run on CPU, or use `--gpus "device=1"` to select a specific GPU. Keep the `melotts_data` volume mounted so optional downloads and settings survive container and image replacement.

Then open [http://localhost:8888](http://localhost:8888). The UI and API are served together; interactive OpenAPI documentation is available at [http://localhost:8888/tts/docs](http://localhost:8888/tts/docs).

### Stable Release

Published releases retain a readable version tag and pin Docker Hub's immutable top-level OCI digest. The digest remains authoritative if a tag is ever changed.
The `v0.1.0` release predates mirrored version tags on GHCR and remains available from Docker Hub.

**Full image**

```bash
docker run --rm -p 8888:8888 --gpus all -v melotts_data:/app/persistent hangrylabs/melotts:v1.0.0
```

**English-family image**

```bash
docker run --rm -p 8888:8888 --gpus all -v melotts_data:/app/persistent hangrylabs/melotts:v1.0.0_en
```

---

## API Usage

<details>
<summary>OpenAI-compatible and native APIs, controls, streaming, and discovery</summary>

### OpenAI-Compatible API

Applications that already support OpenAI text to speech can use `http://localhost:8888/v1` as their API base URL. MP3 is the default:

```bash
curl -X POST "http://localhost:8888/v1/audio/speech" \
  -H "Content-Type: application/json" \
  -d '{"model":"melotts","input":"Hello from Melo Text to Speech.","voice":"EN-Newest"}' \
  -o output.mp3
```

`GET /v1/models` lists the generic `melotts` model plus every configured language-model ID. `GET /v1/audio/voices` returns the loaded speakers in the object form expected by voice-picking clients; pass `?model=melotts-en-newest` to filter the list. The generic model selects the best loaded model for the requested speaker, while an exact model ID provides deterministic model selection.

The compatibility endpoint supports `mp3`, `opus`, `aac`, `flac`, `wav`, and `pcm`, plus the OpenAI speed range from `0.25` to `4.0`. MP3 and raw PCM responses use Melo's real sentence-level streaming path; Opus, AAC, WAV, and FLAC are complete-file responses. Natural-language `instructions`, SSE speech events, and unknown formats fail explicitly rather than being ignored.

Bearer authentication is optional. Set `MELOTTS_API_KEY` on the server to require `Authorization: Bearer <key>` for `/v1` routes; without it, local clients may use any non-empty placeholder key required by their SDK.

### Native API

Generate compact MP3 audio:

```bash
curl -X POST "http://localhost:8888/tts/generate" \
  -H "Content-Type: application/json" \
  -d '{"text":"Hello world!","language":"EN","speaker_id":"EN-BR","format":"mp3"}' \
  -o output.mp3
```

The API defaults remain backward compatible: omitted controls are neutral, omitted `input_type` means plain text, and omitted `format` returns WAV. The deprecated `POST /tts/convert/tts` route remains available for existing clients.

### Synthesis Controls

| Field | Range and default | Behavior |
| --- | --- | --- |
| `input_type` | `text` or `ssml`, default `text` | Explicitly enable the supported experimental SSML subset. Markup is never inferred. |
| `speed` | `0.5` to `2.0`, default `1.0` | Native model speaking speed. |
| `sdp_ratio` | `0.0` to `1.0`, default `0.2` | Blend between deterministic and stochastic duration prediction. |
| `noise_scale` | `0.0` to `1.5`, default `0.6` | Native acoustic sampling variation. |
| `noise_scale_w` | `0.0` to `1.5`, default `0.8` | Native duration sampling variation. |
| `pitch_semitones` | `-12` to `12`, default `0` | Optional FFmpeg pitch shift after synthesis. |
| `tempo` | `0.5` to `2.0`, default `1.0` | Optional FFmpeg tempo change independent of pitch. |
| `volume` | `0.0` to `2.0`, default `1.0` | Optional output volume multiplier. |
| `normalize` | boolean, default `false` | Optional EBU-style loudness normalization. |

Melo TTS does not expose a trained emotion label, style token, reference-audio prompt, or direct emotional-intensity input. The stochastic controls can vary delivery, and pitch/tempo can reshape the result, but the application does not mislabel those effects as native emotion control.

Neutral output-control defaults skip the extra effects pass. For local non-Docker use, FFmpeg is required for Ogg Vorbis, Opus, AAC, and whenever pitch, tempo, volume, or normalization is changed. Docker images already include it.

### Experimental SSML Input

The native generation, streaming, and metrics endpoints accept experimental SSML when `input_type` is explicitly set to `ssml`. Plain text remains the backward-compatible default, and the OpenAI-compatible endpoint continues to interpret `input` as plain text.

```bash
curl -X POST "http://localhost:8888/tts/generate" \
  -H "Content-Type: application/json" \
  -d '{"input_type":"ssml","text":"<speak><voice name=\"EN-Newest\">Good morning.</voice><break time=\"250ms\"/><voice name=\"ES\"><prosody speed=\"0.9\" pitch=\"-1st\">Buenos dias.</prosody></voice></speak>","language":"EN_NEWEST","speaker_id":"EN-Newest","format":"mp3"}' \
  -o dialogue.mp3
```

The supported subset is:

- `<speak>`: one required root, with optional `version="1.0"` or `xml:lang`.
- `<voice name="...">`: select a loaded speaker. Its loaded model becomes the segment language unless a language context is explicit.
- `<lang xml:lang="...">`: select a loaded language model while retaining the current speaker. Because Melo uses separate checkpoints, that speaker must also exist in the target model; use `<voice>` for reliable multilingual dialogue.
- `<prosody speed="0.9" pitch="+2st" tempo="1.05" volume="0.9">`: apply optional inherited controls to one segment. Nested speed, tempo, and volume multiply; pitch adds.
- `<break time="500ms"/>`: set the complete pause at that boundary. `0ms` is valid; adjacent speech units without a break use a 100 ms handoff.
- `<sub alias="spoken text">label</sub>`: speak the alias.
- `<say-as interpret-as="characters|number|ordinal">`: spell characters, validate a number, or produce an English ordinal. Ordinals are limited to English models.

Complete output applies segment effects before assembly, normalizes once when requested, and encodes once. Cross-model dialogue is resampled to the request's default model sample rate. Streaming executes the same plan in order and reports `X-MeloTTS-Stream-Granularity: ssml-unit`.

One document is limited to 50,000 characters, 256 elements, eight nesting levels, 10 seconds per break, and 30 seconds of total explicit silence. Elements, attributes, and namespaces are allowlisted; DTDs, entities, external references, unknown markup, and malformed XML are rejected. Direct `<phoneme>` input is not supported because Melo's language frontends do not expose a safe common IPA boundary.

The browser workspace exposes the same explicit orange SSML mode and an in-app rules guide. The [SSML dialogue examples](https://hangry-labs.github.io/MeloTTS/examples/ssml.html) include the exact scripts and generated MP3 files for multi-accent, multilingual, and directed-delivery demonstrations. Voice names and deployment state can be inspected through `GET /tts/voices`.

SSML that selects Spanish or Korean requires that language pack to be enabled first in the System tab.

### Streaming

```bash
curl -X POST "http://localhost:8888/tts/stream" \
  -H "Content-Type: application/json" \
  -d '{"text":"First sentence. Second sentence.","language":"EN","speaker_id":"EN-BR","stream_format":"mp3"}' \
  -o output.mp3
```

Streaming is sentence-level because the model emits complete sentence segments rather than token-level audio. `pcm_s16le` chunks and a continuous MP3 stream are supported; output controls are applied per sentence chunk.

### Discovery and Operations

| Endpoint | Purpose |
| --- | --- |
| `GET /source` | License, exact corresponding-source location, and third-party notices. |
| `GET /system/settings/models` | Baked core languages plus optional pack download, cache, and enabled state. |
| `GET /tts/status` | Version, build, runtime, languages, controls, and formats. |
| `GET /tts/defaults` | UI texts, presets, neutral output controls, and capability metadata. |
| `GET /tts/languages` | Configured and loaded language models. |
| `GET /tts/voices` | Language/model inventory and speakers. |
| `GET /tts/speakers?language=EN` | Speakers for one language model. |
| `GET /tts/formats` | File output formats and aliases. |
| `GET /tts/stream-formats` | Streaming formats and transport notes. |
| `POST /tts/metrics` | Plain-text sentence metrics or validated SSML plan metrics. |
| `POST /tts/load` | Load a configured model on demand. |
| `POST /tts/purge` | Keep one loaded model and release the others. |
| `POST /system/models/{language}/install` | Explicitly accept upstream terms, download, persist, and enable optional `ES` or `KR`. |
| `DELETE /system/models/{language}` | Disable and unload an optional pack while retaining its persistent files. |

The running service is the source of truth for exact schemas: open `/tts/docs` or inspect `/tts/openapi.json`.

</details>

---

## About This Fork

This independently maintained Hangry Labs fork focuses on simple deployment, offline operation, a complete browser UI, and application-friendly APIs. It is based on the original [MeloTTS](https://github.com/myshell-ai/MeloTTS) by Wenliang Zhao, Xumin Yu, and Zengyi Qin.

The combined application is licensed under AGPL-3.0 because its inherited implementation includes AGPL-covered Bert-VITS2-derived material. The original MyShell.ai MIT grant, source provenance, model terms, and bundled-component notices remain preserved in [Third-Party Notices](THIRD_PARTY_NOTICES.md).

This project is maintained for usability and convenience by a small team. Evaluate security, capacity, observability, and availability requirements before critical production deployment.

## Support and Issues

Open a [GitHub issue](https://github.com/hangry-labs/MeloTTS/issues) for reproducible bugs or feature requests, and include logs, error messages, runtime details, and reproduction steps. Use [GitHub Discussions](https://github.com/hangry-labs/MeloTTS/discussions) for general questions and design ideas.

CPU execution is supported. NVIDIA CUDA is currently the only officially supported and tested GPU acceleration backend because it is the hardware available to the maintainers. Intel XPU, AMD ROCm, Apple MPS, NPUs, and other accelerators are not advertised as supported without end-to-end hardware validation. Anyone who wants another backend maintained can open a discussion and provide or sponsor suitable test hardware.

---

## Docker Images

<details>
<summary>Registries, variants, and offline behavior</summary>

Images are published to [Docker Hub](https://hub.docker.com/r/hangrylabs/melotts/tags) and [GHCR](https://github.com/hangry-labs/MeloTTS/pkgs/container/melotts).

| Variant | Current tag | Release tag | Included models |
| --- | --- | --- | --- |
| Full | `latest` | `<version>` | Baked: `EN`, `EN_V2`, `EN_NEWEST`, `FR`, `ZH`, `JP`; optional: `ES`, `KR` |
| English-family | `latest_en` | `<version>_en` | `EN`, `EN_V2`, `EN_NEWEST` |

Both variants include the browser UI and HTTP API, pinned Python dependencies, audio tooling, and their listed baked model assets. Baked languages run without Hugging Face access. Set `TTS_LANGUAGES` to limit which baked core models load at startup.

Spanish and Korean remain supported but are not distributed in either image. Open System, review the warning and upstream terms, and enable the desired pack while online. Melo downloads the pinned voice checkpoint and encoder directly into `/app/persistent`; after that, the pack works offline and remains available to future image releases using the same `melotts_data` volume. Disabling a pack unloads it without deleting its files. See [Third-Party Notices](THIRD_PARTY_NOTICES.md).

</details>

---

## Local Development

<details>
<summary>Validation and Docker workflows</summary>

This repository targets Python 3.13. Install [Task](https://taskfile.dev/) and `uv`, then use the repository workflows:

```bash
task doctor
task validate
task image
task localdev
```

`task image` builds the full local image. `task imagesmall` builds the English-family image. After one image build, `task localdev` bind-mounts `melo/`, `assets/`, and `VERSION` for rapid backend and UI iteration without rebuilding model layers. See [`docs/notes.md`](docs/notes.md) for copy-paste setup, dependency-resolution, testing, and release notes.

</details>

---

## Version History

Snapshot commands intentionally follow the rolling `latest` tags. Published-release commands retain their readable version tag and also pin Docker Hub's immutable top-level OCI digest; the digest is authoritative if a tag is ever changed.

### v1.0.1 (in development)

The current development snapshot is published through the rolling tags from `main`:

**Full image**

```bash
docker run --rm -p 8888:8888 --gpus all -v melotts_data:/app/persistent hangrylabs/melotts:latest
```

**English-family image**

```bash
docker run --rm -p 8888:8888 --gpus all -v melotts_data:/app/persistent hangrylabs/melotts:latest_en
```

### v1.0.0
- Corrected the combined project license to AGPL-3.0-only, preserved inherited notices, added network-visible source offers, documented model-specific terms, and pinned audited model revisions.
- Removed Spanish BETO and Korean `kykim` artifacts from published images; both languages now use explicit terms-aware online installation into a persistent Docker volume and work offline after that first download.
- Added a strict OpenAI-compatible API with model and voice discovery, optional bearer authentication, OpenAI-shaped errors, MP3 defaults, the full `0.25`-`4.0` speed range, and sentence-streamed MP3/PCM responses.
- Replaced the Gradio interface with the shared Hangry Labs standalone FastAPI UI architecture used by KokoroTTS.
- Added responsive expanded/compact branding, local Lucide icons, WaveSurfer playback and trimming, Generate/Stream/API/System workspaces, model residency controls, and complete demand-driven GPU telemetry with history, hover details, and bounded sampling.
- Added `POST /tts/load` for loading configured models on demand; existing API behavior and the WAV default remain backward compatible.
- Moved the Docker and package baseline to Python 3.13 and CUDA 13.0 PyTorch wheels.
- Removed Gradio and the obsolete `cached-path` dependency branch, then regenerated the Python 3.13 lockfile from `requirements.in`.
- Expanded rapid local iteration tasks to mount the complete `melo/`, `assets/`, and `VERSION` surface without rebuilding the image.
- Made full images and normal local runs default to the six clearly redistributable core model families; English-family images default to `EN`, `EN_V2`, and `EN_NEWEST`.
- Consolidated Docker publication into one strict, metadata-rich pipeline for matching Docker Hub and GHCR full/English-family images.
- Replaced legacy artwork with optimized WebP sets for Melo TTS product surfaces and Hangry Labs organization surfaces.
- Added structural tests for the standalone browser workspace.
- Replaced legacy `setup.py` packaging with `pyproject.toml`; wheels now include the runtime `VERSION`, WebP artwork, standalone UI, and CLI entry points.
- Prevented synthesis text from being written to application logs and serialized inference with model load/purge operations for predictable GPU use.
- Fixed CLI speaker selection for every English model family instead of assuming `EN-Default` exists.
- Added API, CLI, package-contract, and wheel-content tests plus standard `doctor`, `deps`, `lint`, `test`, `package`, and `validate` Taskfile workflows.
- Regenerated the deployment lock for Linux/Python 3.13 and tightened Docker build context exclusions for tests and private agent files.
- Added optional pitch, tempo, volume, and loudness-normalization controls to the UI, generation API, and sentence-streaming API while keeping neutral defaults backward compatible.
- Added explicit experimental SSML to native generation, streaming, metrics, and the browser UI. The hardened bounded parser supports loaded speaker/model routing, inherited segment prosody, substitutions, character/number/English-ordinal reading, exact breaks, multilingual dialogue, and complete-file normalization while plain text remains the default.
- Added a dedicated SSML examples page with five reproducibly generated MP3 dialogues, exact copyable scripts, branded playback controls, and a validation task for regenerating the media through a live Melo service.
- Standardized public branding on `Melo TTS` and `hangrylabs.app`, and removed Tailwind from the examples and 404 pages in favor of purpose-built responsive CSS.
- Documented the distinction between native Melo synthesis controls, post-processing controls, and unsupported named-emotion conditioning.
- Fixed case-sensitive English initialisms and mixed Chinese/English product names: uppercase terms such as `US`, `NLP`, `LLM`, `AI`, `AIGC`, and `SDXL` are now spoken as letters, while lowercase words such as `us` retain their normal pronunciation and camel-case names retain their word boundaries.
- Fixed reproducible English cleaner errors for dropped-`g` spellings such as `chokin'` and `jokin'`, and corrected `plugin`/`plugins` to use the short vowel from `plug` instead of the `g2p-en` fallback's "ploogin" pronunciation.
- Fixed Chinese BERT/phoneme alignment for verb-`一`-verb reduplication when Jieba assigns different parts of speech to the repeated verb, preventing duplicate `word2ph` entries and synthesis failures.
- Reorganized the README around examples, startup, API use, images, development, project context, and release history.

Run this release with either image variant:

**Full image**

```bash
docker run --rm -p 8888:8888 --gpus all -v melotts_data:/app/persistent hangrylabs/melotts:v1.0.0
```

**English-family image**

```bash
docker run --rm -p 8888:8888 --gpus all -v melotts_data:/app/persistent hangrylabs/melotts:v1.0.0_en
```

<details>
<summary>Earlier releases</summary>

### v0.1.0 (11.05.2026)
- Moved the active Docker runtime/build baseline from `python:3.10-slim` to `python:3.11-slim`.
- Raised package metadata from `python_requires>=3.10` to `python_requires>=3.11`.
- Refreshed dependency pins for the Python 3.11 line, including newer `numpy`, `pandas`, and `networkx` pins.
- Validated the English-family Docker build on Python 3.11 with `task imagesmall`, `python -m pip check`, and `task localapi`.
- Added `POST /tts/generate` as the preferred synthesis endpoint while keeping legacy `POST /tts/convert/tts` for backward compatibility.
- Added `POST /tts/stream` for sentence-level streaming responses plus `GET /tts/stream-formats` for discovery. The model does not emit token-level audio; streaming starts after each sentence segment is synthesized.

Run this release with either image variant:

**Full image**

```bash
docker run --rm -p 8888:8888 --gpus all -v melotts_data:/app/persistent hangrylabs/melotts:v0.1.0@sha256:a8b9954378dbe3fc871b07a68c3f833d1f5684e92f0c789744fabb1ce08817e0
```

**English-family image**

```bash
docker run --rm -p 8888:8888 --gpus all -v melotts_data:/app/persistent hangrylabs/melotts:v0.1.0_en@sha256:abf7dfd25fd47121cc06c1a027f6f25a6735d47e7c516324405127496a5c564b
```

### v0.0.8 (10.05.2026)
- Scope: runtime-focused cleanup for the Docker UI/API fork.
- Removed unused upstream training surfaces, including training scripts/modules, training example data, legacy script-style package tests, and original upstream docs that no longer matched this fork.
- Trimmed runtime helper code by reducing `melo/utils.py` to inference text preparation, config loading, and `HParams`.
- Removed stale phonemizer generation artifacts and notebook files that were not read by runtime synthesis.
- Cleaned stale imports, unused locals, and unreachable flow-layer code found by lint checks.
- Improved Taskfile API readiness checks by retrying transient startup errors such as `Empty reply from server`.
- Reworked the UI into a Kokoro-style Gradio layout while keeping Melo TTS language, speaker, preset, and advanced synthesis controls.
- Added text metrics, per-language random quotes, voice inventory, synthesis presets, advanced controls, Gradio audio waveform preview, runtime metadata, favicon/brand icon, and richer API documentation links.
- Added `/tts/status`, `/tts/defaults`, `/tts/voices`, `/tts/metrics`, and `/tts/purge` endpoints for the new UI and companion integrations.
- Added backward-compatible optional API output formats: default WAV plus MP3, FLAC, and Ogg Vorbis via `format`, with discovery at `/tts/formats`.
- Added an output format selector to the Gradio UI; the UI defaults to MP3 while the API remains WAV-by-default for old clients.
- Modernized the runtime dependency stack using `requirements.in` + resolved pins in `requirements.txt`; key validated versions include `gradio==6.14.0`, `fastapi==0.136.1`, `starlette==1.0.0`, `pydantic==2.13.4`, `torch==2.11.0`, `torchaudio==2.11.0`, `transformers==5.8.0`, `numpy==2.2.6`, and `soundfile==0.13.1`.
- Normalized package metadata versioning in `setup.py` so display versions like `v0.0.8-SNAPSHOT` install as valid Python package versions such as `0.0.8.dev0`.
- Added `task release` backed by the root snapshot `VERSION` file, and corrected Docker release tags so the full image publishes as `<version>` while the English-family image publishes as `<version>_en`.
- Expanded rapid local iteration tasks so `task localrun`, `task localdev`, and `task localapi` bind-mount `melo/app.py`.
- Documentation: corrected API examples to use `/tts/convert/tts` JSON payloads and documented the current runtime-only scope.


### v0.0.7 (29.03.2026)
- Upgraded Docker runtime/build baseline to Python 3.10 (`python:3.10-slim`) and aligned packaging with `python_requires>=3.10`.
- Reworked app versioning/build metadata:
  - Root `VERSION` file is now the single version source of truth.
  - Build metadata is generated at image build time (no hardcoded `BUILD_ID`) and exposed in UI/API.
- Upgraded web stack to newer compatible releases: `gradio==4.44.1`, `gradio-client==1.3.0`, `fastapi==0.115.12`, `starlette==0.46.2`, `typer==0.12.5`.
- Applied large dependency/security refresh with pinned versions for reproducible builds, including network/security-sensitive packages such as `requests==2.32.4`, `urllib3==2.3.0`, `certifi==2025.6.15`, plus broad runtime library updates.
- Added/kept compatibility guardrails for stability:
  - `markupsafe` remains on 2.x for Gradio compatibility.
  - `huggingface-hub==0.21.4` and `filelock==3.13.1` remain constrained by `cached-path==1.6.2`.
- Improved offline reliability and startup resilience:
  - Build-time preload profiles (`EN_ONLY` / `FULL`) with retry + strict/non-strict controls.
  - NLTK resources required for EN synthesis (including `averaged_perceptron_tagger_eng` and `cmudict`) are preloaded during image build for offline-ready runs.
- Fixed Gradio 4.x UI regressions after upgrades (language/speaker loading + synth output compatibility) while keeping API behavior stable.
- Split Docker release flow into EN and FULL image tracks/workflows (`<version>_en`, `<version>`) to improve build/release flexibility.

### v0.0.6 (27.03.2026)
- Model loading is now much faster (from ~30 seconds down to only a few seconds in testing).
- Added working RTX 50-series (`sm_120`) support in the Docker setup.
- Added GPU selection support for Docker runs, so you can choose which GPU to use.
- Improved build resilience for model preloading during Docker image creation.

### v0.0.5 (27.03.2026)
- Added more English model options (including V2 and V3 variants).
- Added UI tabs for `UI Playground` and `API Docs`.
- Added build/version badge in UI (top-right) via `APP_VERSION` and `BUILD_ID`.
- Added memory management in UI (`Purge others`) to release non-selected language models.
- Improved API documentation visibility directly inside the app (`/` -> API Docs tab + `/tts/docs`).
- Updated release planning: V2/V3 scope completed; deferred separate base-repo split plan.

### v0.0.4 (09.08.2025)
- **Dependency updates** for improved performance and stability.
- **Full offline support** — all required models are now baked into the image.
- **Model overwrite option**: set `MELOTTTS_MODELS` to point to your custom model folder.
- **Smaller image size** via optimized multi-stage Docker build.

### v0.0.3 (25.07.2025)
- Optimized docker build to use layer caching so we can build stuff fast after the initial build
- Expanded ping to include version and build
- Expanded UI with sdp_ratio, noise_scale and noise_scale_w
- Expanded API with sdp_ratio, noise_scale and noise_scale_w
- Corrected faulty version dates
- Updated documentation

### v0.0.2 (22.06.2025)
- Enable API calls together with UI
- Added configurable language selection through `TTS_LANGUAGES`.
- Added GPU-enabled Docker execution.

### v0.0.1 (21.06.2025)
- Initial release
- Basic TTS functionality
- Support for English (Default, US, BR, India, AU)
- Docker support for both CPU and GPU
- Web interface on port 8888

</details>

---

## License

The combined Melo TTS application is licensed under the [GNU Affero General Public License v3.0 only](LICENSE). You may use, modify, and redistribute it, including commercially. Distributors must provide corresponding source, and operators of modified network services must prominently offer corresponding source to their users.

Original work by Wenliang Zhao, Xumin Yu, and Zengyi Qin in [MeloTTS](https://github.com/myshell-ai/MeloTTS), Bert-VITS2-derived portions, model terms, and bundled component licenses are documented in [Third-Party Notices](THIRD_PARTY_NOTICES.md). Individual components remain under their respective licenses.
