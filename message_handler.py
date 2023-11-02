import fbchat

import cookies
import sensitive
import openai
import people
import osrs
import generate_image

from itertools import islice


class MessageHandler(fbchat.Client):
    osrs_items = osrs.OSRSItems()
    people_to_respond_to = people.RespondTo([sensitive.LH, sensitive.AH, sensitive.JW, sensitive.AW])

    @staticmethod
    def message_object(emoji_size=None, reply_to_id=None, sticker=None, text=None):
        return fbchat.Message(emoji_size=emoji_size, sticker=sticker, text=text, reply_to_id=reply_to_id)

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
        if author_id != self.uid:
            match message_object.text.split()[0]:
                case "!genfill":
                    image_url = generate_image.get_filled_url_from(message_object.text.replace("!generate ", ""),
                                                                   "group_full.png", "group.png")
                    self.sendRemoteImage(image_url, self.message_object(), thread_id=thread_id,
                                         thread_type=thread_type)

                case "!gen":
                    image_url = generate_image.get_url_from(message_object.text.replace("!gen ", ""))
                    self.sendRemoteImage(image_url, self.message_object(), thread_id=thread_id,
                                         thread_type=thread_type)

                case "!examine":
                    message = self.message_object()
                    message.text = self.osrs_items.get_examine_text_from_item_name(
                        message_object.text.replace("!examine ", ""))
                    self.send(message, thread_id=thread_id, thread_type=thread_type)

                case "!echoimages":
                    for image in islice(self.fetchThreadImages(thread_id), 100):
                        if not hasattr(image, 'thumbnail_url'):
                            continue
                        self.sendRemoteImage(image.thumbnail_url, self.message_object(), thread_id=thread_id,
                                             thread_type=thread_type)

                case "!randomimage":
                    image_count_in_thread = 0
                    for count, image in enumerate(islice(self.fetchThreadImages(thread_id), 10000)):
                        image_count_in_thread = count
                    print(image_count_in_thread)

                case _:
                    message = self.message_object()
                    message.text = \
                        self.people_to_respond_to.get_response_from_name_and_message(
                            self.fetchUserInfo(author_id)[author_id].name, message_object.text)
                    self.send(message, thread_id=thread_id, thread_type=thread_type)


def start():
    openai.api_key = sensitive.api_key
    client = MessageHandler(sensitive.email, sensitive.password, session_cookies=cookies.read())
    cookies.store(client.getSession())
    client.listen()
