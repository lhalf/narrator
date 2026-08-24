import random
import time
from datetime import datetime

from fbchat_muqit import ImageAttachment
from fbchat_muqit.graphql import QueryRequest

batch_size = 50
image_search_limit = 1000
search_result_limit = 10
quote_attempts = 8
day_in_milliseconds = 24 * 60 * 60 * 1000
thread_messages_doc_id = "1860982147341344"
graphql_url = "https://www.facebook.com/api/graphqlbatch/"


class ChatHistory:

    def __init__(self, client):
        self.client = client
        self.oldest_timestamps = {}

    async def fetch_messages(self, thread_id, limit, before=None):
        query = QueryRequest(doc_id=thread_messages_doc_id, query_params={
            "id": thread_id,
            "message_limit": limit,
            "load_messages": True,
            "load_read_receipts": True,
            "before": before,
        })
        data = {"queries": self.client._graphql.queries_to_json(query)}
        result = await self.client._state._post(graphql_url, data=data, as_graphql=True)
        return self.client._parser.parse_thread_message(result)

    async def messages_in(self, thread_id, limit):
        messages = []
        before = None
        while len(messages) < limit:
            batch = await self.fetch_messages(thread_id, batch_size, before)
            if not batch or batch[0].timestamp == before:
                break
            messages = list(batch) + messages
            before = batch[0].timestamp
        return messages[-limit:]

    async def image_urls_in(self, thread_id, limit):
        messages = await self.messages_in(thread_id, image_search_limit)
        return [url for message in messages for url in image_urls_in(message)][:limit]

    async def transcript_of(self, messages):
        written = [message for message in messages if message.text]
        if not written:
            return ""
        senders = await self.client.fetch_user_info(*{message.sender_id for message in written})
        return "\n".join(f"{name_of(senders, message.sender_id)}: {message.text}" for message in written)

    async def random_quote_from(self, thread_id):
        oldest = await self.oldest_timestamp_in(thread_id)
        newest = now_in_milliseconds()
        for _ in range(quote_attempts):
            batch = await self.fetch_messages(thread_id, batch_size, random.randint(oldest, newest))
            quotable = [message for message in batch or []
                        if message.text and message.sender_id != self.client.uid]
            if quotable:
                quoted = random.choice(quotable)
                senders = await self.client.fetch_user_info(quoted.sender_id)
                return f"\"{quoted.text}\" - {name_of(senders, quoted.sender_id)}, {date_time_of(quoted.timestamp)}"
        return "Nothing to quote"

    async def oldest_timestamp_in(self, thread_id):
        if thread_id not in self.oldest_timestamps:
            self.oldest_timestamps[thread_id] = await self.find_oldest_timestamp_in(thread_id)
        return self.oldest_timestamps[thread_id]

    async def find_oldest_timestamp_in(self, thread_id):
        now = now_in_milliseconds()
        lookback = day_in_milliseconds
        while lookback < now and await self.has_messages_before(thread_id, now - lookback):
            lookback *= 2

        without_messages = max(now - lookback, 0)
        with_messages = now - lookback // 2
        while with_messages - without_messages > day_in_milliseconds:
            middle = (without_messages + with_messages) // 2
            if await self.has_messages_before(thread_id, middle):
                with_messages = middle
            else:
                without_messages = middle
        return without_messages

    async def has_messages_before(self, thread_id, timestamp):
        return bool(await self.fetch_messages(thread_id, 1, timestamp))

    async def search_results_for(self, thread_id, query):
        found = await self.client.search_message(query, thread_id)
        results = found["results"][:search_result_limit]
        if not results:
            return [f"Nothing found for \"{query}\""]
        return [f"{date_of(result.timestamp_ms)} {result.sender_name}: {result.snippet}"
                for result in results]

    async def name_for(self, sender_id):
        return name_of(await self.client.fetch_user_info(sender_id), sender_id)


def image_urls_in(message):
    return [attachment.large_preview.url for attachment in message.attachments
            if isinstance(attachment, ImageAttachment) and attachment.large_preview]


def name_of(senders, sender_id):
    sender = senders.get(sender_id)
    return sender.name if sender else "Unknown"


def now_in_milliseconds():
    return int(time.time() * 1000)


def date_of(timestamp_ms):
    return datetime.fromtimestamp(int(timestamp_ms) / 1000).strftime("%d/%m/%y")


def date_time_of(timestamp_ms):
    return datetime.fromtimestamp(int(timestamp_ms) / 1000).strftime("%d/%m/%y %H:%M")
