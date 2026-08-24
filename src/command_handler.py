import os
import tempfile

from fbchat_muqit import AudioAttachment

import speech


def extract_from(message_object):
    if message_object.attachments:
        for attachment in message_object.attachments:
            if isinstance(attachment, AudioAttachment):
                return extract_audio_command(attachment)
        return "", ""

    message_elements = (message_object.text or "").split()
    if not message_elements:
        return "", ""
    command = message_elements[0]
    return command, message_object.text.replace(command, "", 1).strip()


def extract_audio_command(attachment):
    audio_file = os.path.join(tempfile.gettempdir(), attachment.filename)
    speech.save_audio_from_url(attachment.playable_url, audio_file)
    query = speech.audio_file_to_text_from(audio_file).lower().replace(".", "")
    words = query.split()
    if not words:
        return "", ""
    return words[0], query.replace(words[0], "", 1).strip()
