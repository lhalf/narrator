# -*- coding: UTF-8 -*-

import fbchat
import cookies
import sensitive


class EchoBot(fbchat.Client):
    default_message_object = fbchat.Message(emoji_size=None, reply_to_id=None, sticker=None, text=None)

    def onMessage(
            self,
            mid=None,
            author_id=None,
            message=None,
            message_object=None,
            thread_id=None,
            thread_type=fbchat.ThreadType.USER,
            ts=None,
            metadata=None,
            msg=None,
    ):
        self.markAsDelivered(thread_id, message_object.uid)
        self.markAsRead(thread_id)

        if author_id != self.uid and message_object.text.startswith("!"):
            self.default_message_object.text = author_id + " sent " + message_object.text
            self.send(self.default_message_object, thread_id=thread_id, thread_type=thread_type)


def start():
    client = EchoBot(sensitive.email, sensitive.password, session_cookies=cookies.read())
    cookies.store(client.getSession())
    client.listen()



