# -*- coding: UTF-8 -*-

import fbchat
import cookies
import sensitive
import openai
import chat


class EchoBot(fbchat.Client):

    chat_history = chat.Chat()

    default_message_object = fbchat.Message(emoji_size=None, reply_to_id=None, sticker=None, text=None)

    cmd_chat_setup = [{"role": "system", "content": "You are a female doctor in a hospital, you have a boyfriend who has started to grow a moustache you hate. Your nickname is ratty. You are very tired, and enjoy classical music."},
                      {"role": "user", "content": "How was your day today?"},
                      {"role": "system", "content": "uh fine had this annoying lady in resp who was a bit violent and kept swinging at nurses, had to swaddle her in clothes"},
                      {"role": "user", "content": "are you excited for this weekend"},
                      {"role": "system", "content": "eeeee yes can't wait ratty will certainly be there, so tired of work"}]

    angus_history = chat.Chat()
    angus_chat_setup = [{"role": "system", "content": "You are a mechanic. This person's motorbike is completely broken and needs very expensive fixing, brakes, tyres etc. Use short replies. You haven't been paid by then for the work yet. Answer quickly, but always bring back up their motorbike and the expense of the fixes."},
                      {"role": "user", "content": "I'll be on later"},
                      {"role": "system", "content": "Yeah that's great and all, but you still need to pay for those fixes on your bike! It's totally broken!"},
                      {"role": "user", "content": "?"},
                      {"role": "system", "content": "What do you mean ?, don't be sassy with me until you've paid for the repairs!"}]

    johann_history = chat.Chat()
    johann_chat_setup = [{"role": "system", "content": "You are very upset, your Suzuki DRZ motorbike just got stolen. Use short replies, if people try to talk to you - answer solemnly"},
                        {"role": "user", "content": "I'll be on later"},
                        {"role": "system", "content": "Ah well, you have fun - I'm still a bit sad my DRZ got stolen..."},
                        {"role": "user", "content": "?"},
                        {"role": "system", "content": "I don't know anymore, don't think I could answer just so annoying about the DRZ being stolen"}]


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
        #self.markAsDelivered(thread_id, message_object.uid)
        #self.markAsRead(thread_id)

        if author_id != self.uid and message_object.text.startswith("!generate"):
        #if author_id != self.uid and message_object.text.startswith("!"):
            print("got: " + message_object.text.replace("!generate ", ""))
            image_url = get_filled_image_url_from(message_object.text.replace("!generate ", ""))
            self.sendRemoteImage(image_url, self.default_message_object, thread_id=thread_id, thread_type=thread_type)

            #self.default_message_object.text = response
            #self.send(self.default_message_object, thread_id=thread_id, thread_type=thread_type)

        if author_id != self.uid and self.fetchUserInfo(author_id)[author_id].name == "Chantal Duchenne":
            self.chat_history.add_message_from(message_object.text, "user")
            self.default_message_object.text = get_response_from_messages_with_setup(self.cmd_chat_setup, self.chat_history.messages)
            self.send(self.default_message_object, thread_id=thread_id, thread_type=thread_type)

        if author_id != self.uid and self.fetchUserInfo(author_id)[author_id].name == "Angus Hutchison":
            self.chat_history.add_message_from(message_object.text, "user")
            self.default_message_object.text = get_response_from_messages_with_setup(self.angus_chat_setup, self.angus_history.messages)
            self.send(self.default_message_object, thread_id=thread_id, thread_type=thread_type)

        if author_id != self.uid and self.fetchUserInfo(author_id)[author_id].name == "Johann Walker":
            self.chat_history.add_message_from(message_object.text, "user")
            self.default_message_object.text = get_response_from_messages_with_setup(self.johann_chat_setup, self.johann_history.messages)
            self.send(self.default_message_object, thread_id=thread_id, thread_type=thread_type)


def get_response_from_messages_with_setup(setup_messages, messages):
    completion = openai.ChatCompletion.create(model="gpt-3.5-turbo", messages=setup_messages + messages)
    return completion.choices[0].message.content


def get_image_url_from(message):
    response = openai.Image.create(
        prompt=message,
        n=1,
        size="256x256",
    )
    return response["data"][0]["url"]


def get_filled_image_url_from(message):
    response = openai.Image.create_edit(
        image=open("group_full.png", "rb"),
        mask=open("group.png", "rb"),
        prompt=message,
        n=1,
        size="512x512"
    )
    return response['data'][0]['url']


def start():
    openai.api_key = sensitive.api_key
    client = EchoBot(sensitive.email, sensitive.password, session_cookies=cookies.read())
    cookies.store(client.getSession())
    client.listen()
