import os
import random
import re
import tempfile
from datetime import datetime
from itertools import islice

from fbchat_muqit import Client, EventType, ImageAttachment

import bikes
import command_handler
import crime
import generate_image
import generate_text
import osrs
import people
import speech

cookies_file = "cookies.json"
temp_directory = tempfile.gettempdir()
generated_image_file = os.path.join(temp_directory, "narrator_image.png")
voice_clip_file = os.path.join(temp_directory, "narrator_voice.mp3")
crime_plot_file = os.path.join(temp_directory, "narrator_plot.png")

batch_size = 50
default_summary_length = 50
quote_search_limit = 500
search_result_limit = 10

help_text = "\n\n".join([
    "help - show this message",
    "@Narrator AI <question> - ask a question, optionally as a reply to another message",
    "summarise [n] - summarise the last n messages",
    "find <text> - search this thread's history for a phrase",
    "quote - post a random message from this thread",
    "gen <prompt> - generate an image",
    "genfill <prompt> - regenerate the masked part of the group photo",
    "say <text> - reply with a voice clip",
    "examine <item> - look up the OSRS examine text for an item",
    "bike <name> - look up a bike's specs",
    "crime <postcode> - map link and crime plot for a postcode",
    "echoimages - resend the last 100 images in this thread",
    "randomimage - count the images in this thread",
])


class MessageHandler:

    def __init__(self, client):
        self.client = client
        self.osrs_items = osrs.OSRSItems()
        self.people_to_respond_to = []
        self.respond_to = people.RespondTo(self.people_to_respond_to)
        self.all_bikes = bikes.AllBikes()

    async def on_message(self, message):
        if message.sender_id == self.client.uid:
            return

        if self.is_mentioned_in(message):
            await self.reply_to_mention(message)
            return

        command, user_input = command_handler.extract_from(message)

        match command:
            case "help":
                await self.reply_with_text(message, help_text)

            case "summarise":
                messages = await self.messages_in_thread(message.thread_id, message_count_in(user_input))
                await self.reply_with_text(message, generate_text.summary_of(await self.transcript_of(messages)))

            case "quote":
                await self.reply_with_text(message, await self.random_quote_from(message.thread_id))

            case "find":
                await self.reply_with_text(message, await self.search_results_for(message.thread_id, user_input))

            case "genfill":
                generate_image.save_filled_at(user_input, "group_full.png", "group.png", generated_image_file)
                await self.reply_with_local_image_at(message, generated_image_file)

            case "gen":
                generate_image.save_generated_at(user_input, generated_image_file)
                await self.reply_with_local_image_at(message, generated_image_file)

            case "say":
                await self.reply_with_local_voice_clip_from(message, user_input)

            case "examine":
                examine_text = self.osrs_items.get_examine_text_from_item_name(user_input)
                await self.reply_with_text(message, examine_text)

            case "echoimages":
                for image_url in await self.image_urls_in_thread(message.thread_id, 100):
                    await self.client.download(image_url, generated_image_file)
                    await self.send_local_image_at(message.thread_id, generated_image_file)

            case "randomimage":
                image_urls = await self.image_urls_in_thread(message.thread_id, 10000)
                print(len(image_urls))

            case "bike":
                bike_info = self.all_bikes.find(user_input)
                await self.reply_with_text(message, bike_info)

            case "crime":
                lat, long = crime.get_lat_long_from_postcode(user_input)
                await self.reply_with_text(message, map_link_for(lat, long))
                crime.create_plot_from_postcode_at(user_input, crime_plot_file)
                await self.reply_with_local_image_at(message, crime_plot_file)

            case _:
                sender = await self.client.fetch_user_info(message.sender_id)
                sender_name = sender[message.sender_id].name
                if sender_name not in self.people_to_respond_to:
                    return
                response = self.respond_to.get_response_from_name_and_message(sender_name, message.text)
                await self.client.send_message(response, message.thread_id)

    def is_mentioned_in(self, message):
        if any(str(mention.user_id) == str(self.client.uid) for mention in mentions_in(message)):
            return True
        return bool(self.client.name) and self.client.name.lower() in (message.text or "").lower()

    async def reply_to_mention(self, message):
        question = text_without(message, self.client.name)
        quoted = message.replied_to_message
        print("Answering mention: " + question)
        await self.reply_with_text(message, generate_text.answer_to(question, quoted.text if quoted else None))

    async def messages_in_thread(self, thread_id, limit):
        messages = []
        before = None
        while len(messages) < limit:
            batch = await self.client.fetch_thread_messages(thread_id, message_limit=batch_size, before=before)
            if not batch or batch[0].timestamp == before:
                break
            messages = list(batch) + messages
            before = batch[0].timestamp
        return messages[-limit:]

    async def transcript_of(self, messages):
        named = [message for message in messages if message.text]
        if not named:
            return ""
        senders = await self.client.fetch_user_info(*{message.sender_id for message in named})
        return "\n".join(f"{name_of(senders, message.sender_id)}: {message.text}" for message in named)

    async def random_quote_from(self, thread_id):
        messages = [message for message in await self.messages_in_thread(thread_id, quote_search_limit)
                    if message.text and message.sender_id != self.client.uid]
        if not messages:
            return "Nothing to quote"
        quoted = random.choice(messages)
        senders = await self.client.fetch_user_info(quoted.sender_id)
        return f"\"{quoted.text}\" - {name_of(senders, quoted.sender_id)}, {date_time_of(quoted.timestamp)}"

    async def search_results_for(self, thread_id, query):
        found = await self.client.search_message(query, thread_id)
        results = found["results"][:search_result_limit]
        if not results:
            return f"Nothing found for \"{query}\""
        return "\n".join(f"{date_of(result.timestamp_ms)} {result.sender_name}: {result.snippet}"
                         for result in results)

    async def image_urls_in_thread(self, thread_id, limit):
        image_urls = []
        before = None
        while len(image_urls) < limit:
            messages = await self.client.fetch_thread_messages(thread_id, message_limit=batch_size, before=before)
            if not messages or messages[0].timestamp == before:
                break
            for message in messages:
                image_urls.extend(image_urls_in(message))
            before = messages[0].timestamp
        return list(islice(image_urls, limit))

    async def reply_with_text(self, input_message, text):
        await self.client.send_message(text, input_message.thread_id, reply_to_message=input_message.id)

    async def reply_with_local_image_at(self, input_message, image_path):
        await self.send_local_image_at(input_message.thread_id, image_path, reply_to=input_message.id)

    async def reply_with_local_voice_clip_from(self, input_message, text):
        speech.create_audio_file_from_at(text, voice_clip_file)
        file_ids = await self.client.uploadFiles(file_path=[voice_clip_file], voice_clip=True)
        await self.client.send_message(None, input_message.thread_id, files_ids=file_ids,
                                       reply_to_message=input_message.id)

    async def send_local_image_at(self, thread_id, image_path, reply_to=None):
        file_ids = await self.client.uploadFiles(file_path=[image_path], voice_clip=False)
        await self.client.send_message(None, thread_id, files_ids=file_ids, reply_to_message=reply_to)


def image_urls_in(message):
    return [attachment.large_preview.url for attachment in message.attachments
            if isinstance(attachment, ImageAttachment) and attachment.large_preview]


def text_without(message, bot_name):
    text = message.text or ""
    for mention in sorted(mentions_in(message), key=lambda mention: mention.offset, reverse=True):
        text = text[:mention.offset] + text[mention.offset + mention.length:]
    if bot_name:
        text = re.sub(re.escape(bot_name), "", text, flags=re.IGNORECASE)
    return text.strip(" @")


def mentions_in(message):
    return message.mentions if isinstance(message.mentions, list) else []


def message_count_in(user_input):
    return int(user_input) if user_input.isdigit() else default_summary_length


def name_of(senders, sender_id):
    sender = senders.get(sender_id)
    return sender.name if sender else "Unknown"


def date_of(timestamp_ms):
    return datetime.fromtimestamp(timestamp_ms / 1000).strftime("%d/%m/%y")


def date_time_of(timestamp_ms):
    return datetime.fromtimestamp(timestamp_ms / 1000).strftime("%d/%m/%y %H:%M")


def map_link_for(lat, long):
    return f"https://www.google.com/maps/search/?api=1&query={lat},{long}"


def start():
    client = Client(cookies_file_path=cookies_file)
    handler = MessageHandler(client)
    client.add_listener(EventType.MESSAGE, handler.on_message)
    client.run()
