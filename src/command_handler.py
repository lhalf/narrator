import unittest
import fbchat
import speech


def extract_from(message_object):
    if message_object.attachments:
        for attachment in message_object.attachments:
            if isinstance(attachment, fbchat.AudioAttachment):
                return extract_audio_command(attachment)
    else:
        message_elements = message_object.text.split()
        if not message_elements:
            return "", ""
        command = message_elements[0]
        return command, message_object.text.replace(command, "").strip()


def extract_audio_command(attachment):
    speech.save_audio_from_url(attachment.url, attachment.filename)
    query = speech.audio_file_to_text_from(attachment.filename).lower().replace(".", "")
    command = query.split()[0]
    return command, query.replace(command, "").strip()


class CommandHandlerTests(unittest.TestCase):
    class FakeMessageObject:
        def __init__(self, text=None, attachments=None):
            self.text = text
            self.attachments = attachments

    def test_basic_extraction(self):
        fake_message = self.FakeMessageObject(text="hey there")
        self.assertEqual(("hey", "there"), extract_from(fake_message))

    def test_weird_spaces(self):
        fake_message = self.FakeMessageObject(text=" hey  there ")
        self.assertEqual(("hey", "there"), extract_from(fake_message))

    def test_no_command(self):
        fake_message = self.FakeMessageObject(text="heythere")
        self.assertEqual(("heythere", ""), extract_from(fake_message))

    def test_nothing(self):
        fake_message = self.FakeMessageObject(text="")
        self.assertEqual(("", ""), extract_from(fake_message))


if __name__ == '__main__':
    unittest.main()
