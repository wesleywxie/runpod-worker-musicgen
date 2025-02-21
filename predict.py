import os
import tempfile
import uuid
from pathlib import Path

import requests
import torchaudio
from audiocraft.data.audio import audio_write
from audiocraft.models import musicgen
from pydub import AudioSegment

from utils import is_valid_url


def generate_melody(
        prompt: str,
        duration: float,
        sample: str,
        top_k: int = 250,
        top_p: float = 0,
        temperature: float = 1,
        cfg_coef: float = 3
) -> str:
    """
    Generate an MP3 melody based on the provided prompt and parameters.

    If a valid URL is provided in `sample`, the function downloads the audio sample
    and uses it as a melody reference with chroma guidance. Otherwise, it generates
    the melody solely based on the prompt.

    The generated output is saved in the ./outputs directory and returned as an MP3 file path.

    Returns:
        str: The file path to the generated MP3 melody.
    """
    texts = [prompt]

    # Load a pretrained model and set generation parameters.
    model = musicgen.MusicGen.get_pretrained('facebook/musicgen-melody-large')
    model.set_generation_params(
        duration=duration, top_k=top_k, top_p=top_p,
        temperature=temperature, cfg_coef=cfg_coef
    )

    if is_valid_url(sample):
        # Load the audio sample from a valid URL.
        melody_waveform, sr = load_audio_from_url(sample)
        outputs = model.generate_with_chroma(
            descriptions=texts,
            melody_wavs=melody_waveform,
            melody_sample_rate=sr,
        )
    else:
        outputs = model.generate(texts)

    outputs = outputs.detach().cpu().float()

    # Ensure the output directory exists.
    output_dir = Path("./outputs")
    output_dir.mkdir(parents=True, exist_ok=True)

    # Generate a unique filename using uuid4.
    wav_filename = output_dir / f"{uuid.uuid4()}.wav"
    mp3_filename = wav_filename.with_suffix(".mp3")

    # Write the generated output to a WAV file.
    audio_write(
        str(wav_filename), outputs[0], model.sample_rate,
        strategy="loudness", loudness_headroom_db=16,
        loudness_compressor=True, add_suffix=False
    )

    # Convert the WAV file to MP3 using pydub.
    sound = AudioSegment.from_wav(str(wav_filename))
    sound.export(str(mp3_filename), format="mp3", bitrate="192k")

    # Remove the intermediate WAV file.
    try:
        os.remove(str(wav_filename))
    except OSError as e:
        print(f"Unable to remove temporary file {wav_filename}: {e}")

    return str(mp3_filename)


def load_audio_from_url(url: str):
    response = requests.get(url)
    response.raise_for_status()  # Raise an error if the download failed

    tmp_file_path = None
    waveform = None
    sample_rate = None

    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".tmp") as tmp_file:
            tmp_file.write(response.content)
            tmp_file_path = tmp_file.name

        # Load the audio file from the temporary file.
        # noinspection PyUnresolvedReferences
        waveform, sample_rate = torchaudio.load(tmp_file_path)
    finally:
        if tmp_file_path and os.path.exists(tmp_file_path):
            try:
                os.remove(tmp_file_path)
            except OSError as e:
                print(f"Failed to delete temporary file {tmp_file_path}: {e}")
    assert waveform is not None and sample_rate is not None, "Failed to load audio from URL"
    return waveform, sample_rate
