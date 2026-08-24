import unittest

from command_handler import extract_from


class CommandHandlerTests(unittest.TestCase):

    def test_basic_extraction(self):
        fake_message = FakeMessageObject(text="hey there")
        self.assertEqual(("hey", "there"), extract_from(fake_message))

    def test_weird_spaces(self):
        fake_message = FakeMessageObject(text=" hey  there ")
        self.assertEqual(("hey", "there"), extract_from(fake_message))

    def test_no_command(self):
        fake_message = FakeMessageObject(text="heythere")
        self.assertEqual(("heythere", ""), extract_from(fake_message))

    def test_nothing(self):
        fake_message = FakeMessageObject(text="")
        self.assertEqual(("", ""), extract_from(fake_message))

    def test_command_word_repeated_in_argument(self):
        fake_message = FakeMessageObject(text="gen a generator")
        self.assertEqual(("gen", "a generator"), extract_from(fake_message))


class FakeMessageObject:
    def __init__(self, text=None, attachments=None):
        self.text = text
        self.attachments = attachments
