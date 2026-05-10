<p>
  <a href="https://hangry-labs.github.io/MeloTTS/examples/">
    <img src="https://github.com/hangry-labs/MeloTTS/raw/main/logo.png" alt="Hangry Labs Melo T T S logo">
  </a>
</p>

# Hangry Labs Melo T T S

Easy-to-run text-to-speech Docker images with a browser UI and HTTP API included.

This Hangry Labs fork is built for people who want text to speech to work without a long setup. Install Docker, run one command, open the local UI, or call the API from your own application.

## Listen First

Voice examples are available here:

https://hangry-labs.github.io/MeloTTS/examples/

The examples page includes MP3 previews for the main English voices plus Spanish, French, Chinese, Japanese, and Korean.

## Project Links

- Voice examples: https://hangry-labs.github.io/MeloTTS/examples/
- GitHub repository: https://github.com/hangry-labs/MeloTTS
- Issues and support: https://github.com/hangry-labs/MeloTTS/issues
- Hangry Labs: https://nuggies.website/

## Quick Start

Full multilingual image:

```bash
docker run -p 8888:8888 --gpus all hangrylabs/melotts:latest
```

EN-focused image:

```bash
docker run -p 8888:8888 --gpus all hangrylabs/melotts:latest_en
```

Then open:

http://localhost:8888

The container includes the web UI and the HTTP API on the same port.

## What You Get

- Browser UI for manual text-to-speech generation
- HTTP API for applications and automation
- MP3 output from the UI by default
- Backward-compatible WAV API responses unless `format` is requested
- Full multilingual image and smaller EN-focused image
- GPU support when Docker/NVIDIA support is available
- Offline-friendly usage once the image and baked model assets are available locally

## API Example

Default API behavior returns WAV for backward compatibility:

```bash
curl -X POST "http://localhost:8888/tts/convert/tts" ^
  -H "Content-Type: application/json" ^
  -d "{\"text\":\"Hello from Hangry Labs Melo T T S\",\"language\":\"EN\",\"speaker_id\":\"EN-BR\"}" ^
  -o hello.wav
```

Request MP3 when you want compact output:

```bash
curl -X POST "http://localhost:8888/tts/convert/tts" ^
  -H "Content-Type: application/json" ^
  -d "{\"text\":\"Hello from Hangry Labs Melo T T S\",\"language\":\"EN\",\"speaker_id\":\"EN-BR\",\"format\":\"mp3\"}" ^
  -o hello.mp3
```

Supported formats are listed by:

```bash
curl http://localhost:8888/tts/formats
```

## Image Tags

- Full multilingual image: `latest`, `<version>`
- EN-focused image: `latest_en`, `<version>_en`

Example release tags:

```bash
docker run -p 8888:8888 --gpus all hangrylabs/melotts:v0.0.8
docker run -p 8888:8888 --gpus all hangrylabs/melotts:v0.0.8_en
```

## Links

- Voice examples: https://hangry-labs.github.io/MeloTTS/examples/
- GitHub: https://github.com/hangry-labs/MeloTTS
- Hangry Labs: https://nuggies.website/
- Issues: https://github.com/hangry-labs/MeloTTS/issues
- Discussions: https://github.com/hangry-labs/MeloTTS/discussions

Docker Hub comments are not monitored regularly. GitHub Issues are the best place to report bugs.

## Attribution

This is an independently maintained fork of the original MeloTTS project by Wenliang Zhao, Xumin Yu, and Zengyi Qin:

https://github.com/myshell-ai/MeloTTS

License and attribution are preserved in the repository. Original MeloTTS copyright remains with MyShell.ai; Hangry Labs maintains the Docker packaging, Web UI/API integration, examples page, documentation, release tooling, and other modifications in this fork.
