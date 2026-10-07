<p align="center">
  <a href="https://hangrylabs.app/ja/software/melotts">
    <img src="assets/melotts_logo_horizontal.webp" alt="Hangry Labs Melo TTS ロゴ" width="1000">
  </a>
</p>

<p align="center">
  <a href="README.md">English</a> ·
  <a href="README.nb.md">Norsk bokmål</a> ·
  <a href="README.pl.md">Polski</a> ·
  <strong>日本語</strong> ·
  <a href="README.zh.md">简体中文</a> ·
  <a href="README.es.md">Español</a>
</p>

# Hangry Labs Melo TTS

ブラウザー UI と HTTP API を 1 つの Docker イメージにまとめた、簡単に実行できるオフライン対応の多言語テキスト読み上げです。

Hangry Labs が保守するこのバージョンは、技術に詳しくない方にも開発者にも使いやすいように作られています。Docker をインストールし、コマンドを 1 つ実行して、ローカル UI を開くだけです。同じアプリケーションからネイティブ API と OpenAI 互換エンドポイントも利用できます。

## まず音声を試す

[日本語の音声サンプルページ](https://hangry-labs.github.io/MeloTTS/examples/?lang=ja)では、対応するすべての言語と英語アクセントを試聴できます。[SSML ダイアログ](https://hangry-labs.github.io/MeloTTS/examples/ssml.html)も公開しています。

## クイックスタート

モデルと設定を永続化する完全版イメージ：

```bash
docker run --rm -p 8888:8888 --gpus all -v melotts_data:/app/persistent hangrylabs/melotts:latest
```

3 世代の英語モデルだけを含む小さいイメージ：

```bash
docker run --rm -p 8888:8888 --gpus all -v melotts_data:/app/persistent hangrylabs/melotts:latest_en
```

CPU を使用する場合は `--gpus all` を削除してください。起動後、[http://localhost:8888/ja](http://localhost:8888/ja) を開きます。対話形式の API ドキュメントは [http://localhost:8888/tts/docs](http://localhost:8888/tts/docs) です。

完全版イメージには英語、フランス語、中国語、日本語が含まれ、すぐにオフラインで利用できます。スペイン語と韓国語のパックは、**システム**タブで提供元の条件に同意して初回のみダウンロードします。`melotts_data` に保存されるため、その後はオフラインで動作します。

## API

OpenAI 互換アプリケーションでは、ベース URL に `http://localhost:8888/v1` を指定できます。Melo はネイティブ生成、文単位のストリーミング、WAV、MP3、FLAC、OGG、実験的 SSML にも対応しています。

[日本語の製品説明とインストールガイド](https://hangrylabs.app/ja/software/melotts)をご覧ください。完全な技術資料、運用コマンド、バージョン履歴については、[英語のメイン README](README.md) を参照してください。

## ライセンス

Melo TTS は AGPL-3.0 の自由ソフトウェアです。個人利用や商用利用、オフラインでのイメージ保管、別アプリケーションからの API 呼び出し、生成音声の利用が可能です。変更した Melo TTS を配布する場合、または変更したサービスをネットワーク経由で他の利用者に提供する場合は、対応するソースコードをその利用者に提示する必要があります。[サードパーティ通知](THIRD_PARTY_NOTICES.md)も確認してください。

公式イメージ：[Docker Hub](https://hub.docker.com/r/hangrylabs/melotts/tags) · [GitHub Container Registry](https://github.com/hangry-labs/MeloTTS/pkgs/container/melotts)
