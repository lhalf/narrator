import asyncio
import os
import random
import re
import tempfile
from collections import namedtuple

from fbchat_muqit import Client, EventType

import bikes
import chat_history
import command_handler
import crime
import generate_image
import generate_text
import messenger
import osrs
import people
import speech

cookies_file = "cookies.json"
temp_directory = tempfile.gettempdir()
generated_image_file = os.path.join(temp_directory, "narrator_image.png")
voice_clip_file = os.path.join(temp_directory, "narrator_voice.mp3")
crime_plot_file = os.path.join(temp_directory, "narrator_plot.png")

default_summary_length = 50
echoed_image_limit = 100
failure_reason_limit = 200

Command = namedtuple("Command", ["usage", "description", "run", "returns_text"])


class MessageHandler:

    def __init__(self, client):
        self.messenger = messenger.Messenger(client)
        self.history = chat_history.ChatHistory(client)
        self.osrs_items = osrs.OSRSItems()
        self.people_to_respond_to = []
        self.respond_to = people.RespondTo(self.people_to_respond_to)
        self.all_bikes = bikes.AllBikes()
        self.commands = self.build_commands()

    def build_commands(self):
        return {
            "help": Command("", "show this message", self.help, True),
            "summarise": Command("[n]", "summarise the last n messages", self.summarise, True),
            "quote": Command("", "post a random message from this thread", self.quote, True),
            "examine": Command("<item>", "look up the OSRS examine text for an item", self.examine, True),
            "bike": Command("<name>", "look up a bike's specs", self.bike, True),
            "find": Command("[summarise] <text>", "search this thread's history for a phrase",
                            self.find, False),
            "gen": Command("<prompt>", "generate an image", self.gen, False),
            "genfill": Command("<prompt>", "regenerate the masked part of the group photo", self.genfill, False),
            "say": Command("<text>", "reply with a voice clip", self.say, False),
            "crime": Command("<postcode>", "map link and crime plot for a postcode", self.crime, False),
            "echoimages": Command("", "resend recent images in this thread", self.echoimages, False),
            "randomimage": Command("", "post a random image from this thread", self.randomimage, False),
        }

    async def on_message(self, message):
        if message.sender_id == self.messenger.uid:
            return

        try:
            await self.respond_to_message(message)
        except Exception as error:
            print(f"Failed to handle message: {error!r}")
            await self.report_failure(message, error)

    async def respond_to_message(self, message):
        if self.is_mentioned_in(message):
            await self.reply_to_mention(message)
            return

        name, user_input = await asyncio.to_thread(command_handler.extract_from, message)
        command = self.commands.get(name.lower())
        if not command:
            await self.reply_as_person_to(message)
            return

        text = await command.run(message, user_input)
        if text is not None:
            await self.reply_with_text(message, text)

    async def report_failure(self, message, error):
        try:
            await self.reply_with_text(message, failure_message_for(error))
        except Exception as reporting_error:
            print(f"Could not report failure: {reporting_error!r}")

    async def help(self, message, user_input):
        return "\n\n".join(help_line_for(name, command) for name, command in self.commands.items())

    async def summarise(self, message, user_input):
        messages = await self.history.messages_in(message.thread_id, message_count_in(user_input))
        transcript = await self.history.transcript_of(messages)
        return await asyncio.to_thread(generate_text.summary_of, transcript)

    async def quote(self, message, user_input):
        return await self.history.random_quote_from(message.thread_id)

    async def examine(self, message, user_input):
        return self.osrs_items.get_examine_text_from_item_name(user_input)

    async def bike(self, message, user_input):
        return await asyncio.to_thread(self.all_bikes.find, user_input)

    async def find(self, message, user_input):
        modifier, remainder = split_command(user_input)
        if modifier.lower() == "summarise":
            return await self.summarise_search(message, remainder)
        for result in await self.history.search_results_for(message.thread_id, user_input):
            await self.reply_with_text(message, result)

    async def summarise_search(self, message, query):
        results = await self.history.search_for(message.thread_id, query)
        if not results:
            return f"Nothing found for \"{query}\""
        found = "\n".join(chat_history.line_for(result) for result in results)
        return await asyncio.to_thread(generate_text.summary_of, found)

    async def gen(self, message, user_input):
        await asyncio.to_thread(generate_image.save_generated_at, user_input, generated_image_file)
        await self.messenger.send_image(message.thread_id, generated_image_file, reply_to=message.id)

    async def genfill(self, message, user_input):
        await asyncio.to_thread(generate_image.save_filled_at, user_input,
                                "group_full.png", "group.png", generated_image_file)
        await self.messenger.send_image(message.thread_id, generated_image_file, reply_to=message.id)

    async def say(self, message, user_input):
        text = await self.spoken_text_for(message, user_input)
        await asyncio.to_thread(speech.create_audio_file_from_at, text, voice_clip_file)
        await self.messenger.send_voice_clip(message.thread_id, voice_clip_file, reply_to=message.id)

    async def crime(self, message, user_input):
        lat, long = await asyncio.to_thread(crime.get_lat_long_from_postcode, user_input)
        if lat is None:
            await self.reply_with_text(message, f"Could not find postcode {user_input}")
            return
        await self.reply_with_text(message, map_link_for(lat, long))
        await asyncio.to_thread(crime.create_plot_from_postcode_at, user_input, crime_plot_file)
        await self.messenger.send_image(message.thread_id, crime_plot_file, reply_to=message.id)

    async def echoimages(self, message, user_input):
        for image_url in await self.history.image_urls_in(message.thread_id, echoed_image_limit):
            await self.messenger.download(image_url, generated_image_file)
            await self.messenger.send_image(message.thread_id, generated_image_file)

    async def randomimage(self, message, user_input):
        image_urls = await self.history.image_urls_in(message.thread_id, chat_history.image_search_limit)
        if not image_urls:
            await self.reply_with_text(message, "No images found")
            return
        await self.messenger.download(random.choice(image_urls), generated_image_file)
        await self.messenger.send_image(message.thread_id, generated_image_file, reply_to=message.id)

    async def spoken_text_for(self, message, user_input):
        name, remainder = split_command(user_input)
        command = self.commands.get(name.lower())
        if not command or not command.returns_text:
            return user_input
        return await command.run(message, remainder) or user_input

    async def reply_as_person_to(self, message):
        sender_name = await self.history.name_for(message.sender_id)
        if sender_name not in self.people_to_respond_to:
            return
        response = await asyncio.to_thread(self.respond_to.get_response_from_name_and_message,
                                           sender_name, message.text)
        await self.messenger.send_text(message.thread_id, response)

    def is_mentioned_in(self, message):
        if any(str(mention.user_id) == str(self.messenger.uid) for mention in mentions_in(message)):
            return True
        return bool(self.messenger.name) and self.messenger.name.lower() in (message.text or "").lower()

    async def reply_to_mention(self, message):
        question = text_without(message, self.messenger.name)
        quoted = message.replied_to_message
        print("Answering mention: " + question)
        answer = await asyncio.to_thread(generate_text.answer_to, question, quoted.text if quoted else None)
        await self.reply_with_text(message, answer)

    async def reply_with_text(self, message, text):
        await self.messenger.send_text(message.thread_id, text, reply_to=message.id)


def help_line_for(name, command):
    if not command.usage:
        return f"{name} - {command.description}"
    return f"{name} {command.usage} - {command.description}"


def failure_message_for(error):
    reason = str(error).strip() or type(error).__name__
    return "Sorry, that went wrong: " + reason[:failure_reason_limit]


def text_without(message, bot_name):
    text = message.text or ""
    for mention in sorted(mentions_in(message), key=lambda mention: mention.offset, reverse=True):
        text = text[:mention.offset] + text[mention.offset + mention.length:]
    if bot_name:
        text = re.sub(re.escape(bot_name), "", text, flags=re.IGNORECASE)
    return text.strip(" @")


def mentions_in(message):
    return message.mentions if isinstance(message.mentions, list) else []


def split_command(text):
    words = text.split()
    if not words:
        return "", ""
    return words[0], text.replace(words[0], "", 1).strip()


def message_count_in(user_input):
    return int(user_input) if user_input.isdigit() else default_summary_length


def map_link_for(lat, long):
    return f"https://www.google.com/maps/search/?api=1&query={lat},{long}"


def start():
    client = Client(cookies_file_path=cookies_file)
    handler = MessageHandler(client)
    client.add_listener(EventType.MESSAGE, handler.on_message)
    client.run()
