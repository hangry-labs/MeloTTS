<p align="center">
  <a href="https://hangrylabs.app/nb/software/melotts">
    <img src="assets/melotts_logo_horizontal.webp" alt="Hangry Labs Melo TTS-logo" width="1000">
  </a>
</p>

<p align="center">
  <a href="README.md">English</a> ·
  <strong>Norsk bokmål</strong> ·
  <a href="README.pl.md">Polski</a> ·
  <a href="README.ja.md">日本語</a> ·
  <a href="README.zh.md">简体中文</a> ·
  <a href="README.es.md">Español</a>
</p>

# Hangry Labs Melo TTS

Flerspråklig tekst-til-tale som er enkel å kjøre og egnet for frakoblet bruk, med nettlesergrensesnitt og HTTP-API i ett Docker-bilde.

Denne versjonen vedlikeholdes av Hangry Labs og er laget for både vanlige brukere og utviklere. Installer Docker, kjør én kommando og åpne det lokale grensesnittet. Det samme programmet tilbyr et eget API og endepunkter som er kompatible med OpenAI.

## Lytt først

[Åpne stemmeeksemplene](https://hangry-labs.github.io/MeloTTS/examples/?lang=en) for å høre alle tilgjengelige språk og engelske aksenter. Du kan også høre [SSML-dialogene](https://hangry-labs.github.io/MeloTTS/examples/ssml.html).

## Hurtigstart

Komplett bilde med vedvarende modeller og innstillinger:

```bash
docker run --rm -p 8888:8888 --gpus all -v melotts_data:/app/persistent hangrylabs/melotts:latest
```

Mindre bilde med de tre engelske modellfamiliene:

```bash
docker run --rm -p 8888:8888 --gpus all -v melotts_data:/app/persistent hangrylabs/melotts:latest_en
```

Fjern `--gpus all` for å bruke CPU. Åpne deretter [http://localhost:8888](http://localhost:8888). Den interaktive API-dokumentasjonen finnes på [http://localhost:8888/tts/docs](http://localhost:8888/tts/docs).

Det komplette bildet inkluderer engelsk, fransk, kinesisk og japansk for umiddelbar frakoblet bruk. De valgfrie spanske og koreanske pakkene krever at du godtar vilkårene og laster dem ned én gang fra fanen **System**. De lagres i `melotts_data` og fungerer deretter uten nett.

## API

OpenAI-kompatible programmer kan bruke `http://localhost:8888/v1` som basisadresse. Melo tilbyr også egen generering, strømming setning for setning, WAV, MP3, FLAC, OGG og eksperimentell SSML.

Les den [komplette norske produktbeskrivelsen og installasjonsveiledningen](https://hangrylabs.app/nb/software/melotts). Den fullstendige tekniske referansen, alle produksjonskommandoer og versjonshistorikken vedlikeholdes i den [engelske README-filen](README.md).

## Lisens

Melo TTS er fri programvare under AGPL-3.0. Du kan bruke den privat eller kommersielt, beholde bildet frakoblet, kalle API-et fra et annet program og bruke den genererte lyden. Hvis du distribuerer en endret Melo TTS-versjon eller lar andre bruke en endret Melo TTS-tjeneste over et nettverk, må du tilby dem den tilhørende kildekoden. Les også [tredjepartsmerknadene](THIRD_PARTY_NOTICES.md).

Offisielle bilder: [Docker Hub](https://hub.docker.com/r/hangrylabs/melotts/tags) · [GitHub Container Registry](https://github.com/hangry-labs/MeloTTS/pkgs/container/melotts)
