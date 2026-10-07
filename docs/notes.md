# Hangry Labs Melo TTS Development Notes

Main project links:

- GitHub: https://github.com/hangry-labs/MeloTTS
- Voice examples: https://hangry-labs.github.io/MeloTTS/examples/
- SSML dialogues: https://hangry-labs.github.io/MeloTTS/examples/ssml.html
- Docker Hub: https://hub.docker.com/r/hangrylabs/melotts/tags
- GitHub Container Registry: https://github.com/hangry-labs/MeloTTS/pkgs/container/melotts
- Hangry Labs: https://hangrylabs.app/

## Before forking any project

Do this before writing code or publishing an image. A famous or well-maintained
upstream can still contain material that its top-level license does not cover.

1. Read the root `LICENSE`, `COPYING`, and `NOTICE` files.
2. Search source headers and documentation for copied or derived projects:

   ```powershell
   rg -n "Copyright|License|licensed|derived from|based on|from https" .
   ```

3. Check the license of the original source for every substantial copied file.
   Use Git history to confirm which license applied when the code was copied.
4. Review model weights, tokenizers, dictionaries, datasets, fonts, JavaScript,
   and artwork separately. A code license does not automatically license models
   or training data.
5. Check direct and transitive runtime dependencies. Installed Python packages
   normally keep their notices in `<package>.dist-info/licenses`.
6. Record findings in a committed third-party notice before publishing.
7. Pin reviewed model revisions so a later upstream change cannot silently alter
   either the artifact or its terms.
8. Re-run the review whenever a dependency, model revision, or copied component
   changes.

For Melo TTS, the combined application is `AGPL-3.0-only`; inherited and model
terms are recorded in `THIRD_PARTY_NOTICES.md`. AGPL permits private and commercial
use. Modified versions distributed to others require corresponding source, and a
modified network service must prominently offer that source to its users.

##Tools

    winget install --id=astral-sh.uv -e

## Version Management

Do not create release tags by hand. Root `VERSION` is authoritative. Preview the
complete version and documentation transition with `task release DRY_RUN=1`, then
follow the [Release](#release) procedure after the candidate has been reviewed.

## Docker Usage
### CPU Version
`docker run -p 8888:8888 -v melotts_data:/app/persistent hangrylabs/melotts`

### GPU Version
`docker run --gpus all -p 8888:8888 -v melotts_data:/app/persistent hangrylabs/melotts`

## Test locally

Install FFmpeg if you run the Python service outside Docker and want Ogg Vorbis, Opus, AAC,
pitch, tempo, volume, or loudness normalization. Neutral output controls do not invoke the
effects pass. The Docker images already include FFmpeg.

### Build image  
You need docker to be working. (Example : Docker Desktop)  
`task image`

Local task builds first check the LAN UniDic mirror at `http://192.168.0.54:5080`. If it is unavailable, the build automatically uses the checksum-verified public source. A plain `docker build -t melotts:test .` always uses the portable public default. GitHub Actions stores the same verified archive in its own build cache.

### Run image  
`docker run -p 8888:8888 --gpus all -v melotts_data:/app/persistent melotts:test`

### Run image - offline mode
`docker run -p 8888:8888 -it --rm --gpus all --network none -v melotts_data:/app/persistent melotts:test`

### Run image - english only
`docker run -p 8888:8888 --gpus all -e TTS_LANGUAGES=EN melotts:test`

### Investigate image without running it (Used to slim the image and see files)
`docker run -it --rm --entrypoint bash hangrylabs/melotts:latest`

### Check UI
Open http://localhost:8888

### Rapid local UI/API loop
After building an image once, use the bind-mounted tasks for backend and browser UI edits:

```bash
task localdev
task localapi
```

These mount `melo/`, `assets`, and `VERSION` into the container so most UI/API changes do not require a Docker rebuild. Both also mount `melotts_data` at `/app/persistent`. Normal tasks load the six baked core model families; use `task localrunsmall` for the three English model families only.

### Enable Spanish or Korean once, then keep it offline

1. Start Melo TTS with the `melotts_data` volume mounted.
2. Open `http://localhost:8888`, select **System**, and find **Optional online packs**.
3. Switch on Spanish or Korean, read the warning, open the upstream terms, then choose **Accept, download, and enable**.
4. Keep using the same `-v melotts_data:/app/persistent` option for later image versions.

The first activation needs internet. Later starts can use `--network none` because
the downloaded checkpoint, encoder, acceptance marker, and enabled setting are in
the volume. Turning a pack off releases it from memory but does not delete it.

### Check API - ping
```bash
curl -v http://localhost:8888/tts/ping
```

### Check OpenAI-compatible API

List models and loaded voices:

```bash
curl -v http://localhost:8888/v1/models
curl -v http://localhost:8888/v1/audio/voices
```

Generate the default sentence-streamed MP3 response:

```bash
curl -v -X POST http://localhost:8888/v1/audio/speech ^
  -H "Content-Type: application/json" ^
  -d "{\"model\":\"melotts\",\"input\":\"Hello from the OpenAI-compatible API.\",\"voice\":\"EN-Newest\"}" ^
  --output openai-hello.mp3
```

Set `MELOTTS_API_KEY` in the server environment only when bearer authentication is required. OpenAI SDKs may still require a non-empty local placeholder key even when the server does not enforce one.

### Check API - tts
```bash
curl -v -X POST http://localhost:8888/tts/generate ^
  -H "Content-Type: application/json" ^
  -d "{\"text\":\"Hello world. I wanted to test this and see if this works properly\",\"speed\":1.0,\"language\":\"EN\",\"speaker_id\":\"EN-BR\",\"sdp_ratio\":\"0.21\",\"noise_scale\":\"0.61\",\"noise_scale_w\":\"0.81\"}" ^
  --output hello.wav
```

Legacy endpoint kept for old clients:

```bash
curl -v -X POST http://localhost:8888/tts/convert/tts ^
  -H "Content-Type: application/json" ^
  -d "{\"text\":\"Legacy endpoint smoke test\",\"language\":\"EN\",\"speaker_id\":\"EN-BR\"}" ^
  --output legacy-hello.wav
```

### Check API - compact output
```bash
curl -v -X POST http://localhost:8888/tts/generate ^
  -H "Content-Type: application/json" ^
  -d "{\"text\":\"Hello world. I wanted to test MP3 output\",\"language\":\"EN\",\"speaker_id\":\"EN-BR\",\"format\":\"mp3\"}" ^
  --output hello.mp3
```

Available response formats:
```bash
curl -v http://localhost:8888/tts/formats
```

The UI has an Output Format dropdown and defaults to MP3. The API remains WAV-by-default when `format` is omitted.

### Check API - SSML dialogue

SSML must always be enabled explicitly with `"input_type":"ssml"`. This example switches between two loaded language models and inserts an exact pause:

```bash
curl -v -X POST http://localhost:8888/tts/generate ^
  -H "Content-Type: application/json" ^
  -d "{\"input_type\":\"ssml\",\"text\":\"<speak><voice name='EN-Newest'>Good morning.</voice><break time='250ms'/><voice name='ES'>Buenos dias.</voice></speak>\",\"language\":\"EN_NEWEST\",\"speaker_id\":\"EN-Newest\",\"format\":\"mp3\"}" ^
  --output dialogue.mp3
```

Use the running service to confirm exact speaker names before writing dialogue:

```bash
curl -v http://localhost:8888/tts/voices
```

The browser UI has an orange SSML mode button and an `i` button with the complete supported subset. Plain text remains the default. Melo uses separate language checkpoints, so `<lang>` can retain a speaker only when that speaker exists in the target model. Use `<voice>` to switch models and speakers for reliable multilingual dialogue. Direct `<phoneme>` input is intentionally unsupported.

### Regenerate the published SSML dialogue examples

Start the full local service first. The generation task sends every checked-in script to the live API, verifies the response metadata and duration, and only then replaces the MP3 file:

```powershell
task localrun
task imagewait
task ssml-examples
```

Generate just one named example while editing it:

```powershell
task ssml-examples SSML_EXAMPLE="Studio readiness"
```

Use another server by setting `SSML_BASE_URL`, for example `task ssml-examples SSML_BASE_URL=http://server:8888`. The script definitions live in `scripts/generate-ssml-examples.ps1`; the public page is `examples/ssml.html`. Keep that PowerShell script ASCII-only and represent non-ASCII dialogue with `\uXXXX` escapes through `Expand-UnicodeEscapes`. Task runs it with Windows PowerShell 5.1, which can otherwise corrupt UTF-8 source text before it reaches the API.

### Check API - streaming tts
Streaming is sentence-level. The model makes one audio segment per sentence, then the API sends that segment immediately.

Raw PCM stream, good for applications that can read `pcm_s16le`:

```bash
curl -v -X POST http://localhost:8888/tts/stream ^
  -H "Content-Type: application/json" ^
  -d "{\"text\":\"First sentence. Second sentence.\",\"language\":\"EN\",\"speaker_id\":\"EN-BR\"}" ^
  --output hello-stream.pcm
```

MP3 stream, good for easier playback when the runtime has MP3 encoding:

```bash
curl -v -X POST http://localhost:8888/tts/stream ^
  -H "Content-Type: application/json" ^
  -d "{\"text\":\"First sentence. Second sentence.\",\"language\":\"EN\",\"speaker_id\":\"EN-BR\",\"stream_format\":\"mp3\"}" ^
  --output hello-stream.mp3
```

Available streaming formats:

```bash
curl -v http://localhost:8888/tts/stream-formats
```

### Check API - languages
```bash
curl -v http://localhost:8888/tts/languages
```

### Check API - languages
```bash
curl -v "http://localhost:8888/tts/speakers?language=EN"
```

### Clean docker
`docker system prune -a --volumes`

## Common Operations
- Port 8888 is exposed for web interface
- Use `--gpus all` only if NVIDIA drivers and Docker GPU support is installed


## Dependency management

Python dependency files in this repo:

- `requirements.in` is the short human-edited list. It says what this project directly needs.
- `requirements.txt` is the full resolved/pinned list. Docker installs this file so builds are repeatable.
- `uv` is the resolver. It reads `requirements.in`, figures out all transitive dependencies, and writes `requirements.txt`.

Go comparison:

- `requirements.in` is a little like the dependencies you intentionally care about.
- `requirements.txt` is closer to a lock file: exact versions that are known to work.
- `uv pip compile` is the command that refreshes the lock-like file.

Install `uv` on Windows:

```bash
winget install --id=astral-sh.uv -e
```

Refresh Python dependencies:

```bash
task deps
```

That task deliberately resolves for the Linux/Python 3.13 Docker runtime, even when it is
run from Windows. The full command is:

```bash
uv pip compile requirements.in --python-version 3.13 --python-platform x86_64-manylinux_2_36 --index-strategy unsafe-best-match --upgrade --no-header --no-annotate --output-file requirements.txt
```

After this command, inspect `requirements.txt`. It may change many indirect packages even if `requirements.in` is small.

Add a new direct dependency:

1. Add the package name to `requirements.in`.
2. Run the resolver command above.
3. Build and test Docker.

Remove a dependency:

1. Remove it from `requirements.in`.
2. Run the resolver command above.
3. Check whether it disappeared from `requirements.txt`.
4. Build and test Docker.

Docker remains the expected validation environment for dependency upgrades:

```bash
task imagesmall
task localapi
```

Check dependency consistency inside the running container:

```bash
docker exec melotts_local python -m pip check
```

Run all lightweight checks, including a real wheel build and wheel-content check:

```bash
task validate
```

Python package metadata lives in `pyproject.toml`. Root `VERSION` remains the easy-to-edit
display and release version; the release task updates the standards-compliant package
version in `pyproject.toml` automatically (`v1.0.0-SNAPSHOT` becomes `1.0.0.dev0`).

Print key runtime versions:

```bash
docker exec melotts_local python -c "import fastapi, starlette, pydantic, torch, torchaudio, transformers, numpy, soundfile; print('fastapi', fastapi.__version__); print('starlette', starlette.__version__); print('pydantic', pydantic.__version__); print('torch', torch.__version__); print('torchaudio', torchaudio.__version__); print('transformers', transformers.__version__); print('numpy', numpy.__version__); print('soundfile', soundfile.__version__)"
```

## Release

Root `VERSION` is the release source of truth. A standard patch release can be prepared from a clean working tree with:

    task release

The task reads the version directly from `VERSION`. It requires a snapshot such as
`v1.0.0-SNAPSHOT`, validates the project, commits `VERSION=v1.0.0`, creates annotated
tag `v1.0.0`, then commits the next patch snapshot such as `v1.0.1-SNAPSHOT` and its
new README development heading.

Preview the release without changing files, creating commits, building an image, or making a tag:

    task release DRY_RUN=1

Override only the next development version when the following release should not be a patch:

    task release NEXT_VERSION=v1.1.0-SNAPSHOT

Skip the release validation only when the exact candidate image and checks were already completed:

    task release SKIP_VALIDATION=1

Private agent memory stays under the locally ignored `.ai/` directory and root
`AGENTS.md`. The release task refuses to proceed if either path is tracked and
requires every public repository file to be clean.

Publish the prepared release with:

    task releasepush RELEASE_VERSION=v1.0.0

This pushes the release tag first so GitHub Actions runs the tag build, then pushes `main` with the next `-SNAPSHOT` version.

The unified `.github/workflows/docker-build.yml` workflow publishes the full and English-family tags to both Docker Hub and GitHub Container Registry. Model preloading is strict: a missing model fails the build instead of publishing an incomplete image.

After both release images publish, inspect each readable tag and copy the first
`Digest:` value, which is the top-level OCI index digest:

    docker buildx imagetools inspect hangrylabs/melotts:v1.0.0
    docker buildx imagetools inspect hangrylabs/melotts:v1.0.0_en
    docker buildx imagetools inspect ghcr.io/hangry-labs/melotts:v1.0.0
    docker buildx imagetools inspect ghcr.io/hangry-labs/melotts:v1.0.0_en

The Docker Hub and GHCR digest for each variant must match. Update the completed
release commands in `README.md` and `docs/dockerhub.md` to use
`<tag>@sha256:<top-level-digest>`. Do not use a platform child-manifest or
attestation digest. Keep rolling `latest` and `latest_en` snapshot commands
unpinned.
