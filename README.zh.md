<p align="center">
  <a href="https://hangrylabs.app/zh/software/melotts">
    <img src="assets/melotts_logo_horizontal.webp" alt="Hangry Labs Melo TTS 标志" width="1000">
  </a>
</p>

<p align="center">
  <a href="README.md">English</a> ·
  <a href="README.nb.md">Norsk bokmål</a> ·
  <a href="README.pl.md">Polski</a> ·
  <a href="README.ja.md">日本語</a> ·
  <strong>简体中文</strong> ·
  <a href="README.es.md">Español</a>
</p>

# Hangry Labs Melo TTS

易于运行、适合离线使用的多语言文本转语音工具，在一个 Docker 镜像中同时提供浏览器界面和 HTTP API。

这个由 Hangry Labs 维护的版本同时面向普通用户和开发者。安装 Docker、运行一条命令，然后打开本地界面即可使用。同一个应用还提供原生 API 和 OpenAI 兼容接口。

## 先听效果

[打开中文声音示例](https://hangry-labs.github.io/MeloTTS/examples/?lang=zh)，试听所有可用语言和英语口音。还可以试听[多角色 SSML 对话](https://hangry-labs.github.io/MeloTTS/examples/ssml.html)。

## 快速开始

包含完整模型并持久保存设置：

```bash
docker run --rm -p 8888:8888 --gpus all -v melotts_data:/app/persistent hangrylabs/melotts:latest
```

仅包含三代英语模型的小型镜像：

```bash
docker run --rm -p 8888:8888 --gpus all -v melotts_data:/app/persistent hangrylabs/melotts:latest_en
```

使用 CPU 时请移除 `--gpus all`。启动后打开 [http://localhost:8888/zh](http://localhost:8888/zh)。交互式 API 文档位于 [http://localhost:8888/tts/docs](http://localhost:8888/tts/docs)。

完整镜像内置英语、法语、中文和日语，可立即离线使用。可选的西班牙语与韩语包需要在**系统**页确认上游条款并联网下载一次。文件保存在 `melotts_data` 中，之后即可离线使用。

## API

兼容 OpenAI 的应用可以将 `http://localhost:8888/v1` 设置为 API 基础地址。Melo 还支持原生生成、按句流式输出、WAV、MP3、FLAC、OGG，以及实验性 SSML。

请查看[完整的中文产品介绍和安装指南](https://hangrylabs.app/zh/software/melotts)。完整技术参考、生产运行命令和版本历史请参阅[英文主 README](README.md)。

## 许可证

Melo TTS 是采用 AGPL-3.0 的自由软件。你可以私下或商业使用、离线保存镜像、从独立应用调用 API，并使用生成的音频。如果你分发修改后的 Melo TTS，或通过网络向其他用户提供修改后的 Melo TTS 服务，则必须向这些用户提供对应的完整源代码。另请阅读[第三方声明](THIRD_PARTY_NOTICES.md)。

官方镜像：[Docker Hub](https://hub.docker.com/r/hangrylabs/melotts/tags) · [GitHub Container Registry](https://github.com/hangry-labs/MeloTTS/pkgs/container/melotts)
