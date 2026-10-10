<p>
  <a href="https://hangry-labs.github.io/MeloTTS/examples/">
    <img src="https://github.com/hangry-labs/MeloTTS/raw/main/assets/melotts_logo_horizontal.webp" alt="Hangry Labs Melo TTS logo">
  </a>
</p>

<p>
  <strong>English</strong> ·
  <a href="https://github.com/hangry-labs/MeloTTS/blob/main/README.nb.md">Norsk bokmål</a> ·
  <a href="https://github.com/hangry-labs/MeloTTS/blob/main/README.pl.md">Polski</a> ·
  <a href="https://github.com/hangry-labs/MeloTTS/blob/main/README.ja.md">日本語</a> ·
  <a href="https://github.com/hangry-labs/MeloTTS/blob/main/README.zh.md">简体中文</a> ·
  <a href="https://github.com/hangry-labs/MeloTTS/blob/main/README.es.md">Español</a>
</p>

# Hangry Labs Melo TTS

Easy-to-run text-to-speech Docker images with a browser UI and HTTP API included.

This Hangry Labs fork is built for people who want text to speech to work without a long setup. Install Docker, run one command, open the local UI, or call the API from your own application.

## Listen First

Voice examples are available here:

https://hangry-labs.github.io/MeloTTS/examples/?lang=en

SSML dialogue examples are available here:

https://hangry-labs.github.io/MeloTTS/examples/ssml.html

The examples include MP3 previews for every language plus multi-voice, multilingual, and directed SSML performances.

## Project Links

- Product page and installation guide: https://hangrylabs.app/software/melotts
- Voice examples: https://hangry-labs.github.io/MeloTTS/examples/?lang=en
- SSML dialogues: https://hangry-labs.github.io/MeloTTS/examples/ssml.html
- GitHub repository: https://github.com/hangry-labs/MeloTTS
- Issues and support: https://github.com/hangry-labs/MeloTTS/issues
- Hangry Labs: https://hangrylabs.app/

## Quick Start

Full image with persistent models and settings:

```bash
docker run --rm -p 8888:8888 --gpus all -v melotts_data:/app/persistent hangrylabs/melotts:latest
```

English-family image:

```bash
docker run --rm -p 8888:8888 --gpus all -v melotts_data:/app/persistent hangrylabs/melotts:latest_en
```

Then open:

http://localhost:8888

The container includes the web UI and the HTTP API on the same port.

## What You Get

- Browser UI for manual text-to-speech generation
- HTTP API for applications and automation
- OpenAI-compatible model, voice, and speech endpoints
- MP3 output from the UI by default
- Backward-compatible WAV API responses unless `format` is requested
- Sentence-level streaming API for applications that want earlier audio delivery
- Native speed and variation controls plus optional pitch, tempo, volume, and loudness normalization
- Experimental opt-in SSML for dialogue, loaded speaker/language switching, per-segment prosody, and exact pauses
- Full multilingual image and smaller English-family image
- Optional Spanish and Korean packs with an explicit upstream-terms warning
- GPU support when Docker/NVIDIA support is available
- Offline core languages immediately; optional packs work offline after one online download

Spanish and Korean are not baked into the image. Enable either one from the
System tab while online after reviewing its upstream terms. The download is kept
in `melotts_data`, so future image versions reuse it and no second download is
needed. Disabling a pack unloads it but keeps the cached files.

## API Example

OpenAI-compatible applications can use `http://localhost:8888/v1` as their API base URL. MP3 is returned by default:

```bash
curl -X POST "http://localhost:8888/v1/audio/speech" ^
  -H "Content-Type: application/json" ^
  -d "{\"model\":\"melotts\",\"input\":\"Hello from Hangry Labs Melo TTS\",\"voice\":\"EN-Newest\"}" ^
  -o hello.mp3
```

Discover models at `/v1/models` and loaded voices at `/v1/audio/voices`. MP3 and raw PCM use sentence-level streaming; Opus, AAC, WAV, and FLAC are complete-file responses. Set `MELOTTS_API_KEY` to require bearer authentication.

The native API provides Melo-specific controls. Default native API behavior returns WAV for backward compatibility:

```bash
curl -X POST "http://localhost:8888/tts/generate" ^
  -H "Content-Type: application/json" ^
  -d "{\"text\":\"Hello from Hangry Labs Melo TTS\",\"language\":\"EN\",\"speaker_id\":\"EN-BR\"}" ^
  -o hello.wav
```

Request MP3 when you want compact output:

```bash
curl -X POST "http://localhost:8888/tts/generate" ^
  -H "Content-Type: application/json" ^
  -d "{\"text\":\"Hello from Hangry Labs Melo TTS\",\"language\":\"EN\",\"speaker_id\":\"EN-BR\",\"format\":\"mp3\"}" ^
  -o hello.mp3
```

Supported formats are listed by:

```bash
curl http://localhost:8888/tts/formats
```

Legacy clients using `POST /tts/convert/tts` still work. New integrations should use `POST /tts/generate`.

Experimental SSML is available on the native API and in the browser UI. Plain text remains the default:

```bash
curl -X POST "http://localhost:8888/tts/generate" ^
  -H "Content-Type: application/json" ^
  -d "{\"input_type\":\"ssml\",\"text\":\"<speak><voice name='EN-Newest'>Good morning.</voice><break time='250ms'/><voice name='ES'>Buenos dias.</voice></speak>\",\"language\":\"EN_NEWEST\",\"speaker_id\":\"EN-Newest\",\"format\":\"mp3\"}" ^
  -o dialogue.mp3
```

The supported bounded subset includes `<voice>`, `<lang>`, `<prosody>`, `<break>`, `<sub>`, and `<say-as>`. Open the SSML guide beside the orange UI mode button for rules and limits. The OpenAI-compatible endpoint remains plain text.

Streaming API for applications:

```bash
curl -X POST "http://localhost:8888/tts/stream" ^
  -H "Content-Type: application/json" ^
  -d "{\"text\":\"First sentence. Second sentence.\",\"language\":\"EN\",\"speaker_id\":\"EN-BR\"}" ^
  -o hello.pcm
```

Streaming defaults to raw mono `pcm_s16le` chunks at the model sample rate. You can also request one continuous MP3 stream fed by sentence-level audio with `"stream_format":"mp3"`. List streaming formats with:

```bash
curl http://localhost:8888/tts/stream-formats
```

## Image Tags

- Full image: `latest`, `<version>`
- English-family image: `latest_en`, `<version>_en`

Latest published release, pinned to Docker Hub's immutable top-level OCI digests:

The `v0.1.0` release predates mirrored version tags on GHCR and remains available from Docker Hub.

**Full image**

```bash
docker run --rm -p 8888:8888 --gpus all -v melotts_data:/app/persistent hangrylabs/melotts:v1.0.1@sha256:f0da2ebce41283a5d2dae7125d4776522f95995abdad80773eb2b200fdd1292b
```

**English-family image**

```bash
docker run --rm -p 8888:8888 --gpus all -v melotts_data:/app/persistent hangrylabs/melotts:v1.0.1_en@sha256:870488904a21cf2e128d80230371270b19dd2a4ea84d70f5505a84afe1bb642f
```

## Links

- Product page: https://hangrylabs.app/software/melotts
- Voice examples: https://hangry-labs.github.io/MeloTTS/examples/?lang=en
- SSML dialogues: https://hangry-labs.github.io/MeloTTS/examples/ssml.html
- GitHub: https://github.com/hangry-labs/MeloTTS
- Hangry Labs: https://hangrylabs.app/
- Issues: https://github.com/hangry-labs/MeloTTS/issues
- Discussions: https://github.com/hangry-labs/MeloTTS/discussions

Docker Hub comments are not monitored regularly. GitHub Issues are the best place to report bugs.

CPU execution and NVIDIA CUDA acceleration are supported. Other GPU or accelerator backends are not advertised without suitable hardware for end-to-end testing; contact the project through GitHub Discussions to provide or sponsor test hardware.

Set `TTS_LANGUAGES` to control which baked core language models load into memory.
Spanish and Korean are controlled by persisted System settings instead.

## Attribution

This is an independently maintained fork of the original MeloTTS project by Wenliang Zhao, Xumin Yu, and Zengyi Qin:

https://github.com/myshell-ai/MeloTTS

The combined application is AGPL-3.0-only. You may use it privately or commercially and call its API from separate applications. If you distribute a modified image or expose a modified Melo TTS service over a network, offer users the corresponding source. Original attribution, model-specific terms, and third-party notices are preserved at:

https://github.com/hangry-labs/MeloTTS/blob/main/THIRD_PARTY_NOTICES.md
