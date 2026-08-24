import asyncio
import time

seconds_between_sends = 1.5


class Messenger:

    def __init__(self, client):
        self.client = client
        self.last_sent_at = 0

    @property
    def uid(self):
        return self.client.uid

    @property
    def name(self):
        return self.client.name

    async def send_text(self, thread_id, text, reply_to=None):
        await self.wait_for_send_slot()
        await self.client.send_message(text, thread_id, reply_to_message=reply_to)

    async def send_image(self, thread_id, image_path, reply_to=None):
        await self.send_upload(thread_id, image_path, voice_clip=False, reply_to=reply_to)

    async def send_voice_clip(self, thread_id, clip_path, reply_to=None):
        await self.send_upload(thread_id, clip_path, voice_clip=True, reply_to=reply_to)

    async def send_upload(self, thread_id, filepath, voice_clip, reply_to=None):
        file_ids = await self.client.uploadFiles(file_path=[filepath], voice_clip=voice_clip)
        await self.wait_for_send_slot()
        await self.client.send_message(None, thread_id, files_ids=file_ids, reply_to_message=reply_to)

    async def download(self, url, filepath):
        await self.client.download(url, filepath)

    async def wait_for_send_slot(self):
        waited = time.monotonic() - self.last_sent_at
        if waited < seconds_between_sends:
            await asyncio.sleep(seconds_between_sends - waited)
        self.last_sent_at = time.monotonic()
