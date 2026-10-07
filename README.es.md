<p align="center">
  <a href="https://hangrylabs.app/es/software/melotts">
    <img src="assets/melotts_logo_horizontal.webp" alt="Logotipo de Hangry Labs Melo TTS" width="1000">
  </a>
</p>

<p align="center">
  <a href="README.md">English</a> ·
  <a href="README.nb.md">Norsk bokmål</a> ·
  <a href="README.pl.md">Polski</a> ·
  <a href="README.ja.md">日本語</a> ·
  <a href="README.zh.md">简体中文</a> ·
  <strong>Español</strong>
</p>

# Hangry Labs Melo TTS

Texto a voz multilingüe fácil de ejecutar, preparado para uso sin conexión, con interfaz web y API HTTP en una sola imagen Docker.

Esta versión mantenida por Hangry Labs está pensada tanto para personas sin experiencia técnica como para desarrolladores. Instala Docker, ejecuta un comando y abre la interfaz local. La misma aplicación ofrece una API nativa y endpoints compatibles con OpenAI.

## Escuchar primero

[Abre los ejemplos de voz en español](https://hangry-labs.github.io/MeloTTS/examples/?lang=es) para escuchar todos los idiomas y acentos ingleses disponibles. También puedes escuchar los [diálogos SSML](https://hangry-labs.github.io/MeloTTS/examples/ssml.html).

## Inicio rápido

Imagen completa con modelos y ajustes persistentes:

```bash
docker run --rm -p 8888:8888 --gpus all -v melotts_data:/app/persistent hangrylabs/melotts:latest
```

Imagen más pequeña con las tres familias de modelos ingleses:

```bash
docker run --rm -p 8888:8888 --gpus all -v melotts_data:/app/persistent hangrylabs/melotts:latest_en
```

Omite `--gpus all` para usar la CPU. Después abre [http://localhost:8888/es](http://localhost:8888/es). La documentación interactiva de la API está en [http://localhost:8888/tts/docs](http://localhost:8888/tts/docs).

La imagen completa incluye inglés, francés, chino y japonés para uso inmediato sin conexión. Los paquetes de español y coreano requieren aceptar sus términos y descargarlos una vez desde la pestaña **Sistema**. Se guardan en `melotts_data` y después funcionan sin conexión.

## API

Las aplicaciones compatibles con OpenAI pueden usar `http://localhost:8888/v1` como URL base. Melo también ofrece generación nativa, transmisión por frases, WAV, MP3, FLAC, OGG y SSML experimental.

Consulta la [página completa del producto y la guía de instalación en español](https://hangrylabs.app/es/software/melotts). La referencia técnica completa, todos los comandos de producción y el historial de versiones están en el [README principal en inglés](README.md).

## Licencia

Melo TTS es software libre bajo AGPL-3.0. Puedes usarlo de forma privada o comercial, mantener la imagen sin conexión, llamar a la API desde otra aplicación y utilizar el audio generado. Si distribuyes una versión modificada o permites que otras personas usen un servicio Melo TTS modificado a través de una red, debes ofrecerles el código fuente correspondiente. Consulta los [avisos de terceros](THIRD_PARTY_NOTICES.md).

Imágenes oficiales: [Docker Hub](https://hub.docker.com/r/hangrylabs/melotts/tags) · [GitHub Container Registry](https://github.com/hangry-labs/MeloTTS/pkgs/container/melotts)
