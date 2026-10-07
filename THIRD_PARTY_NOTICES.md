# Third-Party Notices

Melo TTS combines software, data, model weights, and browser assets from multiple
projects. The combined application source is distributed under AGPL-3.0-only, but
that does not replace the licenses or notices that apply to individual components.

This inventory was reviewed on 2026-10-07. Links identify the upstream source and
model cards used for the review. Redistributors should repeat the review before
changing a dependency or model revision.

## Source provenance

### Hangry Labs modifications

Docker packaging, the browser application, API integration, documentation,
release tooling, and other fork-specific modifications are copyright 2026
Hangry Labs and contributors and are distributed under AGPL-3.0-only.

### Bert-VITS2

The inference architecture and portions of the text-processing implementation are
derived from [Bert-VITS2](https://github.com/fishaudio/Bert-VITS2), distributed
under GNU AGPL version 3. This inherited strong-copyleft code is the reason the
combined Melo TTS application is distributed under AGPL-3.0-only. The complete
AGPL text is in [`LICENSE`](LICENSE).

### Original MeloTTS

This project is based on [MeloTTS](https://github.com/myshell-ai/MeloTTS) by
Wenliang Zhao, Xumin Yu, Zengyi Qin, MyShell.ai, and its contributors. MyShell.ai
published the original MeloTTS repository with an MIT license and the notice:

> Copyright (c) 2024 MyShell.ai

The preserved license is in [`LICENSES/MIT-MeloTTS.txt`](LICENSES/MIT-MeloTTS.txt).
The combined project is nevertheless distributed under AGPL-3.0-only because it
also contains AGPL-covered Bert-VITS2-derived material.

### PaddleSpeech tone sandhi

`melo/text/tone_sandhi.py` retains the PaddlePaddle copyright and Apache-2.0
header from [PaddleSpeech](https://github.com/PaddlePaddle/PaddleSpeech). The
Apache License 2.0 is reproduced in
[`LICENSES/Apache-2.0.txt`](LICENSES/Apache-2.0.txt).

### Tacotron number normalization

`melo/text/english_utils/number_norm.py` contains code originating in
[keithito/tacotron](https://github.com/keithito/tacotron), copyright 2017 Keith
Ito and licensed under MIT. The preserved license is in
[`LICENSES/MIT-Tacotron.txt`](LICENSES/MIT-Tacotron.txt).

### CMU Pronouncing Dictionary

`melo/text/cmudict.rep` contains the CMU Pronouncing Dictionary 0.6. Its original
copyright and unrestricted-use notice are retained at the beginning of that file.

## Bundled browser components

- [WaveSurfer.js](https://github.com/katspaugh/wavesurfer.js): BSD-3-Clause. Its
  license is retained in `melo/standalone_ui/static/vendor/wavesurfer/LICENSE`.
- [Lucide](https://github.com/lucide-icons/lucide): ISC, with MIT-licensed Feather
  icons. Its notices are retained in `melo/standalone_ui/static/vendor/lucide/LICENSE`.

## Runtime dependencies

Python packages remain under their own licenses. Their package metadata and
license files are preserved in each installed `.dist-info` directory in the
Docker image. Notable copyleft or separately licensed runtime components include:

- `pykakasi`: GPL-3.0-or-later.
- `distance`: GPL-2.0-or-later, as declared by its distributed package license.
- `num2words`: LGPL.
- FFmpeg and its Debian libraries: the Debian build declares GPL-3.0-or-later as
  its effective license. Its licenses and source-package notices are retained
  under `/usr/share/doc` in the image.
- NVIDIA CUDA runtime libraries installed with the CUDA-enabled PyTorch wheels:
  NVIDIA proprietary terms, retained in their `.dist-info/licenses` directories.

The AGPL license for Melo TTS does not replace these component licenses.

## Models and language resources

### Melo TTS voice checkpoints

The standard image embeds the following MyShell.ai model repositories, whose model
cards declare MIT:

- `myshell-ai/MeloTTS-English`
- `myshell-ai/MeloTTS-English-v2`
- `myshell-ai/MeloTTS-English-v3`
- `myshell-ai/MeloTTS-French`
- `myshell-ai/MeloTTS-Japanese`
- `myshell-ai/MeloTTS-Chinese`

The English-family image embeds only the three English repositories. The MIT
terms reproduced in `LICENSES/MIT-MeloTTS.txt` apply to these MyShell.ai model
artifacts according to their published model-card metadata.

Spanish `myshell-ai/MeloTTS-Spanish` and Korean `myshell-ai/MeloTTS-Korean`
checkpoints are not embedded in published images. An operator may explicitly
download either pinned checkpoint from Hugging Face into their persistent local
volume after reviewing the associated encoder terms below.

### Language encoders

- `google-bert/bert-base-uncased`: Apache-2.0.
- `google-bert/bert-base-multilingual-uncased`: Apache-2.0.
- `dbmdz/bert-base-french-europeana-cased`: MIT.
- `tohoku-nlp/bert-base-japanese-v3`: Apache-2.0.
- `dccuchile/bert-base-spanish-wwm-uncased` (BETO) is not distributed in the
  Docker image. Its model card says CC BY 4.0
  best describes the authors' intentions and warns that some training datasets may
  have incompatible terms, particularly for commercial use. Users should review
  the [BETO model card](https://huggingface.co/dccuchile/bert-base-spanish-wwm-uncased)
  for their use case and provide attribution to the BETO authors.
- `kykim/bert-kor-base` is not distributed in the Docker image. Its Hugging Face
  model card does not declare a license.
  The linked [LMkor project](https://github.com/kiyoungkim1/LMkor) is Apache-2.0,
  but its README instructs commercial model users to arrange a free MOU with the
  author. Hangry Labs does not grant rights to it; operators must explicitly
  review its terms before the application downloads it from Hugging Face into
  their own persistent volume.

### Dictionaries and language data

- UniDic is distributed under its upstream GPL/LGPL/BSD choice. The downloaded
  dictionary keeps its `COPYING`, `BSD`, `GPL`, `LGPL`, and `AUTHORS` files inside
  the installed `unidic/dicdir/licenses` directory.
- `unidic-lite` retains the corresponding dictionary notices in its installed
  package.
- NLTK resources and pronunciation data retain their upstream notices in the
  installed NLTK data/package directories.

## Generated audio

The software license does not normally apply to audio generated from user input.
Users remain responsible for rights in their input, selected model, voice use,
and resulting audio under applicable law and the model-specific terms above.
