import os

import requests

import openai_client


def create_audio_file_from_at(text, filepath):
    clear_old_audio_file(filepath)
    with openai_client.client().audio.speech.with_streaming_response.create(
        model="gpt-4o-mini-tts",
        voice="onyx",
        input=text,
    ) as response:
        response.stream_to_file(filepath)


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
