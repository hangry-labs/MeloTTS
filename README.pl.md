<p align="center">
  <a href="https://hangrylabs.app/pl/software/melotts">
    <img src="assets/melotts_logo_horizontal.webp" alt="Logo Hangry Labs Melo TTS" width="1000">
  </a>
</p>

<p align="center">
  <a href="README.md">English</a> ·
  <a href="README.nb.md">Norsk bokmål</a> ·
  <strong>Polski</strong> ·
  <a href="README.ja.md">日本語</a> ·
  <a href="README.zh.md">简体中文</a> ·
  <a href="README.es.md">Español</a>
</p>

# Hangry Labs Melo TTS

Łatwy do uruchomienia, wielojęzyczny system zamiany tekstu na mowę, przystosowany do pracy offline, z interfejsem przeglądarkowym i API HTTP w jednym obrazie Docker.

Ta wersja jest utrzymywana przez Hangry Labs i została przygotowana zarówno dla zwykłych użytkowników, jak i programistów. Zainstaluj Docker, uruchom jedno polecenie i otwórz lokalny interfejs. Ta sama aplikacja udostępnia natywne API oraz endpointy zgodne z OpenAI.

## Najpierw posłuchaj

[Otwórz przykłady głosów](https://hangry-labs.github.io/MeloTTS/examples/?lang=en), aby posłuchać wszystkich dostępnych języków i angielskich akcentów. Możesz również odsłuchać [dialogi SSML](https://hangry-labs.github.io/MeloTTS/examples/ssml.html).

## Szybki start

Pełny obraz z trwałym przechowywaniem modeli i ustawień:

```bash
docker run --rm -p 8888:8888 --gpus all -v melotts_data:/app/persistent hangrylabs/melotts:latest
```

Mniejszy obraz z trzema rodzinami modeli angielskich:

```bash
docker run --rm -p 8888:8888 --gpus all -v melotts_data:/app/persistent hangrylabs/melotts:latest_en
```

Usuń `--gpus all`, aby użyć procesora. Następnie otwórz [http://localhost:8888](http://localhost:8888). Interaktywna dokumentacja API jest dostępna pod adresem [http://localhost:8888/tts/docs](http://localhost:8888/tts/docs).

Pełny obraz zawiera język angielski, francuski, chiński i japoński do natychmiastowego użycia offline. Opcjonalne pakiety hiszpański i koreański wymagają zaakceptowania warunków i jednorazowego pobrania na karcie **System**. Pliki są przechowywane w `melotts_data`, dzięki czemu później działają bez połączenia z internetem.

## API

Aplikacje zgodne z OpenAI mogą używać `http://localhost:8888/v1` jako adresu bazowego. Melo udostępnia również natywne generowanie, strumieniowanie zdanie po zdaniu, formaty WAV, MP3, FLAC i OGG oraz eksperymentalną obsługę SSML.

Przeczytaj [pełny polski opis produktu i instrukcję instalacji](https://hangrylabs.app/pl/software/melotts). Pełna dokumentacja techniczna, wszystkie polecenia produkcyjne i historia wersji są utrzymywane w [angielskim README](README.md).

## Licencja

Melo TTS jest wolnym oprogramowaniem na licencji AGPL-3.0. Możesz używać go prywatnie lub komercyjnie, przechowywać obraz offline, wywoływać API z oddzielnej aplikacji i korzystać z wygenerowanego dźwięku. Jeśli rozpowszechniasz zmodyfikowaną wersję Melo TTS lub udostępniasz innym zmodyfikowaną usługę Melo TTS przez sieć, musisz zaoferować im odpowiadający kod źródłowy. Przeczytaj również [informacje o komponentach zewnętrznych](THIRD_PARTY_NOTICES.md).

Oficjalne obrazy: [Docker Hub](https://hub.docker.com/r/hangrylabs/melotts/tags) · [GitHub Container Registry](https://github.com/hangry-labs/MeloTTS/pkgs/container/melotts)
