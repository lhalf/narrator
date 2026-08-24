import os
import subprocess

import requests

import openai_client

pitch_factors = {"high": 1.8, "low": 0.7}
shift_sample_rate = 44100

effect_filters = {
    "vibrato": "vibrato=f=6:d=0.7",
    "shaky": "tremolo=f=8:d=0.8",
    "wobble": "apulsator=hz=3",
    "robot": "afftfilt=real='hypot(re,im)*sin(0)':imag='hypot(re,im)*cos(0)':win_size=512:overlap=0.75",
    "dalek": "acrusher=bits=6:mode=log,aphaser=type=t:speed=2",
    "telephone": "highpass=f=300,lowpass=f=3400,acrusher=bits=8:mode=log",
    "cave": "aecho=0.8:0.9:500|1000:0.4|0.3",
    "crowd": "chorus=0.7:0.9:55|60|75:0.4|0.32|0.3:0.25|0.4|0.3:2|2.3|1.3",
    "underwater": "lowpass=f=500,chorus=0.6:0.9:50:0.4:0.25:2",
    "backwards": "areverse",
    "drunk": "atempo=0.8,aresample=44100,asetrate=35280,aresample=44100",
    "helium": "rubberband=pitch=1.6:formant=preserved",
    "monster": "rubberband=pitch=0.6:formant=shifted",
}


def create_audio_file_from_at(text, filepath, pitch=None, effects=()):
    clear_old_audio_file(filepath)
    with openai_client.client().audio.speech.with_streaming_response.create(
        model="gpt-4o-mini-tts",
        voice="onyx",
        input=text,
    ) as response:
        response.stream_to_file(filepath)
    apply_effects(filepath, pitch, effects)


def apply_effects(filepath, pitch, effects):
    filters = pitch_filters(pitch_factors[pitch]) if pitch in pitch_factors else []
    filters.extend(effect_filters[effect] for effect in effects if effect in effect_filters)
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
