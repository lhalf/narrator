import os
import subprocess

import requests

import openai_client

pitch_factors = {"high": 1.4, "low": 0.75}
shift_sample_rate = 44100


def create_audio_file_from_at(text, filepath, pitch=None):
    clear_old_audio_file(filepath)
    with openai_client.client().audio.speech.with_streaming_response.create(
        model="gpt-4o-mini-tts",
        voice="onyx",
        input=text,
    ) as response:
        response.stream_to_file(filepath)
    if pitch in pitch_factors:
        shift_pitch(filepath, pitch_factors[pitch])


def shift_pitch(filepath, factor):
    shifted = filepath + ".pitched.mp3"
    resample = f"aresample={shift_sample_rate}"
    subprocess.run([
        "ffmpeg", "-y", "-loglevel", "error", "-i", filepath,
        "-af", f"{resample},asetrate={int(shift_sample_rate * factor)},{resample},atempo={1 / factor:.4f}",
        shifted,
    ], check=True)
    os.replace(shifted, filepath)


def clear_old_audio_file(filepath):
    if os.path.exists(filepath):
        os.remove(filepath)


def audio_file_to_text_from(filepath):
    with open(filepath, "rb") as file:
        return openai_client.client().audio.transcriptions.create(
            file=file,
            model="gpt-4o-transcribe",
            response_format="text",
            language="en"
        )


def save_audio_from_url(url, file_path):
    try:
        response = requests.get(url)
        if response.status_code == 200:
            with open(file_path, 'wb') as file:
                file.write(response.content)
    except Exception as e:
        print(f"An error occurred: {e}")
