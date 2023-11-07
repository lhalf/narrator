import requests
import json
import sensitive
import os

headers = {
    "Authorization": "Bearer {}".format(sensitive.api_key),
    "Content-Type": "application/json"
}

data = {
    "model": "tts-1",
    "input": "",
    "voice": 'onyx'
}


def create_audio_file_from(text):
    clear_old_audio_file()
    data["input"] = text
    response = requests.post("https://api.openai.com/v1/audio/speech", headers=headers, data=json.dumps(data))
    if response.status_code == 200:
        with open("tmp.mp3", "wb") as file:
            file.write(response.content)
    else:
        print("Failed to generate speech. Response:", response.text)


def clear_old_audio_file():
    if os.path.exists("tmp.mp3"):
        os.remove("tmp.mp3")
