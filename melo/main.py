import warnings
from pathlib import Path

import click

LANGUAGES = ["EN", "EN_V2", "EN_NEWEST", "ES", "FR", "ZH", "JP", "KR"]


def _speaker_key(value):
    return value.strip().upper().replace("_", "-")


def resolve_speaker_id(speaker_ids, requested_speaker=None):
    if not speaker_ids:
        raise click.ClickException("The selected model does not expose any speakers.")
    if not requested_speaker:
        return next(iter(speaker_ids.values()))

    requested_key = _speaker_key(requested_speaker)
    for speaker_name, speaker_id in speaker_ids.items():
        if _speaker_key(speaker_name) == requested_key:
            return speaker_id

    available = ", ".join(speaker_ids)
    raise click.BadParameter(
        f"unknown speaker '{requested_speaker}'. Available speakers: {available}",
        param_hint="--speaker",
    )


@click.command()
@click.argument("text")
@click.argument("output_path", type=click.Path(dir_okay=False, path_type=Path))
@click.option("--file", "-f", is_flag=True, help="Read text from a UTF-8 file.")
@click.option(
    "--language",
    "-l",
    default="EN",
    show_default=True,
    type=click.Choice(LANGUAGES, case_sensitive=False),
    help="Model language.",
)
@click.option(
    "--speaker",
    "-spk",
    default=None,
    help="English speaker name. Defaults to the first speaker exposed by the selected model.",
)
@click.option("--speed", "-s", default=1.0, show_default=True, type=float)
@click.option("--device", "-d", default="auto", show_default=True)
def main(text, file, output_path, language, speaker, speed, device):
    """Synthesize TEXT to OUTPUT_PATH."""
    if file:
        source_path = Path(text)
        if not source_path.is_file():
            raise click.ClickException(
                f"Text file '{source_path}' was not found. Remove --file to pass literal text."
            )
        text = source_path.read_text(encoding="utf-8").strip()

    if not text.strip():
        raise click.ClickException("Text must not be empty.")

    language = language.upper()
    is_english_variant = language in {"EN", "EN_V2", "EN_NEWEST"}
    if not is_english_variant and speaker:
        warnings.warn(
            "A speaker was specified for a non-English model and will be ignored.",
            stacklevel=2,
        )
        speaker = None

    from melo.api import TTS

    model = TTS(language=language, device=device)
    speaker_id = resolve_speaker_id(model.hps.data.spk2id, speaker)
    model.tts_to_file(text, speaker_id, output_path, speed=speed)


if __name__ == "__main__":
    main()
