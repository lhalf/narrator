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
import commands
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

echoed_image_limit = 100
failure_reason_limit = 200

Request = namedtuple("Request", ["handler", "message"])


class MessageHandler:

    def __init__(self, client):
        self.messenger = messenger.Messenger(client)
        self.history = chat_history.ChatHistory(client)
        self.osrs_items = osrs.OSRSItems()
        self.people_to_respond_to = []
        self.respond_to = people.RespondTo(self.people_to_respond_to)
        self.all_bikes = bikes.AllBikes()

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
        request = f"{name} {user_input}".strip()
        if not commands.is_command(request):
            await self.reply_as_person_to(message)
            return

        text = await commands.run(Request(self, message), request)
        if text is not None:
            await self.reply_with_text(message, text)

    async def help(self, message):
        return commands.help_text()

    async def summarise(self, message, count):
        messages = await self.history.messages_in(message.thread_id, count)
        transcript = await self.history.transcript_of(messages)
        return await asyncio.to_thread(generate_text.summary_of, transcript)

    async def quote(self, message):
        return await self.history.random_quote_from(message.thread_id)

    async def examine(self, message, item):
        return self.osrs_items.get_examine_text_from_item_name(item)

    async def bike(self, message, name):
        return await asyncio.to_thread(self.all_bikes.find, name)

    async def find(self, message, query, summarised):
        if summarised:
            return await self.summarise_search(message, query)
        for result in await self.history.search_results_for(message.thread_id, query):
            await self.reply_with_text(message, result)

    async def summarise_search(self, message, query):
        results = await self.history.search_for(message.thread_id, query)
        if not results:
            return f"Nothing found for \"{query}\""
        found = "\n".join(chat_history.line_for(result) for result in results)
        return await asyncio.to_thread(generate_text.summary_of, found)

    async def gen(self, message, prompt):
        await asyncio.to_thread(generate_image.save_generated_at, prompt, generated_image_file)
        await self.messenger.send_image(message.thread_id, generated_image_file, reply_to=message.id)

    async def genfill(self, message, prompt):
        await asyncio.to_thread(generate_image.save_filled_at, prompt,
                                "group_full.png", "group.png", generated_image_file)
        await self.messenger.send_image(message.thread_id, generated_image_file, reply_to=message.id)

    async def say(self, message, text, pitch, effects):
        spoken = await self.spoken_text_for(message, text)
        if not spoken:
            return
        await asyncio.to_thread(speech.create_audio_file_from_at, spoken, voice_clip_file, pitch, effects)
        await self.messenger.send_voice_clip(message.thread_id, voice_clip_file, reply_to=message.id)

    async def crime(self, message, postcode):
        lat, long = await asyncio.to_thread(crime.get_lat_long_from_postcode, postcode)
        if lat is None:
            return f"Could not find postcode {postcode}"
        await self.reply_with_text(message, map_link_for(lat, long))
        await asyncio.to_thread(crime.create_plot_from_postcode_at, postcode, crime_plot_file)
        await self.messenger.send_image(message.thread_id, crime_plot_file, reply_to=message.id)

    async def echoimages(self, message):
        for image_url in await self.history.image_urls_in(message.thread_id, echoed_image_limit):
            await self.messenger.download(image_url, generated_image_file)
            await self.messenger.send_image(message.thread_id, generated_image_file)

    async def randomimage(self, message):
        image_urls = await self.history.image_urls_in(message.thread_id, chat_history.image_search_limit)
        if not image_urls:
            return "No images found"
        await self.messenger.download(random.choice(image_urls), generated_image_file)
        await self.messenger.send_image(message.thread_id, generated_image_file, reply_to=message.id)

    async def spoken_text_for(self, message, text):
        if not commands.is_command(text):
            return text
        return await commands.run(Request(self, message), text)

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

    async def report_failure(self, message, error):
        try:
            await self.reply_with_text(message, failure_message_for(error))
        except Exception as reporting_error:
            print(f"Could not report failure: {reporting_error!r}")

    async def reply_with_text(self, message, text):
        await self.messenger.send_text(message.thread_id, text, reply_to=message.id)


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


def map_link_for(lat, long):
    return f"https://www.google.com/maps/search/?api=1&query={lat},{long}"


def start():
    client = Client(cookies_file_path=cookies_file)
    handler = MessageHandler(client)
    client.add_listener(EventType.MESSAGE, handler.on_message)
    client.run()
