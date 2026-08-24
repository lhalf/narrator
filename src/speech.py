import os
import subprocess

import requests

import openai_client

pitch_factors = {"high": 1.8, "low": 0.7}
shift_sample_rate = 44100
vibrato_filter = "vibrato=f=6:d=0.7"


def create_audio_file_from_at(text, filepath, pitch=None, vibrato=False):
    clear_old_audio_file(filepath)
    with openai_client.client().audio.speech.with_streaming_response.create(
        model="gpt-4o-mini-tts",
        voice="onyx",
        input=text,
    ) as response:
        response.stream_to_file(filepath)
    apply_effects(filepath, pitch, vibrato)


def apply_effects(filepath, pitch, vibrato):
    filters = pitch_filters(pitch_factors[pitch]) if pitch in pitch_factors else []
    if vibrato:
        filters.append(vibrato_filter)
    if filters:
        run_filters(filepath, filters)


def pitch_filters(factor):
    resample = f"aresample={shift_sample_rate}"
    return [resample, f"asetrate={int(shift_sample_rate * factor)}", resample, f"atempo={1 / factor:.4f}"]


def run_filters(filepath, filters):
    filtered = filepath + ".filtered.mp3"
    subprocess.run([
        "ffmpeg", "-y", "-loglevel", "error", "-i", filepath, "-af", ",".join(filters), filtered,
    ], check=True)
    os.replace(filtered, filepath)


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
