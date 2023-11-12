import requests
import json
import sensitive
import os
import openai

headers = {
    "Authorization": "Bearer {}".format(sensitive.api_key),
    "Content-Type": "application/json"
}

data = {
    "model": "tts-1",
    "input": "",
    "voice": 'onyx'
}


def create_audio_file_from_at(text, filepath):
    clear_old_audio_file(filepath)
    data["input"] = text
    response = requests.post("https://api.openai.com/v1/audio/speech", headers=headers, data=json.dumps(data))
    if response.status_code == 200:
        with open(filepath, "wb") as file:
            file.write(response.content)
    else:
        print("Failed to generate speech. Response:", response.text)


def clear_old_audio_file(filepath):
    if os.path.exists(filepath):
        os.remove(filepath)


files = {
    'model': (None, 'whisper-1'),
}


def audio_file_to_text_from(filepath):
    return openai.Audio.transcribe(
        file=open(filepath, 'rb'),
        model="whisper-1",
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
